from sklearn.linear_model import LinearRegression
import numpy as np
import matplotlib.pyplot as plt
import os
import rasterio
import rioxarray as rxr

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

years = []

mean_ndvi_values = []

for file in file_paths:
    image_year = (os.path.split(file))[-1].split("_")[1] # gets year value as it's second element in this split.
    years.append(image_year)
    with rasterio.open(file) as src:
        image = src.read(1)
        mean_ndvi = np.nanmean(image)
        mean_ndvi_values.append(mean_ndvi)
        
plt.figure(figsize=(10, 6))
plt.plot(years, mean_ndvi_values, marker='o', linestyle='-', color='b', label='Mean NDVI')
plt.title("Mean NDVI Over the Years")
plt.xlabel("Year")
plt.ylabel("Mean NDVI")
plt.grid(True)
plt.legend()
plt.show()