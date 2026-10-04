"""Drive train: knob (token slit), bezel, hex shaft, sleeves, ratchet wheel, gear column, pinion, axle."""
from math import radians, pi, sin, cos, sqrt, tan
import mk
from gears import spur_profile
from params import *

ZH = Z_HANDLE


def hex_pts(af, cx, cz, rot_deg=0.0):
    r = af / sqrt(3)
    return [(cx + r * cos(radians(rot_deg + 60 * i)), cz + r * sin(radians(rot_deg + 60 * i))) for i in range(6)]


def hex_bore(y0, y1, cz=ZH):
    return lambda bm: mk.fv_prism(bm, hex_pts(HEX_AF + HEX_CLR, 0, cz), y0, y1)


def gear_xz(m, z, pa, phase, cz):
    return [(x, y + cz) for x, y in spur_profile(m, z, pa, GEAR_BACKLASH, phase)]


def stadium(w, h, cx, cz, seg=12):
    r, a = h / 2, w / 2 - h / 2
    pts = [(cx + a + r * cos(-pi / 2 + pi * i / seg), cz + r * sin(-pi / 2 + pi * i / seg)) for i in range(seg + 1)]
    pts += [(cx - a + r * cos(pi / 2 + pi * i / seg), cz + r * sin(pi / 2 + pi * i / seg)) for i in range(seg + 1)]
    return pts


def slit_cutter(y0, y1, r_top, x=0.0):
    """Radial token slit at 12 o'clock (home), floor sloping 2 deg down towards the rear stop."""
    prof = [(y0, ZH + slit_floor(y0)), (y1, ZH + slit_floor(y1)), (y1, ZH + r_top), (y0, ZH + r_top)]
    return lambda bm: mk.yz_prism(bm, prof, x - SLIT_W / 2, x + SLIT_W / 2)


def make_knob(C, M):
    yb = KNOB_Y1 - GRIP_D
    cuts = [
        hex_bore(Y_SHAFT0, KNOB_Y0 + 1),
        lambda bm: mk.fv_cyl(bm, M3_CLR / 2, yb - 1, Y_SHAFT0 + 0.5, 0, ZH, 16),
        lambda bm: mk.fv_cyl(bm, 3.3, yb - 1, yb + 6, 0, ZH, 24),                 # screw head counterbore
        slit_cutter(KNOB_Y1 - 1, SLIT_Y_REAR, KNOB_R + 2),
        lambda bm: mk.fv_prism(bm, [(-SLIT_W / 2 - 1.2, ZH + SLIT_FLOOR_R - 1.2), (SLIT_W / 2 + 1.2, ZH + SLIT_FLOOR_R - 1.2),
                                    (SLIT_W / 2 + 1.2, ZH + KNOB_R + 2), (-SLIT_W / 2 - 1.2, ZH + KNOB_R + 2)],
                               KNOB_Y1 - 1, KNOB_Y1 + 1.2),                          # slit mouth lead-in
    ]
    ob = mk.build("knob", C['move'], M['accent'], origin=(0, 0, ZH),
                  add=[lambda bm: mk.fv_cyl(bm, KNOB_R, KNOB_Y1, KNOB_Y0, 0, ZH, 128)],
                  union_parts=[lambda bm: mk.fv_prism(bm, stadium(GRIP_W, GRIP_H, 0, ZH), yb, KNOB_Y1 + 0.5)],
                  cut=cuts)
    mk.smooth(ob, 30)
    return ob


def _sector(r0, r1, a0, a1, seg=24):
    """Annular sector in front-view angles (CW from top), absolute around the handle axis."""
    outer = [fv(r1, a0 + (a1 - a0) * i / seg) for i in range(seg + 1)]
    inner = [fv(r0, a1 - (a1 - a0) * i / seg) for i in range(seg + 1)]
    return [(x, ZH + z) for x, z in outer + inner]


def make_bezel(C, M):
    """Fixed ring around the knob: keeps the token in its slit, houses the blocking pawl,
    lets the token fall out at 6 o'clock. A hump over the pawl bridges its window and holds a
    pen spring (~6x10 mm) that pushes the pawl nose down: gravity alone is too slow for fast spins."""
    dx, dz = dog_pivot()
    rp = 0.5 * (BEZEL_R0 + BEZEL_R1)
    ring = [(BEZEL_R0, KNOB_Y1), (BEZEL_R1, KNOB_Y1), (BEZEL_R1, YFO), (BEZEL_R0, YFO)]
    cuts = [
        lambda bm: mk.fv_prism(bm, _sector(BEZEL_R0 - 1, BEZEL_R1 + 1, -14.0, 42.0), DOG_Y0 - 1.0, DOG_Y1 + 1.0),
        lambda bm: mk.fv_prism(bm, _sector(BEZEL_R0 - 1, BEZEL_R1 + 1, 158.0, 202.0), KNOB_Y1 - 1, SLIT_Y_REAR + 2),  # token exit
        lambda bm: mk.fv_cyl(bm, M3_CLR / 2, KNOB_Y1 - 1, YFO + 1, dx, dz, 16),
    ]
    for a in (90.0, 240.0, 330.0):
        x, z = fv(rp, a)
        cuts.append(lambda bm, x=x, z=z: mk.fv_cyl(bm, M3_CLR / 2, KNOB_Y1 - 1, YFO + 1, x, ZH + z, 16))
        cuts.append(lambda bm, x=x, z=z: mk.fv_cyl(bm, 3.3, KNOB_Y1 - 1, KNOB_Y1 + 3, x, ZH + z, 24))
    ys = 0.5 * (DOG_Y0 + DOG_Y1)
    hump = lambda bm: mk.fv_prism(bm, _sector(BEZEL_R1 - 0.5, BEZEL_R1 + 7.0, -2.0, 10.0), KNOB_Y1, YFO)
    # teardrop pointing to the front: printed back face down, the pocket roof is 60 deg (the slicer
    # supports anything at or under 45), so no support gets trapped in the blind pocket
    rs = SPRING_D / 2
    tear = [(SPRING_X + rs * cos(radians(a)), ys + rs * sin(radians(a))) for a in range(-30, 211, 15)] \
        + [(SPRING_X, ys - 2.0 * rs)]
    cuts.append(lambda bm: mk.prism(bm, tear, ZH + BEZEL_R0, ZH + BEZEL_R1 + 7.0 - 2.5))
    ob = mk.build("bezel", C['fixed'], M['body'],
                  add=[lambda bm: mk.fv_lathe(bm, ring, 128, 0, ZH)], union_parts=[hump], cut=cuts)
    mk.smooth(ob, 30)
    return ob


def make_hex_shaft(C, M):
    return mk.build("hex_shaft", C['move'], M['gear'], origin=(0, 0, ZH),
                    add=[lambda bm: mk.fv_prism(bm, hex_pts(HEX_AF, 0, ZH), Y_SHAFT0, Y_SHAFT1)],
                    cut=[lambda bm: mk.fv_cyl(bm, 1.3, Y_SHAFT0 - 1, Y_SHAFT0 + 16, 0, ZH, 16)])   # crank M3x16 pilot


def make_sleeves(C, M):
    out = {}
    ends = (("sleeve_front", YFO - 1.0, YF + 0.5), ("sleeve_rear", YR - 0.5, YRO + 1.0))
    for name, y0, y1 in ends[1:] if MECH == "v3" else ends:            # v3: the coin wheel boss is the front bearing
        out[name] = mk.build(name, C['move'], M['gear'], origin=(0, 0, ZH),
                             add=[lambda bm, y0=y0, y1=y1: mk.fv_cyl(bm, SLEEVE_D / 2, y0, y1, 0, ZH, 64)],
                             cut=[hex_bore(y0 - 1, y1 + 1)])
    return out


def ratchet_radius(u):
    """Wheel radius at wheel-frame angle u (front-view deg): smooth back-off sector with a home
    notch, then 20 saw teeth whose steep faces block reverse rotation."""
    lo, hi = RAT_PAWL_ANGLE - RAT_FREE[1], RAT_PAWL_ANGLE - RAT_FREE[0]     # -65 .. -17
    u = (u - lo) % 360.0 + lo
    if u <= hi:
        if RAT_HOME_STEP:                                    # root at the home face, ramp up to the rim
            return RAT_R - RAT_DEPTH * max(0.0, 1.0 - (hi - u) / RAT_HOME_STEP)
        d = abs(u - RAT_PAWL_ANGLE)
        return RAT_R - RAT_NOTCH * max(0.0, 1.0 - d / 3.0)
    w = (lo + 360.0) - u                                     # distance back from the commit face
    frac = (w % RAT_PITCH) / RAT_PITCH
    return RAT_R - RAT_DEPTH * (1.0 - frac)


def ratchet_pts():
    lo, hi = RAT_PAWL_ANGLE - RAT_FREE[1], RAT_PAWL_ANGLE - RAT_FREE[0]
    us = [lo + (hi - lo) * i / 48 for i in range(49)]
    if RAT_HOME_STEP:
        us = sorted([u for u in us if abs(u - (hi - RAT_HOME_STEP)) > 0.1] + [hi - RAT_HOME_STEP])
    n_teeth = int(round((360.0 - (hi - lo)) / RAT_PITCH))
    pts = [(ratchet_radius(u), u) for u in us]
    if RAT_HOME_STEP:
        pts.append((RAT_R, hi + 0.01))                       # home face: backing off stops the crank at home
    for j in range(n_teeth, 0, -1):
        uk = lo + 360.0 - RAT_PITCH * j                      # steep face of tooth j
        if j != n_teeth:
            pts.append((RAT_R, uk))
        for i in range(1, 6):
            u = uk + RAT_PITCH * i / 5
            pts.append((RAT_R - RAT_DEPTH * i / 5, u if i < 5 else u - 0.01))
    return [(r * sin(radians(u)), ZH + r * cos(radians(u))) for r, u in pts]


def make_ratchet(C, M):
    return mk.build("ratchet", C['move'], M['gear'], origin=(0, 0, ZH),
                    add=[lambda bm: mk.fv_prism(bm, ratchet_pts(), RAT_Y0, RAT_Y1)],
                    union_parts=[lambda bm: mk.fv_cyl(bm, 14.0, YF + 0.9, RAT_Y1 + 0.5, 0, ZH, 48)],
                    cut=[hex_bore(YF, RAT_Y1 + 1)])


def make_spacer(C, M):
    return mk.build("spacer", C['move'], M['gear'], origin=(0, 0, ZH),
                    add=[lambda bm: mk.fv_cyl(bm, 12.0, RAT_Y1 + 0.5, COL_Y0 - 0.3, 0, ZH, 48)],
                    cut=[hex_bore(RAT_Y1, COL_Y0)])


def make_gear_a(C, M):
    return mk.build("gear_A", C['move'], M['gear'], origin=(0, 0, ZH),
                    add=[lambda bm: mk.fv_prism(bm, gear_xz(GM, Z_COL, PA_COL, 90.0, ZH), COL_Y0, COL_Y1)],
                    union_parts=[lambda bm: mk.fv_cyl(bm, 12.0, COL_Y1 - 0.5, YR - 0.7, 0, ZH, 48)],
                    cut=[hex_bore(COL_Y0 - 1, YR)])


def make_b_pinion(C, M):
    """Gear B (meshes with A) and the crown pinion on one printed part, free on a fixed axle."""
    zp = Z_PIN_AX
    ph_b = 90.0 + 180.0 / Z_COL           # space pointing down to A
    ph_p = 90.0 + 180.0 / Z_PIN           # space pointing up to a crown tooth
    # 40 deg cone under the pinion (was a r14 cylinder): printed gear B down, the pinion no longer
    # hangs over the gap, so no supports end up in gear B's tooth spaces. Kept < r_root at the face.
    r1 = 14.0 + tan(radians(40.0)) * (PIN_Y0 - COL_Y1)
    hub = [(0, COL_Y1 - 0.5), (14.0, COL_Y1 - 0.5), (14.0, COL_Y1), (r1, PIN_Y0),
           (16.0, PIN_Y0 + 0.25), (16.0, PIN_Y0 + 0.5), (0, PIN_Y0 + 0.5)]
    return mk.build(
        "gear_B_pinion", C['move'], M['gear'], origin=(0, 0, zp),
        add=[lambda bm: mk.fv_prism(bm, gear_xz(GM, Z_COL, PA_COL, ph_b, zp), COL_Y0, COL_Y1)],
        union_parts=[lambda bm: mk.fv_lathe(bm, hub, 48, 0, zp),
                     lambda bm: mk.fv_prism(bm, gear_xz(GM, Z_PIN, PA_CROWN, ph_p, zp), PIN_Y0, PIN_Y1),
                     lambda bm: mk.fv_cyl(bm, 12.0, PIN_Y1 - 0.5, YR - 0.4, 0, zp, 48)],
        cut=[lambda bm: mk.fv_cyl(bm, (AXLE_D + CLR_FREE) / 2, COL_Y0 - 1, YR + 1, 0, zp, 32)])


def make_axle(C, M):
    """Pinion axle: pressed into the rear wall, carried at the front by the deck bracket."""
    zp = Z_PIN_AX
    return mk.build("pinion_axle", C['fixed'], M['gear'],
                    add=[lambda bm: mk.fv_cyl(bm, AXLE_D / 2, BRACKET_Y[0], YRO, 0, zp, 32)],
                    union_parts=[lambda bm: mk.fv_cyl(bm, 8.0, YRO - 0.01, YRO + 2.5, 0, zp, 32)])


def make_deck_bracket(C, M):
    """Front support of the pinion axle (no more 30 mm cantilever); two M3x12 from below into the deck."""
    y0, y1 = BRACKET_Y
    zt = Z_DECK_PLATE_TOP - DECK_PLATE_T - 0.05
    sy = BRACKET_SCREWS[0][1]
    return mk.build("deck_bracket", C['fixed'], M['body'],
                    add=[lambda bm: mk.box(bm, -12.0, 12.0, y0, y1, Z_PIN_AX - 8.5, zt)],
                    union_parts=[lambda bm: mk.box(bm, -12.0, 12.0, sy - 5.0, y1 - 0.5, zt - 4.0, zt)],
                    cut=[lambda bm: mk.fv_cyl(bm, (AXLE_D + CLR_SLIDE) / 2, y0 - 1, y1 + 1, 0, Z_PIN_AX, 32)]
                    + [lambda bm, s=s: mk.cyl(bm, M3_CLR / 2, zt - 5.0, zt + 1.0, 16, s[0], s[1])
                       for s in BRACKET_SCREWS])
