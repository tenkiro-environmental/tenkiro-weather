#!/usr/bin/env python3
"""Fail on ERC violations, broken pin/net intent, shorts or missing footprints.

Checks KiCad's exported connectivity, not the generator's internal wiring model.
The committed expected-connections.json is a reviewable design contract.
No fabrication or assembled-circuit validation is implied. CERN-OHL-S-2.0.
"""
from pathlib import Path
import collections
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

HW = Path(__file__).resolve().parents[1]
CLI = os.environ.get('KICAD_CLI', 'kicad-cli')
KICAD = Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')


def run(args):
    result = subprocess.run([CLI, *args], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)


def check(project):
    directory = HW / project
    sch = directory / (project + '.kicad_sch')
    docs = directory / 'docs'
    docs.mkdir(exist_ok=True)
    xml = docs / 'capture.xml'
    erc = docs / 'capture.erc'
    run(['sch', 'export', 'netlist', '--format', 'kicadxml', '-o', str(xml), str(sch)])
    run(['sch', 'erc', '-o', str(erc), str(sch)])
    violations = re.findall(r'^\[([^]]+)\]', erc.read_text(), re.M)
    assert not violations, f'{project}: ERC {collections.Counter(violations)}'
    root = ET.parse(xml).getroot()
    expected = json.loads((directory / 'expected-connections.json').read_text())
    expected = {k:v for k,v in expected.items() if not k.startswith('#')}
    actual = {}
    errors = []
    for net in root.findall('./nets/net'):
        name = net.attrib['name']
        pins = [n.attrib['ref'] + '.' + n.attrib['pin'] for n in net.findall('node')]
        for pin in pins:
            assert pin not in actual, f'{pin} occurs on two nets'
            actual[pin] = name
        intents = {expected[p] for p in pins if p in expected and expected[p] is not None}
        if len(intents) > 1:
            errors.append(f'SHORT: {name}: {sorted(intents)} at {pins}')
    for pin, intent in expected.items():
        net = actual.get(pin)
        if intent is None:
            if net is not None and not net.startswith('unconnected-'):
                errors.append(f'{pin}: expected NC, got {net}')
        elif net is None or net.rsplit('/', 1)[-1] != intent:
            errors.append(f'{pin}: expected {intent}, got {net}')
    extra = set(actual) - set(expected)
    if extra: errors.append(f'Unexpected pins: {sorted(extra)}')
    # Independently extracted manufacturer pin tables check authored symbols.
    checked_ic_pins = 0
    for part in root.findall('./libparts/libpart'):
        if part.attrib.get('lib') != 'tenkiro': continue
        name = part.attrib['part']
        source = HW / 'datasheets/extracted' / (name + '.json')
        if not source.is_file():
            errors.append(f'{name}: missing independent pin extraction')
            continue
        raw = json.loads(source.read_text())['base']['pinout']
        extracted = {}
        for pp in raw:
            for number in pp['numbers']:
                if number == 'EP': number = {'BQ24650RVAR':'17','TPS63900DSKR':'11'}[name]
                extracted[number] = pp['name'].replace('/', '_')
        symbol = {pp.attrib['num']:pp.attrib['name'] for pp in part.findall('./pins/pin')}
        if extracted != symbol:
            errors.append(f'{name}: symbol/extracted pin mismatch: {symbol} / {extracted}')
        checked_ic_pins += len(extracted)
    components = root.findall('./components/comp')
    refs = [cc.attrib['ref'] for cc in components]
    assert len(refs) == len(set(refs)), 'Duplicate references'
    for cc in components:
        ref = cc.attrib['ref']
        footprint = cc.findtext('footprint')
        if not footprint or ':' not in footprint:
            errors.append(f'{ref}: missing footprint')
            continue
        library, name = footprint.split(':', 1)
        location = (HW / 'lib/footprints.pretty' if library == 'tenkiro'
                    else KICAD / (library + '.pretty')) / (name + '.kicad_mod')
        if KICAD.exists() and not location.is_file():
            errors.append(f'{ref}: footprint not found: {footprint}')
    assert not errors, '\n'.join(errors)
    result = dict(project=project, erc_violations=0, components=len(refs),
                  checked_pins=len(expected), exported_nets=len(root.findall('./nets/net')),
                  manufacturer_pin_assignments_checked=checked_ic_pins,
                  status='PASS: capture connectivity only; no bench validation')
    (docs / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    for project in sys.argv[1:] or ['tenkiro-sora', 'tenkiro-hashi']:
        check(project)
