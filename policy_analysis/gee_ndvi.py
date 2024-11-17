
import ee 
import geemap
import geopandas as gpd
import time
#authenticate and initialise api
# ee.Authenticate()




#just do it by west midlands kind of area and clip specifically later - kind of more efficient


# Load and process Sentinel-2 data

class SentinelNDVI():
    def __init__(self):
        ee.Initialize()
        self.roi = ee.Geometry.Rectangle([-2.8524, 51.7836, -1.5161, 52.5075])
        print("Region of Interest (ROI):", self.roi.getInfo())

    def calculate_ndvi(self, image):
        ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        # image with the original bands and the NDVI band
        return image.addBands(ndvi)

    def mask_clouds(self, image):
        scl = image.select('SCL')  # SCL = Scene Classification Layer
        cloud_mask = scl.neq(9).And(scl.neq(10))  # Mask clouds and cirrus
        return image.updateMask(cloud_mask).copyProperties(image, ['system:time_start'])

    
    def sentinel2(self):
        sentinel2 = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(self.roi)
            .filterDate('2018-01-01', '2018-12-31')
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
            .map(self.mask_clouds)
            .map(self.calculate_ndvi)
        )

        #process and clip
        median_ndvi = sentinel2.select('NDVI').median()
        worcs_fc = ee.FeatureCollection('users/hularuns/worcs_boundary_4326')
        median_ndvi = median_ndvi.clip(worcs_fc)
        #clip out the nonsense
        no_data_val = -9999
        median_ndvi = median_ndvi.unmask(no_data_val).updateMask(median_ndvi.neq(no_data_val))


        # Export the result to Google Drive with a bounded region.
        task = ee.batch.Export.image.toDrive(
            image=median_ndvi,
            folder = 'worcs_ndvi',
            description='NDVI_sentinel_2018',
            scale=10,  
            region=self.roi.coordinates().getInfo(),
            fileFormat='GeoTIFF',
            maxPixels=1e13
        )
        return task

    def run_gee_task(self):
        task = self.sentinel2()
        task.start()
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
                print('-' * 40)

            time.sleep(10)

if __name__ == "__main__":
    sentinel = SentinelNDVI()
    sentinel.run_gee_task()