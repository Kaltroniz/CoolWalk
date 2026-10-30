import os
import sys
import json
import pandas as pd

sys.path.insert(0, 'backend/router')
os.environ['GRAPH_LOCAL'] = 'work/graph.json.gz'
import app

df = pd.read_parquet('work/segments.parquet')
print("Total rows in parquet:", len(df))

landmarks = [
    ('Delhi Gate', 'Lahori Gate', [77.2405, 28.6395], [77.2220, 28.6580]),
    ('Chandni Chowk', 'Delhi Gate', [77.2303, 28.6562], [77.2405, 28.6395]),
    ('Jama Masjid', 'Delhi Gate', [77.2334, 28.6507], [77.2405, 28.6395]),
    ('Jama Masjid', 'Raj Ghat', [77.2334, 28.6507], [77.2485, 28.6405]),
    ('Old Delhi Station', 'Delhi Gate', [77.2285, 28.6619], [77.2405, 28.6395]),
]

g = app.load()
for name1, name2, a, b in landmarks:
    try:
        r = app.route(g, {'origin': a, 'destination': b, 'alpha': 3})
        s, c = r['shortest'], r['cool']
        diff_hot = (s['hot_share'] - c['hot_share']) * 100
        extra_min = c['minutes'] - s['minutes']
        print(f"{name1} -> {name2}:")
        print(f"  Shortest: {s['minutes']} min, {s['hot_share']*100:.1f}% hot")
        print(f"  CoolWalk: {c['minutes']} min, {c['hot_share']*100:.1f}% hot")
        print(f"  Avoids: {diff_hot:.1f} pts, extra: {extra_min:.1f} min\n")
    except Exception as e:
        print(name1, name2, e)

