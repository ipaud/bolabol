# BolaBol v1 (Mochi + moneder amagat) - peces i ferreteria

Versió tancada del 28/09/2026. Contingut d'aquesta carpeta:
- `BolaBol-v1.blend` (1 moneda), `BolaBol-v1_2monedes.blend` i `BolaBol-v1_duo.blend` (les dues màquines juntes).
- `stl/`: cada peça tal com és al model; `stl/proves/`: peces i plaques de prova; `stl/bolabol_logo.3mf`: la insígnia.
- `imprimir/`: cada peça ja orientada per imprimir; `imprimir/llits/`: els 20 llits per a Flash Studio (3MF).
- `2monedes/` i `BOM_2monedes.md`: les peces que canvien a la màquina de 2 monedes.
- `codi/`: el codi que genera el model (`codi/gacha/`) i els logos (`codi/brand/`).

| Peça | Qt | Material | Llit 220x220 | Malla | Volum cm3 | Orientació |
|---|---|---|---|---|---|---|
| base_box | 1 | PETG mint | OK flat 213x214 h119 | manifold | 438.6 | floor down (3 mm chamfer prints without support) |
| mech_box | 1 | PETG mint | OK flat 213x214 h113 | manifold | 307.5 | upright, open top up (front wall down needs ~250 cm2 of support) |
| deck | 1 | PETG | OK flat 206x207 h34 | manifold | 278.6 | plate down |
| rotor | 1 | PETG | OK flat 203x203 h53 | manifold | 412.8 | flat underside down, cone up; support only under the crown ring step (outer 14.7 mm, 3 mm high) |
| crown_ring | 1 | PETG | OK flat 203x203 h8 | manifold | 38.8 | flange down, teeth up (no supports) |
| shim_04 | 1 | PETG | OK flat 30x30 h0 | manifold | 0.2 | flat - fitted under the rotor (0.2 mm layers) |
| spare_shim_02 | 1 | PETG | OK flat 30x30 h0 | manifold | 0.1 | flat - swap in if the mesh is loose / skips (lowers the crown) |
| spare_shim_06 | 1 | PETG | OK flat 30x30 h1 | manifold | 0.3 | flat - swap in if the crown/pinion mesh binds (raises the crown) |
| deck_bracket | 1 | PETG | OK flat 19x24 h12 | manifold | 2.2 | flange down |
| funnel | 1 | PETG cream | OK flat 213x214 h29 | manifold | 144.6 | rim band down |
| hood | 1 | PETG | OK flat 90x109 h33 | manifold | 50.1 | top face down |
| lid | 1 | PETG cream | OK flat 213x214 h46 | manifold | 358.0 | flat face down (hollow, lock tabs up), no supports; 2 screws through opposite pillars (refill: undo them) |
| window_front | 1 | acrylic 2 mm | OK flat 154x172 h2 | manifold | 52.9 | laser cut 172.4 x 153.5 (or clear PETG/PC sheet) |
| window_back | 1 | acrylic 2 mm | OK flat 154x172 h2 | manifold | 52.9 | laser cut 172.4 x 153.5 (or clear PETG/PC sheet) |
| window_left | 1 | acrylic 2 mm | OK flat 154x173 h2 | manifold | 53.1 | laser cut 172.9 x 153.5 (or clear PETG/PC sheet) |
| window_right | 1 | acrylic 2 mm | OK flat 154x173 h2 | manifold | 53.1 | laser cut 172.9 x 153.5 (or clear PETG/PC sheet) |
| knob | 1 | PETG coral | OK flat 30x86 h17 | manifold | 29.0 | crank: flat back down, no supports (cap and chamfers on top) |
| hex_shaft | 1 | PETG | OK diagonal 18x229 h16 | manifold | 50.8 | lying on a flat, diagonal on the bed, 100% infill |
| sleeve_rear | 1 | PETG | OK flat 22x22 h5 | manifold | 0.7 | end down |
| spacer | 1 | PETG | OK flat 24x141 h24 | manifold | 31.2 | end down |
| gear_A | 1 | PETG | OK flat 40x40 h30 | manifold | 12.8 | gear face down, hub up |
| gear_B_pinion | 1 | PETG | OK flat 42x42 h30 | manifold | 25.2 | gear B face down, no supports (40 deg cone under the pinion) |
| pinion_axle | 1 | PETG | OK flat 16x42 h16 | manifold | 3.6 | standing on its head, 100% infill (or 10 mm steel rod) |
| dog_pawl | 1 | PETG | OK flat 20x22 h13 | manifold | 2.4 | flat |
| ratchet_pawl | 1 | PETG | OK flat 17x27 h5 | manifold | 0.8 | flat |
| token_drawer | 1 | PETG coral | OK flat 70x153 h26 | manifold | 57.5 | floor down |
| token_0 | 6 | PETG | OK flat 25x25 h4 | manifold | 1.8 | flat, cara BBOL al llit (pont), Boli amunt; gravat 0.6 mm a cada cara, cantells xamfranats 0.4 mm |
| chute | 1 | PETG | OK flat 166x191 h67 | manifold | 172.8 | own bed (llit 20): standing on its back end (166 mm tall), 5 mm brim, normal supports only under the drop tube front wall and the cup lip (inside, next to the open ends) |
| outlet_door | 1 | clear PETG | OK flat 63x78 h6 | manifold | 12.3 | on its bottom edge, 5 mm brim (flat, the hinge barrel lifts the whole door off the bed) |
| door_ear_0 | 1 | PETG coral | OK flat 8x14 h6 | manifold | 0.6 | flat |
| door_ear_1 | 1 | PETG coral | OK flat 8x14 h6 | manifold | 0.6 | flat |
| capsule_top | 10 | clear PETG / PP | OK flat 50x50 h27 | manifold | 4.8 | rim down, tree supports inside the dome |
| capsule_bottom | 10 | PETG / PP colour | OK flat 50x50 h34 | manifold | 6.3 | rim down (flipped), tree supports inside and under the lip |
| pillar_0 | 1 | PETG cream | OK flat 27x156 h27 | manifold | 38.0 | upright, 5 mm brim |
| pillar_1 | 1 | PETG cream | OK flat 27x156 h27 | manifold | 37.9 | upright, 5 mm brim |
| pillar_2 | 1 | PETG cream | OK flat 27x156 h27 | manifold | 38.0 | upright, 5 mm brim |
| pillar_3 | 1 | PETG cream | OK flat 27x156 h27 | manifold | 37.9 | upright, 5 mm brim |
| topper | 1 | PETG coral | OK flat 31x31 h24 | manifold | 9.8 | flat face down |
| foot_0 | 1 | PETG cream | OK flat 28x28 h11 | manifold | 4.9 | peg up |
| foot_1 | 1 | PETG cream | OK flat 28x28 h11 | manifold | 4.9 | peg up |
| foot_2 | 1 | PETG cream | OK flat 28x28 h11 | manifold | 4.9 | peg up |
| foot_3 | 1 | PETG cream | OK flat 28x28 h11 | manifold | 4.9 | peg up |
| coin_wheel | 1 | PETG | OK flat 76x76 h43 | manifold | 146.8 | back face down (saw teeth on the bed), no supports |
| coin_housing | 1 | PETG | OK flat 99x102 h35 | manifold | 40.1 | front face down, supports in the pawl window and under the funnel / exit ceilings |
| coin_plate | 1 | PETG cream | OK flat 100x104 h3 | manifold | 28.5 | back face down (scoop and countersinks on top) |
| logo | 1 | PETG cream + coral | OK flat 25x101 h4 | manifold | 4.2 | back face down; filament change at 1.2 mm (coral letters) and 3.6 mm (cream highlights) |
| logo_sparkles_yellow | 1 | PETG yellow | OK flat 18x88 h2 | manifold | 0.1 | back face down (3 pieces) |
| logo_sparkles_mint | 1 | PETG mint | OK flat 13x89 h2 | manifold | 0.0 | back face down (2 pieces) |
| logo_sparkles_coral | 1 | PETG coral | OK flat 7x92 h2 | manifold | 0.0 | back face down (2 pieces) |

## Ferreteria

| Element | Qt | Ús |
|---|---|---|
| M3 x 16 countersunk (DIN 7991) screw | 2 | lid lock: horizontally through the front-left and back-right pillars into the tabs under the lid (self tapping) |
| M3 x 30 screw | 2 | capsule hood -> funnel slope, from the hood roof (self tapping): the hood used to sit loose on the slope |
| M3 x 12 countersunk (DIN 7991) screw + M3 nut | 2 | coin drawer lock: through the drawer front into the nut pockets of the post behind it (nuts in from behind, before the mech box) |
| CA glue (or epoxy) | 1 | crown ring -> rotor: 0.1 mm press fit on the bore + a drop on each of the 5 tabs (it hangs under the rotor) |
| M3 x 20 screw | 4 | mech box -> base box corner blocks (11.8 mm block: an M3x16 left 4 mm of thread) |
| M3 x 12 screw | 4 | funnel -> mech box top corner blocks (self tapping) |
| M3 x 12 screw | 2 | pinion axle bracket -> deck, from below (self tapping) |
| glue (CA or 2-part epoxy) | 1 | BOLABOL badge into its front wall pocket, sparkles into the badge pockets |
| M3 x 10 screw | 2 | door hinge ears -> front wall (self tapping) |
| steel wire (or PETG filament) 1.75 mm x 81 mm | 1 | outlet door hinge pin, through both ears and the door barrel |
| ballast >= 500 g (steel nuts / washers or a sand bag) | 1 | glued on the base box floor right of the coin drawer, rear half (x 52-95, y 0-95): 15 N at the crank tipped the empty machine forward |
| M3 x 16 countersunk (DIN 7991) screw | 4 | coin plate -> front wall -> coin housing lugs (self tapping) |
| M3 x 25 screw | 1 | blocking pawl pivot, from behind: head sunk 3 mm in the housing, self taps in the front fork |
| M3 x 12 screw | 1 | anti-reverse pawl pivot, from behind through the housing sleeve into the boss (self tapping): the head clamps the sleeve, the pawl turns free |
| M3 x 16 screw | 1 | crank -> hex shaft, through the hub cap (self tapping) |
| glue (CA or 2-part epoxy) | 1 | BOLABOL badge into its front wall pocket, sparkles into the badge pockets |
| pen spring, OD <= 5.5 mm, cut to ~10 mm, stiff: >= 120 g at the pawl nose | 1 | NOT optional in v3: snaps the blocking pawl into the empty pocket while the wheel turns (seat in the housing hump). 0.02 N m: blocks a coinless flick up to ~0.11 s/turn (a soft 60 g spring lets ~0.15 s/turn through). Check: lift the nose to the rim with a kitchen scale. Keep a spare |

## Peces de prova (imprimir primer: stl/proves/)

Munta-les amb les peces reals indicades (de stl/). Si engranen i bloquegen bé a mà,
la màquina sencera també ho farà amb la mateixa impressora i material.

| Fitxer | Llit | Malla | Amb |
|---|---|---|---|
| test_gear_jig | OK flat 94x128 h60 | manifold | gear train jig: + gear_A, gear_B_pinion, pinion_axle, shim_04 and spares |
| test_crown_sector | OK flat 116x118 h10 | manifold | 70 deg crown sector: sits on the shim like the rotor |
| test_hex_coupon_gears | OK flat 18x41 h16 | manifold | hex shaft piece for the gear jig (tests the 16 mm hex fit) |
| test_coin_jig | OK flat 128x140 h44 | manifold | front-wall section: + coin_plate, coin_housing, coin_wheel, dog_pawl (+ spring), ratchet_pawl, knob (crank), token |
| test_hex_coupon_coin | OK flat 18x60 h16 | manifold | hex shaft piece for the coin jig (crank -> wheel -> rear bracket) |

### Plaques 3MF per a Flash Studio (AD5M Pro): stl/proves/*.3mf

Fetes amb FlashPrep (print3mf.py): orientades, col·locades i amb els ajustos per peça.
L'informe de cada placa és dins el 3MF (Metadata/FlashPrep_report.txt).
Les _PLA serveixen per provar el mecanisme; els ajustos justos, confirma'ls amb el material final.

| Placa | Material | Peces | Capa | Suports | Temps | Filament |
|---|---|---|---|---|---|---|
| proves_5_moneda_A.3mf | PETG | test_coin_jig, knob, test_hex_coupon_coin, dog_pawl, ratchet_pawl, token_0, token_0_b | 0.20 mm | cap | 4h 54m 7s | 122 g |
| proves_6_moneda_B.3mf | PETG | coin_housing, coin_plate, coin_wheel | 0.20 mm | coin_housing | 5h 42m 45s | 137 g |
| proves_5_moneda_A_PLA.3mf | PLA | test_coin_jig, knob, test_hex_coupon_coin, dog_pawl, ratchet_pawl, token_0, token_0_b | 0.20 mm | cap | 4h 50m 53s | 119 g |
| proves_6_moneda_B_PLA.3mf | PLA | coin_housing, coin_plate, coin_wheel | 0.20 mm | coin_housing | 5h 34m 11s | 134 g |

### Canvis v4 = v3 + auditoria (26/09/2026)

Primera tanda (v3.1):
- `crown_ring`: entra a pressió al rotor (0.1 mm al diàmetre interior) i el rebaix ja no deixa 0.2 mm de joc a sobre; una gota de CA a cada pestanya. Abans penjava lliure i podia baixar 1 mm fins al deck: els dents xoquen amb el pinyó a partir de -0.4 mm.
- `deck`: carril anti-inclinació sota la brida de la corona (r 98.8-101.2, 0.2 mm per sota), obert sobre el pinyó. El rotor ja no es pot inclinar més de 0.16 deg cap al pinyó (abans 0.6 deg; a 0.25 deg ja xocava).
- `rotor`: avellanat de les butxaques a 50 deg / 16 mm (abans 35 deg / 12 mm): menys ponts de dues càpsules sobre la boca de la butxaca (voltes buides).
- `export.py`: les peces de col·leccions amagades (càpsules, calces de recanvi) sortien com a STL buits de 84 bytes; ara s'exporten sempre i es comprova el nombre de triangles.

Segona tanda (v3.2):
- `coin_wheel`: tope de casa al trinquet. Tornant enrere, la manovella fa tope a casa (-0.3 a -0.6 deg) amb la butxaca alineada amb la ranura; abans anava lliure de -23.6 a +52 deg i la moneda només entra amb la roda a menys de 1-1.5 deg. El trinquet anti-retorn actua des de ~78 deg (abans 71).
- `coin_plate` i paret frontal: ranura de 5.6 mm (abans 5.0); boca de la butxaca amb entrada de 2 mm per costat en 6 mm (abans 1 mm en 2 mm).
- `ratchet_pawl`: gira sobre un casquet del `coin_housing`; el cap del cargol estreny el casquet, no el gatet.
- `gear_A` i `gear_B_pinion`: cares de 12 mm (abans 8, sense marge amb 100 N a la manovella); el suport del pinyó i els seus cargols s'avancen 4 mm.
- `deck_bracket`: forat de 10.3 mm per a l'eix de 10 (abans 10.1, sortia just).
- `door_ear_0/1` i `outlet_door`: orelles de 6.5 mm (abans 4.5, 0.65 mm de paret davant del pern) i pern de filferro de 1.75 mm que ho travessa tot; cargols M3x10.
- `token_drawer` i `base_box`: calaix de les monedes cargolat. Dos cargols M3x12 avellanats a l'extrem dret del frontal van a femelles captives en un pal de la base, darrere del frontal; les femelles entren per darrere abans de muntar la mech_box. El calaix es fa 9 mm més estret.
- `hood`: ja no va solta damunt de la rampa de l'embut (hi podia lliscar fins al rotor). Dues columnes a la cortina i 2 cargols M3x30 des del sostre fins al `funnel`.
- `base_box`: topalls de 3 mm al terra al voltant dels peus del `chute`, que abans podia córrer 5-12 mm i desalinear-se del forat de sortida.
- Detalls: pilot del cargol de la manovella a 16 mm (el M3x16 passava 1.4 mm del fons, al `hex_shaft` i al `test_hex_coupon_coin`); `lid` buidada per sota (1491 -> 354 cm3, sostre de 3 mm, s'imprimeix igual sense suports); cargols embut -> mech_box 1.5 mm cap endins (parets de 0.5 mm al voltant dels pous); disc del `deck` de radi 84 (el forat de sortida hi deixava una llesca de 0.4 mm); pilot del suport del pinyó 1 mm més fons.
- `capsule_bottom`: l'espiga no estava unida al bol (només dues cares de gruix zero es tocaven a la junta; impresa amb la vora avall, el bol començava a l'aire). Espatlla a 45 graus sota la junta.
- `base_box`: llengüetes de centrat de 2 mm a la vora superior, 0.25 mm dins la mech_box (darrere, costats i davant fora del moneder).
- `lid`: ja no s'aixeca sense eines. Dues pestanyes sota la tapa, a les cantonades davant-esquerra i darrere-dreta, i 2 cargols M3x16 avellanats horitzontals a través dels pilars.
- `token_drawer`: 150 mm de fons (abans 36) i rampa de 35 graus sota el conducte, perquè les monedes rellisquin cap al fons. Simulació abocant-hi monedes: el conducte es manté lliure fins a unes 21-36 monedes (abans 10-15) i la primera que surt del calaix arriba a les 40-56 (abans 22-31). Buida'l cada 30 monedes, més o menys.
- Ferreteria i orientacions: M3x20 a les cantonades, llast de 500 g a la cantonada del darrere dreta, molla de recanvi, chute dret, porta de cantell, mech_box dreta, suport només sota el rebaix del rotor.

Tercera tanda (27/09/2026):
- Insígnia BOLABOL al frontal de la `mech_box`, sobre la placa del moneder: rebaix de 0.6 mm a la paret, peça `logo` (base crema, lletres corall, brillantors crema, amb les pauses de canvi de filament al projecte `stl/bolabol_logo.3mf`) i 7 estrelles `logo_sparkles_*` en groc, menta i corall.
- Monedes (`token_0`) gravades 0.6 mm: logo **BBOL** a una cara, el **Boli** a l'altra (`codi/brand/token_faces.json`, de `codi/brand/trace_token.py`). Mateixes mides (25 x 4 mm): res del moneder canvia. S'imprimeixen planes amb BBOL al llit i el Boli amunt (més detall); llits 09-11 de `imprimir/llits/` i `proves_5` regenerats.
- Monedes amb els cantells xamfranats 0.4 mm (entren millor a la butxaca de la roda i no fan pota d'elefant al llit). Validat amb la simulació dinàmica: 6 casos (2 / 0.3 / 0.2 s, 24.5 / 25.5 mm) passen igual que la moneda sense xamfrà. Llit de producció nou: **llit 19** (`imprimir/llits/llit_19_monedes.3mf`), 30 monedes en PETG, 3h 12m, 54 g, sense vora.

Quarta tanda (28/09/2026), de la bateria de simulacions noves (`codi/gacha/coin_battery.py`, ~200 casos):
- `base_box`: la paret del darrere del conducte de monedes comença a 40 mm en lloc de 34. Una moneda que baixava de cantell per la rampa del calaix hi quedava falcada a sota (23.2 mm de pas perpendicular a la rampa per a 25 mm de moneda; ~6 % de les proves). Ara hi ha 28 mm: 0 encallades en 49 proves. `stl` i `imprimir/base_box.stl` i el **llit 01** regenerats (18h 6m, 437 g). Si ja tens la `base_box` impresa: treu el calaix i retalla/lima 6 mm de la part baixa d'aquesta paret (la travessera de 31 mm de darrere del conducte), des del forat del calaix.
- `chute` en un llit propi, **llit 20** (`imprimir/llits/llit_20_chute.3mf`, 9h 3m, 252 g): de peu sobre la cara del darrere (de 74 orientacions és la de més recolzament i menys voladís), vora de 5 mm i suports normals només sota els dos sostres interiors que abans es feien com a ponts de 62 mm: la paret davantera del tub de baixada i la pestanya de la cubeta. Es treuen per la boca del tub i per la sortida. El **llit 04** queda amb `coin_housing` i `deck_bracket` (2h 28m, 47 g).
- Molla del gatet més dura: 0.02 N·m, uns 120 g al nas del gatet (abans 0.01, 60 g). Amb la tova, un cop de manovella molt violent sense moneda (0.15 s/volta, ~400 rpm) passava i donava càpsula; amb la dura bloqueja fins a 0.12 s/volta.

### Prova del moneder v3 (proves_5 + proves_6): què comprovar

Muntatge sobre `test_coin_jig` (mateixos forats que la paret frontal de la màquina):
1. `coin_plate` davant, `coin_housing` darrere, 4 × M3x16 avellanats des de davant.
2. `dog_pawl` a la finestra de l'anella, molla de bolígraf (~10 mm, comprimida ~4 mm) al forat de la gepa, M3x25 des del darrere.
3. `coin_wheel` des del darrere dins l'anella; `ratchet_pawl` sobre les dents, M3x12 des del darrere al cub.
4. `test_hex_coupon_coin`: manovella → placa → roda → suport del darrere; `knob` (manovella) amb M3x16.

Proves (a mà, primer a poc a poc i després amb un cop sec):
- **Sense moneda**: la manovella s'atura a ~52°. Torna-la enrere fins que faci tope: allò és casa (tope del trinquet) i la butxaca queda alineada amb la ranura. Amb cop sec ha de bloquejar SEMPRE.
- **Moneda**: deixa-la a la ranura i empeny-la fins a la placa; ha d'acabar d'entrar sola (rampa 12° + fons 2°) i quedar al tope.
- **Volta sencera amb moneda**: el gatet passa per sobre, la moneda surt entre 165° i 180° i cau per l'embut.
- **Enrere**: entre casa i ~78° la manovella torna lliure i fa tope a casa; a partir de ~78° el trinquet ja no deixa tornar.

Simulació dinàmica (coin_test.py, Bullet, pas 65 µs, velocitat de mà constant):
- Sense moneda, amb molla de 0.01 N·m (60 g al nas) bloqueja fins a 0.16 s/volta i deixa passar un cop de 0.15 s;
  amb 0.02 N·m (120 g, la recomanada) fins a 0.12 s/volta; amb 0.03 N·m (180 g) fins i tot a 0.10 s.
  Sense molla NO bloqueja (a 50° la gravetat quasi no tira del gatet): la molla és obligatòria.
- Amb moneda de 24.5 / 25 / 25.5 mm (gruix 3.7-4.2), de 2.5 a 0.12 s/volta, fricció PETG inclosa: volta sencera,
  la moneda acaba al calaix. Bateria completa: `codi/gacha/coin_battery.py`.
- Monedes d'euro: la de 50 cèntims (24.25 mm) passa com una fitxa; la de 2 € (25.75 mm) és just a la vora: passa o
  s'encalla a l'entrada segons el cop. 1 € i 20 cèntims bloquegen.

Si el gatet no cau prou ràpid: molla més dura (pesa-la: ≥ 120 g al nas, aixecat fins a la vora). Si la moneda no entra sola: puja `SLOT_RAMP` (codi/gacha/parts_coin.py).

### Insígnia BOLABOL (stl/bolabol_logo.3mf)

Sobre la placa del moneder, encolada al rebaix de 0.6 mm de la paret frontal. Una sola peça, cara del
darrere avall, amb dues pauses ja posades al projecte (17m 51s, 4.9 g; pauses abans de les capes a 1.4 mm, 3.8 mm):
comença amb filament **crema** (base), a la 1a pausa canvia a **corall** (lletres), a la 2a torna a
**crema** (brillantors). Les estrelles són peces a part (stl/logo_sparkles_*.stl): groc, menta i
corall, encolades als seus forats de la base.

Per imprimir (v4, `imprimir/`): `logo.stl` i `logo_sparkles_{yellow,mint,coral}.stl` orientats al llit; llits nous a
`imprimir/llits/`: **15** insígnia (crema/corall/crema, pauses incloses, 18 min, 5 g), **16** estrelles grogues,
**17** menta, **18** corall (~1-2 min cadascun). El **llit 02** (`mech_box` amb el rebaix del logo) està regenerat:
si ja l'havies imprès sense rebaix, la insígnia també es pot enganxar directament sobre la paret plana.
