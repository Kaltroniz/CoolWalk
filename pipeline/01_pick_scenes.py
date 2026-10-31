"""Step 1. Pick one clear Landsat 8/9 scene and same-day Sentinel-2 tiles for the study area.

Reads the Earth Search STAC API (public, no login). Writes work/scenes.json.
Choose a different Landsat scene with:  SCENE_INDEX=2 python pipeline/01_pick_scenes.py
"""
import json
import os
import sys

from pystac_client import Client
from shapely.geometry import box, shape

import config

STAC = "https://earth-search.aws.element84.com/v1"


def s3_href(asset):
    """Prefer the s3:// location. Landsat's default https link needs a USGS login."""
    alt = (asset.extra_fields.get("alternate") or {}).get("s3", {}).get("href")
    return alt or asset.href


def need(item, keys):
    missing = [k for k in keys if k not in item.assets]
    if missing:
        print(f"{item.id}: missing assets {missing}. Available: {sorted(item.assets)}")
        sys.exit(1)


def search(collection, max_cloud):
    cat = Client.open(STAC)
    res = cat.search(collections=[collection], bbox=config.BBOX, datetime=config.DATE_RANGE,
                     query={"eo:cloud_cover": {"lt": max_cloud}}, max_items=300)
    return list(res.items())


def main():
    area = box(*config.BBOX)
    ls = [i for i in search("landsat-c2-l2", config.LANDSAT_MAX_CLOUD) if shape(i.geometry).contains(area)]
    if not ls:
        sys.exit("No clear Landsat scene found. Widen COOLWALK_DATES or raise LANDSAT_MAX_CLOUD.")
    ls.sort(key=lambda i: i.properties.get("eo:cloud_cover", 100))
    print("Landsat candidates (lowest cloud first):")
    for n, i in enumerate(ls[:8]):
        print(f"  [{n}] {i.id}  {i.datetime:%Y-%m-%d}  cloud {i.properties.get('eo:cloud_cover'):.1f}%")
    chosen = ls[min(int(os.getenv("SCENE_INDEX", "0")), len(ls) - 1)]
    need(chosen, ["lwir11", "qa_pixel"])

    s2_all = search("sentinel-2-l2a", config.S2_MAX_CLOUD)
    if not s2_all:
        sys.exit("No Sentinel-2 scene found. Raise S2_MAX_CLOUD or widen the date range.")
    day = chosen.datetime.date()
    s2_all.sort(key=lambda i: abs((i.datetime.date() - day).days))
    s2_day = s2_all[0].datetime.date()
    s2 = [i for i in s2_all if i.datetime.date() == s2_day]
    for i in s2:
        need(i, ["red", "nir", "scl"])

    out = {
        "landsat": {"id": chosen.id, "date": f"{chosen.datetime:%Y-%m-%d}",
                    "cloud": chosen.properties.get("eo:cloud_cover"),
                    "lwir11": s3_href(chosen.assets["lwir11"]), "qa": s3_href(chosen.assets["qa_pixel"])},
        "sentinel": {"date": str(s2_day), "items": [
            {"id": i.id, "cloud": i.properties.get("eo:cloud_cover"),
             "red": s3_href(i.assets["red"]), "nir": s3_href(i.assets["nir"]), "scl": s3_href(i.assets["scl"])}
            for i in s2]},
    }

    # Pick up to 3 clear Landsat scenes on different dates for independent held-out validation
    val_candidates = []
    seen_dates = {chosen.datetime.date()}
    for item in ls:
        d = item.datetime.date()
        if d not in seen_dates and item.id != chosen.id and item.properties.get("eo:cloud_cover", 100) < 15:
            seen_dates.add(d)
            val_candidates.append({
                "id": item.id,
                "date": f"{item.datetime:%Y-%m-%d}",
                "cloud": item.properties.get("eo:cloud_cover"),
                "lwir11": s3_href(item.assets["lwir11"]),
                "qa": s3_href(item.assets["qa_pixel"])
            })
            if len(val_candidates) == 3:
                break
    out["validation_scenes"] = val_candidates

    (config.WORK / "scenes.json").write_text(json.dumps(out, indent=2))
    print(f"\nLandsat {out['landsat']['date']} + Sentinel-2 {out['sentinel']['date']} "
          f"({len(s2)} tile(s)). Picked {len(val_candidates)} validation scene(s). Saved work/scenes.json")


if __name__ == "__main__":
    main()
