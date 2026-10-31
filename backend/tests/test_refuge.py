"""Run: python backend/tests/test_refuge.py  (uses the synthetic city from test_router.py)"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "router"))
import app, refuge, test_router as T


def city():
    g = T.make_graph()
    # two shaded places of the same kind: one on the hot street (close), one on the cool street (farther)
    g["places"] = [
        {"kind": "park", "name": "Hot-street park", "lon": T.LON0 + 5 * T.STEP, "lat": T.LAT0},
        {"kind": "park", "name": "Cool-street park", "lon": T.LON0 + 5 * T.STEP, "lat": T.LAT0 + 2 * T.STEP},
        {"kind": "water", "name": "Far fountain", "lon": T.LON0 + 40 * T.STEP, "lat": T.LAT0},  # off the network
    ]
    return g


def test_fastest_vs_cool_choose_differently():
    g = city()
    out = refuge.run(g, {"origin": [T.LON0, T.LAT0], "alpha": 3, "max_minutes": 20}, app)
    park = next(o for o in out["options"] if o["kind"] == "park")
    assert park["fastest"]["name"] == "Hot-street park"
    assert park["cool"]["name"] == "Cool-street park"
    assert park["cool"]["hot_share"] < park["fastest"]["hot_share"]
    assert park["cool"]["minutes"] > park["fastest"]["minutes"]
    assert all(o["kind"] != "water" for o in out["options"])      # not near a street, ignored


def test_budget_and_validation():
    g = city()
    out = refuge.run(g, {"origin": [T.LON0, T.LAT0], "max_minutes": 3}, app)
    assert out["options"] == []                                   # 3 minutes reaches nothing here
    for bad in ({"origin": [10, 10]}, {}):
        try:
            refuge.run(g, bad, app); raise AssertionError("expected ApiError")
        except app.ApiError as e:
            assert e.status == 400


def test_origin_on_a_place():
    g = city()
    out = refuge.run(g, {"origin": [T.LON0 + 5 * T.STEP, T.LAT0], "kinds": ["park"]}, app)
    assert out["options"][0]["fastest"]["minutes"] == 0.0


if __name__ == "__main__":
    for k, v in sorted(globals().items()):
        if k.startswith("test_"): v(); print("ok  ", k)

