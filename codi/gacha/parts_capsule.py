"""Two-piece capsule (50 x 54): clear top = outer sleeve with a snap groove, coloured bottom =
inner spigot with 4 bead segments (push to close, pull to open). Local frame: seam at z=0."""
from math import radians, cos, sin, asin, degrees, sqrt, pi
import bmesh
import mk
from params import *

RO = CAP_R
RI = CAP_R - CAP_WALL                 # sleeve inner / bottom inner
RSO = RI - CAP_GAP                    # spigot outer
RSI = RSO - CAP_WALL                  # spigot inner
B = CAP_BAND / 2
G0, G1 = 0.2, 2.05                    # groove span in the top half (local)
GR = RI + (CAP_BEAD_H - CAP_GAP) + 0.05


def arc(R, zc, a0, a1, n):
    return [(R * cos(radians(a0 + (a1 - a0) * i / n)), zc + R * sin(radians(a0 + (a1 - a0) * i / n)))
            for i in range(n + 1)]


def top_profile():
    p = [(RO, 0.0), (RO, B)] + arc(RO, B, 0, 90, 28)[1:]
    p += [(0.0, B + RI)] + arc(RI, B, 90, 0, 28)[1:]
    p += [(RI, G1), (GR, G1), (GR, G0), (RI, G0), (RI + 0.18, 0.0)]
    return p


def bottom_profile():
    at = degrees(asin((CAP_OVERLAP - B) / RSO))
    ai = degrees(asin((CAP_OVERLAP - B) / RSI))
    p = [(0.0, -(B + RO))] + arc(RO, -B, -90, 0, 28)[1:]
    p += [(RO, 0.0), (RSO, 0.0), (RSO, B)] + arc(RSO, B, 0, at, 6)[1:]
    # shoulder under the seam: the spigot (RSI..RSO) is inside the bowl bore (RI) and used to touch it only along
    # overlapping zero-thickness faces; printed rim down, the bowl started in mid-air 0.2 mm off the spigot
    p += arc(RSI, B, ai, 0, 6) + [(RSI, 0.0), (RSI, -0.4), (RI, -1.8), (RI, -B)] + arc(RI, -B, 0, -90, 28)[1:]
    return p


def lathe_arc(bm, prof, a0, a1, seg):
    rings = [[bm.verts.new((r * cos(a), r * sin(a), z)) for r, z in prof]
             for a in [radians(a0 + (a1 - a0) * i / seg) for i in range(seg + 1)]]
    faces = []
    n = len(prof)
    for A, Bv in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            faces.append(bm.faces.new((A[i], A[j], Bv[j], Bv[i])))
    faces.append(bm.faces.new(rings[0]))
    faces.append(bm.faces.new(list(reversed(rings[-1]))))
    bmesh.ops.recalc_face_normals(bm, faces=faces)


def beads(bm):
    prof = [(RSO - 0.3, 0.35), (RSO + CAP_BEAD_H, 0.9), (RSO + CAP_BEAD_H, 1.05), (RSO - 0.3, 1.95)]
    for k in range(CAP_BEAD_SEGS):
        c = 45.0 + 360.0 * k / CAP_BEAD_SEGS
        lathe_arc(bm, prof, c - CAP_BEAD_ARC / 2, c + CAP_BEAD_ARC / 2, 10)


def make_pair(C, M, center, open_gap=0.0):
    """Design pair as two objects, origins at the capsule centre (mm). open_gap lifts the top half."""
    cx, cy, cz = center
    top = mk.build("capsule_top", C['caps'], M['cap_clear'], origin=center,
                   add=[lambda bm: _placed(bm, top_profile(), cx, cy, cz + CAP_SEAM + open_gap)])
    bot = mk.build("capsule_bottom", C['caps'], M['cap_colors'][0], origin=center,
                   add=[lambda bm: _placed(bm, bottom_profile(), cx, cy, cz)],
                   union_parts=[lambda bm: _beads_at(bm, cx, cy, cz)])
    for o in (top, bot):
        mk.smooth(o, 40)
    return top, bot


def _placed(bm, prof, cx, cy, cz):
    return mk.lathe(bm, [(r, z + cz) for r, z in prof], 72, cx, cy)


def _beads_at(bm, cx, cy, cz):
    beads(bm)
    bmesh.ops.translate(bm, vec=(cx, cy, cz), verts=bm.verts)


def make_sim_mesh(C, M):
    """One joined mesh (top + bottom) shared by all simulated capsules; slot 1 colour is per object."""
    top, bot = make_pair(C, M, (0.0, 0.0, 0.0))
    import bpy
    me = bpy.data.meshes.new("capsule_mesh")
    bmj = bmesh.new()
    for o, slot in ((top, 0), (bot, 1)):
        tmp = o.data.copy()
        tmp.polygons.foreach_set("material_index", [slot] * len(tmp.polygons))
        bmj.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    bmj.to_mesh(me)
    bmj.free()
    me.materials.append(M['cap_clear'])
    me.materials.append(M['cap_colors'][0])
    for o in (top, bot):
        d = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.meshes.remove(d)
    return me
