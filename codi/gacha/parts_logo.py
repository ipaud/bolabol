"""BOLABOL logo badge on the mech box front, over the coin plate (v3), from brand/bolabol_logo.json
(made by brand/trace_logo.py from the logo PNG).

One badge printed back face down with two filament changes, like a die-cut sticker: cream base
(the whole logo's outline, sitting RECESS deep in a pocket of the front wall), coral letters,
cream highlights on top. The sparkles are small separate pieces in their own colours, glued into
pockets of the base (the mint ones would vanish on the mint body without the cream under them).
"""
import json
import os
import mk
from params import *

JSON = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "brand", "bolabol_logo.json")
LOGO_Z = 213.75                     # middle of the mint band between the coin plate (198.5) and the rim (229)
RECESS, BASE_T, POCKET = 0.6, 1.2, 0.6      # wall pocket, base thickness, sparkle pockets in the base
LETTER_H, HILITE_H, SPARK_H = 2.4, 0.6, 1.2  # heights over the base front
YB = YFO + RECESS                   # base back face (pocket floor)
YF = YB - BASE_T                    # base front face, 0.6 proud of the wall
YL = YF - LETTER_H                  # letter tops
COLOURS = {"coral": "#EF5459", "cream": "#FCF7ED", "yellow": "#FEBF41", "mint": "#4FAF9D"}


def _lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple([x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0])


def materials():
    return {k: mk.mat("L_" + k, _lin(v), 0.35) for k, v in COLOURS.items()}


def _data():
    d = json.load(open(JSON))
    w, h = d["size"]
    s = d["height_mm"] / h
    fv_pt = lambda p: ((p[0] - w / 2) * s, LOGO_Z + (p[1] - h / 2) * s)
    return d, lambda ring: [fv_pt(p) for p in ring[:-1]]          # GeoJSON rings repeat the first point


def _area(ring):
    return abs(sum(ring[i][0] * ring[i - 1][1] - ring[i - 1][0] * ring[i][1] for i in range(len(ring)))) / 2


def _outline(polys, ring):
    """Largest outer ring (the base / recess are one piece; tiny potrace islands dropped, holes filled)."""
    return max((ring(p[0]) for p in polys), key=_area)


def _prisms(polys, ring, y0, y1, holes=False):
    y0, y1 = sorted((y0, y1))
    rings = [r for p in polys for r in (p[1:] if holes else p[:1])]
    return [lambda bm, r=ring(r): mk.fv_prism(bm, r, y0, y1) for r in rings]


def recess_cuts():
    """Front-wall pocket for the badge base (with fit clearance)."""
    d, ring = _data()
    return [lambda bm: mk.fv_prism(bm, _outline(d["recess"], ring), YFO - 1.0, YB)]


def _paint(ob, L):
    """Face colours by depth: letters coral, base and highlights cream (the printed colour layers)."""
    me = ob.data
    me.materials.clear()
    for k in ("cream", "coral"):
        me.materials.append(L[k])
    y_mid = lambda p: sum((ob.matrix_world @ me.vertices[i].co).y for i in p.vertices) / len(p.vertices) / MM
    for p in me.polygons:
        y = y_mid(p)
        p.material_index = 1 if YL - 0.01 <= y <= YF - 0.01 else 0


def make_logo(C, M):
    d, ring = _data()
    L = materials()
    badge = mk.build(
        "logo", C['fixed'], L['cream'],
        add=_prisms(d["letters"], ring, YF + 0.2, YL),
        union_parts=[lambda bm: mk.fv_prism(bm, _outline(d["base"], ring), YF, YB)]
        + _prisms(d["highlights"], ring, YL + 0.2, YL - HILITE_H),
        cut=_prisms(d["letters"], ring, YF, YL - 1.0, holes=True)                    # counters show the base
        + _prisms(d["pockets"], ring, YF + POCKET, YF - 1.0))
    _paint(badge, L)
    mk.smooth(badge, 40)
    out = [badge]
    for k, polys in d["sparkles"].items():
        ob = mk.build("logo_sparkles_" + k, C['fixed'], L[k],
                      add=_prisms(polys, ring, YF + POCKET, YF - SPARK_H))
        mk.smooth(ob, 40)
        out.append(ob)
    return out
