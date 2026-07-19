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
- battery voltage, solar voltage/current
- temperature, humidity, pressure
- wind speed, wind gust, wind direction
- rain counter, light/UV
- lightning: cumulative stroke counter + last-storm distance (2026-07 add)
- hail/impact: cumulative counter (2026-07 add)
- sky IR temperature (cloud cover; 2026-07 add)
- status flags, CRC or authentication tag

Design rules:

- Fixed-width binary encoding — never JSON over the air.
- Sequence numbers for duplicate detection.
- **Cumulative** rain and wind counters so one lost packet doesn't destroy the
  measurement.
- Acknowledgments only when needed.
- A unique device key and **authenticated encryption**.
- Periodic bridge-to-node clock correction.
- Local flash buffering on Sora during extended link loss.

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
- **LTO cells** (lithium-titanate; wide-temperature outdoor chemistry —
  supersedes the brief's LiFePO₄) + **flexible charge input**: raw solar
  panel **or** up to 16 V DC (12 V battery system)
- Low-quiescent-current solar/MPPT charger with resistor-set LTO float
- Load switches for the sensor rails
- FRAM for buffered readings
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
                      CN3722 MPPT charger                      │
                      (float ≈ 5.5 V, 2s LTO)        ┌─────────┴───────────┐
                             │                       │  STM32U073CBT6      │
                      2s LTO pack (4.8 V nom,        │  (LQFP-48, ULP M0+) │
                      3.6–5.7 V; −30 °C charge OK)   │                     │
                             │                       │ SPI0: E22-900M22S ──┼── U.FL ant
                      TPS62840 buck → 3.3 V          │ SPI1: MB85RS64 FRAM │
                      (750 nA Iq, VIN ≤ 6.5 V)  ─────┤ ADC: Vbat/Vsolar    │
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
| MCU | **STM32U073CBT6** (LQFP-48, M0+, 128 K/40 K) | C27035627 | 1,009 | Same STM32U0 family as ephemerkey's U083KCU6 (U083 ≈ U073 + LCD driver) — fleet firmware experience carries over; ST ULP line (sub-µA stop w/ RTC, LPUART/LPTIM); right-sized and cheap for a sleep-mostly node (radio + FRAM share one SPI bus, separate CS; buffering lives in FRAM). Software AEAD assumed — don't rely on hw AES. Alternates: STM32U073KCU6 (C22445363, 90 — exact 32-pin sibling of ephemerkey's part, thin stock); **STM32U575VGT6 (C5270988, 17 k)** / U575RGT6 (C5270980, 345) — calcumaker-shared U5 headroom path if Sora outgrows the M0+; STM32G0B1KBU6 (C5159549, 2.6 k, 3 repos) — non-ULP cost fallback. |
| Radio | **E22-900M22S** (SX1262) | C411293 | 789 | JLCPCB-assemblable directly — no consignment needed. |
| Charger | **CN3722** (TSSOP-16) | C77905 | 5.3 k | Solar MPPT controller, VIN to 28 V → handles raw panel **and** 9–16 V DC; resistor-set float ≈ 5.5 V for 2s LTO. Alternates: BQ24650RVAR (C53712, 557) same topology w/ TI docs; LT3652IMSE (C671115, 2.9 k). |
| Battery | 2s **LTO** pack (holder/leads, off-BOM) | — | — | 4.8 V nom, 3.6–5.7 V; charges below freezing, huge cycle life — right chemistry for permanently-outdoor solar. |
| 3V3 rail | **TPS62840DLCR** buck | C2071859 | 5.5 k | 750 nA Iq, VIN 1.8–6.5 V spans the 2s-LTO range; 750 mA covers E22 TX peaks. |
| Storage | **MB85RS64PNF** FRAM (SOP-8 SPI) | C8741 | 6.4 k | Unlimited-endurance buffered readings during link loss. |
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
| UV | **LTR-390UV-01** | C492374 | 1.2 k | UV-A + ALS with UV-index output, I²C; GUVA-S12SD + TIA cost-down; AS7331 parked (unsourceable 2026). |
| Sky IR | **MLX90614ESF-BCC** | C7501763 | 704 | Zenith cloud/fog sensing (35° FOV, 3 V, gradient-comp), I²C load-switched. |
| Hail comparator | **TLV7031DBVR** | C2869832 | 3.6 k | 315 nA comparator for the piezo impact channel (disc off-BOM). |

### Power architecture (flexible input — requirement)

Two charge sources, one battery:

1. **Raw solar panel** (6–18 V panels) — CN3722's input-voltage-regulation
   loop provides MPPT against panel collapse.
2. **DC input up to 16 V** (12 V lead-acid/LiFePO₄ battery systems) — same
   charger input via ORing diodes + reverse-polarity FET + SMBJ26A TVS
   (28 V-max charger leaves headroom for 12 V-system transients).

Battery is **2s LTO** (float ≈ 2.75 V/cell → 5.5 V, resistor-set): chosen
over LiFePO₄ for sub-zero charge acceptance and cycle life; the capacity
penalty is acceptable for a ~mW-average node. The 3.3 V system rail
(TPS62840) spans the full 3.6–5.7 V pack range; the E22 module runs from the
3.3 V rail (its 5.7 V-charging pack peak would exceed the module's 5.5 V max,
so never rail it to VBAT).

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
  1. *Sora-powered chain:* Sora gates bus V+ with a **TPS22919** load switch
     (C2149796) on its RTC schedule — between samples the entire chain is
     unpowered: **exactly zero idle**, no transceiver spec needed.
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
  own TPS22919 and duty-cycles measurements; a small 5 V buck-boost on the
  pod makes it work from either bus V+ (3.6–5.7 V LTO span) or the power
  pack.
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
tolerance than the MA5532 ever was. Source via Premo/reps (DC Electronic
Solutions in the US; DigiKey carries Premo marketplace listings) — off-BOM
like the AS3935 itself. Proto fallbacks: residual MA5532-AEB at Mouser, or
coil-harvest from CJMCU-3935/DFRobot modules. Design invariants:

- It is the **only always-on sensor**: listening mode ≈ 70 µA (~230 µW) —
  budgeted; its IRQ wakes the U073 from STOP, so firmware stays asleep.
  Firmware may disable it below a battery floor.
- **Placement is critical**: the AS3935 false-triggers on switching-converter
  noise. Keep it and the coil far from the CN3722 and TPS62840, feed it from
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
UVA/UVB/UVC) was the original pick but is **hard to source in 2026** — parked
as a premium variant if supply recovers; VEML6075/SI1145 are discontinued.

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
- ~~**Solar charger part**~~ — **CN3722** MPPT (BQ24650/LT3652 alternates);
  **panel sizing** for the 2s LTO pack still open.
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
  active 4513TC family is 1–7.25 mH RFID values only). Order the Premo part
  via Premo direct / DC Electronic Solutions (US rep); the only
  major-distributor listing is **Mouser's MA5532-AEB residual** (verify live
  stock in a browser — Mouser blocks bots) — fine for protos. The coil is a
  consigned/hand-placed part on JLCPCB builds either way, same as the
  AS3935.
- **AS3935 bring-up** — antenna-coil tuning (±3.5 %) and noise-floor
  calibration next to the real board; verify the quiet-rail strategy.
- **Enclosure sky ports** — sky-facing window/hood for MLX90614 + UV, and
  the hail impact plate's mechanical mount.
- **LTO pack format** — cell format (18650/pouch), holder vs tabbed, 2s
  balancing/protection approach.
- **Nami crypto** — pick the AEAD (e.g. AES-CCM vs ChaCha20-Poly1305) and key
  provisioning story.
- **Enclosure / radiation shield** for Sora.
