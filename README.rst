Package to create animation with matplotlib


========
Overview
========

.. image:: _static/logo_low.gif


| ``anim`` is a python package to build animation from matplotlib plots.

You only have to define a fonction which return an matplotlib image, and ``anim`` takes care of the image generation, parallelisation and merging them into a video


Features
--------

* build images in parallel widh ``dask``
* merge images with ``ffmpeg``
* build gif from the video



Installation
------------

simple :

.. code-block:: console

    $ pip install anim


Credits
-------

This package was created with Cookiecutter_ using this template_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _template: https://github.com/ludwigVonKoopa/cookiecutter-python
