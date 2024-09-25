import argparse
import logging
import multiprocessing
import traceback

import anim
import anim.log  # noqa: F401
from anim.anim import simple_building
from anim.tools import Timing

logger = logging.getLogger(__name__)


def usage():
    parser = argparse.ArgumentParser()

    parser.add_argument("pythonfile", type=str, help="python file containing functions to plot and compute date")

    parser.add_argument(
        "-v",
        "--verbose",
        action="store",
        help="verbose",
        choices=["ERROR", "WARNING", "INFO", "DEBUG"],
        default="INFO",
    )
    group1 = parser.add_argument_group("Image Creation", "parameters for image creation")

    group1.add_argument(
        "-j",
        "--nprocess",
        action="store",
        type=int,
        default=multiprocessing.cpu_count() - 1,
        help=f"number of core to use. By default, max-1 ({multiprocessing.cpu_count()-1})",
    )
    group1.add_argument(
        "--no-compute",
        action="store_true",
        help="Don't compute any images. Use only ffmpeg. Usefull if images are already computed and takes time",
    )
    group1.add_argument("-f", "--force", action="store_true", help="force saving images even if they already exist")

    group1.add_argument(
        "-s",
        "--show",
        action="store",
        nargs="?",
        const=None,
        default=False,
        help=(
            "Show the first image from animation then quit. Usefull to visualize and check if your parameters are correct, before doing all the computations. "
            "if nothing is specified after '-s', show the image with `plt.show()`. If an argument is specified, we store the image using the name specified."
            "You can specify a patern name for example `image_{i:03d}.png`, and the i will be interpolated to the indice of the image, usefull when you specified --only arg"
        ),
    )

    group1.add_argument(
        "--only",
        action="store",
        nargs="+",
        type=int,
        default=[],
        help="compute only images with specified indices, without multiprocessing. Usefull for debbuging purposes.",
    )

    group1.add_argument(
        "--ffmpeg-log",
        action="store_true",
        help="print all ffmpeg logs. If not specified, run `ffmpeg` with `-loglevel quiet`",
    )

    group2 = parser.add_argument_group("ImGifage Creation", "parameters for gif creation")

    group2.add_argument(
        "-g",
        "--gif",
        nargs="?",
        type=int,
        const=5,
        default=False,
        help="Create a 5s gif (by default) to test the animation",
    )

    group2.add_argument(
        "--folder",
        type=str,
        default=None,
        help="specify the folder where images and video will be stored. Overwrite the `ANIM_OUTPUT_FOLDER` in the python script",
    )

    return parser.parse_args()


def execfile_(filepath, _globals):
    """Executes a Python code defined in a file"""
    with open(filepath, "rb") as stream:
        source = stream.read()

    code = compile(source, filepath, "exec")
    exec(code, _globals)


def eval_config_file(filename: str):
    """Evaluate a config file."""

    namespace = dict(__file__=filename)
    logger.info(f"loading file {filename}...")
    with Timing() as dt:
        try:
            execfile_(filename, namespace)
        except SyntaxError as err:
            raise RuntimeError(f"There is a syntax error in your configuration file: {err}\n")
        except SystemExit:
            raise RuntimeError("The configuration file (or one of the modules it imports) " "called sys.exit()")
        except Exception:
            raise RuntimeError(
                "There is a programmable error in your configuration " f"file:\n\n{traceback.format_exc()}"
            )
    logger.info(f"loading done ! ({dt})")
    return namespace


def app():
    args = usage()
    anim.log.create_logger(level=args.verbose)
    with Timing() as dt:
        namespace = eval_config_file(args.pythonfile)

        FOLDER = namespace.get("ANIM_OUTPUT_FOLDER", None)
        if FOLDER is None:
            msg = "miss variable `ANIM_OUTPUT_FOLDER` in the python file"
            logging.error(msg)
            raise ValueError(msg)

        # parameter specified in command line overwrite the script one
        if args.folder is not None:
            FOLDER = args.folder

        func_plot = namespace.get("plot", None)
        if func_plot is None:
            msg = "miss function named `plot` in the python file"
            logging.error(msg)
            raise ValueError(msg)

        fps = namespace.get("ANIM_FPS", None)
        if fps is None:
            msg = "miss variable `ANIM_FPS` in the python file"
            logging.error(msg)
            raise ValueError(msg)

        compute = namespace.get("compute", None)
        savefig_kwargs = namespace.get("ANIM_SAVEFIG_KWARGS", dict())
        max_frames = namespace.get("ANIM_MAX_FRAMES", None)
        max_frames = args.gif * fps if args.gif is not False else max_frames

        get_dask_client = namespace.get("get_dask_client", None)

        if (args.show is not False) or len(args.only) > 0:
            simple_building(
                f_plot=func_plot,
                compute=compute,
                max_frames=max_frames,
                indices=args.only,
                savefig_kwargs=savefig_kwargs,
                show=args.show,
            )

        else:
            videoName = anim.animate(
                f_plot=func_plot,
                workFolder=FOLDER,
                fps=fps,
                compute=compute,
                max_frames=max_frames,
                savefig_kwargs=savefig_kwargs,
                client=get_dask_client,
                force=args.force,
                nprocess=args.nprocess,
                only_convert=args.no_compute,
                ffmpeg_log=args.ffmpeg_log,
            )

            if args.gif is not False:
                anim.video2gif(videoName, args.gif)

    logger.info(f"total time for anim tool : {dt}")


if __name__ == "__main__":
    app()
