"""Assembly guides for the test kits as animated Blender scenes.

Parts (and screws, nuts, spring) appear in assembly order and slide in along their real insertion
path, one step per label, the camera orbiting to the side where the part goes in; the last step
runs the mechanism. Built from the machine parts (rest pose), so they match what was printed.
Pawl angles in the token test are solved against the real meshes (rig.pose) and baked.

    import muntatge; muntatge.build("proves_2"); muntatge.render_steps("proves_2", dir); muntatge.save("proves_2", path)
"""
import os
import bpy
import bmesh
from math import radians, cos, sin, pi
from mathutils import Matrix, Vector
import mk
from params import *

MOVE = (4, 30)              # appear -> start moving -> in place (frames into the step)

COL = {"jig": (0.80, 0.83, 0.88), "gearA": (1.00, 0.55, 0.20), "hex": (1.00, 0.84, 0.25),
       "gearB": (0.20, 0.72, 0.68), "axle": (0.35, 0.36, 0.40), "shim": (0.92, 0.22, 0.30),
       "crown": (0.62, 0.52, 0.90), "spare": (0.98, 0.62, 0.72), "text": (0.12, 0.12, 0.14),
       "sleeve": (0.30, 0.62, 0.95), "ratchet": (0.20, 0.72, 0.68), "rpawl": (0.95, 0.35, 0.55),
       "knob": (1.00, 0.45, 0.42), "bezel": (1.00, 0.93, 0.82), "dog": (0.62, 0.52, 0.90),
       "token": (0.95, 0.75, 0.25), "metal": (0.62, 0.64, 0.68)}


# --------------------------------------------------------------------------- hardware (machine mm)

def _screw(x, z, y0, length, flat=False):
    """M3 along +Y. Socket head: bearing face at y0, head in front. Flat head: top flush at y0."""
    def f(bm):
        if flat:
            mk.fv_lathe(bm, [(0, y0), (3.0, y0), (1.5, y0 + 1.5), (0, y0 + 1.5)], 24, x, z)
            mk.fv_cyl(bm, 1.5, y0 + 1.49, y0 + length, x, z, 16)
        else:
            mk.fv_cyl(bm, 2.75, y0 - 3.0, y0, x, z, 24)
            mk.fv_cyl(bm, 1.5, y0 - 0.01, y0 + length, x, z, 16)
    return f


def _nut(x, z, y0):
    from parts_drive import hex_pts
    return lambda bm: mk.fv_prism(bm, hex_pts(5.5, x, z, 30.0), y0, y0 + 2.4)


def _hw(name, fns, root, coll):
    bm = bmesh.new()
    for f in fns:
        f(bm)
    ob = mk.to_obj(name, bm, coll, _mat("metal"))
    ob.parent, ob.matrix_parent_inverse = root, Matrix.Identity(4)
    return ob


def _spring(name, x, y, z0, z1, root, coll, r=2.4, turns=7):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions, cu.bevel_depth, cu.bevel_resolution = '3D', 0.00035, 3
    sp = cu.splines.new('POLY')
    n = turns * 24
    sp.points.add(n)
    for i, p in enumerate(sp.points):
        a = 2 * pi * turns * i / n
        p.co = (x * MM + r * MM * cos(a), y * MM + r * MM * sin(a), (z0 + (z1 - z0) * i / n) * MM, 1.0)
    cu.materials.append(_mat("metal"))
    ob = bpy.data.objects.new(name, cu)
    coll.objects.link(ob)
    ob.parent, ob.matrix_parent_inverse = root, Matrix.Identity(4)
    return ob


# --------------------------------------------------------------------------- tests (last steps)

def _key_rot(ob, f, deg, index=1):
    ob.rotation_euler[index] = radians(deg)
    ob.keyframe_insert("rotation_euler", index=index, frame=f)


def _gear_test(sc, obs, st):
    """Turn gear A back and forth: B/pinion and the crown sector follow (sector teeth span +-33 deg)."""
    t0 = st[-1]
    hexo = obs["hexagon"]
    for f, a in ((t0 + 10, 0.0), (t0 + 50, 140.0), (t0 + 110, -140.0), (t0 + 140, 0.0)):
        _key_rot(hexo, f, a)
    _drive(obs["engranatge_A"], 1, hexo, "t")
    _drive(obs["engranatge_B_pinyo"], 1, hexo, "-t")
    _drive(obs["sector_corona"], 2, hexo, "t*%d/%d" % (Z_PIN, Z_CROWN))


def _pawls(turn, token):
    """Both pawl angles (deg) at a handle angle, solved on the machine parts of the main scene."""
    import rig
    dog, rat = rig.pose(turn, token=token)
    return dog or 0.0, rat or 0.0


def _token_test(sc, obs, st):
    """Step 5: shaft alone, ratchet clicks forward and stops backwards. Step 10: token lock cycle."""
    import rig
    t0, part_t0 = st[-1], st[4]
    win = bpy.context.window
    prev = win.scene
    win.scene = bpy.data.scenes["Scene"]               # rig.pose works on the main scene's parts
    rig.add_drivers()
    knob = bpy.data.objects["knob"]                    # the gravity test keyed the knob: mute it
    ad = knob.animation_data
    stash = ad.action if ad else None
    if ad:
        ad.action = None
    hexo, rat, dog, tok = obs["hexagono"], obs["uña_trinquete"], obs["uña_bloqueo"], obs["ficha"]
    for n in ("casquillo", "trinquete", "pomo"):
        _drive(obs[n], 1, hexo, "t")
    _drive(tok, 1, hexo, "min(t, %f)" % radians(185.0))  # the token leaves the slit at 6 o'clock
    try:
        # step 5: +90 deg forward (smooth back-off zone, then clicks); backwards it stops at once
        track = [(0, 0.0), (40, 90.0), (50, 88.5), (70, 88.5)]
        for (fa, aa), (fb, ab) in zip(track, track[1:]):
            for f in range(fa, fb + 1, 2):
                a = aa + (ab - aa) * (f - fa) / max(fb - fa, 1)
                _key_rot(hexo, part_t0 + f, a)
                _key_rot(rat, part_t0 + f, _pawls(a, False)[1])
        _key_rot(hexo, st[5] - 2, 0.0)                 # back home (pawl lifted by hand) before the knob
        _key_rot(rat, st[5] - 2, _pawls(0.0, False)[1])
        # step 10: blocked without a token, insert it, one full turn, it drops out, locked again
        d_lock, r0 = _pawls(0.0, False)
        d_try, _ = _pawls(1.4, False)
        d_up, _ = _pawls(0.0, True)
        for f, a, d in ((t0 - 1, 0.0, d_lock), (t0 + 8, 1.4, d_try), (t0 + 16, 0.0, d_lock)):
            _key_rot(hexo, f, a)
            _key_rot(dog, f, d)
            _key_rot(rat, f, r0)
        seat = Vector(tok.location)
        _show_from(tok, t0 + 18)
        tok.location = seat + Vector((0, 0, 32)) * MM
        tok.keyframe_insert("location", frame=t0 + 20)
        tok.location = seat
        tok.keyframe_insert("location", frame=t0 + 40)
        _key_rot(dog, t0 + 30, d_lock)
        _key_rot(dog, t0 + 40, d_up)
        drop = None
        for k, f in enumerate(range(t0 + 44, t0 + 141, 2)):
            a = 360.0 * k / 48.0
            token_in = a < 185.0
            if not token_in and drop is None:
                drop = f
            d, r = _pawls(a, token_in)
            _key_rot(hexo, f, a)
            _key_rot(dog, f, d)
            _key_rot(rat, f, r)
        tok.keyframe_insert("location", frame=drop)
        tok.location = seat + Vector((0, 0, -60)) * MM
        tok.keyframe_insert("location", frame=drop + 8)
        for f, hide in ((drop + 8, False), (drop + 9, True)):
            tok.hide_viewport = tok.hide_render = hide
            tok.keyframe_insert("hide_viewport", frame=f)
            tok.keyframe_insert("hide_render", frame=f)
        d_end, r_end = _pawls(360.0, False)
        for f, a in ((t0 + 150, 360.0), (t0 + 156, 361.4), (t0 + 162, 360.0)):
            _key_rot(hexo, f, a)
            _key_rot(dog, f, d_end)
            _key_rot(rat, f, r_end)
    finally:
        rig.pose(0.0, token=True)
        if ad:
            ad.action = stash
        win.scene = prev


def _token_hw(root, coll):
    """Screws, nuts and pen spring of the token kit: (object, step, start offset mm)."""
    zh = Z_HANDLE
    _, _, _, P = ratchet_pawl_geom()
    dx, dz = dog_pivot()
    rp = 0.5 * (BEZEL_R0 + BEZEL_R1)
    bez = [(fv(rp, a)[0], zh + fv(rp, a)[1]) for a in (90.0, 240.0, 330.0)]
    yb = KNOB_Y1 - GRIP_D
    out = [
        (_hw("tornillo_uña_trinquete", [_screw(P[0], P[1], YFO, 16.0, flat=True)], root, coll), 2, (0, -30, 0)),
        (_hw("tuerca_uña_trinquete", [_nut(P[0], P[1], RAT_Y1 + 0.2)], root, coll), 2, (0, 30, 0)),
        (_hw("tornillo_pomo", [_screw(0.0, zh, yb + 6.0, 20.0)], root, coll), 5, (0, -40, 0)),
        (_hw("tornillos_bisel", [_screw(x, z, KNOB_Y1 + 3.0, 40.0) for x, z in bez], root, coll), 6, (0, -40, 0)),
        (_hw("tuercas_bisel", [_nut(x, z, YF) for x, z in bez], root, coll), 6, (0, 30, 0)),
        (_hw("tornillo_pivote", [_screw(dx, dz, KNOB_Y1, 45.0)], root, coll), 8, (0, -50, 0)),
        (_hw("tuerca_pivote", [_nut(dx, dz, YF)], root, coll), 8, (0, 30, 0)),
    ]
    dogo = bpy.data.objects["dog_pawl"]
    loc = dogo.location * 1000.0
    stub_top = max(v.co.z * 1000.0 for v in dogo.data.vertices if abs(v.co.x * 1000.0 + loc.x - SPRING_X) < 1.8) + loc.z
    top = zh + BEZEL_R1 + 7.0 - 2.5                    # blind end of the pocket in the bezel hump
    ys = 0.5 * (DOG_Y0 + DOG_Y1)
    out.append((_spring("muelle", SPRING_X, ys, stub_top + 0.3, top - 0.3, root, coll), 7, (0, 0, -18)))
    return out


# --------------------------------------------------------------------------- guide definitions

GUIDES = {
    "proves_1": dict(
        scene="Muntatge_proves_1", title="Prova d'engranatges · muntatge", still="pas_%d.png",
        base_z=Z_HANDLE - 28.0 - 4.0, root_y=-0.042,
        kit=[("test_gear_jig", "plantilla", "jig", 0, None),
             ("gear_A", "engranatge_A", "gearA", 1, (0, 0, 60)),
             ("test_hex_coupon_gears", "hexagon", "hex", 2, (0, -45, 0)),
             ("gear_B_pinion", "engranatge_B_pinyo", "gearB", 3, (0, 0, 50)),
             ("pinion_axle", "eix_pinyo", "axle", 4, (0, 45, 0)),
             ("shim_04", "galga_04", "shim", 5, (0, 0, 40)),
             ("test_crown_sector", "sector_corona", "crown", 6, (0, 0, 50))],
        spares=[("spare_shim_02", "recanvi_galga_02", "spare", (-52.0, 30.0), 5),
                ("spare_shim_06", "recanvi_galga_06", "spare", (-52.0, -8.0), 5)],
        labels=[
            "1 · Plantilla a la taula. Neteja rebaves dels forats: eix Ø10.1 davant (lliure), Ø9.9 darrere (pressió)",
            "2 · Engranatge A (taronja) entre els dos suports, el cub cap enrere",
            "3 · Hexàgon pel forat gran del davant, travessant A fins al suport del darrere: ha de lliscar sense joc",
            "4 · Engranatge B + pinyó (verd) a dalt: B davant, engranant amb A; el pinyó cap enrere",
            "5 · Eix des del darrere (cap enrere): entra a pressió al suport posterior i lliure al davanter",
            "6 · Galga 0.4 (vermella) sobre la columna central",
            "7 · Sector de corona pel pivot, dents avall encaixant amb el pinyó",
            "8 · Gira l'engranatge A amb el dit: suau i amb poc joc.  S'encalla -> galga 0.6  ·  Balla o salta -> galga 0.2",
        ],
        durations=[36] * 7 + [150],
        cams=[(d, (-0.004, 0.030, 0.042)) for d in
              [(-0.8, -0.9, 0.75), (-1.0, -0.25, 0.65), (-0.75, -1.0, 0.45), (-1.0, -0.25, 0.7),
               (-0.8, 1.0, 0.5), (-0.8, -0.6, 0.95), (-0.9, -0.35, 0.8), (-1.0, -0.4, 0.6)]],
        cam_dist=0.42, test=_gear_test, hardware=None, stills={7: 50}),
    "proves_2": dict(
        scene="Muntatge_proves_2", title="Prueba de ficha · montaje", still="paso_%d.png",
        base_z=Z_HANDLE - 70.0, root_y=0.106,
        kit=[("test_token_jig", "plantilla", "jig", 0, None),
             ("sleeve_front", "casquillo", "sleeve", 1, (0, -40, 0)),
             ("ratchet_pawl", "uña_trinquete", "rpawl", 2, (0, 40, 0)),
             ("test_hex_coupon_token", "hexagono", "hex", 3, (0, -60, 0)),
             ("ratchet", "trinquete", "ratchet", 3, (0, 40, 0)),
             ("knob", "pomo", "knob", 5, (0, -60, 0)),
             ("bezel", "bisel", "bezel", 6, (0, -70, 0)),
             ("dog_pawl", "uña_bloqueo", "dog", 7, (22, 0, 22)),
             ("token_0", "ficha", "token", 9, "test")],
        spares=[("token_0", "ficha_recambio", "token", (58.0, -168.0), 0)],
        labels=[
            "1 · Plantilla de pie sobre su pata (la pata hacia atrás). Limpia los agujeros",
            "2 · Casquillo azul en el agujero grande: tiene que girar libre",
            "3 · Detrás: uña del trinquete con tornillo M3x16 de CABEZA PLANA desde delante, enrasado (avellana el agujero) + tuerca. Sin apretar: la uña cae sola",
            "4 · Hexágono desde delante por el casquillo (el agujerito hacia delante). Detrás, el trinquete: la cara que tocaba la cama hacia la placa",
            "5 · Prueba solo con la placa 2: gira el hexágono a derechas (visto de frente): tras unos 40° libres la uña hace clic; hacia atrás se bloquea",
            "6 · Placa 3: pomo en el hexágono, ranura arriba, y tornillo M3x20 por delante al agujerito del hexágono",
            "7 · Placa 3: bisel sobre el pomo, joroba arriba, con 3 tornillos M3x40 y tuercas detrás",
            "8 · Muelle de boli (~10 mm) en el alojamiento de la joroba y la uña de bloqueo en la ventana, debajo del muelle",
            "9 · Tornillo M3x45 del pivote: bisel -> uña -> placa -> tuerca, sin apretar. La uña cae en la ranura del pomo",
            "10 · Sin ficha no gira. Con la ficha en la ranura, una vuelta a derechas: cae abajo y se vuelve a bloquear. Si con la ranura arriba la uña del trinquete no está en su muesca, gira el trinquete una cara (60°)",
        ],
        durations=[36, 36, 40, 40, 74, 36, 40, 40, 36, 170],
        cams=[((-0.7, -1.0, 0.55), (0.0, -0.012, 0.061)), ((-0.35, -1.0, 0.35), (0.0, -0.012, 0.061)),
              ((-0.6, 1.0, 0.45), (-0.015, 0.006, 0.068)), ((-0.8, 0.9, 0.4), (0.0, -0.005, 0.061)),
              ((-0.35, 1.0, 0.35), (0.0, 0.006, 0.061)), ((-0.5, -1.0, 0.35), (0.0, -0.02, 0.061)),
              ((-0.6, -1.0, 0.5), (0.0, -0.02, 0.064)), ((0.55, -0.8, 0.9), (0.01, -0.025, 0.105)),
              ((0.6, -1.0, 0.45), (0.01, -0.02, 0.09)), ((-0.25, -1.0, 0.28), (0.0, -0.02, 0.066))],
        cam_dist=0.40, test=_token_test, hardware=_token_hw, stills={4: 40, 9: 74}),
}


# --------------------------------------------------------------------------- builder

def starts(g):
    out, s = [], 1
    for d in g["durations"]:
        out.append(s)
        s += d
    return out


def frames(g):
    return 1, starts(g)[-1] + g["durations"][-1] - 1


def _mat(key):
    m = bpy.data.materials.get("MG_" + key) or bpy.data.materials.new("MG_" + key)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = COL[key] + (1.0,)
    p.inputs["Roughness"].default_value = 0.3 if key == "metal" else 0.45
    p.inputs["Metallic"].default_value = 1.0 if key == "metal" else 0.0
    if key == "text":
        p.inputs["Emission Color"].default_value = COL[key] + (1.0,)
        p.inputs["Emission Strength"].default_value = 1.0
    m.diffuse_color = COL[key] + (1.0,)
    return m


def _copy(src, name, key, root, coll):
    s = bpy.data.objects[src]
    ob = bpy.data.objects.new(name, s.data)
    coll.objects.link(ob)
    ob.parent = root
    ob.matrix_parent_inverse = Matrix.Identity(4)
    ob.matrix_basis = s.matrix_basis.copy()          # rest pose in the machine frame
    ob.rotation_euler = (0, 0, 0)
    for slot in ob.material_slots:
        slot.link = 'OBJECT'
        slot.material = _mat(key)
    return ob


def _show_from(ob, frame):
    for f, hide in ((frame - 1, True), (frame, False)):
        ob.hide_viewport = ob.hide_render = hide
        ob.keyframe_insert("hide_viewport", frame=f)
        ob.keyframe_insert("hide_render", frame=f)


def _slide_in(ob, s, off):
    _show_from(ob, s)
    end = Vector(ob.location)
    ob.location = end + Vector(off) * MM
    ob.keyframe_insert("location", frame=s + MOVE[0])
    ob.location = end
    ob.keyframe_insert("location", frame=s + MOVE[1])


def _drive(ob, index, src, expr):
    d = ob.driver_add("rotation_euler", index).driver
    d.type = 'SCRIPTED'
    v = d.variables.new()
    v.name, v.type = "t", 'SINGLE_PROP'
    v.targets[0].id_type, v.targets[0].id = 'OBJECT', src
    v.targets[0].data_path = "rotation_euler[1]"
    d.expression = expr


def _text(name, body, cam, coll, loc, size, width=0.066):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body, cu.size = body, size
    cu.text_boxes[0].width = width               # wrap inside the frame
    ob = bpy.data.objects.new(name, cu)
    coll.objects.link(ob)
    cu.materials.append(_mat("text"))
    ob.parent = cam
    ob.location = loc
    return ob


def _panel(cam, coll):
    """Semi-transparent strip behind the step label, for legibility over the model."""
    m = bpy.data.materials.get("MG_panel") or bpy.data.materials.new("MG_panel")
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (1.0, 0.98, 0.96, 1.0)
    p.inputs["Alpha"].default_value = 0.78
    m.surface_render_method = 'BLENDED'
    bm = bmesh.new()
    for v in ((-0.036, -0.0203), (0.036, -0.0203), (0.036, -0.0100), (-0.036, -0.0100)):
        bm.verts.new((v[0], v[1], 0.0))
    bm.faces.new(bm.verts)
    me = bpy.data.meshes.new("panel")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    ob = bpy.data.objects.new("panel", me)
    coll.objects.link(ob)
    ob.parent = cam
    ob.location = (0.0, 0.0, -0.1002)
    return ob


def remove(key):
    g = GUIDES[key]
    sc = bpy.data.scenes.get(g["scene"])
    if sc:
        for ob in list(sc.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.scenes.remove(sc)
    c = bpy.data.collections.get(g["scene"])
    if c:
        bpy.data.collections.remove(c)


def build(key="proves_1"):
    import v2_concepts as V
    g = GUIDES[key]
    remove(key)
    sc = bpy.data.scenes.new(g["scene"])
    sc.unit_settings.system, sc.unit_settings.scale_length = 'METRIC', 1.0
    sc.render.fps = 24
    sc.frame_start, sc.frame_end = frames(g)
    coll = bpy.data.collections.new(g["scene"])
    sc.collection.children.link(coll)
    root = bpy.data.objects.new("kit", None)
    coll.objects.link(root)
    root.location = (0.0, g["root_y"], -(g["base_z"] + 9.0) * MM)      # kit standing on the studio floor
    st = starts(g)
    obs = {}
    for src, name, key_c, step, off in g["kit"]:
        ob = obs[name] = _copy(src, name, key_c, root, coll)
        if isinstance(off, tuple):
            _slide_in(ob, st[step], off)
    for src, name, key_c, (x, y), step in g["spares"]:            # spares lie on the table
        ob = _copy(src, name, key_c, root, coll)
        if src.startswith("token"):                                 # the token lies flat on the table
            c = sum((v.co for v in ob.data.vertices), Vector()) / len(ob.data.vertices)
            R = Matrix.Rotation(radians(90.0), 4, 'Y')
            target = Vector((x, y, g["base_z"] + TOKEN_T / 2)) * MM
            ob.matrix_basis = Matrix.Translation(target - (R @ c)) @ R
        else:
            c = sum((Vector(b) for b in bpy.data.objects[src].bound_box), Vector()) / 8.0
            ob.location = Vector((x, y, g["base_z"])) * MM - Vector((c.x, c.y, 0.0))
        if step:
            _show_from(ob, st[step])
    if g["hardware"]:
        for ob, step, off in g["hardware"](root, coll):
            _slide_in(ob, st[step], off)
    g["test"](sc, obs, st)
    V.stage(sc)
    for o in list(sc.collection.objects):                        # studio into the guide collection
        sc.collection.objects.unlink(o)
        coll.objects.link(o)
    cam = bpy.data.objects.new("cam_" + key, bpy.data.cameras.new("cam_" + key))
    coll.objects.link(cam)
    cam.data.lens, cam.data.clip_start = 50.0, 0.01          # labels float 0.1 m in front of the lens
    aim = bpy.data.objects.new("mira", None)
    coll.objects.link(aim)
    con = cam.constraints.new('TRACK_TO')
    con.target, con.track_axis, con.up_axis = aim, 'TRACK_NEGATIVE_Z', 'UP_Y'
    for i, (d, a) in enumerate(g["cams"]):                    # orbit to each step's side, then hold
        s = st[i]
        e = s + g["durations"][i] - 1
        aim.location = a
        cam.location = Vector(a) + Vector(d).normalized() * g["cam_dist"]
        for f in (s + 10 if i else 1, e):
            cam.keyframe_insert("location", frame=f)
            aim.keyframe_insert("location", frame=f)
    sc.camera = cam
    _text("titulo", g["title"], cam, coll, (-0.0335, 0.0165, -0.1), 0.0028)
    _panel(cam, coll)
    for i, body in enumerate(g["labels"]):
        t = _text("paso_%d" % (i + 1), body, cam, coll, (-0.0335, -0.0128, -0.1), 0.0018)
        s = st[i]
        e = s + g["durations"][i] if i < len(g["labels"]) - 1 else frames(g)[1] + 1
        for f, hide in ((1, True), (s, False), (e, True)):
            t.hide_viewport = t.hide_render = hide
            t.keyframe_insert("hide_viewport", frame=f)
            t.keyframe_insert("hide_render", frame=f)
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.eevee.taa_render_samples = 48
    return sc


def step_frames(key):
    """Frame shown for each step: parts in place; for test steps the frame given in `stills`."""
    g = GUIDES[key]
    st = starts(g)
    return [s + g["stills"][i] if i in g["stills"] else s + MOVE[1] + 3 for i, s in enumerate(st)]


def render_steps(key, folder):
    """One still per step. The guide scene is made the window scene while rendering: rendering an
    inactive scene evaluates its animation at the active scene's frame."""
    g = GUIDES[key]
    os.makedirs(folder, exist_ok=True)
    sc = bpy.data.scenes[g["scene"]]
    win = bpy.context.window
    prev = win.scene
    win.scene = sc
    paths = []
    try:
        for i, f in enumerate(step_frames(key)):
            sc.frame_set(f)
            sc.render.filepath = os.path.join(folder, g["still"] % (i + 1))
            bpy.ops.render.render(write_still=True)
            paths.append(sc.render.filepath)
    finally:
        win.scene = prev
    return paths


def video_settings(key, path):
    sc = bpy.data.scenes[GUIDES[key]["scene"]]
    ims = sc.render.image_settings
    if "media_type" in ims.bl_rna.properties:
        ims.media_type = 'VIDEO'
    ims.file_format = 'FFMPEG'
    sc.render.ffmpeg.format, sc.render.ffmpeg.codec = 'MPEG4', 'H264'
    sc.render.ffmpeg.constant_rate_factor = 'HIGH'
    sc.render.filepath = path
    sc.frame_set(1)


def save(key, path):
    """Guide scene alone in its own .blend (open it and press play)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.data.libraries.write(path, {bpy.data.scenes[GUIDES[key]["scene"]]}, fake_user=True)
    return path
