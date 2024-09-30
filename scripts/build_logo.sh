

if  conda list --name latest >/dev/null 2>&1 ; then
    # its readthedoc, they overwrite the name of the conda env
    echo "activating latest env already done"
    # conda activate latest
else
    # local or normal config, its the name defined in environment_dev.yml
    conda activate anim_dev
    echo "activating anim_dev env"
fi


SCRIPT=$(realpath "$0")
SCRIPTPATH=$(dirname "$SCRIPT")
GIFFILE=$SCRIPTPATH/../doc/source/_static/logo_low.gif

which python
which anim
which ffmpeg

if [ ! -f $GIFFILE ]; then
    echo "File $GIFFILE not found!"

    anim $SCRIPTPATH/script.py  --folder $SCRIPTPATH/tmp --no-convert
    GIF_FOLDER=$(dirname "$GIFFILE")
    mkdir -p $GIF_FOLDER

    ffmpeg -loglevel error -framerate 50 -f image2  \
        -i $SCRIPTPATH/tmp/imgs/img_%03d.png  \
        -filter_complex "[0:v] split [a][b]; [a] palettegen=reserve_transparent=on:transparency_color=000000 [p];[b][p] paletteuse" \
        -gifflags +transdiff -loop 0 $GIFFILE  -y
fi

# rm -rf $SCRIPTPATH/tmp
