# Hashi wired-Ethernet backup MCU — survey (2026-07)

> **Superseded (2026-07-19):** WIZnet parts were ruled out by decision, so the
> runner-up path is promoted: the Ethernet backup is **STM32H563VGT6 +
> LAN8742A**. A JLCPCB re-check found the survey's H5 stock concern was
> package-specific — STM32H563**VGT6** (LQFP-100, LCSC C18221950) had **8,042**
> in stock vs the ~35–139 of the ZIT6/LQFP-144 checked below; LAN8742A-CZ-TR
> (C621424) 2.6 k, LAN8742AI-CZ-TR (C621425) 3.1 k. The survey below is kept
> for the reasoning and rejected options.

Research supporting the original recommendation: **RP2350A + WIZnet W5500
(SPI)**, runner-up **STM32H723 + LAN8742A**. LCSC prices/stock verified July
2026.

## 1. RP2350A + WIZnet W5500 — ★ chosen

**Parts:** RP2350A (LCSC C42411118) + W5500 (LCSC C32843). RP2350 needs an
external QSPI flash (e.g. W25Q128, a JLCPCB basic part) — the ESP32-S3 plan
already accounts for that class of part.

**Availability (verified):** RP2350A 8,602 in stock, $1.71 @1 / $1.45 @1k.
W5500 51,164 in stock, $2.76 @1 / $1.76 @1k — deep, stable stock (WIZnet's
flagship). Combined silicon ≈ $3.20/board @1k + flash. Both LCSC/JLCPCB-
assemblable; W5500 is a very commonly placed part.

**Ethernet architecture:** W5500 is a hardwired TCP/IP controller (10/100
MAC+PHY + full offloaded stack: 8 sockets of TCP/UDP/IPv4/ICMP/DHCP in-chip)
over **SPI only** — no RMII, no 50 MHz clock tree, no matched pairs beyond
the RJ45 magnetics. Lowest design-complexity path to wired Ethernet. Its
**MACRAW mode** exposes raw L2 frames, so an external stack (smoltcp/lwIP)
can drive it instead — not locked into the hardwired stack.

**Firmware:** first-class both languages. Rust: `embassy-net-wiznet` (MACRAW
over async SPI → embassy-net TCP/UDP/DHCP/DNS) + `embassy-rp`; official
W5500-EVB-Pico example ports trivially from RP2040. C: pico-sdk officially
supports RP2350; WIZnet `ioLibrary_Driver` ships sockets, HTTP server, and
MQTT examples — MQTT + small web UI is essentially a reference-design combo.

**PoE:** possible as add-on (isolated PoE→5V brick or Si3402-class PD +
flyback into the USB-C 5 V rail); nothing in the W5500 path blocks it.

**Gotchas:** RP2350 A2-stepping **E9 GPIO latch/input-pulldown erratum** —
use external pulls on strapping/interface pins. W5500 needs a 25 MHz crystal
and RJ45-with-magnetics; keep SPI ≤ ~33–40 MHz per its timing.

## 2. STM32H723 + LAN8742A (or STM32H563) — ★ runner-up

Integrated Ethernet MAC + external RMII PHY. Firmware is mature (STM32 HAL +
lwIP via CubeMX, ST bare-metal H5/H7 Ethernet references; `embassy-stm32`
eth + embassy-net works with LAN8742). Weak spots: STM32H563ZIT6 (LCSC
C6807803) had only ~35 in stock @ ~$5.23; H723 better stocked but extended
and ~$8–11; LAN8742A chronically hard to source cheaply, while the cheap
LAN8720A carries notorious REF_CLK/nINTSEL strapping and 50 MHz clock-
injection bring-up traps. RMII (7+ signals, clean 50 MHz REF_CLK, matched
pairs) is materially harder PCB and bring-up than SPI. Pick only if
standardizing on STM32 or specifically wanting single-chip MAC.

## 3. WCH CH32V307 — rejected

CH32V307VCT6 (LCSC C2943979, ~$2.17, good stock). Integrated PHY is
**10Base-T only** — 100M needs an external RGMII/RMII PHY (e.g. CH182),
forfeiting the advantage. C support exists (WCH SDK + lwIP + RT-Thread), but
**Rust/embassy Ethernet is unimplemented** (`ch32-hal` issue #11) — would
fracture the firmware codebase if the ESP32-S3 firmware is Rust.

## 4. Microchip SAME54 / Nuvoton M467 — rejected

Both need an external RMII PHY like the STM32 path, with weaker LCSC stock
and smaller communities. No advantage over the STM32H7 runner-up.

## Sources

- W5500 LCSC: https://www.lcsc.com/product-detail/C32843.html
- RP2350A LCSC: https://www.lcsc.com/product-detail/Microcontrollers-MCU-MPU-SOC_Raspberry-Pi-RP2350A_C42411118.html
- STM32H563ZIT6 LCSC: https://www.lcsc.com/product-detail/C6807803.html
- CH32V307VCT6 LCSC: https://www.lcsc.com/product-detail/Microcontroller-Units-MCUs-MPUs-SOCs_WCH-Jiangsu-Qin-Heng-CH32V307VCT6_C2943979.html
- embassy W5500 driver (MACRAW): https://github.com/embassy-rs/embassy-net-w5500 · https://docs.embassy.dev/embassy-net-wiznet
- ch32-hal Ethernet unimplemented: https://github.com/ch32-rs/ch32-hal/issues/11
- CH32V307 10M PHY: https://www.wch-ic.com/products/CH32V307.html · https://blog.dan.drown.org/ch32v307-dev-board/
- STM32 H5/H7 bare-metal Ethernet: https://github.com/stm32-hotspot/CKB-STM32-HAL-Ethernet-BareMetal · https://community.st.com/stm32-mcus-60/how-to-create-a-bare-metal-hal-ethernet-application-on-stm32h563-stm32h723-136820
- LAN8742A: https://www.microchip.com/en-us/product/lan8742a
