# BolaBol v1 · 2 monedes (Sky) - peces que canvien

Tot és igual que el BolaBol v1 d'una moneda (`stl/`, `BOM.md`) excepte aquestes peces.
Colors: `base_box` i `mech_box` en **PETG blau cel (Sky)**; la resta com a la d'una moneda (marc crema, detalls corall).
La `base_box` és la mateixa peça que la d'una moneda (`stl/base_box.stl`), només canvia el color.

| Peça | Qt | Material | Llit 220x220 | Malla | Volum cm3 | Orientació |
|---|---|---|---|---|---|---|
| coin_wheel | 1 | PETG | OK flat 76x76 h43 | manifold | 143.6 | back face down (saw teeth on the bed), no supports - 2 pockets |
| coin_plate | 1 | PETG cream | OK flat 100x104 h3 | manifold | 28.0 | back face down (scoop and countersinks on top) - 2 slots |
| mech_box | 1 | PETG sky blue | OK flat 213x214 h113 | manifold | 307.0 | upright, open top up - 2 coin slots in the front wall |

Monedes: les mateixes fitxes de 25 x 4 mm (`stl/token_0.stl`); calen 2 per càpsula.
Ferreteria: la mateixa que `BOM.md`.

## Peces de prova (2monedes/proves/)

| Fitxer | Llit | Malla | Amb |
|---|---|---|---|
| test_coin_jig | OK flat 128x140 h44 | manifold | front-wall section with the 2 coin slots: + coin_plate, coin_housing, coin_wheel, dog_pawl (+ spring), ratchet_pawl, knob, 2 tokens |

### Plaques 3MF per a Flash Studio (AD5M Pro)

| Placa | Material | Peces | Capa | Suports | Temps | Filament |
|---|---|---|---|---|---|---|
| proves_5_moneda_A.3mf | PETG | test_coin_jig, knob, test_hex_coupon_coin, dog_pawl, ratchet_pawl, token_0, token_0_b | 0.20 mm | cap | 5h 32m 42s | 122 g |
| proves_6_moneda_B.3mf | PETG | coin_housing, coin_plate, coin_wheel | 0.20 mm | coin_housing | 5h 45m 56s | 137 g |
| proves_5_moneda_A_PLA.3mf | PLA | test_coin_jig, knob, test_hex_coupon_coin, dog_pawl, ratchet_pawl, token_0, token_0_b | 0.20 mm | cap | 5h 30m 42s | 119 g |
| proves_6_moneda_B_PLA.3mf | PLA | coin_housing, coin_plate, coin_wheel | 0.20 mm | coin_housing | 5h 37m 44s | 134 g |

### Com funciona i com provar-la

Dues ranures a la placa, una moneda a cada una, i després es gira la maneta. La roda porta dues butxaques una al costat de
l'altra, i passen per sota del mateix gatet amb uns 12 graus de diferència: si qualsevol de les dues va buida, el gatet hi cau
i bloqueja.

Prova amb `proves_5` / `proves_6` d'aquesta carpeta (mateix muntatge que el moneder d'una moneda):
- **Sense monedes**: bloqueja a ~46 graus. **Només la ranura dreta**: bloqueja a ~57. **Només l'esquerra**: bloqueja a ~46.
  En tots els casos torna enrere fins al tope de casa i posa la que falta.
- **Dues monedes**: volta sencera; les dues surten cap a les 5-6 i cauen al calaix.
- Amb cop sec i una sola moneda ha de bloquejar igual.

Simulació dinàmica (coin_test, pas 65 us): sense monedes, amb només A o només B, a 2 s/volta i amb cop sec (0.2 s),
bloqueja sempre i la moneda que hi ha no es perd; amb les dues, a 2 s i a 0.3 s/volta, volta sencera i les dues al calaix.

### Insígnia BOLABOL i monedes gravades

La mateixa insígnia que la v4 d'una moneda, sobre la placa del moneder: rebaix de 0.6 mm a la paret frontal de la
`mech_box` (ja inclòs a `2monedes/mech_box.stl`), peça `logo` i estrelles `logo_sparkles_*`
(`stl/` o, orientades per imprimir, `imprimir/`; llits 15-18 de `imprimir/llits/`, la 15 amb les pauses de canvi
de filament: crema, corall, crema). Sobre el blau cel queda amb el contorn crema com a la menta.

Monedes: les mateixes que la v4 (`stl/token_0.stl`), gravades amb el logo BBOL a una cara i el Boli a l'altra,
amb els cantells xamfranats 0.4 mm. Per fer-ne moltes: `imprimir/llits/llit_19_monedes.3mf` (30 monedes).

Conducte i molla (28/09/2026): la `base_box` és la de la v4 amb la paret del darrere del conducte a 40 mm (la moneda ja no s'encalla sota; `stl/base_box.stl`, llit 01). Molla del gatet dura, ~120 g al nas: amb la tova, una volta molt violenta amb una sola moneda (0.15 s) passava.
