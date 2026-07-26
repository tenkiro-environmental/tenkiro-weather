# Tenkiro — hardware

KiCad 10 design for the **Tenkiro** weather system. Two PCBs (linked by the
915 MHz Nami radio protocol, not a cable):

- **`tenkiro-sora/`** — the outdoor solar-powered weather station: ultra-low-
  power MCU, E22-900M22S (SX1262) radio module, external 915 MHz antenna
  (U.FL), 1S LTO cell + solar panel + MPPT charger + fuel gauge, load-switched
  sensor rails, internal-flash buffering.
- **`tenkiro-hashi/`** — the indoor bridge: E22-900M22S (SX1262) radio module,
  network MCU (ESP32-S3 primary; wired-Ethernet backup variant on a non-ESP32
  MCU — see `../DESIGN.md`), USB-C power, MQTT + local web interface.

See `../DESIGN.md` for the full design and `scripts/README.md` for the
schematic-generation flow. Build docs/BOMs/fab packages with the `Makefile`
(`make help`).

## Library

`lib/{symbols,footprints.pretty,3dmodels}` holds project-specific parts (shared
by both boards, lib name `tenkiro`); most parts resolve to KiCad bundled
libraries.

## License — Hardware: CERN-OHL-S v2

The hardware (schematics, PCB layouts, and associated design files under
`hardware/`) is licensed under the **CERN Open Hardware Licence Version 2 —
Strongly Reciprocal** (`CERN-OHL-S-2.0`). Full text: [`LICENSE`](LICENSE).
Chosen to match the strong-copyleft posture of the AGPL-3.0 firmware.

**Third-party library parts** (vendored symbols / footprints / 3D models) carry
their own upstream licenses — all compatible with incorporation into a
CERN-OHL-S v2 design. Every one is indexed, with its source and license, in
**[`lib/ATTRIBUTIONS.md`](lib/ATTRIBUTIONS.md)**.

> Copyright (c) 2026 tenkiro authors.
>
> This source describes Open Hardware and is licensed under the CERN-OHL-S v2.
>
> You may redistribute and modify this source and make products using it under
> the terms of the CERN-OHL-S v2 (https://ohwr.org/cern_ohl_s_v2.txt).
>
> This source is distributed WITHOUT ANY EXPRESS OR IMPLIED WARRANTY, INCLUDING
> OF MERCHANTABILITY, SATISFACTORY QUALITY AND FITNESS FOR A PARTICULAR PURPOSE.
> Please see the CERN-OHL-S v2 for applicable conditions.
>
> Source location: https://github.com/tenkiro-environmental/tenkiro-weather
>
> As per CERN-OHL-S v2 § 4, if you produce a device using this source, you
> should where practicable keep the above Source Location visible on the device.
