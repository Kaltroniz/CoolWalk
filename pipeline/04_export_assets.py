"""Step 4. Query the Iceberg table with Athena and write the assets the website and Lambda need.

  frontend/data/heat_grid.geojson   150 m heat cells for the map layer
  frontend/data/findings.json       hottest / coolest streets and the share of hot streets
  s3://BUCKET/router/graph.json.gz  routing graph for the Lambda
"""
import importlib
import json
import sys
from pathlib import Path

import numpy as np

import config

ath = importlib.import_module("03_build_iceberg")      # reuse its Athena helpers
SQL = Path(__file__).parent / "sql"
CELL = 0.0015


def query(name):
    return ath.rows(ath.run((SQL / name).read_text().strip().rstrip(";"), config.DB))


def main():
    if not config.BUCKET:
        sys.exit("Set COOLWALK_BUCKET first.")

    grid = query("q_heat_grid.sql")
    heat = np.array([float(r["heat"]) for r in grid])
    lo, hi = np.percentile(heat, [5, 95])
    feats = []
    for r in grid:
        cx, cy, h = int(r["cx"]), int(r["cy"]), float(r["heat"])
        x0, y0 = cx * CELL, cy * CELL
        feats.append({"type": "Feature",
                      "properties": {"h": round(h, 3), "hs": round(float(np.clip((h - lo) / (hi - lo), 0, 1)), 3)},
                      "geometry": {"type": "Polygon", "coordinates": [[
                          [x0, y0], [x0 + CELL, y0], [x0 + CELL, y0 + CELL], [x0, y0 + CELL], [x0, y0]]]}})
    (config.FRONT_DATA / "heat_grid.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")))

    share = query("q_hot_share.sql")[0]
    findings = {
        "hot_share": float(share["hot_share"]), "network_km": float(share["network_km"]),
        "lst_p05_c": float(share["lst_p05_c"]), "lst_p95_c": float(share["lst_p95_c"]),
        "hottest": [{"name": r["name"], "heat": float(r["heat"]), "lst_c": float(r["lst_c"]),
                     "length_m": float(r["length_m"]), "lon": float(r["lon"]), "lat": float(r["lat"])}
                    for r in query("q_hottest_streets.sql")],
        "coolest": [{"name": r["name"], "heat": float(r["heat"]), "lst_c": float(r["lst_c"]),
                     "length_m": float(r["length_m"]), "lon": float(r["lon"]), "lat": float(r["lat"])}
                    for r in query("q_coolest_streets.sql")],
    }
    (config.FRONT_DATA / "findings.json").write_text(json.dumps(findings, indent=2))

    ath.s3.upload_file(str(config.WORK / "graph.json.gz"), config.BUCKET, "router/graph.json.gz")
    print(f"Wrote {len(feats):,} heat cells, findings.json, and uploaded router/graph.json.gz")
    print(f"{findings['hot_share']:.1%} of street length is in high-heat zones.")
    print("Hottest:", ", ".join(h["name"] for h in findings["hottest"][:3]))
    print("Coolest:", ", ".join(c["name"] for c in findings["coolest"][:3]))


if __name__ == "__main__":
    main()
