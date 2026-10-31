import gzip, json, pandas as pd

seg = pd.read_parquet("work/segments.parquet").set_index("edge_id")
lst, veg = seg.lst_c.to_dict(), seg.ndvi.to_dict()
with gzip.open("work/graph.json.gz", "rt", encoding="utf-8") as f:
    g = json.load(f)
for e in g["edges"]:
    e[5:] = [round(float(lst[e[4]]), 2), round(float(veg[e[4]]), 3)]
with gzip.open("work/graph.json.gz", "wt", encoding="utf-8") as f:
    json.dump(g, f, separators=(",", ":"))
print("edges with lst and ndvi:", len(g["edges"]))
