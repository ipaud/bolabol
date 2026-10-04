"""Print prep: per-part STL (mm), bed-fit check, manifold check, volume, bill of materials."""
import os
from math import sqrt
import bpy
import bmesh
from params import BED, BED_MARGIN

# name, qty, material, print orientation / note
PARTS = [
    ("base_box", 1, "PETG", "floor down"),
    ("mech_box", 1, "PETG", "front wall down (bottom edge on bed) or upright"),
    ("deck", 1, "PETG", "plate down"),
    ("rotor", 1, "PETG", "flat underside down, cone up; support only under the crown ring step (outer 14.7 mm, 3 mm high)"),
    ("crown_ring", 1, "PETG", "flange down, teeth up (no supports)"),
    ("shim_04", 1, "PETG", "flat - fitted under the rotor (0.2 mm layers)"),
    ("spare_shim_02", 1, "PETG", "flat - swap in if the mesh is loose / skips (lowers the crown)"),
    ("spare_shim_06", 1, "PETG", "flat - swap in if the crown/pinion mesh binds (raises the crown)"),
    ("deck_bracket", 1, "PETG", "flange down"),
    ("funnel", 1, "PETG", "rim down"),
    ("hood", 1, "PETG", "top face down"),
    ("case_post_0", 1, "PETG", "lying on its side"),
    ("case_post_1", 1, "PETG", "lying on its side"),
    ("case_post_2", 1, "PETG", "lying on its side"),
    ("case_post_3", 1, "PETG", "lying on its side"),
    ("lid", 1, "PETG", "flat"),
    ("window_front", 1, "acrylic 3 mm", "laser cut (or clear PETG, flat)"),
    ("window_back", 1, "acrylic 3 mm", "laser cut (or clear PETG, flat)"),
    ("window_left", 1, "acrylic 3 mm", "laser cut (or clear PETG, flat)"),
    ("window_right", 1, "acrylic 3 mm", "laser cut (or clear PETG, flat)"),
    ("knob", 1, "PETG", "back face down, no supports (hex bore end bridges)"),
    ("bezel", 1, "PETG", "back face down, supports only in the pawl window"),
    ("hex_shaft", 1, "PETG", "lying on a flat, diagonal on the bed, 100% infill"),
    ("sleeve_front", 1, "PETG", "end down"),
    ("sleeve_rear", 1, "PETG", "end down"),
    ("ratchet", 1, "PETG", "front face down"),
    ("spacer", 1, "PETG", "end down"),
    ("gear_A", 1, "PETG", "gear face down, hub up"),
    ("gear_B_pinion", 1, "PETG", "gear B face down, no supports (40 deg cone under the pinion)"),
    ("pinion_axle", 1, "PETG", "standing on its head, 100% infill (or 10 mm steel rod)"),
    ("dog_pawl", 1, "PETG", "flat"),
    ("ratchet_pawl", 1, "PETG", "flat"),
    ("token_chute", 1, "PETG", "on its side"),
    ("token_drawer", 1, "PETG", "floor down"),
    ("token_0", 6, "PETG", "flat (print as many tokens as you like)"),
    ("chute", 1, "PETG", "standing on its back end (166 mm tall), 5 mm brim; on its side the upper wall bridges the 62 mm duct"),
    ("outlet_door", 1, "clear PETG", "on its bottom edge, 5 mm brim (flat, the hinge barrel lifts the whole door off the bed)"),
    ("door_ear_0", 1, "PETG", "flat"),
    ("door_ear_1", 1, "PETG", "flat"),
    ("capsule_top", 10, "clear PETG / PP", "rim down, tree supports inside the dome"),
    ("capsule_bottom", 10, "PETG / PP colour", "rim down (flipped), tree supports inside and under the lip"),
]

HARDWARE = [
    ("M3 x 40 screw + nut", 3, "bezel -> front wall"),
    ("M3 x 45 screw + nut", 1, "blocking pawl pivot (through bezel and front wall)"),
    ("M3 x 16 countersunk (DIN 7991) screw + nut", 1, "anti-reverse pawl pivot: flat head flush, the knob passes 1.8 mm over it"),
    ("M3 x 20 screw", 1, "knob -> hex shaft (self tapping)"),
    ("M3 x 16 countersunk (DIN 7991) screw", 2, "lid lock: horizontally through the front-left and back-right pillars into the tabs under the lid (self tapping)"),
    ("M3 x 30 screw", 2, "capsule hood -> funnel slope, from the hood roof (self tapping): the hood used to sit loose on the slope"),
    ("M3 x 12 countersunk (DIN 7991) screw + M3 nut", 2, "coin drawer lock: through the drawer front into the nut pockets of the post behind it (nuts in from behind, before the mech box)"),
    ("CA glue (or epoxy)", 1, "crown ring -> rotor: 0.1 mm press fit on the bore + a drop on each of the 5 tabs (it hangs under the rotor)"),
    ("M3 x 20 screw", 4, "mech box -> base box corner blocks (11.8 mm block: an M3x16 left 4 mm of thread)"),
    ("M3 x 12 screw", 4, "funnel -> mech box top corner blocks (self tapping)"),
    ("M3 x 12 screw", 2, "pinion axle bracket -> deck, from below (self tapping)"),
    ("glue (CA or 2-part epoxy)", 1, "BOLABOL badge into its front wall pocket, sparkles into the badge pockets"),
    ("pen spring, OD <= 5.5 mm, cut to ~10 mm", 1, "pushes the blocking pawl nose down (seat in the bezel hump)"),
    ("M3 x 10 screw", 4, "lid -> case posts"),
    ("M3 x 10 screw", 2, "door hinge ears -> front wall (self tapping)"),
    ("steel wire (or PETG filament) 1.75 mm x 81 mm", 1, "outlet door hinge pin, through both ears and the door barrel"),
    ("ballast >= 500 g (steel nuts / washers or a sand bag)", 1, "glued on the base box floor right of the coin drawer, rear half (x 52-95, y 0-95): 15 N at the crank tipped the empty machine forward"),
]


# v2 "mochi" shell: colours per part, rounded frame instead of posts, lift-off lid on pegs
_MOCHI_SWAP = {
    "base_box": ("PETG mint", "floor down (3 mm chamfer prints without support)"),
    "mech_box": ("PETG mint", "upright, open top up (front wall down needs ~250 cm2 of support)"),
    "funnel": ("PETG cream", "rim band down"),
    "lid": ("PETG cream", "flat face down (hollow, lock tabs up), no supports; 2 screws through opposite pillars (refill: undo them)"),
    "knob": ("PETG coral", "back face down, no supports (hex bore end bridges)"),
    "bezel": ("PETG cream", "back face down, supports only in the pawl window"),
    "door_ear_0": ("PETG coral", "flat"),
    "door_ear_1": ("PETG coral", "flat"),
    "token_drawer": ("PETG coral", "floor down"),
    "window_front": ("acrylic 2 mm", "laser cut 172.4 x 153.5 (or clear PETG/PC sheet)"),
    "window_back": ("acrylic 2 mm", "laser cut 172.4 x 153.5 (or clear PETG/PC sheet)"),
    "window_left": ("acrylic 2 mm", "laser cut 172.9 x 153.5 (or clear PETG/PC sheet)"),
    "window_right": ("acrylic 2 mm", "laser cut 172.9 x 153.5 (or clear PETG/PC sheet)"),
}
_MOCHI_ADD = [("pillar_%d" % i, 1, "PETG cream", "upright, 5 mm brim") for i in range(4)] \
    + [("topper", 1, "PETG coral", "flat face down"), ] + [("foot_%d" % i, 1, "PETG cream", "peg up") for i in range(4)]


# v3 hidden coin mech: the knob is a plain crank; wheel / housing / plate replace the bezel, the
# ratchet, the front sleeve and the token chute
_V3_DROP = {"bezel", "ratchet", "sleeve_front", "token_chute"}
_V3_SWAP = {"knob": ("PETG coral", "crank: flat back down, no supports (cap and chamfers on top)")}
_V3_ADD = [
    ("coin_wheel", 1, "PETG", "back face down (saw teeth on the bed), no supports"),
    ("coin_housing", 1, "PETG", "front face down, supports in the pawl window and under the funnel / exit ceilings"),
    ("coin_plate", 1, "PETG cream", "back face down (scoop and countersinks on top)"),
    ("logo", 1, "PETG cream + coral", "back face down; filament change at 1.2 mm (coral letters) and 3.6 mm (cream highlights)"),
    ("logo_sparkles_yellow", 1, "PETG yellow", "back face down (3 pieces)"),
    ("logo_sparkles_mint", 1, "PETG mint", "back face down (2 pieces)"),
    ("logo_sparkles_coral", 1, "PETG coral", "back face down (2 pieces)"),
]
_V3_HARDWARE = [
    ("M3 x 16 countersunk (DIN 7991) screw", 4, "coin plate -> front wall -> coin housing lugs (self tapping)"),
    ("M3 x 25 screw", 1, "blocking pawl pivot, from behind: head sunk 3 mm in the housing, self taps in the front fork"),
    ("M3 x 12 screw", 1, "anti-reverse pawl pivot, from behind through the housing sleeve into the boss (self tapping): the head clamps the sleeve, the pawl turns free"),
    ("M3 x 16 screw", 1, "crank -> hex shaft, through the hub cap (self tapping)"),
    ("glue (CA or 2-part epoxy)", 1, "BOLABOL badge into its front wall pocket, sparkles into the badge pockets"),
    ("pen spring, OD <= 5.5 mm, cut to ~10 mm, stiff: >= 120 g at the pawl nose", 1,
     "NOT optional in v3: snaps the blocking pawl into the empty pocket while the wheel turns (seat in the housing hump). "
     "0.02 N m: blocks a coinless flick up to ~0.11 s/turn (a soft 60 g spring lets ~0.15 s/turn through). "
     "Check: lift the nose to the rim with a kitchen scale. Keep a spare"),
]


def parts_list(style="v1", mech="v2"):
    if style != "mochi":
        return PARTS
    out = []
    for name, qty, mat_, note in PARTS:
        if name.startswith("case_post_") or (mech == "v3" and name in _V3_DROP):
            continue
        m2, n2 = (_V3_SWAP if mech == "v3" and name in _V3_SWAP else _MOCHI_SWAP).get(name, (mat_, note))
        out.append((name, qty, m2, n2))
    return out + _MOCHI_ADD + (_V3_ADD if mech == "v3" else [])


def hardware_list(style="v1", mech="v2"):
    hw = [h for h in HARDWARE if style != "mochi" or "lid -> case posts" not in h[2]]
    if mech == "v3":                    # bezel, pawl pivots through the wall, knob screw and spring note change
        hw = [h for h in hw if not any(k in h[2] for k in ("bezel", "pawl pivot", "knob ->"))] + _V3_HARDWARE
    return hw


TEST_PARTS = [
    ("test_gear_jig", "gear train jig: + gear_A, gear_B_pinion, pinion_axle, shim_04 and spares"),
    ("test_crown_sector", "70 deg crown sector: sits on the shim like the rotor"),
    ("test_hex_coupon_gears", "hex shaft piece for the gear jig (tests the 16 mm hex fit)"),
    ("test_token_jig", "front-wall section: + knob, bezel, dog_pawl (+ spring), ratchet, ratchet_pawl, sleeve_front, token"),
    ("test_hex_coupon_token", "hex shaft piece for the token jig"),
]


def _fits(dims):
    """Best orientation on the bed: returns (ok, how)."""
    lim = BED - 2 * BED_MARGIN
    a, b, c = sorted(dims)
    for h, (w, d) in ((a, (b, c)), (b, (a, c)), (c, (a, b))):
        if h > 250:
            continue
        if w <= lim and d <= lim:
            return True, "flat %.0fx%.0f h%.0f" % (w, d, h)
        if (w + d) / sqrt(2) <= lim and d <= lim * sqrt(2):
            return True, "diagonal %.0fx%.0f h%.0f" % (w, d, h)
    return False, "too big %.0fx%.0fx%.0f" % (a, b, c)


def check_and_export(folder, parts=None):
    os.makedirs(folder, exist_ok=True)
    dg = bpy.context.evaluated_depsgraph_get()
    rows = []
    for name, qty, mat_name, note in (parts or PARTS):
        ob = bpy.data.objects.get(name)
        if ob is None:
            rows.append((name, qty, mat_name, "MISSING", "", "", note))
            continue
        me = ob.evaluated_get(dg).to_mesh()
        bm = bmesh.new()
        bm.from_mesh(me)
        bad = sum(1 for e in bm.edges if not e.is_manifold)
        vol = abs(bm.calc_volume()) * 1e9 / 1000.0             # cm^3
        bm.free()
        ob.evaluated_get(dg).to_mesh_clear()
        dims = [d * 1000.0 for d in ob.dimensions]
        ok, how = _fits(dims)
        path = os.path.join(folder, name + ".stl")
        _export_one(ob, path)
        tris = _stl_tris(path)
        rows.append((name, qty, mat_name, ("OK " if ok else "NO ") + how,
                     ("manifold" if bad == 0 else "%d open edges" % bad) if tris else "STL BUIT", "%.1f" % vol, note))
        if not tris:
            print("WARNING: %s exported with 0 triangles" % path)
    return rows


def _export_one(ob, path):
    """export_selected_objects only sees objects visible in the view layer: parts in a hidden
    collection (capsules, spare shims) came out as 84-byte STLs. Link the part to the scene root
    for the export so it is always visible and selectable."""
    root = bpy.context.scene.collection
    linked = ob.name not in root.objects
    if linked:
        root.objects.link(ob)
    hidden = ob.hide_get(), ob.hide_viewport
    ob.hide_set(False)
    ob.hide_viewport = False
    bpy.context.view_layer.update()
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    try:
        with bpy.context.temp_override(selected_objects=[ob], active_object=ob, object=ob):
            bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True, global_scale=1000.0,
                                  apply_modifiers=True)
    finally:
        ob.select_set(False)
        ob.hide_set(hidden[0])
        ob.hide_viewport = hidden[1]
        if linked:
            root.objects.unlink(ob)


def _stl_tris(path):
    """Triangle count from the binary STL header (0 = empty file)."""
    with open(path, "rb") as f:
        f.seek(80)
        return int.from_bytes(f.read(4), "little")


TEST_PARTS_V3 = TEST_PARTS[:3] + [
    ("test_coin_jig", "front-wall section: + coin_plate, coin_housing, coin_wheel, dog_pawl (+ spring), ratchet_pawl, knob (crank), token"),
    ("test_hex_coupon_coin", "hex shaft piece for the coin jig (crank -> wheel -> rear bracket)"),
]


# v3 coin mech: how to try the test kit, and what the dynamic simulation (coin_test.py) says
V3_TEST_GUIDE = """### Prova del moneder v3 (proves_5 + proves_6): què comprovar

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
  la moneda acaba al calaix. Bateria completa: `gacha/coin_battery.py`.
- Monedes d'euro: la de 50 cèntims (24.25 mm) passa com una fitxa; la de 2 € (25.75 mm) és just a la vora: passa o
  s'encalla a l'entrada segons el cop. 1 € i 20 cèntims bloquegen.

Si el gatet no cau prou ràpid: molla més dura (pesa-la: ≥ 120 g al nas, aixecat fins a la vora). Si la moneda no entra sola: puja `SLOT_RAMP` (parts_coin.py).
"""


def export_tests(folder, mech="v2"):
    return check_and_export(folder, [(n, 1, "PETG", note) for n, note in (TEST_PARTS_V3 if mech == "v3" else TEST_PARTS)])


def write_bom(rows, path, test_rows=(), plates=(), hardware=None, title="# Gachapon - peces i ferreteria",
              folder="stl", extra=""):
    lines = [title, "",
             "| Peça | Qt | Material | Llit 220x220 | Malla | Volum cm3 | Orientació |",
             "|---|---|---|---|---|---|---|"]
    lines += ["| %s | %d | %s | %s | %s | %s | %s |" % r for r in rows]
    lines += ["", "## Ferreteria", "", "| Element | Qt | Ús |", "|---|---|---|"]
    lines += ["| %s | %d | %s |" % h for h in (hardware if hardware is not None else HARDWARE)]
    if test_rows:
        lines += ["", "## Peces de prova (imprimir primer: %s/proves/)" % folder, "",
                  "Munta-les amb les peces reals indicades (de %s/). Si engranen i bloquegen bé a mà," % folder,
                  "la màquina sencera també ho farà amb la mateixa impressora i material.", "",
                  "| Fitxer | Llit | Malla | Amb |", "|---|---|---|---|"]
        lines += ["| %s | %s | %s | %s |" % (r[0], r[3], r[4], r[6]) for r in test_rows]
    if plates:
        lines += ["", "### Plaques 3MF per a Flash Studio (AD5M Pro): %s/proves/*.3mf" % folder, "",
                  "Fetes amb FlashPrep (print3mf.py): orientades, col·locades i amb els ajustos per peça.",
                  "L'informe de cada placa és dins el 3MF (Metadata/FlashPrep_report.txt).",
                  "Les _PLA serveixen per provar el mecanisme; els ajustos justos, confirma'ls amb el material final.", "",
                  "| Placa | Material | Peces | Capa | Suports | Temps | Filament |", "|---|---|---|---|---|---|---|"]
        lines += ["| %s | %s | %s | %s mm | %s | %s | %.0f g |" % p for p in plates]
    if extra:
        lines += ["", extra.rstrip()]
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return path
