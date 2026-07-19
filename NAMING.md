# Naming

**Brand / ecosystem:** **Tenkiro** (天気楼 — "weather tower" flavor).
**Internal description:** *"Sora speaks Nami to Hashi."*

## Hierarchy

| Name | Meaning | Role |
|---|---|---|
| **Tenkiro** | — | ecosystem / brand / repo |
| **Sora** | sky | outdoor solar-powered weather station (`hardware/tenkiro-sora`) |
| **Hashi** | bridge | indoor bridge between the radio network and Ethernet/Wi-Fi (`hardware/tenkiro-hashi`) |
| **Nami** | wave | the over-the-air protocol / radio subsystem ("Nami Link Protocol") |
| **Kumo** | cloud | humidity/pressure module |
| **Kaze** | wind | wind module |
| **Ame** | rain | rain module |
| **Hikari** | light | light/UV module |

## Repo vs product

- The **repo** stays `tenkiro` (the brand/line).
- The **PCBs** are `tenkiro-sora` and `tenkiro-hashi`. Schematic title blocks
  read "Tenkiro Sora" / "Tenkiro Hashi".
- The protocol is referred to as **Nami** in code (`nami_*` / `nami::`).

## Trademark posture (informal — not legal clearance)

Before any public launch, run a proper USPTO/TESS + EUIPO search (ideally via a
trademark attorney) on "Tenkiro", and re-verify domain availability. The
Japanese common nouns (sora/hashi/nami/…) are used as internal codenames, not
standalone wordmarks.
