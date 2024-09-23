import logging
import os
import shutil
from pathlib import PurePosixPath

from jinja2 import Template
from sphinx_gallery.scrapers import matplotlib_scraper

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
    ANIM_SAVEFIG_KWARGS = namespace.get("ANIM_SAVEFIG_KWARGS", dict())
    compute = namespace.get("compute", None)

    name = os.path.splitext(os.path.os.path.basename(block_vars["src_file"]))[0]
    PATH_EXEMPLE = gallery_conf["examples_dirs"][0]  # <== should be a list with 1 element
    FOLDER = os.path.join(PATH_EXEMPLE, "../example_built", name)
    # print("name : ", name)
    os.makedirs(FOLDER, exist_ok=True)

    image_path_iterator = block_vars["image_path_iterator"]

    image_path = image_path_iterator.next()
    image_path = PurePosixPath(image_path)

    image_name = image_path.with_suffix("." + "gif")
    video_name = image_path.with_suffix("." + "mp4")
    print(image_name, video_name)

    videoName = anim.animate(
        plot,
        FOLDER,
        fps=ANIM_FPS,
        compute=compute,
        max_frames=ANIM_MAX_FRAMES,
        savefig_kwargs=ANIM_SAVEFIG_KWARGS,
        # gif=10,
        # force=True,
        # only_convert=True,
    )
    path_gif = anim.video2gif(videoName, 10)

    # gif_file = glob(os.path.join(FOLDER, "*.gif"))[0]
    # print(videoName)
    # print(video_name)
    shutil.copy2(path_gif, image_name)
    shutil.copy2(videoName, video_name)
    # print(gallery_conf["src_dir"])
    # import pprint

    # print("gallery_conf : ")
    # pprint.pprint(gallery_conf)
    # print("block_vars : ")
    # pprint.pprint(block_vars)
    # print("block : ")
    # pprint.pprint(block)
    # print("kwargs : ")
    # pprint.pprint(kwargs)
    # exit()
    # exit()
    # image_rst = figure_rst([video_name], "")
    # print(image_rst)
    # exit()
    # image_rst = figure_rst([image_name], gallery_conf["src_dir"])
    # env = Environment(loader=FileSystemLoader("templates"))
    # template = env.get_template("tutorial.jinja")
    # output = Template(template).render()
    # print(image_rst)
    # exit()
    video_rst = Template(template_video).render(videoName=video_name)
    # image_rst = image_rst  # + output
    return video_rst


template_video = """

.. video:: {{videoName}}
    :autoplay:
    :loop:

"""

template = """
Usage :
-------

bash

.. code-block:: console

    $ anim examples/{py_name}

python

.. code-block:: Python

    import anim
    anim.animate(f_plot=plot, fps=ANIM_FPS, workFolder=ANIM_OUTPUT_FOLDER, max_frames=ANIM_MAX_FRAMES)


Python file used to create the example :
----------------------------------------
"""
