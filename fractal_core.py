"""
fractal_core.py
Vectorized Mandelbrot / Julia escape-time computation and a color palette.
Shared by fractal_observatory.py (interactive) and render_preview.py (static/animated).
"""

import numpy as np
from matplotlib.colors import LinearSegmentedColormap

PALETTE_COLORS = [
    "#05060e", "#1b1145", "#4b2e8f", "#7c53c9",
    "#c9a6ff", "#7fe7c4", "#f5d0a9", "#ffffff",
]


def make_cmap():
    """A smooth cyclic-feeling colormap: deep space -> violet -> aurora teal -> gold -> white."""
    return LinearSegmentedColormap.from_list("nebula", PALETTE_COLORS, N=1024)


def _escape_time(Z0, C, max_iter):
    """
    Shared escape-time loop. Z0 and C are broadcastable complex arrays
    (Mandelbrot: Z0=0, C=grid.  Julia: Z0=grid, C=constant).
    Returns a smoothed iteration count (float) in [0, max_iter].
    """
    Z = Z0.astype(np.complex128).copy()
    # points that never escape (inside the set) stay at 0 -> darkest palette
    # color; points that escape quickly are also near 0; only the halo just
    # outside the boundary, which takes nearly max_iter steps to escape,
    # climbs toward the bright end of the palette.
    div_time = np.zeros(Z.shape, dtype=np.float64)
    mask = np.ones(Z.shape, dtype=bool)

    for i in range(max_iter):
        Z[mask] = Z[mask] ** 2 + C[mask]
        escaped = np.abs(Z) > 2
        newly = escaped & mask
        if newly.any():
            # smooth (renormalized) iteration count avoids visible color banding
            div_time[newly] = i + 1 - np.log(np.log(np.abs(Z[newly]))) / np.log(2)
        mask &= ~escaped
        if not mask.any():
            break
    return div_time


def mandelbrot(xmin, xmax, ymin, ymax, w, h, max_iter):
    x = np.linspace(xmin, xmax, w)
    y = np.linspace(ymin, ymax, h)
    C = x[np.newaxis, :] + 1j * y[:, np.newaxis]
    Z0 = np.zeros_like(C)
    return _escape_time(Z0, C, max_iter)


def julia(xmin, xmax, ymin, ymax, w, h, c, max_iter):
    x = np.linspace(xmin, xmax, w)
    y = np.linspace(ymin, ymax, h)
    Z0 = x[np.newaxis, :] + 1j * y[:, np.newaxis]
    C = np.full(Z0.shape, c, dtype=np.complex128)
    return _escape_time(Z0, C, max_iter)


DEFAULT_VIEW = dict(xmin=-2.2, xmax=1.2, ymin=-1.7, ymax=1.7)
