"""Step 5. Independent validation on held-out Landsat scenes from other dates.

Samples surface temperature on clear Landsat scenes that were never used for routing,
and writes per-edge means into work/graph.json.gz under the 'val' key.
"""
import gzip
import json
import os
import sys
from pathlib import Path

import boto3
import numpy as np
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


def main():
    with open(config.WORK / "scenes.json") as f:
        sc = json.load(f)
    val_scenes = sc.get("validation_scenes", [])
    if not val_scenes:
        print("No validation scenes in work/scenes.json.")
        return

    print(f"Scoring {len(val_scenes)} held-out validation scenes:")
    for v in val_scenes:
        print(f"  {v['id']} ({v['date']}) cloud: {v['cloud']}%")

    with gzip.open(config.WORK / "graph.json.gz", "rt", encoding="utf-8") as f:
        g = json.load(f)

    # Collect sample points per edge
    edge_pts = []
    eids = []
    for i, geom in enumerate(g["geoms"]):
        if not geom:
            continue
        coords = np.array(geom)
        # sample at vertices and midpoints
        for k in range(len(coords)):
            edge_pts.append(coords[k])
            eids.append(i)
        if len(coords) > 1:
            mid = (coords[0] + coords[-1]) / 2.0
            edge_pts.append(mid)
            eids.append(i)

    edge_pts = np.array(edge_pts)
    lons, lats = edge_pts[:, 0], edge_pts[:, 1]
    eids = np.array(eids)
    print(f"Sample points across {len(g['edges']):,} edges: {len(lons):,}")

    session = AWSSession(boto3.Session(), requester_pays=True)
    all_scene_lsts = []

    with rasterio.Env(session, AWS_REGION="us-west-2", GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"):
        for v in val_scenes:
            print(f"Sampling {v['date']} ({v['id']})...")
            t = surface_temp_c(v, lons, lats)
            # Compute per-edge mean
            # Group by edge index
            edge_means = np.full(len(g["edges"]), np.nan)
            valid = ~np.isnan(t)
            if np.any(valid):
                sums = np.bincount(eids[valid], weights=t[valid], minlength=len(g["edges"]))
                counts = np.bincount(eids[valid], minlength=len(g["edges"]))
                has_data = counts > 0
                edge_means[has_data] = sums[has_data] / counts[has_data]
            
            med = np.nanmedian(edge_means)
            edge_means[np.isnan(edge_means)] = med
            print(f"  {v['date']} median LST: {med:.1f} °C, range: {np.nanmin(edge_means):.1f} to {np.nanmax(edge_means):.1f} °C")
            all_scene_lsts.append([round(float(x), 2) for x in edge_means])

    g["val"] = {
        "scenes": [{"date": v["date"], "id": v["id"]} for v in val_scenes],
        "lst": all_scene_lsts
    }

    with gzip.open(config.WORK / "graph.json.gz", "wt", encoding="utf-8") as f:
        json.dump(g, f, separators=(",", ":"))

    print(f"Successfully added held-out validation data to work/graph.json.gz")


if __name__ == "__main__":
    main()
