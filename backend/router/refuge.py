"""Cool-refuge finder: nearest park / water point / metro station by a fast walk and by a cool walk.

POST /refuge {origin:[lon,lat], alpha?, kinds?:[...], max_minutes?}
Needs graph["places"] = [{"kind","name","lon","lat"}]. Wire-up in app.py handler:
    if path.endswith("/refuge"):
        import refuge, sys
        return _resp(200, refuge.run(g, body, sys.modules[__name__]))
"""
import heapq


def _places_by_node(g, A):
    if "_pbn" not in g:
        pbn = {}
        for p in g.get("places", []):
            s = A.nearest_node(g, p["lon"], p["lat"])
            if s and s[0] <= 150:                      # ignore places not near a walkable street
                pbn.setdefault(s[1], []).append(p)
        g["_pbn"] = pbn
    return g["_pbn"]


def _search(g, A, s, alpha, kinds, max_len):
    """Dijkstra on length * (1 + alpha * heat); returns best place per kind and the path pointers."""
    pbn, adj = _places_by_node(g, A), g["adj"]
    cost, length, prev, done, best = {s: 0.0}, {s: 0.0}, {}, set(), {}
    pq = [(0.0, s)]
    while pq:
        c, n = heapq.heappop(pq)
        if n in done:
            continue
        done.add(n)
        for p in pbn.get(n, ()):
            if (not kinds or p["kind"] in kinds) and p["kind"] not in best:
                best[p["kind"]] = (p, n)
        if kinds and all(k in best for k in kinds):
            break
        for v, L, h, ei in adj[n]:
            nl = length[n] + L
            if v in done or nl > max_len:
                continue
            nc = c + L * (1.0 + alpha * h)
            if nc < cost.get(v, 1e18):
                cost[v], length[v], prev[v] = nc, nl, (n, ei)
                heapq.heappush(pq, (nc, v))
    return best, prev


def _metrics(g, A, prev, s, t):
    eis, n = [], t
    while n != s:
        n, ei = prev[n]
        eis.append(ei)
    if not eis:
        return {"length_m": 0.0, "minutes": 0.0, "hot_share": None, "mean_lst_c": None, "line": []}
    return A.path_metrics(g, eis[::-1])


def run(g, body, A):
    o = A._point(body.get("origin"), "origin")
    if not A._inside(g, *o):
        raise A.ApiError(400, "Pick a point inside the central Delhi coverage area.")
    so = A.nearest_node(g, *o)
    if not so or so[0] > A.SNAP_MAX_M:
        raise A.ApiError(400, "That point is too far from a walkable street.")
    alpha = min(max(float(body.get("alpha", 3.0)), 0.0), 8.0)
    kinds = [k for k in (body.get("kinds") or []) if isinstance(k, str)] or None
    max_len = min(max(float(body.get("max_minutes", 20)), 3.0), 40.0) * 60.0 * A.WALK_MPS
    s = so[1]
    fast, pf = _search(g, A, s, 0.0, kinds, max_len)
    cool, pc = _search(g, A, s, alpha, kinds, max_len)
    options = []
    for kind in sorted(set(fast) | set(cool)):
        opt = {"kind": kind}
        for label, (best, prev) in (("fastest", (fast, pf)), ("cool", (cool, pc))):
            if kind in best:
                p, n = best[kind]
                name = p.get("name")
                if not name or str(name).strip().lower() in ("", "nan", "none"):
                    name = f"Public {kind.capitalize()}" if kind != "water" else "Drinking Water Point"
                opt[label] = {"name": name, "lon": p["lon"], "lat": p["lat"],
                              **_metrics(g, A, prev, s, n)}
        options.append(opt)
    return {"options": options, "snapped_m": round(so[0])}
