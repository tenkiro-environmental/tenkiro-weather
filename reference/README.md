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

- **ESP32-S3-WROOM-1-N8R2** (LCSC C2913204) — primary network MCU (Wi-Fi).
- **STM32H563VGT6 + LAN8742A** — wired-Ethernet backup variant (decided
  2026-07; WIZnet ruled out by decision, superseding the survey's
  RP2350+W5500 pick — see `../doc/hashi-ethernet-mcu-survey-2026-07.md`).
  - STM32H563VGT6: LCSC C18221950 (integrated Ethernet MAC) —
    https://www.st.com/en/microcontrollers-microprocessors/stm32h563-573.html
  - LAN8742A-CZ-TR: LCSC C621424 (RMII PHY; do **not** substitute LAN8720A) —
    https://www.microchip.com/en-us/product/lan8742a
  - Rust: `embassy-stm32` eth + embassy-net; C: STM32 HAL + lwIP.

## Station (Sora) — platform decided 2026-07 (see `../DESIGN.md`)

- **STM32U073CBT6** (LCSC C27035627) — ULP MCU (M0+, 128 K/40 K, LQFP-48),
  same U0 family as ephemerkey's U083KCU6. Headroom alternate:
  STM32U575VGT6 (C5270988, deep stock; calcumaker-shared U5 line).
- **CN3722** MPPT charger (C77905), 2s LTO float ≈ 5.5 V; alternates
  BQ24650RVAR (C53712) / LT3652IMSE (C671115).
- **TPS62840DLCR** 750 nA-Iq buck (C2071859) → 3.3 V rail.
- **MB85RS64PNF** SPI FRAM (C8741).
- Sensors: SHT40-AD1B-R2 (C2909890), BMP390 (C5124834), VEML7700-TT
  (C1850416), optional SGP40-D-R4 (C2874215).
- **Mast bus** (switched-power RS-485 pod chain): MAX3471EUA+T (C27462,
  1.6 µA transceiver) — https://www.analog.com/en/products/max3471.html ;
  TPS22919DCKR load switch (C2149796); SM712 bus TVS (C521963).
- **PM2.5 (optional pod): Sensirion SPS30** — off-BOM (DigiKey
  1649-1108-ND / Mouser 403-SPS30), UART mode, 5 V; pod header JST
  S5B-ZR(LF)(SN) (C265404) —
  https://sensirion.com/products/catalog/SPS30
- Vane options: resistor-ladder RJ11 vane (Misol/Davis WH-SP class) or
  AS5600-ASOT contactless angle (C499458; MT6701 C3003196 alternate).

## Station (Sora) — TBD

- Ultra-low-power MCU: TBD.
- Sensors (Kumo/Kaze/Ame/Hikari), solar charger, LiFePO₄ cell: TBD.
