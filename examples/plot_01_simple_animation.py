"""
.. _small_reference:

Simple animation
################

explain the utilisation of the ``plot`` function

"""

import matplotlib.pyplot as plt
import numpy as np

ANIM_FPS = 6
ANIM_OUTPUT_FOLDER = "animation/example_01"
ANIM_MAX_FRAMES = ANIM_FPS * 7


def plot(i, ds):
    """
    Parameters
    ----------
    i: int
        indice of the image.
    ds: xarray.Dataset
        data passed to the plotting function


    Returns
    -------
    fig: matplotlib.figure.Figure
        the figure to save
    """

    fig, ax = plt.subplots(1, 1, figsize=(4, 4), dpi=120)
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)

    n = i + 7  # starts indices at 7
    x = np.arange(n + 1) / n * 2 * np.pi
    ax.plot(np.sin(x), np.cos(x))
    ax.set_title(f"image {i} : n={n}")
    return fig
