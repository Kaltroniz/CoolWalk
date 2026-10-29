"""Offline tests: a 3-lane synthetic city. Run: python backend/tests/test_router.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "router"))
import app  # noqa: E402

LON0, LAT0, STEP = 77.2000, 28.6000, 0.001  # ~100 m grid


def make_graph(cols=12, rows=3, hot_row=0, cool_row=2):
    """rows are horizontal streets; the direct row is hot, the far row is cool."""
    nodes, idx = [], {}
    for r in range(rows):
        for c in range(cols):
            idx[(c, r)] = len(nodes)
            nodes.append([LON0 + c * STEP, LAT0 + r * STEP])
    edges, geoms = [], []

    def add(a, b, heat):
        for u, v in ((a, b), (b, a)):
            length = app.dist_m(*nodes[u], *nodes[v])
            edges.append([u, v, length, heat, len(edges)])
            geoms.append([nodes[u], nodes[v]])

    for r in range(rows):
        heat = 0.95 if r == hot_row else (0.05 if r == cool_row else 0.5)
        for c in range(cols - 1):
            add(idx[(c, r)], idx[(c + 1, r)], heat)
    for c in (0, cols - 1):  # only the two ends connect the streets
        for r in range(rows - 1):
            add(idx[(c, r)], idx[(c, r + 1)], 0.5)
    meta = {"bbox": [LON0 - 0.001, LAT0 - 0.001, LON0 + cols * STEP, LAT0 + rows * STEP]}
    return app.build({"nodes": nodes, "edges": edges, "geoms": geoms, "meta": meta})


def test_alpha_zero_is_shortest():
    g = make_graph()
    a, b = nearest = app.nearest_node(g, LON0, LAT0), app.nearest_node(g, LON0 + 11 * STEP, LAT0)
    assert nearest and a[1] != b[1]
    p0 = app.astar(g, a[1], b[1], 0.0)
    m = app.path_metrics(g, p0)
    assert abs(m["length_m"] - 11 * app.dist_m(LON0, LAT0, LON0 + STEP, LAT0)) < 1.0
    assert m["hot_share"] == 1.0  # the direct street is the hot one


def test_cool_route_avoids_heat_with_bounded_detour():
    g = make_graph()
    out = app.route(g, {"origin": [LON0, LAT0], "destination": [LON0 + 11 * STEP, LAT0],
                        "alpha": 3, "max_detour": 1.8})
    assert out["cool"]["hot_share"] < out["shortest"]["hot_share"]
    assert out["cool"]["mean_heat"] < out["shortest"]["mean_heat"]
    assert out["cool"]["length_m"] <= out["shortest"]["length_m"] * 1.8
    assert out["cool"]["minutes"] > out["shortest"]["minutes"]
    assert len(out["cool"]["profile"]) == app.BINS


def test_detour_cap_falls_back_to_shortest():
    g = make_graph()
    out = app.route(g, {"origin": [LON0, LAT0], "destination": [LON0 + 11 * STEP, LAT0],
                        "alpha": 8, "max_detour": 1.0})
    assert out["cool"]["length_m"] == out["shortest"]["length_m"]


def test_score_line_matches_streets():
    g = make_graph()
    hot_line = [[LON0, LAT0], [LON0 + 11 * STEP, LAT0]]
    cool_line = [[LON0, LAT0 + 2 * STEP], [LON0 + 11 * STEP, LAT0 + 2 * STEP]]
    hot, cool = app.score_line(g, hot_line), app.score_line(g, cool_line)
    assert hot["coverage"] > 0.9 and cool["coverage"] > 0.9
    assert hot["mean_heat"] > 0.9 and cool["mean_heat"] < 0.1


def test_validation_errors():
    g = make_graph()
    for body, status in [({"origin": [LON0, LAT0]}, 400),
                         ({"origin": [10, 10], "destination": [LON0, LAT0]}, 400)]:
        try:
            app.route(g, body)
            raise AssertionError("expected ApiError")
        except app.ApiError as e:
            assert e.status == status


def test_handler_roundtrip():
    import json
    os.environ.pop("GRAPH_LOCAL", None)
    app._G = make_graph()
    ev = {"rawPath": "/route", "body": json.dumps(
        {"origin": [LON0, LAT0], "destination": [LON0 + 11 * STEP, LAT0], "alpha": 3})}
    r = app.handler(ev)
    assert r["statusCode"] == 200 and "cool" in json.loads(r["body"])
    assert app.handler({"rawPath": "/health"})["statusCode"] == 200
    assert app.handler({"rawPath": "/route", "body": "{oops"})["statusCode"] == 400


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("ok  ", fn.__name__)
    print(f"{len(fns)} passed")
