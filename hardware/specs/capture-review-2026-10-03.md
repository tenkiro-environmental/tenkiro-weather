# A0 power/radio capture review — 2026-10-03

**Result:** electrically connected, reviewable KiCad 10 capture; **not ready
for fabrication and not bench validated**. Critical remaining release work is
filter-capacitor qualification, exact cell/harness qualification, full-board
capture/layout, and power/RF measurements. All 82 fitted placements per set now
have orderable MPNs and JLCPCB codes; see the procurement record in `hardware/bom/`.
The selected values and bench acceptance work are in
[power-radio.md](power-radio.md).

## Evidence and scope

| Check | Sora | Hashi | Basis / confidence |
|---|---:|---:|---|
| KiCad 10.0.6 ERC | 0 violations | 0 violations | Raw KiCad result; high |
| Physical components including DNP | 72 | 14 | KiCad XML netlist, excluding power flags; high |
| Exported pin connections/NCs checked | 218 | 56 | Every pin compared with committed connection contract; high |
| Exported nets | 51 | 14 | KiCad XML; includes intentionally unconnected gauge pins; high |
| Authored IC pin assignments checked | 70 | 22 | Independent manufacturer extraction vs exported symbol pin table; high |
| Assigned footprint existence | All | All | Installed KiCad 10 and project footprint files; high for existence only |
| PDF inspection | 7 pages | 3 pages | Rendered KiCad output; visual review |
| Assembled circuit measurements | None | None | No hardware available |

The 70 Sora core assignments cover BQ24650 (17 including EP), TPS63900
(11 including EP), TLV3012B (6), BQ34Z100-G1 (14) and E22 (22). Exposed-pad
names in manufacturer documents map to numeric pads 17/11 in the selected
KiCad footprints. The gauge's multifunction pin names use underscores in the
symbol and slashes in TI's table; the checker explicitly normalizes those.

The Ebyte module table and top-view dimensions were also visually checked
against official V1.5, PDF page 10 / printed page 8, §3.2. Pin 12 is ground,
15 is reset. The lower-pad gap is 5.57 mm, not a uniform 1.27 mm pitch.
The custom footprint includes a 0.9 mm outward solder toe beyond the bottom
metallization; physical fit and assembly review remain necessary.

DMN6075S G/S/D = 1/2/3 was manually checked against its manufacturer drawing.
Remaining two-pin passive symbols have electrically symmetric pins. Orderable
parts and package assignments are now selected; MLCC bias and power-stage
behavior still require qualification.
Input, TVS and bootstrap diode polarity is traced in the exported netlist.
Connector cable polarity, physical module fit and all footprints still need
the normal PCB/assembly review.

## Changes from the prior state

The prior repository was an architecture/scaffold with no `.kicad_sch`
capture. The new baseline adds Sora input protection, CC/CV charger, 3.3 V
rail, hardware UVLO, battery/gauge and radio, plus the common Hashi radio.
Commissioning headers explicitly terminate the future MCU interface.

Electrical corrections include 2.75 V instead of 2.85 V charging, SMBJ16A
instead of SMBJ26A, a 6 V panel with a shared solar/DC MPP threshold, 60 V
charger MOSFETs, visible IC exposed pads, proper gauge ground/sense wiring,
and latest-manual radio reset/TCXO settings. The optional SPS30 and 1S2P/1S4P
capacity scenarios are accounted for separately from the base load.

## Analyzer checks and triage

Ran `analyze_schematic.py` on both final root schematics and
`bom_manager.py analyze --recursive` on Sora. These topology analyzers are
supplementary; KiCad's hierarchy export is authoritative for connectivity.
The automated analyzer reported mixed trust, with no findings tagged as
datasheet-backed. Manufacturer verification described above was performed
separately; it must not be attributed to the heuristic analyzer.

Accepted findings:

- **SS-001, sourcing:** initially missing passive MPNs are resolved by the
  subsequent inventory and JLCPCB sourcing pass. Every fitted placement has
  MPN, manufacturer, LCSC code and datasheet properties.
- **DS-003, partial coverage:** passive capacitance-bias/temperature qualification
  remains open despite selected MPNs. Core IC pin tables were separately
  extracted and compared.

Dismissed pullup heuristics, with residual behavior to test:

- BQ24650 TERM_EN is tied directly to VREF; it is not floating.
- Gauge VEN is an intentionally unused output for the external divider option.
- Radio BUSY/MISO are driven outputs; pullups are not required by the module
  contract. RXEN has the intended pulldown, and TXEN is driven by DIO2 through
  R501. Verify power-up/RX/TX/sleep sequencing in firmware.

An early routed-drawing iteration caused net-name conflicts across rotated
passives. These were corrected before release; final strict ERC and every-pin
netlist comparison pass. The final analyzer has no shorted-component findings.
C503 was increased to a 10 V rating after a voltage-derating warning.

## Not performed / limits

- PCB, DRC, schematic/PCB cross-analysis, EMC and thermal analysis: no PCB exists.
- Gerber/DFM analysis: no fabrication outputs exist.
- SPICE: no simulator installed; no vendor switching-model simulation performed.
- Complete lifecycle and production BOM release: pending. Live JLCPCB stock,
  shortage pricing and a 10-set cart with spares were checked separately;
  this remains a partial power/radio capture, not a manufacturing package.
- Charger stability/transients, temperature trips, NTC fault behavior, UVLO,
  cell qualification/recovery, gauge calibration and radio/regulatory tests:
  require assembled hardware and are explicitly pending.
- Autonomy and solar yield: engineering estimates, with assumptions in the spec;
  no claim of guaranteed winter runtime.

Reproduce the structural checks with `make validate-capture` from `hardware/`.
It fails on ERC violations, wrong/shorted/missing pin connections, IC
pin-assignment mismatches, duplicate references and missing footprint files.
The result is a **capture validation**, not a complete product validation.
