"""Build the whole gachapon in the current Blender scene.

Run inside Blender:
    import sys; sys.path.insert(0, "<this folder>"); import build; build.main()
"""
import importlib
import sys
import time
import traceback
import bpy

MODULES = ["params", "gears", "mk", "parts_body", "parts_shell", "parts_rotor", "parts_drive", "parts_coin",
           "parts_logo", "parts_token", "parts_chute", "parts_capsule", "parts_test"]
PALETTE = {  # style -> (body, accent, frame, coral)
    "v1": ((0.90, 0.89, 0.86, 1), (0.78, 0.06, 0.05, 1), (0.78, 0.06, 0.05, 1), (0.78, 0.06, 0.05, 1)),
    "mochi": ((0.38, 0.76, 0.60, 1), (1.0, 0.26, 0.26, 1), (1.0, 0.90, 0.78, 1), (1.0, 0.26, 0.26, 1)),
}


def reload_all(style="v1", mech="v2", coins=1):
    """params first, switched to style / mech, then the part modules: their `from params import *`
    copies must see the switched constants."""
    import params
    importlib.reload(params)
    params.STYLE = style
    params.COIN_POCKETS = coins
    params.apply_mech(mech)
    for name in MODULES[1:]:
        if name in sys.modules:
            importlib.reload(sys.modules[name])
        else:
            importlib.import_module(name)


def materials():
    import mk
    import params
    body, accent, frame, coral = PALETTE[params.STYLE]
    two = params.COIN_POCKETS == 2          # 2-coin machine: sky blue body, own material (both machines in one scene)
    return {
        'body': mk.mat("G_body_sky", SKY, 0.5) if two else mk.mat("G_body", body, 0.5),
        'accent': mk.mat("G_accent", accent, 0.35),
        'frame': mk.mat("G_frame", frame, 0.45),
        'coral': mk.mat("G_coral", coral, 0.35),
        'rotor': mk.mat("G_rotor", (0.10, 0.10, 0.12, 1), 0.55),
        'gear': mk.mat("G_gear", (0.82, 0.82, 0.78, 1), 0.35),
        'window': mk.mat("G_window", (0.85, 0.92, 1.0, 1), 0.03, transmission=1.0, alpha=0.18),
        'door': mk.mat("G_door", (0.55, 0.60, 0.66, 1), 0.08, transmission=0.8, alpha=0.45),
        'token': mk.mat("G_token", (0.90, 0.68, 0.18, 1), 0.3, metal=1.0),
        'cap_clear': mk.mat("G_cap_clear", (0.95, 0.97, 1.0, 1), 0.05, transmission=1.0, alpha=0.25),
        'cap_colors': [mk.mat("G_cap_%d" % i, c, 0.3) for i, c in enumerate([
            (0.85, 0.08, 0.10, 1), (0.10, 0.35, 0.85, 1), (0.98, 0.78, 0.08, 1),
            (0.10, 0.65, 0.30, 1), (0.95, 0.45, 0.70, 1), (0.98, 0.45, 0.05, 1), (0.55, 0.25, 0.80, 1)])],
    }


SKY = (0.32, 0.60, 0.84, 1)      # 2-coin machine body


def collections():
    import mk
    root = mk.coll("GACHA")
    return {'root': root,
            'fixed': mk.coll("G_fixed", root),
            'move': mk.coll("G_moving", root),
            'caps': mk.coll("G_capsules", root),
            'tests': mk.coll("G_test_jigs", root)}


def setup_scene():
    s = bpy.context.scene
    s.unit_settings.system = 'METRIC'
    s.unit_settings.scale_length = 1.0
    try:
        s.unit_settings.length_unit = 'MILLIMETERS'
    except Exception:
        pass


def main(only=None, style="v1", mech="v2", coins=1):
    """style "v1": square shell; "mochi": rounded v2 shell (parts_shell), same mechanism.
    mech "v2": knob with the token slit + bezel + outside token chute; "v3": hidden coin mech
    (parts_coin: coin wheel inside, flush coin plate, crank, coin duct to the drawer)."""
    reload_all(style, mech, coins)
    import params
    import mk
    import parts_body as B
    import parts_rotor as R
    import parts_drive as D
    import parts_token as T
    import parts_chute as H
    import parts_capsule as K
    import parts_test as P
    import parts_shell as S
    mochi = style == "mochi"
    from params import XO

    setup_scene()
    old = bpy.data.collections.get("GACHA")
    if old is not None and only is None:
        mk.wipe(old)
    C, M = collections(), materials()
    steps = [
        ("base_box", lambda: B.make_base_box(C, M)),
        ("mech_box", lambda: B.make_mech_box(C, M)),
        ("case", lambda: S.make_case_mochi(C, M) if mochi else B.make_case(C, M)),
        ("deck", lambda: R.make_deck(C, M)),
        ("rotor", lambda: R.make_rotor(C, M)),
        ("crown_ring", lambda: R.make_crown_ring(C, M)),
        ("shims", lambda: R.make_shims(C, M)),
        ("funnel", lambda: R.make_funnel(C, M)),
        ("hood", lambda: R.make_hood(C, M)),
        ("knob", lambda: D.make_knob(C, M)),
        ("bezel", lambda: D.make_bezel(C, M)),
        ("hex_shaft", lambda: D.make_hex_shaft(C, M)),
        ("sleeves", lambda: D.make_sleeves(C, M)),
        ("ratchet", lambda: D.make_ratchet(C, M)),
        ("spacer", lambda: D.make_spacer(C, M)),
        ("gear_A", lambda: D.make_gear_a(C, M)),
        ("gear_B_pinion", lambda: D.make_b_pinion(C, M)),
        ("axle", lambda: D.make_axle(C, M)),
        ("deck_bracket", lambda: D.make_deck_bracket(C, M)),
        ("dog", lambda: T.make_dog(C, M)),
        ("ratchet_pawl", lambda: T.make_ratchet_pawl(C, M)),
        ("token_chute", lambda: T.make_token_chute(C, M)),
        ("drawer", lambda: T.make_drawer(C, M)),
        ("tokens", lambda: T.make_tokens(C, M)),
        ("chute", lambda: H.make_chute(C, M)),
        ("door", lambda: H.make_door(C, M)),
        ("door_ears", lambda: B.make_door_ears(C, M)),
        ("capsule_pair", lambda: K.make_pair(C, M, (XO + 60.0, -60.0, 27.0))),
        ("test_jigs", lambda: [P.make_gear_jig(C, M), P.make_crown_sector(C, M)]
         + [P.make_coin_jig(C, M) if mech == "v3" else P.make_token_jig(C, M)] + P.make_hex_coupons(C, M)),
    ]
    if mech == "v3":
        import parts_coin as W
        import parts_logo as LG
        v3 = {"knob": [("coin_wheel", lambda: W.make_coin_wheel(C, M)), ("knob", lambda: W.make_crank(C, M))],
              "bezel": [("coin_housing", lambda: W.make_coin_housing(C, M)),
                        ("coin_plate", lambda: W.make_coin_plate(C, M)),
                        ("logo", lambda: LG.make_logo(C, M))],               # BOLABOL badge over the plate
              "ratchet": [], "token_chute": []}         # ratchet teeth on the wheel, coin duct in the base box
        steps = [s for name, fn in steps for s in v3.get(name, [(name, fn)])]
    report = []
    for name, fn in steps:
        if only and name not in only:
            continue
        t0 = time.time()
        try:
            res = fn()
            objs = res if isinstance(res, (list, tuple)) else (res.values() if isinstance(res, dict) else [res])
            info = ", ".join("%s:%dv" % (o.name, len(o.data.vertices)) for o in objs)
            report.append("OK   %-14s %5.2fs  %s" % (name, time.time() - t0, info))
        except Exception:
            report.append("FAIL %-14s %s" % (name, traceback.format_exc(limit=3)))
    if mochi and (not only or "feet" in only):         # like the steps: build.main(only=...) must not duplicate
        report.append("OK   %-14s %s" % ("feet", ", ".join(o.name for o in S.make_feet(C, M))))
    if mochi:
        for name, key in (("bezel", 'frame'), ("door_ear_0", 'coral'), ("door_ear_1", 'coral')):
            ob = bpy.data.objects.get(name)
            if ob is not None:
                ob.data.materials[0] = M[key]
    lc = bpy.context.view_layer.layer_collection.children["GACHA"].children.get("G_test_jigs")
    if lc:
        lc.hide_viewport = True                 # jigs share the machine frame: hidden in the assembly
        lc.collection.hide_render = True
    print("\n".join(report))
    return report
