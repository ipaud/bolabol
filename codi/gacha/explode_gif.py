"""Exploded-view animation of the assembled machine (G_fixed / G_moving collections) -> PNG frames.

    blender -b BolaBol-v1.blend --python codi/gacha/explode_gif.py -- OUT_DIR [still_frame]

Without still_frame it renders the whole loop; then: ffmpeg -framerate 24 -i OUT_DIR/f_%04d.png
-vf "fps=16,scale=600:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=160[p];[b][p]paletteuse=dither=bayer:bayer_scale=4"
-loop 0 docs/images/explode.gif
"""
import sys
import bpy
from mathutils import Vector

OUT = sys.argv[sys.argv.index("--") + 1]
STILL = int(sys.argv[sys.argv.index("--") + 2]) if len(sys.argv) > sys.argv.index("--") + 2 else None
MM = 0.001

# part -> (dx, dy, dz) in mm. Layers bottom -> top; the order of this list sets the stagger.
FRONT_A = ["coin_plate", "logo", "logo_sparkles_coral", "logo_sparkles_mint", "logo_sparkles_yellow", "knob"]
FRONT_B = ["coin_housing", "coin_wheel", "dog_pawl", "ratchet_pawl", "token_0"]
GEARS = ["gear_A", "gear_B_pinion", "pinion_axle", "deck_bracket", "hex_shaft", "spacer", "sleeve_rear"]
OFFS = [
    (["token_drawer", "token_1", "token_2"], (0, -230, 0)),
    (["outlet_door", "door_ear_0", "door_ear_1"], (0, -210, 0)),
    (["chute"], (-250, 0, 0)),
    (["mech_box"], (0, 0, 110)),
    (FRONT_B, (0, -150, 110)),
    (FRONT_A, (0, -290, 110)),
    (GEARS, (0, 250, 110)),
    (["deck"], (0, 0, 200)),
    (["shim_04"], (0, 0, 260)),
    (["crown_ring"], (0, 0, 280)),
    (["rotor"], (0, 0, 330)),
    (["funnel"], (0, 0, 440)),
    (["hood"], (0, 60, 500)),
    (["pillar_0"], (60, -60, 560)), (["pillar_1"], (60, 60, 560)),
    (["pillar_2"], (-60, 60, 560)), (["pillar_3"], (-60, -60, 560)),
    (["window_front"], (0, -230, 560)), (["window_back"], (0, 230, 560)),
    (["window_left"], (-230, 0, 560)), (["window_right"], (230, 0, 560)),
    (["lid"], (0, 0, 620)),
    (["topper"], (0, 0, 700)),
]
HOLD0, GO, HOLD1, BACK, HOLD2, DUR, STAGGER = 12, 40, 24, 40, 12, 36, 0.8
END = HOLD0 + GO + HOLD1 + BACK + HOLD2 + 20

sc = bpy.context.scene
if sc.rigidbody_world:
    sc.rigidbody_world.enabled = False
for lc in bpy.context.view_layer.layer_collection.children:
    if lc.name.startswith("Llit") or lc.name in ("G_capsules", "LLITS"):
        lc.exclude = True


for o in bpy.data.objects:
    if o.name.startswith(("capsule", "spare_shim")):
        o.hide_render = True


def part(name):
    return bpy.data.objects[name]


n = len(OFFS)
for rank, (names, off) in enumerate(OFFS):
    d = rank * STAGGER
    up0, down0 = HOLD0 + (n - rank) * STAGGER * 0 + d, HOLD0 + GO + HOLD1 + (n - rank) * STAGGER
    for nm in names:
        o = part(nm)
        base = Vector(o.location)
        o.location = base
        o.keyframe_insert("location", frame=1)
        for f, k in ((up0, 0), (up0 + DUR, 1), (down0, 1), (down0 + DUR, 0)):
            o.location = base + Vector(off) * MM * k
            o.keyframe_insert("location", frame=int(f))
        o.location = base

sc.frame_start, sc.frame_end = 1, END
sc.render.fps = 24
sc.render.engine = "BLENDER_EEVEE"
sc.eevee.taa_render_samples = 24
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 640, 800, 100
sc.render.image_settings.file_format = "PNG"

# camera: orthographic, 3/4 from front-left above, framing grows with the explosion
tgt = bpy.data.objects.new("explode_tgt", None)
sc.collection.objects.link(tgt)
cam = bpy.data.objects.new("explode_cam", bpy.data.cameras.new("explode_cam"))
sc.collection.objects.link(cam)
cam.data.type = "ORTHO"
cam.location = (-1700 * MM, -2300 * MM, 1500 * MM)
tc = cam.constraints.new("TRACK_TO")
tc.target, tc.track_axis, tc.up_axis = tgt, "TRACK_NEGATIVE_Z", "UP_Y"
sc.camera = cam
FULL = (HOLD0 + GO)
for f, scale, z in ((1, 580, 225), (HOLD0, 580, 225), (HOLD0 + GO, 1500, 520),
                    (HOLD0 + GO + HOLD1, 1500, 520), (HOLD0 + GO + HOLD1 + BACK + 14, 580, 225)):
    cam.data.ortho_scale = scale * MM
    cam.data.keyframe_insert("ortho_scale", frame=f)
    tgt.location = (0, 0, z * MM)
    tgt.keyframe_insert("location", frame=f)

if STILL:
    sc.frame_set(STILL)
    sc.render.filepath = f"{OUT}/still_{STILL:04d}.png"
    bpy.ops.render.render(write_still=True)
else:
    sc.render.filepath = f"{OUT}/f_"
    bpy.ops.render.render(animation=True)
