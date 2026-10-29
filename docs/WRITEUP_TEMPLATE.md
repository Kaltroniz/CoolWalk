# CoolWalk: the cooler way to walk across Delhi

Copy this into your Builder Center article. Replace every `{{...}}` with real values from `docs/FINDINGS.md`. Delete this line.

**Live map:** {{CloudFront URL}} | **Video:** {{video URL}} | **Code:** {{repo URL}} (MIT)

## The problem

Walking directions optimise for distance. In a Delhi summer, the shortest route can run down a bare, sun-baked road when a street one block over is leafy and several degrees cooler at the surface. CoolWalk shows that difference and gives people the choice.

## The dataset

- **Landsat 8/9 Collection 2 Level-2 surface temperature**, scene {{scene id}} from {{date}}, from the USGS Landsat bucket in the AWS Registry of Open Data. Cloud cover {{cloud}}%.
- **Sentinel-2 L2A red and near-infrared bands**, {{date}}, used to compute vegetation (NDVI).
- **OpenStreetMap walking network** for central Delhi: {{N}} street segments covering {{km}} km.

All data is open and contains no personal information.

## How it gets onto the map

1. A Python pipeline samples the satellite rasters every 15 m along each street segment and builds a heat index from surface temperature (60%) and lack of vegetation (40%).
2. The scored segments are stored as an **Apache Iceberg table on Amazon S3** and queried with **Amazon Athena** to produce the heat layer (150 m cells) and the findings below.
3. A **Lambda** function routes over the walking graph with a cost of length times (1 plus alpha times heat), with a cap on detour length.
4. The web app uses **Amazon Location Service** for the base map, place search and the standard pedestrian route, which we score against the same heat data. The site is served by **CloudFront** from **S3**.

## What you can explore

- Click two points, search a place, or try the example walks.
- Drag the slider between fastest and coolest.
- Switch the heat layer on and off and read the heat strip under each route.

## What it shows

- {{share}}% of the {{km}} km of streets in the area are in high-heat zones.
- On {{walk 1}}, {{N}} minutes vs {{M}} minutes cuts time in high-heat zones from {{X}}% to {{Y}}%.
- Hottest streets: {{names}}. Coolest: {{names}}.

## Reuse the pattern

Change the bounding box and date range, run four scripts, and deploy with one command. The repo documents each step.

## Limits, stated plainly

Heat comes from a single dated satellite scene. It shows where streets hold heat, not the air temperature people feel, and it ignores wind, humidity and building shade. Walking time assumes 1.35 m/s.

## Data credits

Landsat data courtesy of the U.S. Geological Survey. Contains modified Copernicus Sentinel data. Street data (c) OpenStreetMap contributors. Base map and places via Amazon Location Service.
