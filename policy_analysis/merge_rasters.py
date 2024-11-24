import rasterio
import numpy as np
import os
from scipy.interpolate import interp1d
import subprocess

# Define directories

class MergeMedianRasters():
    def __init__(self, directory):
        self.directory = directory
        self.output_dir = os.path.join(directory, "merged_outputs") 
        self.filled_dir = os.path.join(self.output_dir, "filled")

        os.makedirs(self.output_dir, exist_ok = True)
        os.makedirs(self.filled_dir, exist_ok = True) 
        
    def valid_subdirectory(self, subdir):
        """
        Checks if a subdirectory contains valid raster files (.tif).
        Returns True if valid, otherwise False.
        """
        raster_files = [f for f in os.listdir(subdir) if f.endswith(".tif")]
        return len(raster_files) > 0
    
    def merge_median_rasters(self):
        
        for subdir, dirs, files in os.walk(self.directory):
            # if self.valid_subdirectory(subdir):
            if "LANDSAT" in subdir:
                raster_files = [
                    os.path.join(subdir, file) 
                    for file in os.listdir(subdir) if file.endswith(".tif")
                ]
                
                if len(raster_files) < 1:
                    print(f"No raster files found in {subdir}.")
                    continue
                print(f"There are {len(raster_files)} being processed")
                stack = []

                # Read and stack rasters
                for file in raster_files:
                    with rasterio.open(file) as src:
                        data = src.read(1)
                        nodata = src.nodata
                        if nodata is not None:
                            data[data == nodata] = np.nan
                        stack.append(data)

                stack = np.stack(stack, axis=0)
                print("Stack shape:", stack.shape)

                if np.all(np.isnan(stack)):
                    print("All input rasters contain only NoData values.")
                    continue
                median_array = np.nanmedian(stack, axis=0)
                print("Median array stats: Min =", np.nanmin(median_array), "Max =", np.nanmax(median_array))

                subname = os.path.split(subdir)[1]
                if 'LANDSAT' in subname:
                    year = (subname.split("_")[-1])
                
                # Save median raster
                median_raster = os.path.join(self.output_dir, f"median_raster_{year}.tif")
                print(f"Median raster save location: {median_raster}")
                
                with rasterio.open(raster_files[0]) as src:
                    profile = src.profile
                    profile.update(dtype=np.float32, count=1, nodata=np.nan)

                with rasterio.open(median_raster, "w", **profile) as dst:
                    dst.write(np.nan_to_num(median_array, nan=profile['nodata']).astype(np.float32), 1)
                
                interpolated_output = os.path.join(self.filled_dir, f"ndvi_filled_{year}.tif")
                self.fill_nodata_with_gdal(median_raster, interpolated_output, max_distance = 50)
        

    def fill_nodata_with_gdal(self, input_raster, output_file_path, max_distance = 50):
        """
        Uses gdal_fillnodata.py to interpolate missing values in a raster.
        """

        cmd = [
            r"C:\OSGeo4W\apps\Python312\python.exe",  # Path to Python interpreter
            r"C:\OSGeo4W\apps\Python312\Scripts\gdal_fillnodata.py",  # Path to fillnodata py file
            input_raster,          # Input raster file
            output_file_path,         # Output raster file
            "-md", str(max_distance),  # Maximum search distance for interpolation
            "-b", "1",             # Band number to process
            "-of", "GTiff"         # Output format
        ]

        try:
            subprocess.run(cmd, check=True, shell=True) 
            print(f"Filled NoData gaps in {input_raster}, output saved to {output_file_path}")
        except FileNotFoundError:
            print("Error: gdal_fillnodata.bat not found. Ensure the file exists and is in the specified path.")
        except subprocess.CalledProcessError as e:
            print(f"Error while running gdal_fillnodata: {e}")


if __name__ == "__main__":
    directory = r"G:\My Drive\projects\policy_analysis\policy_analysis\ndvi\landsat7"
    merger = MergeMedianRasters(directory=directory)
    merger.merge_median_rasters()

