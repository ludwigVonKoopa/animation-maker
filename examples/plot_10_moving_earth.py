"""
Make the earth go round
#######################

Small example showing how to make the earth moving

"""

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt

ANIM_FPS = 60
ANIM_OUTPUT_FOLDER = "animation/example_10"

ANIM_MAX_FRAMES = ANIM_FPS * 10


def plot(i_image, *args):
    """créée une figure"""

    # à chaque image, on augmente la longitude
    dlon = (i_image / ANIM_FPS) * 36
    center_lon = dlon % 360
    center_lat = 0

    fig = plt.figure(figsize=(4, 4), dpi=90)

    proj2 = ccrs.Orthographic(central_latitude=center_lat, central_longitude=center_lon % 360)

    ax = fig.add_subplot(1, 1, 1, projection=proj2)

    ax.coastlines()
    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.OCEAN)
    ax.set_global()

    ax.set_title(f"frame={i_image:03d}, camera_lon={center_lon:7.2f}, camera_lat={center_lat:7.2f}")

    return fig
