"""
render_preview.py
Generates static/animated previews of the Mandelbrot + Julia pair without
needing a GUI backend. Useful in headless environments (CI, this sandbox);
for the real interactive version, run fractal_observatory.py locally.

Outputs:
  hero.png        Mandelbrot (full view + a zoomed filament) next to its Julia set
  zoom.gif         Mandelbrot zooming into a filament, Julia set updating alongside
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from fractal_core import mandelbrot, julia, make_cmap, DEFAULT_VIEW

CMAP = make_cmap()
BG = "#05060c"
INK = "#e9ebf6"

# an interesting point right on the boundary of the Mandelbrot set
TARGET = complex(-0.743643887037151, 0.131825904205330)


def style_axes(ax):
    ax.set_facecolor(BG)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def render_hero(path="hero.png", w=640, h=640, max_iter=400):
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.4))
    fig.patch.set_facecolor(BG)
    for ax in axes:
        style_axes(ax)

    full = mandelbrot(**DEFAULT_VIEW, w=w, h=h, max_iter=260)
    axes[0].imshow(full, cmap=CMAP, origin="lower")
    axes[0].set_title("Mandelbrot \u2014 full set", color=INK, fontsize=11)

    span = 0.02
    zoomed = mandelbrot(
        TARGET.real - span, TARGET.real + span,
        TARGET.imag - span, TARGET.imag + span,
        w, h, max_iter,
    )
    axes[1].imshow(zoomed, cmap=CMAP, origin="lower")
    axes[1].set_title(f"Zoomed \u00d7{3.4/(2*span):.0f}", color=INK, fontsize=11)

    j = julia(-1.8, 1.8, -1.8, 1.8, w, h, TARGET, max_iter)
    axes[2].imshow(j, cmap=CMAP, origin="lower")
    axes[2].set_title("Matching Julia set", color=INK, fontsize=11)

    fig.suptitle(
        "Fractal Observatory \u2014 Mandelbrot \u00d7 Julia", color=INK, fontsize=15, y=1.02
    )
    fig.tight_layout()
    fig.savefig(path, dpi=140, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {path}")


def render_zoom_gif(path="zoom.gif", w=340, h=340, frames=48, base_iter=200):
    fig, (ax_m, ax_j) = plt.subplots(1, 2, figsize=(8.4, 4.4))
    fig.patch.set_facecolor(BG)
    for ax in (ax_m, ax_j):
        style_axes(ax)

    im_m = ax_m.imshow(np.zeros((h, w)), cmap=CMAP, origin="lower", vmin=0)
    im_j = ax_j.imshow(np.zeros((h, w)), cmap=CMAP, origin="lower", vmin=0)
    ax_m.set_title("Zooming toward the boundary", color=INK, fontsize=10)
    j_title = ax_j.set_title("Julia set along the way", color=INK, fontsize=10)
    fig.tight_layout()

    start_span, end_span = 1.7, 0.0012

    def frame_fn(i):
        t = i / (frames - 1)
        # ease toward the target so the zoom feels like it's accelerating in
        span = start_span * (end_span / start_span) ** t
        max_iter = int(base_iter + 900 * t)

        m = mandelbrot(
            TARGET.real - span, TARGET.real + span,
            TARGET.imag - span, TARGET.imag + span,
            w, h, max_iter,
        )
        im_m.set_data(m)
        im_m.set_clim(0, max_iter)

        # sweep c slightly around the target so the Julia panel visibly breathes
        wobble = 0.03 * (1 - t)
        c = TARGET + complex(wobble * np.cos(4 * np.pi * t), wobble * np.sin(4 * np.pi * t))
        j = julia(-1.8, 1.8, -1.8, 1.8, w, h, c, 220)
        im_j.set_data(j)
        im_j.set_clim(0, 220)
        j_title.set_text(f"Julia \u2014 c \u2248 {c.real:.4f} {'+' if c.imag>=0 else '-'} {abs(c.imag):.4f}i")

        return im_m, im_j

    anim = animation.FuncAnimation(fig, frame_fn, frames=frames, blit=False)
    anim.save(path, writer="pillow", fps=12)
    plt.close(fig)
    print(f"wrote {path}")


if __name__ == "__main__":
    render_hero()
    render_zoom_gif()
