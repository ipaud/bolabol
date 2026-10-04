"""Kinematic rig: the knob rotation (Y, + = clockwise seen from the front) drives everything.

Gear train: knob/shaft/gear A (+t) -> gear B + pinion (-t) -> rotor (+t * 19/95 about Z, CCW from
above). Pawls are cam followers: their angle is solved against the real meshes (lowest pose
without overlap), so the rig shows exactly what the printed parts allow.
"""
import bpy
from math import radians
from mathutils.bvhtree import BVHTree
from params import Z_PIN, Z_CROWN

KNOB = "knob"
WITH_SHAFT = ["hex_shaft", "sleeve_front", "sleeve_rear", "ratchet", "spacer", "gear_A", "token_0", "coin_wheel"]
REVERSE = ["gear_B_pinion"]
ROTOR = ["rotor", "crown_ring"]


def _drive(ob, index, expr):
    ob.driver_remove("rotation_euler", index)
    d = ob.driver_add("rotation_euler", index).driver
    d.type = 'SCRIPTED'
    v = d.variables.new()
    v.name, v.type = "t", 'SINGLE_PROP'
    v.targets[0].id_type = 'OBJECT'
    v.targets[0].id = bpy.data.objects[KNOB]
    v.targets[0].data_path = "rotation_euler[1]"
    d.expression = expr


def add_drivers():
    for n in WITH_SHAFT:
        if n in bpy.data.objects:
            _drive(bpy.data.objects[n], 1, "t")
    for n in REVERSE:
        _drive(bpy.data.objects[n], 1, "-t")
    for n in ROTOR:
        _drive(bpy.data.objects[n], 2, "t*%d/%d" % (Z_PIN, Z_CROWN))


def remove_drivers():
    for n in WITH_SHAFT + REVERSE + ROTOR:
        ob = bpy.data.objects.get(n)
        if ob and ob.animation_data:
            for i in range(3):
                ob.driver_remove("rotation_euler", i)


def world_bvh(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ev.matrix_world
    verts = [mw @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys, all_triangles=False)


def hits(a_bvh, ob):
    return len(a_bvh.overlap(world_bvh(ob))) > 0


def settle(pawl, obstacles, lower_sign, lo=-25.0, hi=25.0, iters=22):
    """Rotate `pawl` (about its local Y at the pivot) to the lowest angle that does not overlap the
    obstacles. lower_sign = +1 if positive rotation lowers the nose, -1 otherwise. Degrees."""
    ob = bpy.data.objects[pawl]
    obs_bvh = [world_bvh(bpy.data.objects[o]) for o in obstacles]

    def free(angle):
        ob.rotation_euler[1] = radians(angle)
        bpy.context.view_layer.update()
        me = world_bvh(ob)
        return not any(me.overlap(b) for b in obs_bvh)

    raised = -lower_sign * 12.0
    if not free(raised):
        ob.rotation_euler[1] = 0.0
        return None
    a, b = raised, lower_sign * 25.0            # a free, b candidate lowest
    if free(b):
        return b
    for _ in range(iters):
        m = 0.5 * (a + b)
        if free(m):
            a = m
        else:
            b = m
    free(a)
    return a


def pose(turn_deg, token=True):
    """Put the machine at a handle angle and let both pawls fall onto their cams."""
    bpy.data.objects[KNOB].rotation_euler[1] = radians(turn_deg)
    tok = bpy.data.objects.get("token_0")
    if tok:
        tok.hide_set(not token)
        tok.hide_render = not token
    bpy.context.view_layer.update()
    wheel = "coin_wheel" if bpy.data.objects.get("coin_wheel") else None    # v3: both pawls ride on it
    obst = [wheel or "knob"] + (["token_0"] if token else [])
    dog = settle("dog_pawl", obst, lower_sign=-1)
    rat = settle("ratchet_pawl", [wheel or "ratchet"], lower_sign=+1)
    return dog, rat
