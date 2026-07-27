#!/usr/bin/env python3
"""Prepare the homepage illustrations: strip the flat backdrop to transparency.

The source illustrations are exported on a flat off-white backdrop. A plain
flood fill gives a hard, binary mask, which throws away the anti-aliasing the
artwork was drawn with and leaves a stair-stepped silhouette. Trimming that
mask afterwards does not help: the pixels on the edge are a *blend* of ink and
backdrop, so a pale rim survives however much is shaved off.

So the fill only decides which pixels are outside the artwork. Along the
boundary the alpha is then derived from how far each pixel sits from the
backdrop colour, which reconstructs the original soft edge. Interior pixels are
left fully opaque, so light areas enclosed by the artwork -- the chef's jacket,
a milk carton -- keep their fill no matter how close to the backdrop they are.

Usage: python3 tools/prep-illustrations.py raw/chef-mascot.png illustrations/chef-mascot.png [max_width]
"""
import sys
from collections import deque

import numpy as np
from PIL import Image, ImageFilter

# How far a pixel may drift from the sampled corner colour and still be treated
# as backdrop by the fill. Deliberately tight: the chef's white jacket sits only
# ~19 levels above the backdrop, and a looser threshold reaches through the
# jacket's open hem and hollows it out.
FILL_TOLERANCE = 10

# Distance from the backdrop colour over which the edge ramps from clear to
# solid. Below SOFT_LO a boundary pixel is essentially backdrop; above SOFT_HI
# it is essentially ink.
SOFT_LO, SOFT_HI = 8.0, 40.0

# How far the soft ramp reaches inward from the fill boundary, in pixels.
EDGE_BAND = 2


def _outside_mask(px, w, h, backdrop, tolerance):
    """Flood fill inward from every border pixel, following backdrop colour."""
    br, bg, bb = backdrop
    seen = bytearray(w * h)
    outside = bytearray(w * h)
    queue = deque()
    for x in range(w):
        queue.append((x, 0)); queue.append((x, h - 1))
    for y in range(h):
        queue.append((0, y)); queue.append((w - 1, y))

    while queue:
        x, y = queue.popleft()
        if not (0 <= x < w and 0 <= y < h):
            continue
        i = y * w + x
        if seen[i]:
            continue
        seen[i] = 1
        p = px[x, y]
        if abs(p[0] - br) > tolerance or abs(p[1] - bg) > tolerance or abs(p[2] - bb) > tolerance:
            continue
        outside[i] = 1
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return np.frombuffer(bytes(outside), dtype=np.uint8).reshape(h, w).astype(bool)


def _bleed_colour(rgb, opaque, rounds=6):
    """Grow artwork colour into the cleared area.

    Resizing an RGBA image blends the colour channels of transparent pixels into
    their neighbours. If those still hold backdrop grey, a pale halo reappears
    the moment the image is scaled, so the colour has to be pushed outward first.
    """
    rgb = rgb.astype(np.float32)
    known = opaque.copy()
    for _ in range(rounds):
        total = np.zeros_like(rgb)
        count = np.zeros(known.shape, np.float32)
        for axis, shift in ((0, 1), (0, -1), (1, 1), (1, -1)):
            total += np.roll(rgb, shift, axis) * np.roll(known, shift, axis)[..., None]
            count += np.roll(known, shift, axis)
        fill = ~known & (count > 0)
        if not fill.any():
            break
        rgb[fill] = total[fill] / count[fill][..., None]
        known |= fill
    return np.clip(rgb, 0, 255).astype(np.uint8)


def strip_backdrop(src: str, dst: str, max_width: int = 0) -> None:
    img = Image.open(src).convert("RGBA")
    w, h = img.size
    px = img.load()

    corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    backdrop = tuple(sum(c[i] for c in corners) // len(corners) for i in range(3))

    outside = _outside_mask(px, w, h, backdrop, FILL_TOLERANCE)

    rgb = np.asarray(img.convert("RGB"), dtype=np.int16)
    distance = np.abs(rgb - np.array(backdrop, dtype=np.int16)).max(axis=2).astype(np.float32)

    # The ramp applies only in a thin band just inside the fill boundary. Running
    # it everywhere would eat the enclosed light areas, which sit as close to the
    # backdrop colour as the edge pixels do.
    grown = Image.fromarray((outside * 255).astype(np.uint8)).filter(
        ImageFilter.MaxFilter(EDGE_BAND * 2 + 1)
    )
    band = (np.asarray(grown) > 0) & ~outside

    soft = np.clip((distance - SOFT_LO) / (SOFT_HI - SOFT_LO), 0.0, 1.0) * 255.0
    alpha = np.where(outside, 0.0, np.where(band, soft, 255.0)).astype(np.uint8)

    out = np.dstack([_bleed_colour(np.asarray(img.convert("RGB")), alpha > 0), alpha])
    img = Image.fromarray(out, "RGBA")

    img = img.crop(img.getbbox() or (0, 0, w, h))

    # Downscale to roughly 2x the largest size the layout renders it at, so a
    # decorative illustration does not ship several hundred KB it cannot use.
    if max_width and img.width > max_width:
        img = img.resize((max_width, round(img.height * max_width / img.width)), Image.LANCZOS)

    img.save(dst, optimize=True)
    print(f"{src} -> {dst} ({img.width}x{img.height})")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    strip_backdrop(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) == 4 else 0)
