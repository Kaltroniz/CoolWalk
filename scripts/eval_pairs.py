import urllib.request
import json

KEY = 'v1.public.eyJqdGkiOiJmMjE0ODcxZS00NzFkLTQxZDItOTZlNi1lYmU3ZTdiMmJjZWEifWeEYCtJOXjUE20R5AOJbGkKw8kiid1QbPKJ4ibNB-M8BSq18WWfZ3RElVvNsHpN50VSYosqgQTJhQFtA_ASdVOnPcAFYvE2A8yPj3PmH42KY1JlIko_MHvEP7CZDuT8awXnLIzNDEk4t76uUiEy12mRjugyX5aEO6milL42yBdOQ_SJZd2zyAskDoCEolPUTtDh8SDNhUgXHfnjL05_mDr0F51RzNnambeor_Z5LMGcI8TnIhjm37duYGCuEBdj8JlrzjSZ4MFv4jiNXVqOrh3c6iEYejU_Ju6olZ6To4tfBuIsmMRc4HSxCEMEwwYAhlV8iYfS0T5CqlBo5ZecsG0.ZWU0ZWIzMTktMWRhNi00Mzg0LTllMzYtNzlmMDU3MjRmYTkx'
API = 'https://euzq1skask.execute-api.us-east-1.amazonaws.com'

pairs = [
    ('Chandni Chowk', 'Connaught Place', [77.2303, 28.6562], [77.2167, 28.6315]),
    ('Jama Masjid', 'Delhi Gate', [77.2334, 28.6507], [77.2405, 28.6395]),
    ('Jama Masjid', 'Raj Ghat', [77.2334, 28.6507], [77.2485, 28.6405]),
    ('Chandni Chowk', 'Delhi Gate', [77.2303, 28.6562], [77.2405, 28.6395]),
    ('Delhi Gate', 'Lahori Gate', [77.2405, 28.6395], [77.2220, 28.6580]),
]

print(f"{'Walk':<35} | {'Std Source':<15} | {'Std min':<8} | {'Cool min':<8} | {'Std hot':<8} | {'Cool hot':<8} | {'Avoid pp':<8} | {'Std LST':<8} | {'Cool LST':<8}")
print("-" * 125)

for name1, name2, a, b in pairs:
    # 1. CoolWalk API route
    req = urllib.request.Request(f"{API}/route", data=json.dumps({'origin': a, 'destination': b, 'alpha': 3}).encode(), headers={'Content-Type': 'application/json'})
    r = json.loads(urllib.request.urlopen(req).read())
    s, c = r['shortest'], r['cool']

    # 2. Amazon Location Route
    aws_url = f"https://routes.geo.us-east-1.amazonaws.com/v2/routes?key={KEY}"
    aws_req = urllib.request.Request(aws_url, data=json.dumps({'Origin': a, 'Destination': b, 'TravelMode': 'Pedestrian', 'LegGeometryFormat': 'Simple'}).encode(), headers={'Content-Type': 'application/json', 'Referer': 'https://main.d3miw0zrayytbj.amplifyapp.com'})
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
    std_lst = f"{std.get('mean_lst_c', 0):.1f}°C"
    cool_lst = f"{c.get('mean_lst_c', 0):.1f}°C"
    print(f"{walk_name:<35} | {std_source:<15} | {std['minutes']:<8.1f} | {c['minutes']:<8.1f} | {std['hot_share']*100:<7.1f}% | {c['hot_share']*100:<7.1f}% | {avoided:<7.1f}pp | {std_lst:<8} | {cool_lst:<8}")
