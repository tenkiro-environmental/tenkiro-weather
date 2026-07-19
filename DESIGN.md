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

### `tenkiro-hashi` — indoor bridge

- E22-900M22S (SX1262) radio module — same radio as Sora for rev A
- **Primary MCU: ESP32-S3** (Wi-Fi; ESP32-S3-WROOM-1 module)
- **Backup option (wired Ethernet, non-ESP32): STM32H563VGT6 + LAN8742A
  RMII PHY** — decided 2026-07 (see below)
- USB-C power
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
                                       Kaze/Ame pulse port ─┘      └─ mast module port
                                       (reed anemometer / rain     (power-gated 3V3/5V +
                                        tipping bucket, RJ11)       UART/RS-485: smart wind
                                                                    and/or air-quality pod)
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
- **Mast module port:** power-gated 3V3/5 V + UART (RS-485 option for long
  runs) for a **smart pod** — wind (Kaze) and/or particulate air quality
  combined or separate; PM sensors (SPS30/PMSx003 class) are UART-native.
  Smart pods, if they get their own MCU, use fleet part **STM32G031K8U6** /
  **STM32G030F6P6** class (calcumaker/tsumikoro small-G0 precedent).

Whether wind + air quality share one pod or split into two is deferred — the
port is the stable interface either way (same connector, addressable
protocol).

### Hashi variants

| Variant | MCU | Network | LCSC | Stock |
|---|---|---|---|---|
| Primary | **ESP32-S3-WROOM-1-N8R2** | Wi-Fi | C2913204 | 17.8 k |
| Ethernet backup | **STM32H563VGT6** | integrated MAC + **LAN8742A-CZ-TR** RMII PHY | C18221950 / C621424 | 8 k / 2.6 k |

Both carry the same E22-900M22S (C411293) radio + USB-C power + console.

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
  air-quality pods (port interface is fixed either way); pick the PM sensor.
- **UV sensor** — VEML7700 covers lux; a UV-index part is still open
  (LTR-390UV had no JLCPCB stock 2026-07).
- **LTO pack format** — cell format (18650/pouch), holder vs tabbed, 2s
  balancing/protection approach.
- **Nami crypto** — pick the AEAD (e.g. AES-CCM vs ChaCha20-Poly1305) and key
  provisioning story.
- **Enclosure / radiation shield** for Sora.
