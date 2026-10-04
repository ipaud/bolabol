"""Functional battery for the v3/v4 coin mech, on the coin_test harness. Needs the UI (Bullet under -b
is unreliable): the script runs from a timer and quits Blender when done.

    Blender <copy>.blend --python gacha/coin_battery.py -- <out.json> [1|2|velocitat]

1 / 2 = the 1- or 2-coin machine; velocitat = how fast a coinless turn must be to slip past the pawl;
euro = every euro coin (and glued pairs), report only: 50 cent and 2 EUR can turn the wheel (accepted; making
them block needs a 7 mm token and a 0.4 mm pawl lead, which snags the 2-coin wheel: tried and dropped 28/09/2026).

Each case states what must happen: "pass" = the wheel completes the turn and every coin ends in the
drawer, "block" = the wheel stops at the pawl, "info" = no requirement (foreign coins), just report."""
import json
import os
import sys
import time
import traceback
from math import pi
import bpy
import bmesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from params import TOKEN_T

ARGS = sys.argv[sys.argv.index("--") + 1:]
OUT, SUITE = ARGS[0], ARGS[1] if len(ARGS) > 1 else "1"
COINS = 2 if SUITE == "2" else 1
EURO = {"1 cent": (16.25, 1.67, 2.3), "2 cent": (18.75, 1.67, 3.06), "5 cent": (21.25, 1.67, 3.92),
        "10 cent": (19.75, 1.93, 4.1), "20 cent": (22.25, 2.14, 5.74), "50 cent": (24.25, 2.38, 7.8),
        "1 EUR": (23.25, 2.33, 7.5), "2 EUR": (25.75, 2.20, 8.5)}      # diameter mm, thickness mm, mass g
PAIRS = [("20 cent", "20 cent"), ("50 cent", "20 cent"), ("50 cent", "50 cent"), ("2 EUR", "2 EUR"),
         ("1 EUR", "50 cent")]                          # glued face to face: one thicker coin

CASES_1 = [
    ("sense moneda, 2 s", "block", dict(coin=False, turn_s=2.0)),
    ("sense moneda, cop 0.15 s", "block", dict(coin=False, turn_s=0.15)),
    ("sense moneda, molla fatigada 0.01, 0.3 s", "block", dict(coin=False, turn_s=0.3, spring=0.01)),
    ("moneda, 2 s", "pass", dict(turn_s=2.0)),
    ("moneda, 0.5 s", "pass", dict(turn_s=0.5)),
    ("moneda, cop 0.12 s", "pass", dict(turn_s=0.12)),
    ("moneda girada (Boli davant), 1 s", "pass", dict(turn_s=1.0, flip=True)),
    ("moneda 24.5 mm, 1 s", "pass", dict(turn_s=1.0, coin_d=24.5)),
    ("moneda 25.5 mm, 1 s", "pass", dict(turn_s=1.0, coin_d=25.5)),
    ("moneda prima -0.3 mm, 1 s", "pass", dict(turn_s=1.0, coin_t=TOKEN_T - 0.3)),
    ("moneda gruixuda +0.2 mm, 1 s", "pass", dict(turn_s=1.0, coin_t=TOKEN_T + 0.2)),
    ("moneda +0.3 mm (fora de tolerància), 1 s", "info", dict(turn_s=1.0, coin_t=TOKEN_T + 0.3)),
    ("friccio PETG (mu 0.25), 2 s", "pass", dict(turn_s=2.0, friction=0.5)),
    ("friccio PETG (mu 0.25), 0.3 s", "pass", dict(turn_s=0.3, friction=0.5)),
    ("friccio alta (mu 0.49), 1 s", "pass", dict(turn_s=1.0, friction=0.7)),
    ("molla forta 0.03, 1 s", "pass", dict(turn_s=1.0, spring=0.03)),
    ("friccio alta + molla forta, 0.3 s", "pass", dict(turn_s=0.3, spring=0.03, friction=0.7)),
]

CASES_EURO = [("%s, %g s" % (k, ts), "info", dict(turn_s=ts, coin_d=d, coin_t=t, mass=m / 1000.0))
              for k, (d, t, m) in EURO.items() for ts in ((2.0, 0.3) if k in ("50 cent", "1 EUR", "2 EUR") else (1.0,))] + \
             [("%s + %s enganxades, 1 s" % (a, b), "info",
               dict(turn_s=1.0, coin_d=max(EURO[a][0], EURO[b][0]), coin_t=EURO[a][1] + EURO[b][1],
                    mass=(EURO[a][2] + EURO[b][2]) / 1000.0)) for a, b in PAIRS]

CASES_2 = [
    ("sense monedes, 2 s", "block", dict(coin="")),
    ("nomes A, 2 s", "block", dict(coin="A")),
    ("nomes B, 2 s", "block", dict(coin="B")),
    ("nomes A, cop 0.15 s", "block", dict(coin="A", turn_s=0.15)),
    ("A+B, 2 s", "pass", dict(coin="AB")),
    ("A+B, 0.3 s", "pass", dict(coin="AB", turn_s=0.3)),
    ("A+B, friccio PETG (mu 0.25), 1 s", "pass", dict(coin="AB", turn_s=1.0, friction=0.5)),
]

CASES_SPEED = [("sense moneda, molla %.2f, %.2f s" % (sp, t), "info", dict(coin=False, turn_s=t, spring=sp))
               for sp in (0.01, 0.02, 0.03) for t in (0.18, 0.16, 0.14, 0.12, 0.10)] + \
              [("moneda, molla %.2f, %.2f s" % (sp, t), "pass", dict(turn_s=t, spring=sp))
               for sp in (0.02, 0.03) for t in (2.0, 0.12)]


def disc_mesh(src, keep):
    """token_0 of the 2-coin machine holds both coins: copy with only coin A (+x) or B (-x)."""
    me = src.data.copy()
    bm = bmesh.new()
    bm.from_mesh(me)
    mw = src.matrix_world
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if ((mw @ v.co).x > 0) != (keep == "A")], context='VERTS')
    bm.to_mesh(me)
    bm.free()
    return me


def verdict(s):
    zs = [xz[1] for xz in (s.get("coin_final_xz"), s.get("coinB_final_xz")) if xz]
    if s["wheel_final"] > 320:         # the harness hand is a soft spring: with high friction the wheel lags ~30 deg
        return "pass" if all(z < 20 for z in zs) else "moneda encallada"
    return "block" if s["wheel_final"] < 90 else "a mitges (%.0f deg)" % s["wheel_final"]


def run_case(T, kw, tok, split):
    kw = dict(kw)
    flip, mass, coins = kw.pop("flip", False), kw.pop("mass", None), kw.pop("coin", True)
    if split:                                   # 2-coin machine: token_0 = A or B, the other coin added below
        tok.data = (split["A"] if coins in ("A", "AB") else split["B"]).copy()
        coins = bool(coins) and coins
    T.build(coin=bool(coins), fps=240, substeps=64, **{"spring": 0.02, "turn_s": 2.0, **kw})
    sc, o = T.OBJ["sc"], T.OBJ["o"]
    second = None
    if coins:
        c = o["token_0"]
        if flip:
            c.rotation_euler = (0, 0, pi)
        if mass:
            c.rigid_body.mass = mass
        if coins == "AB":
            second = bpy.data.objects.new("ct_token_b", split["B"].copy())
            sc.collection.objects.link(second)
            second.matrix_world = tok.matrix_world.copy()
            second.rotation_euler = (0, 0, 0)
            bpy.context.view_layer.update()
            T._recenter_bbox(second)
            T._rb(sc, second, 'ACTIVE', 'CONVEX_HULL', mass=0.0025, friction=kw.get("friction") or 0.3)
            T._groups(second, 0, 1)
    sc.frame_set(1)
    s = T.summary(T.step())
    if second is not None:
        p = second.matrix_world.translation * 1000
        s["coinB_final_xz"] = (round(p.x, 1), round(p.z, 1))
    return s


def main():
    import build
    build.reload_all(style="mochi", mech="v3", coins=COINS)
    import coin_test as T
    for o in bpy.data.objects:
        if o.animation_data:
            o.animation_data.action = None
    tok = bpy.data.objects["token_0"]
    full = tok.data
    split = {k: disc_mesh(tok, k) for k in "AB"} if COINS == 2 else None
    bm = bmesh.new()
    bm.from_mesh(full)
    res = {"suite": SUITE, "token_vol_mm3": round(abs(bm.calc_volume()) * 1e9), "cases": []}
    bm.free()
    for name, expect, kw in {"1": CASES_1, "2": CASES_2, "velocitat": CASES_SPEED, "euro": CASES_EURO}[SUITE]:
        t0 = time.time()
        row = {"case": name, "expect": expect}
        try:
            s = run_case(T, kw, tok, split)
            row.update(summary=s, got=verdict(s), secs=round(time.time() - t0, 1))
            row["ok"] = expect == "info" or row["got"] == expect
        except Exception:
            row.update(error=traceback.format_exc(), ok=False)
        finally:
            try:
                T.done()
            except Exception:
                pass
            tok.data = full
        res["cases"].append(row)
        json.dump(res, open(OUT, "w"), indent=1, default=str)
        print("BAT>", name, row.get("got"), row.get("ok"), row.get("summary") or row.get("error"), flush=True)


def _go():
    try:
        main()
    finally:
        os._exit(0)


bpy.app.timers.register(_go, first_interval=2.0)
