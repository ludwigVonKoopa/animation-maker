# @pytest.mark.new
# @pytest.mark.mpl_image_compare(filename="oui.png")
# def test_basic_with_mpl():
#     import cartopy.crs as ccrs
#     import matplotlib.pyplot as plt

#     fig = plt.figure(figsize=(9, 4))
#     ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

#     ax.gridlines(
#         alpha=0.2,
#         color="black",
#         draw_labels=dict(bottom="x", right=False, top=False, left="y"),
#         auto_update=True,
#     )
#     return fig
