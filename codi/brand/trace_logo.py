"""Trace the BOLABOL logo PNG into polygons for the machine badge (run with system python3 + potrace).

    python3 brand/trace_logo.py        -> brand/bolabol_logo.json

Pixels are classified by nearest logo colour (edge speckles from anti-aliasing dropped by size);
big coral blobs are letters, small ones sparkles. potrace turns each mask into polygons (outer ring
first, holes after, pixel units, y up). Extra masks: the badge base (the whole logo grown by
BORDER_MM, a die-cut sticker outline), the sparkle pockets in it and the wall recess (grown by
CLEAR_MM).
"""
import json
import os
import subprocess
import tempfile
from collections import deque
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "bolabol_logo.png")
OUT = os.path.join(HERE, "bolabol_logo.json")
HEIGHT_MM = 22.0                    # printed logo height (whole canvas): fits the mech box band over the coin plate
BORDER_MM, CLEAR_MM = 1.5, 0.15     # sticker border around the logo, fit clearance of pockets / recess
PALETTE = {"coral": (0xEF, 0x54, 0x59), "cream": (0xFC, 0xF7, 0xED),
           "yellow": (0xFE, 0xBF, 0x41), "mint": (0x4F, 0xAF, 0x9D)}
SPECKLE, LETTER = 40, 5000          # blob areas (px): below = anti-aliasing noise, above = a letter


def classify(img):
    a = np.asarray(img.convert("RGBA")).astype(int)
    rgb, alpha = a[..., :3], a[..., 3]
    names = list(PALETTE)
    near = np.stack([((rgb - PALETTE[n]) ** 2).sum(-1) for n in names]).argmin(0)
    return {n: (near == i) & (alpha >= 128) for i, n in enumerate(names)}


def blobs(mask):
    """4-connected components -> list of boolean masks."""
    seen, out = np.zeros_like(mask), []
    h, w = mask.shape
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]:
            continue
        comp, q = [], deque([(y0, x0)])
        seen[y0, x0] = True
        while q:
            y, x = q.popleft()
            comp.append((y, x))
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and not seen[yy, xx]:
                    seen[yy, xx] = True
                    q.append((yy, xx))
        m = np.zeros_like(mask)
        ys, xs = zip(*comp)
        m[list(ys), list(xs)] = True
        out.append(m)
    return out


def union(masks, like):
    out = np.zeros_like(like)
    for m in masks:
        out |= m
    return out


def grow(mask, r):
    """Disk dilation by r pixels (round corners, unlike a square max filter)."""
    out = mask.copy()
    h, w = mask.shape
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                src = mask[max(0, -dy):h - max(0, dy), max(0, -dx):w - max(0, dx)]
                out[max(0, dy):h - max(0, -dy), max(0, dx):w - max(0, -dx)] |= src
    return out


def trace(m, pad):
    """potrace a boolean mask (canvas padded by pad) -> [[outer ring, hole, ...], ...] in canvas
    pixels, y up."""
    with tempfile.TemporaryDirectory() as tmp:
        pbm, gj = os.path.join(tmp, "m.pbm"), os.path.join(tmp, "m.json")
        Image.fromarray(~m).convert("1").save(pbm)       # potrace traces black
        subprocess.run(["potrace", "-b", "geojson", "-x", "1", "-t", "4", "-O", "0.4", "-o", gj, pbm], check=True)
        feats = json.load(open(gj))["features"]
    return [[[(x - pad, y - pad) for x, y in ring] for ring in f["geometry"]["coordinates"]] for f in feats]


def main():
    img = Image.open(SRC)
    w, h = img.size
    mm = HEIGHT_MM / h
    clear = max(1, round(CLEAR_MM / mm))
    pad = round(BORDER_MM / mm) + clear + 4             # room to grow past the canvas edge
    c = {k: [b for b in blobs(np.pad(m, pad)) if b.sum() >= SPECKLE] for k, m in classify(img).items()}
    coral_big = [b for b in c["coral"] if b.sum() > LETTER]
    letters = union(coral_big + c["cream"], c["coral"][0])
    sparkles = {"yellow": union(c["yellow"], letters), "mint": union(c["mint"], letters),
                "coral": union([b for b in c["coral"] if b.sum() <= LETTER], letters)}
    every = letters | sparkles["yellow"] | sparkles["mint"] | sparkles["coral"]
    base = grow(every, round(BORDER_MM / mm))
    pockets = grow(sparkles["yellow"] | sparkles["mint"] | sparkles["coral"], clear)
    data = {"size": [w, h], "height_mm": HEIGHT_MM, "letters": trace(letters, pad),
            "highlights": trace(union(c["cream"], letters), pad),
            "sparkles": {k: trace(m, pad) for k, m in sparkles.items()},
            "pockets": trace(pockets, pad), "base": trace(base, pad), "recess": trace(grow(base, clear), pad)}
    json.dump(data, open(OUT, "w"))
    n = {k: len(v) for k, v in data.items() if isinstance(v, list) and k != "size"}
    n.update({"sparkles_" + k: len(v) for k, v in data["sparkles"].items()})
    print(OUT, n)


if __name__ == "__main__":
    main()
