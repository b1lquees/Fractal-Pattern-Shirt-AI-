"""
shirtmockup.py
Puts a print design onto a shirt photo, programmatically.

What it does:
  1. Renders a circular fractal badge (via fractal_core.py) as a transparent PNG.
  2. Picks a chest-sized box on the shirt photo.
  3. Pulls a shading map out of the shirt photo itself (fabric folds/shadows)
     and multiplies it into the badge so the print isn't just pasted flat.
  4. Adds a soft grounding shadow and composites the result.

Swap `render_design()` for any transparent-background PNG if you want to
mock up a different graphic instead of the fractal.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
import matplotlib
matplotlib.use("Agg")
from matplotlib.colors import Normalize

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fractal_core import mandelbrot, make_cmap

CMAP = make_cmap()
TARGET = complex(-0.743643887037151, 0.131825904205330)  # a pretty boundary point


def render_design(size=1200, span=0.016, max_iter=550):
    """Render the fractal as a circular, soft-edged RGBA badge."""
    iter_data = mandelbrot(
        TARGET.real - span, TARGET.real + span,
        TARGET.imag - span, TARGET.imag + span,
        size, size, max_iter,
    )
    norm = Normalize(vmin=0, vmax=iter_data.max())
    rgba = (CMAP(norm(iter_data)) * 255).astype(np.uint8)
    design = Image.fromarray(rgba, mode="RGBA")

    yy, xx = np.mgrid[0:size, 0:size]
    cx = cy = size / 2
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (size / 2)
    edge_alpha = np.clip(1.0 - (r - 0.82) / 0.16, 0, 1)
    edge_alpha = np.where(r > 0.98, 0.0, edge_alpha)
    design.putalpha(Image.fromarray((edge_alpha * 255).astype(np.uint8), mode="L"))
    return design


def apply_shading(design, shirt, box):
    """Multiply the shirt's own fold/shadow luminance into the design."""
    box_x, box_y, box_w = box
    region = shirt.crop((box_x, box_y, box_x + box_w, box_y + box_w)).convert("L")
    region = region.resize(design.size, Image.LANCZOS)
    gray = np.asarray(region).astype(np.float32)
    shade = np.clip(gray / 245.0, 0.75, 1.08)
    shade_mult = 1.0 + 0.35 * (shade - 1.0)  # keep the effect subtle

    arr = np.asarray(design).astype(np.float32)
    arr[..., :3] = np.clip(arr[..., :3] * shade_mult[..., None], 0, 255)
    return Image.fromarray(arr.astype(np.uint8), mode="RGBA")


def composite(shirt_path, out_path, box_frac=(0.29, 0.29, 0.40)):
    shirt = Image.open(shirt_path).convert("RGB")
    W, H = shirt.size
    box_x, box_y, box_w = (int(W * box_frac[0]), int(H * box_frac[1]), int(W * box_frac[2]))

    design = render_design()
    design = apply_shading(design, shirt, (box_x, box_y, box_w))
    design_small = design.resize((box_w, box_w), Image.LANCZOS)

    mockup = shirt.convert("RGBA")

    # soft grounding shadow, offset slightly down-right of the print
    shadow_alpha = design_small.split()[3].point(lambda a: int(a * 0.18))
    shadow = Image.new("L", (box_w, box_w), 0)
    shadow.paste(shadow_alpha, (0, 0))
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))
    shadow_layer = Image.new("RGBA", mockup.size, (0, 0, 0, 0))
    shadow_layer.paste((0, 0, 0, 255), (box_x + 3, box_y + 5), shadow)
    mockup = Image.alpha_composite(mockup, shadow_layer)

    mockup.paste(design_small, (box_x, box_y), design_small)
    mockup.convert("RGB").save(out_path)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--shirt", default="images.png", help="path to the blank shirt photo")
    p.add_argument("--out", default="shirt_mockup.png", help="output path")
    args = p.parse_args()
    composite(args.shirt, args.out)