#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
split_3x3.py — alpha-edge sticker splitter for 3x3 source sheets.

The 3x3 layout is used ONLY to establish virtual cells. Within each cell we
build an alpha-aware foreground mask (alpha >= threshold) and keep the LARGEST
8-connected foreground component. Its tight bounding box is expanded by
`margin` source pixels outward, then the source is cropped at native pixel
resolution (no resampling). Output is RGBA PNG.

Outputs nine PNGs plus `split_manifest.json` recording detected/expanded
boxes, dimensions, padding clipping, and `resampled: false`.

Usage:
  python split_3x3.py <source.png> <output_dir> [--threshold 1] [--margin 1]
"""
from __future__ import annotations
import argparse
import json
import sys
from collections import deque
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


def clean_alpha0(arr: np.ndarray) -> np.ndarray:
    """Zero RGB where alpha == 0 (the model writes stray RGB into transparent
    pixels and viewers show them as 'color blocks')."""
    m0 = arr[:, :, 3] == 0
    arr[m0, 0:3] = 0
    ml = arr[:, :, 3] < 8
    arr[ml, 3] = 0
    arr[ml, 0:3] = 0
    return arr


def largest_component_bbox(mask: np.ndarray, x0: int, y0: int, x1: int, y1: int):
    """8-connected BFS inside the rectangle [x0,x1) x [y0,y1); return tight bbox
    of the largest component, or None if the cell is empty."""
    H, W = mask.shape
    x0c = max(0, x0); y0c = max(0, y0)
    x1c = min(W, x1); y1c = min(H, y1)
    if x0c >= x1c or y0c >= y1c:
        return None
    sub = mask[y0c:y1c, x0c:x1c]
    if not sub.any():
        return None
    visited = np.zeros_like(sub, dtype=bool)
    best = None  # (area, minx, miny, maxx, maxy) in cell-local coords
    # BFS over all component seeds, return the largest
    for sy in range(sub.shape[0]):
        for sx in range(sub.shape[1]):
            if not sub[sy, sx] or visited[sy, sx]:
                continue
            q = deque([(sy, sx)])
            visited[sy, sx] = True
            mn_x = mx_x = sx
            mn_y = mx_y = sy
            area = 0
            while q:
                y, x = q.popleft()
                area += 1
                if x < mn_x: mn_x = x
                if x > mx_x: mx_x = x
                if y < mn_y: mn_y = y
                if y > mx_y: mx_y = y
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < sub.shape[0] and 0 <= nx < sub.shape[1] and sub[ny, nx] and not visited[ny, nx]:
                            visited[ny, nx] = True
                            q.append((ny, nx))
            if best is None or area > best[0]:
                best = (area, mn_x, mn_y, mx_x, mx_y)
    if best is None:
        return None
    _, mn_x, mn_y, mx_x, mx_y = best
    # map back to global coords
    return (
        x0c + mn_x,
        y0c + mn_y,
        x0c + mx_x + 1,  # exclusive
        y0c + mx_y + 1,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="path to the 3x3 source PNG (RGBA)")
    ap.add_argument("out_dir", help="output directory for the 9 PNGs + manifest")
    ap.add_argument("--threshold", type=int, default=1, help="alpha threshold (default 1)")
    ap.add_argument("--margin", type=int, default=1, help="expand bbox outward by N source pixels (default 1)")
    args = ap.parse_args()

    src = Path(args.source)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    im = Image.open(src).convert("RGBA")
    arr = np.array(im)
    arr = clean_alpha0(arr)
    im = Image.fromarray(arr, "RGBA")
    W, H = im.size
    alpha = arr[:, :, 3]
    mask = alpha >= args.threshold

    xs = [round(W * i / 3) for i in range(4)]
    ys = [round(H * i / 3) for i in range(4)]
    cell_w = xs[1] - xs[0]
    cell_h = ys[1] - ys[0]

    manifest_entries: list[dict[str, Any]] = []
    seq = 0
    for r in range(3):
        for c in range(3):
            seq += 1
            x0, y0 = xs[c], ys[r]
            x1, y1 = xs[c + 1], ys[r + 1]
            # search inside cell, with no margin expansion (cell-BFS finds the
            # actual alpha bbox within the cell)
            bb = largest_component_bbox(mask, x0, y0, x1, y1)
            if bb is None:
                manifest_entries.append(
                    {
                        "sequence": seq,
                        "cell": [x0, y0, x1, y1],
                        "detected_bbox": None,
                        "expanded_bbox": None,
                        "output_size": None,
                        "padding_clipped": False,
                        "resampled": False,
                        "status": "empty",
                    }
                )
                continue
            dx0, dy0, dx1, dy1 = bb
            # expand by margin
            ex0 = max(0, dx0 - args.margin)
            ey0 = max(0, dy0 - args.margin)
            ex1 = min(W, dx1 + args.margin)
            ey1 = min(H, dy1 + args.margin)
            padding_clipped = (ex0 != dx0 - args.margin) or (ey0 != dy0 - args.margin) or \
                             (ex1 != dx1 + args.margin) or (ey1 != dy1 + args.margin)
            crop = im.crop((ex0, ey0, ex1, ey1))
            fn = f"{seq:02d}_cell_{r}{c}.png"
            crop.save(out_dir / fn, "PNG")
            manifest_entries.append(
                {
                    "sequence": seq,
                    "cell": [x0, y0, x1, y1],
                    "detected_bbox": [dx0, dy0, dx1, dy1],
                    "expanded_bbox": [ex0, ey0, ex1, ey1],
                    "output_size": [crop.size[0], crop.size[1]],
                    "padding_clipped": padding_clipped,
                    "resampled": False,
                    "file": fn,
                    "status": "ok",
                }
            )
    manifest = {
        "source": str(src),
        "size": [W, H],
        "threshold": args.threshold,
        "margin": args.margin,
        "cell_size": [cell_w, cell_h],
        "stickers": manifest_entries,
    }
    (out_dir / "split_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"split {src.name} -> {out_dir} ({seq} cells, margin={args.margin}px, threshold={args.threshold})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
