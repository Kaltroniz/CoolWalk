# CoolWalk Dataset & Analytics Dictionary

CoolWalk processes open satellite earth observation data and street geometries into accessible spatial formats and serverless analytical tables.

---

## 1. Primary Files & Download Links

| File | Location | Format | Description |
|---|---|---|---|
| **Heat Grid Layer** | `frontend/data/heat_grid.geojson` | GeoJSON (Polygon) | 2,092 spatial cells (150 m resolution) with normalized heat scores. [Download GeoJSON](data/heat_grid.geojson) |
| **City Findings** | `frontend/data/findings.json` | JSON | Aggregated statistics, high-heat network share, and top hottest/coolest streets with centroids. |
| **Cool Places & Refuges** | `frontend/data/places.geojson` | GeoJSON (Point) | Civic amenities (metro stations, parks, drinking water, clinics/hospitals) with thermal attributes. |
| **Shade Priority Corridors** | `frontend/data/shade_priority.csv` | CSV / JSON | Ranked hot corridors near vulnerable civic facilities for municipal tree canopy planning. |
| **Scored Street Segments** | `work/segments.parquet` / S3 Lakehouse | Apache Parquet / Iceberg | 35,748 directed street segments (representing 1,188.5 km of network) with physical Landsat surface temperatures, Sentinel-2 NDVI, and heat scores. |
| **Routing Graph** | `work/graph.json.gz` / `s3://<DataBucket>/router/graph.json.gz` | Gzip JSON | Compact indexed graph representation consumed by AWS Lambda. |

---

## 2. GeoJSON Schema: `heat_grid.geojson`

Each polygon represents a 150 m cell (`0.0015°` latitude/longitude grid) spanning central Delhi:

- `h`: Raw heat score (`0.0` to `1.0`), computed as `0.6 * normalized_LST + 0.4 * (1 - normalized_NDVI)`.
- `hs`: Clamped and rescaled heat score (`0.0` to `1.0`) relative to the 5th and 95th percentiles of the study area for map visualization.
- `geometry`: Polygon bounding coordinates `[[ [x0, y0], [x0+w, y0], [x0+w, y0+h], [x0, y0+h], [x0, y0] ]]`.

---

## 3. Apache Iceberg Tables

Stored in Apache Iceberg format on Amazon S3 and cataloged in AWS Glue / Amazon Athena:

### 3.1 Street Segments Table: `coolwalk.segments`

```sql
CREATE TABLE coolwalk.segments (
  edge_id bigint,
  u bigint,
  v bigint,
  length_m double,
  mid_lon double,
  mid_lat double,
  lst_c double,
  ndvi double,
  heat_index double,
  highway string,
  name string)
LOCATION 's3://<DataBucket>/iceberg/segments'
TBLPROPERTIES (
  'table_type'='iceberg',
  'compression_level'='3',
  'format'='PARQUET',
  'write_compression'='ZSTD'
);
```

#### Field Definitions:
- `edge_id`: Unique 64-bit integer segment identifier.
- `u`, `v`: OpenStreetMap intersection node identifiers (35,748 directed edges, representing 17,644 distinct intersection pairs).
- `length_m`: Metric Euclidean length along segment centerline geometry.
- `mid_lon`, `mid_lat`: Midpoint coordinates of segment centerline.
- `lst_c`: Mean Land Surface Temperature in degrees Celsius from USGS Landsat 8 TIRS Band 10.
- `ndvi`: Mean Normalized Difference Vegetation Index from Copernicus Sentinel-2 B4/B8.
- `heat_index`: Composite heat score (`0.0` to `1.0`). Scores $\ge 0.66$ indicate high-heat zones.
- `highway`: OSM road hierarchy classification (`primary`, `secondary`, `tertiary`, `residential`, `pedestrian`, `living_street`, etc.).
- `name`: Street name from OpenStreetMap (`NULL` or empty for unnamed alleys).

### 3.2 Places & Civic Facilities Table: `coolwalk.places`

```sql
CREATE TABLE coolwalk.places (
  place_id bigint,
  kind string,
  name string,
  lon double,
  lat double,
  lst_c double,
  ndvi double,
  heat_index double)
LOCATION 's3://<DataBucket>/iceberg/places'
TBLPROPERTIES (
  'table_type'='iceberg',
  'compression_level'='3',
  'format'='PARQUET',
  'write_compression'='ZSTD'
);
```

#### Field Definitions:
- `place_id`: Unique identifier for the civic amenity / place.
- `kind`: Amenity category with true values: `park` (373), `bus_stop` (353), `school` (85), `hospital` (73), `water` (58), `metro` (32).
- `name`: Name of the place or station.
- `lon`, `lat`: Point coordinates (WGS 84).
- `lst_c`: Mean Land Surface Temperature in degrees Celsius at this location.
- `ndvi`: Mean NDVI vegetation index at this location.
- `heat_index`: Heat index score (`0.0` to `1.0`).

---

## 4. Amazon Athena Queries Used for Findings

### 4.1 Overall High-Heat Network Share
```sql
SELECT
  round(sum(CASE WHEN heat_index >= 0.66 THEN length_m ELSE 0 END) / sum(length_m), 4) AS hot_share,
  round(sum(length_m) / 2000.0, 1) AS network_km,
  round(approx_percentile(lst_c, 0.05), 1) AS lst_p05_c,
  round(approx_percentile(lst_c, 0.95), 1) AS lst_p95_c
FROM coolwalk.segments;
```

### 4.2 Top Hottest Named Corridors
```sql
SELECT
  name,
  round(avg(heat_index), 3) AS heat,
  round(sum(length_m) / 2) AS length_m,
  round(avg(lst_c), 1) AS lst_c,
  round(max_by(mid_lon, length_m), 5) AS lon,
  round(max_by(mid_lat, length_m), 5) AS lat
FROM coolwalk.segments
WHERE name IS NOT NULL AND name <> '' 
  AND highway IN ('primary','secondary','tertiary','residential','unclassified','pedestrian','living_street')
GROUP BY name 
HAVING sum(length_m) > 1000
ORDER BY heat DESC 
LIMIT 8;
```

### 4.3 Top Coolest Named Corridors
```sql
SELECT
  name,
  round(avg(heat_index), 3) AS heat,
  round(sum(length_m) / 2) AS length_m,
  round(avg(lst_c), 1) AS lst_c,
  round(max_by(mid_lon, length_m), 5) AS lon,
  round(max_by(mid_lat, length_m), 5) AS lat
FROM coolwalk.segments
WHERE name IS NOT NULL AND name <> '' 
  AND highway IN ('primary','secondary','tertiary','residential','unclassified','pedestrian','living_street')
GROUP BY name 
HAVING sum(length_m) > 1000
ORDER BY heat ASC 
LIMIT 8;
```

### 4.4 Shade Priority Corridors
```sql
WITH hot AS (
  SELECT name, length_m, lst_c, heat_index, mid_lon, mid_lat
  FROM coolwalk.segments
  WHERE heat_index >= 0.66 AND name IS NOT NULL AND name <> ''),
st AS (
  SELECT name, round(avg(lst_c), 1) AS avg_surface_c, round(avg(heat_index), 2) AS avg_heat_index,
         round(sum(length_m) / 2) AS total_hot_m,
         round(max_by(mid_lon, length_m), 5) AS lon, round(max_by(mid_lat, length_m), 5) AS lat
  FROM hot GROUP BY name),
near AS (
  SELECT DISTINCT h.name, p.place_id, p.kind
  FROM hot h JOIN coolwalk.places p
    ON p.kind IN ('bus_stop', 'school', 'hospital')
   AND abs(h.mid_lat - p.lat) <= 0.0013 AND abs(h.mid_lon - p.lon) <= 0.0015
   AND sqrt(power((h.mid_lon - p.lon) * 111320.0 * 0.878, 2) + power((h.mid_lat - p.lat) * 110540.0, 2)) <= 150.0),
pc AS (
  SELECT name,
         count(CASE WHEN kind = 'bus_stop' THEN 1 END) AS bus_stops,
         count(CASE WHEN kind = 'school' THEN 1 END) AS schools,
         count(CASE WHEN kind = 'hospital' THEN 1 END) AS hospitals
  FROM near GROUP BY name)
SELECT st.name AS corridor, st.avg_surface_c, st.avg_heat_index, st.total_hot_m,
       pc.bus_stops, pc.schools, pc.hospitals, st.lon, st.lat
FROM st JOIN pc ON st.name = pc.name
ORDER BY (pc.schools * 3 + pc.hospitals * 3 + pc.bus_stops * 2) DESC, st.total_hot_m DESC
LIMIT 20;
```
