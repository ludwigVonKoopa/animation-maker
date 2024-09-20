=====
Usage
=====

Animation-maker can be use in a python script or in command line.
Please check the :ref:`gallery_reference` to see differents exemples of features.



Basic example
=============

you want to create a small animation with matplotlib, to show how many points you need to draw a circle

.. plot::
    :include-source:

    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots(1, 1, figsize=(4,4), dpi=120,)

    ax.set_xlim(-1,1); ax.set_ylim(-1,1)

    n = 7
    x = np.arange(n+1)/n * 2*np.pi
    ax.plot(np.sin(x), np.cos(x))
    ax.set_title("n=7")



you need to define a plotting function with this patern :

.. code-block:: python

    import matplotlib.pyplot as plt
    import numpy as np

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


        fig, ax = plt.subplots(1, 1, figsize=(4,4), dpi=120,)

        ax.set_xlim(-1,1); ax.set_ylim(-1,1)

        n = i+7  # starts indices at 7
        x = np.arange(n+1)/n * 2*np.pi
        ax.plot(np.sin(x), np.cos(x))
        ax.set_title(f"n={i}")
        return fig


We will explain the ``ds`` argument later.

You should define all your plotting logic in this function, and return a matplotlib Figure.
You can use the ``i`` parameter to know which image is being computed.

now we have 2 choices to use the tool : the command line, or use in a python script.


Use in a python script | jupyter notebook
-----------------------------------------


.. code-block:: python

    import matplotlib.pyplot as plt
    import numpy as np
    import anim

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

        fig, ax = plt.subplots(1, 1, figsize=(4,4), dpi=120,)
        ax.set_xlim(-1,1); ax.set_ylim(-1,1)

        n = i+7  # starts indices at 7
        x = np.arange(n+1)/n * 2*np.pi
        ax.plot(np.sin(x), np.cos(x))
        ax.set_title(f"n={i}")
        return fig

    fps = 6
    folder = "~/my_animation"
    max_frames = fps * 7  # we want 7s of a video, with 6fps => 6*7=42 frames

    anim.animate(plot, folder, fps, max_frames=max_frames)


Use in command line
-------------------

To use in a command line, you must define a script file with all function needed, then use the command ``anim``:

create the ``~/circle.py`` file

.. code-block:: python
    :linenos:
    :caption: circle.py


    import matplotlib.pyplot as plt
    import numpy as np

    ANIM_FPS = 6
    ANIM_OUTPUT_FOLDER = "~/my_animation"
    ANIM_MAX_FRAMES = ANIM_FPS * 4

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

then start

.. code-block:: console

    anim circle.py

you can check the result in the example :ref:`small_reference`


create a gif
============

You can create a gif from your video, and specify the length of the gif in seconds.
(so it will take only the first X seconds from the video, and convert it to gif).
The name of the gif will be the same as the video, with extension modified

.. tab-set::

    .. tab-item:: Python script

        .. code-block:: python

            # [...]
            video_name = anim.animate(plot, folder, fps, max_frames=max_frames)
            gif_name = anim.video2gif(video_name, gif_fps=5)  # <== specify duration of gif

    .. tab-item:: console

        .. code-block:: console

            anim circle.py -g 5  # <== specify duration of gif
