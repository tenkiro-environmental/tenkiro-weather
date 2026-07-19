# reference

Datasheet + dependency pointers for Tenkiro. Download datasheets locally as
needed (see the `digikey`/`lcsc` skills' datasheet-sync flow); don't commit
large PDFs.

## Radio

- **Semtech SX1262** — LoRa transceiver, 902–928 MHz NA ISM, +22 dBm max, ~4.2 mA RX.
  https://www.semtech.com/products/wireless-rf/lora-connect/sx1262
- **Ebyte E22-900M22S** — SX1262 SPI module, 850–930 MHz, +22 dBm, 14 × 20 mm
  castellated. Rev-A radio for both boards.
  https://www.cdebyte.com/products/E22-900M22S
- (Rejected: E220-900M22S — LLCC68-based; 30 dBm PA modules — power/regulatory
  cost. UART **T** variants — wrong interface. See `../DESIGN.md`.)

## Bridge (Hashi)

- **ESP32-S3** — primary network MCU (Wi-Fi).
- **RP2350A + WIZnet W5500** — wired-Ethernet backup variant (decided 2026-07).
  - RP2350A: LCSC C42411118 — https://www.raspberrypi.com/products/rp2350/
  - W5500: LCSC C32843 (hardwired TCP/IP over SPI; MACRAW mode for external
    stacks) — https://wiznet.io/products/iethernet-chips/w5500
  - Rust: `embassy-net-wiznet` + `embassy-rp`; C: pico-sdk + WIZnet ioLibrary.
  - Runner-up (documented in `../DESIGN.md`): STM32H723 + LAN8742A RMII PHY.

## Station (Sora) — TBD

- Ultra-low-power MCU: TBD.
- Sensors (Kumo/Kaze/Ame/Hikari), solar charger, LiFePO₄ cell: TBD.
