import urllib.request
import json
import time

url = 'https://euzq1skask.execute-api.us-east-1.amazonaws.com/route'
presets = [
  {'label': 'Jama Masjid to Delhi Gate', 'a': [77.2334, 28.6507], 'b': [77.2405, 28.6395]},
  {'label': 'Jama Masjid to Raj Ghat', 'a': [77.2334, 28.6507], 'b': [77.2485, 28.6405]},
  {'label': 'Delhi Gate to Lahori Gate', 'a': [77.2405, 28.6395], 'b': [77.2220, 28.6580]},
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
            print(f"Shortest: {s['minutes']} min, {s['length_m']} m, hot_share={s['hot_share']:.1%}, mean_lst={s.get('mean_lst_c')} C")
            print(f"CoolWalk: {c['minutes']} min, {c['length_m']} m, hot_share={c['hot_share']:.1%}, mean_lst={c.get('mean_lst_c')} C")
            gain = (s['hot_share'] - c['hot_share']) * 100
            diff_m = c['minutes'] - s['minutes']
            diff_lst = (s.get('mean_lst_c', 0) - c.get('mean_lst_c', 0))
            print(f"Avoids: {gain:.1f} percentage points hot exposure for +{diff_m:.1f} min (LST drop: {diff_lst:.1f} C)\n")
    except Exception as e:
        print(f"Error for {p['label']}: {e}\n")