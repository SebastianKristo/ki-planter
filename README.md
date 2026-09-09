<p align="center"><img src="icon.png" width="128" alt="KI Planter"></p>

# KI Planter

Custom integration for vanning av planter. Erstatter YAML-pakken `planter_sebastian.yaml`.
Ett **sted** per oppføring (f.eks. «Sebastians soverom») med så mange planter du vil.

## Installasjon (HACS)
1. HACS → Integrations → ⋮ → Custom repositories → `https://github.com/SebastianKristo/ki-planter` (Integration)
2. Installer **KI Planter**, restart HA
3. Innstillinger → Enheter og tjenester → Legg til integrasjon → **KI Planter**: sted → varsling → planter

Planter legges til, redigeres og fjernes under **Konfigurer** på oppføringen (meny: Legg til / Rediger / Fjern / Varsling).

## Entiteter
Per plante (egen enhet med plantens navn, f.eks. `arekapalme_*`):

| Entitet | Funksjon |
|---|---|
| `binary_sensor.<plante>_trenger_vann` | on når intervallet er passert. Attributter: `navn`, `latin`, `ikon`, `tips`, `intervall_dager`, `sist_vannet`, `dager_siden`, `dager_igjen`, `neste_vanning`, `prosent`, `status`, `sted` |
| `datetime.<plante>_sist_vannet` | redigerbar |
| `number.<plante>_intervall` | sommerintervall i dager (1–60) |
| `number.<plante>_intervall_vinter` | vinterintervall (0 = samme som sommer). Vintermånedene settes under Varsling (standard nov–mar) |
| `number.<plante>_fuktighet_min`, `switch.<plante>_auto_registrer` | bare med fuktighetssensor: «tørr jord» under terskelen overstyrer intervallet, og fuktig jord utsetter vanning. Hopper fuktigheten ≥ 15 pp opp, registreres vanning automatisk |
| `button.<plante>_vannet_na` | registrer vanning nå |
| `sensor.<plante>_dager_siden_vannet`, `sensor.<plante>_neste_vanning` | |

Per sted (`<sted>_planter_*`):

| Entitet | Funksjon |
|---|---|
| `sensor.<sted>_planter_trenger_vann` | antall, med liste i attributtet `trenger_vann` |
| `button.<sted>_planter_alle_vannet` | registrer alle som trenger vann |
| `switch.<sted>_planter_varsling` | varsel på/av |
| `button.<sted>_planter_send_varsel` | send varselet nå |

Varsel sendes til valgt `notify.*`-tjeneste på valgt klokkeslett når minst én plante trenger vann, med valgfri lenke.

## Kort
`ki-planter-card` i [ki-cards](https://github.com/SebastianKristo/ki-cards) v2 finner plantene selv (attributt `integrasjon: ki_planter`);
`sted:` begrenser til ett sted.

## Migrering fra YAML-pakken
Legg til plantene med samme intervall, trykk «Vannet nå» (eller sett `datetime.<plante>_sist_vannet` til gammel verdi),
slett pakken og automasjonen `planter_sebastian_varsel`.

## v1.1.0
- Sommer-/vinterintervall per plante, vintermåneder per sted (attributt `sesong`).
- Valgfri jordfuktighetssensor per plante (`fuktighet`, `fuktighet_min`, `grunn` i attributtene).
