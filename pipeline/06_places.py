"""Step 6. Ingest, score, and analyze OpenStreetMap points of interest (places).

Fetches bus stops, drinking water, parks, metro stations, hospitals, and schools.
Scores them against Landsat LST and Sentinel-2 NDVI.
Embeds refuge places (park, water, metro) into work/graph.json.gz.
Exports frontend/data/places.geojson and updates findings.json with exposure metrics.
"""
import gzip
import json
import sys
from pathlib import Path

import boto3
import numpy as np
import osmnx as ox
import pandas as pd
import rasterio
from pyproj import Transformer
from rasterio.errors import WindowError
from rasterio.session import AWSSession
from rasterio.windows import Window, from_bounds

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
import config


class Raster:
    def __init__(self, href):
        self.data = None
        with rasterio.open(href) as ds:
            tf = Transformer.from_crs("EPSG:4326", ds.crs, always_xy=True)
            w, s, e, n = config.BBOX
            xs, ys = tf.transform([w, e, w, e], [s, s, n, n])
            try:
                win = from_bounds(min(xs), min(ys), max(xs), max(ys), ds.transform)
                win = win.round_offsets().round_lengths().intersection(Window(0, 0, ds.width, ds.height))
            except WindowError:
                return
            self.data = ds.read(1, window=win)
            self.inv = ~ds.window_transform(win)
            self.crs = ds.crs
        self.tf = Transformer.from_crs("EPSG:4326", self.crs, always_xy=True)

    def sample(self, lons, lats):
        out = np.full(len(lons), np.nan)
        if self.data is None:
            return out
        x, y = self.tf.transform(lons, lats)
        cols, rows = self.inv * (np.asarray(x), np.asarray(y))
        rows, cols = np.floor(rows).astype(int), np.floor(cols).astype(int)
        ok = (rows >= 0) & (rows < self.data.shape[0]) & (cols >= 0) & (cols < self.data.shape[1])
        out[ok] = self.data[rows[ok], cols[ok]]
        return out


def surface_temp_c(ls, lon, lat):
    dn = Raster(ls["lwir11"]).sample(lon, lat)
    qa = Raster(ls["qa"]).sample(lon, lat)
    bad = np.isnan(qa) | ((np.nan_to_num(qa).astype(np.int64) & 0b11011) != 0)
    t = dn * 0.00341802 + 149.0 - 273.15
    t[(dn <= 0) | bad | (t < 15) | (t > 75)] = np.nan
    return t


def ndvi(sc, lon, lat):
    out = np.full(len(lon), np.nan)
    for it in sc["sentinel"]["items"]:
        red, nir, scl = Raster(it["red"]), Raster(it["nir"]), Raster(it["scl"])
        r, n, c = red.sample(lon, lat), nir.sample(lon, lat), scl.sample(lon, lat)
        r = np.where(r > 0, np.clip((r - 1000.0) / 10000.0, 0.01, None), np.nan)
        n = np.where(n > 0, np.clip((n - 1000.0) / 10000.0, 0, None), np.nan)
        v = (n - r) / (n + r + 1e-6)
        v[np.isin(np.nan_to_num(c), [0, 1, 3, 8, 9, 10, 11])] = np.nan
        out = np.where(np.isnan(out), v, out)
    return out


def main():
    w, s, e, n = config.BBOX
    print(f"Fetching OpenStreetMap places in bbox: {config.BBOX}...")
    tags = {
        "highway": "bus_stop",
        "amenity": ["drinking_water", "hospital", "clinic", "school"],
        "leisure": ["park", "garden"],
        "railway": "station",
        "public_transport": "station"
    }
    gdf = ox.features_from_bbox(bbox=(w, s, e, n), tags=tags)
    print(f"Retrieved {len(gdf):,} raw features from OSM.")

    records = []
    seen = set()
    for idx, row in gdf.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        pt = geom.centroid if geom.geom_type != "Point" else geom
        lon, lat = round(float(pt.x), 6), round(float(pt.y), 6)
        
        name = str(row.get("name") or "").strip()
        kind = None
        if row.get("highway") == "bus_stop":
            kind = "bus_stop"
        elif row.get("amenity") == "drinking_water":
            kind = "water"
        elif row.get("leisure") in ("park", "garden"):
            kind = "park"
        elif (row.get("railway") == "station" and row.get("station") == "subway") or \
             (row.get("public_transport") == "station" and row.get("subway") == "yes") or \
             ("metro" in name.lower() and row.get("railway") == "station"):
            kind = "metro"
        elif row.get("amenity") in ("hospital", "clinic"):
            kind = "hospital"
        elif row.get("amenity") == "school":
            kind = "school"

        if not kind:
            continue

        # Deduplicate
        key = (kind, round(lon, 4), round(lat, 4))
        if key in seen:
            continue
        seen.add(key)

        records.append({
            "place_id": len(records),
            "kind": kind,
            "name": name if name else f"Unnamed {kind.replace('_', ' ')}",
            "lon": lon,
            "lat": lat
        })

    df = pd.DataFrame(records)
    print("\nPlaces count per kind (after deduplication):")
    counts = df["kind"].value_counts().to_dict()
    for k, count in sorted(counts.items()):
        print(f"  {k:<12}: {count}")

    # Gate verification: drop kinds with fewer than 15 places
    valid_kinds = {k for k, count in counts.items() if count >= 15}
    dropped_kinds = set(counts.keys()) - valid_kinds
    if dropped_kinds:
        print(f"Dropping kinds with < 15 places: {dropped_kinds}")
        df = df[df["kind"].isin(valid_kinds)].reset_index(drop=True)
        df["place_id"] = df.index

    # Score places with satellite rasters
    with open(config.WORK / "scenes.json") as f:
        sc = json.load(f)

    with gzip.open(config.WORK / "graph.json.gz", "rt", encoding="utf-8") as f:
        g = json.load(f)

    meta = g.get("meta", {})
    p5 = meta.get("lst_p5_c", 40.33)
    p95 = meta.get("lst_p95_c", 46.28)

    print(f"\nSampling Landsat and Sentinel-2 rasters at {len(df):,} place coordinates...")
    session = AWSSession(boto3.Session(), requester_pays=True)
    with rasterio.Env(session, AWS_REGION="us-west-2", GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"):
        lst = surface_temp_c(sc["landsat"], df["lon"].values, df["lat"].values)
        veg = ndvi(sc, df["lon"].values, df["lat"].values)

    df["lst_c"] = pd.Series(lst).fillna(float(np.nanmedian(lst))).round(1)
    df["ndvi"] = pd.Series(veg).fillna(float(np.nanmedian(veg))).round(3)

    lst_n = np.clip((df["lst_c"] - p5) / (p95 - p5), 0, 1)
    veg_n = 1.0 - np.clip(df["ndvi"] / 0.6, 0, 1)
    df["heat_index"] = (config.W_LST * lst_n + config.W_VEG * veg_n).round(4)

    # Save work/places.parquet
    out_parquet = config.WORK / "places.parquet"
    df.to_parquet(out_parquet, index=False)
    print(f"Saved {len(df):,} scored places to {out_parquet}")

    # Embed refuge places (park, water, metro) in graph.json.gz
    refuge_kinds = {"park", "water", "metro"}
    refuge_df = df[df["kind"].isin(refuge_kinds)]
    g["places"] = [
        {"kind": r.kind, "name": r.name, "lon": round(float(r.lon), 5), "lat": round(float(r.lat), 5)}
        for r in refuge_df.itertuples()
    ]
    with gzip.open(config.WORK / "graph.json.gz", "wt", encoding="utf-8") as f:
        json.dump(g, f, separators=(",", ":"))
    print(f"Embedded {len(g['places'])} refuge places (park, water, metro) into work/graph.json.gz")

    # Export frontend/data/places.geojson
    features = []
    for r in df.itertuples():
        features.append({
            "type": "Feature",
            "properties": {
                "id": int(r.place_id),
                "kind": r.kind,
                "name": r.name,
                "heat": float(r.heat_index),
                "lst_c": float(r.lst_c),
                "ndvi": float(r.ndvi)
            },
            "geometry": {
                "type": "Point",
                "coordinates": [round(float(r.lon), 5), round(float(r.lat), 5)]
            }
        })
    (config.FRONT_DATA / "places.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":"))
    )
    print(f"Exported frontend/data/places.geojson ({len(features):,} features)")

    # Compute findings exposure metrics
    bus = df[df.kind == "bus_stop"]
    sch = df[df.kind == "school"]
    hosp = df[df.kind == "hospital"]
    parks = df[df.kind == "park"]

    def exp_stat(sub):
        if len(sub) == 0:
            return {"total": 0, "hot": 0, "hot_pct": 0.0}
        hot = (sub.heat_index >= 0.66).sum()
        return {"total": len(sub), "hot": int(hot), "hot_pct": round(float(hot / len(sub)), 3)}

    hottest_bus = bus.sort_values("heat_index", ascending=False).head(5)
    coolest_parks = parks.sort_values("heat_index", ascending=True).head(5)

    with open(config.FRONT_DATA / "findings.json") as f:
        findings = json.load(f)

    findings["place_exposure"] = {
        "bus_stops": exp_stat(bus),
        "schools": exp_stat(sch),
        "hospitals": exp_stat(hosp),
        "hottest_bus_stops": [
            {"name": r.name, "heat": float(r.heat_index), "lst_c": float(r.lst_c), "lon": float(r.lon), "lat": float(r.lat)}
            for r in hottest_bus.itertuples()
        ],
        "coolest_parks": [
            {"name": r.name, "heat": float(r.heat_index), "lst_c": float(r.lst_c), "ndvi": float(r.ndvi), "lon": float(r.lon), "lat": float(r.lat)}
            for r in coolest_parks.itertuples()
        ]
    }

    with open(config.FRONT_DATA / "findings.json", "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2)

    print("\nUpdated frontend/data/findings.json with place exposure metrics:")
    print(f"  Bus stops in high-heat zones: {findings['place_exposure']['bus_stops']['hot']}/{findings['place_exposure']['bus_stops']['total']} ({findings['place_exposure']['bus_stops']['hot_pct']:.1%})")
    print(f"  Schools in high-heat zones:   {findings['place_exposure']['schools']['hot']}/{findings['place_exposure']['schools']['total']} ({findings['place_exposure']['schools']['hot_pct']:.1%})")
    print(f"  Hospitals in high-heat zones: {findings['place_exposure']['hospitals']['hot']}/{findings['place_exposure']['hospitals']['total']} ({findings['place_exposure']['hospitals']['hot_pct']:.1%})")


if __name__ == "__main__":
    main()
