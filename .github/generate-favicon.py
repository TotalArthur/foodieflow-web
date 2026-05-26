#!/usr/bin/env python3
"""
Generates favicon.ico (16, 32, 48 px) from logo.png using Pillow.
Called by .github/workflows/update-pricing.yml after logo.png is updated.
"""
from PIL import Image

img = Image.open("favicon.png").convert("RGBA")
img.save("favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
print("✓  favicon.ico generated from favicon.png")
