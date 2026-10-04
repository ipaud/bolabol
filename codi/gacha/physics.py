"""Gravity test: capsules fill the hopper, the handle turns N times, count capsules per turn.

Bullet simulates only the capsules (CAPSULE shape). The rotor and cone
are kinematic (driven by the knob through the rig drivers); everything else is static mesh.
"""
import random
from math import radians, pi, cos, sin
import bpy
from mathutils import Vector, Euler
from params import *

FPS = 24
SETTLE = 36                 # frames before the first turn
TURN = 48                   # frames per 360 deg turn
PAUSE = 36                  # frames resting at home after each turn (1.5 s to take the capsule)
STATIC = ["deck", "funnel", "hood", "chute", "window_front", "window_back", "window_left",
          "window_right", "lid", "base_box", "outlet_door", "mech_box"]
KINEMATIC = ["rotor"]
SIM = "G_sim"


def turn_frames(k):
    """(start, end) frame of turn k (0-based)."""
    s = SETTLE + k * (TURN + PAUSE)
    return s, s + TURN


def _ctx(ob):
    """Explicit context. rigidbody.constraint_add reads the *view layer* active object and
    segfaults when it is None (Blender 5.1), so make `ob` really active and selected first."""
    s = bpy.context.scene
    vl = bpy.context.view_layer
    vl.update()
    vl.objects.active = ob
    ob.select_set(True)
    return bpy.context.temp_override(scene=s, view_layer=bpy.context.view_layer, object=ob,
                                     active_object=ob, selected_objects=[ob], selected_editable_objects=[ob])


def _rb(ob, kind, shape, margin=0.0005, friction=0.6, restitution=0.35, mass=1.0):
    if ob.rigid_body is None:
        with _ctx(ob):
            bpy.ops.rigidbody.object_add(type=kind)
    rb = ob.rigid_body
    rb.type = kind
    rb.collision_shape = shape
    rb.use_margin, rb.collision_margin = True, margin
    rb.friction, rb.restitution = friction, restitution
    rb.use_deactivation = False
    if kind == 'ACTIVE':
        rb.mass = mass
        rb.linear_damping, rb.angular_damping = 0.04, 0.15
    return rb


def world(frames, substeps=30, iters=30):
    s = bpy.context.scene
    if s.rigidbody_world is None:
        with bpy.context.temp_override(scene=s):
            bpy.ops.rigidbody.world_add()
    w = s.rigidbody_world
    w.enabled = True
    w.substeps_per_frame, w.solver_iterations, w.use_split_impulse = substeps, iters, False
    w.time_scale = 1.0
    w.point_cache.frame_start, w.point_cache.frame_end = 1, frames
    s.frame_start, s.frame_end = 1, frames
    s.render.fps = FPS
    s.gravity = (0, 0, -9.81)
    return w


def clear_sim():
    s = bpy.context.scene
    c = bpy.data.collections.get(SIM)
    if c:
        for o in list(c.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    for o in list(bpy.data.objects):
        if o.rigid_body_constraint:
            bpy.data.objects.remove(o, do_unlink=True)
    for o in bpy.data.collections["GACHA"].all_objects:
        if o.rigid_body:
            with _ctx(o):
                bpy.ops.rigidbody.object_remove()
    if s.rigidbody_world:
        with bpy.context.temp_override(scene=s):
            bpy.ops.rigidbody.world_remove()


def animate_handle(turns):
    knob = bpy.data.objects["knob"]
    knob.animation_data_clear()
    knob.rotation_euler[1] = 0.0
    knob.keyframe_insert("rotation_euler", index=1, frame=1)
    for k in range(turns):
        s, e = turn_frames(k)
        knob.rotation_euler[1] = radians(360.0 * k)
        knob.keyframe_insert("rotation_euler", index=1, frame=s)
        knob.rotation_euler[1] = radians(360.0 * (k + 1))
        knob.keyframe_insert("rotation_euler", index=1, frame=e)
    return knob


def capsule_spots(n_layers=2, seed=7):
    """Jittered grid above the hood inside the case, plus one capsule seated in each loaded pocket."""
    rnd = random.Random(seed)
    spots = []
    for k in range(1, N_POCKETS):
        a = radians(pocket_angle(k, 0.0))
        spots.append(((R_POCKET * cos(a), R_POCKET * sin(a), Z_DECK + CAP_H / 2 + 0.6), (0, 0, rnd.uniform(0, 6.3))))
    import params
    grid = ((-62.0, 0.0, 62.0), (-62.0, -2.0, 58.0), 56.0) if params.STYLE == "mochi" else \
        ((-78.0, -26.0, 26.0, 78.0), (-62.0, -2.0, 58.0), 58.0)     # v2: no spawn overlaps under the lower lid
    for layer in range(n_layers):
        z = 300.0 + layer * grid[2]
        for x in grid[0]:
            for y in grid[1]:
                p = (x + rnd.uniform(-2, 2), y + rnd.uniform(-2, 2), z + rnd.uniform(-1, 1))
                r = (rnd.uniform(0, 6.3), rnd.uniform(0, 6.3), rnd.uniform(0, 6.3))
                spots.append((p, r))
    return spots


def hinge(name, a, b, pivot_mm, axis_rot, lo_deg, hi_deg):
    e = bpy.data.objects.new(name, None)
    bpy.data.collections[SIM].objects.link(e)
    e.location = Vector(pivot_mm) * MM
    e.rotation_euler = axis_rot
    bpy.context.view_layer.update()
    if bpy.context.scene.rigidbody_world is None:
        raise RuntimeError("rigid body world missing")
    with _ctx(e):
        bpy.ops.rigidbody.constraint_add(type='HINGE')
    c = e.rigid_body_constraint
    c.object1, c.object2 = a, b
    c.use_limit_ang_z, c.limit_ang_z_lower, c.limit_ang_z_upper = True, radians(lo_deg), radians(hi_deg)
    c.disable_collisions = True
    return e


def setup(turns=5, n_layers=2, substeps=30, iters=30, seed=7):
    import rig
    import parts_capsule as K
    import build
    frames = turn_frames(turns - 1)[1] + PAUSE + 12
    clear_sim()
    rig.add_drivers()
    rig.pose(0.0, token=True)
    animate_handle(turns)
    w = world(frames, substeps, iters)
    sim = bpy.data.collections.get(SIM) or bpy.data.collections.new(SIM)
    if sim.name not in bpy.data.collections["GACHA"].children:
        bpy.data.collections["GACHA"].children.link(sim)
    for n in STATIC + [n for n in ("pillar_0", "pillar_1", "pillar_2", "pillar_3") if bpy.data.objects.get(n)]:
        _rb(bpy.data.objects[n], 'PASSIVE', 'MESH')
    for n in KINEMATIC:
        _rb(bpy.data.objects[n], 'PASSIVE', 'MESH').kinematic = True
    M = build.materials()
    me = bpy.data.meshes.get("capsule_mesh") or K.make_sim_mesh({'caps': sim}, M)
    caps = []
    for i, (p, r) in enumerate(capsule_spots(n_layers, seed)):
        o = bpy.data.objects.new("cap_%02d" % i, me)
        sim.objects.link(o)
        o.location = Vector(p) * MM
        o.rotation_euler = r
        o.material_slots[1].link = 'OBJECT'
        o.material_slots[1].material = M['cap_colors'][i % len(M['cap_colors'])]
        _rb(o, 'ACTIVE', 'CAPSULE', margin=0.0005, mass=CAP_MASS, friction=0.6, restitution=0.35)
        caps.append(o)
    bpy.context.scene.frame_set(1)
    return caps, frames


def step_to(frame):
    s = bpy.context.scene
    f = s.frame_current
    while f < frame:
        f += 1
        s.frame_set(f)
    return f


def capsule_states():
    """Classify every capsule by where it is (world mm)."""
    ex, ey = exit_xy()
    out = {}
    for o in bpy.data.collections[SIM].objects:
        if not o.name.startswith("cap_"):
            continue
        p = o.matrix_world.translation / MM
        if p.z > Z_DECK - 5:
            where = "hopper" if p.z > Z_ROT_BOT else "deck"
        elif p.y < YFO - 30:
            where = "taken"
        elif p.y < Y_CUP_BACK + 8 and p.z < OUTLET_Z[1]:
            where = "cup"
        elif p.z > 0:
            where = "chute"
        else:
            where = "lost"
        out[o.name] = (where, tuple(round(c, 1) for c in p))
    return out


def reset():
    """Invalidate the rigid body cache (touching a world property does it) and rewind."""
    w = bpy.context.scene.rigidbody_world
    w.substeps_per_frame += 1
    w.substeps_per_frame -= 1
    bpy.context.scene.frame_set(1)


# ---------------- full test with "user takes the capsule" events ----------------
SPAWN_KEY = "spawn"


def _key_spawn(caps):
    for o in caps:
        o[SPAWN_KEY] = list(o.location) + list(o.rotation_euler)


def _keys_constant(ob):
    ad = ob.animation_data
    if not ad or not ad.action:
        return
    try:
        fcs = ad.action.fcurves
    except AttributeError:                      # Blender 5 layered actions
        from bpy_extras import anim_utils
        cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
        fcs = cb.fcurves if cb else []
    for fc in fcs:
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER' if kp.co[0] > 1.5 else 'CONSTANT'


def take(cap, frame, k):
    """Emulate the user: at `frame` the capsule becomes kinematic, is lifted over the lip, pulled
    out through the (opening) door and placed on the table in front of the machine."""
    loc, rot = cap.matrix_world.translation.copy(), cap.matrix_world.to_euler()
    sp = cap[SPAWN_KEY]
    cap.location, cap.rotation_euler = sp[:3], sp[3:]
    cap.keyframe_insert("location", frame=1)
    cap.keyframe_insert("rotation_euler", frame=1)
    cap.rigid_body.kinematic = False
    cap.keyframe_insert("rigid_body.kinematic", frame=1)
    cap.keyframe_insert("rigid_body.kinematic", frame=frame - 1)
    cap.rigid_body.kinematic = True
    cap.keyframe_insert("rigid_body.kinematic", frame=frame)
    cap.location, cap.rotation_euler = loc, rot
    cap.keyframe_insert("location", frame=frame)
    cap.keyframe_insert("rotation_euler", frame=frame)
    cap.location = Vector((loc.x, (YFO - 8.0) * MM, (OUTLET_Z[1] - 20.0) * MM))
    cap.keyframe_insert("location", frame=frame + 6)
    cap.location = Vector(((-110.0 + 55.0 * k) * MM, -205.0 * MM, CAP_R * MM))
    cap.rotation_euler = (0.0, 0.0, 0.0)
    cap.keyframe_insert("location", frame=frame + 14)
    cap.keyframe_insert("rotation_euler", frame=frame + 14)
    _keys_constant(cap)
    door = bpy.data.objects["outlet_door"]
    door.rigid_body.kinematic = True
    for f, a in ((frame - 2, 0.0), (frame + 3, -100.0), (frame + 9, -100.0), (frame + 16, 0.0)):
        door.rotation_euler[0] = radians(a)
        door.keyframe_insert("rotation_euler", index=0, frame=f)
    door.rotation_euler[0] = 0.0


def step_track(frame_end, crossed):
    """Step the sim to frame_end; record the first frame each capsule falls through the deck."""
    s = bpy.context.scene
    f = s.frame_current
    caps = [o for o in bpy.data.collections[SIM].objects if o.name.startswith("cap_")]
    while f < frame_end:
        f += 1
        s.frame_set(f)
        for o in caps:
            if o.name not in crossed and o.matrix_world.translation.z < (Z_DECK - 30.0) * MM:
                crossed[o.name] = f
    return f


def turn_of(frame):
    for k in range(64):
        s, e = turn_frames(k)
        if frame <= e + PAUSE:
            return k
    return None


def run_test(turns=5, n_layers=2, substeps=30, iters=30, seed=7):
    """Full gravity test. Returns per-turn report lines and the capsule->frame crossing table."""
    import time
    caps, frames = setup(turns, n_layers, substeps, iters, seed)
    _key_spawn(caps)
    lines, taken = [], []
    for k in range(turns):
        t0 = time.time()
        reset()
        crossed = {}
        end = turn_frames(k)[1] + PAUSE
        step_track(end, crossed)
        st = capsule_states()
        in_cup = [n for n, v in st.items() if v[0] == "cup" and n not in taken]
        per_turn = {}
        for n, fr in crossed.items():
            per_turn.setdefault(turn_of(fr), []).append(n)
        lines.append("turn %d: dropped this turn %s | cup %s | %.1fs" % (
            k + 1, per_turn.get(k, []), in_cup, time.time() - t0))
        for n in in_cup:
            take(bpy.data.objects[n], end, len(taken))
            taken.append(n)
    reset()
    crossed = {}
    step_track(frames, crossed)
    from collections import Counter
    st = capsule_states()
    lines.append("final: %s" % dict(Counter(v[0] for v in st.values())))
    lines.append("drops by turn: %s" % {k: sorted(v) for k, v in _group(crossed).items()})
    return lines, crossed


def _group(crossed):
    g = {}
    for n, fr in crossed.items():
        g.setdefault(turn_of(fr), []).append(n)
    return g


STATE = {}


def test_begin(turns=5, n_layers=2, substeps=30, iters=30, seed=7):
    caps, frames = setup(turns, n_layers, substeps, iters, seed)
    _key_spawn(caps)
    STATE.clear()
    STATE.update(turns=turns, frames=frames, taken=[], lines=[])
    return len(caps), frames


def test_turn(k):
    """Replay from frame 1 to the end of turn k, then let the user take what is in the cup."""
    import time
    t0 = time.time()
    reset()
    crossed = {}
    end = turn_frames(k)[1] + PAUSE
    step_track(end, crossed)
    st = capsule_states()
    taken = STATE["taken"]
    in_cup = [n for n, v in st.items() if v[0] == "cup" and n not in taken]
    line = "turn %d: dropped %s | in cup %s | %.1fs" % (k + 1, sorted(_group(crossed).get(k, [])), in_cup,
                                                        time.time() - t0)
    for n in in_cup:
        take(bpy.data.objects[n], end, len(taken))
        taken.append(n)
    STATE["lines"].append(line)
    return line, st


def test_final():
    from collections import Counter
    reset()
    crossed = {}
    step_track(STATE["frames"], crossed)
    st = capsule_states()
    return dict(Counter(v[0] for v in st.values())), {k: sorted(v) for k, v in _group(crossed).items()}


# ---------------- continuous test: no replays, no "take" teleports ----------------
# run_test replays from frame 1 every turn and keys the take on the capsule names of the previous
# replay. The pile is chaotic, so in a later replay the take can teleport a capsule into the cup onto a
# different one and shoot it back up the chute (false 1.7-3.8 m/s "jams", capsules lost through walls).
# run_flow runs Bullet once: the cup lip is cut away (sim only) and the door is open, so each delivered
# capsule rolls out onto a sloped table. Delivery per turn = capsules crossing below the deck, by turn.

def _nolip_mesh(chute):
    import bmesh
    xs = [(chute.matrix_world @ v.co).x / MM for v in chute.data.vertices]
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = (min(xs) + CHUTE_T if v.co.x < 0 else max(xs) - CHUTE_T) * MM
        v.co.y = (YF - 8.0 if v.co.y < 0 else YF + 3.6) * MM
        v.co.z = (Z_CUP - 0.2 if v.co.z < 0 else Z_CUP + CUP_LIP + 2.0) * MM
    me = bpy.data.meshes.new("_lipcut")
    bm.to_mesh(me)
    bm.free()
    cutter = bpy.data.objects.new("_lipcut", me)
    bpy.context.scene.collection.objects.link(cutter)
    mod = chute.modifiers.new("nolip", 'BOOLEAN')
    mod.operation, mod.solver, mod.object = 'DIFFERENCE', 'EXACT', cutter
    dg = bpy.context.evaluated_depsgraph_get()
    out = bpy.data.meshes.new_from_object(chute.evaluated_get(dg), depsgraph=dg)
    chute.modifiers.remove(mod)
    bpy.data.objects.remove(cutter, do_unlink=True)
    bpy.data.meshes.remove(me)
    return out


def run_flow(turns=12, n_layers=2, seed=7, substeps=30, iters=30):
    """One continuous run. Returns (capsules delivered per turn, crossing frames). The chute mesh and the
    door angle are restored afterwards; call clear_sim() to drop the capsules and the rigid body world."""
    caps, frames = setup(turns, n_layers, seed=seed, substeps=substeps, iters=iters)
    chute, door = bpy.data.objects["chute"], bpy.data.objects["outlet_door"]
    keep_me, keep_door = chute.data, door.rotation_euler[0]
    try:
        chute.data = _nolip_mesh(chute)
        door.rotation_euler[0] = radians(-100.0)
        k = tan(radians(4.0))                                   # table falls away from the machine
        tv = [(-300, YFO - 1, 8.0), (300, YFO - 1, 8.0), (300, YFO - 600, 8.0 - 599 * k), (-300, YFO - 600, 8.0 - 599 * k)]
        me = bpy.data.meshes.new("_table")
        me.from_pydata([Vector(c) * MM for c in tv], [], [(0, 1, 2, 3)])
        table = bpy.data.objects.new("_table", me)
        bpy.data.collections[SIM].objects.link(table)
        _rb(table, 'PASSIVE', 'MESH')
        reset()
        crossed = {}
        step_track(frames, crossed)
    finally:
        lipless = chute.data
        chute.data = keep_me
        if lipless is not keep_me:
            bpy.data.meshes.remove(lipless)
        door.rotation_euler[0] = keep_door
    per_turn = [len([n for n, f in crossed.items() if turn_of(f) == t]) for t in range(turns)]
    return per_turn, crossed
