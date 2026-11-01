# CoolWalk

A walking map for central Delhi that trades a few minutes for much less time in the heat. Pick two points and CoolWalk shows the standard walk next to a cooler one, with a heat strip along each route and the average surface temperature avoided.

Built for the AWS Builder Center "Weekend Challenge: Map It".

**Live demo:** [https://main.d3miw0zrayytbj.amplifyapp.com](https://main.d3miw0zrayytbj.amplifyapp.com)  
**Video:** [YouTube Demo Link - Human to insert]

![CoolWalk Routed Walk](docs/screenshots/02_routed_walk.png)

## How it works

```mermaid
flowchart LR
  L8[Landsat 8/9 surface temperature<br/>requester-pays S3 bucket] --> P[Python pipeline<br/>scores 35k segments]
  S2[Sentinel-2 NDVI<br/>S3 open data] --> P
  OSM[OpenStreetMap walk network] --> P
  P --> ICE[(Apache Iceberg table<br/>on Amazon S3 via Athena)]
  ICE -->|Athena queries| ASSETS[Heat grid & findings]
  P --> GRAPH[Routing graph on S3]
  GRAPH --> LAM[AWS Lambda<br/>heat-weighted A*]
  ASSETS --> HOST[AWS Amplify Hosting<br/>HTTPS frontend]
  LAM <--> API[Amazon API Gateway HTTP API<br/>throttled & CORS-enabled]
  HOST <--> API
  HOST --> ALS[Amazon Location Service<br/>maps, place search, routes]
```

1. **Data.** Landsat Collection 2 Level-2 surface temperature (`LC08_L2SP_147040_20260609_02_T1` from the USGS requester-pays S3 bucket on AWS Open Data), Sentinel-2 L2A red and near-infrared bands (for vegetation), and the OpenStreetMap walking network. One clear pre-monsoon day (June 2026), shown in the app footer.
2. **Heat index.** For each street segment: `0.6 x surface temperature + 0.4 x lack of vegetation`, both normalized 0 to 1 across the area. It shows where streets hold heat.
3. **Iceberg and Athena.** Segment scores are stored as an Apache Iceberg table on S3 (`coolwalk.segments`). Athena produces the heat grid layer and statistical findings.
4. **Routing.** An AWS Lambda function runs A* where a segment costs `length x (1 + alpha x heat)`. The service computes routes in ~50 ms of routing compute, returning both heat exposure and physical surface temperature (`mean_lst_c`). A detour cap keeps the cooler walk reasonable. The "standard" walk is the Amazon Location Service pedestrian route, scored against the same thermal data, with our network shortest path as a fallback.
5. **Map & Place Search.** MapLibre on an Amazon Location Service Light basemap. Place search uses Amazon Location Places v2 with autocomplete.
6. **Hosting & Security.** Deployed with full HTTPS on AWS Amplify Hosting, backed by an Amazon API Gateway HTTP API with configured rate and burst throttling (20 req/s, 50 burst).

## Screenshots

| Desktop View | Mobile Route | Mobile Map |
|---|---|---|
| ![Desktop View](docs/screenshots/01_first_view.png) | ![Mobile Route](docs/screenshots/03_phone_layout.png) | ![Mobile Map](docs/screenshots/03_phone_collapsed.png) |

## Run it

Prerequisites: Python 3.11+, AWS CLI and SAM CLI configured, an AWS account with an active budget alert, Node not required.

```bash
# 1. Setup virtual environment
python -m venv .venv
# Linux / macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r pipeline/requirements.txt

# 2. Deploy AWS infrastructure
# Windows:
powershell -ExecutionPolicy Bypass -File scripts/deploy.ps1
# Linux / macOS:
export AWS_REGION=us-east-1
export MAP_API_KEY=...
./scripts/deploy.sh

# 3. Run data pipeline
export COOLWALK_BUCKET=<DataBucket from deploy output>
python pipeline/01_pick_scenes.py          # choose Landsat 8/9 thermal & Sentinel-2 vegetation scenes
python pipeline/02_score_segments.py       # score every street segment and build graph
python pipeline/03_build_iceberg.py        # Iceberg segments table via Athena
python pipeline/04_export_assets.py        # heat grid, findings, shade priority, and router graph
python pipeline/05_validation.py           # multi-date Landsat validation check
python pipeline/06_places.py               # extract civic infrastructure points
python pipeline/07_build_places_iceberg.py # Iceberg places table via Athena
python pipeline/08_shade_priority.py       # civic planner shade priority analysis

# 4. Deploy frontend to AWS Amplify (HTTPS)
# Packages frontend/ and deploys to AWS Amplify Hosting
powershell -ExecutionPolicy Bypass -File scripts/deploy.ps1
```

## Reuse it for your city

To adapt CoolWalk for another city:
1. Change `BBOX` and `DATE_RANGE` in `pipeline/config.py`.
2. Update the `bbox` and `PRESETS` in `frontend/index.html`.
3. Pick a clear, hot summer season with minimal cloud cover.
4. Run the pipeline scripts and re-deploy.

## Known limits

- **Heat index evaluation:** CoolWalk optimizes a heat index and compares routes against that index. To provide an objective physical baseline, CoolWalk also calculates and displays mean surface temperature (`mean_lst_c`) along each route.
- **Satellite thermal proxy:** Heat comes from a dated satellite scene (June 2026). Landsat's thermal band is 100 m native resolution (resampled to 30 m), so we blend it with 10 m Sentinel-2 vegetation to distinguish shaded streets from unshaded ones.
- **Surface temperature:** Surface temperature is a proxy for how hot a street surface feels underfoot and radiative heat. It ignores momentary wind, humidity, microscale building shade geometry, and time of day.
- **Walking pace:** Walking time assumes a constant 1.35 m/s speed everywhere.
- **Coverage:** Central Delhi (Old Delhi to Lodhi Garden).

## Data credits

Landsat data courtesy of the U.S. Geological Survey. Contains modified Copernicus Sentinel data. Street data from OpenStreetMap contributors (ODbL). Base map, geocoding and pedestrian routing via Amazon Location Service.

## License

MIT.
