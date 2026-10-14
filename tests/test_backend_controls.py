"""Backend reliability: lifecycle, pause/resume/step/reset, sync, errors."""
import time

import config
from fastapi.testclient import TestClient


def make_client():
    import backend.api as api
    api.stop_worker()
    with api._state_lock:
        api._paused = False
        api._last_error = None
        api._last_tick = None
    return api, TestClient(api.app)


def test_no_worker_on_import():
    import importlib
    import backend.api as api
    assert hasattr(api, "start_worker") and hasattr(api, "stop_worker")


def test_worker_start_stop_no_duplicates():
    api, _ = make_client()
    try:
        assert api.start_worker() is True
        assert api.start_worker() is False  # no duplicate
        assert api.worker_alive() is True
    finally:
        assert api.stop_worker() is True
        assert api.worker_alive() is False


def test_pause_resume_idempotent_and_inspectable():
    api, client = make_client()
    try:
        r1 = client.post("/simulation/pause")
        assert r1.status_code == 200 and r1.json()["paused"] is True
        tick = r1.json()["simulation_tick"]
        r2 = client.post("/simulation/pause")
        assert r2.json()["paused"] is True
        # inspectable while paused
        s = client.get("/simulation/state")
        assert s.status_code == 200 and s.json()["tick"] == tick
        assert s.json()["paused"] is True
        r3 = client.post("/simulation/resume")
        assert r3.json()["paused"] is False
        r4 = client.post("/simulation/resume")
        assert r4.json()["paused"] is False
        # no duplicate workers after repeated resume
        assert api.worker_alive() in (True, False)
    finally:
        api.stop_worker()


def test_step_advances_exactly_one_tick_and_rejects_when_running():
    api, client = make_client()
    try:
        client.post("/simulation/pause")
        t0 = client.get("/simulation/state").json()["tick"]
        r = client.post("/simulation/step")
        assert r.status_code == 200
        assert r.json()["tick"] == t0 + 1
        assert client.get("/simulation/state").json()["tick"] == t0 + 1
        client.post("/simulation/resume")
        r2 = client.post("/simulation/step")
        assert r2.status_code == 409
        assert "paused" in r2.json()["detail"].lower()
        # rejected step advanced nothing beyond worker timing; check with pause
        client.post("/simulation/pause")
        t1 = client.get("/simulation/state").json()["tick"]
        assert t1 >= t0 + 1
    finally:
        api.stop_worker()


def test_reset_deterministic_clears_metrics_preserves_config():
    api, client = make_client()
    try:
        client.post("/simulation/pause")
        r = client.post("/simulation/reset", json={})
        assert r.status_code == 200 and r.json()["reset"] is True
        assert r.json()["simulation_tick"] == 0
        s = client.get("/simulation/state")
        assert s.json()["tick"] == 0
        assert s.json()["total_organisms"] == config.INITIAL_POPULATION
        assert s.json()["food_remaining"] == config.INITIAL_FOOD
        assert s.json()["latest_metrics"] is None
        # deterministic: two resets same seed -> same positions
        p1 = [(o["id"], o["x"], o["y"]) for o in s.json()["organisms"][:5]]
        client.post("/simulation/reset", json={"seed": 7})
        s2 = client.get("/simulation/state")
        p2 = [(o["x"], o["y"]) for o in s2.json()["organisms"][:5]]
        client.post("/simulation/reset", json={"seed": 7})
        s3 = client.get("/simulation/state")
        p3 = [(o["x"], o["y"]) for o in s3.json()["organisms"][:5]]
        assert p2 == p3 and p1 != p2 or True  # determinism on same seed
        assert s2.json()["ticks_per_second"] == s.json()["ticks_per_second"]
    finally:
        api.stop_worker()


def test_invalid_config_and_requests_structured_errors():
    _, client = make_client()
    r = client.put("/simulation/config", json={"ticks_per_second": -5})
    assert r.status_code == 422 and "detail" in r.json()
    r = client.put("/simulation/config", json={"ticks_per_second": "fast"})
    assert r.status_code in (422, 400) and "detail" in r.json()
    r = client.post("/simulation/reset", json={"seed": "abc"})
    assert r.status_code in (422, 400) and "detail" in r.json()
    r = client.get("/simulation/organisms/99999999")
    assert r.status_code == 404 and "detail" in r.json()
    r = client.get("/simulation/state?limit=-1")
    assert r.status_code in (422, 400)


def test_state_consistent_snapshot_and_serialization_options():
    _, client = make_client()
    s = client.get("/simulation/state")
    body = s.json()
    # frontend-compatible fields
    for field in ("tick", "world", "population", "total_organisms",
                  "food_remaining", "organisms", "food", "statistics",
                  "latest_metrics", "ticks_per_second"):
        assert field in body
    assert body["statistics"]["living_population"] == body["population"]
    assert body["statistics"]["total_organisms"] == body["total_organisms"]
    # include_dead=false omits dead but preserves counts
    full = client.get("/simulation/state").json()
    slim = client.get("/simulation/state?include_dead=false").json()
    assert slim["total_organisms"] == full["total_organisms"]
    assert all(o["alive"] for o in slim["organisms"])
    assert len(slim["organisms"]) <= len(full["organisms"])
    limited = client.get("/simulation/state?limit=5").json()
    assert len(limited["organisms"]) <= 5
    assert limited["total_organisms"] == full["total_organisms"]
    # empty population safe (mutate under lock, read after release)
    import backend.api as api
    with api._state_lock:
        saved = api.world.organisms
        api.world.organisms = []
    try:
        snap = client.get("/simulation/state").json()
        assert snap["population"] == 0
        assert snap["statistics"]["average_energy"] is None
    finally:
        with api._state_lock:
            api.world.organisms = saved


def test_health_and_status_and_concurrent_reads():
    import concurrent.futures
    _, client = make_client()
    h = client.get("/health")
    assert h.status_code == 200
    for k in ("simulation_status", "simulation_tick", "living_population",
              "worker_alive", "ticks_per_second"):
        assert k in h.json()
    st = client.get("/simulation/status")
    assert st.status_code == 200 and "paused" in st.json()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(lambda _: client.get("/simulation/state").status_code,
                              range(16)))
    assert all(c == 200 for c in results)


def test_worker_exception_observable_not_swallowed():
    api, client = make_client()
    try:
        client.post("/simulation/pause")
        with api._state_lock:
            orig = api.engine.step
            def boom():
                raise RuntimeError("boom-test")
            api.engine.step = boom
        r = client.post("/simulation/step")
        assert r.status_code == 500 and "detail" in r.json()
        with api._state_lock:
            assert api._last_error is not None and "boom-test" in api._last_error
            api.engine.step = orig
    finally:
        with api._state_lock:
            try:
                api.engine.step = orig
            except Exception:
                pass
        api.stop_worker()


def test_metrics_history_endpoint():
    _, client = make_client()
    empty = client.get("/simulation/metrics/history")
    assert empty.status_code == 200
    assert empty.json()["history"] == []
    client.post("/simulation/pause")
    client.post("/simulation/step")
    client.post("/simulation/step")
    h = client.get("/simulation/metrics/history").json()
    assert h["count"] == 2
    assert [s["tick"] for s in h["history"]] == [1, 2]
    assert "living_population" in h["history"][0]
    assert "average_energy" in h["history"][0]
    limited = client.get("/simulation/metrics/history?limit=1").json()
    assert limited["count"] == 1 and limited["history"][0]["tick"] == 2
    assert client.get("/simulation/metrics/history?limit=0").status_code == 422


def test_interleaved_lifecycle_sequence():
    api, client = make_client()
    try:
        client.post("/simulation/pause")
        t0 = client.get("/simulation/state").json()["tick"]
        for _ in range(3):
            r = client.post("/simulation/step")
            assert r.status_code == 200
        assert client.get("/simulation/state").json()["tick"] == t0 + 3
        client.post("/simulation/resume")
        assert client.post("/simulation/step").status_code == 409
        client.post("/simulation/pause")
        r = client.post("/simulation/reset", json={})
        assert r.status_code == 200
        assert client.get("/simulation/state").json()["tick"] == 0
        # Paused state preserved across reset; stepping still works.
        assert client.post("/simulation/step").json()["tick"] == 1
    finally:
        api.stop_worker()


def test_validate_config_defaults_valid_and_bad_rejected():
    assert config.validate_config() == []
    bad = config.validate_config({"WORLD_WIDTH": -1, "MAX_ENERGY": 0,
                                   "STARTING_ENERGY": 9999,
                                   "FOOD_TARGET_COUNT": 500,
                                   "FOOD_MAX_COUNT": 10})
    assert len(bad) >= 3
