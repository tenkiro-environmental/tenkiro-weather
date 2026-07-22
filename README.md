# Tenkiro

**Tenkiro** is a private-radio home weather system:

- **Tenkiro Sora** — a solar-powered outdoor weather station (1S LTO cell
  with fuel gauge, charged from raw solar or a 12 V system, STM32U073
  ultra-low-power MCU, Semtech SX1262 915 MHz LoRa radio).
- **Tenkiro Hashi** — an always-on indoor bridge between the radio link and
  your network (USB-C powered, MQTT + local web interface; ESP32-S3, with a
  wired-Ethernet backup variant on STM32H563 + LAN8742A).
- **Nami** — the small private point-to-point LoRa protocol they speak:
  fixed-width binary packets, sequence numbers, cumulative counters,
  authenticated encryption. Deliberately **not** LoRaWAN.

*Sora speaks Nami to Hashi.*

## Layout

| Path | Contents |
|---|---|
| `DESIGN.md` | The design document — decisions, part choices, protocol, open questions. **Start here.** |
| `NAMING.md` | Naming hierarchy (Tenkiro / Sora / Hashi / Nami / …). |
| `hardware/` | KiCad 10 projects `tenkiro-sora` + `tenkiro-hashi`, shared `lib/`, Makefile-driven tooling (docs, BOMs, JLCPCB packages). |
| `reference/` | Datasheet + dependency pointers. |
| `doc/` | Working notes and reviews. |

Hardware tooling mirrors the sibling BenchBits repos (`calcumaker` et al.):
from `hardware/`, `make help` lists the doc/BOM/fab targets.

## Status

Early design capture (2026-07). Radio architecture, the Nami protocol
(Ascon-128a AEAD with cipher agility), the hardware platform (Sora:
STM32U073 + BQ24650 1S-LTO charging with BQ34Z100 fuel gauge; Hashi:
ESP32-S3 / STM32H563 + LAN8742A
Ethernet backup), and JLCPCB part picks are settled; the wind/air-quality
pod split, mechanical choices (vane, mast-bus connector, enclosures), and
LTO pack format are open — see `DESIGN.md` → Open Questions.

## License

Firmware: **AGPL-3.0** (`LICENSE`). Hardware: **CERN-OHL-S v2**
(`hardware/LICENSE`).
