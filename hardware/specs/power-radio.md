# Tenkiro A0 power and radio capture

Resolved 2026-10-03. This is the electrical design basis for Sora's power chain
and the shared Sora/Hashi radio. User decisions: the SPS30 is optional and may
run intermittently; these sheets are fully wired. MCU, sensor, switched mast-bus,
Hashi USB power and PCB layout are subsequent captures.

**Status:** datasheet cross-check, calculations and connected KiCad capture.
No assembled circuit, charger stability, environmental runtime or RF link has
been measured. ERC passing does not establish those properties.

## Design decisions

| Function | A0 selection / requirement |
|---|---|
| Solar | Voltaic P105, 6 V class / approximately 5 W; expected Vmp 6.01 V, Imp 0.83 A, Voc 7.07 V. Raw panel, no USB regulator. |
| DC | 9–16 V at J102; 12 V nominal. Source must be regulated or appropriately fused. No automotive load-dump qualification. |
| Input sharing | Separate 1 A / 63 V Littelfuse 0466001.NRHF fuses and owned FUXINSEMI B360A 60 V / 3 A SMA Schottky diodes; common ground. Both sources may be connected; higher voltage normally supplies charge. |
| Surge clamp | SMBJ16A after ORing, 16 V standoff / 26 V specified clamp at rated pulse. Replaces SMBJ26A (42.1 V clamp exceeds BQ24650 VCC absolute maximum). |
| Cell | GWL LTO1865-13 electrical basis, 1S1P 18650 LTO, 1.3 Ah nominal / 0.95 Ah minimum, 2.4 V nominal. Keyed pigtail with a fuse near the cell; no generic removable Li-ion holder. Qualify the purchased cell against its supplier datasheet. |
| Charger | BQ24650RVAR; 2.7489 V nominal, 0.5 A CC, termination enabled, 50 mA nominal precharge/termination. |
| Solar regulation | MPPSET = 5.376 V at VIN_CHG, after the ORing diode. This is fixed input-voltage regulation, not an adaptive maximum-power search. |
| Temperature | Separate cell-mounted Semitec 103AT-2 for charger and gauge. Charger nominal window about −5…40°C, with open/short inhibition. |
| Main rail | TPS63900DSKR, 3.3 V for both SEL states, unlimited programmed input current. Murata DFE201612E-2R2M=P2, 2.2 µH ±20%, 2.4 A saturation / 1.8 A thermal rating; manufacturer land pattern captured. |
| Undervoltage | TLV3012BIDBVR comparator; ideal battery shutdown 2.09 V / restart 2.30 V. Final trips require tolerance and load testing. |
| Gauge | BQ34Z100PWR-G1, 10 mΩ low-side shunt; powered by 3.3 V; real LTO ChemID and learning required. |
| Radio, both boards | Ebyte E22-900M22S, SX1262 SPI module; 3.3 V, allocate 124 mA peak TX and ≥200 mA supply budget at Hashi's capture boundary. |
| Starting RF settings | 915 MHz, SF7, 125 kHz bandwidth, CR 4/5, +14 dBm, one packet per 60 s. Region/channel/antenna qualification remains required. |
| Antenna | Board U.FL through 0 Ω R506; remove R506 when using the module's own IPEX. One antenna path only. PESD5V0F1BRSF bidirectional 5 V, 0.25 pF typical ESD shunt at board U.FL. |

The cell specification gives 1.85–2.75 V working voltage, 2.8 V maximum,
−15…45°C charging and −25…55°C discharging. This supersedes the earlier
generic 2.85 V / −30°C assumptions. The complete outdoor product's operating
range is limited by its actual cell, enclosure and thermistor attachment.

## Circuit constraints and calculations

### Charger and input

- R205/R206 = 30.9 kΩ / 100 kΩ, both 0.1%:
  `Vcharge = 2.1 × (1 + 30.9/100) = 2.7489 V`.
  Including TI's ±0.7% regulation, resistor corners and 100 nA feedback
  leakage gives approximately **2.77254 V worst high**, below 2.8 V.
  The originally tempting 309 kΩ / 1 MΩ costs up to 30.9 mV leakage error
  and was rejected. Gauge-shunt voltage drop slightly reduces cell voltage
  during charge because the charger references system ground.
- R201 = 80 mΩ, 1%: `40 mV / 80 mΩ = 0.5 A`. Include charger current
  tolerance and shunt tolerance. Nominal shunt dissipation is only 20 mW;
  the 0.5 W part provides ample electrical margin. Kelvin sense both ends.
- R203/R204 = 348 kΩ (1%) / 100 kΩ (0.1%):
  `1.2 × (1 + 348/100) = 5.376 V`. The panel terminal must also cover
  D101's forward drop. Measure hot-panel and weak-light behavior. A higher
  voltage panel is not an approved plug-in alternative without retuning MPPSET.
  The stocked 1% R203 replaces a scarce 0.1% part. Including TI's ±0.6%
  input-regulation accuracy and resistor initial tolerances gives 5.298–5.455 V,
  excluding temperature coefficients and MPPSET leakage. TI specifies up to
  1 µA MPPSET leakage at 7 V over 0–85°C; this is not a complete worst-case
  panel setpoint bound. Characterize the actual threshold and hot/weak panel
  behavior. Charge-voltage and UVLO divider precision remain 0.1%.
- Q201/Q202 are DMN6075S-7, 60 V N-MOSFETs, G/S/D = pins 1/2/3.
  The 60 V rating gives margin over the nominal 26 V TVS clamp. Gate-drive,
  switching loss, temperature and actual overshoot remain bench/layout checks.
- Bootstrap: BAT46W anode REGN, cathode BTST; 100 nF BTST-to-PH;
  1 µF REGN and VREF bypass; VCC has 10 Ω / 1 µF input filtering.
  SRP has both differential 100 nF to SRN and common-mode 100 nF to ground.
- The charger and buck-boost share **one battery-node filter**. L201 is
  10 µH SRN6045TA-100M. C201 4.7 µF + TPS input C301 10 µF + small
  bypasses total about 15 µF nominal: roughly **13 kHz resonance**.
  At exactly 10 µH, 12–17 kHz corresponds to 8.76–17.59 µF effective
  capacitance. Account for L tolerance, MLCC DC bias, temperature and all
  attached capacitance together. C201 is Samsung CL32B475KBUYNNE, 4.7 µF /
  50 V X7R in 1210; C301 is owned SAMWHA CS3225X7R106K500NRL, 10 µF / 50 V X7R in 1210.
  Their effective capacitance at cell voltage/temperature and measured
  stability are release gates; nominal arithmetic is insufficient.
- Do not rely on the TVS voltage number alone: coordinate source impedance,
  wiring fuses, diode pulse ratings and TVS energy. The circuit does not provide
  an independent precision overvoltage disconnect or single-fault cell BMS.
- No input-to-load bypass is provided. A valid battery is required for normal
  system operation. Continuous system load can affect charger termination;
  schedule pod activity around charge characterization.
- BQ24650 precharge is limited to 30 minutes. Test recovery near the selected
  cell's floor; do not assume a deeply depleted cell will recover automatically.

### Temperature and undervoltage

Charger TS uses 6.04 kΩ from VREF, 33.2 kΩ to ground and 103AT-2 to ground.
Manufacturer R(T) interpolation gives nominal −4.85°C cold stop, 40.11°C hot
stop and 36.74°C hot restart. Estimated resistor/thermistor/comparator corners
are −8.59…−1.48°C, 38.36…41.97°C and 34.88…38.63°C respectively. These
estimates fit the selected cell's charge range; thermistor thermal lag, mounting,
leakage and ageing still require testing. An open NTC leaves TS/VREF ≈0.846;
a short pulls it to zero, inhibiting charge in either case.

UVLO uses the TLV3012B's 1.242 V reference at IN−, 750 kΩ (0.1%) from VBAT
to IN+, 1 MΩ (0.1%) from IN+ to ground and 7.5 MΩ (1%) positive feedback
from OUT. These stocked values replace 1 MΩ / 1.33 MΩ / 10 MΩ. Ideal trips:
`Von = 1.242 × (1 + 750k/1M + 750k/7.5M) = 2.2977 V`;
`Voff = Von / (1 + 750k/7.5M) ≈ 2.0888 V`.
Real trips include reference/offset/internal hysteresis, resistor tolerances and
output swing. OUT drives TPS63900 EN; SEL is grounded. Hardware cutoff removes
the 3.3 V load, but comparator/divider/charger leakage remains, so it is not a
storage disconnect. Store/ship with the cell unplugged. Recovery must be tested
with the actual LTO voltage curve to ensure adequate restart hysteresis.

TPS63900 CFG1 = 36.5 kΩ, CFG2 = GND, CFG3 = 16.2 kΩ. Both presets give
3.3 V. Its headline output rating is not a guaranteed low-cell output current:
verify 180 mA pod demand and radio transients at the UVLO floor and temperature.
Use local output bulk; adding arbitrary VBAT bulk changes charger compensation.

Inventory substitutions: C204 uses the owned Samsung CL10A105KB8NNNC,
1 µF / 50 V X5R in 0603; the X5R 85°C ceiling exceeds the qualified cell
operating range, but board temperature and effective capacitance still need
validation. Both C502 use the same 10 µF / 50 V 1210 SAMWHA part as C301.
Each radio replaces its 47 µF capacitor with two owned Samsung 22 µF / 25 V
X7R capacitors (C503/C505): 44 µF nominal plus the separate 10 µF bypass,
versus 47 + 10 µF previously. This adds one 1210 placement per board. The
Ebyte supply-bypass recommendation is met; TPS63900 permits larger output
capacitance. Effective capacitance and TX/startup droop remain bench gates.
Large owned polymer/electrolytic caps were not selected because of leakage
and package tradeoffs in this sleep-powered design.

### Gauge

VSS, local bypasses and SRP reference BAT_NEG; SRN references system GND.
Every charger/load return must cross R401. BAT_NEG must never be shorted to
system GND elsewhere, including test fixtures. REGIN and CE connect to 3.3 V;
REG25 is bypassed only. BAT senses cell positive through 220 Ω with 100 nF
to BAT_NEG. Use separate charger and gauge thermistors; sharing biased TS
nodes is invalid. P1/P2 are grounded as specified; unused VEN/HDQ are NC.

Configure one series cell, the internal 5:1 divider (VOLTSEL=0), and
VoltageDivider=5000 as the calibration starting point. Run TI GPCCHEM on the
actual cell, calibrate voltage/current/temperature and complete a learning
cycle. The 10 mΩ shunt produces 10 µV at 1 mA, equal to the specified ADC
offset scale; **microamp sleep-current accuracy is not established**. Gauge
power is lost below UVLO. Validate restart/state retention and do not promise
accurate SoC until characterized over the intended duty cycle.

## Radio pin and firmware contract

The current official **E22-M Series V1.5, 2026-09-18** manual takes precedence
over the inconsistent product web pin table and old demo code.

| Module pin | Net / action |
|---|---|
| 9 | 3V3, with 100 nF + 10 µF + 2 × 22 µF local bypass (C501/C502/C503/C505) |
| 19 / 18 / 17 / 16 | NSS / SCK / MOSI / MISO |
| **15** / 14 / 13 | NRST / BUSY / DIO1 |
| 6 | RXEN from host; 100 kΩ default pulldown |
| 7 / 8 | TXEN connected through 0 Ω to DIO2; enable SX1262 DIO2 RF-switch control |
| 21 | ANT to R506 and board U.FL |
| 1–5, 10–12, 20, 22 | GND; **pin 12 is not reset** |
| Internal DIO3 | Configure TCXO voltage **2.2 V**; initial delay 5 ms, characterize at temperature |

NSS and NRST have 100 kΩ pullups. Hold RXEN low during transmit and sleep;
raise for receive in coordination with the SX1262 state. Honor BUSY before
commands. Use the M SPI module, not the T UART variant. The RF shunt is
bidirectional because the antenna signal swings about ground. At +22 dBm
into matched 50 Ω the peak is approximately 3.98 V; antenna mismatch can
increase it, so maximum-power mismatch and protection tests remain necessary.

The custom module footprint follows the manufacturer's top-view geometry:
14 × 20 mm body, right side pins 11…1 and left side 12…22 from top to bottom,
with the nonuniform lower-pad spacing retained. Final print-to-module fit and
antenna/ground keepout review are required before layout release.

## Load and autonomy budget

The SPS30 option does not determine the base-station requirement. Its initial
schedule is **60 s once per hour**, then the entire pod is switched off. Follow
Sensirion's stabilization/discard guidance within the active window, and budget
fan cleaning separately. Do not overlap radio TX and pod/fan startup.

| Case | Battery energy allocation / day | Conservative planning runtime |
|---|---:|---:|
| Base station target | ≤0.060 Wh | 19 days arithmetic; set 14 days acceptance target |
| Optional SPS30, 60 s/hour | +0.1625 Wh (65 mA × 5 V × 0.4 h / 80% end-to-end efficiency) | About 5.1 days with base load |
| Optional SPS30, 60 s/4 hours | +0.0406 Wh | About 11.3 days with base load |

These figures assume **0.95 Ah minimum × 2.4 V × 50% usable = 1.14 Wh**.
The 50% is a planning allowance for discharge cutoff, cold, ageing and
conversion, not measured cell performance. The 80% pod efficiency includes
both conversion stages/cabling as an assumption; measure it. Pod controller and
other pod sensors consume additional energy. At SPS30 fan startup (80 mA at
5 V for approximately 200 ms), an 85%-efficient local boost takes about
143 mA at 3.3 V. Reserve **180 mA** on the 3.3 V bus for pod plus electronics.

An illustrative base allocation is 0.025 Wh/day for continuous electronics,
0.010 for radio, 0.010 for sampling/MCU, and 0.015 margin. This includes the
always-on lightning sensor and gauge, but must be replaced with measurements
once their sheets/firmware exist. The charger divider alone draws about 21 µA
from the cell. A 5 W panel is charge-current-limited by the 0.5 A setting:
approximately 1.2 W into a nominal cell in strong sun, not 5 W into the cell.
At 0.5 effective peak-sun-hours/day and an illustrative 60% delivery factor,
the charge ceiling is about 0.36 Wh/day; actual winter/shading yield depends
on installation. Increase sample interval automatically as energy falls.

### Expandable battery option

More capacity can support more frequent particulate sampling for a similar
sunless interval. Keep the electrical pack **1S**; the existing charger/rail
must not receive a series-connected 2S pack. A larger single LTO cell with
compatible limits or a professionally assembled parallel pack can use J401.
For a parallel pack use matched cells, a qualified assembly and protection
appropriate to each branch; do not connect loose cells at unequal voltages.

| Pack equivalent | SPS30 schedule | Estimated total energy/day | Estimated sunless runtime |
|---|---|---:|---:|
| 1 × reference cell | 60 s/hour | 0.223 Wh | 5.1 days |
| 2 × reference capacity, 1S2P | 60 s/30 min | 0.385 Wh | 5.9 days |
| 4 × reference capacity, 1S4P | 60 s/15 min | 0.710 Wh | 6.4 days |

These use the same 50% usable minimum capacity and 80% conversion assumptions,
excluding extra pod electronics. They are sizing options, not measured runtime
or a change to the baseline pack. At 0.5 A the approximate nominal-capacity
CC charging times scale from 2.6 h to 5.2 h and 10.4 h, before CV taper and
system load. Solar replenishment, not storage alone, limits sustainable duty
cycle: the illustrative 0.36 Wh/day winter scenario cannot sustain the 2-cell
30-minute or 4-cell 15-minute schedules indefinitely. More panel yield and/or
a revised charge-current design may be needed. A larger panel alone cannot
exceed the captured 0.5 A charge limit. Scale gauge Design Capacity/ChemID
qualification and redo thermal, fuse and recovery checks for any pack change.

## Capture, verification and remaining work

Open `hardware/tenkiro-sora/tenkiro-sora.kicad_pro` and
`hardware/tenkiro-hashi/tenkiro-hashi.kicad_pro` in KiCad 10. Continuous wires
show the input and charger power paths; matching net labels connect control
and sense circuitry. DNP commissioning headers expose a real external host
boundary until the onboard MCU sheets are added. On Sora header pin 1 is a
3.3 V **output**; on Hashi it is the 3.3 V **input**. Never backfeed Sora's
rail from a debugger/host. All header IO is 3.3 V.

From `hardware/`:

```sh
make gen-tenkiro-sora gen-tenkiro-hashi   # preserves existing schematic edits
make validate-capture                   # strict ERC + exported pin/net checks
make capture-pdfs                       # PDFs for review
```

`KSCHGEN_FORCE=1` deliberately replaces generated sheets; do not use it after
manual KiCad edits unless those edits have been reconciled into the manifests.
The source location and library provenance are in `hardware/README.md` and
`hardware/lib/ATTRIBUTIONS.md`. MPNs are populated for critical ICs, switches,
inductors, protection and connectors. Generic passives still need qualified
orderable MPNs, especially the charger-filter MLCCs; this is not an assembly BOM.

Before a PCB release or claims of validation:

1. Qualify exact cell/NTCs and filter capacitor MPNs. Check effective LC corners,
   temperature limits, cell mounting and the keyed harness/fuse.
2. Complete MCU, sensors, switched mast bus, Hashi USB/3.3 V supply and board
   layout. Review Kelvin ground paths, switch loops, RF keepout and gauge ground.
3. Bench solar/DC startup, ORing/backfeed, reverse polarity, source removal,
   CC/CV, termination with load, depleted-cell recovery, open/short NTC, thermal
   trips and shutdown/restart. Check transients at the actual IC pins.
4. Measure 3.3 V ripple, peak loads and stability over cell voltage/temperature;
   characterize sleep/day energy and optional pod startup/cable drop.
5. Configure/calibrate/learn the gauge; verify energy accounting over UVLO cycles.
6. Radio bring-up on both boards: reset/BUSY/SPI, TCXO, RX/TX switching,
   packet loss, antenna mismatch, RF emissions and connector ESD.

Verification basis: high confidence in extracted core pin assignments and
resistor arithmetic; analytical estimates for autonomy/temperature corners;
unverified assembled behavior. Schematic analyzer and raw KiCad export checks
apply. PCB/DRC, cross-analysis, EMC, thermal and Gerber analyses do not yet
apply because no PCB exists. No SPICE simulator is installed, and no vendor
switching model simulation was run. Supply/lifecycle auditing remains incomplete
for generic passives. The previous repository state contained no captured circuit,
so this is the first electrical baseline, not evidence of a tested revision.

See [the capture review](capture-review-2026-10-03.md) and
[machine-readable results](capture-validation.json) for exact check counts,
analyzer triage and verification limits.

## Primary references

- [TI BQ24650 datasheet](https://www.ti.com/lit/ds/symlink/bq24650.pdf), pin table, charge/temperature equations and application circuit.
- [TI BQ24650 filter clarification](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/825968/bq24650-output-capacitor-selection), 12–17 kHz guidance despite one conflicting datasheet paragraph.
- [TI TPS63900](https://www.ti.com/lit/ds/symlink/tps63900.pdf), configuration table and effective capacitance requirements.
- [TI BQ34Z100-G1](https://www.ti.com/lit/ds/symlink/bq34z100-g1.pdf), low-side sensing, CE/REGIN and low-voltage supply arrangement.
- [TI TLV3012 family](https://www.ti.com/lit/ds/symlink/tlv3012.pdf), B variant reference/comparator.
- [Ebyte official E22-M manual](https://www.cdebyte.com/pdf-down.aspx?id=4216), V1.5 §§3.2 and 4.2.
- [Voltaic P105](https://voltaicsystems.com/content/P105_ds.pdf), expected panel performance, 2026-08-27.
- [GWL LTO1865-13 specification](https://files.gwl.eu/inc/_doc/attach/StoItem/4576/GWL-LTO1865-13-Spec.pdf), cell electrical basis; verify supplied lot.
- [Semitec 103AT-2](https://www.semitec-global.com/uploads/2022/01/P12-13-AT-Thermistor.pdf), NTC curve.
- [SPS30 datasheet](https://sensirion.com/file/datasheet_sps30) and [low-power application note](https://sensirion.com/media/documents/188A2C3C/6166F165/Sensirion_Particulate_Matter_AppNotes_SPS30_Low_Power_Operation_D1.pdf).
- [DMN6075S](https://www.diodes.com/datasheet/download/DMN6075S.pdf), MOSFET ratings and G/S/D pin order.
- [SRN6045TA](https://www.bourns.com/docs/Product-Datasheets/SRN6045TA.pdf), 10 µH charger inductor.
- [Murata DFE201612E](https://datasheet.lcsc.com/datasheet/pdf/9a2227c0960d033e774a76ebdabff58d.pdf), 2.2 µH buck-boost inductor: 2.4 A saturation, 1.8 A thermal current, 116 mΩ maximum DCR; recommended land pattern on page 5.
- [PESD5V0F1BRSF](https://assets.nexperia.com/documents/data-sheet/PESD5V0F1BRSF.pdf), bidirectional RF ESD shunt.

Downloaded core PDFs and extracted facts are under `hardware/datasheets/`.
Manufacturer PDFs are local reference material excluded from Git; structured
extractions and source links preserve the decision evidence.
