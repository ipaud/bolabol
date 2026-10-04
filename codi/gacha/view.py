"""Viewport helpers for inspection screenshots (not part of the model)."""
import bpy
from math import radians
from mathutils import Euler, Vector


def set_view(loc, dist, rot_deg, shading='SOLID', xray=False, ortho=False):
    for area in bpy.context.screen.areas:
        if area.type != 'VIEW_3D':
            continue
        sp = area.spaces.active
        r3d = sp.region_3d
        r3d.view_perspective = 'ORTHO' if ortho else 'PERSP'
        r3d.view_location = Vector(loc)
        r3d.view_distance = dist
        r3d.view_rotation = Euler([radians(a) for a in rot_deg]).to_quaternion()
        sp.shading.type = shading
        sp.shading.show_xray = xray
        sp.shading.color_type = 'MATERIAL'
        sp.overlay.show_floor = False
        sp.overlay.show_axis_x = sp.overlay.show_axis_y = False
        sp.clip_start, sp.clip_end = 0.001, 100.0


def show_only(names=None, hide=()):
    """Show only objects whose name starts with any prefix in `names` (None = all), minus `hide`."""
    root = bpy.data.collections.get("GACHA")
    for o in root.all_objects:
        vis = names is None or any(o.name.startswith(n) for n in names)
        vis = vis and not any(o.name.startswith(h) for h in hide)
        if o.hide_viewport:
            o.hide_viewport = False
        o.hide_set(not vis)


FRONT = (90, 0, 0)
SIDE_R = (90, 0, 90)
TOP = (0, 0, 0)
ISO = (62, 0, -35)
