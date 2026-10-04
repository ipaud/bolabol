"""V2 'Mochi' shell: rounded plan (R_PLAN), cream frame of corner pillars + pillow lid, flat recessed
windows, topper and feet. Same mechanism as v1: build.main(style="mochi").

Plan corner radius is capped by the capsule outlet: its door hinge ear sits at x = -89.5 and needs
the flat front face (XO - R_PLAN = 89.7). At the side midpoints only 5.2 mm separate the rotor edge
from the skin, so the rim band clears the rotor by 2 mm vertically there.
"""
from math import cos, sin, radians, sqrt, atan2
from mathutils import Matrix
import bmesh
import mk
from params import *

R_PLAN = 17.0               # outer plan corner radius (v1: square)
CYC = 0.5 * (YFO + YRO)     # plan centre y
M2_RIM = 242.0              # cream rim band top = pillar bottom
M2_TOP = 390.0              # pillar top = lid bottom
M2_LID = 424.0              # lid top
LID_FILLET = 16.0
PIL_T = 7.0                 # pillar wall (skin -> inner face)
PIL_EXT = 10.0              # pillar flat past the corner arc
SLOT = 7.0                  # window edge slot depth in the pillar flat
WIN_T2 = 2.0                # window sheet (2 mm acrylic / PETG): inner face at XI, hopper as wide as v1
WIN_IN = 1.2                # window outer face recess from the skin (1 mm outer lip on slots and grooves)
GROOVE = 3.0                # rim / lid groove depth
FOOT_IN = 24.0              # foot centre inset from the skin
FOOT_R, FOOT_H = 14.0, 8.0
PEG_R = 2.0                 # pillar pegs (holes +0.2)
LID_LOCK = ((1, 1), (-1, -1))   # back-right and front-left: M3x16 countersunk through the pillar into a tab of the lid
LOCK_Z = M2_TOP - 6.0


def diag(bm, verts, sx, sy, z):
    """Lay a Z-axis primitive (s = distance from the corner arc centre) along the corner diagonal at height z."""
    cx, cy = arc_centre(sx, sy)
    m = Matrix.Translation((cx, cy, z)) @ Matrix.Rotation(atan2(sy, sx), 4, 'Z') @ Matrix.Rotation(radians(90), 4, 'Y')
    bmesh.ops.transform(bm, matrix=m, verts=verts)


def lock_tab_poly(sx, sy, r0=1.0, r1=8.8, w=4.0):    # corners stay inside the pillar bore (r 10)
    cx, cy = arc_centre(sx, sy)
    d, t = (sx / sqrt(2), sy / sqrt(2)), (-sy / sqrt(2), sx / sqrt(2))
    return [(cx + d[0] * r + t[0] * q, cy + d[1] * r + t[1] * q) for r, q in ((r0, -w), (r1, -w), (r1, w), (r0, w))]


# --------------------------------------------------------------------------- plan outlines

def rrect(d, seg=12):
    """Rounded plan outline inset d from the skin (corner arcs concentric with the skin)."""
    r = max(R_PLAN - d, 0.5)
    x1, y0, y1 = XO - d, YFO + d, YRO - d
    pts = []
    for cx, cy, a0 in ((x1 - r, y1 - r, 0), (-(x1 - r), y1 - r, 90), (-(x1 - r), y0 + r, 180), (x1 - r, y0 + r, 270)):
        pts += [(cx + r * cos(radians(a0 + 90.0 * i / seg)), cy + r * sin(radians(a0 + 90.0 * i / seg)))
                for i in range(seg + 1)]
    return pts


def plate(bm, d, z0, z1):
    return mk.prism(bm, rrect(d), z0, z1)


def ring(bm, d_out, d_in, z0, z1):
    """Rounded band between two insets."""
    out, inn = rrect(d_out), rrect(d_in)
    ol, oh = [bm.verts.new((x, y, z0)) for x, y in out], [bm.verts.new((x, y, z1)) for x, y in out]
    il, ih = [bm.verts.new((x, y, z0)) for x, y in inn], [bm.verts.new((x, y, z1)) for x, y in inn]
    n = len(out)
    faces = []
    for i in range(n):
        j = (i + 1) % n
        for f in ((ol[i], ol[j], oh[j], oh[i]), (il[j], il[i], ih[i], ih[j]),
                  (ol[j], ol[i], il[i], il[j]), (oh[i], oh[j], ih[j], ih[i])):
            faces.append(bm.faces.new(f))
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    return ol + oh + il + ih


def skin(bm, prof):
    """Outer skin solid: stack of outlines (z, inset) bottom to top (fillets / chamfers)."""
    rings = [[bm.verts.new((x, y, z)) for x, y in rrect(d)] for z, d in prof]
    n = len(rings[0])
    faces = []
    for a, b in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            faces.append(bm.faces.new((a[i], a[j], b[j], b[i])))
    faces.append(bm.faces.new(list(reversed(rings[0]))))
    faces.append(bm.faces.new(rings[-1]))
    bmesh.ops.recalc_face_normals(bm, faces=faces)


def fillet(z_edge, f, n=6, up=True):
    s = -1 if up else 1
    pts = [(z_edge + s * (f - f * sin(radians(90.0 * i / n))), f - f * cos(radians(90.0 * i / n))) for i in range(n + 1)]
    return pts if up else pts[::-1]


def skin_between(z0, z1, bottom=0.0, top=0.0):
    """Skin callable for mk.build(inter=...): 45 deg chamfers at the bottom / top outer edges."""
    prof = ([(z0, bottom), (z0 + bottom, 0.0)] if bottom else [(z0, 0.0)]) + \
           ([(z1 - top, 0.0), (z1, top)] if top else [(z1, 0.0)])
    return lambda bm: skin(bm, prof)


# --------------------------------------------------------------------------- corners

CORNERS = ((1, -1), (1, 1), (-1, 1), (-1, -1))


def arc_centre(sx, sy):
    return sx * (XO - R_PLAN), (YRO - R_PLAN) if sy > 0 else (YFO + R_PLAN)


def pillar_point(sx, sy, r=R_PLAN - PIL_T / 2):
    """Mid-thickness point of the pillar on the corner diagonal (pegs, screw)."""
    cx, cy = arc_centre(sx, sy)
    return cx + sx * r / sqrt(2), cy + sy * r / sqrt(2)


def pillar_poly(sx, sy, seg=12, grow=0.0):
    cx, cy = arc_centre(sx, sy)
    a0 = {(1, -1): 270, (1, 1): 0, (-1, 1): 90, (-1, -1): 180}[(sx, sy)]
    paths = []
    ext = PIL_EXT + grow
    for rr in (R_PLAN + grow, R_PLAN - PIL_T - grow):
        arc = [(cx + rr * cos(radians(a0 + 90.0 * i / seg)), cy + rr * sin(radians(a0 + 90.0 * i / seg)))
               for i in range(seg + 1)]
        t0 = (-sin(radians(a0)), cos(radians(a0)))
        t1 = (-sin(radians(a0 + 90)), cos(radians(a0 + 90)))
        paths.append([(arc[0][0] - t0[0] * ext, arc[0][1] - t0[1] * ext)] + arc
                     + [(arc[-1][0] + t1[0] * ext, arc[-1][1] + t1[1] * ext)])
    return paths[0] + paths[1][::-1]


def window_boxes(grow=0.0):
    """Flat windows between the pillar slots (x0, x1, y0, y1)."""
    g = grow
    wx = XO - R_PLAN - PIL_EXT + SLOT - 0.5 + g          # half width into the slots
    wy0, wy1 = YFO + R_PLAN + PIL_EXT - SLOT + 0.5 - g, YRO - R_PLAN - PIL_EXT + SLOT - 0.5 + g
    a, b = WIN_IN - g, WIN_IN + WIN_T2 + g
    return {"front": (-wx, wx, YFO + a, YFO + b), "back": (-wx, wx, YRO - b, YRO - a),
            "left": (-XO + a, -XO + b, wy0, wy1), "right": (XO - b, XO - a, wy0, wy1)}


def groove(bm, z0, z1):
    return ring(bm, WIN_IN - 0.2, WIN_IN + WIN_T2 + 0.2, z0, z1)


def foot_xy():
    return [(sx * (XO - FOOT_IN), (YRO - FOOT_IN) if sy > 0 else (YFO + FOOT_IN)) for sx, sy in CORNERS]


# --------------------------------------------------------------------------- parts

def make_case_mochi(C, M):
    objs = {}
    slots = [lambda bm, b=b: mk.box(bm, b[0], b[1], b[2], b[3], M2_RIM - 1.0, M2_TOP + 1.0)
             for b in window_boxes(0.2).values()]
    for i, (sx, sy) in enumerate(CORNERS):
        px, py = pillar_point(sx, sy)
        objs["pillar%d" % i] = mk.build(
            "pillar_%d" % i, C['fixed'], M['frame'],
            add=[lambda bm, sx=sx, sy=sy: mk.prism(bm, pillar_poly(sx, sy), M2_RIM, M2_TOP)],
            union_parts=[lambda bm, px=px, py=py: mk.cyl(bm, PEG_R, M2_RIM - 4.0, M2_RIM + 0.5, 24, px, py),
                         lambda bm, px=px, py=py: mk.cyl(bm, PEG_R, M2_TOP - 0.5, M2_TOP + 4.0, 24, px, py)],
            cut=slots)
    for i, (sx, sy) in enumerate(CORNERS):          # lid lock: clearance + countersink through the pillar corner
        if (sx, sy) not in LID_LOCK:
            continue
        def _c(f):
            b = bmesh.new()
            f(b)
            return mk.tmp(b)
        mk.boolean(objs["pillar%d" % i], [
            _c(lambda bm, sx=sx, sy=sy: diag(bm, mk.cyl(bm, M3_CLR / 2, 9.5, R_PLAN + 1.0, 16), sx, sy, LOCK_Z)),
            _c(lambda bm, sx=sx, sy=sy: diag(bm, mk.frustum(bm, M3_CLR / 2, M3_CLR / 2 + 3.0, R_PLAN - 1.5, R_PLAN + 1.5, 24),
                                            sx, sy, LOCK_Z))], 'DIFFERENCE')
    wz0, wz1 = M2_RIM - GROOVE + 0.25, M2_TOP + GROOVE - 0.25
    for name, b in window_boxes().items():
        objs["win_" + name] = mk.build("window_" + name, C['fixed'], M['window'],
                                       add=[lambda bm, b=b: mk.box(bm, b[0], b[1], b[2], b[3], wz0, wz1)])
    objs["lid"] = mk.build(
        "lid", C['fixed'], M['frame'],
        add=[lambda bm: skin(bm, [(M2_TOP, 0.0)] + fillet(M2_LID, LID_FILLET))],
        cut=[lambda bm: groove(bm, M2_TOP - 1.0, M2_TOP + GROOVE),
             lambda bm: mk.cyl(bm, 4.1, M2_LID - 6.0, M2_LID + 1.0, 32, 0.0, CYC)]
            + [lambda bm, p=pillar_point(sx, sy): mk.cyl(bm, PEG_R + 0.2, M2_TOP - 1.0, M2_TOP + 4.5, 24, p[0], p[1])
               for sx, sy in CORNERS])
    lid = objs["lid"]                  # hollow from below: 1491 cm3 almost solid. Step keeps 3 mm to the 16 mm fillet;
    zr = M2_LID - 3.0                   # printed top down, every layer is the same or smaller: no supports
    def _t(f):
        b = bmesh.new()
        f(b)
        return mk.tmp(b)
    mk.boolean(lid, [_t(lambda bm: plate(bm, 9.0, M2_TOP - 1.0, zr - 9.0)),
                     _t(lambda bm: plate(bm, 16.0, zr - 9.5, zr))], 'DIFFERENCE')
    mk.boolean(lid, [_t(lambda bm: mk.cyl(bm, 7.5, M2_LID - 8.0, zr + 0.5, 32, 0.0, CYC))]
               + [_t(lambda bm, c=c: mk.prism(bm, lock_tab_poly(*c), M2_TOP - 12.0, zr - 8.5)) for c in LID_LOCK], 'UNION')
    mk.boolean(lid, [_t(lambda bm, c=c: diag(bm, mk.cyl(bm, 1.4, 0.5, 10.5, 16), c[0], c[1], LOCK_Z)) for c in LID_LOCK],
               'DIFFERENCE')                                             # lock screw pilots in the tabs
    mk.boolean(lid, [_t(lambda bm: mk.cyl(bm, 4.1, M2_LID - 6.0, M2_LID + 1.0, 32, 0.0, CYC))], 'DIFFERENCE')
    objs["topper"] = mk.build(
        "topper", C['fixed'], M['coral'],
        add=[lambda bm: mk.lathe(bm, [(0, M2_LID), (15, M2_LID), (15.5, M2_LID + 5), (12, M2_LID + 13),
                                      (6, M2_LID + 17), (0, M2_LID + 18)], 64, 0.0, CYC)],
        union_parts=[lambda bm: mk.cyl(bm, 4.0, M2_LID - 5.5, M2_LID, 32, 0.0, CYC)])
    return objs


def make_feet(C, M):
    out = []
    for i, (x, y) in enumerate(foot_xy()):
        out.append(mk.build("foot_%d" % i, C['fixed'], M['frame'],
                            add=[lambda bm, x=x, y=y: mk.lathe(bm, [(0, -FOOT_H), (FOOT_R - 2, -FOOT_H), (FOOT_R, -FOOT_H + 2),
                                                                     (FOOT_R, 0.0), (0, 0.0)], 48, x, y)],
                            union_parts=[lambda bm, x=x, y=y: mk.cyl(bm, 4.0, -0.5, Z_FLOOR_T - 0.2, 32, x, y)]))
    return out
