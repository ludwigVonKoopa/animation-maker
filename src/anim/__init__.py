"""Top-level package for animation-maker."""

from importlib import metadata

from anim import log  # noqa: F401
from anim.anim import animate  # noqa: F401

__version__ = metadata.version(__package__)
__author__ = """LudwigVonKoopa"""
__email__ = "49512274+ludwigVonKoopa@users.noreply.github.com"

del metadata
