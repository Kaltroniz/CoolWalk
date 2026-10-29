# Antigravity prompt: ship CoolWalk

Paste everything below the line into Antigravity as the task. Keep this file in the repo root so the agent can re-read it.

---

You are the lead engineer finishing **CoolWalk** for the AWS Builder Center "Weekend Challenge: Map It". CoolWalk is a public web map of central Delhi that gives pedestrians the cooler of two walking routes and shows how much heat the cooler route avoids. A working scaffold already exists in this repository. Your job is to make it run end to end on real data, deploy it publicly, polish it, and prepare the submission materials. Read `README.md`, `docs/PLAN.md` and every file you will touch before changing anything.

## Contest rules that decide whether we qualify (pass/fail)
1. The app must show spatial data on a map and be **publicly reachable, running on AWS**, with no login.
2. Use at least one AWS location or data service. We use Amazon Location Service (maps, place search, pedestrian routing), Amazon S3, Apache Iceberg tables via Amazon Athena, Lambda, API Gateway, CloudFront.
3. Only open data we have the right to use. No personal or sensitive data. Credit the sources.
4. A written project on AWS Builder Center (dataset, how it got on the map, AWS services, live link) and a public video under 3 minutes with no copyrighted music. The human will publish these. You prepare drafts.
5. Public repo uses the MIT license already in `LICENSE`.
6. Submission window: opens Oct 30 2026 12:00 am PT, closes Nov 2 2026 1:00 pm PT. **Do not write new application code before the window opens.** Before it opens you may only run read-only checks (Step 0).

## Ground rules
- **Never invent facts.** Every number shown in the UI, the write-up or the video script must come from our data or from a command you ran. If an API response differs from what the code assumes, read the current AWS documentation, fix the code, and say what changed.
- The scaffold was syntax-checked and the router logic passes offline tests (`python backend/tests/test_router.py`), but it has **never been run against live AWS, Landsat, Sentinel-2 or OpenStreetMap services**. Assume integration bugs exist and fix them.
- Run commands yourself and read their output. After each step, state what you verified and what you could not.
- Ask the human only for things you cannot do: AWS credentials, approving spend, creating the Location Service API key if you lack permission, publishing the Builder Center article, recording the video.
- Keep the scope tight. One city area, one polished experience. Do not add features that are not listed here until every step passes.
- Never commit secrets. `frontend/config.js` and `.env` are git-ignored. The Location Service API key is browser-visible by design, so it must be restricted to our site's referer and to the needed actions only.
- Prefer small, explainable changes. Keep comments short and explain why.

## Step 0: read-only checks (allowed before the window opens)
Run these and report the results in a short table. Stop and tell the human if any fails.
1. `aws sts get-caller-identity` works. Note the account and default region. Confirm a **budget alert** exists or ask the human to create one.
2. Confirm the chosen `AWS_REGION` supports Amazon Location **Maps, Places and Routes (v2)** and also Athena. Default is `us-east-1`. Check the AWS documentation for current availability instead of guessing.
3. One test `CalculateRoutes` call for **TravelMode Pedestrian** between two points in central Delhi, for example [77.2303,28.6562] to [77.2167,28.6315]. Record whether it returns a sensible walking route and what the response JSON looks like (field names for geometry and summary). The coverage documentation lists car, truck and scooter for India but does not list pedestrian, so this test matters.
4. Test one `SearchText` request in Places v2 for "India Gate Delhi" and confirm the response has `ResultItems[].Position`.
5. Run `python pipeline/01_pick_scenes.py`. Confirm a Landsat 8/9 scene with low cloud covers the box, and that the Landsat `lwir11` (surface temperature) and `qa_pixel` assets exist. If the asset names differ, fix the script. This step only reads the public STAC catalog.
6. Count street segments: `python -c "import osmnx as ox; G=ox.graph.graph_from_bbox(bbox=(77.19,28.585,77.26,28.668), network_type='walk'); print(len(G.edges))"`. If above about 120,000, shrink `BBOX` in `pipeline/config.py` and in `scripts/deploy.sh` and `frontend/index.html` (the `bbox` defaults and the PRESETS must stay inside it).
Report: pedestrian routing works yes or no, region, segment count, selected Landsat scene and cloud cover.

**Fallback decisions** if a check fails:
- Pedestrian routing fails or looks wrong in India: keep the app as is. The frontend already falls back to our own shortest-path route as the "standard" walk, labelled "Shortest walk". Keep Location Service for the base map and place search.
- Place search fails: keep click-to-pick and the example walks.
- No clear Landsat scene in Apr 15 to Jun 20 2026: widen `COOLWALK_DATES`, or use a later clear date, and tell the human the date.

## Step 1: stack and keys (after the window opens)
1. `python -m venv .venv && . .venv/bin/activate && pip install -r pipeline/requirements.txt`. Also install the AWS SAM CLI if missing.
2. Create the Amazon Location **API key**. Check the current docs for the exact CLI or console steps and action names. Restrict it to Maps, Places and Routes actions and resources in our region. Allowed referers start with `http://localhost:*` so we can test, and are tightened to the CloudFront URL after deploy. Put the key in `MAP_API_KEY`.
3. `./scripts/deploy.sh` (first deploy creates buckets, CloudFront, Lambda and API; the site will show a missing graph until Step 3 finishes). Record the outputs and `export COOLWALK_BUCKET=<DataBucket>`.

## Step 2: data pipeline
1. `python pipeline/01_pick_scenes.py` (done in Step 0 if unchanged).
2. `python pipeline/02_score_segments.py`. Watch for: requester-pays access to the Landsat bucket, CRS and window handling in `Raster`, how many segments end up with missing temperature or vegetation after masking, and the printed temperature range. Landsat surface temperature over Delhi in May should look like roughly 35 to 55 C. If the range looks wrong, check the scale formula `DN * 0.00341802 + 149.0` (Kelvin) and the mask.
3. Sanity-check the result: sample 10 segments and confirm that leafy streets (for example around Lodhi Garden or Rajpath) score cooler than dense markets (for example Chandni Chowk). Write what you found in `docs/FINDINGS.md`. If the pattern is backwards or flat, fix the pipeline before continuing. Do not tune weights just to produce a nicer demo. If you change `W_LST` or `W_VEG`, say why.
4. `python pipeline/03_build_iceberg.py`. Confirm `coolwalk.segments` is an Iceberg table (for example `SHOW CREATE TABLE`) and that the row count equals the parquet row count.
5. `python pipeline/04_export_assets.py`. This runs the Athena queries, writes `frontend/data/heat_grid.geojson` and `frontend/data/findings.json`, and uploads `router/graph.json.gz`.

## Step 3: backend
1. `python backend/tests/test_router.py` must pass.
2. Hit the deployed API: `GET /health` then `POST /route` for the three preset walks. Check cold-start time and response time. If cold start exceeds about 8 seconds, shrink the area, slim the graph file, or enable provisioned concurrency for the demo, and tell the human about any cost.
3. Run `python scripts/find_demo_pairs.py` and pick the three most convincing walks. They must be real, sensible walking trips between places a viewer recognises. Update `PRESETS` in `frontend/index.html`. Record the exact numbers (minutes, hot-zone share) for each in `docs/FINDINGS.md`.

## Step 4: frontend and polish
Redeploy with `./scripts/deploy.sh`, open the CloudFront URL, and test on a desktop width and a 390 px phone width. Fix, in this order:
1. Anything that blocks the core loop: pick two points, see both routes and the verdict.
2. Map style loading, API key referer errors, CORS, and error messages. Errors must say what happened and how to fix it.
3. The heat layer legibility on the Light basemap. Tune the colour ramp or opacity only if the layer is hard to read.
4. Keyboard focus, the slider, the search suggestions, and marker dragging.
5. Empty, loading and failure states.
Keep the design: light basemap, shade-green CoolWalk route, dashed charcoal standard route, heat strip under each route. Do not add new panels. Take screenshots of the first view, a routed walk, and the phone layout into `docs/screenshots/`.

## Step 5: submission materials (drafts for the human to publish)
1. Fill in `docs/WRITEUP_TEMPLATE.md` as `docs/WRITEUP.md` using real numbers from `docs/FINDINGS.md`.
2. Adjust `docs/VIDEO_SCRIPT.md` to the final three walks and real numbers, with timings under 2 minutes 50 seconds.
3. Update `README.md` with the final live URL, a short "swap your city" section, and an architecture diagram that matches what is actually deployed.
4. Make sure the repo has no secrets and that `LICENSE` is present.

## Definition of done
- The CloudFront URL loads without login, shows the map and heat layer, and returns both routes for all three preset walks within a few seconds.
- The `coolwalk.segments` Iceberg table exists and the findings and heat grid come from Athena queries on it.
- `test_router.py` passes, `deploy.sh` redeploys cleanly, and every number in the write-up matches `docs/FINDINGS.md`.
- Honest limits are visible in the UI footer and in the write-up: heat is a satellite-based proxy from a single dated scene, not air temperature.
- A final report lists what you verified, what you could not verify, any costs incurred, and the exact things the human must still do (publish the article, record and upload the video, submit before the deadline).

## What not to do
- Do not claim real-time data, air temperature, or health outcomes.
- Do not claim the standard route came from Amazon Location Service when the frontend fell back to the graph shortest path. The label already handles this; keep it correct.
- Do not hide failures. If a service is unavailable, say so and use the documented fallback.
- Do not exceed the budget alert. Prefer free-tier or low-cost choices and tell the human before anything that costs more than a few dollars.
