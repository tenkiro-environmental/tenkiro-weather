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
│ solar + LiFePO₄         │                          │ MQTT / HTTP / local DB│
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

- Ultra-low-power MCU (part TBD — open question)
- E22-900M22S (SX1262) radio module
- External 915 MHz antenna (U.FL)
- LiFePO₄ cell + small solar panel
- Low-quiescent-current solar charger
- Load switches for the sensor rails
- FRAM or low-power flash for buffered readings

### `tenkiro-hashi` — indoor bridge

- E22-900M22S (SX1262) radio module — same radio as Sora for rev A
- **Primary MCU: ESP32-S3** (Wi-Fi; obvious, well-supported choice)
- **Backup option (wired Ethernet, non-ESP32): RP2350A + WIZnet W5500** —
  decided 2026-07 (see below)
- USB-C power
- MQTT client + local web interface
- Optional USB serial console

#### Hashi Ethernet-backup variant — RP2350A + W5500 (decided 2026-07)

Survey of non-ESP32 wired-Ethernet options (LCSC prices/stock verified
2026-07):

- **★ RP2350A + WIZnet W5500 (SPI) — chosen.** The only combo where both
  chips are deep-stocked, cheap, JLCPCB-assemblable (RP2350A ~$1.45 @1k,
  8.6k stock, LCSC C42411118; W5500 ~$1.76 @1k, 51k stock, C32843 — ~$3.20
  silicon/board + QSPI flash), **and** the Ethernet interface collapses to
  plain SPI — no RMII routing, no 50 MHz clock tree, just a 25 MHz crystal
  and an RJ45 with magnetics. The W5500 is a hardwired TCP/IP controller
  (10/100 MAC+PHY + 8 offloaded sockets), but its **MACRAW mode** exposes raw
  L2 frames, so an external stack can drive it instead. Firmware is
  first-class in both languages: embassy-Rust via `embassy-net-wiznet`
  (MACRAW → embassy-net TCP/UDP/DHCP/DNS) + `embassy-rp`, and pico-sdk C via
  WIZnet's ioLibrary (MQTT + HTTP server examples). PoE remains possible as
  an external PD add-on into the 5 V rail. Gotchas: RP2350 A2-stepping **E9
  GPIO-pulldown erratum** — use external pulls on strapping/interface pins;
  keep W5500 SPI ≤ ~33–40 MHz.
- **Runner-up: STM32H723 + LAN8742A RMII PHY.** Best single-chip-MAC firmware
  maturity (STM32 HAL + lwIP; `embassy-stm32` eth works), but LCSC stock is
  thin/expensive (STM32H563 was ~35 pcs), LAN8742A is chronically hard to
  source (and the cheap LAN8720A carries notorious REF_CLK/strapping
  bring-up traps), and RMII is the hardest layout of the group.
- **Rejected: WCH CH32V307** — integrated PHY is 10Base-T only (100M needs an
  external PHY, forfeiting its advantage), and Rust/embassy Ethernet support
  is unimplemented (`ch32-hal` issue #11), which would fracture the firmware
  codebase.
- **Rejected: Microchip SAME54 / Nuvoton M467** — need an external RMII PHY
  anyway, with weaker LCSC stock and smaller ecosystems than the STM32 path.

## Open questions

- **Sora MCU** — ultra-low-power part not yet chosen.
- ~~**Hashi backup MCU (wired Ethernet)**~~ — **resolved 2026-07:
  RP2350A + WIZnet W5500 (SPI)**; runner-up STM32H723 + LAN8742A. See the
  Hashi section.
- **Sensor set / module split** — which of Kumo/Kaze/Ame/Hikari are on-board
  vs. plug-in modules for rev A.
- **Solar charger part** and panel sizing for the LiFePO₄ cell.
- **Nami crypto** — pick the AEAD (e.g. AES-CCM vs ChaCha20-Poly1305) and key
  provisioning story.
- **Enclosure / radiation shield** for Sora.
