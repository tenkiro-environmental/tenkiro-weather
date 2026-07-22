# Tenkiro — Design

Tenkiro is a private-radio home weather system: a solar-powered outdoor station
speaking a small point-to-point LoRa protocol to an always-on indoor bridge.
This document captures the founding design brief (2026-07) and is the **source
of truth** for decisions and open questions. See `NAMING.md` for the naming
hierarchy.

```
Tenkiro          ecosystem / brand
Sora             outdoor solar weather station   (hardware/tenkiro-sora)
Hashi            indoor radio ↔ network bridge   (hardware/tenkiro-hashi)
Nami             the over-the-air protocol / radio subsystem
Kumo / Kaze / Ame / Hikari   humidity-pressure / wind / rain / light-UV modules
```

"Sora speaks Nami to Hashi."

## System topology

```
┌─────────────────────────┐       915 MHz LoRa       ┌───────────────────────┐
│ Tenkiro Sora            │  ─────────────────────▶  │ Tenkiro Hashi         │
│                         │  ◀── ACK / time sync ──  │                       │
│ sensors                 │                          │ SX1262                │
│ low-power MCU           │                          │ Ethernet or Wi-Fi     │
│ SX1262 / radio module   │                          │ USB-C power           │
│ solar / 12 V in + LTO   │                          │ MQTT / HTTP / local DB│
└─────────────────────────┘                          └───────────────────────┘
```

Sora spends almost all its time asleep:

1. Wake on RTC.
2. Power and sample sensors (load-switched rails).
3. Build a compact packet.
4. Transmit.
5. Listen briefly for an acknowledgment.
6. Retry later only when necessary.
7. Return to deep sleep.

Hashi remains powered and listening continuously — it is indoors on USB power.

## Radio — SX1262 at 915 MHz (decided)

A **private 915 MHz LoRa link** with our own bridge, rather than Wi-Fi on the
station or a full LoRaWAN deployment. The **Semtech SX1262** is the radio:

- Sub-GHz propagation handles walls and outdoor placement far better than 2.4 GHz.
- LoRa modulation suits tiny, infrequent packets; FSK remains available for
  faster local transfers.
- Up to +22 dBm TX, ~4.2 mA RX current; covers the North American 902–928 MHz
  ISM band, with a Semtech NA reference design available.

**Avoid the 30 dBm amplified modules** (e.g. Ebyte's PA variants): much higher
peak current (~155 mA class), more RF-layout complexity, less comfortable
regulatory margin. For a weather packet every 30–120 s, +14 to +20 dBm is
likely plenty with a well-placed antenna; keep +22 dBm as a configurable
upper limit.

### Module vs bare radio

- **Revision A (both boards): Ebyte E22-900M22S module** — SX1262, 850–930 MHz,
  +22 dBm, pre-designed RF matching, SPI control, 14 × 20 mm castellated
  footprint. Least painful route: we still own the protocol and firmware but
  the first hardware spin doesn't depend on a perfect matching network.
- **Later revision: bare SX1262 on the PCB** — lower BOM cost, smaller board,
  more control over antenna switching/filtering; more RF design and validation
  work. Caution: JLCPCB's "SX1262" listing shows a package/description
  inconsistent with the bare Semtech IC — verify manufacturer number, footprint
  and datasheet inside the assembly library before selecting it.
- **Not** an ESP32+SX1262 combo module on Sora: an ESP32 outdoors undermines
  the low-power budget unless aggressively power-gated.

### E22-900M22S vs E220-900M22S

| Module | Radio IC | Notes |
|---|---|---|
| **E22-900M22S** | Semtech **SX1262** | chosen — full SX126x envelope, best library support |
| E220-900M22S | Semtech **LLCC68** | cheaper SX1262 relative; broadly command-compatible but limited to standard narrowband LoRa operation |

Both are 850–930 MHz, +22 dBm, SPI, ~14 × 20 mm castellated. The SX1262 gives
fewer firmware surprises, better RadioLib/SX126x support, room to tune the
link (FSK, unusual LoRa settings, LoRaWAN if ever wanted), and easier bridge
interoperability. Note the **M** in these names means the raw **SPI radio
module** — our MCU runs the packet protocol and configures the radio. (UART
variants carry a **T**, e.g. E220-900T22S — not what we want.)

## Nami — the protocol (decided direction)

**Not LoRaWAN.** A small private point-to-point protocol is easier to debug and
better matched to one station + one bridge.

A packet contains (fixed-width binary, roughly 40–80 bytes total):

- protocol version, station ID, packet sequence, station uptime
- battery voltage, state of charge (BQ34Z100 fuel gauge), solar
  voltage/current
- temperature, humidity, pressure
- wind speed, wind gust, wind direction
- rain counter, light/UV
- lightning: cumulative stroke counter + last-storm distance (2026-07 add)
- hail/impact: cumulative counter (2026-07 add)
- sky IR temperature (cloud cover; 2026-07 add)
- status flags, authentication tag (16 B AEAD tag — see Security below; the
  tag replaces a CRC, it is not in addition to one)

Design rules:

- Fixed-width binary encoding — never JSON over the air.
- Sequence numbers for duplicate detection.
- **Cumulative** rain and wind counters so one lost packet doesn't destroy the
  measurement.
- Acknowledgments only when needed.
- A unique device key and **authenticated encryption**.
- Periodic bridge-to-node clock correction.
- Local flash buffering on Sora during extended link loss.

### Security (decided 2026-07)

**AEAD: Ascon-128a (NIST SP 800-232) is the plan of record**, with the frame
built for **cipher agility** so it isn't welded in. Rationale: crypto cost is
a rounding error next to radio TX (an 80-byte packet costs ~µJ to seal in
software on the U073's M0+ vs. ~130 ms of +14 dBm airtime), so the pick is
about fit, not speed — Ascon is the NIST lightweight-crypto standard,
purpose-designed for exactly this class of device, constant-time by
construction, small code/state, with a maintained `ascon-aead` no_std Rust
crate. **ChaCha20-Poly1305 (RFC 8439) is the named alternate** (most-analyzed
software AEAD, best cross-language tooling) and gets a reserved suite ID from
day one. Software AEAD only — never depend on hw AES (the U073 has none).

Frame layout (cleartext header is the AAD; payload encrypted; tag full-width):

```
[ver:1][suite:1][devid:4][epoch:2][seq:4] [encrypted payload 24–56 B] [tag:16]
```

- **`suite` byte = cipher agility.** 0x01 = Ascon-128a (default), 0x02 =
  ChaCha20-Poly1305 (reserved). Hashi accepts any suite it knows for a paired
  device; a future cipher is a firmware update and a new suite ID, not a
  protocol break. `ver` covers layout changes, `suite` covers crypto changes —
  they are deliberately separate fields.
- **Nonce = devid (4 B) ‖ epoch (2 B) ‖ seq (4 B)**, zero-padded/truncated to
  the suite's nonce size. No random nonces, no negotiation, **no external
  NVM needed**: `epoch` is a boot counter persisted in a dedicated internal
  flash page and incremented **once per boot** (~1 flash write per power
  cycle — endurance is a non-issue; 65 k boots at even one brownout a day is
  ~180 years), and `seq` is a RAM counter zeroed at boot. Any reboot bumps
  the epoch, so a (epoch, seq) pair — and hence a nonce — can never repeat,
  even across brownouts with lost RAM. This is the structural nonce-safety
  property, bought without per-packet NVM writes.
- **Replay protection**: Hashi enforces strictly increasing `(epoch, seq)`
  (lexicographic) per device — a replayed packet fails the ordering check
  before tag verification even runs. 2³² packets per boot at one a minute is
  ~8000 years, so `seq` never wraps within an epoch (wrap forces a reboot →
  new epoch, belt-and-suspenders).
- **Tag: full 16 bytes.** At SF7 truncating to 8 B saves ~10 ms airtime per
  minute — not worth reasoning about reduced forgery margins.

Key management stays deliberately primitive: **one pre-shared 256-bit key per
Sora↔Hashi pairing, provisioned at flash time**, with per-direction subkeys
derived via HKDF (`uplink` / `downlink` labels) so ACKs never share a nonce
space with telemetry. No join procedure, no key exchange, no session state —
that is the LoRaWAN complexity Nami exists to avoid. Rekeying is a reflash
(honest for a device you own and can walk to); in-field pairing can layer on
later without changing the frame. Known residual: encryption doesn't hide
traffic timing or stop jamming — inherent to LoRa, acceptable here.

### Initial link settings

```
Frequency:        915 MHz region-appropriate channel
Bandwidth:        125 kHz
Spreading factor: SF7 or SF8
Coding rate:      4/5
Transmit power:   +14 dBm initially
Packet interval:  60 seconds
ACK window:       150–300 ms
Retries:          1 delayed retry
```

**Do not jump to SF12.** It buys sensitivity at a large cost in airtime and
energy. Start around SF7, test through the actual walls, move up only when
packet-loss measurements justify it.

## Antenna

Antenna placement matters more than maximum TX power. At 915 MHz a quarter-wave
element is ~82 mm; a simple external whip or sealed adhesive antenna mounted
away from the ground plane, battery and solar wiring will usually beat a
compromised PCB antenna driven several dB harder. Sora includes:

- U.FL/I-PEX connector
- Optional footprint for a spring or wire antenna
- Antenna keepout
- ESD protection near any external connector
- Test connector or RF probe point
- Software-selectable transmit power

## Revision A boards

### `tenkiro-sora` — outdoor station

- Ultra-low-power MCU: **STM32U073CBT6** (decided 2026-07 — see platform sketch)
- E22-900M22S (SX1262) radio module
- External 915 MHz antenna (U.FL)
- **1S LTO cell** (lithium-titanate; wide-temperature outdoor chemistry —
  supersedes the brief's LiFePO₄; 1S since 2026-07) + **fuel gauge** +
  **flexible charge input**: raw solar panel **or** up to 16 V DC (12 V
  battery system)
- Low-quiescent-current solar/MPPT charger with resistor-set LTO float
- Load switches for the sensor rails
- Internal-flash buffering for readings during link loss (no external NVM —
  FRAM dropped 2026-07)
- Sensor split kept flexible: on-board temp/RH/pressure; wind and air-quality
  on detachable module ports (may be combined or separate — see platform
  sketch)
- Atmospheric extras: AS3935 lightning (always-listening), AS7331/GUVA UV,
  MLX90614 sky-IR cloud sensing, piezo hail/impact channel

### `tenkiro-hashi` — indoor bridge

- E22-900M22S (SX1262) radio module — same radio as Sora for rev A
- **Primary MCU: ESP32-S3** (Wi-Fi; ESP32-S3-WROOM-1 module)
- **Backup option (wired Ethernet, non-ESP32): STM32H563VGT6 + LAN8742A
  RMII PHY** — decided 2026-07 (see below)
- USB-C power
- **SCD40 CO₂ + temp/RH** (indoor air on the always-on node; 2026-07 add)
- MQTT client + local web interface
- Optional USB serial console

#### Hashi Ethernet-backup variant — STM32H563 + LAN8742A (decided 2026-07)

The initial survey (`doc/hashi-ethernet-mcu-survey-2026-07.md`) recommended
RP2350A + WIZnet W5500, but the **WIZnet path was ruled out by decision**
(2026-07: no WIZnet parts), which promotes the STM32 integrated-MAC path —
and it keeps the whole fleet on STM32:

- **★ STM32H563VGT6 + LAN8742A — chosen.** Cortex-M33 @ 250 MHz with an
  integrated Ethernet MAC; JLCPCB stock is healthy at the VGT6 (LQFP-100)
  option — **8,042 in stock (LCSC C18221950)**, unlike the thin ZIT6/LQFP-144
  the first survey checked. PHY: **LAN8742A-CZ-TR (C621424, 2.6 k stock)** or
  the industrial **LAN8742AI-CZ-TR (C621425, 3.1 k stock)** over RMII.
  Firmware: STM32 HAL + lwIP is mature (ST ships H5 bare-metal Ethernet
  references); `embassy-stm32` eth + embassy-net works with LAN8742.
- **Layout cost accepted:** RMII (7+ signals + clean 50 MHz REF_CLK + matched
  pairs to the magnetics) is the hardest routing of the surveyed options —
  that's the price of dropping the SPI-Ethernet chips. Follow ST's REF_CLK
  sourcing guidance (AN; PHY-out vs MCU-out timing).
- **Avoid LAN8720A** as a "cheaper PHY" swap (44 k stock but notorious
  REF_CLK/nINTSEL strapping and clock-injection bring-up traps).
- Rejected: WIZnet W5500/W6100 (ruled out by decision); WCH CH32V307
  (10Base-T-only integrated PHY, no embassy Ethernet); SAME54/Nuvoton
  (external PHY anyway, weaker stock/ecosystem).

## Hardware platform sketch (2026-07)

Part picks verified against the JLCPCB/LCSC assembly library (jlcsearch,
2026-07). Fleet rule: MCUs come from parts already used across the sibling
repos (calcumaker / tsumikoro / ephemerkey / pulsarfab / reefvolt-*).

### Sora — block diagram

```
        solar panel (raw)  ──┐                       ┌── SHT40 temp/RH ────┐
        DC in 9–16 V ────────┤  input ORing +        │   BMP390 pressure   │ I²C,
        (12 V battery sys)   │  reverse-pol FET      │   VEML7700 ambient  │ load-
                             │  + SMBJ26A TVS        │   (SGP40 VOC opt.)  │ switched
                             ▼                       └─────────┬───────────┘
                      BQ24650 MPPT charger                     │
                      (float ≈ 2.85 V, 1S LTO)       ┌─────────┴───────────┐
                             │                       │  STM32U073CBT6      │
                      1S LTO cell (2.4 V nom,        │  (LQFP-48, ULP M0+) │
                      1.8–2.9 V; −30 °C charge OK)   │                     │
                        ├─ BQ34Z100 fuel gauge       │ SPI0: E22-900M22S ──┼── U.FL ant
                        │  (low-side sense, I²C) ────┤ int flash: outage   │
                      TPS63900 buck-boost → 3.3 V    │  buffer+nonce epoch │
                      (75 nA Iq, VIN 1.8–5.5 V) ─────┤ ADC: Vbat/Vsolar    │
                                                     │ LPTIM/EXTI: pulses  │
                                                     └──────┬──────┬───────┘
                                                            │      │
                                       Kaze/Ame pulse port ─┘      └─ mast bus (4-wire chain:
                                       (reed anemometer / rain      switched V+ · GND · RS-485 A/B,
                                        tipping bucket, RJ11,       MAX3471 micropower transceivers;
                                        ladder-vane ADC line)       smart wind / AQ pods, SPS30 opt.)
```

### Sora part table

| Block | Part | LCSC | Stock (2026-07) | Why |
|---|---|---|---|---|
| MCU | **STM32U073CBT6** (LQFP-48, M0+, 128 K/40 K) | C27035627 | 1,009 | Same STM32U0 family as ephemerkey's U083KCU6 (U083 ≈ U073 + LCD driver) — fleet firmware experience carries over; ST ULP line (sub-µA stop w/ RTC, LPUART/LPTIM); right-sized and cheap for a sleep-mostly node (outage buffering + the nonce epoch counter live in internal flash — no external NVM on the board). Software AEAD assumed — don't rely on hw AES. Alternates: STM32U073KCU6 (C22445363, 90 — exact 32-pin sibling of ephemerkey's part, thin stock); **STM32U575VGT6 (C5270988, 17 k)** / U575RGT6 (C5270980, 345) — calcumaker-shared U5 headroom path if Sora outgrows the M0+; STM32G0B1KBU6 (C5159549, 2.6 k, 3 repos) — non-ULP cost fallback. |
| Radio | **E22-900M22S** (SX1262) | C411293 | 789 | JLCPCB-assemblable directly — no consignment needed. |
| Charger | **BQ24650RVAR** (VQFN-16) | C53712 | 557 | Solar-MPPT synchronous buck controller, VIN 5–28 V → raw panel **and** 9–16 V DC; float programmable down to 2.1 V → **2.85 V 1S-LTO** divider-set (revised 2026-07; the only topology that reaches an LTO float — integrated 1-cell chargers stop at 3.0 V). RVAT sibling C2876745; deep DigiKey stock backs the thin LCSC count. CN3722 (C77905, 5.3 k) = revert-to-2s fallback only. |
| Fuel gauge | **BQ34Z100PWR-G1** (TSSOP-14) | C91302 | 3 k | Multi-chemistry Impedance Track gauge — **officially supports LTO** (MAX17048/17055 don't); low-side sense, I²C SoC/SoH into the Nami packet. Second always-on load beside the AS3935 (~2–3 mAh/day). VCC from the 3.3 V rail; verify LTO ChemID at bring-up. |
| Battery | 1S **LTO** cell (holder/leads, off-BOM) | — | — | 2.4 V nom, 1.8–2.9 V (revised 2026-07 from 2s: no balancing, gauge-friendly); charges below freezing, huge cycle life — right chemistry for permanently-outdoor solar. |
| 3V3 rail | **TPS63900DSKR** buck-boost | C1518762 | 4.2 k | 75 nA Iq, VIN 1.8–5.5 V spans the 1S-LTO range (2.4 V nom is *below* 3.3 V — buck-only TPS62840 no longer works); ~400 mA covers E22 TX, derate at pack floor. |
| Storage | *(none — internal flash)* | — | — | Outage readings buffer in the U073's internal flash (128 K is plenty; wear only during link loss) and the nonce epoch counter is 1 flash write per boot. FRAM (e.g. MB85RS64PNF, C8741) was considered and **dropped 2026-07** — nothing needs per-packet NVM writes; re-add only if that changes. |
| T/RH | **SHT40-AD1B-R2** | C2909890 | 8.8 k | On-board (Kumo function), I²C, load-switched. |
| Pressure | **BMP390** | C5124834 | 1.3 k | On-board, I²C. |
| Light | **VEML7700-TT** | C1850416 | 3.2 k | Ambient lux (Hikari); dedicated UV sensor TBD. |
| VOC (opt.) | SGP40-D-R4 | C2874215 | 1.6 k | Optional on-board air-quality proxy; PM stays off-board. |
| Input TVS | SMBJ26A | C908802 | 39 k | Clamps 12 V-system transients at the DC input. |
| Mast bus xcvr | **MAX3471EUA+T** | C27462 | 11 k | Micropower RS-485 (1.6 µA listening) — one on Sora, one per pod. |
| Bus V+ switch | **TPS22919DCKR** | C2149796 | 1.5 k | Gates bus/pod power on the RTC schedule (also gates SPS30 + AS5600 on pods). |
| Bus TVS | **SM712** | C521963 | 327 k | RS-485-profile ±12/−7 V clamp on A/B at every node. |
| SPS30 header | **S5B-ZR(LF)(SN)** (JST ZH-5, side entry) | C265404 | 13 k | Mates the off-BOM Sensirion SPS30 pigtail (pod PCB). |
| Vane sensor | **AS5600-ASOT** (pod option) | C499458 | 37 k | Contactless 12-bit vane angle; MT6701 (C3003196) alternate. |
| Lightning | **AS3935** + **Premo SDTR1103-HF1-0100J** coil | — (off-BOM) | — | Storm detection to ~40 km; only always-on sensor (~70 µA). Coil: 100 µH ±5 %, Q45 @ 0.5 MHz (damped to ~15), purpose-made for lightning detectors; MA5532 obsolete. |
| UV | **LTR-390UV-01** | C492374 | 1.2 k | UV-A + ALS with UV-index output, I²C; GUVA-S12SD + TIA cost-down. Board also carries a **DNP AS7331 footprint** (OLGA-16, C20482877) as the spectral-UV upgrade option. |
| Sky IR | **MLX90614ESF-BCC** | C7501763 | 704 | Zenith cloud/fog sensing (35° FOV, 3 V, gradient-comp), I²C load-switched. |
| Hail comparator | **TLV7031DBVR** | C2869832 | 3.6 k | 315 nA comparator for the piezo impact channel (disc off-BOM). |

### Power architecture (flexible input — requirement)

Two charge sources, one battery:

1. **Raw solar panel** (6–18 V panels) — BQ24650's input-voltage-regulation
   loop provides MPPT against panel collapse.
2. **DC input up to 16 V** (12 V lead-acid/LiFePO₄ battery systems) — same
   charger input via ORing diodes + reverse-polarity FET + SMBJ26A TVS
   (28 V-max charger leaves headroom for 12 V-system transients).

Battery is **1S LTO** (revised 2026-07 from 2s — kills the balancing
question entirely and enables a real fuel gauge): float ≈ 2.85 V
resistor-set, working range ~1.8–2.9 V, 2.4 V nominal. LTO stays the
chemistry — sub-zero charge acceptance and cycle life are why it was picked
over LiFePO₄, and no integrated 1-cell charger reaches a 2.85 V float
(BQ25798-class parts bottom out at VREG = 3.0 V), which is what forces the
discrete controller:

- **Charger: BQ24650** (promoted from alternate to primary) — synchronous
  buck charge controller *designed for solar MPPT*, VIN 5–28 V covers both
  inputs, and its feedback reference lets the float be programmed down to
  2.1 V, so a 2.85 V 1S-LTO float is just a divider. CN3722 is demoted to
  the revert-to-2s fallback; LT3652 drops out entirely (3.3 V minimum float
  can't reach 1S LTO).
- **Fuel gauge: BQ34Z100-G1** — the only stocked gauge that *officially
  supports LTO chemistry* (Impedance Track with LTO ChemIDs; MAX17048/17055
  are Li-ion-OCV parts whose supply ranges don't even survive LTO's 1.8 V
  floor). Chemistry-independent low-side sense resistor, I²C, reports
  SoC/SoH/current/temp — SoC goes in the Nami packet. Honest cost: a gauge
  must integrate 24/7, so this is the **second always-on load** beside the
  AS3935 (~tens of µA in its sleep modes, ~100 µA tracking) ≈ 2–3 mAh/day —
  acceptable against a multi-Ah 1S cell and any real panel. Bring-up items:
  power its VCC/REGIN from the 3.3 V rail (not the 2.4 V pack), verify the
  chosen LTO ChemID against the actual cell, tune sleep-mode strategy.
- **3.3 V rail: TPS63900 buck-boost** (replaces the TPS62840 buck — a 2.4 V
  nominal pack sits *below* the rail, so buck-only no longer works). VIN
  1.8–5.5 V spans the whole 1S-LTO range, 75 nA Iq keeps the
  sleep budget, ~400 mA output covers E22 TX peaks (+22 dBm ≈ 110 mA;
  derate near the 1.8 V pack floor — fine at our +14 dBm start; give it
  generous bulk capacitance).
- The E22 module and everything else run from the 3.3 V rail; the pack
  voltage (≤2.9 V) is never railed anywhere directly.
- **Mast bus V+ becomes the gated 3.3 V rail**, not raw pack — 1S LTO
  (1.8–2.9 V) is below the MAX3471's 2.5 V minimum, so bus V+ is now the
  TPS22919-switched 3.3 V. Pods needing 5 V (SPS30) boost locally, as
  already planned. Power-pack mode is unchanged.

### Sensor split (kept flexible — requirement)

- **On Sora proper:** temp/RH (SHT40), pressure (BMP390), light (VEML7700),
  optional VOC (SGP40) — the sheltered, radiation-shield-adjacent set.
- **Pulse port (RJ11-style):** classic reed anemometer + tipping-bucket rain
  — zero-power contacts into LPTIM/EXTI, debounced in firmware.
- **Mast bus:** a switched-power RS-485 multidrop chain for **smart pods** —
  wind (Kaze) and/or particulate air quality combined or separate. Pods, if
  they get their own MCU, use fleet part **STM32G031K8U6** /
  **STM32G030F6P6** class (calcumaker/tsumikoro small-G0 precedent; the
  U031C8T6, C23172783, 1.5 k stock, is the U0-family option).

Whether wind + air quality share one pod or split into two is deferred — the
bus is the stable interface either way (same connector, addressable
protocol).

### Mast bus — pod interlink (decided direction, 2026-07)

Requirements: pods may **chain over short wires**, may be powered by Sora
**or by a wired power pack**, must survive outdoor exposure, and must burn
**no idle power on the bus**.

**Design: 4-wire switched-power RS-485 daisy-chain** — V+, GND, and an
A/B differential pair; every pod has an in + out connector (or a T-splice).

- **Transceiver: MAX3471** (C27462, 11 k stock) on every node including
  Sora — a micropower half-duplex RS-485 built for battery multidrop:
  **1.6 µA quiescent with the receiver listening**, 2.5–5.5 V supply, up to
  64 kbps, 64 nodes. 9.6–38.4 kbaud Nami-framed (same CRC/auth style as the
  radio protocol), Sora as polling master.
- **Zero idle power, two modes:**
  1. *Sora-powered chain:* Sora gates bus V+ — the **3.3 V rail** since the
     1S-LTO move (raw pack at 1.8–2.9 V is below the MAX3471's 2.5 V min) —
     with a **TPS22919** load switch (C2149796) on its RTC schedule; between
     samples the entire chain is unpowered: **exactly zero idle**, no
     transceiver spec needed.
  2. *Power-pack-powered chain:* pods fed continuously from the pack idle in
     STOP with the MAX3471 receiver listening (~2 µA/node) and wake on bus
     traffic. ORing/ideal diodes on each pod let pack and Sora V+ coexist
     without backfeed.
- **Durability:** differential signalling tolerates long wet cable runs;
  **SM712** RS-485-profile TVS (C521963, 327 k stock, ±12/−7 V asymmetric)
  on A/B at every node, SMBJ clamp on V+, fail-safe biasing at Sora.
  Field-side connectors are off-BOM (IP67 M8 4-pin or cable glands —
  open question); PCB side is ordinary headers/screw terminals.
- **Why not the alternatives:** I²C doesn't survive cable runs; CAN adds
  controller complexity and higher standby; LIN wants a 12 V rail; 1-Wire is
  too slow/fragile for PM data. RS-485 is multidrop-native and the MAX3471
  makes it micropower.

### PM2.5 — Sensirion SPS30 (optional pod sensor, decided 2026-07)

The **Sensirion SPS30** is the supported PM2.5/PM10 option. It's off-BOM
(source from DigiKey/Mouser — doesn't need to come from JLCPCB), but the pod
PCB **carries its mating header**: the SPS30 pigtail is **JST ZH 5-pin**, so
populate a genuine JST **S5B-ZR(LF)(SN)** side-entry shrouded header
(C265404, 13 k stock at LCSC; SMD variant S5B-ZR-SM4A-TF, C485355).

- Pinout (SPS30): 1 VDD 5 V, 2 RX/SDA, 3 TX/SCL, 4 SEL (GND → I²C, float →
  UART), 5 GND. **Use UART** — Sensirion only rates I²C for very short
  traces.
- Power: 4.5–5.5 V, ~55 mA measuring, <8 mA idle — the pod gates it with its
  own TPS22919 and duty-cycles measurements; a small 5 V boost on the pod
  makes it work from either bus V+ (the gated 3.3 V rail since the 1S move)
  or the power pack.
- Logic is 3.3 V-compatible (5 V-tolerant inputs on the SPS30 side).

### Wind vane + rain — scoping (2026-07)

Two supported vane paths, both zero/near-zero idle:

1. **Commodity resistor-ladder vane** (Misol/Davis WH-SP class, 8 reeds /
   16 headings, shares the anemometer RJ11): excite the divider from a GPIO
   **only during the ADC sample** — zero idle by construction. Coarse
   (22.5°) but proven and cheap.
2. **Contactless magnetic vane** on the Kaze pod: **AS5600** 12-bit I²C
   angle sensor (C499458, 37 k stock; MT6701, C3003196, as alternate) with a
   diametral magnet on the vane shaft — 0.1°-class, no contacts to wear,
   ~6 mA while powered so it lives behind the pod's load switch and is
   sampled, not left running.

Anemometer + rain gauge stay **dumb reed pulses** into Sora's pulse port:
LPTIM counts in STOP mode, so gust capture is continuous at negligible cost —
use a high-value (≥1 MΩ) pull-up so a stuck-closed reed leaks single-digit
µA, plus RC + TVS on the port (long exposed wires). A heated rain gauge, if
ever, is power-pack-only territory.

### Atmospheric extras (locked in 2026-07)

Four additional measurements are part of the platform:

**Lightning — AS3935 (ScioSense) + 100 µH antenna coil.** Detects strokes
to ~40 km with storm-distance estimation. Both parts are **off-BOM**
(DigiKey/Mouser — not in the JLCPCB library); footprints go on the Sora
board. The classic **Coilcraft MA5532 is obsolete** (2026); the antenna
requirement per the AS3935 Hardware Design Guide is **100 µH, Q trimmed to
~15** (10 kΩ parallel damping), parallel-resonant at 500 kHz.

**Production coil: Premo SDTR1103-HF1-0100J** (datasheet-verified 2026-07):
100 µH **±5 %**, **Q = 45 ±5 % specified at 0.5 MHz** (damp to ~15 with the
10 kΩ), SMD 11.8 × 3.6 × 2.5 mm ferrite-laminate coil with plastic base,
drop-tested >500 × 1 m, −40…+85 °C, AEC-Q200, T&R 3000/reel — Premo's
stated application is "RF reception at 500 kHz" and the series page is
literally titled *"for lightning detector."* In production and tighter
tolerance than the MA5532 ever was. **The plan of record is the Premo for
all builds, protos included** — order via Premo direct or DC Electronic
Solutions (US rep); it exists at no major distributor (checked 2026-07), so
treat it as a consigned/hand-placed part like the AS3935 itself. (Bench-only
fallbacks if an order stalls: Mouser's MA5532-AEB residual or coil-harvest
from a CJMCU-3935/DFRobot module.) Design invariants:

- It is the **only always-on sensor**: listening mode ≈ 70 µA (~230 µW) —
  budgeted; its IRQ wakes the U073 from STOP, so firmware stays asleep.
  Firmware may disable it below a battery floor.
- **Placement is critical**: the AS3935 false-triggers on switching-converter
  noise. Keep it and the coil far from the BQ24650 and TPS63900, feed it from
  a quiet RC-filtered rail or its own small LDO, and keep the coil clear of
  the SX1262 antenna path (500 kHz vs 915 MHz — different worlds, but the
  coil is still a magnetic pickup).
- Antenna tuning (internal caps, ±3.5 % target) is a per-board calibration
  step — note it in the bring-up checklist.

**UV — LTR-390UV-01 primary, GUVA-S12SD cost-down (Hikari function).** The
Lite-On **LTR-390UV-01** (LCSC **C492374, 1.2 k stock — JLCPCB-assemblable**;
also ships-today at DigiKey) does UV-A + ALS with direct UV-index output
over I²C, µA-class standby. (Earlier searches missed it — the library lists
the exact hyphenated MPN.) Budget alternate: **GUVA-S12SD** photodiode
(off-BOM) into a TIA op-amp → U073 ADC. The ams **AS7331** (true spectral
UVA/UVB/UVC) is **hard to source in 2026**, but **the board must carry its
footprint (OLGA-16) as a DNP alternate stuffing option** — same I²C bus, so
if supply recovers a premium spectral-UV variant is a stuffing change, not a
respin. VEML6075/SI1145 are discontinued.

**Sky IR thermometer / cloud cover — MLX90614ESF-BCC** (C7501763, 704 in
stock — JLCPCB-assemblable). Zenith-pointed, narrow-FOV (35°),
gradient-compensated, 3 V variant: clear sky reads 20–40 °C below ambient,
overcast reads near-ambient → cloud-fraction estimate, and with the SHT40
dew point, fog prediction. I²C, sleeps to µA, load-switched with the sensor
rail. Needs a sky-facing window in the enclosure (IR-transparent or open
port under a hood).

**Hail / rain impact — piezo disc + TLV7031 comparator.** A generic piezo
disc (off-BOM, cents) bonded under an impact plate, into a **TLV7031DBVR**
nanopower comparator (C2869832, 3.6 k stock, 315 nA) → EXTI/LPTIM pulse
counting in STOP. Impact energy discriminates hail from heavy rain and gives
a rain-intensity proxy independent of the tipping bucket. Threshold set by
resistor divider; two comparator levels (rain/hail) if a second TLV7031 is
stuffed.

**Indoor CO₂ on Hashi — SCD40** (C3659421, 1.2 k stock, JLCPCB-assemblable):
the bridge is always-on USB-powered indoors, so Sensirion SCD40 CO₂ +
temp/RH costs nothing power-wise and makes Hashi a sensor node in its own
right (published over the same MQTT).

Parked (surveyed 2026-07, not in rev A): TSL2591 night-sky brightness
(astro pod with the MLX90614), VL53L1 ToF snow depth (experimental on snow;
ultrasonic JSN-SR04T-class is the proven alternative), capacitive
soil-moisture / leaf-wetness garden pods.

### Hashi variants

| Variant | MCU | Network | LCSC | Stock |
|---|---|---|---|---|
| Primary | **ESP32-S3-WROOM-1-N8R2** | Wi-Fi | C2913204 | 17.8 k |
| Ethernet backup | **STM32H563VGT6** | integrated MAC + **LAN8742A-CZ-TR** RMII PHY | C18221950 / C621424 | 8 k / 2.6 k |

Both carry the same E22-900M22S (C411293) radio + USB-C power + console,
plus an **SCD40** CO₂/T/RH sensor (C3659421, 1.2 k stock) for indoor air.

## Open questions

- ~~**Sora MCU**~~ — **resolved 2026-07: STM32U073CBT6** (U0 family shared
  with ephemerkey; U575VGT6 documented as the headroom alternate). See
  platform sketch.
- ~~**Hashi backup MCU (wired Ethernet)**~~ — **resolved 2026-07:
  STM32H563VGT6 + LAN8742A** (WIZnet ruled out by decision; supersedes the
  survey's RP2350+W5500 pick). See the Hashi section.
- ~~**Solar charger part**~~ — **revised 2026-07: BQ24650** MPPT promoted to
  primary for the **1S LTO** move (2.85 V float; adds BQ34Z100-G1 fuel gauge,
  TPS63900 buck-boost rail; CN3722 = revert-to-2s fallback, LT3652 dropped);
  **panel sizing** for the 1S cell still open.
- **Wind/air-quality pod split** — one combined mast pod vs separate Kaze +
  air-quality pods (the mast bus is the fixed interface either way).
  ~~PM sensor~~ — **resolved: Sensirion SPS30 as the supported option**
  (off-BOM, JST ZH-5 header on the pod).
- **Vane mechanics** — resistor-ladder RJ11 vane vs AS5600 contactless pod
  vane (both electrically supported; pick per product tier / mechanics).
- **Field connector family for the mast bus** — IP67 M8 4-pin vs glands +
  pigtails (off-BOM either way).
- ~~**UV sensor**~~ — **resolved 2026-07: LTR-390UV-01** (C492374,
  JLCPCB-stocked), GUVA-S12SD as cost-down stuffing; AS7331 parked
  (unsourceable); VEML7700 covers lux.
- ~~**AS3935 coil sourcing**~~ — **resolved 2026-07: Premo
  SDTR1103-HF1-0100J** (100 µH ±5 %, Q45 @ 0.5 MHz, in production,
  purpose-made for lightning detectors). **Channel reality (checked
  2026-07): no 100 µH lightning coil exists at JLCPCB or DigiKey at all**
  (DigiKey returns zero results for SDTR1103 *and* MA5532; Coilcraft's
  active 4513TC family is 1–7.25 mH RFID values only). **Plan of record:
  Premo for all builds** — order via Premo direct / DC Electronic Solutions
  (US rep), consigned/hand-placed on JLCPCB builds, same as the AS3935.
  Remaining action: place the Premo order early (direct-channel lead time is
  the risk, not availability).
- **AS3935 bring-up** — antenna-coil tuning (±3.5 %) and noise-floor
  calibration next to the real board; verify the quiet-rail strategy.
- **Enclosure sky ports** — sky-facing window/hood for MLX90614 + UV, and
  the hail impact plate's mechanical mount.
- **LTO cell format** — 1S (2026-07): which cell (18650-LTO vs pouch vs
  Toshiba SCiB-class), capacity, holder vs tabbed. Balancing is no longer a
  question — 1S killed it; protection is just the charger float + gauge
  undervoltage alarm.
- ~~**Nami crypto**~~ — **decided 2026-07**: Ascon-128a AEAD with a cipher-suite
  byte for agility (ChaCha20-Poly1305 reserved as suite 0x02); PSK-per-pairing
  + HKDF direction keys; epoch-counter nonces in internal flash (no FRAM —
  dropped). See "Nami → Security".
- **Enclosure / radiation shield** for Sora.
