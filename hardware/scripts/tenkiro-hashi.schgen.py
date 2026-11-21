#!/usr/bin/env python3
"""Hashi A0 radio capture; USB/host/sensor sheets follow separately."""
from tenkiro_capture import *

build('tenkiro-hashi',[radio()],
 'A0 RADIO CAPTURE — fully wired radio shared with Sora.\n'
 'Host ESP32-S3, USB-C supply and SCD40 are outside this power/radio capture and are not yet drawn.\n'
 'Host must supply regulated3.3V (>=200mA radio allocation) and the named SPI/control signals.\n'
 'Continuous receive on Hashi; same SX1262/TCXO/RF-switch configuration as Sora.\n'
 'See hardware/specs/power-radio.md for module-revision checks and bring-up requirements.')
