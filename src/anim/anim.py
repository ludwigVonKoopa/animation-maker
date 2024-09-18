import logging
import multiprocessing
import os
import warnings
from dataclasses import dataclass, field

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas
import xarray as xr
import zarr
from dask.distributed import Client, LocalCluster, as_completed

from anim.tools import Timing, get_imgName, images2video, video2gif, zarr_weight

logger = logging.getLogger(__name__)


@dataclass
class Stats:
    img_name: str = None  # filled in `process`
    img_building: float = np.nan  # filled in `process`
    img_saving: float = np.nan  # filled in `process`
    time_data_compress: float = np.nan  # filled in `dump_data`
    time_data_uncompress: float = np.nan  # filled in `load_data`
    time_data_computation: float = np.nan  # filled in `animate`
    size_data_uncompressed: float = np.nan  # filled in `dump_data`
    size_data_compressed: float = np.nan  # filled in `dump_data`

    def __or__(self, other):
        stat = Stats()
        stat.img_name = other.img_name if other.img_name is not None else self.img_name
        for k, v in other.__dict__.items():
            if k == "img_name":
                continue

            if not np.isnan(v):
                setattr(stat, k, v)
            else:
                setattr(stat, k, getattr(self, k))
        return stat

    def to_dict(self):
        return self.__dict__

    def __str__(self):
        msg = ""
        if not np.isnan(self.size_data_uncompressed):  # is not None:
            msg = msg + f"size {self.size_data_uncompressed/1e6:.2f}Mo"

        if not np.isnan(self.size_data_compressed):  # is not None:
            msg = msg + f"->{self.size_data_compressed/1e6:.2f}Mo"

        if not np.isnan(self.time_data_computation):  # is not None:
            msg = msg + f", compute={self.time_data_computation*1e3:.2f}ms"

        if not np.isnan(self.time_data_compress):  # is not None:
            msg = msg + f", compress={self.time_data_compress*1e3:.2f}ms"
        if not np.isnan(self.img_building):  # is not None:
            msg = msg + ""
        if not np.isnan(self.img_saving):  # is not None:
            msg = msg + ""

        return msg


class StatStorage:
    def __init__(self):
        self.data = dict()

    def __call__(self, stat: Stats):
        img_name = stat.img_name
        if img_name not in self.data:
            self.data[img_name] = stat
        else:
            self.data[img_name] |= stat

    def __getitem__(self, stat):
        return self.data[stat.img_name]

    def describe(self):
        df = pandas.DataFrame(list(x.to_dict() for x in self.data.values()))
        del df["img_name"]
        units = {}  # "img_name": "img_name"}
        for k in "size_data_uncompressed", "size_data_compressed":
            df[k] = df[k] / 1e6
            units[k] = f"{k[5:]} (Mo)"

        for k in ("time_data_compress", "time_data_uncompress", "time_data_computation"):
            df[k] = df[k] * 1e3
            units[k] = f"{k[5:]} (ms)"

        for k in ("img_building", "img_saving"):
            units[k] = f"{k[4:]} (s)"

        df.columns = [f"{units[k]}" for k in df.columns]
        return df.describe()


@dataclass
class AnimationInfo:
    imagePatern: str
    checkIfImageExist: bool = False
    onlyCompute: bool = False
    savefig_kwargs: dict = field(default_factory=dict)


def load_data(raw: xr.Dataset | zarr.hierarchy.Group):
    if isinstance(raw, zarr.hierarchy.Group):
        with Timing() as timing:
            ds = xr.open_zarr(raw.store, chunks=None).load()
            ds.attrs.update(raw.attrs)
        return ds, Stats(time_data_uncompress=timing.dt)

    return raw, Stats()


def dump_data(ds: xr.Dataset or zarr.hierarchy.Group, max_size=1e6, encoding: dict() or None = None):
    # if data is already compressed
    stats = Stats(size_data_uncompressed=ds.nbytes)

    if isinstance(ds, zarr.hierarchy.Group):
        stats.size_data_compressed = zarr_weight(ds)
        return ds, stats

    elif ds.nbytes > max_size:
        zg = zarr.group()
        with Timing() as timing:
            ds.to_zarr(zg._store, mode="w", encoding=encoding)

        stats.size_data_compressed = zarr_weight(zg)
        stats.time_data_compress = timing.dt
        return zg, stats
    else:
        return ds, stats


def process(i, data, f_plot, animationInfo: AnimationInfo):
    """function started on every worker, for each image"""

    img_name = animationInfo.imagePatern % i
    stats = Stats(img_name=img_name)

    if animationInfo.checkIfImageExist:
        if os.path.exists(img_name):
            return stats

    ds, stat = load_data(data)
    stats |= stat

    with warnings.catch_warnings():
        warnings.filterwarnings(
            action="ignore", message="Starting a Matplotlib GUI outside of the main thread will likely fail"
        )
        with Timing() as timer:
            fig = f_plot(i, ds)
    stats.img_building = timer.dt

    if fig is None:
        raise Exception("plot function did not return anything. It should return a matplotlib Figure")

    if not isinstance(fig, matplotlib.figure.Figure):
        raise Exception(f"plot function did not return a matplotlib.figure.Figure, but  '{type(fig)}'")

    if animationInfo.onlyCompute:
        return fig, stats

    try:
        with Timing() as timer:
            fig.savefig(img_name, **animationInfo.savefig_kwargs)  # enregistre l'image
    except FileNotFoundError as err:
        logger.error(f"problem when saving {img_name}")
        raise err

    stats.img_saving = timer.dt

    # sometimes not all artists are deleted
    try:
        for ax in fig.axes:
            for obj_name in [
                "artists",
                "lines",
                "texts",
                "_colorbars",
                "_path_effects",
                "collections",
            ]:
                for obj in list(getattr(ax, obj_name)):
                    obj.remove()
    except Exception:
        pass

    # delete matplotlib figure
    plt.close(fig)
    return stats


def animate(
    f_plot,
    fps,
    workFolder,
    compute=None,
    max_frames=None,
    savefig_kwargs=dict(),
    client=None,
    show=False,
    gif=False,
    force=False,
    nprocess=0,
    only_convert=False,
    # only=[],
    max_memory_ds=1e6,
    # max_memory_dump=1e6,
    # stdout=True,
):
    # at least one of max_frames and compute have to be defined
    if max_frames is None and compute is None:
        raise ValueError("max_frames or compute() have to be defined")

    # both are defined : OK
    elif (max_frames is not None) and (compute is not None):
        compute = compute

    # only max_frames is defined => loop until the end
    elif max_frames is None:
        max_frames = -10

    elif compute is None:

        def custom_compute():
            for _ in range(max_frames):
                yield xr.Dataset()

        compute = custom_compute

    iter_compute = iter(compute())

    os.makedirs(workFolder, exist_ok=True)
    imageNames = os.path.join(workFolder, "imgs", get_imgName(max_frames))
    os.makedirs(os.path.dirname(imageNames), exist_ok=True)
    # tmpFolder = os.path.join(workFolder, "tmp")
    logger.info(f"image will be saved under : {imageNames}")

    # si on veut créer un gif
    if gif is not False:
        max_frames = fps * gif

    animationInfo = AnimationInfo(imagePatern=imageNames, checkIfImageExist=not force, savefig_kwargs=savefig_kwargs)

    # this wrap function is needed to pass the f_plot function
    def _process(i, data):
        return process(i, data, f_plot, animationInfo)

    statStorage = StatStorage()
    need_delete_client = False

    if not only_convert:
        if force:
            os.system(f"rm -rf {os.path.dirname(imageNames)}")
            os.system(f"mkdir -p {os.path.dirname(imageNames)}")
            # os.system(f"rm -rf {tmpFolder}")

        if client is None:
            need_delete_client = True
            n_workers = nprocess if nprocess > 0 else multiprocessing.cpu_count() - 1

            cluster = LocalCluster(processes=True, n_workers=n_workers, threads_per_worker=1)
            client = Client(cluster)

        # if its a function, execute it
        elif hasattr(client, "__call__"):
            client = client()
            need_delete_client = True

        else:
            pass

        dask_info = client.scheduler_info()
        logger.info(dask_info["services"])
        logger.info(f"nbr workers : {len(dask_info['workers'])}")

        futures = []
        dict_futures = {}

        i_image = -1
        str_max_frames = max_frames if max_frames > 0 else "???"

        while i_image != max_frames:
            i_image += 1

            image_name = imageNames % i_image

            try:
                with Timing() as timer:
                    ds = next(iter_compute)
            except StopIteration:
                break

            stat = Stats(img_name=image_name, time_data_computation=timer.dt)
            statStorage(stat)

            if os.path.exists(image_name):
                logger.debug(f"img {i_image+1:03d}/{str_max_frames} already exist")
                continue

            data, stat2 = dump_data(ds)
            statStorage(stat | stat2)

            r = client.submit(_process, i_image, data)
            futures.append(r)
            dict_futures[r] = i_image

            logger.debug(f"img {i_image+1:03d}/{str_max_frames} : {statStorage[stat]}")

        logger.info("%d futures to be computed", len(futures))

        _tot = len(futures)
        for i_future, future in enumerate(as_completed(futures)):
            if future.status == "error":
                import traceback

                msg = f"Future [{i_future+1:03d}/{_tot}]: NOK\n"
                msg += f"  args = {dict_futures[future]}\n"
                msg += f"  exception = {future.exception()}\n"
                msg += f"  traceback = {traceback.print_tb(future.traceback())}"
                logger.debug(msg)

            else:
                try:
                    stat = future.result()
                except Exception:
                    msg = "problems with future reception"
                    logger.debug(msg)

                statStorage(stat)

                logger.debug(f"fig {i_future+1:03d}/{_tot} done : {statStorage[stat]}")

        logger.info("%d futures computed", len(futures))

    if need_delete_client:
        client.close()
        client.cluster.close()

    videoName = os.path.join(workFolder, "video.mp4")
    name, ext = os.path.splitext(videoName)
    if ext != ".mp4":
        ext = ext + ".mp4"

    if gif is not False:
        name = name + f"_{gif:d}s"
    videoName = name + ext

    real_videoName = images2video(imageNames, fps, videoName)

    if gif is not False:
        name, ext = os.path.splitext(real_videoName)
        gifName = name + ".gif"

        video2gif(videoName, gifName)

    print(statStorage.describe())
