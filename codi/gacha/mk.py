"""Mesh kit: bmesh builders (millimetres in, metres out) and object helpers."""
import bpy
import bmesh
from math import pi, sin, cos
from mathutils import Matrix, Vector
from params import MM

ROT_XZ = Matrix.Rotation(pi / 2, 4, 'X')   # 2D (x, y) -> front view (x, z); +Z extrusion -> -Y


# ---------- scene helpers ----------
def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def wipe(c):
    """Delete every object in collection c (and its children), including rigid body links."""
    for ch in list(c.children):
        wipe(ch)
        bpy.data.collections.remove(ch)
    for o in list(c.objects):
        me = o.data if o.type == 'MESH' else None
        bpy.data.objects.remove(o, do_unlink=True)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)


def mat(name, rgba, rough=0.45, metal=0.0, transmission=0.0, alpha=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = rgba
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Transmission Weight"].default_value = transmission
    b.inputs["Alpha"].default_value = alpha
    m.diffuse_color = (rgba[0], rgba[1], rgba[2], min(alpha, 1.0) if transmission == 0 else 0.35)
    if alpha < 1.0 or transmission > 0:
        try:
            m.surface_render_method = 'BLENDED'
        except Exception:
            pass
    return m


# ---------- bmesh primitives (all mm) ----------
def _ccw(pts):
    a = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
            for i in range(len(pts)))
    return pts if a > 0 else list(reversed(pts))


def prism(bm, pts, z0, z1):
    """Extrude a simple 2D polygon [(x, y)] between z0 and z1."""
    pts = _ccw(pts)
    bot = [bm.verts.new((x, y, z0)) for x, y in pts]
    top = [bm.verts.new((x, y, z1)) for x, y in pts]
    bm.faces.new(list(reversed(bot)))
    bm.faces.new(top)
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    return bot + top


def circle_pts(r, seg=64, cx=0.0, cy=0.0, a0=0.0):
    return [(cx + r * cos(a0 + 2 * pi * i / seg), cy + r * sin(a0 + 2 * pi * i / seg)) for i in range(seg)]


def cyl(bm, r, z0, z1, seg=64, cx=0.0, cy=0.0):
    return prism(bm, circle_pts(r, seg, cx, cy), z0, z1)


def box(bm, x0, x1, y0, y1, z0, z1):
    return prism(bm, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1)


def lathe(bm, prof, seg=64, cx=0.0, cy=0.0):
    """Revolve a closed profile [(r, z)] about the vertical axis through (cx, cy)."""
    rings = []
    for r, z in prof:
        if r < 1e-6:
            rings.append([bm.verts.new((cx, cy, z))])
        else:
            rings.append([bm.verts.new((cx + r * cos(2 * pi * i / seg), cy + r * sin(2 * pi * i / seg), z))
                          for i in range(seg)])
    faces = []
    n = len(rings)
    for a in range(n):
        A, B = rings[a], rings[(a + 1) % n]
        if len(A) == 1 and len(B) == 1:
            continue
        for i in range(seg):
            j = (i + 1) % seg
            if len(A) == 1:
                faces.append(bm.faces.new((A[0], B[j], B[i])))
            elif len(B) == 1:
                faces.append(bm.faces.new((A[i], A[j], B[0])))
            else:
                faces.append(bm.faces.new((A[i], A[j], B[j], B[i])))
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    return [v for ring in rings for v in ring]


def frustum(bm, r0, r1, z0, z1, seg=64, cx=0.0, cy=0.0):
    return lathe(bm, [(0, z0), (r0, z0), (r1, z1), (0, z1)], seg, cx, cy)


def fv_prism(bm, pts_xz, y0, y1):
    """Front-view polygon [(x, z)] extruded along Y from y0 to y1."""
    vs = prism(bm, pts_xz, -y1, -y0)
    bmesh.ops.transform(bm, matrix=ROT_XZ, verts=vs)
    return vs


YZ = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))   # 2D (y, z), extrusion along X


def yz_prism(bm, pts_yz, x0, x1):
    """Side-view polygon [(y, z)] extruded along X from x0 to x1."""
    vs = prism(bm, pts_yz, x0, x1)
    bmesh.ops.transform(bm, matrix=YZ, verts=vs)
    return vs


def fv_cyl(bm, r, y0, y1, cx=0.0, cz=0.0, seg=64):
    return fv_prism(bm, circle_pts(r, seg, cx, cz), y0, y1)


def fv_lathe(bm, prof, seg=64, cx=0.0, cz=0.0):
    """Revolve profile [(r, y)] about a Y-parallel axis through front-view point (cx, cz)."""
    vs = lathe(bm, [(r, -y) for r, y in prof], seg, cx, cz)
    bmesh.ops.transform(bm, matrix=ROT_XZ, verts=vs)
    return vs


# ---------- objects ----------
def to_obj(name, bm, collection, material=None, origin=(0.0, 0.0, 0.0)):
    """bm in absolute mm; object origin placed at `origin` (mm)."""
    o = Vector(origin)
    bmesh.ops.translate(bm, vec=-o, verts=bm.verts)
    bmesh.ops.scale(bm, vec=(MM, MM, MM), verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = o * MM
    collection.objects.link(ob)
    if material is not None:
        me.materials.append(material)
    return ob


def tmp(bm, name="_cut"):
    return to_obj(name, bm, bpy.context.scene.collection)


def apply_mods(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    name = old.name
    bpy.data.meshes.remove(old)
    me.name = name


def boolean(target, cutters, op='DIFFERENCE'):
    """Apply one boolean against a list of cutter objects (deleted afterwards)."""
    if not cutters:
        return target
    c = bpy.data.collections.new("_bool")
    bpy.context.scene.collection.children.link(c)
    for ob in cutters:
        for uc in list(ob.users_collection):
            uc.objects.unlink(ob)
        c.objects.link(ob)
    backup = target.data.copy()
    for solver in ('MANIFOLD', 'EXACT'):
        mod = target.modifiers.new("bool", 'BOOLEAN')
        mod.operation, mod.solver = op, solver
        mod.operand_type, mod.collection = 'COLLECTION', c
        apply_mods(target)
        if len(target.data.polygons) > 0:
            break
        old = target.data
        target.data = backup.copy()
        bpy.data.meshes.remove(old)
    bpy.data.meshes.remove(backup)
    for ob in cutters:
        me = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.meshes.remove(me)
    bpy.data.collections.remove(c)
    return target


def build(name, collection, material=None, origin=(0, 0, 0), add=(), union_parts=(), cut=(), inter=()):
    """Compose a part from bmesh builder callables (absolute mm):
    `add` joined as-is (must not overlap), `union_parts` boolean-unioned, `cut` subtracted,
    `inter` intersected one by one. Cutters live in world space, so the part origin can sit
    anywhere (e.g. on its rotation axis)."""
    bm = bmesh.new()
    for f in add:
        f(bm)
    ob = to_obj(name, bm, collection, material, origin)

    def mk_cutter(f):
        b = bmesh.new()
        f(b)
        return tmp(b)

    for group, op in ((union_parts, 'UNION'), (cut, 'DIFFERENCE')):
        boolean(ob, [mk_cutter(f) for f in group], op)
    for f in inter:
        boolean(ob, [mk_cutter(f)], 'INTERSECT')
    return ob


def turn_y(ob, deg, cx=0.0, cz=0.0):
    """Turn geometry and origin deg clockwise (front view) about the Y-parallel axis through
    front-view point (cx, cz) mm. rotation_euler stays zero, so the rig still solves from 0."""
    r = Matrix.Rotation(deg * pi / 180.0, 4, 'Y')
    ob.data.transform(r)
    c = Vector((cx, 0.0, cz)) * MM
    ob.location = c + r.to_3x3() @ (ob.location - c)
    return ob


def smooth(ob, angle_deg=35.0):
    me = ob.data
    try:
        me.shade_smooth()
        me.set_sharp_from_angle(angle=angle_deg * pi / 180.0)
    except Exception:
        pass


def recenter(ob):
    """Move the object origin to its vertex centroid (Bullet uses the origin as centre of mass),
    keeping the geometry where it is. Makes the mesh single-user first."""
    if ob.data.users > 1:
        ob.data = ob.data.copy()
    me = ob.data
    n = len(me.vertices)
    c = sum((v.co for v in me.vertices), Vector()) / max(n, 1)
    me.transform(Matrix.Translation(-c))
    ob.location = ob.matrix_basis @ c              # matrix_basis is always current (no parents here)
    return c


def swept(bm, pts_xz, y0, dz0, y1, dz1):
    """Planar polygon [(x, z)] swept straight from plane y=y0 (z offset dz0) to y=y1 (offset dz1)."""
    r0 = [bm.verts.new((x, y0, z + dz0)) for x, z in pts_xz]
    r1 = [bm.verts.new((x, y1, z + dz1)) for x, z in pts_xz]
    faces = [bm.faces.new(r0), bm.faces.new(list(reversed(r1)))]
    n = len(pts_xz)
    for i in range(n):
        j = (i + 1) % n
        faces.append(bm.faces.new((r0[i], r0[j], r1[j], r1[i])))
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    return r0 + r1
