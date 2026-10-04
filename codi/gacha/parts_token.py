"""Token path: blocking pawl (dog), anti-reverse pawl, token chute, drawer, tokens."""
import json
import os
from math import radians, tan, pi, cos, sin
import mk
from parts_body import x_cyl, countersink
from params import *

ZH = Z_HANDLE
Z_TIP = ZH + KNOB_R            # dog nose tip height in the "riding on the rim" pose


FOOT_X = (6.5, 9.5)


def foot_z():
    """Foot bottom height so that, rotated DOG_STOP deg nose-down, it just lands on the knob rim."""
    from math import sqrt
    px, pz = dog_pivot()
    a = radians(DOG_STOP)                       # CCW in the front view lowers the nose
    need = []
    for x in FOOT_X:
        # solve z: rotated point lies on the rim circle -> scan (monotonic, small range)
        best = None
        for i in range(2001):
            z = Z_TIP - 2.0 + i * 0.005
            dx, dz = x - px, z - pz
            rx, rz = px + dx * cos(a) - dz * sin(a), pz + dx * sin(a) + dz * cos(a)
            if abs(rx) < KNOB_R and rz - Z_HANDLE >= sqrt(KNOB_R ** 2 - rx ** 2) + 0.05:
                best = z
                break
        need.append(best)
    return max(need)


def hub_top_z():
    return dog_pivot()[1] + 4.5


def dog_outline():
    """Front-view outline (absolute) of the blocking pawl, nose riding on the knob rim."""
    px, pz = dog_pivot()
    x0, x1 = DOG_TIP
    zb = Z_TIP + DOG_NOSE_H                     # lever underside at the nose
    zt = zb + 6.0                               # lever top
    ramp = tan(radians(DOG_RAMP))
    xr = x1 + DOG_NOSE_H * ramp
    hub = [(px + 4.5 * cos(a), pz + 4.5 * sin(a)) for a in [-pi / 2 + pi * i / 12 for i in range(13)]]

    def under(x):                               # lever underside line nose -> hub bottom
        return zb + (hub[0][1] - zb) * (x - xr) / (hub[0][0] - xr)

    zf = foot_z()
    tip = [(x0, Z_TIP + DOG_LEAD), (x0 + DOG_LEAD, Z_TIP)] if DOG_LEAD else [(x0, Z_TIP)]
    pts = tip + [(x1, Z_TIP), (xr, zb),
           (FOOT_X[0], under(FOOT_X[0])), (FOOT_X[0], zf), (FOOT_X[1], zf), (FOOT_X[1], under(FOOT_X[1]))]
    pts += hub
    pts += [(x0, zt)]
    return pts


def make_dog(C, M):
    """Gravity pawl. Rests inside the empty slit at home (handle locked); a token pushed into the
    knob lifts it via the 45 deg front chamfer; the 30 deg rear flank cams it out when backing off.
    v3: built at 12 o'clock and turned DOG_ANGLE onto the coin wheel rim; the coin arrives from
    behind the front wall already seated, so no lead-in chamfer."""
    px, pz = dog_pivot()
    y0, y1 = DOG_Y0, DOG_Y1
    chamfer = [(y0 - 0.5, Z_TIP + 5.5), (y0 - 0.5, Z_TIP - 1.0), (y0 + 6.0, Z_TIP - 1.0)]   # lead-in only
    ys = 0.5 * (y0 + y1)
    zl = Z_TIP + DOG_NOSE_H + 6.0 + (hub_top_z() - (Z_TIP + DOG_NOSE_H + 6.0)) * (SPRING_X - DOG_TIP[0]) \
        / (px - DOG_TIP[0])                     # lever top height at the spring seat
    cuts = [lambda bm: mk.fv_cyl(bm, M3_CLR / 2, y0 - 1, y1 + 1, px, pz, 16)]
    if MECH != "v3":
        cuts.append(lambda bm: mk.yz_prism(bm, chamfer, -6, 6))
    ob = mk.build("dog_pawl", C['move'], M['accent'], origin=(px, 0, pz),
                  add=[lambda bm: mk.fv_prism(bm, dog_outline(), y0, y1)],
                  union_parts=[lambda bm: mk.cyl(bm, 1.7, zl - 1.0, zl + 1.0, 16, SPRING_X, ys)],   # spring stub
                  cut=cuts)
    return mk.turn_y(ob, DOG_ANGLE, 0.0, ZH) if DOG_ANGLE else ob


def make_ratchet_pawl(C, M):
    """Gravity pawl on the saw teeth: +t face is radial (locks reverse), lever offset so it clears
    the tooth tips when the nose drops into a root."""
    N, t, n, P = ratchet_pawl_geom()

    def at(a, b):                               # a along the tangent, b along the normal, from the nose tip
        return N[0] + a * t[0] + b * n[0], N[1] + a * t[1] + b * n[1]

    nose = [at(-1.0, 0.0), at(1.0, 0.0), at(1.0, 9.0), at(-1.0, 9.0)]
    lever = [at(1.0, 9.0), at(-20.0, 9.0), at(-20.0, 3.0), at(-1.0, 3.0)]
    return mk.build("ratchet_pawl", C['move'], M['accent'], origin=(P[0], 0, P[1]),
                    add=[lambda bm: mk.fv_prism(bm, nose, RAT_Y0, RAT_Y1)],
                    union_parts=[lambda bm: mk.fv_prism(bm, lever, RAT_Y0, RAT_Y1),
                                 lambda bm: mk.fv_cyl(bm, RAT_SLEEVE_R + 2.3, RAT_Y0, RAT_Y1, P[0], P[1], 32)],
                    cut=[lambda bm: mk.fv_cyl(bm, RAT_SLEEVE_R + CLR_FREE / 2, RAT_Y0 - 1, RAT_Y1 + 1, P[0], P[1], 24)])


TV_Y = KNOB_Y1 + 26.0          # end of the V mouth, start of the narrow chute (-115)
V_IN = [(-2.6, 0.0), (2.6, 0.0), (2.6, 6.0), (26.0, 29.4), (26.0, 60.0), (-26.0, 60.0), (-26.0, 29.4), (-2.6, 6.0)]
V_OUT = [(-5.0, -2.4), (5.0, -2.4), (5.0, 5.0), (28.4, 28.4), (28.4, 29.4), (-28.4, 29.4), (-28.4, 28.4), (-5.0, 5.0)]


def make_token_chute(C, M):
    """V mouth under the bezel (catches the token wherever it leaves the slit and stands it on
    edge), then a closed slide through the front wall into the drawer."""
    ya, yb, yw = KNOB_Y1 - 4.0, -99.0, YFO
    t, f, w = 2.4, tchute_floor, TCHUTE_W / 2
    tube_o = [(TV_Y - 1.0, f(TV_Y - 1.0) - t), (yb, f(yb) - t), (yb, f(yb) + 31 + t), (TV_Y - 1.0, f(TV_Y - 1.0) + 31 + t)]
    tube_i = [(TV_Y - 2.0, f(TV_Y - 2.0)), (yb + 1, f(yb + 1)), (yb + 1, f(yb + 1) + 31), (TV_Y - 2.0, f(TV_Y - 2.0) + 31)]
    return mk.build("token_chute", C['fixed'], M['body'],
                    add=[lambda bm: mk.swept(bm, V_OUT, ya, f(ya), TV_Y, f(TV_Y))],
                    union_parts=[lambda bm: mk.yz_prism(bm, tube_o, -w - 2.0, w + 2.0)],
                    cut=[lambda bm: mk.swept(bm, V_IN, ya + 2.0, f(ya + 2.0), TV_Y - 1.0, f(TV_Y - 1.0)),
                         lambda bm: mk.yz_prism(bm, tube_i, -w, w)])


def make_drawer(C, M):
    x0, x1 = DRAWER_X[0] + 0.5, DRAWER_LOCK_X - 4.5            # body clears the lock post on the right
    y0, y1 = YF, YF + DRAWER_D
    z0, z1 = Z_FLOOR_T + 0.5, DRAWER_Z[1] - 2.0
    ob = mk.build("token_drawer", C['fixed'], M['accent'],
                    add=[lambda bm: mk.box(bm, x0, x1, y0, y1, z0, z1)],
                    union_parts=[lambda bm: mk.box(bm, DRAWER_X[0] + 0.2, DRAWER_X[1] - 0.2, YFO + 0.1, YF + 0.5,
                                                   DRAWER_Z[0] + 0.2, DRAWER_Z[1] - 0.2)],
                    cut=[lambda bm: mk.box(bm, x0 + 2, x1 - 2, y0 + 2, y1 - 2, z0 + 2, z1 + 5),
                         lambda bm: mk.box(bm, 16, 30, YFO - 1, YF + 0.6, DRAWER_Z[1] - 8, DRAWER_Z[1])]
                    + [f for z in DRAWER_LOCK_Z for f in (countersink((DRAWER_LOCK_X, z)),
                       lambda bm, z=z: mk.fv_cyl(bm, M3_CLR / 2, YFO - 1, YF + 1, DRAWER_LOCK_X, z, 16))])
    if DRAWER_RAMP:                     # coins land under the duct at the front and pile up into it: slide them back
        import bmesh
        from math import tan, radians
        yf, zf, zt = y0 + 1.9, z0 + 1.9, z1 - 2.0
        prof = [(yf, zf), (yf + (zt - zf) / tan(radians(DRAWER_RAMP)), zf), (yf, zt)]
        b = bmesh.new()
        mk.yz_prism(b, prof, x0 + 1.9, x1 - 1.9)
        mk.boolean(ob, [mk.tmp(b)], 'UNION')
    return ob


TOKEN_ART = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "brand", "token_faces.json")
ENGRAVE = 0.6                       # v3 coins: BBOL logo cut into one face, Boli into the other (3 layers each)
COIN_CHAMFER = 0.4                  # v3 coins: 45 deg on both edges (eats the first-layer elephant foot, leads the
                                    # coin into the slot and under the pawl nose)


def _coin_profile(z0, z1):
    """Coin half section (r, z) for mk.lathe: chamfered edges on v3, plain cylinder otherwise."""
    r, c = TOKEN_D / 2, COIN_CHAMFER if MECH == "v3" else 0.0
    return [(0, z0), (r - c, z0), (r, z0 + c), (r, z1 - c), (r - c, z1), (0, z1)] if c else \
        [(0, z0), (r, z0), (r, z1), (0, z1)]


def _x_coin(bm, x0, x1, y, z):
    """Coin with its axis along X (the one in the wheel pocket), like parts_body.x_cyl."""
    from math import radians as _rad
    import bmesh
    from mathutils import Matrix
    vs = mk.lathe(bm, _coin_profile(x0, x1), 48)
    bmesh.ops.transform(bm, matrix=Matrix.Translation((0, y, z)) @ Matrix.Rotation(_rad(90), 4, 'Y'), verts=vs)
    return vs


def _engrave(ob, faces):
    """Cut the coin face art (brand/token_faces.json, made by brand/trace_token.py) into ob.
    faces: [(art key, builder(bm, ring_mm) for one ring)]. Each traced feature is its outer ring minus
    its holes, so the paper islands (counters, highlights, eyes) stay at face level."""
    import bmesh
    art = json.load(open(TOKEN_ART))
    cutters = []
    for key, prism in faces:
        for poly in art[key]:
            parts = []
            for ring in poly:
                b = bmesh.new()
                prism(b, ring)
                parts.append(mk.tmp(b))
            if len(parts) > 1:
                mk.boolean(parts[0], parts[1:], 'DIFFERENCE')
            cutters.append(parts[0])
    return mk.boolean(ob, cutters, 'DIFFERENCE')


def make_tokens(C, M):
    """One token pushed flush into the knob slit (ready to turn), two in the drawer. v3: BBOL on the +x
    face (on the bed when printed, bold enough to bridge), Boli on the other (on top, finer)."""
    out = []
    zc = ZH + SLIT_FLOOR_R + TOKEN_D / 2
    t, e = TOKEN_T / 2, ENGRAVE
    out.append(mk.build("token_0", C['move'], M['token'], origin=(0, 0, ZH),
                        add=[lambda bm, x=x: _x_coin(bm, x - TOKEN_T / 2, x + TOKEN_T / 2, TOKEN_Y, zc)
                             for x in pocket_xs()]))           # 2-coin machine: both coins in one object
    art = MECH == "v3" and os.path.exists(TOKEN_ART)
    if art:                                                    # seen from +x: right = +y; from -x: right = -y
        _engrave(out[0], [f for x in pocket_xs() for f in (
            ("bbol", lambda bm, r, x=x: mk.yz_prism(bm, [(TOKEN_Y + u, zc + v) for u, v in r], x + t - e, x + t + 1)),
            ("boli", lambda bm, r, x=x: mk.yz_prism(bm, [(TOKEN_Y - u, zc + v) for u, v in r], x - t - 1, x - t + e)))])
    for i, (x, y) in enumerate(((8.0, -55.0), (31.0, -32.0))):      # on the drawer floor, past the ramp
        z0 = Z_FLOOR_T + 2.5
        ob = mk.build("token_%d" % (i + 1), C['fixed'], M['token'],
                      add=[lambda bm, x=x, y=y: mk.lathe(bm, _coin_profile(z0, z0 + TOKEN_T), 48, x, y)])
        if art:                                                # seen from above: right = +x; from below: -x
            _engrave(ob, [("bbol", lambda bm, r, x=x, y=y: mk.prism(bm, [(x + u, y + v) for u, v in r], z0 + TOKEN_T - e, z0 + TOKEN_T + 1)),
                          ("boli", lambda bm, r, x=x, y=y: mk.prism(bm, [(x - u, y + v) for u, v in r], z0 - 1, z0 + e))])
        out.append(ob)
    return out
