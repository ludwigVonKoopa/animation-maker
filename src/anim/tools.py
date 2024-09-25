import logging
import os
import time

import numpy as np
import xarray as xr

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


def image_patern(n_frames=None):
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


def images2video(imagePatern, fps, videoName, crf=24, vcodec="libx264", pix_fmt="yuv420p", ffmpeg_log=False):
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
    ffmpeg_log : bool
        print all ffmpeg logs. If not specified, run `ffmpeg` with `-loglevel quiet`
    """

    with Timing() as dt:
        _check_video_name(videoName)

        try:
            os.makedirs(os.path.dirname(videoName), exist_ok=True)
        except FileNotFoundError:
            pass

        if ffmpeg_log:
            _cmd = "ffmpeg "
        else:
            _cmd = "ffmpeg -loglevel error "

        cmd = (
            f"{_cmd}"
            f" -framerate {fps} "
            f" -i {imagePatern} "
            f" -c:v {vcodec} "
            # " -profile:v high "
            f" -crf {crf} "
            f" -pix_fmt {pix_fmt} "
            f" {videoName} -y "
        )

        logger.info("ffmpeg command : \n%s", cmd)
        res = os.system(cmd)

    if res != 0:
        logger.error("video not created, ffmpeg error. Please use -v DEBUG to have full ffmpeg debug output")
    else:
        logger.warning(f"video {videoName} done! (ffmpeg time : {dt})")

    return videoName


def _check_video_name(videoName):
    name, ext = os.path.splitext(videoName)
    if ext != ".mp4":
        msg = "Please give a valid videoName which ends by '.mp4'"
        logger.error(msg)
        raise ValueError(msg)


def video2gif(videoName, gif_fps=10, scale=350, ffmpeg_log=False):
    """convert mp4 into gif

    Parameters
    ----------
    videoName : str
        video name
    gif_fps : int, optional
        frame per seconds for the gif, by default 15
    scale : int, optional
        height in pixel size. Video scale is kept. by default 350
    ffmpeg_log : bool
        print all ffmpeg logs. If not specified, run `ffmpeg` with `-loglevel quiet`
    """

    with Timing() as dt:
        _check_video_name(videoName)

        gifName = videoName.replace(".mp4", ".gif")
        # palette = "/tmp/palette.png"
        # filters = f"fps={gif_fps},scale=-1:{scale}:flags=lanczos"

        # cmd = "ffmpeg " f" -i {videoName} -vf " f" {filters},palettegen -y {palette}"
        # os.system(cmd)

        # cmd = "ffmpeg " f" -i {videoName} -i {palette} " f' -lavfi "{filters} [x]; [x][1:v] paletteuse" -y {gifName}'

        # os.system(cmd)
        if ffmpeg_log:
            _cmd = "ffmpeg"
        else:
            _cmd = "ffmpeg -loglevel error "

        cmd = (
            f"{_cmd}"
            f" -i {videoName} "
            f' -vf "fps={gif_fps},scale=-1:{scale}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"'
            " -loop 0"
            f" -y {gifName}"
        )
        logger.info(cmd)
        res = os.system(cmd)

    if res != 0:
        logger.error("video not created, ffmpeg error. Please use -v DEBUG to have full ffmpeg debug output")
    else:
        logger.warning(f"gif {gifName} fait! (temps ffmpeg : {dt})")

    return gifName


def parallelize_computation(func, data_iterator, client=None):
    pass


def _sanitize_inputs(max_frames, compute):
    # at least one of max_frames and compute have to be defined
    if max_frames is None and compute is None:
        raise ValueError("`max_frames` or `compute` have to be defined")

    # both are defined : OK
    elif (max_frames is not None) and (compute is not None):
        # compute = compute
        pass

    # only max_frames is defined => loop until the end using compute
    elif max_frames is None:
        max_frames = -10

        if not hasattr(compute, "__call__"):
            raise ValueError("`compute` need to be a function. Please check docstring to provide correct function")

    elif compute is None:

        def custom_compute():
            for _ in range(max_frames):
                yield xr.Dataset()

        compute = custom_compute

    return max_frames, iter(compute())
