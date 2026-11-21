#!/usr/bin/env python3
"""Sora A0: fully wired input, charger, rail, gauge, radio. CERN-OHL-S-2.0."""
from tenkiro_capture import *

input_sheet=dict(name='Solar and DC inputs',file='inputs.kicad_sch',exports=['VIN_CHG','GND'],comps=[
 connector('J101','SOLAR: P105 / 6V 5W',18,20,'SOLAR_POS','GND'),
 connector('J102','DC: 9-16V',18,48,'DC_POS','GND'),
 c('F101','Device:Fuse','1A / 63V',46,20,{1:'SOLAR_POS',2:'SOLAR_FUSED'},'Fuse:Fuse_1206_3216Metric','0466001.NRHF','Littelfuse'),
 c('F102','Device:Fuse','1A / 63V',46,48,{1:'DC_POS',2:'DC_FUSED'},'Fuse:Fuse_1206_3216Metric','0466001.NRHF','Littelfuse'),
 c('D101','Device:D_Schottky','B360A / 60V',72,20,{1:'VIN_CHG',2:'SOLAR_FUSED'},'Diode_SMD:D_SMA','B360A','FUXINSEMI','https://datasheet.lcsc.com/datasheet/pdf/4341698a2794575dc7c94af0a06dfb39.pdf?productCode=C6807778'),
 c('D102','Device:D_Schottky','B360A / 60V',72,48,{1:'VIN_CHG',2:'DC_FUSED'},'Diode_SMD:D_SMA','B360A','FUXINSEMI','https://datasheet.lcsc.com/datasheet/pdf/4341698a2794575dc7c94af0a06dfb39.pdf?productCode=C6807778'),
 c('D103','Device:D_Zener','SMBJ16A / TVS',99,20,{1:'VIN_CHG',2:'GND'},'Diode_SMD:D_SMB','SMBJ16A','Littelfuse','https://www.littelfuse.com/products/overvoltage-protection/tvs-diodes/surface-mount/smbj/smbj16a'),
 cap('C101','10u / 50V X7R',99,48,'VIN_CHG',fp='Capacitor_SMD:C_1210_3225Metric'),
 cap('C102','100n / 50V',122,48,'VIN_CHG'),
 c('#FLG101','power:PWR_FLAG','PWR_FLAG',122,20,{1:'VIN_CHG'},in_bom=False),
 c('#FLG102','power:PWR_FLAG','PWR_FLAG',138,20,{1:'GND'},in_bom=False),
],notes=[(18,175,'INPUT CONTRACT\nSolar: Voltaic P105, 6V class, expected ~5W / Vmp6.01V / Voc7.07V; raw panel, no USB regulator.\nDC: regulated or fused 9-16V battery source; NOT an automotive load-dump qualified input.\nD101/D102 provide source ORing, reverse-polarity blocking and prevent DC feeding the panel.\nHigher-voltage DC normally wins. Both inputs may be connected. Grounds are common.\nSMBJ16A: 16V standoff, specified clamp26V at rated pulse; replace old SMBJ26A.\nTVS is AFTER blocking diodes; reversed input must not forward-bias the TVS.\nF101/F102 protect wiring; coordinate source fault current/fuse/TVS energy during bench validation.\nBoard connectors are internal JST PH pigtail landings; external weatherproof connector remains mechanical scope.\nNo input bypasses the cell: system operation requires a valid battery.')])

charger=dict(name='1S LTO charger',file='charger.kicad_sch',exports=['VIN_CHG','VBAT','GND','3V3','CHG_STAT1','CHG_STAT2'],comps=[
 c('U201','tenkiro:BQ24650RVAR','BQ24650RVAR',40,30,{1:'CHG_VCC',2:'MPPSET',3:'CHG_STAT1',4:'CHG_TS',5:'CHG_STAT2',6:'CHG_VREF',7:'CHG_VREF',8:'CHG_VFB',9:'VBAT',10:'CHG_SRP',11:'GND',12:'CHG_REGN',13:'CHG_LODRV',14:'CHG_SW',15:'CHG_HIDRV',16:'CHG_BTST',17:'GND'},CUSTOM['BQ24650RVAR'][1],'BQ24650RVAR','Texas Instruments',TI+'bq24650.pdf'),
 c('Q201','Transistor_FET:Q_NMOS_GSD','DMN6075S-7 / 60V',75,22,{1:'CHG_HIDRV',2:'CHG_SW',3:'VIN_CHG'},'Package_TO_SOT_SMD:SOT-23','DMN6075S-7','Diodes Incorporated','https://www.diodes.com/datasheet/download/DMN6075S.pdf'),
 c('Q202','Transistor_FET:Q_NMOS_GSD','DMN6075S-7 / 60V',75,40,{1:'CHG_LODRV',2:'GND',3:'CHG_SW'},'Package_TO_SOT_SMD:SOT-23','DMN6075S-7','Diodes Incorporated','https://www.diodes.com/datasheet/download/DMN6075S.pdf'),
 c('L201','Device:L','10uH / 3.2A',97,22,{1:'CHG_SW',2:'CHG_SRP'},'Inductor_SMD:L_Bourns_SRN6045TA','SRN6045TA-100M','Bourns','https://www.bourns.com/docs/Product-Datasheets/SRN6045TA.pdf'),
 r('R201','80m / 1% / 0.5W',119,22,'CHG_SRP','VBAT',fp='Resistor_SMD:R_2010_5025Metric',mpn='WSL2010R0800FEA',mfr='Vishay'),
 cap('C201','4.7u / 50V X7R',139,22,'VBAT',fp='Capacitor_SMD:C_1210_3225Metric'),
 cap('C202','100n / 50V',97,40,'CHG_BTST','CHG_SW'),
 c('D201','Device:D_Schottky','BAT46W / 100V',119,40,{1:'CHG_BTST',2:'CHG_REGN'},'Diode_SMD:D_SOD-123','BAT46W-7-F','Diodes Incorporated','https://www.diodes.com/assets/Datasheets/ds30123.pdf'),
 cap('C203','1u / 16V',139,40,'CHG_REGN'),
 r('R202','10R',20,57,'VIN_CHG','CHG_VCC'),cap('C204','1u / 50V X5R',38,57,'CHG_VCC'),
 r('R203','348k / 1%',57,57,'VIN_CHG','MPPSET'),r('R204','100k / 0.1%',77,57,'MPPSET','GND'),
 r('R205','30.9k / 0.1%',97,57,'VBAT','CHG_VFB'),r('R206','100k / 0.1%',117,57,'CHG_VFB','GND'),
 cap('C205','100n / 16V',139,57,'CHG_SRP','VBAT'),
 r('R207','6.04k / 1%',20,75,'CHG_VREF','CHG_TS'),r('R208','33.2k / 1%',40,75,'CHG_TS','GND'),
 connector('J201','Cell NTC: 103AT-2',65,75,'CHG_TS','GND'),cap('C206','1u / 10V',87,75,'CHG_VREF'),
 r('R209','100k',108,75,'3V3','CHG_STAT1'),r('R210','100k',129,75,'3V3','CHG_STAT2'),
 c('#FLG201','power:PWR_FLAG','PWR_FLAG',140,75,{1:'CHG_VCC'},in_bom=False),
],notes=[(18,213,'CC/CV: 2.7489V nominal = 2.1*(1+30.9k/100k), 0.5A = 40mV/80mOhm. Termination enabled.\nMPP input setpoint5.376V AFTER ORing: usable with6V panel and9-16VDC; hot/weak panel performance must be measured.\nNTC is attached to CELL, not PCB. 6.04k/33.2k with103AT-2 targets roughly -5..40C; open/short inhibits charge.\nPrecharge/termination50mA; depleted-cell precharge is limited to30minutes. Validate recovery with selected cell.\nL201/C201 plus TPS63900 input capacitance form ONE charger filter: nominal10uH/14.7uF ->13.1kHz.\nMLCC effective capacitance, tolerances and loop stability remain required bench checks. Kelvin route R201 sense.')])

rail=dict(name='3V3 rail and UVLO',file='rail.kicad_sch',exports=['VBAT','GND','3V3'],comps=[
 c('U301','tenkiro:TPS63900DSKR','TPS63900DSKR',40,29,{10:'VBAT',1:'BAT_OK',2:'GND',3:'BB_CFG1',4:'GND',5:'BB_CFG3',9:'BB_LX1',7:'BB_LX2',6:'3V3',8:'GND',11:'GND'},CUSTOM['TPS63900DSKR'][1],'TPS63900DSKR','Texas Instruments',TI+'tps63900.pdf'),
 c('L301','Device:L','2.2uH / 20%',78,22,{1:'BB_LX1',2:'BB_LX2'},'tenkiro:L_Murata_DFE201612E','DFE201612E-2R2M=P2','Murata','https://datasheet.lcsc.com/datasheet/pdf/9a2227c0960d033e774a76ebdabff58d.pdf?productCode=C337893'),
 cap('C301','10u / 50V X7R',100,22,'VBAT',fp='Capacitor_SMD:C_1210_3225Metric'),
 cap('C302','22u / 25V X7R',123,22,'3V3',fp='Capacitor_SMD:C_1210_3225Metric'),
 r('R301','36.5k / 1%',78,43,'BB_CFG1','GND'),r('R302','16.2k / 1%',101,43,'BB_CFG3','GND'),
 c('U302','tenkiro:TLV3012BIDBVR','TLV3012BIDBVR',40,66,{6:'VBAT',3:'UV_SENSE',4:'UV_REF',2:'GND',5:'UV_REF',1:'BAT_OK'},CUSTOM['TLV3012BIDBVR'][1],'TLV3012BIDBVR','Texas Instruments',TI+'tlv3012.pdf'),
 r('R303','750k / 0.1%',78,66,'VBAT','UV_SENSE'),r('R304','1M / 0.1%',100,66,'UV_SENSE','GND'),r('R305','7.5M / 1%',123,66,'BAT_OK','UV_SENSE'),
 cap('C303','100n / 10V',78,84,'VBAT'),cap('C304','10n / 10V',100,84,'UV_REF'),
],notes=[(18,227,'Both output presets3.3V: CFG1=36.5k, CFG2=GND, CFG3=16.2k; SEL=GND. Input current limit unlimited.\nHardware UVLO: ideal thresholds2.09V off /2.30V on. Include comparator offset/reference/hysteresis in bench trip tests.\nUVLO keeps TPS input above its1.8V minimum and suppresses weak-battery restart cycling. Gauge loses power below UVLO.\nC301 counts toward charger filter! 3V3 output may have local bulk; do not add arbitrary VBAT bulk.\nPM pod: budget180mA peak on3V3, switch fully off between samples; schedule separately from radio TX.')])

gauge=dict(name='Battery and fuel gauge',file='battery.kicad_sch',exports=['VBAT','GND','3V3','I2C_SCL','I2C_SDA'],comps=[
 connector('J401','1S LTO PACK ONLY',21,20,'BAT_RAW','BAT_NEG'),
 c('F401','Device:Fuse','2A / 63V',48,20,{1:'BAT_RAW',2:'VBAT'},'Fuse:Fuse_1206_3216Metric','0466002.NRHF','Littelfuse'),
 r('R401','10m / 1% / 0.5W',74,20,'BAT_NEG','GND',fp='Resistor_SMD:R_2010_5025Metric',mpn='WSL2010R0100FEA',mfr='Vishay'),
 c('U401','tenkiro:BQ34Z100PWR-G1','BQ34Z100PWR-G1',43,49,{1:'BAT_NEG',2:None,3:'BAT_NEG',4:'GAUGE_BAT',5:'3V3',6:'3V3',7:'GAUGE_REG25',8:'BAT_NEG',9:'GAUGE_SRP',10:'GAUGE_SRN',11:'GAUGE_TS',12:None,13:'I2C_SCL',14:'I2C_SDA'},CUSTOM['BQ34Z100PWR-G1'][1],'BQ34Z100PWR-G1','Texas Instruments',TI+'bq34z100-g1.pdf'),
 r('R402','220R',99,20,'BAT_RAW','GAUGE_BAT'),cap('C401','100n / 10V',123,20,'GAUGE_BAT','BAT_NEG'),
 r('R403','100R',78,45,'BAT_NEG','GAUGE_SRP'),r('R404','100R',101,45,'GND','GAUGE_SRN'),cap('C402','100n / 10V',124,45,'GAUGE_SRP','GAUGE_SRN'),
 cap('C403','100n / 10V',78,65,'3V3','BAT_NEG'),cap('C404','1u / 10V',101,65,'GAUGE_REG25','BAT_NEG'),
 connector('J402','Gauge NTC: 103AT-2',124,65,'GAUGE_TS','BAT_NEG'),
 r('R405','10k',78,85,'3V3','I2C_SCL'),r('R406','10k',101,85,'3V3','I2C_SDA'),
 c('#FLG401','power:PWR_FLAG','PWR_FLAG',128,85,{1:'VBAT'},in_bom=False),c('#FLG402','power:PWR_FLAG','PWR_FLAG',141,85,{1:'BAT_NEG'},in_bom=False),
],notes=[(18,230,'REV-A CELL: GWL LTO1865-13 class,1S1P,1.3Ah nominal /0.95Ah guaranteed minimum; keyed fused pigtail.\nGauge VSS/local caps are BAT_NEG, NOT system GND. All charger/load returns must cross R401.\nSRP is cell-negative side; SRN is system-ground side. Kelvin routing; never short BAT_NEG to GND elsewhere.\nREGIN and CE from3V3; REG25 decoupled only. BAT measures raw cell through220R, no high-voltage divider.\nSeparate thermistors J201/J402: do not share biased TS nodes. Select GPCCHEM ChemID/calibrate/learn actual cell.\nNo lithium-ion4.2V substitute. External cell pigtail needs its own fuse near the cell; PCB fuse cannot protect that lead.')])

# Draw the source paths and the charger power stage as continuous circuits.
# Short labelled wires handle the remaining control/sense interfaces.
def place(sheet, placements):
    for cc in sheet['comps']:
        if cc['ref'] in placements:
            x,y,angle=placements[cc['ref']]
            cc.update(x=x*G,y=y*G,rotation=angle)

place(input_sheet,{'F101':(35,20,90),'F102':(35,48,90),
    'D101':(55,20,180),'D102':(55,48,180),'D103':(80,34,270),
    'C101':(100,34,0),'C102':(120,34,0)})
input_sheet['routes']=[['J101.1','F101.1'],['F101.2','D101.2'],
    ['J102.1','F102.1'],['F102.2','D102.2'],
    ['D101.1',[80,20],[80,32.5],'D103.1'],
    ['D102.1',[70,48],[70,20],[80,20]],
    ['C101.1',[100,20],[80,20]],['C102.1',[120,20],[100,20]]]
# Shared points require explicit junctions, emitted below by the helper.
input_sheet['junctions']=[[80,20],[100,20],[70,20]]
place(charger,{'L201':(97,31,90),'R201':(119,31,90),
    'C201':(139,41,0),'C205':(130,45,0), 'C202':(97,44,0),
    'D201':(119,43,0),'C203':(139,58,0),'R205':(97,62,0),'R206':(97,73,0)})
charger['routes']=[['Q201.2',[76,31],'Q202.3'],
    ['L201.1',[76,31]],['L201.2','R201.1'],
    ['R201.2',[139,31],'C201.1'],['R205.2','R206.1']]
charger['junctions']=[[76,31]]
# The SRP common-mode bypass is required in addition to the differential filter.
charger['comps'].append(cap('C207','100n / 10V',119,62,'CHG_SRP'))

build('tenkiro-sora',[input_sheet,charger,rail,gauge,radio()],
 'A0 POWER/RADIO CAPTURE — fully wired sheets, not a complete station PCB.\n'
 'Root net labels interconnect sheets. MCU, sensor rails, mast-bus interface and sensor sheets remain to be captured.\n'
 'RADIO_* and I2C_* are3.3V host interfaces; CHG_STAT1/2 are open-drain status. 3V3 powers the future host.\n'
 'Base target<=0.06Wh/day; optional SPS30 budget60s/hour, off otherwise. No TX during pod/fan startup.\n'
 'See DESIGN.md and hardware/specs/power-radio.md for limits, calculations and release gates.')
