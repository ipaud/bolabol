"""Rotor (5 pockets + crown gear), hub cone, deck, funnel insert, exit hood."""
from math import pi, sin, cos, tan, radians, atan2
import mk
from gears import crown_section
from params import *

SEG = 160


def _pocket_xy(k):
    a = radians(pocket_angle(k, 0.0))
    return R_POCKET * cos(a), R_POCKET * sin(a)


def crown_teeth(bm, n_r=9, a_range=None):
    """Face-gear teeth hanging under the rotor, generated per radius from the pinion geometry.
    a_range=(deg0, deg1) keeps only the teeth centred inside that angle window (test sector)."""
    rs = [CROWN_R_IN + (CROWN_R_OUT - CROWN_R_IN) * i / (n_r - 1) for i in range(n_r)]
    z_top = Z_ROT_BOT + 0.6                     # overlap into the rotor body for the union
    for k in range(Z_CROWN):
        th = pi / 2 + 2 * pi * k / Z_CROWN      # tooth 0 centred on +Y (pinion space at its top)
        if a_range and not (radians(a_range[0]) <= (th % (2 * pi)) <= radians(a_range[1])):
            continue
        secs = []
        for r in rs:
            ht, hr, zt, al = crown_section(r, GM, Z_CROWN, Z_PIN, PA_CROWN, Z_PIN_AX, Z_ROT_BOT, GEAR_BACKLASH)
            hr2 = min(hr + 0.6 * tan(al), pi * r / Z_CROWN - 0.02)
            quad = [(-ht, zt), (ht, zt), (hr2, z_top), (-hr2, z_top)]
            secs.append([bm.verts.new((r * cos(th + u / r), r * sin(th + u / r), z)) for u, z in quad])
        for a, b in zip(secs, secs[1:]):
            for i in range(4):
                j = (i + 1) % 4
                bm.faces.new((a[i], a[j], b[j], b[i]))
        bm.faces.new(list(reversed(secs[0])))
        bm.faces.new(secs[-1])


def _tab_angles():
    return [pocket_angle(k, 0.0) + 180.0 / N_POCKETS for k in range(N_POCKETS)]


def _tabs(bm, r0, r1, z0, z1, w):
    for a in _tab_angles():
        c, s = cos(radians(a)), sin(radians(a))
        pts = [(r0, -w / 2), (r1, -w / 2), (r1, w / 2), (r0, w / 2)]
        mk.prism(bm, [(x * c - y * s, x * s + y * c) for x, y in pts], z0, z1)


def make_rotor(C, M):
    """Pocket wheel: 5 pockets with 35 deg countersinks (the whole top funnels capsules into
    pockets), integral hub cone, underside recess + notches for the crown ring."""
    pockets = [_pocket_xy(k) for k in range(N_POCKETS)]
    rb = (PIVOT_D + CLR_FREE) / 2
    k = tan(radians(CS_SLOPE))
    r_top = POCKET_D / 2 + CS_DEPTH / k
    cone = [(0, Z_ROT_TOP - 1.0), (HUB_CONE_R0, Z_ROT_TOP - 1.0), (HUB_CONE_R0, Z_ROT_TOP),
            (HUB_CONE_R1, Z_ROT_TOP + HUB_CONE_H), (0, Z_ROT_TOP + HUB_CONE_H + 1.0)]
    cuts = []
    for (x, y) in pockets:
        cuts.append(lambda bm, x=x, y=y: mk.cyl(bm, POCKET_D / 2, Z_ROT_BOT - 1, Z_ROT_TOP + 1, 96, x, y))
        cuts.append(lambda bm, x=x, y=y: mk.frustum(bm, POCKET_D / 2, r_top + 3.0 / k, Z_ROT_TOP - CS_DEPTH,
                                                    Z_ROT_TOP + 3.0, 96, x, y))
    cuts.append(lambda bm: mk.cyl(bm, rb, Z_ROT_BOT - 1, Z_ROT_TOP - 4.0, 48))
    # crown ring recess: press fit on the bore, ceiling flush with the ring top (it hangs there, at its design height)
    ring = [(RING_R0 + RING_PRESS, Z_ROT_BOT - 1.0), (ROT_R + 1.0, Z_ROT_BOT - 1.0),
            (ROT_R + 1.0, Z_ROT_BOT + RING_T), (RING_R0 + RING_PRESS, Z_ROT_BOT + RING_T)]
    cuts.append(lambda bm: mk.lathe(bm, ring, SEG))
    cuts.append(lambda bm: _tabs(bm, RING_R0 - 3.4, RING_R0 + 0.5, Z_ROT_BOT - 1.0,
                                 Z_ROT_BOT + RING_T, 6.4))                            # tab notches
    rot = mk.build("rotor", C['move'], M['rotor'], origin=(0, 0, Z_ROT_BOT),
                   add=[lambda bm: mk.cyl(bm, ROT_R, Z_ROT_BOT, Z_ROT_TOP, SEG)],
                   union_parts=[lambda bm: mk.lathe(bm, cone, 48)], cut=cuts)
    mk.smooth(rot, 30)
    return rot


def make_crown_ring(C, M):
    """Face gear ring (95 teeth), printed teeth-up, pressed into the rotor recess; 5 tabs key it."""
    flange = [(RING_R0, Z_ROT_BOT), (ROT_R, Z_ROT_BOT), (ROT_R, Z_ROT_BOT + RING_T), (RING_R0, Z_ROT_BOT + RING_T)]
    ob = mk.build("crown_ring", C['move'], M['gear'], origin=(0, 0, Z_ROT_BOT),
                  add=[lambda bm: mk.lathe(bm, flange, SEG)],
                  union_parts=[crown_teeth, lambda bm: _tabs(bm, RING_R0 - 3.2, RING_R0 + 0.3, Z_ROT_BOT,
                                                             Z_ROT_BOT + RING_T, 6.0)])
    return ob


def make_deck(C, M):
    z1 = Z_DECK_PLATE_TOP
    z0 = z1 - DECK_PLATE_T
    ex, ey = exit_xy()
    col_r = GM * (Z_COL / 2 + 1) + 1.5

    def plate(bm):
        mk.box(bm, -XI + 0.3, XI - 0.3, YF + 0.3, YR - 0.3, z0, z1)

    unions = [
        lambda bm: mk.cyl(bm, DECK_DISK_R, z1 - 1.0, Z_DECK, SEG),
        lambda bm: mk.cyl(bm, 16.0, Z_DECK - 1.0, Z_ROT_BOT - SHIM_NOM, 64),         # thrust boss (+ shim)
        lambda bm: mk.cyl(bm, PIVOT_D / 2, Z_DECK, Z_ROT_TOP - 5.0, 48),            # pivot post
        # anti-tilt rail under the crown ring flange, outside the teeth: the rotor rides on the r16 boss and
        # the separating force / an off-centre load tilts it on the post clearance; the rail catches it
        lambda bm: mk.lathe(bm, [(CROWN_R_OUT + 0.8, z1 - 0.5), (ROT_R - 0.3, z1 - 0.5),
                                 (ROT_R - 0.3, Z_ROT_BOT - RAIL_GAP), (CROWN_R_OUT + 0.8, Z_ROT_BOT - RAIL_GAP)], SEG),
    ]
    cuts = [
        lambda bm: mk.box(bm, -26, 26, PIN_Y0 + 5.0, YR + 1, z1 + 0.01, Z_DECK + 1),        # rail gap over the pinion
        lambda bm: mk.cyl(bm, EXIT_HOLE_D / 2, z0 - 1, Z_DECK + 1, 96, ex, ey),
        lambda bm: mk.box(bm, -col_r, col_r, COL_Y0 - 1.5, PIN_Y0 - 1.25, z0 - 1, Z_DECK + 1),   # gear B window
        lambda bm: mk.box(bm, -24, 24, PIN_Y0 - 1.25, YR, z0 - 1, z1 + 1),                        # pinion window
    ] + [lambda bm, s=s: mk.cyl(bm, 1.4, z0 - 1, z0 + 9.0, 16, s[0], s[1]) for s in BRACKET_SCREWS]   # M3x12 + 1 mm
    from parts_body import rounded
    inter = []
    if rounded():
        import parts_shell as S
        inter = [lambda bm: S.plate(bm, WALL + 0.3, z0 - 1.0, Z_ROT_TOP)]      # corners follow the box
    ob = mk.build("deck", C['fixed'], M['body'], add=[plate], union_parts=unions, cut=cuts, inter=inter)
    return ob


def make_shims(C, M):
    """Rotor height shims (crown/pinion mesh tuning). The 0.4 mm one is fitted; spares lie beside."""
    ri, ro = (PIVOT_D + CLR_FREE) / 2 + 0.1, 15.0
    out = [mk.build("shim_04", C['move'], M['gear'], origin=(0, 0, Z_ROT_BOT),
                    add=[lambda bm: mk.lathe(bm, [(ri, Z_ROT_BOT - SHIM_NOM), (ro, Z_ROT_BOT - SHIM_NOM),
                                                  (ro, Z_ROT_BOT - 0.01), (ri, Z_ROT_BOT - 0.01)], 64)])]
    for i, t in enumerate((0.2, 0.6)):
        x = XO + 40.0 + 35.0 * i
        out.append(mk.build("spare_shim_%02d" % int(t * 10), C['caps'], M['gear'],
                            add=[lambda bm, x=x, t=t: mk.lathe(bm, [(ri, 0), (ro, 0), (ro, t), (ri, t)], 64, x, 60.0)]))
    return out


def make_funnel(C, M):
    ztop = Z_FUNNEL_LIP + (150.0 - FUNNEL_R) * tan(radians(FUNNEL_SLOPE)) + 1.0
    rtop = FUNNEL_R + (ztop + 2 - Z_FUNNEL_LIP) / tan(radians(FUNNEL_SLOPE))
    from parts_body import rounded
    if rounded():
        return _funnel_mochi(C, M, ztop, rtop)

    def core(bm):
        mk.box(bm, -XI + 0.2, XI - 0.2, YF + 0.2, YR - 0.2, Z_BODY_TOP, ztop)

    def rim(bm):                                   # half the wall thickness: part fits the bed flat
        mk.box(bm, -XI - 1.6, XI + 1.6, YF - 1.6, YR + 1.6, Z_BODY_TOP, Z_RIM)

    from parts_body import post_boxes, post_pins, funnel_screw_xy
    wells = []
    for (x, y) in funnel_screw_xy():                    # M3x12 into the mech box corner blocks
        wells.append(lambda bm, x=x, y=y: mk.cyl(bm, M3_CLR / 2, Z_BODY_TOP - 1, Z_BODY_TOP + 4.0, 16, x, y))
        wells.append(lambda bm, x=x, y=y: mk.cyl(bm, 3.3, Z_BODY_TOP + 3.0, ztop + 5, 24, x, y))
    cuts = wells + [
        lambda bm: mk.frustum(bm, FUNNEL_R, rtop, Z_FUNNEL_LIP, ztop + 2, SEG),
        lambda bm: mk.cyl(bm, FUNNEL_R, Z_BODY_TOP - 1, Z_FUNNEL_LIP + 0.01, SEG),
    ] + [lambda bm, b=b: mk.box(bm, b[0] - 0.3, b[1] + 0.3, b[2] - 0.3, b[3] + 0.3, Z_RIM, ztop + 5)
         for b in post_boxes()] + [lambda bm, p=p: mk.cyl(bm, 2.2, Z_RIM - 4.5, Z_RIM + 1, 24, p[0], p[1])
                                   for p in post_pins()]
    cuts += [lambda bm, p=p: mk.cyl(bm, 1.4, Z_BODY_TOP + 1.0, ztop + 5, 16, p[0], p[1]) for p in hood_screws()]
    return mk.build("funnel", C['fixed'], M['body'], add=[core], union_parts=[rim], cut=cuts)


def _funnel_mochi(C, M, ztop, rtop):
    """Cream rim band (visible, holds the window groove) + the same sloped core, rounded plan."""
    import bmesh
    import parts_shell as S
    from parts_body import funnel_screw_xy
    D = S.WIN_IN + S.WIN_T2 + 0.2 + 1.5          # band inner inset: groove inner wall 1.5 mm
    core = mk.build("_funnel_core", C['fixed'], None,
                    add=[lambda bm: S.plate(bm, D - 0.5, Z_BODY_TOP, ztop)],
                    cut=[lambda bm: mk.frustum(bm, FUNNEL_R, rtop, Z_FUNNEL_LIP, ztop + 2, SEG),
                         lambda bm: mk.cyl(bm, FUNNEL_R, Z_BODY_TOP - 1, Z_FUNNEL_LIP + 0.01, SEG)])
    ob = mk.build("funnel", C['fixed'], M['frame'], add=[lambda bm: S.ring(bm, 0.0, D, Z_BODY_TOP, S.M2_RIM)])
    mk.boolean(ob, [core], 'UNION')
    cuts = [lambda bm: mk.cyl(bm, FUNNEL_R, Z_BODY_TOP - 1, Z_RIM, SEG),     # band stays 2 mm over the rotor rim
            lambda bm: S.groove(bm, S.M2_RIM - S.GROOVE, S.M2_RIM + 1.0)]
    for (x, y) in funnel_screw_xy():                                          # M3x12 into the mech box corners
        cuts.append(lambda bm, x=x, y=y: mk.cyl(bm, M3_CLR / 2, Z_BODY_TOP - 1, Z_BODY_TOP + 4.0, 16, x, y))
        cuts.append(lambda bm, x=x, y=y: mk.cyl(bm, 3.3, Z_BODY_TOP + 3.0, ztop + 5, 24, x, y))
    for p in hood_screws():                                                   # hood screws (self-tap)
        cuts.append(lambda bm, p=p: mk.cyl(bm, 1.4, Z_BODY_TOP + 1.0, ztop + 5, 16, p[0], p[1]))
    for sx, sy in S.CORNERS:                                                  # pillars stand on the band
        p = S.pillar_point(sx, sy)
        cuts.append(lambda bm, sx=sx, sy=sy: mk.prism(bm, S.pillar_poly(sx, sy, grow=0.3), S.M2_RIM, ztop + 5))
        cuts.append(lambda bm, p=p: mk.cyl(bm, S.PEG_R + 0.2, S.M2_RIM - 4.5, S.M2_RIM + 1.0, 24, p[0], p[1]))
    tmp = []
    for f in cuts:
        b = bmesh.new()
        f(b)
        tmp.append(mk.tmp(b))
    mk.boolean(ob, tmp, 'DIFFERENCE')
    b = bmesh.new()
    S.skin_between(Z_BODY_TOP, ztop + 10.0, bottom=1.0)(b)
    mk.boolean(ob, [mk.tmp(b)], 'INTERSECT')
    return ob


def _hood_poly(r_in=24.0, a0=EXIT_ANGLE - 38.0, a1=EXIT_ANGLE + 38.0, inset=0.6):
    """Sector r >= r_in between angles a0..a1 clipped to the interior rectangle (back-left corner)."""
    xl, yr = -XI + inset, YR - inset
    pts = [(r_in * cos(radians(a)), r_in * sin(radians(a))) for a in
           [a0 + (a1 - a0) * i / 16 for i in range(17)]]
    t1 = radians(a1)                     # ray at a1 hits the left wall
    pts.append((xl, xl * tan(t1)))
    pts.append((xl, yr))                 # back-left corner
    t0 = radians(a0)                     # ray at a0 hits the rear wall
    pts.append((yr / tan(t0), yr))
    return pts


HOOD_Z = Z_ROT_TOP + CAP_H - ROT_T + 3.0          # 3 mm over an upright pocketed capsule
HOOD_T = 5.0


def hood_screws():
    """Two M3x30 from the hood roof down into the funnel slope (the hood used to just sit on the 35 deg slope
    and could slide onto the rotor). On the curtain, over the funnel (r > FUNNEL_R), clear of the pocket path."""
    from parts_body import rounded
    inset = 7.2 if rounded() else 0.6
    return ((-XI + inset + 5.0, 78.0), (-68.0, YR - inset - 5.0))


def make_hood(C, M):
    """Roof over the parked exit pocket: only the pocketed capsule can reach the drop hole.
    A curtain along the case walls carries it down onto the funnel slope."""
    import bmesh
    from mathutils import Matrix
    from parts_body import rounded
    inset = 7.2 if rounded() else 0.6            # v2: curtain corner inside the rounded frame (r 9.7)
    z0, a0, a1 = HOOD_Z, radians(EXIT_ANGLE - 38.0), radians(EXIT_ANGLE + 38.0)
    xl, yr = -XI + inset, YR - inset
    k = tan(radians(FUNNEL_SLOPE))

    def plate(bm):
        mk.prism(bm, _hood_poly(inset=inset), z0, z0 + HOOD_T)

    def curtain(bm):
        poly = [(xl, xl * tan(a1)), (xl, yr), (yr / tan(a0), yr),
                (yr / tan(a0), yr - 3.0), (xl + 3.0, yr - 3.0), (xl + 3.0, xl * tan(a1))]
        mk.prism(bm, poly, Z_BODY_TOP, z0 + HOOD_T)

    def lead_edge(bm):                             # rounded leading edge along the a0 ray
        vs = mk.cyl(bm, HOOD_T / 2, 24.0, 140.0, 24)
        R = Matrix.Translation((0, 0, z0 + HOOD_T / 2)) @ Matrix.Rotation(a0, 4, 'Z') \
            @ Matrix.Rotation(pi / 2, 4, 'Y')
        bmesh.ops.transform(bm, matrix=R, verts=vs)

    def interior(bm):
        mk.box(bm, xl, XI, YF, yr, 0, 400)

    def above_funnel(bm):                          # keep only what is above the funnel slope (+0.3 gap)
        zl = Z_FUNNEL_LIP + 0.3
        mk.frustum(bm, FUNNEL_R, FUNNEL_R + 120 / k, zl, zl + 120, SEG)

    from parts_body import post_boxes
    posts = [lambda bm, b=b: mk.box(bm, b[0] - 0.3, b[1] + 0.3, b[2] - 0.3, b[3] + 0.3, Z_BODY_TOP, 400)
             for b in post_boxes()]
    bosses = [lambda bm, p=p: mk.cyl(bm, 3.5, Z_BODY_TOP, z0 + HOOD_T, 24, p[0], p[1]) for p in hood_screws()]
    holes = [f for p in hood_screws() for f in (
        lambda bm, p=p: mk.cyl(bm, M3_CLR / 2, Z_BODY_TOP - 1, z0 + HOOD_T + 1, 16, p[0], p[1]),
        lambda bm, p=p: mk.cyl(bm, 3.2, z0 + HOOD_T - 4.0, z0 + HOOD_T + 1, 24, p[0], p[1]))]   # head sunk 4 mm
    return mk.build("hood", C['fixed'], M['accent'], add=[plate], union_parts=[curtain, lead_edge] + bosses,
                    cut=posts + holes, inter=[interior, above_funnel])
