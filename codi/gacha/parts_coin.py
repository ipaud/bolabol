"""v3 hidden coin mech (build.main(mech="v3")): coin wheel behind the front wall, housing with the
blocking pawl, flush coin plate with the slot, crank ("knob", it is the part the hand turns), and
the coin duct inside the base box.

Coin path: slot in the plate + front wall (12 deg ramp floor, the coin rolls in) -> wheel pocket at
12 o'clock, on its rear stop -> carried clockwise under the housing ring, past the blocking pawl
at DOG_ANGLE -> exit window at 6 o'clock -> funnel -> duct -> drawer. The coin is never visible.
"""
from math import radians, degrees, tan, hypot, cos, sin, atan2
import bmesh
from mathutils import Matrix
import mk
from parts_drive import hex_bore, ratchet_pts, slit_cutter, stadium, _sector
from params import *

ZH = Z_HANDLE
SLOT_W = SLIT_W + 1.0               # slot in the plate / front wall (was +0.4: the coin could only tilt 2 deg in it)
SLOT_RAMP = 12.0                    # deg, slot floor falls towards the wheel
SLOT_TOP = W_R + 3.5                # coin top on the ramp + 0.9
EXIT = (115.0, 200.0)               # exit window (front-view deg): the coin leaves on the way down (right side)
FUNNEL_Z = 92.0                     # funnel outlet = duct top (clear of the capsule chute roof, 100.6 at x < -15.5)
DUCT_X, DUCT_T, DUCT_Z0 = (-5.5, 22.5), 1.6, 34.0   # duct inner x, wall, bottom (a coin standing on edge in the drawer: top 31):
                                                    # 27 wide, a tilted coin falls through; right of the chute
DUCT_REAR_Z0 = 40.0                 # rear wall bottom: a coin rolling back on edge down the drawer ramp passes
                                    # under it (28 mm square to the ramp; from 34 it had 23.2 and wedged ~6%)
PLATE_HW, PLATE_HH, PLATE_R, PLATE_CH = 52.0, 50.0, 12.0, 1.2
LUGS = ((-20.0, ZH + 37.5), (20.0, ZH + 37.5), (-46.0, ZH - 38.0), (46.0, ZH - 38.0))   # plate screws, clear of the funnel
LUG_D = 11.0                        # lug depth behind the wall: M3x16 countersunk, 9.8 mm of thread
H_REAR = W_Y_STOP + 1.6             # housing rear face (the saw-tooth band runs behind it)


# --------------------------------------------------------------------------- helpers

def slot_floor(y):
    """Slot floor above the axis: 12 deg ramp ending 0.3 over the pocket floor at the wheel face."""
    return slit_floor(W_Y0) + 0.3 + (W_Y0 - y) * tan(radians(SLOT_RAMP))


def slot_cutter(y0, y1, x=0.0):
    prof = [(y0, ZH + slot_floor(y0)), (y1, ZH + slot_floor(y1)), (y1, ZH + SLOT_TOP), (y0, ZH + SLOT_TOP)]
    return lambda bm: mk.yz_prism(bm, prof, x - SLOT_W / 2, x + SLOT_W / 2)


def loft_fv(bm, rings):
    """Front-view outlines [(pts_xz, y), ...] with equal point counts, bridged into one solid."""
    vs = [[bm.verts.new((x, y, z)) for x, z in pts] for pts, y in rings]
    n = len(vs[0])
    faces = [bm.faces.new(vs[0]), bm.faces.new(vs[-1][::-1])]
    for a, b in zip(vs, vs[1:]):
        faces += [bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i])) for i in range(n)]
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    return [v for ring in vs for v in ring]


def rrect(hw, hh, r, cx=0.0, cz=ZH, seg=10):
    pts = []
    for ox, oz, a0 in ((hw - r, hh - r, 0.0), (r - hw, hh - r, 90.0), (r - hw, r - hh, 180.0), (hw - r, r - hh, 270.0)):
        pts += [(cx + ox + r * cos(radians(a0 + 90.0 * i / seg)), cz + oz + r * sin(radians(a0 + 90.0 * i / seg)))
                for i in range(seg + 1)]
    return pts


def vstadium(w, h, cx, cz):
    return [(cx + z, cz + x) for x, z in stadium(h, w, 0.0, 0.0)]


def rect(x0, x1, z0, z1):
    return [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]


def web(p, width, r_in):
    """Front-view strip from point p towards the handle axis, ending at radius r_in."""
    dx, dz = -p[0], ZH - p[1]
    d = hypot(dx, dz)
    ux, uz, h = dx / d, dz / d, width / 2
    e = (p[0] + ux * (d - r_in), p[1] + uz * (d - r_in))
    return [(p[0] - uz * h, p[1] + ux * h), (e[0] - uz * h, e[1] + ux * h),
            (e[0] + uz * h, e[1] - ux * h), (p[0] + uz * h, p[1] - ux * h)]


def grow(pts, d):
    """Convex polygon grown by d (edges offset outwards, neighbours intersected)."""
    pts = mk._ccw(pts)
    n = len(pts)
    lines = []
    for i in range(n):
        (x0, z0), (x1, z1) = pts[i], pts[(i + 1) % n]
        ex, ez = x1 - x0, z1 - z0
        k = d / hypot(ex, ez)
        lines.append(((x0 + ez * k, z0 - ex * k), (ex, ez)))
    out = []
    for i in range(n):
        (p, u), (q, v) = lines[i - 1], lines[i]
        s = ((q[0] - p[0]) * v[1] - (q[1] - p[1]) * v[0]) / (u[0] * v[1] - u[1] * v[0])
        out.append((p[0] + s * u[0], p[1] + s * u[1]))
    return out


RING_R = W_R + 1.5                 # housing ring bore: a 0.5 mm oversize coin still clears it by 1 mm
LIP_R = W_R + 4.0                  # coin retaining lips in the pawl window (the pawl stays above 44 there)


def ramped(r1, a0, a1, a2):
    """Cut in the housing ring from the wheel up to r1 over a0..a1 (front-view deg), closing with a
    ramp back down to the ring at a2: a coin sticking out is cammed back in, never caught on an edge."""
    ring = RING_R
    arc = lambda r, b0, b1: [fv(r, b0 + (b1 - b0) * i / 12) for i in range(13)]
    pts = arc(r1, a0, a1) + [fv(ring, a2)] + arc(W_R - 1.0, a2, a0)
    return [(x, ZH + z) for x, z in pts]


def spun(f, deg):
    """Builder f turned deg clockwise (front view) about the handle axis."""
    def g(bm):
        vs = f(bm)
        bmesh.ops.rotate(bm, verts=vs, cent=(0.0, 0.0, ZH), matrix=Matrix.Rotation(radians(deg), 3, 'Y'))
        return vs
    return g


# funnel under the lower right quadrant: the ring opens from ~115 deg, where the pocket already heads
# down, so the coin is out before 6 o'clock. Dynamic test: past 6 o'clock the pocket climbs left and
# drags a half-dropped coin into the far wall, which pushes it back in (jam). Left wall 68 deg, right
# wall 57 deg, outlet narrower than the duct; nothing below z 100.6 left of x -15.5 (capsule chute).
FUNNEL = [(-14.0, 116.0), (40.0, 134.0), (44.0, 128.0), (DUCT_X[1] - 0.5, 94.0), (DUCT_X[1] - 0.5, FUNNEL_Z - 2.0),
          (DUCT_X[0] + 0.5, FUNNEL_Z - 2.0), (DUCT_X[0] + 0.5, 94.0)]


# --------------------------------------------------------------------------- parts

def make_coin_wheel(C, M):
    """Coin carrier on the hex shaft. Pocket at 12 o'clock (floor 2 deg down to the rear stop, side
    lead-in at the face), saw-tooth band at the back for the anti-reverse pawl, front boss = front
    bearing through the wall and the plate. Printed back face down, no supports."""
    # lead-in: the coin only entered with the wheel < 1-1.5 deg off home (0.3 mm a side); stays clear of the pawl
    y_mouth = W_Y0 + 6.0
    mouths = [[(rect(x - SLIT_W / 2 - 2.0, x + SLIT_W / 2 + 2.0, ZH + slit_floor(W_Y0 - 0.5), ZH + W_R + 2), W_Y0 - 0.5),
               (rect(x - SLIT_W / 2, x + SLIT_W / 2, ZH + slit_floor(y_mouth), ZH + W_R + 2), y_mouth)] for x in pocket_xs()]
    ob = mk.build("coin_wheel", C['move'], M['gear'], origin=(0, 0, ZH),
                  add=[lambda bm: mk.fv_cyl(bm, W_R, W_Y0, W_RAT_Y0, 0, ZH, 128)],
                  union_parts=[lambda bm: mk.fv_prism(bm, ratchet_pts(), W_RAT_Y0 - 0.5, W_Y1),
                               lambda bm: mk.fv_cyl(bm, SLEEVE_D / 2, CRANK_Y0, W_Y0 + 0.5, 0, ZH, 64)],
                  cut=[hex_bore(CRANK_Y0 - 1, W_Y1 + 1)]
                  + [slit_cutter(W_Y0 - 1, W_Y_STOP, W_R + 2, x) for x in pocket_xs()]
                  + [lambda bm, m=m: loft_fv(bm, m) for m in mouths])
    mk.smooth(ob, 30)
    return ob


WING_C, WING_R, WING_H, WING_F = 28.0, 15.0, 11.5, 8.0   # lobe centre x, lobe r, waist half height, fillet r


def wing(inset=0.0, seg=12):
    """Butterfly crank outline (front view, around the axis): two round lobes, a waist and concave
    fillets. `inset` shrinks it evenly with a fixed point count (chamfer loft)."""
    r, h, f, c = WING_R - inset, WING_H - inset, WING_F + inset, WING_C
    xf = c - ((r + f) ** 2 - (h + f) ** 2) ** 0.5              # fillet / waist tangent point
    phi = degrees(atan2(h + f, xf - c))                        # lobe centre -> fillet centre
    arc = lambda cx, cz, rr, a0, a1: [(cx + rr * cos(radians(a0 + (a1 - a0) * i / seg)),
                                       cz + rr * sin(radians(a0 + (a1 - a0) * i / seg))) for i in range(seg + 1)]
    top = arc(c, 0.0, r, 0.0, phi) + arc(xf, h + f, f, phi - 180.0, -90.0) \
        + arc(-xf, h + f, f, -90.0, -phi) + arc(-c, 0.0, r, 180.0 - phi, 180.0)
    pts = top + [(x, -z) for x, z in reversed(top[1:-1])]
    return [(x, ZH + z) for x, z in pts]


def make_crank(C, M):
    """Butterfly crank on the shaft end, M3x16 into the shaft through the hub cap. Flat back 1 mm
    off the plate; printed back face down (chamfers and cap on top)."""
    y0, y1, c = CRANK_Y0, CRANK_Y1, 1.5
    cap = [(0, y1 + 1.0), (9.5, y1 + 1.0), (9.5, y1 - 1.5), (8.5, y1 - 2.5), (0, y1 - 2.5)]
    ob = mk.build("knob", C['move'], M['accent'], origin=(0, 0, ZH),
                  add=[lambda bm: loft_fv(bm, [(wing(), y0), (wing(), y1 + c), (wing(c), y1)])],
                  union_parts=[lambda bm: mk.fv_lathe(bm, cap, 64, 0, ZH)],
                  cut=[hex_bore(Y_SHAFT0, y0 + 1),
                       lambda bm: mk.fv_cyl(bm, M3_CLR / 2, y1 - 3.5, Y_SHAFT0 + 0.5, 0, ZH, 16),
                       lambda bm: mk.fv_cyl(bm, 3.0, y1 - 3.5, y1 + 0.7, 0, ZH, 24)])   # M3 head 5.5
    mk.smooth(ob, 30)
    return ob


def make_coin_housing(C, M):
    """Fixed shroud around the coin wheel, screwed to the inside of the front wall through the
    plate. Keeps the coin in its pocket from 12 to 6 o'clock, carries the blocking pawl (window,
    pivot, spring hump at DOG_ANGLE) and the anti-reverse pawl boss, opens at 6 o'clock into the
    funnel. Printed front face down; supports only in the pawl window."""
    da = DOG_ANGLE
    dx, dz = spin(*dog_pivot(), da)
    _, _, _, rp = ratchet_pawl_geom()
    ys = 0.5 * (DOG_Y0 + DOG_Y1)
    rs = SPRING_D / 2
    tear = [(SPRING_X + rs * cos(radians(a)), ys + rs * sin(radians(a))) for a in range(150, 391, 15)] + [(SPRING_X, ys + 2.0 * rs)]
    unions = [
        lambda bm: mk.fv_prism(bm, _sector(BEZEL_R0, BEZEL_R1, da - 14.0, da + 42.0), YF, H_REAR),
        lambda bm: mk.fv_prism(bm, _sector(BEZEL_R1 - 0.5, BEZEL_R1 + 7.0, da - 2.0, da + 10.0), YF, H_REAR),
        lambda bm: mk.fv_prism(bm, grow(FUNNEL, 2.0), YF, H_REAR),
        lambda bm: mk.fv_cyl(bm, 5.5, YF, RAT_Y0 - 0.5, rp[0], rp[1], 32),
        lambda bm: mk.fv_cyl(bm, 4.0, YF, DOG_Y0 - 1.0, dx, dz, 32),          # pawl pivot bosses: the pivot
        lambda bm: mk.fv_cyl(bm, 4.5, DOG_Y1 + 1.0, H_REAR, dx, dz, 32),      # sits 3 mm from the pod edge
        lambda bm: mk.fv_prism(bm, web(rp, 8.0, W_R + 2.0), YF, RAT_Y0 - 0.5),
        lambda bm: mk.fv_cyl(bm, RAT_SLEEVE_R, RAT_Y0 - 1.0, RAT_Y1 + 0.2, rp[0], rp[1], 32),   # pawl sleeve
    ]
    for p in LUGS:
        unions += [lambda bm, p=p: mk.fv_cyl(bm, 4.5, YF, YF + LUG_D, p[0], p[1], 32),
                   lambda bm, p=p: mk.fv_prism(bm, web(p, 7.0, W_R + 2.0), YF, YF + LUG_D)]
    cuts = [
        lambda bm: mk.fv_cyl(bm, RING_R, YF - 1, H_REAR + 1, 0, ZH, 128),                           # wheel
        lambda bm: mk.fv_prism(bm, _sector(W_R + 0.5, W_R + 8.0, EXIT[0], EXIT[1]), YF - 1, W_Y_STOP + 0.2),
        lambda bm: mk.fv_prism(bm, FUNNEL, YF - 1, W_Y_STOP + 0.2),
        # pawl window: open above LIP_R over the whole pawl, below it only where nose, lever and foot reach
        # (-5..+20 deg); the lip before it keeps a coin thrown out by the spin (0.4 g at 0.5 s/turn) in
        # its pocket; past the pawl a long ramp (16 deg, to the window end) cams a coin the spin threw out
        # back in (dynamic test: a 48 deg ramp jammed the coin at 0.25 s/turn)
        lambda bm: mk.fv_prism(bm, _sector(LIP_R, BEZEL_R1 + 1, da - 14.0, da + 42.0), DOG_Y0 - 1.0, DOG_Y1 + 1.0),
        lambda bm: mk.fv_prism(bm, ramped(LIP_R + 0.5, da - 5.0, da + 20.0, da + 42.0), DOG_Y0 - 1.0, DOG_Y1 + 1.0),
        lambda bm: mk.fv_cyl(bm, 1.4, YF + 0.6, DOG_Y0, dx, dz, 16),                  # pawl pivot, M3x25 self-tap
        lambda bm: mk.fv_cyl(bm, M3_CLR / 2, DOG_Y1, H_REAR + 1, dx, dz, 16),         # from behind,
        lambda bm: mk.fv_cyl(bm, 3.1, H_REAR - 3.0, H_REAR + 1, dx, dz, 24),          # head sunk 3 mm: 6 mm of thread
        spun(lambda bm: mk.prism(bm, tear, ZH + BEZEL_R0, ZH + BEZEL_R1 + 7.0 - 2.5), da),   # pen spring
        lambda bm: mk.fv_cyl(bm, 1.4, RAT_Y0 - 12.0, RAT_Y0 - 0.5, rp[0], rp[1], 16),  # anti-reverse pawl screw:
        lambda bm: mk.fv_cyl(bm, M3_CLR / 2, RAT_Y0 - 0.5, RAT_Y1 + 1.0, rp[0], rp[1], 16),  # passes the sleeve
    ] + [lambda bm, p=p: mk.fv_cyl(bm, 1.4, YF - 1, YF + LUG_D + 1, p[0], p[1], 16) for p in LUGS]
    clip = lambda bm: mk.box(bm, -XI + 0.5, XI - 0.5, YF, max(H_REAR + 5.0, RAT_Y1 + 1.0), FUNNEL_Z, V3_TOP)
    ob = mk.build("coin_housing", C['fixed'], M['body'], add=[lambda bm: mk.fv_cyl(bm, W_R + 6.0, YF, H_REAR, 0, ZH, 128)],
                  union_parts=unions, cut=cuts, inter=[clip])
    mk.smooth(ob, 30)
    return ob


def make_coin_plate(C, M):
    """Flush coin plate on the front wall: slot with a finger scoop, bearing hole for the wheel boss,
    four M3x16 countersunk screws through the wall into the housing lugs. Printed back face down."""
    back = rrect(PLATE_HW, PLATE_HH, PLATE_R)
    front = rrect(PLATE_HW - PLATE_CH, PLATE_HH - PLATE_CH, PLATE_R - PLATE_CH)
    y_in = PLATE_Y + 2.0
    zs0, zs1 = ZH + slot_floor(y_in) - 0.3, ZH + SLOT_TOP + 0.3
    span = max(pocket_xs()) - min(pocket_xs())      # 2 coins: one scoop over both slots
    scoop = [(vstadium(14.0 + span, 33.0, 0.0, ZH + 28.5), PLATE_Y - 0.5),
             (vstadium(SLOT_W + 0.6 + span, zs1 - zs0, 0.0, 0.5 * (zs0 + zs1)), y_in)]
    sink = [(0, PLATE_Y - 1.0), (3.2, PLATE_Y - 1.0), (3.2, PLATE_Y), (M3_CLR / 2, PLATE_Y + 3.2 - M3_CLR / 2),
            (0, PLATE_Y + 3.2 - M3_CLR / 2)]
    cuts = [slot_cutter(PLATE_Y - 1, YFO + 1, x) for x in pocket_xs()] + [lambda bm: loft_fv(bm, scoop),
            lambda bm: mk.fv_cyl(bm, (SLEEVE_D + CLR_FREE) / 2, PLATE_Y - 1, YFO + 1, 0, ZH, 64)]
    for p in LUGS:
        cuts += [lambda bm, p=p: mk.fv_cyl(bm, M3_CLR / 2, PLATE_Y - 1, YFO + 1, p[0], p[1], 16),
                 lambda bm, p=p: mk.fv_lathe(bm, sink, 24, p[0], p[1])]
    ob = mk.build("coin_plate", C['fixed'], M['frame'],
                  add=[lambda bm: loft_fv(bm, [(front, PLATE_Y), (back, PLATE_Y + PLATE_CH), (back, YFO)])], cut=cuts)
    mk.smooth(ob, 30)
    return ob


def wall_cuts():
    """Front-wall holes (mech box and base box share them): coin slot, plate / housing screws."""
    return [slot_cutter(YFO - 1, YF + 0.3, x) for x in pocket_xs()] + \
        [lambda bm, p=p: mk.fv_cyl(bm, M3_CLR / 2, YFO - 1, YF + 1, p[0], p[1], 16) for p in LUGS]


def duct_parts():
    """Coin duct on the inside of the base box front wall, funnel outlet -> drawer: 28 wide and
    28.5-31 deep, more than a coin across in any pose (the dynamic test wedged a 25.5 coin lying flat
    in a 25.5 deep duct). A slope over its whole height moves the coin 2.5 mm back so it lands clear
    of the drawer front wall."""
    (x0, x1), t, y1 = DUCT_X, DUCT_T, W_Y_STOP + 3.9
    return [lambda bm: mk.box(bm, x0 - t, x0, YF - 0.5, y1 + t, DUCT_Z0, FUNNEL_Z),
            lambda bm: mk.box(bm, x1, x1 + t, YF - 0.5, y1 + t, DUCT_Z0, FUNNEL_Z),
            lambda bm: mk.box(bm, x0 - t, x1 + t, y1, y1 + t, DUCT_REAR_Z0, FUNNEL_Z),
            lambda bm: mk.yz_prism(bm, [(YF - 0.5, DUCT_Z0), (YF + 2.5, DUCT_Z0), (YF, FUNNEL_Z), (YF - 0.5, FUNNEL_Z)],
                                   x0 - 0.1, x1 + 0.1)]

