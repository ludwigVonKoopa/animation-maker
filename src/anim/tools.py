import logging
import os
import time

import numpy as np

logger = logging.getLogger(__name__)


class Timing:
    """compute time execution

    example :

    with Timing() as dt:
        myfunction()

    print("time for myfunction : {dt}")
    """

    scale = {"s": 1, "ms": 1e3}

    def __init__(self, unit: str = "ms"):
        self.unit = unit

    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tN = time.perf_counter()
        self.dt = self.tN - self.t0

    def __str__(self):
        return f"{self.dt*self.scale[self.unit]:.2f}{self.unit}"


def zarr_weight(group):
    "compute size of all variable contained in the group"
    return sum(group[var].nbytes_stored for var in group.array_keys())


def get_imgName(n_frames=None):
    """compute how many leading 0 is needed in the name

    Parameters
    ----------
    n_frames : int
        total number of images
    """

    if n_frames is None or n_frames <= 0:
        n_zeros = 7
    else:
        n_zeros = int(np.ceil(np.log10(n_frames)))
    return f"img_%0{n_zeros}d.png"


def images2video(imagePatern, fps, videoName, crf=24, vcodec="libx264", pix_fmt="yuv420p"):
    """convert images into mp4 video

    Parameters
    ----------
    imagePatern : str
        patern where to find images. For example '/tmp/img_%03d.png'
    fps : int
        frames per seconds for the video
    videoName : str
        video name. If the folder doesn't exist, create it
    vcodec : str
        video codec to use. If x265 is installed its better, but its not always installed.
    crf : str
        I don't remember... Its something for the quality, but its works well
        0 : high quality, 51:  bad quality, 20 by default, and starting at 18 we don't see differences
    pix_fmt : str
        pixel format. I don't remember but its OK.
        If you don't specify yuv420p, you cannot read your video into the webbrowser
    """

    with Timing() as dt:
        name, ext = os.path.splitext(videoName)
        if ext != ".mp4":
            ext = ext + ".mp4"
        videoName = name + ext

        try:
            os.makedirs(os.path.dirname(videoName), exist_ok=True)
        except FileNotFoundError:
            pass

        cmd = (
            "ffmpeg "
            f" -framerate {fps} "
            f" -i {imagePatern} "
            f" -c:v {vcodec} "
            # " -profile:v high "
            f" -crf {crf} "
            f" -pix_fmt {pix_fmt} "
            f" {videoName} -y "
        )

        logger.info("ffmpeg command : \n%s", cmd)
        os.system(cmd)
    logger.warning(f"video {videoName} done! (ffmpeg time : {dt})")

    return videoName


def video2gif(videoName, gifName, gif_fps=10, scale=350):
    """convert mp4 into gif

    Parameters
    ----------
    videoName : str
        video name
    gifName : str
        output gif name
    gif_fps : int, optional
        frame per seconds for the gif, by default 15
    scale : int, optional
        height in pixel size. Video scale is kept. by default 350
    """

    with Timing() as dt:
        # palette = "/tmp/palette.png"
        # filters = f"fps={gif_fps},scale=-1:{scale}:flags=lanczos"

        # cmd = "ffmpeg " f" -i {videoName} -vf " f" {filters},palettegen -y {palette}"
        # os.system(cmd)

        # cmd = "ffmpeg " f" -i {videoName} -i {palette} " f' -lavfi "{filters} [x]; [x][1:v] paletteuse" -y {gifName}'

        # os.system(cmd)
        cmd = (
            "ffmpeg "
            f" -i {videoName} "
            f' -vf "fps={gif_fps},scale=-1:{scale}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"'
            " -loop 0"
            f" -y {gifName}"
        )
        logger.error(cmd)
        os.system(cmd)
    logger.warning(f"gif {gifName} fait! (temps ffmpeg : {dt})")

    return gifName
