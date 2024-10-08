"""

.. _path_exemple:

Build a path for the camera
###########################

How to use the class `Path`
"""

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from anim.path import TimePath

ANIM_FPS = 60
ANIM_OUTPUT_FOLDER = "animation/example_20"

ANIM_MAX_FRAMES = ANIM_FPS * 10


def plot(i_image, ds):
    """créée une figure"""

    extent = ds.attrs["extent"]
    tn = ds.attrs["tn"]
    speed = ds.attrs["speed"]

    fig = plt.figure(figsize=(7, 3.5), dpi=80)

    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    ax.set_extent(extent, crs=ccrs.PlateCarree())

    ax.coastlines()
    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.OCEAN)

    gl = ax.gridlines(draw_labels=True)
    gl.top_labels = False
    gl.right_labels = False

    x0, x1, y0, y1 = extent
    x = (x0 + x1) / 2
    y = (y0 + y1) / 2

    ax.set_title(f"i={i_image:03d} date={tn} | pos=({x:6.2f}, {y:6.2f}), speed={speed:6.2f}°/day", fontsize=11)

    return fig


def compute():
    t0 = np.datetime64("2003-06-03T00:25:00")

    # cannot have float when creating timedelta64, so use seconds
    dt = np.timedelta64(int(60 * 60 * 24 / ANIM_FPS), "s")

    path = TimePath(coords=(-5, 36), dx=20, dy=10, t0=t0)
    # move to the coordinate (9, 43) in 2 days
    path.move(np.timedelta64(2, "D"), coords=(9, 43))
    # move to the coordinate (15, 41) in 1 days
    path.move(np.timedelta64(1, "D"), coords=(15, 41))
    # move to the coordinate (26, 36) in 3 days and zoom in (=> reducing dx and dy by a half)
    path.move_and_zoom(np.timedelta64(3, "D"), zoom=2, coords=(26, 36))

    # wait a little (move to the same place in 1 day, so no move)
    path.move(np.timedelta64(1, "D"))

    # don't move, but change the zooming by dezooming until having dx=40 and dy=20
    path.move_and_focus(np.timedelta64(3, "D"), dx=40, dy=20)

    for tn, extent, speed in zip(*path.compute_path(dt)):
        ds = xr.Dataset(attrs={"tn": tn, "extent": extent, "speed": speed})
        yield ds
