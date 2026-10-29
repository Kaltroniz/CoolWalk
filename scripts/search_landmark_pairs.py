import os
import sys
import json

sys.path.insert(0, 'backend/router')
os.environ['GRAPH_LOCAL'] = 'work/graph.json.gz'
import app

g = app.load()

landmarks = [
    ('Chandni Chowk', [77.2303, 28.6562]),
    ('Red Fort', [77.2410, 28.6562]),
    ('Jama Masjid', [77.2334, 28.6507]),
    ('Connaught Place', [77.2167, 28.6315]),
    ('New Delhi Station', [77.2197, 28.6430]),
    ('Old Delhi Station', [77.2285, 28.6619]),
    ('Delhi Gate', [77.2405, 28.6395]),
    ('Daryaganj', [77.2405, 28.6465]),
    ('Raj Ghat', [77.2485, 28.6405]),
    ('Kashmere Gate', [77.2295, 28.6665]),
    ('Jhandewalan', [77.1995, 28.6445]),
    ('Ajmeri Gate', [77.2235, 28.6440]),
    ('Turkman Gate', [77.2330, 28.6430]),
    ('Lahori Gate', [77.2220, 28.6580]),
]

results = []
for i in range(len(landmarks)):
    for j in range(len(landmarks)):
        if i == j:
            continue
        name1, p1 = landmarks[i]
        name2, p2 = landmarks[j]
        d = app.dist_m(p1[0], p1[1], p2[0], p2[1])
        if not 1200 <= d <= 3800:
            continue
        try:
            r = app.route(g, {'origin': p1, 'destination': p2, 'alpha': 3})
            s, c = r['shortest'], r['cool']
            gain = (s['hot_share'] - c['hot_share']) * 100
            extra_m = c['minutes'] - s['minutes']
            if s['hot_share'] > 0.15 and gain > 5:
                results.append((gain, extra_m, name1, name2, p1, p2, s, c))
        except Exception:
            pass

results.sort(key=lambda x: (x[0], -x[1]), reverse=True)
print(f'Found {len(results)} landmark pairs with significant heat reduction:')
for gain, extra, n1, n2, p1, p2, s, c in results[:15]:
    sh_pct = s['hot_share'] * 100
    cl_pct = c['hot_share'] * 100
    print(f"{n1} -> {n2}: avoids {gain:.1f}% hot share (Shortest {sh_pct:.1f}% -> Cool {cl_pct:.1f}%), extra {extra:.1f} min (base {s['minutes']:.1f}m)")
    print(f"  Coords: {p1} to {p2}\n")

