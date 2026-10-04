"""Capsule path below the deck: drop tube, sloped duct, outlet cup with lip, outlet door.

No one-way flap: at rest the pocket over the drop hole is always empty, so there is nothing to
steal through the outlet, and the physics test showed a gravity-return flap pinning capsules."""
from math import radians, tan, cos, sin
import mk
from parts_body import x_cyl, DOOR_PIN_Y, DOOR_PIN_Z, PIN_WIRE_R
from params import *

T = CHUTE_T
DUCT_H = 66.0 / cos(radians(CHUTE_SLOPE))   # 66 mm clear perpendicular to the floor (vertical value)


def _xs():
    ex, _ = exit_xy()
    h = CHUTE_W / 2
    return ex - h, ex + h, ex - h - T, ex + h + T


def make_chute(C, M):
    """One side profile for drop tube + 30 deg duct + outlet cup, extruded across the chute width."""
    ex, ey = exit_xy()
    h = CHUTE_W / 2
    xi0, xi1, xo0, xo1 = _xs()
    y_back_i, y_back_o = ey + h, ey + h + T
    z_top = Z_DECK_PLATE_TOP - DECK_PLATE_T - 0.3
    f = chute_floor
    kz = T / cos(radians(CHUTE_SLOPE))
    zo = chute_floor(Y_CUP_BACK) + DUCT_H           # cup roof flush with the duct roof: no step to catch on
    yc = Y_CUP_BACK
    outer = [(YF + 0.3, f(YF + 0.3) - T), (yc, f(yc) - T), (y_back_o, f(y_back_o) - kz),
             (y_back_o, z_top), (ey - h - T, z_top), (ey - h - T, f(ey - h - T) + DUCT_H + kz),
             (yc - T, f(yc) + DUCT_H + kz), (yc - T, zo + T), (YF + 0.3, zo + T)]
    inner = [(YF - 1.0, f(YF) - 0.1), (yc, f(yc)), (y_back_i, f(y_back_i)),
             (y_back_i, z_top + 1), (ey - h, z_top + 1), (ey - h, f(ey - h) + DUCT_H),
             (yc, f(yc) + DUCT_H), (yc, zo), (YF - 1.0, zo)]
    ob = mk.build("chute", C['fixed'], M['body'],
                  add=[lambda bm: mk.yz_prism(bm, outer, xo0, xo1)],
                  cut=[lambda bm: mk.yz_prism(bm, inner, xi0, xi1)])
    lip = mk.tmp(_bm(lambda bm: mk.box(bm, xi0 - 0.1, xi1 + 0.1, YF + 0.3, YF + 3.3, Z_CUP - 0.5, Z_CUP + CUP_LIP)))
    zf = Z_FLOOR_T + 0.3                                    # keel + feet: the chute stands on the floor
    keel = [(YF + 6.0, zf), (y_back_o - 1.0, zf), (y_back_o - 1.0, f(y_back_o - 1.0) - kz + 0.5),
            (yc, f(yc) - T + 0.5), (YF + 6.0, f(YF + 6.0) - T + 0.5)]
    legs = mk.tmp(_bm(lambda bm: mk.yz_prism(bm, keel, ex - 1.5, ex + 1.5)))
    feet = [mk.tmp(_bm(lambda bm, x=x: mk.box(bm, x - 1.5, x + 1.5, YF + 6.0, yc, zf, f(yc) - T + 0.5)))
            for x in (xo0 + 1.5, xo1 - 1.5)]
    mk.boolean(ob, [lip, legs] + feet, 'UNION')
    return ob


def _bm(f):
    import bmesh
    b = bmesh.new()
    f(b)
    return b


def make_door(C, M):
    """Clear outlet cover hinged at the top; lift it to take the capsule over the cup lip."""
    x0, x1 = OUTLET_X[0] + 0.5, OUTLET_X[1] - 0.5              # between the hinge ears
    y0, y1 = YFO - 3.0, YFO - 0.6
    return mk.build("outlet_door", C['move'], M['door'], origin=(0, DOOR_PIN_Y, DOOR_PIN_Z),
                    add=[lambda bm: mk.box(bm, x0, x1, y0, y1, OUTLET_Z[0] - 3.0, OUTLET_Z[1] + 2.5)],
                    union_parts=[lambda bm: x_cyl(bm, 2.4, x0 + 3.0, x1 - 3.0, DOOR_PIN_Y, DOOR_PIN_Z),
                                 lambda bm: mk.box(bm, (x0 + x1) / 2 - 12, (x0 + x1) / 2 + 12, y0 - 3.0, y0 + 0.5,
                                                   OUTLET_Z[0] - 3.0, OUTLET_Z[0] + 3.0)],
                    cut=[lambda bm: x_cyl(bm, PIN_WIRE_R + 0.15, x0 - 1.0, x1 + 1.0, DOOR_PIN_Y, DOOR_PIN_Z)])   # wire pin
