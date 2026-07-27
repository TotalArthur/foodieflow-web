#!/usr/bin/env python3
"""Prepare the homepage illustrations: strip the flat backdrop to transparency.

The source illustrations are exported on a flat off-white/grey backdrop. Flood
fill inward from the border so only the outer backdrop is cleared -- light areas
*inside* the artwork (a milk carton, the chef's jacket) keep their fill.

Usage: python3 tools/prep-illustrations.py raw/chef-mascot.png illustrations/chef-mascot.png
"""
import sys
from collections import deque

from PIL import Image

# How far a pixel may drift from the sampled corner colour and still count as backdrop.
TOLERANCE = 32


def strip_backdrop(src: str, dst: str, tolerance: int = TOLERANCE) -> None:
    img = Image.open(src).convert("RGBA")
    w, h = img.size
    px = img.load()

    # Sample the four corners; the backdrop is whichever colour they agree on.
    corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    br, bg, bb = (sum(c[i] for c in corners) // len(corners) for i in range(3))

    def is_backdrop(p):
        return abs(p[0] - br) <= tolerance and abs(p[1] - bg) <= tolerance and abs(p[2] - bb) <= tolerance

    seen = bytearray(w * h)
    queue = deque()
    for x in range(w):
        for y in (0, h - 1):
            queue.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            queue.append((x, y))

    while queue:
        x, y = queue.popleft()
        if not (0 <= x < w and 0 <= y < h):
            continue
        idx = y * w + x
        if seen[idx]:
            continue
        seen[idx] = 1
        p = px[x, y]
        if not is_backdrop(p):
            continue
        px[x, y] = (p[0], p[1], p[2], 0)
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    img = img.crop(img.getbbox() or (0, 0, w, h))
    img.save(dst)
    print(f"{src} -> {dst} ({img.width}x{img.height})")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    strip_backdrop(sys.argv[1], sys.argv[2])
