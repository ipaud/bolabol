"""V2 look concepts: same v1 mechanism, softer shell. Massing only, to pick a direction.

Builds scene 'V2_concepts' with three shells around the v1 knob, bezel and outlet door, fills
them with capsules and renders them. The v1 scene is not touched.

    import v2_concepts; v2_concepts.build(); v2_concepts.render("<dir>")
"""
import random
from math import pi, sin, cos, radians, atan2
import bmesh
import bpy
from mathutils import Matrix, Vector
import mk

A, B, CY = 106.8, 107.0, -1.25          # v1 outer half-width / half-depth / centre y (mm)
R = 44.0                                  # plan corner radius
FRONT = CY - B                            # front face y
SEG = 14
OFFSET = {"mochi": -340.0, "neko": 0.0, "capsula": 340.0}
PASTEL = ["#FFB3C7", "#B8E6D1", "#FFE29A", "#CDB4F5", "#A8D8FF", "#FFC8A2"]


# --------------------------------------------------------------------------- materials

def _lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]


def mat(name, hexcol, rough=0.5, glass=False):
    m = bpy.data.materials.get("V2_" + name) or bpy.data.materials.new("V2_" + name)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = _lin(hexcol)
    p.inputs["Roughness"].default_value = rough
    if glass:
        p.inputs["Transmission Weight"].default_value = 1.0
        p.inputs["Roughness"].default_value = 0.04
        p.inputs["IOR"].default_value = 1.49
        if hasattr(m, "use_raytrace_refraction"):
            m.use_raytrace_refraction = True
    m.diffuse_color = _lin(hexcol)
    return m


# --------------------------------------------------------------------------- geometry

def squircle(a, b, r, cy=CY, seg=SEG):
    pts = []
    for cx_, cy_, a0 in ((a - r, b - r, 0), (-(a - r), b - r, 90), (-(a - r), -(b - r), 180), (a - r, -(b - r), 270)):
        for i in range(seg + 1):
            t = radians(a0 + 90.0 * i / seg)
            pts.append((cx_ + r * cos(t), cy + cy_ + r * sin(t)))
    return pts


def fillet(z_edge, f, up=True, n=6):
    """Profile points (z, inset) rounding an edge at z_edge with radius f."""
    s = -1 if up else 1
    pts = [(z_edge + s * (f - f * sin(pi / 2 * i / n)), f - f * cos(pi / 2 * i / n)) for i in range(n + 1)]
    return pts if up else pts[::-1]          # always bottom to top


def loft(name, coll, material, prof, a=A, b=B, r=R, cy=CY):
    """Stack of squircle rings (z, inset) bridged into a closed solid."""
    bm = bmesh.new()
    rings = []
    for z, d in prof:
        pts = squircle(a - d, b - d, max(r - d, 0.5), cy)
        rings.append([bm.verts.new((x, y, z)) for x, y in pts])
    n = len(rings[0])
    for A_, B_ in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((A_[i], A_[j], B_[j], B_[i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _finish(mk.to_obj(name, bm, coll, material))


def lathe(name, coll, material, prof, cx=0.0, cy=CY, seg=64):
    bm = bmesh.new()
    mk.lathe(bm, prof, seg, cx, cy)
    return _finish(mk.to_obj(name, bm, coll, material))


def _finish(ob):
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.data.set_sharp_from_angle(angle=radians(35))
    return ob


def blob(name, coll, material, loc, size, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                     matrix=Matrix.Rotation(radians(rot[0]), 3, "X") @ Matrix.Rotation(radians(rot[2]), 3, "Z"))
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return _finish(mk.to_obj(name, bm, coll, material))


def tube(name, coll, material, pts, radius, taper=None):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius * 0.001
    cu.bevel_resolution = 6
    cu.use_fill_caps = True
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(pts) - 1)
    for i, (bp, p) in enumerate(zip(sp.bezier_points, pts)):
        bp.co = Vector(p) * 0.001
        bp.handle_left_type = bp.handle_right_type = "AUTO"
        if taper:
            bp.radius = 1.0 + (taper - 1.0) * i / (len(pts) - 1)
    ob = bpy.data.objects.new(name, cu)
    cu.materials.append(material)
    coll.objects.link(ob)
    return ob


def rounded_tri(p, rr, seg=10):
    """Triangle with corners rounded to rr, straight edges kept: incentre inset + disc."""
    P = [Vector(v) for v in p]
    if (P[1] - P[0]).cross(P[2] - P[0]) < 0:
        P.reverse()
    a, b, c = (P[1] - P[2]).length, (P[2] - P[0]).length, (P[0] - P[1]).length
    inc = (a * P[0] + b * P[1] + c * P[2]) / (a + b + c)
    rho = abs((P[1] - P[0]).cross(P[2] - P[0])) / (a + b + c)
    Q = [inc + (v - inc) * (1 - rr / rho) for v in P]
    out = []
    for i in range(3):
        e0, e1 = Q[i] - Q[i - 1], Q[(i + 1) % 3] - Q[i]
        t0, t1 = atan2(-e0.x, e0.y), atan2(-e1.x, e1.y)
        if t1 < t0:
            t1 += 2 * pi
        out += [(Q[i].x + rr * cos(t0 + (t1 - t0) * k / seg), Q[i].y + rr * sin(t0 + (t1 - t0) * k / seg))
                for k in range(seg + 1)]
    return out


# --------------------------------------------------------------------------- shared pieces

def body(coll, m_body, top_fillet=6.0):
    prof = [(0.0, 6.0), (6.0, 0.0), (116.0, 0.0), (116.6, 1.0), (117.4, 1.0), (118.0, 0.0)] \
        + fillet(230.0, top_fillet)
    return loft("body", coll, m_body, prof)


def feet(coll, m, h=9.0, small=False):
    k = 38.0
    for i, (sx, sy) in enumerate(((1, 1), (-1, 1), (1, -1), (-1, -1))):
        lathe("foot_%d" % i, coll, m, [(0, -h), (13, -h), (15, -h + 2), (15, 0.5), (0, 0.5)],
              sx * (A - k), CY + sy * (B - k), 32)


def front_parts(coll, m_knob, m_bezel, m_frame, m_glass):
    for name, m in (("knob", m_knob), ("bezel", m_bezel), ("outlet_door", m_glass)):
        src = bpy.data.objects[name]
        ob = bpy.data.objects.new("v2_" + name, src.data)
        ob.matrix_world = src.matrix_basis.copy()        # rest pose, not the rig / physics frame
        coll.objects.link(ob)
        for s in ob.material_slots:
            s.link = "OBJECT"
            s.material = m
    # pill frame around the capsule outlet (v1 outlet is left of the knob) + token drawer front
    bm = bmesh.new()
    outer = rounded_rect(98, 98, 34, -49.0, 48.0)
    inner = rounded_rect(82, 82, 26, -49.0, 48.0)
    vo = [bm.verts.new((x, FRONT - 3.0, z)) for x, z in outer]
    vi = [bm.verts.new((x, FRONT - 3.0, z)) for x, z in inner]
    vo2 = [bm.verts.new((x, FRONT + 0.5, z)) for x, z in outer]
    vi2 = [bm.verts.new((x, FRONT + 0.5, z)) for x, z in inner]
    n = len(outer)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((vo[i], vo[j], vi[j], vi[i]))
        bm.faces.new((vo[i], vo2[i], vo2[j], vo[j]))
        bm.faces.new((vi[i], vi[j], vi2[j], vi2[i]))
        bm.faces.new((vo2[i], vi2[i], vi2[j], vo2[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _finish(mk.to_obj("outlet_frame", bm, coll, m_frame))
    bm = bmesh.new()
    mk.fv_prism(bm, rounded_rect(69.0, 25.0, 9.0, 23.0, 16.8), FRONT - 2.5, FRONT + 0.5)
    _finish(mk.to_obj("drawer_front", bm, coll, m_frame))
    blob("drawer_pull", coll, m_knob, (23.0, FRONT - 3.0, 16.8), (7.0, 4.0, 7.0))


def rounded_rect(w, h, r, cx, cz, seg=10):
    pts = []
    for ox, oz, a0 in ((w / 2 - r, h / 2 - r, 0), (-(w / 2 - r), h / 2 - r, 90),
                       (-(w / 2 - r), -(h / 2 - r), 180), (w / 2 - r, -(h / 2 - r), 270)):
        pts += [(cx + ox + r * cos(radians(a0 + 90 * i / seg)), cz + oz + r * sin(radians(a0 + 90 * i / seg)))
                for i in range(seg + 1)]
    return pts


def glass_band(coll, m_glass, z0, z1, inset=3.0, t=2.0):
    bm = bmesh.new()
    out, inn = squircle(A - inset, B - inset, R - inset), squircle(A - inset - t, B - inset - t, R - inset - t)
    ol, oh = [bm.verts.new((x, y, z0)) for x, y in out], [bm.verts.new((x, y, z1)) for x, y in out]
    il, ih = [bm.verts.new((x, y, z0)) for x, y in inn], [bm.verts.new((x, y, z1)) for x, y in inn]
    n = len(out)
    for i in range(n):
        j = (i + 1) % n
        for f in ((ol[i], ol[j], oh[j], oh[i]), (il[j], il[i], ih[i], ih[j]),
                  (ol[j], ol[i], il[i], il[j]), (oh[i], oh[j], ih[j], ih[i])):
            bm.faces.new(f)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _finish(mk.to_obj("window", bm, coll, m_glass))


def posts(coll, m, z0, z1, inset=10.0):
    for i, (sx, sy) in enumerate(((1, 1), (-1, 1), (1, -1), (-1, -1))):
        k = (R - inset) * 0.2929 + inset          # on the corner arc, `inset` inside
        x, y = sx * (A - k), CY + sy * (B - k)
        bm = bmesh.new()
        mk.cyl(bm, 5.0, z0, z1, 24, x, y)
        _finish(mk.to_obj("post_%d" % i, bm, coll, m))


def capsules(coll, region, n, seed):
    """region(x, y, z) -> inside?; z from the bottom up so the pile looks settled."""
    rnd = random.Random(seed)
    src = bpy.data.objects["cap_00"].data
    mats = [mat("cap%d" % i, h, 0.35) for i, h in enumerate(PASTEL)]
    placed, tries = [], 0
    zmin, zmax, span = region["z0"], region["z1"], region["span"]
    while len(placed) < n and tries < 20000:
        tries += 1
        z = zmin + (zmax - zmin) * rnd.random() ** 2
        p = Vector((rnd.uniform(-span, span), CY + rnd.uniform(-span, span), z))
        if not region["inside"](p) or any((p - q).length < 53.0 for q in placed):
            continue
        placed.append(p)
    for i, p in enumerate(placed):
        ob = bpy.data.objects.new("cap_v2_%02d" % i, src)
        ob.matrix_world = Matrix.Translation(p * 0.001) @ (
            Matrix.Rotation(rnd.uniform(0, 2 * pi), 4, "Z") @ Matrix.Rotation(rnd.uniform(-0.9, 0.9), 4, "X"))
        coll.objects.link(ob)
        ob.material_slots[1].link = "OBJECT"
        ob.material_slots[1].material = mats[i % len(mats)]
        ob.material_slots[0].link = "OBJECT"
        ob.material_slots[0].material = mat("cap_clear", "#FFFFFF", glass=True)


def squircle_inside(a, b, r, z0, z1):
    def f(p):
        if not (z0 <= p.z <= z1):
            return False
        x, y = abs(p.x), abs(p.y - CY)
        if x > a or y > b:
            return False
        if x > a - r and y > b - r:
            return (Vector((x - (a - r), y - (b - r)))).length <= r
        return True
    return f


# --------------------------------------------------------------------------- concepts

def mochi(coll):
    """Soft minimal: mint body, cream pillow lid, continuous clear band, coral accents."""
    cream, coral, mint = mat("cream", "#FFF3E2"), mat("coral", "#FF8C8C"), mat("mint", "#A6E3C9")
    glass = mat("glass", "#FFFFFF", glass=True)
    body(coll, mint)
    loft("rim", coll, cream, fillet(230.0, 4, up=False) + fillet(242.0, 4))
    glass_band(coll, glass, 242.0, 378.0)
    posts(coll, cream, 242.0, 378.0)
    loft("lid", coll, cream, fillet(378.0, 3, up=False) + fillet(412.0, 24))
    lathe("topper", coll, coral, [(0, 411), (14, 411), (15, 418), (12, 427), (6, 431), (0, 432)])
    feet(coll, cream)
    front_parts(coll, coral, cream, coral, glass)
    capsules(coll, dict(z0=272.0, z1=350.0, span=78.0, inside=squircle_inside(80, 80, 30, 272, 350)), 22, 3)


def neko(coll):
    """Character: pink body, cream cat head with ears and face, paws and tail."""
    cream, pink, dark = mat("cream", "#FFF3E2"), mat("pink", "#F8C3CF"), mat("eye", "#3B2B2B", 0.25)
    blush, white = mat("blush", "#FF9FB0"), mat("white", "#FFFFFF", 0.3)
    glass = mat("glass", "#FFFFFF", glass=True)
    body(coll, pink)
    loft("rim", coll, cream, fillet(230.0, 4, up=False) + fillet(242.0, 4))
    glass_band(coll, glass, 242.0, 372.0)
    posts(coll, cream, 242.0, 372.0)
    loft("head", coll, cream, fillet(372.0, 4, up=False) + fillet(442.0, 30))
    for s in (1, -1):
        tri = rounded_tri([(s * 28, 0), (s * 86, 0), (s * 70, 52)], 9)
        for name, pts, m, y0, y1, dz in (("ear", tri, cream, -9.0, 9.0, 0.0),
                                         ("ear_in", rounded_tri([(s * 40, 4), (s * 76, 4), (s * 66, 38)], 6), pink,
                                          -11.0, -8.0, 0.0)):
            bm = bmesh.new()
            mk.fv_prism(bm, [(x, z + 428.0 + dz) for x, z in pts], CY + y0, CY + y1)
            _finish(mk.to_obj("%s_%d" % (name, s), bm, coll, m))
        blob("eye_%d" % s, coll, dark, (s * 36, FRONT - 1.0, 397), (8.5, 3.0, 11.0))
        blob("glint_%d" % s, coll, white, (s * 36 - 3, FRONT - 3.6, 402), (2.6, 1.2, 2.6))
        blob("blush_%d" % s, coll, blush, (s * 64, FRONT - 0.6, 385), (11.0, 1.6, 6.0))
        blob("paw_%d" % s, coll, cream, (s * 58, FRONT + 6.0, 0.0), (20.0, 22.0, 9.0))
    tube("mouth", coll, dark, [(-9, FRONT - 1.2, 389), (-4.5, FRONT - 1.6, 384), (0, FRONT - 1.2, 388),
                               (4.5, FRONT - 1.6, 384), (9, FRONT - 1.2, 389)], 1.3)
    tail = [(60, CY + B - 3, 26), (100, CY + B + 12, 40), (124, CY + B + 8, 92), (132, CY + B - 2, 142),
            (146, CY + B - 6, 178), (162, CY + B + 2, 192)]             # rises up the side, tip curls out free
    tube("tail", coll, cream, tail, 8.0, taper=0.75)
    blob("tail_tip", coll, pink, tail[-1], (7.5, 7.5, 7.5))
    for i, (sx, sy) in enumerate(((1, 1), (-1, 1))):
        lathe("foot_b%d" % i, coll, cream, [(0, -9), (13, -9), (15, -7), (15, 0.5), (0, 0.5)],
              sx * (A - 38), CY + sy * (B - 38), 32)
    front_parts(coll, white, cream, blush, glass)
    capsules(coll, dict(z0=272.0, z1=345.0, span=78.0, inside=squircle_inside(80, 80, 30, 272, 345)), 20, 5)


def capsula(coll):
    """The machine as a giant capsule: lilac base, white seam band, clear dome, butter cap."""
    lilac, white, butter = mat("lilac", "#CDB8F2"), mat("white", "#FFFFFF", 0.3), mat("butter", "#FFE08A")
    glass = mat("glass", "#FFFFFF", glass=True)
    body(coll, lilac, top_fillet=18.0)
    lathe("seam", coll, white, [(0, 224), (103, 224), (106, 227), (106, 243), (103, 246), (0, 246)])
    dome = [(98.0, 246.0), (100.0, 246.0), (100.0, 296.0)] \
        + [(100.0 * cos(radians(a)), 296.0 + 100.0 * sin(radians(a))) for a in range(6, 91, 6)] \
        + [(0.0, 394.0)] + [(98.0 * cos(radians(a)), 296.0 + 98.0 * sin(radians(a))) for a in range(84, 5, -6)] \
        + [(98.0, 296.0)]
    lathe("dome", coll, glass, dome, seg=96)
    lathe("cap", coll, butter, [(0, 393), (22, 393), (24, 397), (20, 404), (10, 409), (0, 410)])
    feet(coll, white)
    front_parts(coll, butter, white, white, glass)
    capsules(coll, dict(z0=272.0, z1=330.0, span=78.0,
                        inside=lambda p: 262 <= p.z <= 336 and (p.xy - Vector((0, CY))).length < 70), 14, 7)


# --------------------------------------------------------------------------- scene + render

def build():
    old = bpy.data.scenes.get("V2_concepts")
    if old:
        for ob in list(old.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.scenes.remove(old)
    for c in [c for c in bpy.data.collections if c.name.startswith("V2_")]:
        bpy.data.collections.remove(c)
    sc = bpy.data.scenes.new("V2_concepts")
    sc.unit_settings.system, sc.unit_settings.scale_length = "METRIC", 1.0
    for key, fn in (("mochi", mochi), ("neko", neko), ("capsula", capsula)):
        coll = bpy.data.collections.new("V2_" + key)
        sc.collection.children.link(coll)
        fn(coll)
        root = bpy.data.objects.new("V2_root_" + key, None)
        coll.objects.link(root)
        for ob in coll.objects:
            if ob is not root:
                ob.parent = root
                ob.matrix_parent_inverse = Matrix.Identity(4)
        root.location = (OFFSET[key] * 0.001, 0, 0)
    stage(sc)
    return sc


def stage(sc):
    """Studio cyclorama (floor curving into a back wall) and soft area lights."""
    prof = [(-4.0, -0.009), (0.9, -0.009)] + [(0.9 + 0.9 * sin(pi / 2 * i / 12), 0.891 - 0.9 * cos(pi / 2 * i / 12))
                                             for i in range(1, 13)] + [(1.8, 4.0)]
    bm = bmesh.new()
    left = [bm.verts.new((-5.0, y, z)) for y, z in prof]
    right = [bm.verts.new((5.0, y, z)) for y, z in prof]
    for i in range(len(prof) - 1):
        bm.faces.new((left[i], right[i], right[i + 1], left[i + 1]))
    me = bpy.data.meshes.new("V2_cyc")
    bm.to_mesh(me)
    bm.free()
    for f in me.polygons:
        f.use_smooth = True
    me.materials.append(mat("floor", "#E8DFD8", 0.85))
    sc.collection.objects.link(bpy.data.objects.new("V2_cyc", me))
    w = sc.world or bpy.data.worlds.new("V2_world")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = _lin("#E8DFD8")
    bg.inputs["Strength"].default_value = 0.45
    for name, loc, energy, size in (("key", (-1.3, -1.7, 1.8), 160.0, 1.8), ("fill", (1.7, -1.1, 0.8), 55.0, 2.2),
                                    ("rim", (0.4, 1.2, 1.5), 70.0, 1.2)):
        li = bpy.data.lights.new("V2_" + name, "AREA")
        li.energy, li.size = energy, size
        lo = bpy.data.objects.new("V2_" + name, li)
        lo.location = loc
        lo.rotation_euler = (Vector((0, 0, 0.25)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(lo)
    sc.render.engine = "BLENDER_EEVEE"
    sc.view_settings.view_transform = "Standard"
    try:
        sc.eevee.use_raytracing = True
        sc.eevee.use_shadows = True
        sc.eevee.ray_tracing_options.resolution_scale = "1"     # sharp refraction through the windows
    except AttributeError:
        pass
    sc.view_settings.exposure = -1.6
    bg.inputs["Strength"].default_value = 0.35


def camera(sc, target, dist, lens=70.0, name="V2_cam"):
    cam = bpy.data.objects.get(name)
    if cam is None:
        cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        sc.collection.objects.link(cam)
    cam.data.lens = lens
    t = Vector(target)
    d = Vector((0.42, -1.0, 0.36)).normalized()
    cam.location = t + d * dist
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    return cam


def render(folder, which=("lineup", "mochi", "neko", "capsula"), res=(1600, 1100), samples=48):
    import os
    os.makedirs(folder, exist_ok=True)
    sc = bpy.data.scenes["V2_concepts"]
    sc.eevee.taa_render_samples = samples
    for w in which:
        if w == "lineup":
            camera(sc, (0, 0, 0.2), 2.75, 70)
            sc.render.resolution_x, sc.render.resolution_y = res
        else:
            camera(sc, (OFFSET[w] * 0.001, 0, 0.22), 1.35, 70)
            sc.render.resolution_x, sc.render.resolution_y = 1100, 1300
        sc.render.filepath = os.path.join(folder, "v2_%s.png" % w)
        bpy.ops.render.render(write_still=True, scene=sc.name)


# --------------------------------------------------------------------------- Mochi variants (flat windows)

def pillar_poly(sx, sy, r, t=7.0, ext=7.0, seg=SEG):
    """Corner pillar footprint: quarter of the squircle band (outer radius r, wall t) plus short flats."""
    cx, cy = sx * (A - r), CY + sy * (B - r)
    a0 = {(1, 1): 0, (-1, 1): 90, (-1, -1): 180, (1, -1): 270}[(sx, sy)]
    outer, inner = [], []
    for rr, dst in ((r, outer), (r - t, inner)):
        pts = [(cx + rr * cos(radians(a0 + 90.0 * i / seg)), cy + rr * sin(radians(a0 + 90.0 * i / seg)))
               for i in range(seg + 1)]
        u0 = Vector((-sin(radians(a0)), cos(radians(a0))))            # tangent at the arc start
        u1 = Vector((-sin(radians(a0 + 90)), cos(radians(a0 + 90))))  # tangent at the arc end
        dst += [tuple(Vector(pts[0]) - u0 * ext)] + pts + [tuple(Vector(pts[-1]) + u1 * ext)]
    return outer + inner[::-1]


def flat_windows(coll, m_glass, m_frame, r, z0, z1, t=7.0, ext=7.0):
    for i, (sx, sy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        bm = bmesh.new()
        mk.prism(bm, pillar_poly(sx, sy, r, t, ext), z0, z1)
        _finish(mk.to_obj("pillar_%d" % i, bm, coll, m_frame))
    hw, hd = A - r - ext + 1.0, B - r - ext + 1.0                      # 1 mm into the pillar slots
    for name, box in (("win_f", (-hw, hw, FRONT + 2.0, FRONT + 5.0)), ("win_b", (-hw, hw, CY + B - 5.0, CY + B - 2.0)),
                      ("win_l", (-A + 2.0, -A + 5.0, CY - hd, CY + hd)), ("win_r", (A - 5.0, A - 2.0, CY - hd, CY + hd))):
        bm = bmesh.new()
        mk.box(bm, box[0], box[1], box[2], box[3], z0, z1)
        _finish(mk.to_obj(name, bm, coll, m_glass))


def mochi_variant(coll, r_base, r_top, base_hex):
    cream, coral, mint = mat("cream", "#FFF3E2"), mat("coral", "#FF8C8C"), mat("mint", "#A6E3C9")
    glass = mat("glass", "#FFFFFF", glass=True)
    base = mat("base_" + base_hex[1:], base_hex)
    loft("base", coll, base, [(0.0, 6.0), (6.0, 0.0)] + fillet(117.0, 1.5), r=r_base)
    loft("upper", coll, mint, fillet(117.0, 1.5, up=False) + fillet(230.0, 6.0), r=r_top)
    loft("rim", coll, cream, fillet(230.0, 4, up=False) + fillet(242.0, 4), r=r_top)
    flat_windows(coll, glass, cream, r_top, 242.0, 378.0)
    loft("lid", coll, cream, fillet(378.0, 3, up=False) + fillet(412.0, 24), r=r_top)
    lathe("topper", coll, coral, [(0, 411), (14, 411), (15, 418), (12, 427), (6, 431), (0, 432)])
    k = max(r_base, 24.0)
    for i, (sx, sy) in enumerate(((1, 1), (-1, 1), (1, -1), (-1, -1))):
        lathe("foot_%d" % i, coll, cream, [(0, -9), (13, -9), (15, -7), (15, 0.5), (0, 0.5)],
              sx * (A - k), CY + sy * (B - k), 32)
    front_parts(coll, coral, cream, coral, glass)
    capsules(coll, dict(z0=272.0, z1=350.0, span=78.0, inside=squircle_inside(80, 80, 30, 272, 350)), 22, 3)


VARIANTS = {"uniforme": (17.0, 17.0, "#A6E3C9", -170.0), "bandeja": (17.0, 44.0, "#FFF3E2", 170.0)}


def build_variants():
    old = bpy.data.scenes.get("V2_mochi")
    if old:
        for ob in list(old.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.scenes.remove(old)
    for c in [c for c in bpy.data.collections if c.name.startswith("V2m_")]:
        bpy.data.collections.remove(c)
    sc = bpy.data.scenes.new("V2_mochi")
    sc.unit_settings.system, sc.unit_settings.scale_length = "METRIC", 1.0
    for key, (rb, rt, bh, off) in VARIANTS.items():
        coll = bpy.data.collections.new("V2m_" + key)
        sc.collection.children.link(coll)
        mochi_variant(coll, rb, rt, bh)
        root = bpy.data.objects.new("V2m_root_" + key, None)
        coll.objects.link(root)
        for ob in coll.objects:
            if ob is not root:
                ob.parent = root
                ob.matrix_parent_inverse = Matrix.Identity(4)
        root.location = (off * 0.001, 0, 0)
    stage(sc)
    return sc


def render_variants(folder, samples=128):
    import os
    os.makedirs(folder, exist_ok=True)
    sc = bpy.data.scenes["V2_mochi"]
    sc.eevee.taa_render_samples = samples
    shots = [("mochi_variantes", (0, 0, 0.21), 2.05, (1700, 1150))] + \
        [("mochi_" + k, (v[3] * 0.001, 0, 0.22), 1.35, (1100, 1300)) for k, v in VARIANTS.items()]
    for name, target, dist, res in shots:
        camera(sc, target, dist, 70, name="V2m_cam")
        sc.render.resolution_x, sc.render.resolution_y = res
        sc.render.filepath = os.path.join(folder, "v2_%s.png" % name)
        bpy.ops.render.render(write_still=True, scene=sc.name)
