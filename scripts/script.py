import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt

ANIM_FPS = 50
ANIM_OUTPUT_FOLDER = "tmp"

SECONDS = 5
ANIM_MAX_FRAMES = ANIM_FPS * SECONDS
ANIM_SAVEFIG_KWARGS = dict(transparent=True)


def plot(i_image, *args):
    """créée une figure"""

    # à chaque image, on augmente la longitude
    dlon = (i_image / ANIM_FPS) * (360 / SECONDS)
    center_lon = dlon % 360
    center_lat = 0

    fig = plt.figure(figsize=(1, 1), dpi=60)

    proj2 = ccrs.Orthographic(central_latitude=center_lat, central_longitude=center_lon % 360)

    # ax = fig.add_subplot(1, 1, 1, projection=proj2)
    ax = fig.add_axes([0, 0, 1, 1], projection=proj2, frameon=False, xticks=[], yticks=[])
    ax.coastlines()
    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.OCEAN)
    ax.set_global()
    plt.subplots_adjust(wspace=0, hspace=0)

    # ax.set_title(f"i_image={i_image:03d}, camera_lon={center_lon:7.2f}, camera_lat={center_lat:7.2f}")

    return fig
