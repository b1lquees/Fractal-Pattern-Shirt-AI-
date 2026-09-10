"""
fractal_observatory.py
Interactive Mandelbrot + Julia set explorer.

Run:  python fractal_observatory.py
(needs a local display / GUI backend — TkAgg, Qt5Agg, etc. Won't do
anything useful over SSH without X forwarding or a notebook backend.)

Controls
  scroll on the left panel   zoom in/out, centered on the cursor
  move mouse over left panel Julia set on the right updates live for c = cursor
  click on the left panel    lock / unlock the Julia point
  'r'                        reset the view
"""

import copy
import numpy as np
import matplotlib.pyplot as plt

from fractal_core import mandelbrot, julia, make_cmap, DEFAULT_VIEW

WIDTH, HEIGHT = 480, 480
MAX_ITER = 250
CMAP = make_cmap()
BG = "#05060c"
INK = "#e9ebf6"


class FractalExplorer:
    def __init__(self):
        self.view = copy.deepcopy(DEFAULT_VIEW)
        self.c = complex(-0.5, 0.0)
        self.locked = False
        self.max_iter = MAX_ITER

        self.fig, (self.ax_m, self.ax_j) = plt.subplots(1, 2, figsize=(11, 5.4))
        self.fig.patch.set_facecolor(BG)
        for ax in (self.ax_m, self.ax_j):
            ax.set_facecolor(BG)
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_visible(False)

        blank = np.zeros((HEIGHT, WIDTH))
        self.im_m = self.ax_m.imshow(blank, cmap=CMAP, origin="lower")
        self.im_j = self.ax_j.imshow(blank, cmap=CMAP, origin="lower")

        self.ax_m.set_title(
            "Mandelbrot — scroll to zoom, click to lock", color=INK, fontsize=10
        )
        self.j_title = self.ax_j.set_title("Julia", color=INK, fontsize=10)

        self.fig.canvas.mpl_connect("scroll_event", self.on_scroll)
        self.fig.canvas.mpl_connect("motion_notify_event", self.on_move)
        self.fig.canvas.mpl_connect("button_press_event", self.on_click)
        self.fig.canvas.mpl_connect("key_press_event", self.on_key)

        self.redraw_mandel()
        self.redraw_julia()
        self.fig.tight_layout()

    # -- rendering --------------------------------------------------
    def redraw_mandel(self):
        v = self.view
        data = mandelbrot(v["xmin"], v["xmax"], v["ymin"], v["ymax"], WIDTH, HEIGHT, self.max_iter)
        self.im_m.set_data(data)
        self.im_m.set_extent([v["xmin"], v["xmax"], v["ymin"], v["ymax"]])
        self.im_m.set_clim(0, self.max_iter)
        self.fig.canvas.draw_idle()

    def redraw_julia(self):
        data = julia(-1.8, 1.8, -1.8, 1.8, WIDTH, HEIGHT, self.c, self.max_iter)
        self.im_j.set_data(data)
        self.im_j.set_clim(0, self.max_iter)
        sign = "+" if self.c.imag >= 0 else "\u2212"
        state = "locked" if self.locked else "live"
        self.j_title.set_text(
            f"Julia ({state}) \u2014 c = {self.c.real:.4f} {sign} {abs(self.c.imag):.4f}i"
        )
        self.fig.canvas.draw_idle()

    # -- events -------------------------------------------------------
    def on_scroll(self, event):
        if event.inaxes is not self.ax_m or event.xdata is None:
            return
        v = self.view
        factor = 0.8 if event.button == "up" else 1.25
        xr = (v["xmax"] - v["xmin"]) * factor
        yr = (v["ymax"] - v["ymin"]) * factor
        v["xmin"] = event.xdata - (event.xdata - v["xmin"]) * factor
        v["xmax"] = v["xmin"] + xr
        v["ymin"] = event.ydata - (event.ydata - v["ymin"]) * factor
        v["ymax"] = v["ymin"] + yr
        # zoom in -> more detail needed to keep the boundary crisp
        self.max_iter = int(np.clip(MAX_ITER * (3.4 / xr), MAX_ITER, 2000))
        self.redraw_mandel()

    def on_move(self, event):
        if self.locked or event.inaxes is not self.ax_m or event.xdata is None:
            return
        self.c = complex(event.xdata, event.ydata)
        self.redraw_julia()

    def on_click(self, event):
        if event.inaxes is not self.ax_m:
            return
        self.locked = not self.locked
        self.redraw_julia()

    def on_key(self, event):
        if event.key == "r":
            self.view = copy.deepcopy(DEFAULT_VIEW)
            self.max_iter = MAX_ITER
            self.locked = False
            self.redraw_mandel()
            self.redraw_julia()


if __name__ == "__main__":
    explorer = FractalExplorer()
    plt.show()
