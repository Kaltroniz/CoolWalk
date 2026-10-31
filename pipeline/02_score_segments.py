"""Step 2. Score every walkable street segment for heat.

Inputs : work/scenes.json (step 1), OpenStreetMap walking network (downloaded here)
Outputs: work/segments.parquet   one row per street segment (loaded into Athena/Iceberg in step 3)
         work/graph.json.gz      compact routing graph for the Lambda
Heat index (0..1) = 0.6 * normalised surface temperature + 0.4 * lack of vegetation.
"""
import gzip
import json
import sys

import boto3
import numpy as np
import osmnx as ox
import pandas as pd
import rasterio
from pyproj import Transformer
from rasterio.errors import WindowError
from rasterio.session import AWSSession
from rasterio.windows import Window, from_bounds

import config


class Raster:
    """Reads the study-area window of a COG once, then answers point lookups in lon/lat."""

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
                return  # this tile does not overlap the study area
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


def edge_points(edges):
    lon, lat, eid = [], [], []
    for i, (geom, length) in enumerate(zip(edges.geometry, edges["length"])):
        for t in np.linspace(0.0, 1.0, max(2, int(length // config.STEP_M) + 1)):
            p = geom.interpolate(t, normalized=True)
            lon.append(p.x)
            lat.append(p.y)
            eid.append(i)
    return np.array(lon), np.array(lat), np.array(eid)


def surface_temp_c(sc, lon, lat):
    ls = sc["landsat"]
    dn = Raster(ls["lwir11"]).sample(lon, lat)
    qa = Raster(ls["qa"]).sample(lon, lat)
    bad = np.isnan(qa) | ((np.nan_to_num(qa).astype(np.int64) & 0b11011) != 0)  # fill, cloud, shadow
    t = dn * 0.00341802 + 149.0 - 273.15                                          # Landsat C2 L2 scale, Kelvin to C
    t[(dn <= 0) | bad | (t < 15) | (t > 75)] = np.nan
    return t


def ndvi(sc, lon, lat):
    out = np.full(len(lon), np.nan)
    for it in sc["sentinel"]["items"]:
        red, nir, scl = Raster(it["red"]), Raster(it["nir"]), Raster(it["scl"])
        r, n, c = red.sample(lon, lat), nir.sample(lon, lat), scl.sample(lon, lat)
        r = np.where(r > 0, np.clip((r - 1000.0) / 10000.0, 0.01, None), np.nan)   # L2A BOA offset, floored to prevent zero division
        n = np.where(n > 0, np.clip((n - 1000.0) / 10000.0, 0, None), np.nan)
        v = (n - r) / (n + r + 1e-6)
        v[np.isin(np.nan_to_num(c), [0, 1, 3, 8, 9, 10, 11])] = np.nan
        out = np.where(np.isnan(out), v, out)
    return out


def main():
    sc = json.loads((config.WORK / "scenes.json").read_text())
    print("Downloading OpenStreetMap walking network ...")
    G = ox.graph.graph_from_bbox(bbox=config.BBOX, network_type="walk", simplify=True)
    nodes, edges = ox.convert.graph_to_gdfs(G, fill_edge_geometry=True)
    edges = edges.reset_index()
    print(f"{len(edges):,} street segments, {len(nodes):,} intersections")
    if len(edges) > 120_000:
        print("WARNING: graph is large. Shrink BBOX in pipeline/config.py to keep Lambda cold starts fast.")

    lon, lat, eid = edge_points(edges)
    print(f"Sampling {len(lon):,} points ...")
    session = AWSSession(boto3.Session(), requester_pays=True)       # Landsat bucket is requester-pays
    with rasterio.Env(session, AWS_REGION="us-west-2", GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"):
        lst = surface_temp_c(sc, lon, lat)
        veg = ndvi(sc, lon, lat)

    per = pd.DataFrame({"e": eid, "lst": lst, "ndvi": veg}).groupby("e").mean().reindex(range(len(edges)))
    print(f"Missing after masking: LST {per.lst.isna().mean():.1%}, NDVI {per.ndvi.isna().mean():.1%}")
    per = per.fillna(per.median())
    p5, p95 = np.percentile(per.lst, [5, 95])
    lst_n = ((per.lst - p5) / (p95 - p5)).clip(0, 1)
    veg_n = 1.0 - (per.ndvi / 0.6).clip(0, 1)
    heat = (config.W_LST * lst_n + config.W_VEG * veg_n).round(4)

    mid = edges.geometry.interpolate(0.5, normalized=True)
    seg = pd.DataFrame({
        "edge_id": np.arange(len(edges), dtype="int64"),
        "u": edges["u"].astype("int64"), "v": edges["v"].astype("int64"),
        "length_m": edges["length"].round(1), "mid_lon": mid.x.round(6), "mid_lat": mid.y.round(6),
        "lst_c": per.lst.round(2).values, "ndvi": per.ndvi.round(3).values, "heat_index": heat.values,
        "highway": edges["highway"].map(lambda v: v[0] if isinstance(v, list) else str(v)),
        "name": edges["name"].map(lambda v: (v[0] if isinstance(v, list) else v) if isinstance(v, (str, list)) else ""),
    })
    seg.to_parquet(config.WORK / "segments.parquet", index=False)

    # compact routing graph: edge schema [u, v, length, heat, edge_id, lst_c, ndvi]
    ids = pd.unique(pd.concat([seg.u, seg.v]))
    index = {int(n): i for i, n in enumerate(ids)}
    node_xy = [[round(float(nodes.loc[n, "x"]), 6), round(float(nodes.loc[n, "y"]), 6)] for n in ids]
    g_edges, g_geoms = [], []
    for row, geom in zip(seg.itertuples(index=False), edges.geometry):
        coords = [[round(x, 5), round(y, 5)] for x, y in geom.coords]
        u_xy = node_xy[index[int(row.u)]]
        if (coords[0][0] - u_xy[0]) ** 2 + (coords[0][1] - u_xy[1]) ** 2 > \
           (coords[-1][0] - u_xy[0]) ** 2 + (coords[-1][1] - u_xy[1]) ** 2:
            coords.reverse()                                          # make geometry run u -> v
        g_edges.append([index[int(row.u)], index[int(row.v)], float(row.length_m), float(row.heat_index), int(row.edge_id), float(row.lst_c), float(row.ndvi)])
        g_geoms.append(coords)
    meta = {"bbox": list(config.BBOX), "landsat_date": sc["landsat"]["date"], "landsat_id": sc["landsat"]["id"],
            "sentinel_date": sc["sentinel"]["date"], "weights": {"lst": config.W_LST, "veg": config.W_VEG},
            "lst_p5_c": round(float(p5), 2), "lst_p95_c": round(float(p95), 2), "hot_threshold": config.HOT_T}
    with gzip.open(config.WORK / "graph.json.gz", "wt", encoding="utf-8") as f:
        json.dump({"nodes": node_xy, "edges": g_edges, "geoms": g_geoms, "meta": meta}, f, separators=(",", ":"))

    print(f"Saved work/segments.parquet and work/graph.json.gz")
    print(f"Surface temperature range in the area (5th to 95th percentile): {p5:.1f} to {p95:.1f} C")
    print(f"Share of street length at or above the hot threshold: "
          f"{(seg.length_m[seg.heat_index >= config.HOT_T].sum() / seg.length_m.sum()):.1%}")


if __name__ == "__main__":
    sys.exit(main())
