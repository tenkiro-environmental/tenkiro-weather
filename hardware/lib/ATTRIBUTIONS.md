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

*(none yet — likely first entries: the Ebyte E22-900M22S castellated module
footprint+symbol, the U.FL/I-PEX receptacle if not using the bundled one, and
any weather-sensor modules without bundled parts)*

| Part | Files | Source | License | Pinout verified against |
|------|-------|--------|---------|-------------------------|
