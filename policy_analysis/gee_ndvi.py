
import ee 
import geemap
import geopandas as gpd
import time
import os
#authenticate and initialise api
# ee.Authenticate()

class SentinelNDVI():
    def __init__(self):
        ee.Initialize()
        self.roi = ee.Geometry.Rectangle([-2.8524, 51.7836, -1.5161, 52.5075])
        self.folder_prefix = "SENTINEL2"
        print("Region of Interest (ROI):", self.roi.getInfo())
        
    def create_subfolder(self, folder_list):
        for folder in folder_list:
            folder = f"{self.folder_prefix}{folder}"
            path = os.path.join(f'ndvi/SENTINEL2/{folder}')
            if not os.path.exists(path):
                os.makedirs(path)
                print(f"{folder} created at {path}")

    def calculate_ndvi(self, image):
        ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        # image with the original bands and the NDVI band
        return image.addBands(ndvi)

    def mask_clouds(self, image):
        scl = image.select('SCL')  # SCL = Scene Classification Layer
        cloud_mask = scl.neq(9).And(scl.neq(10))  # Mask clouds and cirrus
        return image.updateMask(cloud_mask).copyProperties(image, ['system:time_start'])

    def sentinel2(self, year):
        for year in years:
            sentinel2 = (
                ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                .filterBounds(self.roi)
                .filterDate(f'{year}-01-01', f'{year}-12-31')
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
                .map(self.mask_clouds)
                .map(self.calculate_ndvi)
            )

            #process and clip
            median_ndvi = sentinel2.select('NDVI').median()
            worcs_fc = ee.FeatureCollection('users/hularuns/worcs_boundary_4326')
            median_ndvi = median_ndvi.clip(worcs_fc)
            #clip out the nonsense
            # no_data_val = -9999
            # median_ndvi = median_ndvi.unmask(no_data_val).updateMask(median_ndvi.neq(no_data_val))


            # Export the result to Google Drive with a bounded region.
            task = ee.batch.Export.image.toDrive(
                image=median_ndvi,
                folder = F'{self.folder_prefix}',
                description=f"MedianNDVI_{year}_no_mask",
                scale=10,  
                region=self.roi.coordinates().getInfo(),
                fileFormat='GeoTIFF',
                maxPixels=1e13
            )
            task.start()

    def run_gee_task(self, years):
        self.create_subfolder(years)
        # self.sentinel2(years)
        
        while True:
            tasks = ee.batch.Task.list()
            ongoing_tasks = [task for task in tasks if task.status().get('state') in ['RUNNING', 'READY']]

            if len(ongoing_tasks) == 0:
                print("No ongoing tasks. Shit's probably finished.")
                break

            for task in ongoing_tasks:
                status = task.status()
                print(status)
                print(f"Task ID: {status['id']}")
                print(f"Description: {status['description']}")
                print(f"State: {status['state']}")
                print(f"Creation Time: {status['creation_timestamp_ms']} ms")
                print(f"Update Time: {status['update_timestamp_ms']} ms")
                print('-' * 60)
                

            time.sleep(10)

if __name__ == "__main__":
    
    sentinel = SentinelNDVI()
    years = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
    sentinel.run_gee_task(years)