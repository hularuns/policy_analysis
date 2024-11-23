Using remote sensing, has the condition of remote-sensed habitats improved within policy defined areas in Worcestershire, UK?
- map average NDVI from 2010 to now.
	- stats on average diff from earliest ndvi to now.
	- Time Series NDVI change
	- map of gain loss in NDVI

- Map LCM
	- Time Series of LCM cover of habitats
	- categorise habitats of Very high, high, moderate, low value to biodiversity.
	- stats on average diff from earliest lcm to now within the BDAs.



# Process
install the environment by running 
```bash
poetry install
```
1) Run the below , ensure that the ndvi files end up in the `ndvi/landsat7` folder
``` python
poetry run python policy_analysis/gee_ndvi_landsat_7.py
```
2) Run analysis on the survey areas ...