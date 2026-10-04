"""Machine body: base box (outlet, drawer), mech box (deck ledges, bearings), case posts, windows, lid."""
from math import radians
import bmesh
from mathutils import Matrix
import mk
import params as _P
from params import *


def rounded():
    """v2 'mochi' shell (build.main(style="mochi")): rounded plan, see parts_shell."""
    return _P.STYLE == "mochi"


def coin_v3():
    """v3 hidden coin mech (build.main(mech="v3")): front-wall holes and duct from parts_coin."""
    return _P.MECH == "v3"

POST = 6.0          # post reaches this far inside the interior corner
WIN_T = 3.0         # acrylic (or clear PETG) window thickness
DOOR_PIN_Z = OUTLET_Z[1] + 4.5
DOOR_PIN_Y = YFO - 2.75
EAR_X = (OUTLET_X[0] - 4.5, OUTLET_X[1] + 4.5)   # separate hinge ears keep the base box bed-sized
EAR_SCREW_Z = OUTLET_Z[1] - 2.5                   # below the pin, where the wall is solid
PIN_WIRE_R = 1.0            # 1.75 mm wire, snug in the ears (was a printed 2 mm pin in 0.65 mm walls)


def make_door_ears(C, M):
    """Two small hinge ears screwed (M3 self-tap) to the front wall; the door pins run in them."""
    out = []
    for i, x in enumerate(EAR_X):
        out.append(mk.build("door_ear_%d" % i, C['fixed'], M['body'],
                            add=[lambda bm, x=x: mk.box(bm, x - 4.0, x + 4.0, YFO - 6.5, YFO - 0.05,
                                                        OUTLET_Z[1] - 6.0, OUTLET_Z[1] + 8.0)],
                            cut=[lambda bm, x=x: x_cyl(bm, PIN_WIRE_R, x - 5, x + 5, DOOR_PIN_Y, DOOR_PIN_Z),
                                 lambda bm, x=x: mk.fv_cyl(bm, M3_CLR / 2, YFO - 8, YFO + 1, x, EAR_SCREW_Z, 16)]))
    return out


def x_cyl(bm, r, x0, x1, y, z, seg=24):
    """Cylinder along X from x0 to x1 through (y, z)."""
    vs = mk.cyl(bm, r, x0, x1, seg)
    bmesh.ops.transform(bm, matrix=Matrix.Translation((0, y, z)) @ Matrix.Rotation(radians(90), 4, 'Y'), verts=vs)
    return vs


def _walls(z0, z1):
    if rounded():
        import parts_shell as S
        return [lambda bm: S.ring(bm, 0.0, WALL, z0, z1)]
    return [
        lambda bm: mk.box(bm, -XO, XO, YFO, YF, z0, z1),
        lambda bm: mk.box(bm, -XO, XO, YR, YRO, z0, z1),
        lambda bm: mk.box(bm, -XO, -XI, YF - 0.5, YR + 0.5, z0, z1),
        lambda bm: mk.box(bm, XI, XO, YF - 0.5, YR + 0.5, z0, z1),
    ]


def countersink(p):
    """90 deg countersink on the outer front face for an M3 flat head (DIN 7991, head 6 mm)."""
    prof = [(0, YFO - 1.0), (3.2, YFO - 1.0), (3.2, YFO), (M3_CLR / 2, YFO + 3.2 - M3_CLR / 2), (0, YFO + 3.2 - M3_CLR / 2)]
    return lambda bm: mk.fv_lathe(bm, prof, 24, p[0], p[1])


def tslot_z():
    """Front-wall window for the token chute."""
    return tchute_floor(YF) - 2.4 - 0.4, tchute_floor(YFO) + 33.4 + 0.4


def corner_xy(inset=4.5):
    if rounded():
        inset += 1.5                    # screw heads / wells stay clear of the rounded skin
    return [(sx * (XI - inset), y) for sx in (-1, 1) for y in (YF + inset, YR - inset)]


def _corner_blocks(z0, z1, size=9.0):
    size += 2.0 if rounded() else 0.0
    out = []
    for sx in (-1, 1):
        for front in (True, False):
            x0, x1 = (XI - size, XI + 0.5) if sx > 0 else (-XI - 0.5, -XI + size)
            y0, y1 = (YF - 0.5, YF + size) if front else (YR - size, YR + 0.5)
            out.append(lambda bm, b=(x0, x1, y0, y1): mk.box(bm, b[0], b[1], b[2], b[3], z0, z1))
    return out


def funnel_screw_xy():
    """Funnel -> mech box screws (clear of the case posts that stand on the funnel corners)."""
    return corner_xy(9.0)                # 7.5 left 0.5 mm walls around the wells on the rounded skin


def make_base_box(C, M):
    z0, z1 = tslot_z()
    cuts = [
        lambda bm: mk.box(bm, OUTLET_X[0], OUTLET_X[1], YFO - 1, YF + 1, OUTLET_Z[0], OUTLET_Z[1]),
        lambda bm: mk.box(bm, DRAWER_X[0], DRAWER_X[1], YFO - 1, YF + 1, DRAWER_Z[0], DRAWER_Z[1]),
    ] + [lambda bm, x=x: mk.fv_cyl(bm, 1.4, YFO - 1, YF + 1, x, EAR_SCREW_Z, 16) for x in EAR_X]   # ear screws
    cuts += [lambda bm, p=p: mk.cyl(bm, 1.4, Z_SPLIT - 11.0, Z_SPLIT + 1, 16, p[0], p[1]) for p in corner_xy()]
    duct = []
    if coin_v3():                       # coin falls inside: duct from the funnel to the drawer
        import parts_coin as K
        cuts += K.wall_cuts()
        duct = K.duct_parts()
    else:                               # token chute through the front wall
        cuts.append(lambda bm: mk.box(bm, -TCHUTE_W / 2 - 2.3, TCHUTE_W / 2 + 2.3, YFO - 1, YF + 1, z0, z1))
    floor, inter = (lambda bm: mk.box(bm, -XO, XO, YFO, YRO, 0, Z_FLOOR_T)), []
    if rounded():
        import parts_shell as S
        floor = lambda bm: S.plate(bm, 0.0, 0.0, Z_FLOOR_T)
        inter = [S.skin_between(0.0, Z_SPLIT, bottom=3.0, top=1.0)]
        cuts += [lambda bm, p=p: mk.cyl(bm, 4.1, -1.0, Z_FLOOR_T + 1.0, 32, p[0], p[1]) for p in S.foot_xy()]
    ob = mk.build("base_box", C['fixed'], M['body'], add=[floor],
                  union_parts=_walls(Z_FLOOR_T - 0.5, Z_SPLIT) + _corner_blocks(Z_SPLIT - 12.0, Z_SPLIT) + duct
                  + drawer_lock_post() + chute_stops(), cut=cuts + drawer_lock_cuts(), inter=inter)
    tongues = []                        # after the skin intersect, which stops at the joint
    for f in centring_tongues():
        b = bmesh.new()
        f(b)
        tongues.append(mk.tmp(b))
    mk.boolean(ob, tongues, 'UNION')
    return ob


def centring_tongues():
    """2 mm tongues up from the base box top edge, 0.2 inside the mech box walls: the boxes line up by themselves
    (before, only the 4 corner screws located them). Back, sides, and the front outside the coin mech; they stop
    short of the corner blocks. Printed floor down, they are the last layers: no supports."""
    t, g, c = 1.6, 0.25, 9.0 + (2.0 if rounded() else 0.0) + 1.5
    z, w = Z_SPLIT, g + t
    hi = (z - 0.5, z + 2.0)
    out = []
    def piece(xa, xb, ya, yb, za, zb):
        return lambda bm: mk.box(bm, min(xa, xb), max(xa, xb), min(ya, yb), max(ya, yb), za, zb)
    def gusset_y(face, inward, x0, x1):             # joint to the wall, 45 deg underneath (no flat overhang)
        f = [(face - 0.5 * inward, z - 3.0), (face - 0.5 * inward, z), (face + w * inward, z),
             (face + w * inward, z - 0.2), (face, z - 0.2 - w), (face, z - 3.0)]
        return lambda bm: mk.yz_prism(bm, f, x0, x1)
    def gusset_x(face, inward, y0, y1):
        f = [(face - 0.5 * inward, z - 3.0), (face - 0.5 * inward, z), (face + w * inward, z),
             (face + w * inward, z - 0.2), (face, z - 0.2 - w), (face, z - 3.0)]
        return lambda bm: mk.fv_prism(bm, f, y0, y1)
    out += [gusset_y(YR, -1, -XI + c, XI - c), piece(-XI + c, XI - c, YR - w, YR - g, *hi)]
    for sx in (-1, 1):
        out += [gusset_x(sx * XI, -sx, YF + c, YR - c), piece(sx * (XI - w), sx * (XI - g), YF + c, YR - c, *hi),
                gusset_y(YF, 1, min(sx * 56.0, sx * (XI - c)), max(sx * 56.0, sx * (XI - c))),
                piece(sx * 56.0, sx * (XI - c), YF + g, YF + w, *hi)]
    return out


def chute_stops():
    """3 mm floor stops around the capsule chute's feet: it stands loose on the floor and could slide 5-12 mm,
    out of line with the drop hole. Sides and back here; the front wall stops it at the cup lip."""
    from parts_chute import _xs
    _, _, xo0, xo1 = _xs()
    z0, z1, ya, yb = Z_FLOOR_T - 0.5, Z_FLOOR_T + 3.0, YF + 10.0, Y_CUP_BACK - 4.0
    return [lambda bm: mk.box(bm, xo0 - 3.3, xo0 - 0.3, ya, yb, z0, z1),               # left
            lambda bm: mk.box(bm, xo1 + 0.3, xo1 + 2.3, ya, yb, z0, z1),               # right (drawer 1.7 mm away)
            lambda bm: mk.box(bm, xo0, xo0 + 3.0, Y_CUP_BACK + 0.3, Y_CUP_BACK + 3.3, z0, z1),   # behind the feet
            lambda bm: mk.box(bm, xo1 - 3.0, xo1, Y_CUP_BACK + 0.3, Y_CUP_BACK + 3.3, z0, z1)]


def drawer_lock_post():
    """Post behind the right end of the drawer front, off the floor and tied into the front wall."""
    x, z1 = DRAWER_LOCK_X, DRAWER_Z[1] - 1.0
    return [lambda bm: mk.box(bm, x - 4.0, DRAWER_X[1] + 4.0, YF + 0.6, YF + 10.6, Z_FLOOR_T - 0.5, z1),
            lambda bm: mk.box(bm, DRAWER_X[1] + 0.2, DRAWER_X[1] + 4.0, YF - 0.5, YF + 0.7, Z_FLOOR_T - 0.5, z1)]


def drawer_lock_cuts():
    """M3 clearance through the post + hex nut pockets open at the back (pointed top: prints without support)."""
    x, r = DRAWER_LOCK_X, 5.6 / sqrt(3)
    out = []
    for z in DRAWER_LOCK_Z:
        hexa = [(x + r * cos(radians(90 + 60 * i)), z + r * sin(radians(90 + 60 * i))) for i in range(6)]
        out += [lambda bm, z=z: mk.fv_cyl(bm, M3_CLR / 2, YF, YF + 11.0, x, z, 16),
                lambda bm, h=hexa: mk.fv_prism(bm, h, YF + 4.0, YF + 11.0)]
    return out


def make_mech_box(C, M):
    zl1 = Z_DECK_PLATE_TOP - DECK_PLATE_T
    zl0 = zl1 - 3.5
    ledges = [
        lambda bm: mk.box(bm, -XI - 0.5, XI + 0.5, YF - 0.5, YF + LEDGE, zl0, zl1),
        lambda bm: mk.box(bm, -XI - 0.5, -24.0, YR - LEDGE, YR + 0.5, zl0, zl1),     # gap for the pinion
        lambda bm: mk.box(bm, 24.0, XI + 0.5, YR - LEDGE, YR + 0.5, zl0, zl1),
        lambda bm: mk.box(bm, -XI - 0.5, -XI + LEDGE, YF, YR, zl0, zl1),
        lambda bm: mk.box(bm, XI - LEDGE, XI + 0.5, YF, YR, zl0, zl1),
    ]
    hole = (SLEEVE_D + CLR_FREE) / 2
    rp = 0.5 * (BEZEL_R0 + BEZEL_R1)
    _, _, _, rP = ratchet_pawl_geom()
    dx, dz = dog_pivot()
    cuts = [
        lambda bm: mk.fv_cyl(bm, hole, YFO - 1, YF + 1, 0, Z_HANDLE),
        lambda bm: mk.fv_cyl(bm, hole, YR - 1, YRO + 1, 0, Z_HANDLE),
        lambda bm: mk.fv_cyl(bm, (AXLE_D - 0.1) / 2, YR - 1, YRO + 1, 0, Z_PIN_AX),   # press fit
    ]
    if coin_v3():                       # coin slot + plate / housing screws; the pawls live in the housing
        import parts_coin as K
        import parts_logo as L
        cuts += K.wall_cuts() + L.recess_cuts()     # + pocket for the BOLABOL badge
    else:
        cuts += [
            lambda bm: mk.fv_cyl(bm, 1.4, YFO - 1, YF + 1, dx, dz, 16),                # dog pivot screw
            lambda bm: mk.fv_cyl(bm, M3_CLR / 2, YFO - 1, YF + 1, rP[0], rP[1], 16),    # ratchet pawl screw
            countersink(rP),                            # its head sits under the knob, 1.8 mm away: flush
        ]
        for a in (90.0, 240.0, 330.0):                                          # bezel screws
            x, z = fv(rp, a)
            cuts.append(lambda bm, x=x, z=z: mk.fv_cyl(bm, 1.4, YFO - 1, YF + 1, x, Z_HANDLE + z, 16))
    for p in corner_xy():                                                         # joint screws M3x16
        cuts.append(lambda bm, p=p: mk.cyl(bm, M3_CLR / 2, Z_SPLIT - 1, Z_SPLIT + 13, 16, p[0], p[1]))
        cuts.append(lambda bm, p=p: mk.cyl(bm, 3.2, Z_SPLIT + 6.0, Z_SPLIT + 13, 24, p[0], p[1]))
    for p in funnel_screw_xy():                                                   # funnel screws (self-tap)
        cuts.append(lambda bm, p=p: mk.cyl(bm, 1.4, Z_BODY_TOP - 10.0, Z_BODY_TOP + 1, 16, p[0], p[1]))
    walls, inter = [lambda bm: mk.box(bm, -XO, XO, YFO, YF, Z_SPLIT, Z_BODY_TOP)] + _walls(Z_SPLIT, Z_BODY_TOP)[1:], []
    if rounded():
        import parts_shell as S
        walls = _walls(Z_SPLIT, Z_BODY_TOP)
        ledges = [lambda bm: S.ring(bm, WALL - 0.5, WALL + LEDGE, zl0, zl1)]
        cuts.append(lambda bm: mk.box(bm, -24.0, 24.0, YR - LEDGE - 1.0, YR - 0.01, zl0 - 1, zl1 + 1))   # pinion gap
        inter = [S.skin_between(Z_SPLIT, Z_BODY_TOP, bottom=1.0, top=1.0)]
    return mk.build("mech_box", C['fixed'], M['body'], add=walls[:1],
                    union_parts=walls[1:] + ledges + _corner_blocks(Z_SPLIT, Z_SPLIT + 12.0)
                    + _corner_blocks(Z_BODY_TOP - 12.0, Z_BODY_TOP, 12.0),
                    cut=cuts, inter=inter)


def window_slabs(grow=0.0):
    g = grow
    z0, z1 = Z_RIM, Z_CASE_TOP - 0.2
    return {
        "front": (-XI + 0.2 - g, XI - 0.2 + g, YF - WIN_T - g, YF + g, z0, z1),
        "back": (-XI + 0.2 - g, XI - 0.2 + g, YR - g, YR + WIN_T + g, z0, z1),
        "left": (-XI - WIN_T - g, -XI + g, YF + 0.2 - g, YR - 0.2 + g, z0, z1),
        "right": (XI - g, XI + WIN_T + g, YF + 0.2 - g, YR - 0.2 + g, z0, z1),
    }


def post_pins():
    """Peg / screw axis of each post: centre of its solid part inside the interior corner."""
    out = []
    for sx in (-1, 1):
        for front in (True, False):
            out.append((sx * (XI - 3.1), YF + 3.1 if front else YR - 3.1))
    return out


def post_boxes():
    out = []
    for sx in (-1, 1):
        for front in (True, False):
            x0, x1 = (XI - POST, XO) if sx > 0 else (-XO, -XI + POST)
            y0, y1 = (YFO, YF + POST) if front else (YR - POST, YRO)
            out.append((x0, x1, y0, y1))
    return out


def make_case(C, M):
    objs = {}
    slabs = window_slabs(0.2)
    for i, (b, p) in enumerate(zip(post_boxes(), post_pins())):
        objs["post%d" % i] = mk.build(
            "case_post_%d" % i, C['fixed'], M['accent'],
            add=[lambda bm, b=b: mk.box(bm, b[0], b[1], b[2], b[3], Z_RIM, Z_CASE_TOP)],
            union_parts=[lambda bm, p=p: mk.cyl(bm, 2.0, Z_RIM - 4.0, Z_RIM + 0.5, 24, p[0], p[1])],
            cut=[lambda bm, s=s: mk.box(bm, *s) for s in slabs.values()] +
                [lambda bm, p=p: mk.cyl(bm, 1.4, Z_CASE_TOP - 10.0, Z_CASE_TOP + 1, 16, p[0], p[1])])
    for name, s in window_slabs(0.0).items():
        objs["win_" + name] = mk.build("window_" + name, C['fixed'], M['window'],
                                       add=[lambda bm, s=s: mk.box(bm, *s)])
    objs["lid"] = mk.build("lid", C['fixed'], M['accent'],
                           add=[lambda bm: mk.box(bm, -XO, XO, YFO, YRO, Z_CASE_TOP, Z_CASE_TOP + LID_T)],
                           cut=[lambda bm, p=p: mk.cyl(bm, M3_CLR / 2, Z_CASE_TOP - 1, Z_CASE_TOP + LID_T + 1, 16,
                                                      p[0], p[1]) for p in post_pins()])
    return objs
