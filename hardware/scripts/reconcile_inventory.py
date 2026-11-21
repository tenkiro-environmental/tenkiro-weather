#!/usr/bin/env python3
"""Reconcile the captured BOM, owned JLCPCB balance and verified shortage cart.

The dated inputs are snapshots, not a live stock query or inventory reservation.
CERN-OHL-S-2.0.
"""
from pathlib import Path
from collections import Counter
import csv
import json
import re
import xml.etree.ElementTree as ET

HW = Path(__file__).resolve().parents[1]
BOM = HW / 'bom'
INVENTORY = HW.parents[1] / 'jlcpcb-private-inventory.csv'
SETS = 10


def main():
    inventory = {r['lcsc_part_number']: r for r in csv.DictReader(INVENTORY.open())}
    selection = json.loads((BOM / 'selected-parts.json').read_text())
    cart_record = json.loads((BOM / 'cart-verified-2026-10-03.json').read_text())
    cart = {r['code']: r for r in cart_record['parts']}
    assert len(cart) == len(cart_record['parts']), 'Duplicate cart lines'
    groups = {}
    for board in ['sora', 'hashi']:
        directory = HW / f'tenkiro-{board}'
        manifest = {c['ref']: c for sh in json.loads((directory / 'capture-manifest.json').read_text()) for c in sh['comps']}
        exported = {c.attrib['ref']: c for c in ET.parse(directory / 'docs/capture.xml').findall('./components/comp')}
        fitted = {ref for ref, c in manifest.items() if not c.get('dnp') and c.get('in_bom', True)}
        assert fitted == set(selection[board]), (board, 'Incomplete sourcing')
        # Equal values/packages may still use different owned ordering codes.
        exported_counts = Counter()
        for row in csv.DictReader((directory / 'jlcpcb_bom.csv').open()):
            assert re.fullmatch(r'C\d+', row['LCSC Part #']), (board, 'Ambiguous grouped BOM line', row)
            exported_counts[row['LCSC Part #']] += int(row['Qty'])
        assert exported_counts == Counter(p['lcsc'] for p in selection[board].values()), (board, 'BOM quantities differ from fitted symbols')
        for ref, part in selection[board].items():
            c = exported[ref]
            fields = {f.attrib['name']: f.text for f in c.findall('./fields/field')}
            assert fields['LCSC'] == part['lcsc'] and fields['MPN'] == part['mpn'], (board, ref)
            assert fields['Manufacturer'] == part['mfr'] and c.findtext('datasheet') == part['datasheet'], (board, ref)
            assert c.findtext('value') == manifest[ref]['value'] and c.findtext('footprint') == manifest[ref]['fp'], (board, ref)
            code = part['lcsc']
            g = groups.setdefault(code, dict(part, sora=[], hashi=[], footprints=set(), values=set()))
            assert g['mpn'] == part['mpn']
            g[board].append(ref)
            g['footprints'].add(c.findtext('footprint'))
            g['values'].add(c.findtext('value'))
    assert set(cart) <= set(groups), 'Cart contains unrelated new parts'
    rows = []
    for code, g in sorted(groups.items(), key=lambda x: int(x[0][1:])):
        base = SETS * (len(g['sora']) + len(g['hashi']))
        owned = int(inventory.get(code, {}).get('total_private_qty') or 0)
        incoming = int(inventory.get(code, {}).get('incoming_qty') or 0)
        purchase = cart.get(code, {})
        if purchase:
            target = purchase['quantity']
            assert purchase['available'] >= target >= base, code
        else:
            # Owned small passives: ten spare tape positions per board type.
            # Owned ICs, modules and power diodes: 20%, minimum two.
            refs = g['sora'] + g['hashi']
            target = base + (10 * sum(bool(g[b]) for b in ['sora', 'hashi'])
                             if all(r[0] in 'RC' for r in refs) else max(2, (base + 4) // 5))
            assert owned >= target, (code, owned, target)
        rows.append(dict(
            lcsc=code, mpn=g['mpn'], manufacturer=g['mfr'],
            sora_references=' '.join(sorted(g['sora'])), hashi_references=' '.join(sorted(g['hashi'])),
            sora_per_board=len(g['sora']), hashi_per_board=len(g['hashi']),
            sets=SETS, assembly_quantity=base, spare_quantity=target-base, target_quantity=target,
            owned_snapshot_quantity=owned, incoming_quantity=incoming,
            shortage_quantity=max(0, target-owned-incoming),
            cart_quantity=purchase.get('quantity', 0), jlcpcb_available=purchase.get('available', ''),
            unit_price_usd=purchase.get('unit_price_usd', ''), line_total_usd=purchase.get('line_total_usd', 0),
            values='; '.join(sorted(g['values'])), footprints='; '.join(sorted(g['footprints'])),
            datasheet=g['datasheet'], source='owned inventory' if owned >= target else 'incoming order' if owned+incoming >= target else 'uncovered requirement'))
    placements = sum(len(parts) for parts in selection.values())
    assert sum(r['assembly_quantity'] for r in rows) == SETS * placements
    assert all(r['shortage_quantity'] <= r['cart_quantity'] for r in rows)
    total = round(sum(r['line_total_usd'] for r in rows), 2)
    assert total == cart_record['subtotal_usd']
    with (BOM / 'inventory-comparison-10-sets.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    with (BOM / 'shortage-cart-10-sets.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['LCSC Part #', 'MPN', 'Manufacturer', 'Quantity', 'Line total USD'])
        writer.writeheader()
        writer.writerows({'LCSC Part #':r['lcsc'], 'MPN':r['mpn'], 'Manufacturer':r['manufacturer'],
                          'Quantity':r['shortage_quantity'], 'Line total USD':r['line_total_usd'] if r['shortage_quantity']==r['cart_quantity'] else ''}
                         for r in rows if r['shortage_quantity'])
    summary = dict(sets=SETS, placements_per_set=placements, total_placements=SETS * placements, selected_codes=len(rows),
                   owned_codes=sum(bool(r['owned_snapshot_quantity']) for r in rows),
                   placements_covered_by_owned=sum(r['assembly_quantity'] for r in rows if r['owned_snapshot_quantity']),
                   shortage_lines=sum(r['shortage_quantity'] > 0 for r in rows),
                   shortage_parts=sum(r['shortage_quantity'] for r in rows),
                   incoming_lines=sum(r['incoming_quantity'] > 0 for r in rows),
                   incoming_parts=sum(r['incoming_quantity'] for r in rows),
                   cart_snapshot_lines=len(cart), cart_parts=sum(r['cart_quantity'] for r in rows), subtotal_usd=total,
                   inventory_snapshot_utc=next(iter(inventory.values()))['snapshot_utc'],
                   cart_verified_at=cart_record['verified_at'],
                   reservation_status='Not reserved; on-hand reservation breakdown unknown; incoming tracked separately from user-confirmed orders',
                   validation=f'All {placements} fitted symbol properties and footprints agree with selection and manifest')
    (BOM / 'reconciliation-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
