"""Fit checks: interference volumes (boolean intersect) and clearances (BVH nearest)."""
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from rig import world_bvh

# Resting / screwed / press-fit contacts that are allowed to touch (not to penetrate).
CONTACT = {
    frozenset(p) for p in [
        ("deck", "rotor"), ("pinion_axle", "mech_box"), ("mech_box", "base_box"), ("mech_box", "funnel"),
        ("mech_box", "bezel"), ("funnel", "window_front"), ("funnel", "window_back"),
        ("funnel", "window_left"), ("funnel", "window_right"), ("lid", "case_post_0"), ("lid", "case_post_1"),
        ("lid", "case_post_2"), ("lid", "case_post_3"), ("funnel", "case_post_0"), ("funnel", "case_post_1"),
        ("funnel", "case_post_2"), ("funnel", "case_post_3"), ("rotor", "crown_ring"), ("token_0", "knob"),
        ("deck", "mech_box"), ("token_drawer", "base_box"), ("token_1", "token_drawer"),
        ("token_2", "token_drawer"), ("hood", "funnel"), ("deck", "shim_04"), ("rotor", "shim_04"),
        ("deck", "deck_bracket"), ("pinion_axle", "test_gear_jig"), ("test_gear_jig", "shim_04"),
        ("test_crown_sector", "shim_04"), ("test_token_jig", "bezel"), ("topper", "lid"),
        ("token_0", "coin_wheel"), ("knob", "coin_wheel"), ("coin_housing", "mech_box"),  # v3 coin mech
        ("coin_housing", "base_box"), ("coin_plate", "mech_box"), ("coin_plate", "base_box"),
        ("logo", "mech_box"), ("logo_sparkles_yellow", "logo"), ("logo_sparkles_mint", "logo"),
        ("logo_sparkles_coral", "logo"),
    ] + [("funnel", "pillar_%d" % i) for i in range(4)] + [("lid", "pillar_%d" % i) for i in range(4)]
    + [("base_box", "foot_%d" % i) for i in range(4)]
}
SKIP = ("capsule_", "cap_", "test_", "spare_")   # capsules, test jigs and spares are not machine parts


def parts():
    root = bpy.data.collections["GACHA"]
    return [o for o in root.all_objects if o.type == 'MESH' and not o.name.startswith(SKIP)]


def world_aabb(ob):
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])


def _aabb_hit(a, b, pad=1e-4):
    return all(a[0][i] <= b[1][i] + pad and b[0][i] <= a[1][i] + pad for i in range(3))


def inter_volume(a, b):
    """Intersection volume in mm^3 (Manifold boolean on evaluated copies)."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(a.evaluated_get(dg), depsgraph=dg)
    tmp = bpy.data.objects.new("_iv", me)
    bpy.context.scene.collection.objects.link(tmp)
    tmp.matrix_world = a.evaluated_get(dg).matrix_world.copy()
    other_me = bpy.data.meshes.new_from_object(b.evaluated_get(dg), depsgraph=dg)
    other = bpy.data.objects.new("_iv2", other_me)
    bpy.context.scene.collection.objects.link(other)
    other.matrix_world = b.evaluated_get(dg).matrix_world.copy()
    mod = tmp.modifiers.new("i", 'BOOLEAN')
    mod.operation, mod.solver, mod.object = 'INTERSECT', 'MANIFOLD', other
    dg = bpy.context.evaluated_depsgraph_get()
    res = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg), depsgraph=dg)
    bm = bmesh.new()
    bm.from_mesh(res)
    bm.transform(tmp.matrix_world)
    vol = abs(bm.calc_volume()) * 1e9
    bm.free()
    for o, m in ((tmp, me), (other, other_me)):
        bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.meshes.remove(m)
    bpy.data.meshes.remove(res)
    return vol


def interferences(objs=None, movers=None, min_vol=0.01):
    """Pairs whose meshes overlap. If movers is given, only pairs involving a mover are tested.
    Returns [(a, b, volume_mm3, is_contact_pair)]."""
    objs = objs or parts()
    boxes = {o.name: world_aabb(o) for o in objs}
    bvhs = {}
    out = []
    for i, a in enumerate(objs):
        for b in objs[i + 1:]:
            if movers and a.name not in movers and b.name not in movers:
                continue
            if not _aabb_hit(boxes[a.name], boxes[b.name]):
                continue
            for o in (a, b):
                if o.name not in bvhs:
                    bvhs[o.name] = world_bvh(o)
            if not bvhs[a.name].overlap(bvhs[b.name]):
                continue
            vol = inter_volume(a, b)
            if vol >= min_vol:
                out.append((a.name, b.name, round(vol, 3), frozenset((a.name, b.name)) in CONTACT))
    return out


def clearance(a, b, sample=4000):
    """Approximate minimum distance (mm) between two objects (vertex -> surface both ways)."""
    oa, ob = bpy.data.objects[a], bpy.data.objects[b]
    ta, tb = world_bvh(oa), world_bvh(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    best = 1e9
    for src, tgt in ((oa, tb), (ob, ta)):
        ev = src.evaluated_get(dg)
        me = ev.to_mesh()
        mw = ev.matrix_world
        step = max(1, len(me.vertices) // sample)
        for k in range(0, len(me.vertices), step):
            hit = tgt.find_nearest(mw @ me.vertices[k].co)
            if hit[0] is not None:
                best = min(best, hit[3])
        ev.to_mesh_clear()
    return best * 1000.0


MOVERS = ["knob", "token_0", "dog_pawl", "ratchet", "ratchet_pawl", "hex_shaft", "sleeve_front",
          "sleeve_rear", "spacer", "gear_A", "gear_B_pinion", "rotor", "crown_ring", "coin_wheel"]


def sweep(step=2.0, token=True, turn=360.0):
    """Turn the handle through a full cycle; at each step drop the pawls onto their cams and look
    for any interference involving a moving part. Returns (clashes, pawl_log)."""
    import rig
    objs = parts()
    clashes, log = [], []
    n = int(round(turn / step))
    for i in range(n + 1):
        t = i * step
        dog, rat = rig.pose(t, token=token)
        log.append((t, dog, rat))
        for a, b, vol, contact in interferences(objs, movers=set(MOVERS)):
            if not contact:
                clashes.append((t, a, b, vol))
    rig.pose(0.0, token=token)
    return clashes, log
