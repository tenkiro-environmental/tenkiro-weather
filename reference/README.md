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
- **BQ24650RVAR** solar-MPPT charge controller (C53712; RVAT C2876745) —
  **1S LTO float 2.85 V** (programmable ≥ 2.1 V — integrated 1-cell chargers
  can't reach LTO). CN3722 (C77905) kept only as revert-to-2s fallback —
  https://www.ti.com/product/BQ24650
- **BQ34Z100PWR-G1** multi-chemistry fuel gauge (C91302) — Impedance Track
  with **LTO ChemID support** (TI-confirmed: e2e.ti.com threads 329276 &
  1252347; get the exact ChemID via the GPCCHEM tool), low-side sense, I²C.
  Verified vs datasheet SLUSBZ5D: REGIN 2.7–4.5 V (feed from 3.3 V rail),
  BAT pin direct ≤5 V (no divider at 1S), FULLSLEEP <30 µA —
  https://www.ti.com/product/BQ34Z100-G1
- **TPS63900DSKR** 75 nA-Iq buck-boost (C1518762) → 3.3 V rail (1S LTO
  2.4 V nom is below the rail; replaced the TPS62840 buck) —
  https://www.ti.com/product/TPS63900
- ~~MB85RS64PNF SPI FRAM (C8741)~~ — **dropped 2026-07**: outage buffering
  and the Nami nonce epoch counter use the U073's internal flash; nothing
  needs per-packet NVM writes.
- **Nami AEAD: Ascon-128a** (NIST SP 800-232) —
  https://csrc.nist.gov/pubs/sp/800/232/final ; Rust `ascon-aead` crate
  (no_std). Alternate suite (reserved 0x02): ChaCha20-Poly1305, RFC 8439,
  `chacha20poly1305` crate. Key derivation: HKDF (RFC 5869), `hkdf` crate.
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
- **Lightning: ScioSense AS3935** (off-BOM, DigiKey) —
  https://www.sciosense.com/as3935-franklin-lightning-sensor-ic/
  - Antenna: 100 µH, Q trimmed to ~15 (10 k parallel), 500 kHz parallel
    resonance — per the
    [AS3935 HW Design Guide](https://www.sciosense.com/wp-content/uploads/2023/12/AS3935-Application-Note-Hardware-Design-Guide.pdf).
  - **Production coil: Premo SDTR1103-HF1-0100J** — 100 µH ±5 %, Q45 ±5 %
    @ 0.5 MHz, SMD 11.8×3.6×2.5 mm, −40…+85 °C, AEC-Q200, purpose-made for
    lightning detectors ([datasheet](https://www.dcelectronicsolutions.com/wp-content/uploads/2018/04/SDTR1103-HF1.pdf),
    [Premo product page](https://grupopremo.com/products/sdtr1103)).
    **Plan of record for all builds** — order via Premo direct / DC
    Electronic Solutions; consigned at JLCPCB. No major distributor carries
    it (MA5532 is obsolete; Mouser -AEB residual = bench fallback only).
- **UV: Lite-On LTR-390UV-01** (LCSC C492374, JLCPCB-assemblable; DigiKey
  7322497) — UV-A + ALS, UV-index output. Cost-down: GUVA-S12SD + TIA.
  Board also carries a **DNP ams AS7331 footprint** (OLGA-16, C20482877) as
  the spectral-UV upgrade option; VEML6075/SI1145 discontinued. —
  https://optoelectronics.liteon.com/upload/download/DS86-2015-0004/LTR-390UV_Final_%20DS_V1%201.pdf
- **Sky IR / cloud: MLX90614ESF-BCC** (C7501763) —
  https://www.melexis.com/en/product/MLX90614/
- **Hail/impact:** generic piezo disc + TLV7031DBVR comparator (C2869832).
- **Hashi indoor CO₂: Sensirion SCD40** (C3659421) —
  https://sensirion.com/products/catalog/SCD40

## Station (Sora) — TBD

- Ultra-low-power MCU: TBD.
- Sensors (Kumo/Kaze/Ame/Hikari), solar charger, LiFePO₄ cell: TBD.
