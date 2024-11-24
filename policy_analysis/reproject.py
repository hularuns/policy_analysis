import rasterio
import os
import fiona

import rasterio 
from rasterio.enums import Resampling
import rioxarray as rxr
import matplotlib.pyplot as plt
import geopandas as gpd
import time
from pyproj import CRS


def is_valid_epsg(epsg_str: str) -> bool:
    try:
        crs = CRS.from_user_input(epsg_str)
        epsg_code = crs.to_epsg()
        return epsg_code is not None
    except Exception as e:
        print(f"Error determining valid EPSG code: {e}")
        return False
    
def parse_epsg(crs_ref):
    if isinstance(crs_ref, gpd.GeoDataFrame):
        crs_ref = crs_ref.crs  # Extract the CRS from GeoDataFrame
        # Try to get the EPSG code if possible. This is awkward with just a straight gpd.read_file. Wrap it in a fiona.open and it resolves this.
        epsg_code = CRS.from_user_input(crs_ref).to_epsg()
        if epsg_code:
            print(f"CRS was passed through as a {type(crs_ref)} object with a valid EPSG code: {epsg_code}")
        else:
            print("No EPSG code found, CRS is more complex or custom (WKT).")
    elif isinstance(crs_ref, str):
        if is_valid_epsg(crs_ref):
            print(f"CRS was passed through as a {type(crs_ref)} object with a valid EPSG code: {epsg_code}")
        else:
            print(f"Invalid crs_ref input - Not a valid EPSG code.")
    elif isinstance(crs_ref, CRS):
        epsg_code = crs_ref.to_epsg()
        if epsg_code:
            print(f"CRS was passed through as a {type(crs_ref)} object with a valid EPSG code: {epsg_code}")
        else:
            print("No EPSG code found in CRS object.")

    if epsg_code is None:
        print("Unable to determine EPSG code.")

    return epsg_code

def reproject_rasters(input_dir, 
                      crs_ref: gpd.GeoDataFrame | str | CRS = None, 
                      clip_gdf: gpd.GeoDataFrame = None, 
                      output_folder = 'reprojected'):
    """ crs_ref if using Geopandas DataFrame, input opened with fiona.open(), otherwise there's a peculiar bug with how it parses EPSG. """
    # put in tqdm ... 
    output_dir = os.path.join(input_dir, output_folder)
    os.makedirs(output_dir, exist_ok = True)
    print(f"{output_dir} has been successfully made for the reprojected outputs.")
    
    epsg_code = parse_epsg(crs_ref)
    
    if clip_gdf is not None:
        clip_gdf = clip_gdf.to_crs(epsg_code)
        
    for file in os.listdir(input_dir):
        if file.endswith(".tif"):
            input_raster_path = os.path.join(input_dir, file)
            opened_file = rxr.open_rasterio(input_raster_path, masked = True).squeeze()
            reprojected_raster = opened_file.rio.reproject(epsg_code, resampling=Resampling.nearest) # nearest neighbour if any resampling needed - Takes mean value.
            
            if not clip_gdf.empty:
                reprojected_raster = reprojected_raster.rio.clip(clip_gdf.geometry, all_touched = True, drop = False)
                print(f"The raster has been clipped")
            
            transform = reprojected_raster.rio.transform() # Get the transformation after reprojecting
            crs = reprojected_raster.rio.crs

            kwargs = {
                'driver': 'GTiff',
                'count': 1,
                'dtype': 'float32',
                'crs': crs,
                'transform': transform,
                'width': reprojected_raster.shape[1],
                'height': reprojected_raster.shape[0],
                'compress': 'lzw'
            }
            crs = (kwargs['crs'])
            raster_name = f"{file.split('.tif')[0]}_repro.tif"
            output_raster_path = os.path.join(output_dir, raster_name)
            
            with rasterio.open(output_raster_path, 'w', **kwargs) as dst:
                dst.write_band(1, reprojected_raster.astype(rasterio.float32))

            print(f"{file} has been reprojected to CRS: {crs} and was saved to {output_raster_path} \n {'-'*60}")


    

if __name__ == "__main__":
    
    #example input with sentinel 2 data.
    interest_area_gpkg = "interest_areas/bda.gpkg"
    interest_layers = []
    for name in fiona.listlayers(interest_area_gpkg):
        interest_layers.append(name) 
    gdf = gpd.read_file(interest_area_gpkg, layer = interest_layers[3])
    
    
    interest_area_gpkg = "interest_areas/bda.gpkg"
    with fiona.open(interest_area_gpkg, layer="bdas") as src:
        gdf = gpd.read_file(interest_area_gpkg, layer="bdas")
    clip_path = "interest_areas/worcs_boundary.shp"
    
    with fiona.open(clip_path) as src:
        clip_gdf = gpd.read_file(clip_path)

    #run the reproject
    reproject_rasters("ndvi/SENTINEL2", crs_ref = gdf, clip_gdf = clip_gdf)        
