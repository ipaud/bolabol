"""Dynamic token-lock test in its own scene.

The knob is a free rigid body driven through a torsion spring (GENERIC_SPRING / SPRING2) by a
kinematic driver that turns at hand speed: if something blocks the knob, the spring winds up and
the knob stays put, exactly like a hand meeting a lock. The blocking pawl hangs on a hinge and
falls by gravity; the token is a free body inside the knob slit.
"""
from math import radians, degrees
import bpy
from mathutils import Vector, Euler
from params import MM, Z_HANDLE, TOKEN_Y

SCENE = "TokenTest"
COPIES = ["knob", "bezel", "dog_pawl", "token_0", "token_chute"]


def _win():
    return bpy.data.window_managers[0].windows[0]


def _ctx(sc, ob):
    vl = sc.view_layers[0]
    vl.objects.active = ob
    ob.select_set(True, view_layer=vl)
    return bpy.context.temp_override(window=_win(), scene=sc, view_layer=vl, object=ob, active_object=ob,
                                     selected_objects=[ob], selected_editable_objects=[ob])


def _rb(sc, ob, kind, shape, mass=0.01, friction=0.4, margin=0.0001):
    with _ctx(sc, ob):
        bpy.ops.rigidbody.object_add(type=kind)
    rb = ob.rigid_body
    rb.collision_shape, rb.use_margin, rb.collision_margin = shape, True, margin
    rb.friction, rb.restitution, rb.use_deactivation = friction, 0.05, False
    if kind == 'ACTIVE':
        rb.mass = mass
        rb.linear_damping, rb.angular_damping = 0.1, 0.1
    return rb


def remove_scene(name):
    """Delete a test scene: rigid body world FIRST (deleting its objects first double-frees Bullet's
    broadphase and crashes Blender 5.1), then objects, then the scene."""
    old = bpy.data.scenes.get(name)
    if not old:
        return
    if old.rigidbody_world:
        win = _win()
        prev = win.scene
        win.scene = old                                # the operator polls the window's scene
        with bpy.context.temp_override(window=win):
            bpy.ops.rigidbody.world_remove()
        win.scene = prev
    for o in list(old.collection.all_objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.scenes.remove(old)


def build(token=True, dog_angle=0.0, turn_to=360.0, frames=150, dog_shape='CONVEX_HULL', name=SCENE):
    """(Re)create the test scene. dog_angle: starting pawl angle (deg) solved by rig.pose()."""
    main = bpy.data.scenes["Scene"]
    _win().scene = main
    remove_scene(name)
    sc = bpy.data.scenes.new(name)
    sc.unit_settings.system, sc.unit_settings.length_unit = 'METRIC', 'MILLIMETERS'
    objs = {}
    for n in COPIES:
        if n == "token_0" and not token:
            continue
        o = bpy.data.objects[n].copy()
        o.animation_data_clear()
        o.name = "tt_" + n
        sc.collection.objects.link(o)
        objs[n] = o
    objs["knob"].rotation_euler = (0, 0, 0)
    pivot = objs["dog_pawl"].location.copy()
    objs["dog_pawl"].rotation_euler = (0, radians(dog_angle), 0)
    import mk
    bpy.context.view_layer.update()
    mk.recenter(objs["dog_pawl"])                      # centre of mass off the pivot: gravity pulls the nose down
    if token:
        mk.recenter(objs["token_0"])
    if token:
        objs["token_0"].rotation_euler = (0, 0, 0)
    drv = bpy.data.objects.new("tt_driver", bpy.data.meshes.new_from_object(bpy.data.objects["hex_shaft"]))
    sc.collection.objects.link(drv)
    drv.location = bpy.data.objects["knob"].location.copy()
    floor = bpy.data.objects.new("tt_floor", bpy.data.meshes.new("tt_floor"))
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(0.3, 0.3, 0.01), verts=bm.verts)
    bm.to_mesh(floor.data)
    bm.free()
    floor.location = (0, TOKEN_Y * MM, 0.02)
    sc.collection.objects.link(floor)
    win = _win()
    win.scene = sc
    with bpy.context.temp_override(window=win, scene=sc):
        bpy.ops.rigidbody.world_add()
    w = sc.rigidbody_world
    w.substeps_per_frame, w.solver_iterations = 60, 60
    w.point_cache.frame_start, w.point_cache.frame_end = 1, frames
    sc.frame_start, sc.frame_end = 1, frames
    _rb(sc, objs["bezel"], 'PASSIVE', 'MESH')
    _rb(sc, objs["token_chute"], 'PASSIVE', 'MESH')
    _rb(sc, floor, 'PASSIVE', 'BOX')
    _rb(sc, objs["knob"], 'ACTIVE', 'MESH', mass=0.02, friction=0.3)   # moderate mass ratio for Bullet
    _rb(sc, objs["dog_pawl"], 'ACTIVE', dog_shape, mass=0.004, friction=0.3)
    if dog_shape == 'COMPOUND':
        dog_compound(sc, objs["dog_pawl"], dog_angle)
    if token:
        _rb(sc, objs["token_0"], 'ACTIVE', 'CONVEX_HULL', mass=0.0025, friction=0.3)
    _rb(sc, drv, 'PASSIVE', 'CONVEX_HULL').kinematic = True
    drv.rigid_body.collision_collections[0] = False
    drv.rigid_body.collision_collections[19] = True
    # driver: rest, then turn at hand speed (360 deg in 2 s)
    drv.rotation_euler = (0, 0, 0)
    drv.keyframe_insert("rotation_euler", index=1, frame=1)
    drv.keyframe_insert("rotation_euler", index=1, frame=20)
    drv.rotation_euler = (0, radians(turn_to), 0)
    drv.keyframe_insert("rotation_euler", index=1, frame=20 + int(abs(turn_to) / 360.0 * 48) + 1)
    # torsion spring driver -> knob (free axis = constraint Z, aligned with world Y)
    e = bpy.data.objects.new("tt_spring", None)
    sc.collection.objects.link(e)
    e.location = drv.location.copy()
    e.rotation_euler = Euler((radians(-90), 0, 0))
    with _ctx(sc, e):
        bpy.ops.rigidbody.constraint_add(type='GENERIC_SPRING')
    c = e.rigid_body_constraint
    c.object1, c.object2, c.spring_type = drv, objs["knob"], 'SPRING2'
    for ax in "xyz":
        setattr(c, "use_limit_lin_" + ax, True)
        setattr(c, "limit_lin_%s_lower" % ax, 0.0)
        setattr(c, "limit_lin_%s_upper" % ax, 0.0)
    for ax in "xy":
        setattr(c, "use_limit_ang_" + ax, True)
        setattr(c, "limit_ang_%s_lower" % ax, 0.0)
        setattr(c, "limit_ang_%s_upper" % ax, 0.0)
    c.use_spring_ang_z, c.spring_stiffness_ang_z, c.spring_damping_ang_z = True, 0.08, 0.02
    c.disable_collisions = True
    # blocking pawl hinge on the bezel, axis along Y
    h = bpy.data.objects.new("tt_dog_hinge", None)
    sc.collection.objects.link(h)
    h.location = pivot
    h.rotation_euler = Euler((radians(-90), 0, 0))
    with _ctx(sc, h):
        bpy.ops.rigidbody.constraint_add(type='HINGE')
    hc = h.rigid_body_constraint
    hc.object1, hc.object2, hc.disable_collisions = objs["bezel"], objs["dog_pawl"], True
    sc.frame_set(1)
    return sc, objs, drv, main


def run(sc, objs, drv, main, frames=150):
    """Step the test; return [(frame, driver_deg, knob_deg, dog_deg, token_z_mm)]."""
    trace = []
    for f in range(1, frames + 1):
        sc.frame_set(f)
        k = objs["knob"].matrix_world.to_euler('YXZ')[1]
        d = objs["dog_pawl"].matrix_world.to_euler('YXZ')[1]
        dv = drv.matrix_world.to_euler('YXZ')[1]
        tz = objs["token_0"].matrix_world.translation.z / MM if "token_0" in objs else None
        trace.append((f, round(degrees(dv), 1), round(degrees(k), 1), round(degrees(d), 2),
                      None if tz is None else round(tz, 1)))
    _win().scene = main
    return trace


def step(sc, objs, drv, f_end):
    """Advance the (active) test scene to f_end; returns trace rows for the new frames."""
    _win().scene = sc
    rows = []
    f = sc.frame_current
    while f < f_end:
        f += 1
        sc.frame_set(f)
        k = objs["knob"].matrix_world.to_euler('YXZ')[1]
        d = objs["dog_pawl"].matrix_world.to_euler('YXZ')[1]
        dv = drv.matrix_world.to_euler('YXZ')[1]
        tz = objs["token_0"].matrix_world.translation.z / MM if "token_0" in objs else None
        rows.append((f, round(degrees(dv), 1), round(degrees(k), 1), round(degrees(d), 2),
                     None if tz is None else round(tz, 1)))
    return rows


def handles(name=SCENE):
    sc = bpy.data.scenes[name]
    objs = {n: bpy.data.objects["tt_" + n] for n in COPIES if ("tt_" + n) in bpy.data.objects}
    return sc, objs, bpy.data.objects["tt_driver"]


def dog_compound(sc, dog, dog_angle):
    """Replace the pawl's concave mesh collider with a compound of convex pieces (nose, lever+hub,
    foot): Bullet handles convex pieces robustly, and the nose can still drop into the slit."""
    import bmesh
    from math import tan, cos, sin
    import mk
    import parts_token as T
    from params import DOG_TIP, DOG_NOSE_H, DOG_RAMP, DOG_Y0, DOG_Y1
    px, pz = T.dog_pivot()
    x0, x1 = DOG_TIP
    zb = T.Z_TIP + DOG_NOSE_H
    xr = x1 + DOG_NOSE_H * tan(radians(DOG_RAMP))
    hub = [(px + 4.5 * cos(a), pz + 4.5 * sin(a)) for a in [-1.5708 + 3.14159 * i / 12 for i in range(13)]]
    zf = T.foot_z()

    def under(x):
        return zb + (hub[0][1] - zb) * (x - xr) / (hub[0][0] - xr)

    pieces = {
        "nose": [(x0, T.Z_TIP), (x1, T.Z_TIP), (xr, zb + 0.2), (x0, zb + 0.2)],
        "lever": [(x0, zb), (xr, zb)] + hub + [(x0, zb + 6.0)],
        "foot": [(T.FOOT_X[0], zf), (T.FOOT_X[1], zf), (T.FOOT_X[1], under(T.FOOT_X[1]) + 0.3),
                 (T.FOOT_X[0], under(T.FOOT_X[0]) + 0.3)],
    }
    a = radians(-dog_angle)                    # front-view CCW = nose down; Blender +Y rot = CW
    kids = []
    for name, poly in pieces.items():
        rot = [(px + (x - px) * cos(a) - (z - pz) * sin(a), pz + (x - px) * sin(a) + (z - pz) * cos(a))
               for x, z in poly]
        bm = bmesh.new()
        mk.fv_prism(bm, rot, DOG_Y0, DOG_Y1)
        ch = mk.to_obj("tt_dog_" + name, bm, sc.collection)
        ch.parent = dog
        ch.matrix_parent_inverse = dog.matrix_basis.inverted()
        _rb(sc, ch, 'ACTIVE', 'CONVEX_HULL', mass=0.001, friction=0.3)
        ch.hide_render = True
        kids.append(ch)
    dog.rigid_body.collision_shape = 'COMPOUND'
    return kids
