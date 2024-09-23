"""

.. _compute_exemple:

Animation using computed data
#############################

explain the utilisation of the ``compute`` function

"""

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

ANIM_FPS = 20
ANIM_OUTPUT_FOLDER = "animation/example_02"
ANIM_MAX_FRAMES = ANIM_FPS * 4


size = 10
fps = 10

max_frames = fps * 8


def compute():
    x = np.zeros(size) + np.nan
    y = np.zeros(size) + np.nan

    for i in range(max_frames):
        n = i / size * np.pi
        x[:-1] = x[1:]
        y[:-1] = y[1:]
        x[-1] = np.sin(n) * 0.9
        y[-1] = np.cos(n) * 0.9
        yield xr.Dataset({"x": ("size", np.copy(x)), "y": ("size", np.copy(y))})


def plot(i, ds):
    fig, ax = plt.subplots(1, 1, figsize=(4, 4), dpi=120)
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    size = ds.sizes["size"]

    ax.scatter(ds.x, ds.y, s=np.arange(size) * 70, alpha=np.arange(size) / size)
    return fig
