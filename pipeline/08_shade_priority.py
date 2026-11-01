"""Step 8. Civic planner view - Where shade matters most.

Queries Amazon Athena / Apache Iceberg tables to find the highest-priority
walking corridors needing shade canopy, ranked by thermal exposure (heat >= 0.66)
and proximity (within 150m) to vulnerable civic facilities (schools, clinics/hospitals, bus stops).

Outputs:
  frontend/data/shade_priority.csv
  frontend/data/shade_priority.json
"""
import csv
import json
import math
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
import config
import importlib

ath = importlib.import_module("03_build_iceberg")

SQL_ATHENA = """
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
LIMIT 20
"""


def compute_from_parquet():
    """Fallback if Athena is unreachable: exact same spatial logic using local parquet files."""
    seg_file = config.WORK / "segments.parquet"
    places_file = config.WORK / "places.parquet"
    if not seg_file.exists() or not places_file.exists():
        raise RuntimeError("Missing segments.parquet or places.parquet in work/")

    df_seg = pd.read_parquet(seg_file)
    df_places = pd.read_parquet(places_file)

    # Filter hot segments with names
    hot = df_seg[(df_seg["heat_index"] >= 0.66) & (df_seg["name"].str.strip().str.len() > 0)].copy()
    civic = df_places[df_places["kind"].isin(["bus_stop", "school", "hospital"])].copy()

    records = []
    # Group by name
    for name, group in hot.groupby("name"):
        tot_m = group["length_m"].sum() / 2
        avg_lst = round(float(group["lst_c"].mean()), 1)
        avg_h = round(float(group["heat_index"].mean()), 2)
        longest_row = group.loc[group["length_m"].idxmax()]
        rep_lon = round(float(longest_row["mid_lon"]), 5)
        rep_lat = round(float(longest_row["mid_lat"]), 5)

        # Match facilities within 150m of any segment midpoint in group
        matched_places = set()
        for _, s_row in group.iterrows():
            slon, slat = s_row["mid_lon"], s_row["mid_lat"]
            box = civic[
                (civic["lat"].between(slat - 0.0013, slat + 0.0013)) &
                (civic["lon"].between(slon - 0.0015, slon + 0.0015))
            ]
            for _, p_row in box.iterrows():
                plon, plat = p_row["lon"], p_row["lat"]
                d = math.hypot((plon - slon) * 111320.0 * 0.878, (plat - slat) * 110540.0)
                if d <= 150.0:
                    matched_places.add((p_row["place_id"], p_row["kind"]))

        if not matched_places:
            continue

        b_count = sum(1 for _, k in matched_places if k == "bus_stop")
        s_count = sum(1 for _, k in matched_places if k == "school")
        h_count = sum(1 for _, k in matched_places if k == "hospital")
        score = s_count * 3 + h_count * 3 + b_count * 2

        records.append({
            "corridor": name,
            "avg_surface_c": avg_lst,
            "avg_heat_index": avg_h,
            "total_hot_m": round(tot_m),
            "bus_stops": b_count,
            "schools": s_count,
            "hospitals": h_count,
            "score": score,
            "lon": rep_lon,
            "lat": rep_lat,
        })

    records.sort(key=lambda r: (r["score"], r["total_hot_m"]), reverse=True)
    return records[:20]


def main():
    print("Running shade priority analysis...")
    data = None
    try:
        print("Querying Amazon Athena (coolwalk.segments JOIN coolwalk.places)...")
        qid = ath.run(SQL_ATHENA.strip(), config.DB)
        raw_rows = ath.rows(qid)
        data = []
        for r in raw_rows:
            data.append({
                "corridor": r["corridor"],
                "avg_surface_c": float(r["avg_surface_c"]),
                "avg_heat_index": float(r["avg_heat_index"]),
                "total_hot_m": int(float(r["total_hot_m"])),
                "bus_stops": int(r["bus_stops"]),
                "schools": int(r["schools"]),
                "hospitals": int(r["hospitals"]),
                "lon": float(r["lon"]),
                "lat": float(r["lat"]),
            })
        print(f"Athena returned {len(data)} corridors.")
    except Exception as e:
        print(f"Athena query note: {e}. Falling back to exact local parquet computation...")
        data = compute_from_parquet()
        print(f"Computed {len(data)} corridors from parquet.")

    # Save to frontend/data/
    out_dir = ROOT / "frontend" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "shade_priority.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Corridor", "Avg Surface Temp (°C)", "Avg Heat Index", "Hot Segment Length (m)", "Bus Stops", "Schools", "Hospitals/Clinics", "Longitude", "Latitude"])
        for r in data:
            writer.writerow([
                r["corridor"],
                f"{r['avg_surface_c']:.1f}",
                f"{r['avg_heat_index']:.2f}",
                r["total_hot_m"],
                r["bus_stops"],
                r["schools"],
                r["hospitals"],
                r["lon"],
                r["lat"],
            ])
    print(f"Wrote {csv_path}")

    json_path = out_dir / "shade_priority.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote {json_path}")

    print("\n--- TOP PRIORITY CORRIDORS FOR CIVIC SHADE INTERVENTION ---")
    print(f"{'Corridor':<30} | {'Hot (m)':<8} | {'Avg °C':<7} | {'Schools':<8} | {'Hospitals':<10} | {'Bus Stops':<9}")
    print("-" * 85)
    for r in data[:10]:
        print(f"{r['corridor']:<30} | {r['total_hot_m']:<8} | {r['avg_surface_c']:<7.1f} | {r['schools']:<8} | {r['hospitals']:<10} | {r['bus_stops']:<9}")


if __name__ == "__main__":
    main()

