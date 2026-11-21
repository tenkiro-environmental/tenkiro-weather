"""Shared power/radio capture helpers. CERN-OHL-S-2.0; no external EDA dependency.

Per-board manifests own components, values, interfaces and pin/net intent.
Existing sheets are preserved unless KSCHGEN_FORCE=1 is explicitly requested.
"""
from pathlib import Path
import json
import re
import uuid
import kschgen as K

HW = Path(__file__).resolve().parents[1]
LIB = HW / 'lib/symbols/tenkiro.kicad_sym'
G = 2.54
RFP = 'Resistor_SMD:R_0603_1608Metric'
CFP = 'Capacitor_SMD:C_0603_1608Metric'
JFP = 'Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical'
TI = 'https://www.ti.com/lit/ds/symlink/'

def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://github.com/tenkiro-environmental/tenkiro-weather/'+name))

def c(ref, lib, value, x, y, nets, fp='', mpn='', mfr='', datasheet='', **kw):
    return dict(ref=ref, lib_id=lib, value=value, x=x*G, y=y*G,
                nets={str(k):v for k,v in nets.items()}, fp=fp, mpn=mpn,
                mfr=mfr, datasheet=datasheet, **kw)

def r(ref, value, x, y, a, b, **kw):
    return c(ref,'Device:R',value,x,y,{1:a,2:b},fp=kw.pop('fp',RFP),**kw)

def cap(ref, value, x, y, a, b='GND', **kw):
    return c(ref,'Device:C',value,x,y,{1:a,2:b},fp=kw.pop('fp',CFP),**kw)

def connector(ref, value, x, y, a, b, **kw):
    return c(ref,'Connector:Conn_01x02_Pin',value,x,y,{1:a,2:b},JFP,
             'B2B-PH-K-S(LF)(SN)','JST',**kw)

def symbol(name, pins, footprint, url):
    # pins = (number, name, electrical type, side). Exposed pads are visible.
    sides={'L':[], 'R':[]}
    for p in pins: sides[p[3]].append(p)
    half=max(len(v) for v in sides.values())*1.27+2.54
    out=f'\n\t(symbol "{name}" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)\n'
    for k,v,yy in [('Reference','U',half+2.54),('Value',name,-half-2.54),('Footprint',footprint,0),('Datasheet',url,0)]:
        hide=' hide' if k in ('Footprint','Datasheet') else ''
        out+=f' (property "{k}" "{v}" (at 0 {yy} 0) (effects (font (size 1.27 1.27)){hide}))\n'
    out+=f' (symbol "{name}_0_1" (rectangle (start -12.7 {half}) (end 12.7 {-half}) (stroke (width 0.254) (type default)) (fill (type background))))\n'
    out+=f' (symbol "{name}_1_1"\n'
    for side,pp in sides.items():
        for i,(num,pn,typ,_) in enumerate(pp):
            x,angle=(-17.78,0) if side=='L' else (17.78,180)
            y=(len(pp)-1)*1.27-i*2.54
            out+=f' (pin {typ} line (at {x} {y} {angle}) (length 5.08) (name "{pn}" (effects (font (size 1.016 1.016)))) (number "{num}" (effects (font (size 1.016 1.016)))))\n'
    return out+' ))\n'

CUSTOM={
 'BQ24650RVAR': (
  [(1,'VCC','power_in','L'),(2,'MPPSET','input','L'),(4,'TS','input','L'),(6,'VREF','power_out','L'),(7,'TERM_EN','input','L'),(8,'VFB','input','L'),(11,'GND','power_in','L'),(17,'EP','power_in','L'),(16,'BTST','passive','R'),(15,'HIDRV','output','R'),(14,'PH','passive','R'),(13,'LODRV','output','R'),(12,'REGN','power_out','R'),(10,'SRP','input','R'),(9,'SRN','input','R'),(3,'STAT1','open_collector','R'),(5,'STAT2','open_collector','R')],
  'Package_DFN_QFN:Texas_RVA_VQFN-16-1EP_3.5x3.5mm_P0.5mm_EP2.14x2.14mm',TI+'bq24650.pdf'),
 'BQ34Z100PWR-G1': (
  [(4,'BAT','input','L'),(5,'CE','input','L'),(6,'REGIN','power_in','L'),(7,'REG25','power_out','L'),(8,'VSS','power_in','L'),(9,'SRP','input','L'),(10,'SRN','input','L'),(1,'P2','passive','R'),(2,'VEN','output','R'),(3,'P1','passive','R'),(11,'P6_TS','input','R'),(12,'P5_HDQ','bidirectional','R'),(13,'P4_SCL','input','R'),(14,'P3_SDA','bidirectional','R')],
  'Package_SO:TSSOP-14_4.4x5mm_P0.65mm',TI+'bq34z100-g1.pdf'),
 'TPS63900DSKR': (
  [(10,'VIN','power_in','L'),(1,'EN','input','L'),(2,'SEL','input','L'),(3,'CFG1','passive','L'),(4,'CFG2','passive','L'),(5,'CFG3','passive','L'),(9,'LX1','passive','R'),(7,'LX2','passive','R'),(6,'VOUT','power_out','R'),(8,'GND','power_in','R'),(11,'EP','power_in','R')],
  'Package_SON:WSON-10-1EP_2.5x2.5mm_P0.5mm_EP1.2x2mm',TI+'tps63900.pdf'),
 'TLV3012BIDBVR': (
  [(6,'V+','power_in','L'),(3,'IN+','input','L'),(4,'IN-','input','L'),(2,'V-','power_in','L'),(5,'REF','output','R'),(1,'OUT','output','R')],
  'Package_TO_SOT_SMD:SOT-23-6',TI+'tlv3012.pdf'),
 'E22-900M22S': (
  [(9,'VCC','power_in','L'),(19,'NSS','input','L'),(18,'SCK','input','L'),(17,'MOSI','input','L'),(16,'MISO','output','L'),(15,'NRST','input','L'),(14,'BUSY','output','L'),(13,'DIO1','bidirectional','L'),(6,'RXEN','input','L'),(7,'TXEN','input','L'),(8,'DIO2','bidirectional','L'),(21,'ANT','passive','R')]+[(n,'GND','power_in','R') for n in [1,2,3,4,5,10,11,12,20,22]],
  'tenkiro:E22-900M22S_14x20mm','https://www.cdebyte.com/pdf-down.aspx?id=4216'),
}

def libraries():
    LIB.write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor")\n'+''.join(symbol(n,*v) for n,v in CUSTOM.items())+')\n')
    for lib,names in {'Device':['R','C','L','D_Schottky','D_Zener','D_TVS','Fuse'], 'Transistor_FET':['Q_NMOS_GSD'], 'Connector':['Conn_01x02_Pin','Conn_Coaxial','TestPoint'], 'Connector_Generic':['Conn_01x14','Conn_01x10'], 'power':['PWR_FLAG']}.items():
        K.register_stdlib(lib,*names)
    K.register_lib('tenkiro',str(LIB),*CUSTOM)
    # Top-view pad numbering from Ebyte E22-M manual v1.5, PDF p10. Pad size includes
    # 0.9mm outward solder toe beyond the module's 0.9mm bottom metallization.
    out='(footprint "E22-900M22S_14x20mm" (version 20241229) (generator "pcbnew") (layer "F.Cu") (attr smd)\n'
    out+=' (property "Reference" "REF**" (at 0 -11.5 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))\n'
    out+=' (property "Value" "E22-900M22S" (at 0 11.5 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))\n'
    for layer,dx,dy,width in [('F.Fab',7,10,0.1),('F.CrtYd',8.5,10.5,0.05),('F.SilkS',5.7,10.1,0.12)]:
        out+=f' (fp_rect (start {-dx} {-dy}) (end {dx} {dy}) (stroke (width {width}) (type solid)) (layer "{layer}"))\n'
    ys=[-8+i*1.27 for i in range(8)]+[6.46,7.73,9.0]
    for side,nums in [(-1,range(12,23)),(1,list(range(11,3,-1))+[3,2,1])]:
        for n,y in zip(nums,ys):
            out+=f' (pad "{n}" smd rect (at {side*7.0} {y:.2f}) (size 1.8 0.8) (layers "F.Cu" "F.Paste" "F.Mask"))\n'
    out+=' (fp_circle (center 8.0 9.0) (end 8.15 9.0) (stroke (width 0.15) (type solid)) (fill solid) (layer "F.SilkS"))\n)\n'
    (HW/'lib/footprints.pretty/E22-900M22S_14x20mm.kicad_mod').write_text(out)

def radio():
    nets={9:'3V3',19:'RADIO_NSS',18:'RADIO_SCK',17:'RADIO_MOSI',16:'RADIO_MISO',15:'RADIO_NRST',14:'RADIO_BUSY',13:'RADIO_DIO1',6:'RADIO_RXEN',7:'RADIO_TXEN',8:'RADIO_DIO2',21:'RF_MODULE'}
    nets.update({n:'GND' for n in [1,2,3,4,5,10,11,12,20,22]})
    return dict(name='Radio',file='radio.kicad_sch',exports=['3V3','GND','RADIO_NSS','RADIO_SCK','RADIO_MOSI','RADIO_MISO','RADIO_NRST','RADIO_BUSY','RADIO_DIO1','RADIO_RXEN'],
     comps=[c('U501','tenkiro:E22-900M22S','E22-900M22S',43,35,nets,*CUSTOM['E22-900M22S'][1:2],mpn='E22-900M22S',mfr='Ebyte',datasheet=CUSTOM['E22-900M22S'][2]),
       r('R501','0R',80,23,'RADIO_DIO2','RADIO_TXEN'),r('R502','100k',96,23,'RADIO_RXEN','GND'),r('R503','100k',112,23,'3V3','RADIO_NSS'),r('R504','100k',128,23,'3V3','RADIO_NRST'),
       cap('C501','100n / 16V',80,44,'3V3'),cap('C502','10u / 50V X7R',96,44,'3V3',fp='Capacitor_SMD:C_1210_3225Metric'),cap('C503','22u / 25V X7R',112,44,'3V3',fp='Capacitor_SMD:C_1210_3225Metric'),cap('C505','22u / 25V X7R',128,44,'3V3',fp='Capacitor_SMD:C_1210_3225Metric'),
       r('R506','0R external RF',65,67,'RF_MODULE','RF_UFL'),
       c('J501','Connector:Conn_Coaxial','U.FL external antenna',93,67,{1:'RF_UFL',2:'GND'},'Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical','U.FL-R-SMT-1(10)','Hirose'),
       cap('C504','DNP RF shunt',112,67,'RF_UFL',dnp=True),
       c('D501','Device:D_TVS','PESD5V0F1BRSF',130,67,{1:'RF_UFL',2:'GND'},'Diode_SMD:Nexperia_DSN0603-2_0.6x0.3mm_P0.4mm','PESD5V0F1BRSF','Nexperia','https://assets.nexperia.com/documents/data-sheet/PESD5V0F1BRSF.pdf',rotation=270)],
     notes=[(18,205,'SPI module, not UART T variant. MCU controls RXEN; DIO2 controls TXEN through R501.\nRXEN low during TX/sleep; set DIO2 RF-switch control in firmware. 3.3 V supply, budget 124 mA TX.\nSTART: 915 MHz, SF7 / 125 kHz / CR4/5, +14 dBm, 60 s packet interval.\nDo not fit/use two antennas: R506 connects board U.FL; remove R506 if using module IPEX.\nPin 12 = GND, pin 15 = NRST per official E22-M V1.5 (2026-09-18), not the erroneous web pin table.\nInternal DIO3 TCXO supply = 2.2 V per official manual 4.2; initial startup delay 5 ms, verify at temperature.\nPCB: short 50-ohm RF trace, continuous GND, antenna keepout, close C501/C502/C503/C505.\nD501: bidirectional 5 V / 0.25 pF RF ESD at U.FL; C504 DNP tuning. Verify RF loss and ESD on PCB.')])

def build(project, sheets, overview):
    # Keep sourced ordering codes in generated symbols as well as the live sheets.
    sourcing_file = HW / 'bom/selected-parts.json'
    sourcing = json.loads(sourcing_file.read_text()).get(project.removeprefix('tenkiro-'), {}) if sourcing_file.exists() else {}
    for sheet in sheets:
        for component in sheet['comps']:
            component.update(sourcing.get(component['ref'], {}))
    libraries()
    # A real DNP commissioning header terminates the host boundary without
    # pretending that the future MCU sheet has already been implemented.
    host=['3V3','GND','RADIO_NSS','RADIO_SCK','RADIO_MOSI','RADIO_MISO','RADIO_NRST','RADIO_BUSY','RADIO_DIO1','RADIO_RXEN']
    if project.endswith('sora'): host+=['I2C_SCL','I2C_SDA','CHG_STAT1','CHG_STAT2']
    count=len(host)
    host_comps=[c('J901',f'Connector_Generic:Conn_01x{count}','DNP commissioning host',42,39,dict(enumerate(host,1)),f'Connector_PinHeader_2.54mm:PinHeader_1x{count}_P2.54mm_Vertical',dnp=True)]
    if project.endswith('hashi'):
        host_comps += [c('#FLG901','power:PWR_FLAG','PWR_FLAG',80,30,{1:'3V3'},in_bom=False),c('#FLG902','power:PWR_FLAG','PWR_FLAG',100,30,{1:'GND'},in_bom=False)]
    sheets.append(dict(name='Commissioning host interface',file='host_interface.kicad_sch',exports=host,comps=host_comps,
        notes=[(18,175,'DNP header allows power/radio bring-up with an external 3.3 V MCU. Final onboard MCU is not captured yet.\nPin 1 = 3V3, pin 2 = GND; all IO must be 3.3 V. Never apply 5 V to any pin.\nSora: pin 1 is an OUTPUT; do not drive 3V3 from the external host while the battery rail is powered.\nHashi: pin 1 is an INPUT; external regulated 3.3 V supply must allocate >= 200 mA for radio.\nHost supplies SPI SCK/MOSI/NSS, NRST and RXEN; reads MISO/BUSY/DIO1.\nOptional Sora pins 11/12 are I2C SCL/SDA; pins 13/14 read CHG_STAT1/2.\nHeaders are explicitly DNP and can be removed when the actual MCU sheets replace this boundary.')]))
    directory=HW/project
    directory.mkdir(exist_ok=True)
    (directory/'sym-lib-table').write_text('(sym_lib_table (version 7)\n (lib (name "tenkiro") (type "KiCad") (uri "${KIPRJMOD}/../lib/symbols/tenkiro.kicad_sym") (options "") (descr "Tenkiro authored parts")))\n')
    root=K._schematic_uuid(directory/(project+'.kicad_sch')) or uid(project)
    pro=directory/(project+'.kicad_pro')
    if not pro.exists(): pro.write_text(json.dumps({'meta':{'filename':project+'.kicad_pro','version':1},'sheets':[]},indent=2)+'\n')
    title=dict(title=project,date='2026-10-03',rev='A0',company='Tenkiro')
    root_sheets=''; root_wiring=''; pro_sheets=[]; expected={}
    for i,sh in enumerate(sheets):
        existed=(directory/sh['file']).exists()
        su=K._schematic_uuid(directory/sh['file']) or uid(project+'/'+sh['file'])
        path=f'/{root}/{su}'
        wiring=''; placed=[]
        byref={cc['ref']:cc for cc in sh['comps']}
        routed={item for route in sh.get('routes',[]) for item in route if isinstance(item,str)}
        for route in sh.get('routes',[]):
            points=[]; route_nets=set()
            for item in route:
                if isinstance(item,str):
                    ref,pn=item.split('.')
                    points.append(K.pin_at(byref[ref],pn)[:2])
                    route_nets.add(byref[ref]['nets'][pn])
                else: points.append(tuple(v*G for v in item))
            assert len(route_nets)==1, route
            for a,b in zip(points,points[1:]):
                assert a[0]==b[0] or a[1]==b[1], (route,a,b)
                if a!=b: wiring+=K.w_wire(*a,*b)
            a,b=max(zip(points,points[1:]),key=lambda pair:sum(abs(x-y) for x,y in zip(*pair)))
            wiring+=K.w_label(next(iter(route_nets)),round((a[0]+b[0])/2,4),round((a[1]+b[1])/2,4))
        for xx,yy in sh.get('junctions',[]):
            wiring+=f'(junction (at {xx*G:.4f} {yy*G:.4f}) (diameter 0) (color 0 0 0 0) (uuid "{K.U()}"))\n'
        for cc in sh['comps']:
            pins=K.pin_geom(cc['lib_id']); numbers={p['number'] for p in pins}
            assert numbers==set(cc['nets']), (cc['ref'],numbers,set(cc['nets']))
            seen=set()
            for pn,net in cc['nets'].items():
                x,y,ang=K.pin_at(cc,pn)
                if net is None:
                    wiring+=f'(no_connect (at {x} {y}) (uuid "{K.U()}"))\n'
                elif cc['ref']+'.'+pn not in routed and (x,y,net) not in seen:
                    # Horizontal labels on vertical passive stubs are easier to read.
                    dx,dy=K._OUTWARD[ang]; stub=7.62 if cc['ref'].startswith('D') else 2.54
                    ex=x+dx*stub; ey=y+dy*stub
                    label=K.w_label(net,ex,ey,0)
                    if dx<0: label=label.replace('(justify left bottom)','(justify right bottom)')
                    wiring+=K.w_wire(x,y,ex,ey)+label
                    seen.add((x,y,net))
                expected[cc['ref']+'.'+pn]=net
            placed.append((cc,[(path,cc['ref'])]))
        # One hierarchical port per interface, with a local named wire on child.
        for j,n in enumerate(sh['exports']):
            xx=(8+(j%5)*30)*G; yy=(96+(j//5)*3)*G
            wiring+=K.w_hlabel(n,xx,yy,0,'passive')+K.w_wire(xx,yy,xx+35.56,yy)+K.w_label(n,xx+35.56,yy)
        sh2=dict(sh,_dir=str(directory),uuid=su,title=sh['name'],page=str(i+2),comps=placed,wiring=wiring)
        K.write_wired_child(sh2,project,root,title,paper='A3')
        # Pull IC text clear of its body (generated placements only).
        f=directory/sh['file']
        if K._force_regen() or not existed:
            txt=f.read_text()
            for cc in sh['comps']:
                if cc.get('rotation',0) in (90,270):
                    for key,val,yy in [('Reference',cc['ref'],cc['y']-7.62),('Value',cc['value'],cc['y']-5.08)]:
                        pattern=r'(\(property "'+key+r'" "'+re.escape(val)+r'"\s*\(at )[-\d.]+ [-\d.]+ 0\)'
                        txt=re.sub(pattern,lambda m:m[1]+f'{cc["x"]:.4f} {yy:.4f} {cc["rotation"]})',txt)
                if not cc['ref'].startswith(('U','J')): continue
                pp=K.pin_geom(cc['lib_id']); top=cc['y']-max(p['y'] for p in pp)-8.89
                for key,val,yy in [('Reference',cc['ref'],top),('Value',cc['value'],top+2.54)]:
                    pattern=r'(\(property "'+key+r'" "'+re.escape(val)+r'"\s*\(at )[-\d.]+ [-\d.]+ 0\)'
                    txt=re.sub(pattern,lambda m:m[1]+f'{cc["x"]-12.7:.4f} {yy:.4f} 0)',txt)
            f.write_text(txt)
        x=(12+(i%3)*49)*G; y=(14+(i//3)*36)*G; h=max(40,(len(sh['exports'])+1)*5.08)
        pins=[(n,'passive',x,y+7.62+j*5.08,180) for j,n in enumerate(sh['exports'])]
        root_sheets+=K.w_sheet(sh['name'],sh['file'],su,x,y,65,h,pins)
        for n,_,xx,yy,_ in pins:
            root_wiring+=K.w_wire(xx-5.08,yy,xx,yy)+K.w_label(n,xx-5.08,yy,0).replace('(justify left bottom)','(justify right bottom)')
        pro_sheets.append([su,sh['name']])
    root_wiring+=K.text_note(overview,20,245,1.27)
    K.write_root(project,str(directory),root,title,root_sheets,root_wiring,pro_sheets)
    (directory/'expected-connections.json').write_text(json.dumps(expected,indent=2,sort_keys=True)+'\n')
    # Audit inputs are durable; no fabricated distributor IDs or approval status.
    (directory/'capture-manifest.json').write_text(json.dumps(sheets,indent=2)+'\n')
