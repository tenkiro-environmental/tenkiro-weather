# Claude Code Assistant Guidelines — Tenkiro

Repo `tenkiro`; a private-radio home **weather system** (see `NAMING.md`):
**Sora**, a solar-powered outdoor weather station, speaks the **Nami** protocol
(915 MHz LoRa, Semtech SX1262 via the Ebyte E22-900M22S SPI module) to
**Hashi**, an always-on indoor bridge (USB-C powered, MQTT + local web UI).
Two PCBs: `hardware/tenkiro-sora` and `hardware/tenkiro-hashi`. Not LoRaWAN —
a small private point-to-point protocol with authenticated encryption. This
repo holds the KiCad hardware (`hardware/`), future firmware (`firmware/`),
the design doc (`DESIGN.md`), naming (`NAMING.md`), and references
(`reference/`). Tooling mirrors the sibling `calcumaker` repo exactly.

## General Rules
- Do not run `cat` or `stty` commands.
- Do not read debug messages from the serial port — ask the user to do that.
- Use Makefile targets when possible.
- This is a **KiCad 10** project — use `kicad-cli` for schematic/PCB operations.
- Use `uv` for all Python operations (never bare `pip`).
- **Don't assume** final part choices that are still open (wind/AQ pod split,
  PM + UV sensors, LTO pack format, panel sizing, Nami AEAD). Source of truth
  is `DESIGN.md` → Open Questions. **No WIZnet parts** (2026-07 decision).

## Source of truth
- **`DESIGN.md`** — full system design: radio choice (SX1262 / E22-900M22S,
  why not E220/LLCC68, why not 30 dBm PA modules), Nami packet layout + link
  settings, antenna rules, rev-A board outlines, and the **Open Questions**.
- `reference/README.md` — dependency + datasheet pointers.
- Per-sheet **on-canvas notes** in the schematic carry the wiring/pin spec.

## Hardware (KiCad 10) — two boards, radio-linked
- `hardware/tenkiro-sora/` — outdoor station: **STM32U073CBT6** (U0 family
  shared with ephemerkey), E22-900M22S radio, U.FL antenna, **2s LTO** pack
  charged by CN3722 MPPT from raw solar **or** 9–16 V DC (12 V battery
  systems), TPS62840 3.3 V rail, load switches for sensor rails, MB85RS64
  FRAM buffering. On-board temp/RH/pressure/light; reed wind/rain on the
  pulse port; smart pods (wind vane / SPS30 PM2.5) on the **mast bus** — a
  4-wire switched-power RS-485 chain (MAX3471 micropower transceivers,
  SM712 TVS per node). **Power budget is sacred**: Sora sleeps almost always
  (wake → sample → TX → short ACK window → sleep), and the mast bus must
  burn **zero idle power** — bus V+ is gated on the RTC schedule
  (power-pack-fed pods may idle listening at ~2 µA, never more). The SPS30
  is off-BOM but its JST ZH-5 header (S5B-ZR) is on the pod PCB; SPS30 runs
  in UART mode, never I²C over cable. Atmospheric extras (2026-07):
  **AS3935 lightning** (off-BOM; the *only* always-on sensor, ~70 µA — keep
  it and the coil away from the switchers, on a quiet RC/LDO rail, and treat
  coil tuning as a bring-up step. Coil = **Premo SDTR1103-HF1-0100J**
  (100 µH ±5 %, Q45 @ 0.5 MHz, damped to ~15 with 10 k) — **plan of record
  for all builds**, ordered direct from Premo/DC Electronic Solutions,
  consigned at JLCPCB (no distributor carries it; MA5532 is obsolete),
  **LTR-390UV-01 UV** (C492374, JLCPCB-stocked; GUVA-S12SD cost-down; the
  board must also carry a **DNP AS7331 OLGA-16 footprint** on the same I²C
  bus as the spectral-UV upgrade stuffing option),
  **MLX90614ESF-BCC** sky-IR cloud sensor, piezo + TLV7031 hail/impact
  channel.
- `hardware/tenkiro-hashi/` — indoor bridge: E22-900M22S radio + ESP32-S3
  (primary, Wi-Fi). Backup wired-Ethernet variant: **STM32H563VGT6 +
  LAN8742A RMII PHY** (decided 2026-07; **no WIZnet**, and don't substitute
  LAN8720A — see DESIGN.md). Both variants carry an **SCD40** CO₂/T/RH
  sensor (indoor air on the always-on node).
- Each board's schematic is **generated from its own data manifest**
  (`hardware/scripts/tenkiro-{sora,hashi}.schgen.py` — to be authored), not
  hand-authored, then **placed, not wired** — wiring happens in eeschema using
  the per-sheet notes. Regenerating needs `KSCHGEN_FORCE=1` (kschgen keeps
  existing `.kicad_sch` to protect manual wiring).
- Custom parts (E22-900M22S module, sensor connectors, etc.) go in
  `hardware/lib/{symbols,footprints.pretty,3dmodels}` and are registered in
  the per-board lib-tables (lib name `tenkiro`, shared).
  **Every vendored/authored part MUST get a row in `hardware/lib/ATTRIBUTIONS.md`**
  (source + license + where the pinout came from) — required by CERN-OHL-S, and
  it's what lets a later reader trust a land pattern instead of re-deriving it.
  Author **exposed pads as visible pins** (never hidden power pins): the sheets
  are placed-not-wired and wired by hand, so a hidden EP is invisible to both
  the wirer and ERC.
- Run from `hardware/` (set `KICAD_CLI` if `kicad-cli` isn't on PATH):
  ```sh
  make gen-tenkiro-sora    # regenerate a board's schematic from its manifest
  make check-tenkiro-hashi # components / footprints / dup refs / ERC tally
  make docs                # schematic + PCB SVGs + 3D renders + JLCPCB BOM (all boards)
  make jlc                 # full JLCPCB fab+assembly zips (all boards)
  ```

## Radio / protocol invariants
- **SX1262** (E22-900M22S, the SPI **M** variant — not the UART **T** modules)
  on both boards for rev A; bare SX1262 is a later cost-down, not rev A.
- Start links at SF7/125 kHz/4-5, +14 dBm, 60 s interval — **never default to
  SF12** or the 30 dBm PA modules.
- Nami packets are fixed-width binary (~40–80 B) with sequence numbers,
  cumulative rain/wind counters, and an authentication tag — no JSON over the
  air, no unauthenticated packets.

## Licensing
- **Firmware** — repo `LICENSE` is **AGPL-3.0**.
- **Hardware** — `hardware/LICENSE` is **CERN-OHL-S v2** (strongly reciprocal;
  matches the AGPL posture). Keep the source-location notice (`hardware/README.md`).
