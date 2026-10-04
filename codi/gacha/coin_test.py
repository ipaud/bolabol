"""v3 dynamic coin-mech test in its own scene (token_test is the v2 knob version).

The coin wheel is a free rigid body driven through a torsion spring by a kinematic "hand" turning
at a set speed: a lock stops the wheel while the hand winds the spring up. The blocking pawl hangs
on a hinge at DOG_ANGLE, pulled by gravity and by the pen spring, modelled as a hinge motor
saturated at the spring torque (a preloaded spring of flat rate). The coin is a free
body in the pocket; housing (funnel), mech box (front wall), base box (duct) and drawer are static.

    import coin_test as T
    T.build(coin=False, turn_s=0.5, spring=0.02); rows = T.step(150); T.summary(rows)
"""
from math import radians, degrees, tan, cos, sin, pi
import bpy
import bmesh
from mathutils import Euler
import mk
from token_test import _win, _ctx, _rb, remove_scene
from params import *

SCENE = "CoinTest"
FPS = 24
STATIC = ["coin_housing", "mech_box", "base_box", "token_drawer"]
MOTOR_SIGN = 1.0                # motor sense that lowers the nose
MOTOR_SCALE = 1.0               # Blender's motor 'max impulse' acts as a torque limit in N m (calibrate())
OBJ = {}


def _recenter_bbox(ob):
    """Origin (Bullet's centre of mass) at the bounding box centre: right for a symmetric coin, whose
    engraving puts thousands of vertices on one face and drags mk.recenter's vertex centroid off."""
    from mathutils import Vector, Matrix
    if ob.data.users > 1:
        ob.data = ob.data.copy()
    c = sum((Vector(v) for v in ob.bound_box), Vector()) / 8
    ob.data.transform(Matrix.Translation(-c))
    ob.location = ob.matrix_basis @ c


def _groups(ob, *layers):
    """Collision collections: 0 = static walls, 1 = wheel / pawl / coin, 19 = hand and anchor."""
    cc = ob.rigid_body.collision_collections
    for i in range(20):
        cc[i] = i in layers


def _dog_compound(sc, dog):
    """Convex nose / lever / foot pieces (Bullet is robust with convex parts), turned DOG_ANGLE."""
    import parts_token as T
    px, pz = T.dog_pivot()
    x0, x1 = DOG_TIP
    zb = T.Z_TIP + DOG_NOSE_H
    xr = x1 + DOG_NOSE_H * tan(radians(DOG_RAMP))
    hub = [(px + 4.5 * cos(a), pz + 4.5 * sin(a)) for a in [-pi / 2 + pi * i / 12 for i in range(13)]]
    zf = T.foot_z()

    def under(x):
        return zb + (hub[0][1] - zb) * (x - xr) / (hub[0][0] - xr)
    pieces = {
        "nose": ([(x0, T.Z_TIP + DOG_LEAD), (x0 + DOG_LEAD, T.Z_TIP)] if DOG_LEAD else [(x0, T.Z_TIP)])
        + [(x1, T.Z_TIP), (xr, zb + 0.2), (x0, zb + 0.2)],
        "lever": [(x0, zb), (xr, zb)] + hub + [(x0, zb + 6.0)],
        "foot": [(T.FOOT_X[0], zf), (T.FOOT_X[1], zf), (T.FOOT_X[1], under(T.FOOT_X[1]) + 0.3),
                 (T.FOOT_X[0], under(T.FOOT_X[0]) + 0.3)],
    }
    for name, poly in pieces.items():
        bm = bmesh.new()
        mk.fv_prism(bm, [spin(x, z, DOG_ANGLE) for x, z in poly], DOG_Y0, DOG_Y1)
        ch = mk.to_obj("ct_dog_" + name, bm, sc.collection)
        ch.parent = dog
        ch.matrix_parent_inverse = dog.matrix_basis.inverted()
        _rb(sc, ch, 'ACTIVE', 'CONVEX_HULL', mass=0.001, friction=0.3)
        _groups(ch, 1)
        ch.hide_render = True
    dog.rigid_body.collision_shape = 'COMPOUND'


def _linear(ob):
    """Constant speed between keys (the default Bezier eases in and out: the peak speed is ~1.6x)."""
    ad = ob.animation_data
    try:
        fcs = ad.action.fcurves
    except AttributeError:                                  # Blender 5 layered actions
        from bpy_extras import anim_utils
        cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
        fcs = cb.fcurves if cb else []
    for fc in fcs:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'


def _y_joint(sc, name, loc, kind, a, b):
    e = bpy.data.objects.new(name, None)
    sc.collection.objects.link(e)
    e.location = loc
    e.rotation_euler = Euler((radians(-90), 0, 0))          # constraint Z = world Y (the machine axes)
    with _ctx(sc, e):
        bpy.ops.rigidbody.constraint_add(type=kind)
    c = e.rigid_body_constraint
    c.object1, c.object2, c.disable_collisions = a, b, True
    return c


def _ang_spring(c, k, damp, lock_lin=True):
    c.spring_type = 'SPRING2'
    for ax in "xyz":
        setattr(c, "use_limit_lin_" + ax, lock_lin)
        if lock_lin:
            setattr(c, "limit_lin_%s_lower" % ax, 0.0)
            setattr(c, "limit_lin_%s_upper" % ax, 0.0)
    for ax in "xy":
        setattr(c, "use_limit_ang_" + ax, lock_lin)
        if lock_lin:
            setattr(c, "limit_ang_%s_lower" % ax, 0.0)
            setattr(c, "limit_ang_%s_upper" % ax, 0.0)
    c.use_spring_ang_z, c.spring_stiffness_ang_z, c.spring_damping_ang_z = True, k, damp


def build(coin=True, turn_s=2.0, turn_to=360.0, spring=0.02, frames=None, substeps=60, fps=FPS, coin_d=TOKEN_D,
          coin_t=TOKEN_T, friction=None):
    """(Re)create the test. turn_s: seconds per hand turn; spring: pen spring torque (N m) on the
    pawl at its rest pose (0 = gravity only). fps: sampling rate (the step is 1 / (fps * substeps)).
    coin_d / coin_t: printed coin diameter / thickness (tolerance, or a foreign coin).
    friction: same coefficient on every body (Bullet multiplies the pair: 0.6 -> mu 0.36);
    None keeps 0.3 on the movers and 0.4 on the walls (mu 0.09-0.12, slippery)."""
    main = bpy.data.scenes["Scene"]
    _win().scene = main
    remove_scene(SCENE)
    sc = bpy.data.scenes.new(SCENE)
    sc.unit_settings.system, sc.unit_settings.length_unit = 'METRIC', 'MILLIMETERS'
    sc.render.fps = fps
    t_turn = int(round(turn_to / 360.0 * turn_s * fps))
    rest = int(fps * 0.8)                                  # 0.8 s: spring preloads, pawl settles
    frames = frames or rest + t_turn + fps
    names = ["coin_wheel", "dog_pawl"] + STATIC + (["token_0"] if coin else [])
    o = {}
    for n in names:
        c = bpy.data.objects[n].copy()
        c.animation_data_clear()
        c.name = "ct_" + n
        sc.collection.objects.link(c)
        c.hide_render = c.hide_viewport = False
        o[n] = c
    o["coin_wheel"].rotation_euler = (0, 0, 0)
    o["dog_pawl"].rotation_euler = (0, 0, 0)               # resting on the rim at home
    pivot = o["dog_pawl"].location.copy()
    bpy.context.view_layer.update()
    mk.recenter(o["dog_pawl"])                             # centre of mass off the pivot: gravity acts
    if coin:
        o["token_0"].rotation_euler = (0, 0, 0)
        _recenter_bbox(o["token_0"])            # engraved coin: the vertex centroid is not its centre of mass
        k = coin_d / TOKEN_D                                # coin plane = YZ, bottom stays on the floor
        o["token_0"].scale = (coin_t / TOKEN_T, k, k)
        o["token_0"].location.z += (coin_d - TOKEN_D) / 2 * MM
    hand = bpy.data.objects.new("ct_hand", bpy.data.meshes.new_from_object(bpy.data.objects["hex_shaft"]))
    sc.collection.objects.link(hand)
    hand.location = o["coin_wheel"].location.copy()
    hand.hide_render = True
    win = _win()
    win.scene = sc
    with bpy.context.temp_override(window=win, scene=sc):
        bpy.ops.rigidbody.world_add()
    w = sc.rigidbody_world
    w.substeps_per_frame, w.solver_iterations = substeps, 60
    w.point_cache.frame_start, w.point_cache.frame_end = 1, frames
    sc.frame_start, sc.frame_end = 1, frames
    for n in STATIC:
        _rb(sc, o[n], 'PASSIVE', 'MESH')
        _groups(o[n], 0)
    _rb(sc, o["coin_wheel"], 'ACTIVE', 'MESH', mass=0.02, friction=0.3)
    _groups(o["coin_wheel"], 1)                            # held by its joint: only meets pawl and coin
    _rb(sc, o["dog_pawl"], 'ACTIVE', 'CONVEX_HULL', mass=0.003, friction=0.3)
    _groups(o["dog_pawl"], 1)
    _dog_compound(sc, o["dog_pawl"])
    if coin:
        _rb(sc, o["token_0"], 'ACTIVE', 'CONVEX_HULL', mass=0.0025, friction=0.3)
        _groups(o["token_0"], 0, 1)
    _rb(sc, hand, 'PASSIVE', 'CONVEX_HULL').kinematic = True
    _groups(hand, 19)
    # hand: rest, then one turn at a constant speed
    hand.keyframe_insert("rotation_euler", index=1, frame=1)
    hand.keyframe_insert("rotation_euler", index=1, frame=rest)
    hand.rotation_euler = (0, radians(turn_to), 0)
    hand.keyframe_insert("rotation_euler", index=1, frame=rest + t_turn)
    _linear(hand)
    _ang_spring(_y_joint(sc, "ct_hand_joint", hand.location.copy(), 'GENERIC_SPRING', hand, o["coin_wheel"]), 0.08, 0.02)
    _y_joint(sc, "ct_dog_hinge", pivot, 'HINGE', o["coin_housing"], o["dog_pawl"])
    if spring > 0:                                         # pen spring: constant nose-down torque (hinge motor
        e = bpy.data.objects.new("ct_pen_spring", None)     # saturated at `spring` N m, like a preloaded spring)
        sc.collection.objects.link(e)
        e.location, e.rotation_euler = pivot, Euler((0, 0, radians(90)))   # motor axis (local X) = world Y
        with _ctx(sc, e):
            bpy.ops.rigidbody.constraint_add(type='MOTOR')
        c = e.rigid_body_constraint
        c.object1, c.object2, c.disable_collisions = o["coin_housing"], o["dog_pawl"], True
        c.use_motor_ang, c.motor_ang_target_velocity = True, MOTOR_SIGN * 200.0
        c.motor_ang_max_impulse = spring * MOTOR_SCALE
    if friction is not None:
        for ob in sc.objects:
            if ob.rigid_body and ob is not hand:
                ob.rigid_body.friction = friction
    sc.frame_set(1)
    OBJ.clear()
    OBJ.update(sc=sc, main=main, o=o, hand=hand, frames=frames, coin=coin)
    return sc


def _ang(ob):
    return degrees(ob.matrix_world.to_euler('YXZ')[1])


def step(f_end=None):
    """Advance the test scene; rows (frame, hand deg, wheel deg, pawl deg, coin x z mm)."""
    sc, o = OBJ["sc"], OBJ["o"]
    _win().scene = sc
    f_end = min(f_end or OBJ["frames"], OBJ["frames"])
    rows, f = OBJ.setdefault("rows", []), sc.frame_current
    prev = rows[-1][2] if rows else 0.0
    while f < f_end:
        f += 1
        sc.frame_set(f)
        wh = _ang(o["coin_wheel"])
        wh += 360.0 * round((prev - wh) / 360.0)                       # unwrap
        prev = wh
        c = o["token_0"].matrix_world.translation / MM if OBJ["coin"] else None
        rows.append((f, round(_ang(OBJ["hand"]) % 360.0, 1), round(wh, 1),
                     round(_ang(o["dog_pawl"]), 2), None if c is None else (round(c.x, 1), round(c.z, 1))))
    return rows


def summary(rows):
    """Where the wheel stopped, deepest pawl angle, where the coin ended (drawer floor ~ z 6-10)."""
    wheel = [r[2] for r in rows]
    out = {"wheel_final": wheel[-1], "wheel_max": max(wheel), "pawl_min": min(r[3] for r in rows)}
    if rows[0][4] is not None:
        out["coin_final_xz"] = rows[-1][4]
        drop = next((r for r in rows if r[4][1] < Z_HANDLE - W_R - 10.0), None)
        out["coin_leaves_wheel_at_deg"] = drop[2] if drop else None
    return out


def done():
    remove_scene(SCENE)
    _win().scene = bpy.data.scenes["Scene"]


def calibrate(spring=0.01, fps=4800, substeps=1, ms=4.0):
    """Pocket parked under the pawl, no hand: early angular acceleration with gravity only vs gravity
    + motor, the motor run lifting the nose (free travel, the foot stop cannot cap it). Gravity torque
    is exact (mass, centre of mass), so the ratio gives the motor torque.
    Returns (gravity N m, motor N m measured, requested) and the per-sample traces."""
    global MOTOR_SIGN
    MOTOR_SIGN, sign = -MOTOR_SIGN, MOTOR_SIGN
    out = {}
    for s in (0.0, spring):
        build(coin=False, turn_to=0.0, spring=s, fps=fps, substeps=substeps, frames=int(fps * ms / 1000) + 2)
        o = OBJ["o"]
        for ob in (o["coin_wheel"], OBJ["hand"]):
            ob.rotation_euler = (0, radians(DOG_ANGLE), 0)
        OBJ["hand"].animation_data_clear()
        OBJ["sc"].frame_set(1)
        rows = step()
        out[s] = [(r[0] / fps * 1000.0, r[3]) for r in rows]
    dog = OBJ["o"]["dog_pawl"]
    import parts_token as P
    px, _ = spin(*P.dog_pivot(), DOG_ANGLE)
    tau_g = dog.rigid_body.mass * 9.81 * abs(dog.location.x - px * MM)
    t, a0 = out[0.0][-1][0] / 1000.0, radians(out[0.0][0][1] - out[0.0][-1][1])
    a1 = radians(out[spring][0][1] - out[spring][-1][1])
    MOTOR_SIGN = sign
    done()
    return (tau_g, -tau_g * (a1 / a0 - 1.0), spring), out
