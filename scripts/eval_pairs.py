import os
import re
import urllib.request
import json

KEY = os.getenv("MAP_API_KEY", "")
API = os.getenv("COOLWALK_API_URL", "")
if not (KEY and API) and os.path.exists("frontend/config.js"):
    cfg_text = open("frontend/config.js").read()
    if not KEY:
        m = re.search(r'mapKey:\s*["\']([^"\']+)["\']', cfg_text)
        if m: KEY = m.group(1)
    if not API:
        m = re.search(r'apiUrl:\s*["\']([^"\']+)["\']', cfg_text)
        if m: API = m.group(1)

pairs = [
    ('Chandni Chowk', 'Connaught Place', [77.2303, 28.6562], [77.2167, 28.6315]),
    ('Jama Masjid', 'Delhi Gate', [77.2334, 28.6507], [77.2405, 28.6395]),
    ('Jama Masjid', 'Raj Ghat', [77.2334, 28.6507], [77.2485, 28.6405]),
    ('Chandni Chowk', 'Delhi Gate', [77.2303, 28.6562], [77.2405, 28.6395]),
    ('Delhi Gate', 'Lahori Gate', [77.2405, 28.6395], [77.2220, 28.6580]),
]

print(f"{'Walk':<35} | {'Std Source':<15} | {'Std min':<8} | {'Cool min':<8} | {'Std hot':<8} | {'Cool hot':<8} | {'Avoided':<8}")
print("-" * 105)

for name1, name2, a, b in pairs:
    # 1. CoolWalk API route
    req = urllib.request.Request(f"{API}/route", data=json.dumps({'origin': a, 'destination': b, 'alpha': 3}).encode(), headers={'Content-Type': 'application/json'})
    r = json.loads(urllib.request.urlopen(req).read())
    s, c = r['shortest'], r['cool']

    # 2. Amazon Location Route
    aws_url = f"https://routes.geo.us-east-1.amazonaws.com/v2/routes?key={KEY}"
    aws_req = urllib.request.Request(aws_url, data=json.dumps({'Origin': a, 'Destination': b, 'TravelMode': 'Pedestrian', 'LegGeometryFormat': 'Simple'}).encode(), headers={'Content-Type': 'application/json', 'Referer': 'http://localhost:3000'})
    std_source = "Amazon Location"
    try:
        aws_resp = json.loads(urllib.request.urlopen(aws_req).read())
        line = aws_resp['Routes'][0]['Legs'][0]['Geometry']['LineString']
        score_req = urllib.request.Request(f"{API}/score", data=json.dumps({'line': line}).encode(), headers={'Content-Type': 'application/json'})
        std = json.loads(urllib.request.urlopen(score_req).read())
    except Exception as e:
        std_source = "Shortest path (fallback)"
        std = s

    avoided = (std['hot_share'] - c['hot_share']) * 100
    walk_name = f"{name1} to {name2}"
    print(f"{walk_name:<35} | {std_source:<15} | {std['minutes']:<8.1f} | {c['minutes']:<8.1f} | {std['hot_share']*100:<7.1f}% | {c['hot_share']*100:<7.1f}% | {avoided:<7.1f}%")

