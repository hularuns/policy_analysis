import ee
import time

# Authenticate and initialize API
# ee.Authenticate()

class LandsatNDVI():
    def __init__(self):
        ee.Initialize()
        self.roi = ee.Geometry.Rectangle([-2.8524, 51.7836, -1.5161, 52.5075])
        print("Region of Interest (ROI):", self.roi.getInfo())

    def calculate_ndvi(self, image):
        # NDVI using Landsat 7 bands
        ndvi = image.normalizedDifference(['B4', 'B3']).rename('NDVI')
        return image.addBands(ndvi)

    def mask_clouds_and_gaps(self, image):
        # Mask clouds and shadows using the QA_PIXEL band
        qa = image.select('QA_PIXEL')
        cloud_bit = ee.Number(2).pow(3).int()  # Bit 3 indicates cloud
        shadow_bit = ee.Number(2).pow(4).int()  # Bit 4 indicates cloud shadow
        mask = (
            qa.bitwiseAnd(cloud_bit).eq(0)
            .And(qa.bitwiseAnd(shadow_bit).eq(0))
        )
        
        # Mask out missing pixels due to the SLC-off issue
        slc_off_mask = image.select('B4').mask()
        
        # Combine cloud/shadow mask and SLC-off mask
        final_mask = mask.And(slc_off_mask)
        return image.updateMask(final_mask).copyProperties(image, ['system:time_start'])

    def landsat7(self, years):
        for year in years:
            # Filter the Landsat 7 collection and process for NDVI
            landsat = (
                ee.ImageCollection("LANDSAT/LE07/C02/T1_RT")
                .filterBounds(self.roi)
                .filterDate(f'{year}-01-01', f'{year}-12-31')  # Year range
                .map(self.mask_clouds_and_gaps)  # Mask clouds and fill gaps
                .map(self.calculate_ndvi)  # Add NDVI band
            )
            
            # Temporal compositing to fill gaps
            composite = landsat.select('NDVI').median()
            worcs_fc = ee.FeatureCollection('users/hularuns/worcs_boundary_4326')
            composite = composite.clip(worcs_fc)

            # Export the result to Google Drive
            task = ee.batch.Export.image.toDrive(
                image=composite,
                folder='projects/policy_analysis/ndvi/landsat7',
                description=f"NDVI_Landsat7_{year}_gap_filled",
                scale=30,  # 30m resolution for Landsat 7
                region=self.roi.coordinates().getInfo(),
                fileFormat='GeoTIFF',
                maxPixels=1e13
            )
            task.start()

    def run_gee_task(self, years):
        self.landsat7(years)
        
        while True:
            tasks = ee.batch.Task.list()
            ongoing_tasks = [task for task in tasks if task.status().get('state') in ['RUNNING', 'READY']]

            if len(ongoing_tasks) == 0:
                print("No ongoing tasks. Processing probably finished.")
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
    landsat = LandsatNDVI()
    years = [2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
    landsat.run_gee_task(years)
