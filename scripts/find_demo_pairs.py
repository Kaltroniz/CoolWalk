"""Find the best walks for the demo video, using the real graph (no AWS needed).

Run after pipeline step 2:  python scripts/find_demo_pairs.py
Prints origin/destination pairs 1.5-4 km apart where CoolWalk cuts the most time in
high-heat zones for the smallest extra walking time. Paste the best three into
the PRESETS list in frontend/index.html (check them on the map first).
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend", "router"))
os.environ.setdefault("GRAPH_LOCAL", os.path.join(os.path.dirname(__file__), "..", "work", "graph.json.gz"))
import app  # noqa: E402

g = app.load()
random.seed(7)
n = len(g["nodes"])
rows = []
for _ in range(600):
    a, b = random.randrange(n), random.randrange(n)
    d = app.dist_m(*g["nodes"][a], *g["nodes"][b])
    if not 1500 <= d <= 4000:
        continue
    pa, pb = g["nodes"][a], g["nodes"][b]
    try:
        r = app.route(g, {"origin": pa, "destination": pb, "alpha": 3})
    except app.ApiError:
        continue
    s, c = r["shortest"], r["cool"]
    if s["hot_share"] is None or c["hot_share"] is None:
        continue
    gain = s["hot_share"] - c["hot_share"]
    extra = c["minutes"] - s["minutes"]
    rows.append((gain - 0.02 * max(extra, 0), gain, extra, s["minutes"], pa, pb))
rows.sort(reverse=True)
print("score  hot-zone share cut   extra min  base min   origin -> destination")
for score, gain, extra, base, pa, pb in rows[:12]:
    print(f"{score:5.2f}  {gain:6.0%}              {extra:5.1f}      {base:5.1f}    {pa} -> {pb}")
