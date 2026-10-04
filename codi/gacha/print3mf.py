"""Test-kit print plates as Flash Studio (Orca) 3MF projects, through the FlashPrep addon.

FlashPrep supplies the AD5M Pro project template, the PETG rules and the per-part analysis.
Its own export writes one object per 3MF, so this module orients the parts, lays out the
220x220 plates and writes one multi-object 3MF per plate. Where FlashPrep's heuristics misread
CAD parts (horizontal holes and hex bores read as "needs supports"), the reviewed setting wins
and the reason goes into the plate report (Metadata/FlashPrep_report.txt).

    import print3mf; print3mf.export_all("<project>/stl/proves")
"""
import json
import os
import subprocess
import uuid
import zipfile
from math import radians, cos, sin, pi
import numpy as np
import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.geometry import convex_hull_2d
import flashprep as fp

MATERIAL, PRIORITY = "PETG", "BALANCED"         # machine material; export_all(material="PLA") for cheap tests
DENSITY = {"PETG": "1.27"}                      # g/cm3 for the weight estimate; template default 1.24 = PLA
GAP, MARGIN = 5.0, 3.0                    # mm between parts / to the bed edge
FLASH_STUDIO = "/Applications/Flash Studio.app/Contents/MacOS/Flash Studio"

# local face that goes on the bed -> rotation
DOWN = {"-z": Matrix.Identity(3), "+z": Matrix.Rotation(radians(180), 3, "X"),
        "+y": Matrix.Rotation(radians(-90), 3, "X"), "-y": Matrix.Rotation(radians(90), 3, "X"),
        "+x": Matrix.Rotation(radians(90), 3, "Y"), "-x": Matrix.Rotation(radians(-90), 3, "Y")}

SUPPORT = {"enable_support": "1"}          # FlashPrep's own support parameters for that part are added
DOME = {"enable_support": "1", "support_critical_regions_only": "0"}   # the whole ceiling, not just "critical"

# (file, reference part for the plate settings, mechanical?, plate overrides, reason,
#  [(object, copy name, face on bed, spin deg, footprint centre on the bed (0,0 = centre), overrides, reason)])
# mechanical: FlashPrep's shape guess reads round CAD parts as organic; these are machine parts.
PLATES = [
    ("proves_1_engranatges", "test_gear_jig", True, {"layer_height": "0.20"},
     "capa 0.20: galgues 0.2/0.4/0.6 = 1/2/3 capes exactes", [
        ("test_crown_sector", None, "+z", 0, (-47.5, 46.5), None, "dents amunt"),
        ("test_gear_jig", None, "-z", 0, (76.0, 42.0), None,
         "forats horitzontals Ø10/Ø20 de 3-4 mm: fan pont, sense suports"),
        ("test_hex_coupon_gears", None, "-z", 0, (28.5, 80.0), None, "estirat sobre una cara, com l'eix real"),
        ("pinion_axle", None, "+y", 0, (28.5, 45.0), {"sparse_infill_density": "100%"},
         "dret sobre el cap: rodó i sense suports; 100% farciment (eix)"),
        ("gear_B_pinion", None, "-y", 0, (-85.0, -37.5), None,
         "engranatge B avall; con 40° sota el pinyó, puntes de dent en voladís 3.9 mm"),
        ("gear_A", None, "-y", 0, (-39.0, -37.5), None, "cara de l'engranatge avall, cub amunt"),
        ("shim_04", None, "-z", 0, (-90.0, -78.5), None, "2 capes"),
        ("spare_shim_02", None, "-z", 0, (-54.0, -78.5), None, "1 capa"),
        ("spare_shim_06", None, "-z", 0, (-18.0, -78.5), None, "3 capes"),
    ]),
    ("proves_2_fitxa_A", "test_token_jig", True, {}, None, [
        ("test_token_jig", None, "-y", 0, (-36.0, -36.0), None, "paret frontal avall, peu amunt"),
        ("ratchet", None, "-y", 0, (76.0, 76.0), None, "cara frontal avall"),
        ("dog_pawl", None, "+y", 0, (76.0, 25.0), None, "pla"),
        ("test_hex_coupon_token", None, "-z", 0, (-96.0, 80.0), None, "estirat sobre una cara"),
        ("token_0", None, "+x", 0, (-69.0, 80.0), None, "pla"),
        ("token_0", "token_0_b", "+x", 0, (-38.5, 80.0), None, "pla (recanvi)"),
        ("sleeve_front", None, "-y", 0, (-9.0, 80.0), None, "dret sobre un extrem"),
        ("ratchet_pawl", None, "-y", 0, (22.0, 80.0), None, "pla"),
    ]),
    ("proves_3_fitxa_B", "bezel", True, {}, None, [
        ("bezel", None, "+y", 0, (-46.0, -42.5), SUPPORT,
         "cara del darrere avall; suports NOMÉS a la finestra del gatet (sostre 45x22 mm, arc de 52 mm)"),
        ("knob", None, "+y", 0, (60.0, 60.0), None,
         "cara del darrere avall; el fons de l'hexàgon Ø16 fa pont, sense suports dins l'encaix"),
    ]),
    ("proves_4_capsula", "capsule_top", False, {}, None, [
        ("capsule_top", None, "-z", 0, (-30.0, 0.0), DOME, "vora avall; suports d'arbre per dins la cúpula"),
        ("capsule_bottom", None, "+z", 0, (30.0, 0.0), DOME,
         "vora avall; suports d'arbre per dins i sota el graó de 1.4 mm"),
    ]),
]

def coin_batch(name="monedes_x30", nx=6, ny=5, pitch=32.0):
    """Production plate of coins from token_0 of a 1-coin build (BBOL face on the bed, Boli up)."""
    rows = []
    for j in range(ny):
        for i in range(nx):
            k = j * nx + i
            rows.append(("token_0", None if k == 0 else "token_0_%02d" % (k + 1), "+x", 0,
                         ((i - (nx - 1) / 2) * pitch, (j - (ny - 1) / 2) * pitch), None,
                         "cara BBOL al llit (pont sobre el gravat), Boli amunt"))
    return (name, "token_0", True, {"brim_type": "no_brim"}, "llit de producció: %d monedes" % (nx * ny), rows)


# BOLABOL badge (v3 build): one plate, filament changes stored in the project
PLATES_LOGO = [
    ("bolabol_logo", "logo", True, {"layer_height": "0.20", "initial_layer_print_height": "0.20",
                                    "_colour_changes": [(1.4, "#EF5459"), (3.8, "#FCF7ED")]},
     "insígnia BOLABOL: base crema 0-1.2 mm, lletres corall 1.2-3.6 mm, brillantors crema 3.6-4.2 mm", [
        ("logo", None, "+y", 0, (0.0, 0.0), None, "cara del darrere avall; els canvis de filament ja són al projecte"),
    ]),
]

# chute on its own bed (llit 20): standing on its back, the only ceilings are the drop tube front wall (62 mm span,
# 64 mm up) and the cup lip (163 mm up); unsupported they bridge 62 mm and sag into the capsule path. Normal snug
# supports land inside the tube / cup, next to their open ends (tree: same result, 1h15 slower).
PLATES_CHUTE = [
    ("llit_20_chute", "chute", True, {"brim_type": "no_brim"},
     "chute sol: de peu sobre la cara del darrere, vora de 5 mm, suports només sota els dos sostres interiors", [
        ("chute", None, "+y", 0, (0.0, 0.0),
         dict(SUPPORT, brim_type="outer_only", brim_width="5", support_on_build_plate_only="0",
              support_type="normal(auto)", support_style="snug", support_threshold_angle="45"),
         "suports dins el tub de baixada i sota la pestanya de la cubeta: es treuen per la boca del tub i per la sortida"),
    ]),
]

# v3 hidden coin mech (build.main(mech="v3")): export_all(folder, plates=PLATES_V3)
PLATES_V3 = [
    ("proves_5_moneda_A", "test_coin_jig", True, {}, None, [
        ("test_coin_jig", None, "-z", 0, (0.0, 80.0), None,
         "peu avall, paret dreta: forat Ø22, ranura i forats de cargol horitzontals fan pont"),
        ("knob", None, "+y", 0, (-55.0, 25.0), None, "manovella: esquena plana avall, tapa i xamfrans amunt"),
        ("test_hex_coupon_coin", None, "-z", 90, (-70.0, -25.0), None, "estirat sobre una cara, com l'eix real"),
        ("dog_pawl", None, "+y", 0, (20.0, 25.0), None, "pla"),
        ("ratchet_pawl", None, "-y", 0, (55.0, 25.0), None, "pla"),
        ("token_0", None, "+x", 0, (-20.0, -25.0), None, "pla"),
        ("token_0", "token_0_b", "+x", 0, (15.0, -25.0), None, "pla (recanvi)"),
    ]),
    ("proves_6_moneda_B", "coin_housing", True, {}, None, [
        ("coin_housing", None, "-y", 0, (-55.0, -55.0), SUPPORT,
         "cara frontal avall; suports a la finestra del gatet i sota els sostres de l'embut i de la sortida"),
        ("coin_plate", None, "+y", 0, (-50.0, 50.0), None, "cara del darrere avall; rebaix i avellanats amunt"),
        ("coin_wheel", None, "+y", 0, (60.0, 50.0), None,
         "cara del darrere avall (dents al llit); la butxaca queda oberta amunt, sense suports"),
    ]),
]


# --------------------------------------------------------------------------- geometry

def local_arrays(ob):
    """Rest-shape mesh in mm, object rotation ignored (parts are modelled in the machine frame,
    rigged ones may be posed)."""
    me = ob.data
    me.calc_loop_triangles()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    tri = np.empty(len(me.loop_triangles) * 3, dtype=np.int32)
    me.loop_triangles.foreach_get("vertices", tri)
    return co.reshape(-1, 3) * 1000.0, tri.reshape(-1, 3)


def placed(ob, face, spin, centre):
    co, tri = local_arrays(ob)
    R = Matrix.Rotation(radians(spin), 3, "Z") @ DOWN[face]
    co = co @ np.array(R).T
    lo, hi = co.min(axis=0), co.max(axis=0)
    co -= np.array([(lo[0] + hi[0]) / 2 - centre[0], (lo[1] + hi[1]) / 2 - centre[1], lo[2]])
    return co, tri


def hull(co, grow=0.0):
    pts = co[:, :2]
    if grow:
        ring = np.array([(grow * cos(2 * pi * k / 16), grow * sin(2 * pi * k / 16)) for k in range(16)])
        pts = pts[convex_hull_2d([Vector(p) for p in pts])]
        pts = (pts[:, None, :] + ring[None]).reshape(-1, 2)
    return pts[convex_hull_2d([Vector(p) for p in pts])]


def _separated(a, b):
    for poly in (a, b):
        e = np.roll(poly, -1, axis=0) - poly
        for nx, ny in np.stack([-e[:, 1], e[:, 0]], axis=1):
            pa, pb = a @ (nx, ny), b @ (nx, ny)
            if pa.max() < pb.min() or pb.max() < pa.min():
                return True
    return False


def check_layout(items):
    """items: [(name, co)]. Returns problems: off the bed or closer than GAP to a neighbour."""
    bad = []
    hulls = [(n, hull(co, GAP / 2)) for n, co in items]
    lim = fp.BED_HALF - MARGIN
    for n, co in items:
        lo, hi = co[:, :2].min(axis=0), co[:, :2].max(axis=0)
        if lo.min() < -lim or hi.max() > lim:
            bad.append("%s fora del llit (%.1f..%.1f)" % (n, lo.min(), hi.max()))
        if co[:, 2].max() > fp.BED_HEIGHT:
            bad.append("%s massa alt" % n)
    for i, (na, ha) in enumerate(hulls):
        for nb, hb in hulls[i + 1:]:
            if not _separated(ha, hb):
                bad.append("%s i %s a menys de %.0f mm" % (na, nb, GAP))
    return bad


# --------------------------------------------------------------------------- FlashPrep

def _temp_object(name, co, tri, coll, max_edge=1.2):
    """Analysis copy with edges <= max_edge: FlashPrep slices the mesh and groups section segments
    on a 1.2 mm grid, so long CAD edges break the sections into fake islands (fake 'bottlenecks').
    max_edge=None: as is (section areas and perimeters, all the plate cooling needs, are exact)."""
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in co.tolist()]
    for f in tri.tolist():
        try:
            bm.faces.new([vs[i] for i in f])
        except ValueError:                  # duplicate face
            pass
    bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=bm.edges)       # boolean slivers
    bmesh.ops.triangulate(bm, faces=bm.faces)
    for _ in range(12 if max_edge else 0):
        long = [e for e in bm.edges if e.calc_length() > max_edge]
        if not long:
            break
        bmesh.ops.subdivide_edges(bm, edges=long, cuts=1, use_grid_fill=True)
        bmesh.ops.triangulate(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def _open_edges(tri):
    e = np.sort(np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]]), axis=1)
    return int((np.unique(e, axis=0, return_counts=True)[1] != 2).sum())


def _analyse(ob, mechanical, tri, material):
    dg = bpy.context.evaluated_depsgraph_get()
    a = fp.analyze(ob, dg, material)
    assert a["unit_factor"] == 1.0, "unit guess went wrong for %s" % ob.name
    a["non_manifold_edges"] = _open_edges(tri)   # of the mesh that is exported, not the analysis copy
    a["ripple_p95"] = 0.0                    # CAD surfaces: facets, no scan/AI noise
    if mechanical:
        a["shape"] = "MECHANICAL"
    return a, fp.decide(a, material, PRIORITY)


def _shells(lh):
    return {"top_shell_layers": str(max(4, int(round(0.8 / lh)))),
            "bottom_shell_layers": str(max(3, int(round(0.6 / lh))))}


def _cad_warnings(ws, a):
    # orientation hint: the orientations here are reviewed; "thin zones" on a shim = its Z thickness;
    # a "bottleneck" as thin as the part's own wall is a thin shell by design (capsule), not a neck
    skip = ("Otra orientación",) + (("Zonas de",) if a["height"] < 1.0 else ()) \
        + (("Cuello de botella",) if a["crit_dh"] < 2.5 * a["thick_median"] else ())
    return [w for w in ws if not w.startswith(skip)]


def plan_plate(plate, material=MATERIAL):
    """Analyse every part with FlashPrep and compose plate + per-object settings."""
    fname, ref, mechanical, plate_set, plate_why, rows = plate
    plate_set = dict(plate_set)
    colour_changes = plate_set.pop("_colour_changes", [])     # [(layer top z mm, new filament #hex)]
    coll = bpy.data.collections.new("_print3mf")
    bpy.context.scene.collection.children.link(coll)
    try:
        parts, items = [], []
        for obj, alias, face, spin, centre, over, reason in rows:
            co, tri = placed(bpy.data.objects[obj], face, spin, centre)
            name = alias or obj
            a, (s, fil, ranges, why, warn) = _analyse(_temp_object(name, co, tri, coll), mechanical, tri, material)
            parts.append(dict(name=name, co=co, tri=tri, a=a, s=s, fil=fil, ranges=ranges, why=why,
                              warn=_cad_warnings(warn, a), over=dict(over or {}), reason=reason, face=face))
            items.append((name, co))
        joined = _temp_object("plate", np.concatenate([p["co"] for p in parts]),
                              np.concatenate([p["tri"] + sum(len(q["co"]) for q in parts[:i])
                                              for i, p in enumerate(parts)]), coll, max_edge=None)
        pa, (ps, pfil, _, pwhy, pwarn) = _analyse(joined, mechanical, np.zeros((0, 3), int), material)
    finally:
        for ob in list(coll.objects):
            me = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.meshes.remove(me)
        bpy.data.collections.remove(coll)

    base = next(p for p in parts if p["name"] == ref)
    s, fil = dict(base["s"]), dict(base["fil"])
    why = ["Base: decisions FlashPrep per a %s" % ref] \
        + ["  " + w for w in base["why"] if not w.startswith(("Soportes", "Sin voladizos"))]
    sup = [p["name"] for p in parts if p["over"].get("enable_support") == "1"]
    why.append("Suports revisats per peça: " + (", ".join(sup) if sup else "cap (forats i encaixos fan pont)"))
    s.update(plate_set)
    s.update(_shells(float(s["layer_height"])))
    if plate_why:
        why.append(plate_why)
    # supports are per object: none at plate level
    for k in [k for k in s if k.startswith(("support_", "tree_support_"))]:
        s.pop(k)
    s["enable_support"] = "0"
    # cooling from the whole plate: all parts share every layer
    for k in ("slow_down_for_layer_cooling", "slow_down_layer_time", "slow_down_min_speed", "fan_cooling_layer_time"):
        if k in pfil:
            fil[k] = pfil[k]
        else:
            fil.pop(k, None)
    why += ["Placa sencera: " + w for w in pwhy if w.startswith("Capa mas corta")]
    if material in DENSITY:
        fil["filament_density"] = [DENSITY[material]]
        why.append("Densitat %s %s g/cm3 per a l'estimació de pes" % (material, DENSITY[material]))

    for p in parts:
        p["ranges"] = [] if "layer_height" in plate_set else p["ranges"]     # FlashPrep's fine-layer bands
        o = {}
        if int(p["s"]["wall_loops"]) > int(s["wall_loops"]):
            o["wall_loops"] = p["s"]["wall_loops"]
        if p["over"].get("enable_support") == "1":
            o.update({k: v for k, v in p["s"].items() if k.startswith(("support_", "tree_support_"))})
        o.update(p["over"])
        p["obj_settings"] = o
    warnings = [w for w in pwarn if "cabe" in w or "copias" in w]
    for p in parts:
        warnings += ["%s: %s" % (p["name"], w) for w in p["warn"]]
    return dict(file=fname + ("" if material == MATERIAL else "_" + material), material=material,
                ref=ref, parts=parts, s=s, fil=fil, why=why,
                warnings=warnings, layout=check_layout(items), plate_a=pa, colour_changes=colour_changes)


# --------------------------------------------------------------------------- report + 3MF

def report_text(plan):
    s = plan["s"]
    L = ["FlashPrep — %s (gachapon, peces de prova)" % plan["file"],
         "Material %s · Prioritat %s · capa %s mm · %s parets · farciment %s %s"
         % (plan["material"], PRIORITY, s["layer_height"], s["wall_loops"], s["sparse_infill_density"],
            s["sparse_infill_pattern"]), "", "Peces:"]
    for p in plan["parts"]:
        a = p["a"]
        L.append("  %s — cara %s al llit · %.0fx%.0fx%.1f mm · %.1f cm3 · apoiat %.0f mm2 · voladís %.0f mm2"
                 % (p["name"], p["face"], *a["dims"], a["volume_cm3"], a["contact_area"], a["overhang_area"]))
        L.append("      %s" % p["reason"])
        if p["obj_settings"]:
            L.append("      ajustos propis: " + ", ".join("%s=%s" % kv for kv in sorted(p["obj_settings"].items())))
        if p["ranges"]:
            L.append("      capa 0.12 a: " + ", ".join("%s-%s mm" % (lo, hi) for lo, hi, _ in p["ranges"]))
    L += ["", "Decisions:"] + ["  • " + w for w in plan["why"]]
    L += ["  • canvi de filament abans de la capa de %.2f mm -> %s" % cc for cc in plan.get("colour_changes", [])]
    L += ["", "Ajustos de placa:"] + ["  %s = %s" % kv for kv in sorted(s.items())]
    L += ["  %s = %s" % (k, v[0]) for k, v in sorted(plan["fil"].items())]
    if plan["warnings"]:
        L += ["", "Avisos FlashPrep:"] + ["  ⚠ " + w for w in plan["warnings"]]
    return "\n".join(L)


def _xml(t):
    return str(t).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def project_config(title, s, fil):
    with open(fp.TEMPLATE_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    known = set(cfg)
    s = {k: v for k, v in s.items() if k in known}
    fil = {k: v for k, v in fil.items() if k in known}
    cfg.update(s)
    cfg.update(fil)
    cfg["print_settings_id"] = "FlashPrep %s" % title
    cfg["inherits_group"][0] = fp.BASE_PRINT_PRESET
    diff = cfg["different_settings_to_system"]
    diff[0] = ";".join(sorted(set(filter(None, diff[0].split(";"))) | set(s)))
    diff[1] = ";".join(sorted(set(filter(None, diff[1].split(";")))
                              | {k for k in fil if k not in ("filament_settings_id", "filament_type")}))
    return cfg


def colour_change_xml(changes):
    """Orca / Bambu per-layer custom G-code, type 1 = pause (machine_pause_gcode: PAUSE on the AD5M Pro,
    whose profile has no colour-change G-code) before that layer: swap the filament, resume."""
    rows = "".join('<layer top_z="%.2f" type="1" extruder="1" color="%s" extra="" gcode="PAUSE"/>\n' % c
                   for c in changes)
    return ('<?xml version="1.0" encoding="utf-8"?>\n<custom_gcodes_per_layer>\n<plate>\n<plate_info id="1"/>\n'
            + rows + '<mode value="SingleExtruder"/>\n</plate>\n</custom_gcodes_per_layer>\n')


def write_3mf(path, plan):
    """Bambu/Orca project: one object per part (own name, own settings), all on plate 1."""
    NS = fp.NS
    objs, res, build, settings, inst, asm = [], [], [], [], [], []
    for k, p in enumerate(plan["parts"]):
        mid, oid = 2 * k + 1, 2 * k + 2
        co = p["co"]
        lo, hi = co.min(axis=0), co.max(axis=0)
        c = np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2])
        loc = co - c                                         # Orca: local origin at the bbox centre
        v = "\n".join('     <vertex x="%.5f" y="%.5f" z="%.5f"/>' % tuple(q) for q in loc.tolist())
        t = "\n".join('     <triangle v1="%d" v2="%d" v3="%d"/>' % tuple(q) for q in p["tri"].tolist())
        objs.append(("3D/Objects/object_%d.model" % (k + 1),
                     '<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" %s>\n'
                     ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n'
                     '  <object id="%d" p:UUID="%s" type="model">\n   <mesh>\n    <vertices>\n%s\n    </vertices>\n'
                     '    <triangles>\n%s\n    </triangles>\n   </mesh>\n  </object>\n </resources>\n <build/>\n</model>\n'
                     % (NS, mid, uuid.uuid4(), v, t)))
        tr = "1 0 0 0 1 0 0 0 1 %.6f %.6f %.6f" % tuple(c)
        res.append('  <object id="%d" p:UUID="%s" type="model">\n   <components>\n'
                   '    <component p:path="/3D/Objects/object_%d.model" objectid="%d" p:UUID="%s" '
                   'transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n   </components>\n  </object>\n'
                   % (oid, uuid.uuid4(), k + 1, mid, uuid.uuid4()))
        build.append('  <item objectid="%d" p:UUID="%s" transform="%s" printable="1"/>\n' % (oid, uuid.uuid4(), tr))
        meta = "".join('    <metadata key="%s" value="%s"/>\n' % (kk, _xml(vv))
                       for kk, vv in sorted(p["obj_settings"].items()))
        n = _xml(p["name"])
        rng = ""
        if p["ranges"]:
            rng = "    <layer_config_ranges>\n" + "".join(
                '     <range min_z="%s" max_z="%s">\n      <option opt_key="extruder">0</option>\n'
                '      <option opt_key="layer_height">%s</option>\n     </range>\n' % r for r in p["ranges"]) \
                + "    </layer_config_ranges>\n"
        settings.append(
            '  <object id="%d">\n    <metadata key="name" value="%s"/>\n    <metadata key="extruder" value="1"/>\n%s'
            '    <metadata face_count="%d"/>\n    <part id="%d" subtype="normal_part">\n'
            '      <metadata key="name" value="%s"/>\n'
            '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
            '      <metadata key="source_file" value="gachapon.blend"/>\n'
            '      <metadata key="source_object_id" value="%d"/>\n      <metadata key="source_volume_id" value="0"/>\n'
            '      <mesh_stat face_count="%d" edges_fixed="0" degenerate_facets="0" facets_removed="0" '
            'facets_reversed="0" backwards_edges="0"/>\n    </part>\n%s  </object>\n'
            % (oid, n, meta, len(p["tri"]), mid, n, k, len(p["tri"]), rng))
        inst.append('    <model_instance>\n      <metadata key="object_id" value="%d"/>\n'
                    '      <metadata key="instance_id" value="0"/>\n      <metadata key="identify_id" value="%d"/>\n'
                    '    </model_instance>\n' % (oid, k + 1))
        asm.append('   <assemble_item object_id="%d" instance_id="0" transform="%s" offset="0 0 0" />\n' % (oid, tr))
    main = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" %s>\n'
            ' <metadata name="Application">BambuStudio-01.10.01.50</metadata>\n'
            ' <metadata name="OrcaSlicer">2.3.2</metadata>\n <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
            ' <metadata name="Title">%s</metadata>\n <resources>\n%s </resources>\n <build p:UUID="%s">\n%s </build>\n'
            '</model>\n' % (NS, _xml(plan["file"]), "".join(res), uuid.uuid4(), "".join(build)))
    model_settings = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n%s  <plate>\n'
                      '    <metadata key="plater_id" value="1"/>\n    <metadata key="plater_name" value="%s"/>\n'
                      '    <metadata key="locked" value="false"/>\n%s  </plate>\n  <assemble>\n%s  </assemble>\n'
                      '</config>\n' % ("".join(settings), _xml(plan["file"]), "".join(inst), "".join(asm)))
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            ' <Relationship Target="/3D/3dmodel.model" Id="rel-1" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n</Relationships>\n')
    model_rels = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                  '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                  + "".join(' <Relationship Target="/%s" Id="rel-%d" '
                            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n' % (o[0], i + 1)
                            for i, o in enumerate(objs)) + '</Relationships>\n')
    types = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
             ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
             ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
             ' <Default Extension="png" ContentType="image/png"/>\n'
             ' <Default Extension="gcode" ContentType="text/x.gcode"/>\n</Types>\n')
    slice_info = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n  <header>\n'
                  '    <header_item key="X-BBL-Client-Type" value="slicer"/>\n'
                  '    <header_item key="X-BBL-Client-Version" value="01.10.01.50"/>\n'
                  '    <header_item key="OrcaSlicer-Version" value="2.3.2"/>\n  </header>\n</config>\n')
    cfg = project_config(plan["file"], plan["s"], plan["fil"])
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.writestr("[Content_Types].xml", types)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", main)
        z.writestr("3D/_rels/3dmodel.model.rels", model_rels)
        for name, text in objs:
            z.writestr(name, text)
        z.writestr("Metadata/project_settings.config", json.dumps(cfg, indent=4, ensure_ascii=False))
        z.writestr("Metadata/model_settings.config", model_settings)
        z.writestr("Metadata/slice_info.config", slice_info)
        z.writestr("Metadata/FlashPrep_report.txt", report_text(plan))
        if plan.get("colour_changes"):
            z.writestr("Metadata/custom_gcode_per_layer.xml", colour_change_xml(plan["colour_changes"]))
    return path


# --------------------------------------------------------------------------- run + verify

def export_plate(folder, plate, material=MATERIAL):
    plan = plan_plate(plate, material)
    if plan["layout"]:
        raise RuntimeError("; ".join(plan["layout"]))
    bad = [p["name"] for p in plan["parts"] if p["a"]["non_manifold_edges"]]
    if bad:
        raise RuntimeError("no manifold: " + ", ".join(bad))
    os.makedirs(folder, exist_ok=True)
    plan["path"] = write_3mf(os.path.join(folder, plan["file"] + ".3mf"), plan)
    return plan


def export_all(folder, names=None, material=MATERIAL, plates=PLATES):
    return [export_plate(folder, p, material) for p in plates if names is None or p[0] in names]


def slice_check(plan, outdir):
    """Slice with Flash Studio's CLI: proves the project loads and slices. Returns time, grams,
    layers and the support extrusion moves per object (supports must land only where intended)."""
    os.makedirs(outdir, exist_ok=True)
    r = subprocess.run([FLASH_STUDIO, "--slice", "0", "--outputdir", outdir, plan["path"]],
                       capture_output=True, text=True, timeout=900)
    g = os.path.join(outdir, "plate_1.gcode")
    if r.returncode or not os.path.exists(g):
        raise RuntimeError("slice failed (%d): %s" % (r.returncode, (r.stdout + r.stderr)[-2000:]))
    boxes = [(p["name"], p["co"][:, :2].min(axis=0) - 4, p["co"][:, :2].max(axis=0) + 4) for p in plan["parts"]]
    info, sup, typ, x, y, zc = {}, {}, "", 0.0, 0.0, 0.0
    with open(g, "r", errors="ignore") as f:
        for line in f:
            if line.startswith(";TYPE:"):
                typ = line[6:].strip()
            elif line.startswith("; estimated printing time (normal mode)"):
                info["time"] = line.split("=")[1].strip()
            elif line.startswith("; total filament used [g]"):
                info["grams"] = float(line.split("=")[1])
            elif line.startswith("; total layers count"):
                info["layers"] = int(line.split("=")[1])
            elif line.startswith(("M600", "PAUSE")):                     # filament swaps (pause events)
                info.setdefault("colour_changes", []).append((round(zc, 2), line.strip()[:40]))
            elif line.startswith(";Z:") or line.startswith("; Z_HEIGHT:"):
                zc = float(line.split(":")[1])
            elif line.startswith("G1") and typ.startswith("Support"):
                w = dict((c[0], float(c[1:])) for c in line.split()[1:] if c[0] in "XYE")
                x, y = w.get("X", x), w.get("Y", y)
                if w.get("E", 0) > 0 and ("X" in w or "Y" in w):     # not an unretract
                    k = [n for n, lo, hi in boxes if lo[0] <= x <= hi[0] and lo[1] <= y <= hi[1]] or ["?"]
                    sup[k[0]] = sup.get(k[0], 0) + 1
            elif line.startswith("G1"):
                w = dict((c[0], float(c[1:])) for c in line.split()[1:] if c[0] in "XY")
                x, y = w.get("X", x), w.get("Y", y)
    info["support_moves"] = sup
    return info


def bom_row(plan, info):
    sup = ", ".join(sorted(k for k in info["support_moves"] if k != "?")) or "cap"   # "?" = tree bases
    return (plan["file"] + ".3mf", plan["material"], ", ".join(p["name"] for p in plan["parts"]),
            plan["s"]["layer_height"], sup, info["time"], info["grams"])
