"""CoolWalk router (AWS Lambda, HTTP API payload v2).

Endpoints
  GET  /health  -> coverage box and data provenance
  POST /route   -> {origin:[lon,lat], destination:[lon,lat], alpha?, max_detour?}
                   returns the shortest walk and the heat-aware walk, with metrics
  POST /score   -> {line:[[lon,lat],...]}
                   scores any walking route (used for the Amazon Location baseline)

Heat-aware cost of a street segment = length_m * (1 + alpha * heat), heat in 0..1.
alpha = 0 gives the plain shortest walk. Standard library only (boto3 is imported lazily).
"""
import bisect
import gzip
import heapq
import json
import math
import os

WALK_MPS = 1.35          # average walking speed, metres per second
HOT_T = 0.66             # heat index at or above this counts as a "high-heat zone"
CELL = 0.001             # spatial hash cell, degrees (about 110 m)
SAMPLE_M = 20.0          # spacing of sample points along streets and routes
SNAP_MAX_M = 400.0       # farthest we will snap a click to a street
MATCH_M = 60.0           # farthest a route point may sit from a scored street
BINS = 48                # resolution of the heat strip

_G = None


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


# ---------------------------------------------------------------- geometry
def dist_m(lon1, lat1, lon2, lat2):
    k = math.cos(math.radians((lat1 + lat2) / 2))
    return math.hypot((lon2 - lon1) * 111320.0 * k, (lat2 - lat1) * 110540.0)


def densify(coords, step=SAMPLE_M):
    """Yield points roughly every `step` metres along a polyline."""
    if not coords:
        return
    for (x1, y1), (x2, y2) in zip(coords, coords[1:]):
        n = max(1, int(dist_m(x1, y1, x2, y2) // step))
        for k in range(n):
            t = k / n
            yield (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)
    yield tuple(coords[-1])


def cell(lon, lat):
    return (int(lon // CELL), int(lat // CELL))


# ---------------------------------------------------------------- graph
def build(data):
    nodes, edges, geoms = data["nodes"], data["edges"], data["geoms"]
    adj = [[] for _ in nodes]
    for i, e in enumerate(edges):
        u, v, length, heat, _eid = e[:5]          # 6th is lst_c, 7th is ndvi if present
        adj[u].append((v, length, heat, i))
    node_grid = {}
    for i, (lon, lat) in enumerate(nodes):
        node_grid.setdefault(cell(lon, lat), []).append(i)
    pt_grid = {}
    for i, e in enumerate(edges):
        lst = e[5] if len(e) > 5 else None
        ndvi = e[6] if len(e) > 6 else None
        for lon, lat in densify(geoms[i]):
            pt_grid.setdefault(cell(lon, lat), []).append((lon, lat, e[3], lst, ndvi))
    return {"nodes": nodes, "edges": edges, "geoms": geoms, "adj": adj,
            "node_grid": node_grid, "pt_grid": pt_grid, "meta": data.get("meta", {})}


def load():
    global _G
    if _G is not None:
        return _G
    local = os.environ.get("GRAPH_LOCAL")
    if local:
        with open(local, "rb") as f:
            raw = f.read()
    else:
        import boto3
        obj = boto3.client("s3").get_object(
            Bucket=os.environ["BUCKET"], Key=os.environ.get("GRAPH_KEY", "router/graph.json.gz"))
        raw = obj["Body"].read()
    _G = build(json.loads(gzip.decompress(raw)))
    return _G


def nearest_node(g, lon, lat):
    cx, cy = cell(lon, lat)
    best, stop_at = None, None
    for r in range(0, 9):
        if stop_at is not None and r > stop_at:
            break
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r:
                    continue
                for i in g["node_grid"].get((cx + dx, cy + dy), ()):
                    d = dist_m(lon, lat, *g["nodes"][i])
                    if best is None or d < best[0]:
                        best = (d, i)
        if best and stop_at is None:
            stop_at = r + 1
    return best  # (metres, node index) or None


def astar(g, s, t, alpha):
    nodes, adj = g["nodes"], g["adj"]
    tx, ty = nodes[t]

    def h(n):
        return dist_m(nodes[n][0], nodes[n][1], tx, ty)

    best = {s: 0.0}
    prev = {}
    done = set()
    pq = [(h(s), 0.0, s)]
    while pq:
        _f, gc, n = heapq.heappop(pq)
        if n in done:
            continue
        if n == t:
            break
        done.add(n)
        for v, length, heat, ei in adj[n]:
            if v in done:
                continue
            c = gc + length * (1.0 + alpha * heat)
            if c < best.get(v, 1e18):
                best[v] = c
                prev[v] = (n, ei)
                heapq.heappush(pq, (c + h(v), c, v))
    else:
        return None
    path, n = [], t
    while n != s:
        n, ei = prev[n][0], prev[n][1]
        path.append(ei)
    path.reverse()
    return path


# ---------------------------------------------------------------- metrics
def _round_line(line):
    return [[round(x, 5), round(y, 5)] for x, y in line]


def _finish(length_m, heats, profile, line=None, extra=None, lsts=None, ndvis=None):
    known = [h for h in heats if h is not None]
    known_lst = [t for t in (lsts or []) if t is not None]
    known_ndvi = [v for v in (ndvis or []) if v is not None]
    out = {
        "length_m": round(length_m, 1),
        "minutes": round(length_m / WALK_MPS / 60.0, 1),
        "mean_heat": round(sum(known) / len(known), 3) if known else None,
        "hot_share": round(sum(1 for h in known if h >= HOT_T) / len(known), 3) if known else None,
        "mean_lst_c": round(sum(known_lst) / len(known_lst), 1) if known_lst else None,
        "mean_ndvi": round(sum(known_ndvi) / len(known_ndvi), 3) if known_ndvi else None,
        "profile": [None if p is None else round(p, 3) for p in profile],
    }
    if line is not None:
        out["line"] = _round_line(line)
    if extra:
        out.update(extra)
    return out


def path_metrics(g, eis):
    edges, geoms = g["edges"], g["geoms"]
    line, cum, total, per_edge, per_lst, per_ndvi = [], [], 0.0, [], [], []
    for ei in eis:
        gm = geoms[ei]
        line.extend(gm if not line else gm[1:])
        total += edges[ei][2]
        cum.append(total)
        per_edge.append(edges[ei][3])
        per_lst.append(edges[ei][5] if len(edges[ei]) > 5 else None)
        per_ndvi.append(edges[ei][6] if len(edges[ei]) > 6 else None)
    # length-weighted heat samples at 5 m spacing for stable shares
    heats, lsts, ndvis, prev = [], [], [], 0.0
    for c, h, t, v in zip(cum, per_edge, per_lst, per_ndvi):
        n = max(1, int((c - prev) // 5))
        heats.extend([h] * n)
        lsts.extend([t] * n)
        ndvis.extend([v] * n)
        prev = c
    profile = []
    for k in range(BINS):
        d = (k + 0.5) / BINS * total
        profile.append(per_edge[min(bisect.bisect_left(cum, d), len(per_edge) - 1)])
    return _finish(total, heats, profile, line, lsts=lsts, ndvis=ndvis)


def score_line(g, line):
    pts = list(densify([tuple(p) for p in line]))
    heats, lsts, ndvis = [], [], []
    for lon, lat in pts:
        cx, cy = cell(lon, lat)
        best = None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for pt_tuple in g["pt_grid"].get((cx + dx, cy + dy), ()):
                    plon, plat, h = pt_tuple[:3]
                    lst = pt_tuple[3] if len(pt_tuple) > 3 else None
                    ndvi = pt_tuple[4] if len(pt_tuple) > 4 else None
                    d = dist_m(lon, lat, plon, plat)
                    if d <= MATCH_M and (best is None or d < best[0]):
                        best = (d, h, lst, ndvi)
        heats.append(best[1] if best else None)
        lsts.append(best[2] if best else None)
        ndvis.append(best[3] if best else None)
    length = sum(dist_m(a[0], a[1], b[0], b[1]) for a, b in zip(line, line[1:]))
    profile = [heats[min(int((k + 0.5) / BINS * len(heats)), len(heats) - 1)] for k in range(BINS)] if heats else []
    matched = sum(1 for h in heats if h is not None)
    return _finish(length, heats, profile, None,
                   {"coverage": round(matched / len(heats), 3) if heats else 0.0}, lsts=lsts, ndvis=ndvis)


# ---------------------------------------------------------------- handlers
def _point(v, name):
    if (not isinstance(v, (list, tuple)) or len(v) != 2
            or not all(isinstance(x, (int, float)) for x in v)):
        raise ApiError(400, f"{name} must be [longitude, latitude].")
    return float(v[0]), float(v[1])


def _inside(g, lon, lat):
    w, s, e, n = g["meta"].get("bbox", (-180, -90, 180, 90))
    return w - 0.01 <= lon <= e + 0.01 and s - 0.01 <= lat <= n + 0.01


def route(g, body):
    o = _point(body.get("origin"), "origin")
    d = _point(body.get("destination"), "destination")
    if not (_inside(g, *o) and _inside(g, *d)):
        raise ApiError(400, "Both points need to be inside the central Delhi coverage area.")
    alpha = min(max(float(body.get("alpha", 3.0)), 0.0), 8.0)
    max_detour = min(max(float(body.get("max_detour", 1.45)), 1.0), 2.5)
    so, sd = nearest_node(g, *o), nearest_node(g, *d)
    if not so or not sd or so[0] > SNAP_MAX_M or sd[0] > SNAP_MAX_M:
        raise ApiError(400, "One of the points is too far from a walkable street. Move it closer to a road.")
    shortest = astar(g, so[1], sd[1], 0.0)
    if shortest is None:
        raise ApiError(404, "No walking connection between those points.")
    s_met = path_metrics(g, shortest)
    cool, used = shortest, 0.0
    a = alpha
    while a > 0.05 and alpha > 0:
        cand = astar(g, so[1], sd[1], a)
        if cand is not None:
            m = path_metrics(g, cand)
            if m["length_m"] <= s_met["length_m"] * max_detour:
                cool, used = cand, a
                break
        a /= 2.0
    c_met = path_metrics(g, cool)
    return {
        "shortest": s_met,
        "cool": c_met,
        "alpha_used": round(used, 2),
        "snapped": {"origin_m": round(so[0]), "destination_m": round(sd[0])},
    }


def score(g, body):
    line = body.get("line")
    if not isinstance(line, list) or len(line) < 2 or len(line) > 6000:
        raise ApiError(400, "line must be a list of 2 to 6000 [longitude, latitude] points.")
    return score_line(g, [_point(p, "line point") for p in line])


def health(g):
    return {"ok": True, "bbox": g["meta"].get("bbox"), "meta": g["meta"],
            "nodes": len(g["nodes"]), "edges": len(g["edges"]),
            "hot_threshold": HOT_T, "walk_speed_mps": WALK_MPS}


HEADERS = {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}


def _resp(status, payload):
    return {"statusCode": status, "headers": HEADERS, "body": json.dumps(payload)}


def handler(event, _context=None):
    path = event.get("rawPath", "/")
    try:
        g = load()
        if path.endswith("/health"):
            return _resp(200, health(g))
        body = json.loads(event.get("body") or "{}")
        if path.endswith("/route"):
            return _resp(200, route(g, body))
        if path.endswith("/score"):
            return _resp(200, score(g, body))
        return _resp(404, {"error": "Not found."})
    except ApiError as e:
        return _resp(e.status, {"error": str(e)})
    except json.JSONDecodeError:
        return _resp(400, {"error": "Request body must be valid JSON."})
    except Exception as e:  # noqa: BLE001 - log, never leak internals
        print("router error:", repr(e))
        return _resp(500, {"error": "Routing failed. Try again in a moment."})
