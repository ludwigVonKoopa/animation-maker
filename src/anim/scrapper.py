import logging
import os
import shutil
from glob import glob
from pathlib import PurePosixPath

from sphinx_gallery.scrapers import figure_rst, matplotlib_scraper

import anim

logger = logging.getLogger(__name__)


def pngScrapper(block, block_vars, gallery_conf, **kwargs):
    namespace = block_vars["example_globals"]
    for var in ["ANIM_FPS", "plot"]:
        if var not in namespace:
            print(f"Carefull, it miss variable '{var}' in the exemple")
            print("we will use normal scrapper")
            return matplotlib_scraper(block, block_vars, gallery_conf, **kwargs)

    ANIM_FPS = namespace["ANIM_FPS"]
    plot = namespace["plot"]

    ANIM_MAX_FRAMES = namespace.get("ANIM_MAX_FRAMES", None)
    compute = namespace.get("compute", None)

    name = os.path.splitext(os.path.os.path.basename(block_vars["src_file"]))[0]
    PATH_EXEMPLE = gallery_conf["examples_dirs"][0]  # <== should be a list with 1 element
    FOLDER = os.path.join(PATH_EXEMPLE, "../example_built", name)

    os.makedirs(FOLDER, exist_ok=True)

    image_path_iterator = block_vars["image_path_iterator"]

    image_path = image_path_iterator.next()
    image_path = PurePosixPath(image_path)

    image_name = image_path.with_suffix("." + "gif")

    anim.animate(
        f_plot=plot,
        fps=ANIM_FPS,
        workFolder=FOLDER,
        compute=compute,
        max_frames=ANIM_MAX_FRAMES,
        gif=10,
        force=True,
    )

    gif_file = glob(os.path.join(FOLDER, "*.gif"))[0]
    shutil.copy2(gif_file, image_name)

    image_rst = figure_rst([image_name], gallery_conf["src_dir"])
    return image_rst
