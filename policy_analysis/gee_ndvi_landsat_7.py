import ee
import time
import os

# Authenticate and initialize API
# ee.Authenticate()

class LandsatNDVI():
    def __init__(self):
        ee.Initialize()
        self.roi = ee.Geometry.Rectangle([-2.8524, 51.7836, -1.5161, 52.5075])
        self.folder_prefix = "LANDSAT_7_"
        print("Region of Interest (ROI):", self.roi.getInfo())
        
    def create_subfolder(self, folder_list):
        for folder in folder_list:
            folder = f"{self.folder_prefix}{folder}"
            path = os.path.join(f'ndvi/landsat7/{folder}')
            if not os.path.exists(path):
                os.makedirs(path)
                print(f"{folder} created at {path}")

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

    def landsat7_median_ndvi(self, years):
        for year in years:
            print(f"Processing year: {year}")

            # Filter the Landsat 7 collection for the year
            landsat = (
                ee.ImageCollection("LANDSAT/LE07/C02/T1_RT")
                .filterBounds(self.roi)
                .filterDate(f'{year}-01-01', f'{year}-12-31')  # Strictly within the year
                .map(self.mask_clouds_and_gaps)  # Mask clouds and SLC-off gaps
                .map(self.calculate_ndvi)  # Add NDVI band
            )

            median_ndvi = landsat.select('NDVI').median()

            worcs_fc = ee.FeatureCollection('users/hularuns/worcs_boundary_4326')
            final_ndvi = median_ndvi.clip(worcs_fc)

            # Export the result to Google Drive
            task = ee.batch.Export.image.toDrive(
                image=final_ndvi,
                folder=f'{self.folder_prefix}{year}',
                description=f"MedianNDVI_Landsat7_{year}",
                scale=30,  # 30m resolution for Landsat 7
                region=self.roi.coordinates().getInfo(),
                fileFormat='GeoTIFF',
                maxPixels=1e13
            )
            task.start()
            
    def landsat7_export_individual_ndvi(self, years):
        for year in years:
            print(f"Processing year: {year}")

            # Filter the Landsat 7 collection for the year
            landsat = (
                ee.ImageCollection("LANDSAT/LE07/C02/T1_RT")
                .filterBounds(self.roi)
                .filterDate(f'{year}-01-01', f'{year}-12-31')  # Strictly within the year
                .map(self.mask_clouds_and_gaps)  # Mask clouds and SLC-off gaps
                .map(self.calculate_ndvi)  # Add NDVI band
            )

            # Loop through each image in the collection
            landsat_list = landsat.toList(landsat.size())
            for i in range(landsat.size().getInfo()):
                image = ee.Image(landsat_list.get(i))
                image_id = image.get('LANDSAT_PRODUCT_ID').getInfo() 

                # Clip the image to the Worcestershire boundary
                worcs_fc = ee.FeatureCollection('users/hularuns/worcs_boundary_4326')
                final_image = image.select('NDVI').clip(worcs_fc)

                # Calculate the count of valid NDVI pixels within the ROI
                valid_pixel_count = final_image.reduceRegion(
                    reducer=ee.Reducer.count(),
                    geometry=self.roi,
                    scale=30,
                    maxPixels=1e13
                ).get('NDVI').getInfo()

                MIN_VALID_PIXELS = 5000
                if valid_pixel_count is None or valid_pixel_count <= 500:
                    print(f"Skipping {image_id} (no or low valid pixels in ROI).")
                    continue

                print(f"Exporting {image_id} with {valid_pixel_count} valid pixels.")

                task = ee.batch.Export.image.toDrive(
                    image=final_image,
                    folder=f'{self.folder_prefix}{year}',
                    description=f"NDVI_Landsat7_{image_id}",
                    scale=30,  # 30m resolution for Landsat 7
                    region=self.roi.coordinates().getInfo(),
                    fileFormat='GeoTIFF',
                    maxPixels=1e13
                )
                task.start()


    def run_gee_task(self, years):
        self.create_subfolder(years)
        self.landsat7_export_individual_ndvi(years)
        
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
