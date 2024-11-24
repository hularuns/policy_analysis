from sklearn.linear_model import LinearRegression
import numpy as np
import matplotlib.pyplot as plt
import os
import rasterio
from rasterio.mask import mask
import rioxarray as rxr
import geopandas as gpd 
from pprint import pprint
from tqdm import tqdm

input_dir = "ndvi/SENTINEL2/reprojected"
file_paths = sorted([os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.endswith(".tif")])

def raster_difference(file_1, file_2):
    """ Differences a raster and shows the plot. 
        Returns the difference in a rasterio compliant array `nump.ndarray`"""

    with rasterio.open(file_1) as src1:
        top_raster = src1.read(1)
    with rasterio.open(file_2) as bot_src:
        bottom_raster = bot_src.read(1)
        
    if top_raster.shape == bottom_raster.shape:
        difference = bottom_raster - top_raster
        
        plt.figure(figsize=(10, 6))
        plt.imshow(difference, cmap='RdYlGn', interpolation='none')  # Plot using a color map
        plt.title(f"Difference Between {file_1} and {file_2}")
        plt.colorbar(label="NDVI Difference")
        plt.show()
        print(type(difference))
        return difference
    else:    
        print("The images have different shapes. Please ensure the rasters are aligned.")
# raster_difference(file_paths[0], file_paths[-1])





data = {}
interest_areas = "interest_areas/bda.gpkg"

for file in tqdm(file_paths):
    image_year = (os.path.split(file))[-1].split("_")[1] # gets year value as it's second element in this split.
    
    with rasterio.open(file) as src:
        image = src.read(1)

        gdf = gpd.read_file(interest_areas, layer = 'bdas')
        if gdf.crs != src.crs:
            gdf = gdf.to_crs(src.crs)
            print(f"gdf was in {gdf.crs} projection and has now been converted to {src.crs} in line with the raster")

        gdf = gdf[gdf.is_valid]

        for idx, row in gdf.iterrows():
            # Extract the geometry (polygon) to use for clipping
            geometry = [row['geometry']] 
            out_image, out_transform = mask(src, geometry, crop=True)
            poly_name = row['project_name'] 
            mean_ndvi = np.nanmean(out_image)

            if poly_name not in data:
                data[poly_name] = {} 
            data[poly_name][image_year] = mean_ndvi

            # plt.figure(figsize=(10, 6))
            # plt.imshow(out_image[0], cmap='RdYlGn')
            # plt.title(f"Clipped Raster for Polygon {poly_name}")
            # plt.colorbar(label="NDVI Values")
            # plt.show()

first_key = next(iter(data))
key_years = data.get(first_key).keys()

years = list(key_years)
print(years)
plt.figure(figsize = (10, 6))

for poly_name, year_data in tqdm(data.items()):
    mean_ndvi_values = [year_data[str(year)] for year in years]
    
    plt.plot(years, mean_ndvi_values, label = poly_name)

plt.xlabel('Year')
plt.ylabel('Mean NDVI')
plt.title('Mean NDVI Over Time for Different Policy Areas')
plt.legend(title=f"NDVI over BDAs between {min(years)} - {max(years)}")
plt.grid(True)
plt.show()
        
