# Third-party & authored library parts

Vendored / authored KiCad symbols, footprints and 3D models live in this `lib/`
directory and are referenced project-locally through each board's `sym-lib-table` /
`fp-lib-table` (the shared **`tenkiro:`** library). **Record every part here with
its source and license.**

This matters more than usual for this repo: `hardware/LICENSE` is **CERN-OHL-S v2**
(strongly reciprocal), so the provenance of every imported land pattern and symbol has
to be traceable. It also has a practical payoff — an attribution line stating *where a
pinout came from* is what lets a future reader trust a part over a guess.

Import workflow (matches the other BenchBits hardware projects):

```sh
# 1. drop the pre-built KiCad part in place
cp <download>/Foo.kicad_mod   lib/footprints.pretty/
cp <download>/Foo.step        lib/3dmodels/
# 2. append the (symbol "Foo" ...) block to lib/symbols/tenkiro.kicad_sym
#    (drop any vendor library prefix on the embedded Footprint property so it
#     resolves against our project-local "tenkiro:" library)
# 3. repoint the footprint's 3D path to our local copy:
sed -i 's|\${KICAD.*_3RD_PARTY}/3dmodels/.*/|\${KIPRJMOD}/../lib/3dmodels/|' \
    lib/footprints.pretty/Foo.kicad_mod
```

## Imported / authored parts

All entries below were authored for Tenkiro on 2026-10-03. Datasheets
are references for functional pin assignments/dimensions; vendor PDFs retain
their own copyright. Bundled KiCad symbols/footprints are used under the
KiCad Libraries License (CC-BY-SA-4.0 with its schematic/PCB exception).

| Part | Files | Source | License | Pinout verified against |
|------|-------|--------|---------|-------------------------|
| BQ24650RVAR symbol | `symbols/tenkiro.kicad_sym` | Authored for Tenkiro | CERN-OHL-S-2.0 | [TI BQ24650](https://www.ti.com/lit/ds/symlink/bq24650.pdf), pin table, EP visible as 17 |
| BQ34Z100PWR-G1 symbol | `symbols/tenkiro.kicad_sym` | Authored for Tenkiro | CERN-OHL-S-2.0 | [TI BQ34Z100-G1](https://www.ti.com/lit/ds/symlink/bq34z100-g1.pdf), pin table; unused P1/P2 modeled passive for specified GND connection |
| TPS63900DSKR symbol | `symbols/tenkiro.kicad_sym` | Authored for Tenkiro | CERN-OHL-S-2.0 | [TI TPS63900](https://www.ti.com/lit/ds/symlink/tps63900.pdf), pin table, EP visible as 11 |
| TLV3012BIDBVR symbol | `symbols/tenkiro.kicad_sym` | Authored for Tenkiro | CERN-OHL-S-2.0 | [TI TLV3012 family](https://www.ti.com/lit/ds/symlink/tlv3012.pdf), DBV pin table, B variant |
| E22-900M22S symbol | `symbols/tenkiro.kicad_sym` | Authored for Tenkiro | CERN-OHL-S-2.0 | [Ebyte official E22-M V1.5](https://www.cdebyte.com/pdf-down.aspx?id=4216), §3.2; pin 12 GND, pin 15 NRST |
| E22-900M22S footprint | `footprints.pretty/E22-900M22S_14x20mm.kicad_mod` | Authored from manufacturer mechanical drawing; 1.8 × 0.8 mm PCB pads include outward solder toe | CERN-OHL-S-2.0 | Ebyte V1.3 dimension drawing, checked against official V1.5 §3.2; top-view numbering, irregular lower-pad spacing. Physical fit remains a release check. |

| Murata DFE201612E footprint | `footprints.pretty/L_Murata_DFE201612E.kicad_mod` | Authored from [Murata J(E)TE243A-0006-01](https://datasheet.lcsc.com/datasheet/pdf/9a2227c0960d033e774a76ebdabff58d.pdf), pp. 1 and 5 | CERN-OHL-S-2.0 | Nonpolar 2-pad inductor; recommended pads 0.8 × 1.8 mm at ±0.8 mm, outer span 2.4 mm, gap 0.8 mm. No 3D model. |
