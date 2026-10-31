import os
from pathlib import Path

ROOT = Path(__file__).parent.parent

files_to_include = [
    ('Infrastructure as Code & CI/CD', [
        'infra/template.yaml',
        'scripts/deploy.ps1',
        'scripts/deploy.sh',
        'scripts/deploy_amplify.py',
        '.github/workflows/test.yml',
        'LICENSE'
    ]),
    ('Satellite Data Ingestion & Geometry Scoring Pipeline', [
        'pipeline/config.py',
        'pipeline/requirements.txt',
        'pipeline/01_pick_scenes.py',
        'pipeline/02_score_segments.py',
        'pipeline/05_validation.py',
        'pipeline/06_places.py',
        'pipeline/07_build_places_iceberg.py',
        'scripts/augment_graph.py'
    ]),
    ('Apache Iceberg & Amazon Athena SQL Engine', [
        'pipeline/sql/01_database.sql',
        'pipeline/sql/02_staging_table.sql',
        'pipeline/sql/03_iceberg_table.sql',
        'pipeline/sql/q_heat_grid.sql',
        'pipeline/sql/q_hot_share.sql',
        'pipeline/sql/q_hottest_streets.sql',
        'pipeline/sql/q_coolest_streets.sql',
        'pipeline/03_build_iceberg.py',
        'pipeline/04_export_assets.py'
    ]),
    ('Serverless Heat-Aware Routing Microservice', [
        'backend/router/app.py',
        'backend/router/refuge.py',
        'backend/tests/test_router.py',
        'backend/tests/test_refuge.py'
    ]),
    ('Client-Side Web Application & UI', [
        'frontend/index.html'
    ]),
    ('Benchmarking, Verification & QA Harnesses', [
        'scripts/benchmark.py',
        'scripts/verify_ui_qa.py',
        'scripts/capture_screenshots.py',
        'scripts/test_presets.py',
        'scripts/eval_pairs.py'
    ]),
    ('Submission Materials, Documentation & Empirical Findings', [
        'docs/FINDINGS.md',
        'docs/BENCHMARK.md',
        'docs/DATA.md',
        'docs/WRITEUP.md',
        'docs/VIDEO_SCRIPT.md',
        'README.md'
    ])
]

header = """# CoolWalk: Complete Architecture, Mathematical Logic, and Full Source Code

This document provides a complete, unified reference for the entire **CoolWalk** application built for the AWS Builder Center "Weekend Challenge: Map It". It contains:
1. **The System Architecture & End-to-End Logic** explaining how every component connects to the next (from earth-observation satellite data down to pixel rendering in the browser).
2. **Mathematical Formulations** for thermal radiometric scaling, vegetation indexing, heat cost weights, detour-capped A* search, and Dijkstra cool-refuge optimization.
3. **Every Single Line of Code** across all infrastructure definitions, data pipelines, SQL queries, backend router microservices, test harnesses, evaluation scripts, documentation, and frontend user interface.

---

# Architecture & System Flow

CoolWalk bridges open earth-observation satellite data with real-time pedestrian navigation on AWS.

```mermaid
flowchart TD
    subgraph Data_Acquisition ["Phase 1: Ingestion and Spatial Scoring"]
        STAC[Earth Search STAC API] -->|Query cloud < 15%| P1[01_pick_scenes.py]
        P1 -->|Select clear scene| S_JSON[work/scenes.json]
        
        USGS[(s3://usgs-landsat/<br/>TIRS Band 10 LST + QA)] -->|Requester-Pays S3| P2[02_score_segments.py]
        S2_COG[(s3://sentinel-cogs/<br/>B04 Red, B08 NIR, SCL)] -->|HTTPS COG Window| P2
        OSM[(OpenStreetMap Overpass)] -->|ox.graph_from_bbox| P2
        S_JSON --> P2
        
        P2 -->|Export scored edges| PARQUET[work/segments.parquet<br/>35,748 rows]
        P2 -->|Serialize compact graph| GRAPH_GZ[work/graph.json.gz<br/>Nodes, Edges, Geometries]

        VAL[05_validation.py] -->|Sample 3 held-out scenes| GRAPH_GZ
        PLC[06_places.py] -->|OSM civic places + Satellite heat| PL_PARQUET[work/places.parquet<br/>974 places]
        PLC -->|Embed 463 refuges| GRAPH_GZ
        PLC -->|Export GeoJSON| PL_GEOJSON[frontend/data/places.geojson]
    end

    subgraph Analytics_Engine ["Phase 2: Lakehouse Analytics (Iceberg + Athena)"]
        PARQUET -->|S3 Upload| S3_STAGE[s3://DataBucket/staging/segments/]
        S3_STAGE -->|External Table| GLUE[AWS Glue Catalog / Athena]
        P3[03_build_iceberg.py] -->|CTAS query| ICEBERG[(coolwalk.segments<br/>Apache Iceberg on S3)]

        PL_PARQUET -->|S3 Upload| S3_PL_STAGE[s3://DataBucket/staging/places/]
        PL_ICE[07_build_places_iceberg.py] -->|CTAS query| ICEBERG_PL[(coolwalk.places<br/>Apache Iceberg on S3)]
        
        ICEBERG -->|q_heat_grid.sql| P4[04_export_assets.py]
        ICEBERG -->|q_hot_share.sql| P4
        ICEBERG -->|q_hottest_streets.sql| P4
        ICEBERG -->|q_coolest_streets.sql| P4
        
        P4 -->|Spatial binning| HEAT_GEOJSON[frontend/data/heat_grid.geojson<br/>2,092 cells]
        P4 -->|Statistics| FINDINGS_JSON[frontend/data/findings.json]
        GRAPH_GZ -->|Upload| S3_GRAPH[s3://DataBucket/router/graph.json.gz]
    end

    subgraph Backend_Routing ["Phase 3: Serverless Routing Microservice"]
        S3_GRAPH -->|Cold-start load| LAMBDA[AWS Lambda: Python 3.12<br/>2048 MB Memory]
        APIGW[Amazon API Gateway HTTP API] <-->|Event v2 payload| LAMBDA
        
        LAMBDA -->|GET /health| HEALTH_EP[Coverage metadata and provenance]
        LAMBDA -->|POST /route| ROUTE_EP[A* heat-weighted path and metrics]
        LAMBDA -->|POST /score| SCORE_EP[Flexible/Simple polyline heat scoring]
        LAMBDA -->|POST /refuge| REFUGE_EP[Dijkstra nearest cool refuge finder]
    end

    subgraph Frontend_App ["Phase 4: Client Web Application"]
        AMPLIFY[AWS Amplify Hosting (HTTPS)] -->|Serve HTML/JS| BROWSER[User Web Browser]
        BROWSER <-->|Fetch routes and refuges| APIGW
        BROWSER <-->|Vector tiles, place search, routes| ALS[Amazon Location Service v2]
        BROWSER -->|Overlay heat grid and places| HEAT_GEOJSON
        BROWSER -->|Display independent checks| ROUTE_EP
        BROWSER -->|Interactive 40-sec tour| BROWSER
    end
```

---
"""

out = [header]

for section_title, file_list in files_to_include:
    out.append(f'# {section_title}\n')
    for fpath in file_list:
        p = ROOT / fpath
        if not p.exists():
            continue
        ext = p.suffix.lstrip('.')
        if ext == 'ps1':
            lang = 'powershell'
        elif ext == 'sh':
            lang = 'bash'
        elif ext in ('yaml', 'yml'):
            lang = 'yaml'
        elif ext == 'py':
            lang = 'python'
        elif ext == 'sql':
            lang = 'sql'
        elif ext == 'html':
            lang = 'html'
        elif ext == 'json':
            lang = 'json'
        elif ext == 'md':
            lang = 'markdown'
        else:
            lang = 'text'

        content = p.read_text(encoding='utf-8')
        out.append(f'## `{fpath}`\n\n```{lang}\n{content.strip()}\n```\n')

full_doc = '\n'.join(out)
(ROOT / 'COOLWALK_FULL_CODE_AND_LOGIC.md').write_text(full_doc, encoding='utf-8')
print(f'COOLWALK_FULL_CODE_AND_LOGIC.md updated: {len(full_doc):,} characters across {len(full_doc.splitlines()):,} lines.')

