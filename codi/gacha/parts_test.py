"""Test jigs: print these first to validate the critical fits before the full machine.

Built in the machine frame, so the real parts (gear_A, gear_B_pinion, pinion_axle, shims, knob,
bezel, dog_pawl, ratchet, ratchet_pawl, sleeve_front, token) sit on them at their true positions.

- gear_jig + crown_sector + hex_coupon_gears: whole gear train (hex fit, A-B mesh, axle support,
  pinion/crown mesh on the rotor shim stack). Swap shims to feel the mesh tighten/loosen.
- token_jig + hex_coupon_token: front-wall section with knob, bezel, blocking pawl (+ spring),
  ratchet and anti-reverse pawl: token lock, back-off, one-turn stop, ratchet clicks, by hand.
- v3 coin_jig + hex_coupon_coin (instead of the token jig): front-wall section with the coin plate,
  housing, coin wheel, both pawls and the crank: coin roll-in, lock without coin, pawl catch at speed.
"""
from math import cos, sin, radians
import mk
from parts_rotor import crown_teeth
from parts_drive import hex_pts, _sector
from parts_body import countersink
from params import *

ZH = Z_HANDLE
JIG_Z0 = ZH - 28.0                  # jig base plate top


def make_gear_jig(C, M):
    hole_hex = HEX_AF / 3 ** 0.5 + 0.6          # hex coupon turns in a plain round hole (test only)
    front, rear = BRACKET_Y, (YR, YR + WALL)
    parts = [
        lambda bm: mk.cyl(bm, 16.0, JIG_Z0 - 0.5, Z_ROT_BOT - SHIM_NOM, 64),                 # thrust column
        lambda bm: mk.cyl(bm, PIVOT_D / 2, Z_ROT_BOT - SHIM_NOM - 0.5, Z_ROT_BOT + 4.0, 48),  # pivot
        lambda bm: mk.box(bm, -25.0, 25.0, front[0], front[1], JIG_Z0 - 0.5, Z_PIN_AX + 9.0),
        lambda bm: mk.box(bm, -25.0, 25.0, rear[0], rear[1], JIG_Z0 - 0.5, Z_PIN_AX + 9.0),
    ]
    cuts = [
        lambda bm: mk.fv_cyl(bm, (AXLE_D + 0.1) / 2, front[0] - 1, front[1] + 1, 0, Z_PIN_AX, 32),
        lambda bm: mk.fv_cyl(bm, (AXLE_D - 0.1) / 2, rear[0] - 1, rear[1] + 1, 0, Z_PIN_AX, 32),   # press
        lambda bm: mk.fv_cyl(bm, hole_hex, front[0] - 1, rear[1] + 1, 0, ZH, 48),
    ]
    return mk.build("test_gear_jig", C['tests'], M['body'],
                    add=[lambda bm: mk.box(bm, -30.0, 30.0, -22.0, rear[1], JIG_Z0 - 4.0, JIG_Z0)],
                    union_parts=parts, cut=cuts)


def make_crown_sector(C, M):
    """70 deg slice of rotor underside + crown teeth; sits on the jig's shim stack like the rotor."""
    a0, a1 = 55.0, 125.0
    rb = (PIVOT_D + CLR_FREE) / 2
    pie = [(0.0, 0.0)] + [(ROT_R * cos(radians(a0 + (a1 - a0) * i / 24)), ROT_R * sin(radians(a0 + (a1 - a0) * i / 24)))
                          for i in range(25)]
    return mk.build("test_crown_sector", C['tests'], M['gear'], origin=(0, 0, Z_ROT_BOT),
                    add=[lambda bm: mk.prism(bm, pie, Z_ROT_BOT, Z_ROT_BOT + 5.0)],
                    union_parts=[lambda bm: mk.cyl(bm, 16.0, Z_ROT_BOT, Z_ROT_BOT + 5.0, 48),
                                 lambda bm: crown_teeth(bm, a_range=(a0 + 2.0, a1 - 2.0))],
                    cut=[lambda bm: mk.cyl(bm, rb, Z_ROT_BOT - 1, Z_ROT_BOT + 6, 48)])


def make_hex_coupons(C, M):
    out = []
    coupons = (("test_hex_coupon_gears", BRACKET_Y[0] - 1.0, YR + WALL + 1.0),
               ("test_hex_coupon_coin", Y_SHAFT0, W_Y1 + 6.0) if MECH == "v3" else
               ("test_hex_coupon_token", Y_SHAFT0, RAT_Y1 + 1.5))
    for name, y0, y1 in coupons:
        out.append(mk.build(name, C['tests'], M['gear'], origin=(0, 0, ZH),
                            add=[lambda bm, y0=y0, y1=y1: mk.fv_prism(bm, hex_pts(HEX_AF, 0, ZH), y0, y1)],
                            cut=[lambda bm, y0=y0: mk.fv_cyl(bm, 1.3, y0 - 1, y0 + 16, 0, ZH, 16)]))
    return out


def make_coin_jig(C, M):
    """v3 coin mech on a front-wall section (same holes as the machine: coin slot, wheel boss
    bearing, plate / housing screws), standing on a foot, with a rear bracket carrying the hex
    coupon 1 mm behind the wheel. Mount plate, housing (+ both pawls, spring), wheel, coupon,
    crank: tests coin roll-in, lock without coin, pawl catch at speed, exit at 6 o'clock."""
    import parts_coin as K
    x, z0 = 64.0, ZH - 88.0                 # foot top 27 mm under the funnel: the coin falls clear
    zf, yb = z0 + 4.0, W_Y1 + 1.0
    gusset = [(YF - 0.5, zf - 0.5), (yb, zf - 0.5), (YF - 0.5, zf + 40.0)]
    hole_hex = HEX_AF / 3 ** 0.5 + 0.6      # coupon turns in a plain round hole (test only)
    return mk.build("test_coin_jig", C['tests'], M['body'],
                    add=[lambda bm: mk.box(bm, -x, x, YFO, YF, z0, ZH + 52.0)],
                    union_parts=[lambda bm: mk.box(bm, -x, x, YF - 0.5, yb + 4.0, z0, zf),
                                 lambda bm: mk.box(bm, -15.0, 15.0, yb, yb + 4.0, zf - 0.5, ZH + 14.0)]
                    + [lambda bm, s=s: mk.yz_prism(bm, gusset, s - 2.0, s + 2.0) for s in (2.0 - x, x - 2.0)],
                    cut=K.wall_cuts() + [
                        lambda bm: mk.fv_cyl(bm, (SLEEVE_D + CLR_FREE) / 2, YFO - 1, YF + 1, 0, ZH, 64),
                        lambda bm: mk.fv_cyl(bm, hole_hex, yb - 1, yb + 5, 0, ZH, 48)])


def make_token_jig(C, M):
    """Front-wall section (same holes as the mech box front) standing on an L foot."""
    h = 70.0
    rp = 0.5 * (BEZEL_R0 + BEZEL_R1)
    _, _, _, rP = ratchet_pawl_geom()
    dx, dz = dog_pivot()
    cuts = [
        lambda bm: mk.fv_cyl(bm, (SLEEVE_D + CLR_FREE) / 2, YFO - 1, YF + 1, 0, ZH),
        lambda bm: mk.fv_cyl(bm, M3_CLR / 2, YFO - 1, YF + 1, dx, dz, 16),
        lambda bm: mk.fv_cyl(bm, M3_CLR / 2, YFO - 1, YF + 1, rP[0], rP[1], 16),
        countersink(rP),                    # flat-head pivot screw: the knob passes 1.8 mm over it
    ]
    for a in (90.0, 240.0, 330.0):
        x, z = fv(rp, a)
        cuts.append(lambda bm, x=x, z=z: mk.fv_cyl(bm, M3_CLR / 2, YFO - 1, YF + 1, x, ZH + z, 16))
    return mk.build("test_token_jig", C['tests'], M['body'],
                    add=[lambda bm: mk.box(bm, -h, h, YFO, YF, ZH - h, ZH + h)],
                    union_parts=[lambda bm: mk.box(bm, -h, h, YF - 0.5, YF + 45.0, ZH - h, ZH - h + 4.0)],
                    cut=cuts)
