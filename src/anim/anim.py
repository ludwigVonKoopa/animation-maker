import logging
import multiprocessing
import os
import warnings

import matplotlib
import matplotlib.pyplot as plt
from dask.distributed import Client, LocalCluster, as_completed

from anim.data import AnimationInfo, Stats, StatStorage, dump_data, load_data
from anim.tools import Timing, _sanitize_inputs, image_patern, images2video

logger = logging.getLogger(__name__)


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
    return None, stats


def get_imagePatern(imageFolder, max_frames):
    return os.path.join(imageFolder, image_patern(max_frames))


def simple_building(
    f_plot,
    compute=None,
    max_frames=None,
    indices=[],  # only
    savefig_kwargs=dict(),
    show=None,
):
    max_frames, iter_compute = _sanitize_inputs(max_frames, compute)

    if len(indices) == 0:
        indices = [0]
    logger.info(f"we will build only images : {indices}")

    _i = -1
    while len(indices) > 0:
        _i += 1

        try:
            ds = next(iter_compute)
        except StopIteration:
            break

        if _i in indices:
            indices.remove(_i)
            logger.info(f"processing image i={_i}")
            if show is not False:
                fig = f_plot(_i, ds)

                if show is None:
                    plt.show()
                else:
                    name = show.format(i=_i)
                    fig.savefig(name, **savefig_kwargs)
                    logger.info(f"figure i={_i} saved in '{name}'")

            else:
                f_plot(_i, ds)
    return


def build_images(
    f_plot,
    imageFolder,
    compute=None,
    max_frames=None,
    force=False,
    nprocess=0,
    savefig_kwargs=dict(),
    client=None,
    max_memory_ds=1e6,
):
    max_frames, iter_compute = _sanitize_inputs(max_frames, compute)

    os.makedirs(imageFolder, exist_ok=True)
    imageNames = get_imagePatern(imageFolder, max_frames)
    logger.info(f"image will be saved under : {imageNames}")

    animationInfo = AnimationInfo(
        imagePatern=imageNames,
        checkIfImageExist=not force,
        savefig_kwargs=savefig_kwargs,  # onlyCompute=only
    )

    # this wrap function is needed to pass the f_plot function
    def _process(i, data):
        return process(i, data, f_plot, animationInfo)

    statStorage = StatStorage()
    need_delete_client = False

    if force:
        logger.warning(os.path.dirname(imageNames))
        os.system(f"rm -rf {os.path.dirname(imageNames)}")
        os.system(f"mkdir -p {os.path.dirname(imageNames)}")

    if client is None:
        logger.info("building dask local client..")
        need_delete_client = True
        n_workers = nprocess if nprocess > 0 else multiprocessing.cpu_count() - 1

        cluster = LocalCluster(processes=True, n_workers=n_workers, threads_per_worker=1)
        client = Client(cluster)

    # if its a function, execute it
    elif hasattr(client, "__call__"):
        logger.info("building dask custom client..")
        client = client()
        need_delete_client = True

    else:
        logger.info("no need to build dask client (given by parameter)")

    dask_info = client.scheduler_info()
    logger.info(
        f"dask client built. nbr workers : {len(dask_info['workers'])}, dashboard : {dask_info["services"]["dashboard"]}"
    )

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

        stat = Stats(img_name=image_name, time_data_computation=timer.dt, size_data_uncompressed=ds.nbytes)
        statStorage(stat)

        if animationInfo.checkIfImageExist and os.path.exists(image_name):
            logger.debug(f"img {i_image+1:03d}/{str_max_frames} already exist")
            continue

        data, stat2 = dump_data(ds)
        statStorage(stat | stat2)

        r = client.submit(_process, i_image, data)
        futures.append(r)
        dict_futures[r] = i_image

        logger.debug(f"img {i_image+1:03d}/{str_max_frames} : {statStorage[stat]}")

    nbImagesAlreadyDone = statStorage.size - len(futures)
    if nbImagesAlreadyDone > 0:
        logger.info(f"{nbImagesAlreadyDone} images already computed")
    logger.info("%d images to be computed..", len(futures))

    with Timing() as dt_computation:
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
                    _, stat = future.result()
                except Exception:
                    msg = "problems with future reception"
                    logger.debug(msg)

                statStorage(stat)

                logger.debug(f"fig {i_future+1:03d}/{_tot} done : {statStorage[stat]}")

    if need_delete_client:
        import time

        time.sleep(0.5)
        client.close()
        client.cluster.close()

    logger.info(
        f"{len(futures)} images computed ({dt_computation})",
    )
    return imageNames, statStorage.build_dataframe()


def animate(
    f_plot,
    workFolder,
    fps,
    compute=None,
    max_frames=None,
    savefig_kwargs=dict(),
    client=None,
    force=False,
    nprocess=0,
    only_convert=False,
    max_memory_ds=1e6,
    ffmpeg_log=False,
):
    """create images in parallel and then combine them in a video


    Parameters
    ----------
    f_plot : callable
        function used to build the image. See Note for more infos
    workFolder : str
        path where all the images and video will be created
    fps : int
        frame per seconds for the video
    compute : callable, optional
        function which yield data to be used by `f_plot`. See Note for more infos. By default None
    max_frames : int, optional
        maximum of images to build, by default None
    savefig_kwargs : _type_, optional
        options to pass to `fig.savefig(...)`, by default dict()
    client : dask.Client or callable, optional
        dask client used for building images.
        You can pass a function which return a dask.Client.
        by default None
    force : bool, optional
        if True, force regeneration of all images.
        if False, image already computed and saved on disk won't be computed.
        By default False
    nprocess : int, optional
        number of cpu to use when not providing a dask.Client.
        If not provided, use all cpus
    only_convert : bool, optional
        if True, don't generate images at all. We only build the video, by default False
    max_memory_ds : int, optional
        if data provided by `compute` exceed max_memory_ds, it will be compressed in zarr to minimise ram usage.
        By default 1e6
    ffmpeg_log : bool, optional
        print all ffmpeg logs. If not specified, run `ffmpeg` with `-loglevel quiet

    Returns
    -------
    str
        return the video name
    """

    os.makedirs(workFolder, exist_ok=True)
    workFolder = os.path.normpath(workFolder)
    imageFolder = os.path.join(workFolder, "imgs")

    if only_convert:
        imageNames = get_imagePatern(workFolder, max_frames)
    else:
        imageNames, df = build_images(
            f_plot,
            imageFolder,
            compute=compute,
            max_frames=max_frames,
            force=force,
            nprocess=nprocess,
            savefig_kwargs=savefig_kwargs,
            client=client,
            max_memory_ds=max_memory_ds,
        )
        logger.info("\n" + str(df.describe()))

    videoName = "video.mp4"

    pathVideo = os.path.join(workFolder, videoName)
    name, ext = os.path.splitext(pathVideo)
    if ext != ".mp4":
        ext = ext + ".mp4"

    images2video(imageNames, fps, pathVideo, ffmpeg_log=ffmpeg_log)
    return pathVideo
