import os
import re
import urllib.request
import json
import time

api_url = os.getenv("COOLWALK_API_URL", "")
if not api_url and os.path.exists("frontend/config.js"):
    cfg_text = open("frontend/config.js").read()
    m = re.search(r'apiUrl:\s*["\']([^"\']+)["\']', cfg_text)
    if m: api_url = m.group(1)

url = f"{api_url}/route"
presets = [
  {'label': 'Chandni Chowk to Connaught Place', 'a': [77.2303, 28.6562], 'b': [77.2167, 28.6315]},
  {'label': 'Connaught Place to India Gate', 'a': [77.2167, 28.6315], 'b': [77.2295, 28.6129]},
  {'label': 'India Gate to Lodhi Garden', 'a': [77.2295, 28.6129], 'b': [77.2197, 28.5931]},
]

for p in presets:
    t0 = time.time()
    data = json.dumps({'origin': p['a'], 'destination': p['b'], 'alpha': 3}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as resp:
            t1 = time.time()
            res = json.loads(resp.read().decode('utf-8'))
            s = res['shortest']
            c = res['cool']
            print(f"=== {p['label']} (took {t1-t0:.2f}s) ===")
            print(f"Shortest: {s['minutes']} min, {s['length_m']} m, hot_share={s['hot_share']:.1%}")
            print(f"CoolWalk: {c['minutes']} min, {c['length_m']} m, hot_share={c['hot_share']:.1%}")
            gain = (s['hot_share'] - c['hot_share']) * 100
            diff_m = c['minutes'] - s['minutes']
            print(f"Avoids: {gain:.1f}% hot-zone exposure for +{diff_m:.1f} min extra walking\n")
    except Exception as e:
        print(f"Error for {p['label']}: {e}\n")
