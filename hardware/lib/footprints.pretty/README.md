# tenkiro project footprints

> **Sources + licenses for every vendored/authored part are indexed in
> [`../ATTRIBUTIONS.md`](../ATTRIBUTIONS.md)** — add a row there for anything new.
> This file holds the *why* (geometry, placement); that file holds the *provenance*.

Most parts resolve to **KiCad bundled libraries** (symbols + footprints).

This directory is reserved for any part that is **not** in KiCad's standard
libraries. The most likely candidates for this project are:

- the **Ebyte E22-900M22S** castellated radio module (14 × 20 mm, SPI) — used
  on both Sora and Hashi;
- weather **sensor modules** (wind/rain reed-switch connectors, radiation-shield
  mounted sensors) whose pinout/dimensions don't match a bundled footprint;
- the **solar panel / battery connectors** if the exact parts aren't bundled.

Add `*.kicad_mod` files here and register them via `../../fp-lib-table` /
per-board `fp-lib-table` (lib name `tenkiro`).

## Vendored

*(none yet)*
