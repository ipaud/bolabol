"""Trace the coin face art (dark ink of brand/bbol_logo.png and brand/boli.png) for the engraved token.

    python3 brand/trace_token.py        -> brand/token_faces.json

The ink is what gets cut into the coin. Each drawing is scaled so all ink fits a circle of ART_R mm
(1.5 mm plain rim on the 25 mm coin), then the ink is thinned by RIDGE_MM so the uncut lines between
letters and details stay printable with a 0.4 mm nozzle. Polygons in mm, centred, x right, y up.
"""
import json
import os
import numpy as np
from PIL import Image
from trace_logo import grow, trace

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "token_faces.json")
ART_R = 11.0                        # coin radius 12.5 - 1.5 mm rim
RIDGE_MM = 0.12                     # ink shrink: uncut gaps grow by 2x this
FACES = {"bbol": "bbol_logo.png", "boli": "boli.png"}


def face(fn):
    a = np.asarray(Image.open(os.path.join(HERE, fn)).convert("RGBA")).astype(int)
    ink = (a[..., :3].mean(-1) < 128) & (a[..., 3] >= 128)
    h = ink.shape[0]
    ys, xs = np.nonzero(ink)
    cx, cy = (xs.min() + xs.max()) / 2, h - (ys.min() + ys.max()) / 2        # ink bbox centre, y up
    s = ART_R / np.hypot(xs - cx, (h - ys) - cy).max()
    r = max(1, round(RIDGE_MM / s))
    pad = r + 4
    ink = ~grow(~np.pad(ink, pad), r)                                    # grow the paper = thin the ink
    return [[[((x - cx) * s, (y - cy) * s) for x, y in ring] for ring in poly] for poly in trace(ink, pad)], s


def main():
    data = {}
    for k, fn in FACES.items():
        polys, s = face(fn)
        data[k] = polys
        print(k, "%d features, %.4f mm/px" % (len(polys), s))
    json.dump(data, open(OUT, "w"))
    print(OUT)


if __name__ == "__main__":
    main()
