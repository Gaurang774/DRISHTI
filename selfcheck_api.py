"""End-to-end check for the DRISHTI API gateway.

Starts the real server on a spare port and asserts the things that were
actually broken, so a regression fails here instead of in front of a judge:

  1. GET /../../<file>.css must NOT serve a file outside the static roots.
  2. Malformed telemetry must return 400, not die with an empty reply.
  3. /api/ticker must exist (the dashboard polls it).
  4. A telemetry frame with sensor streams must run the 12 AI layers;
     one without them must say so rather than invent an answer.

Run:  python3 selfcheck_api.py
"""
import json
import os
import socket
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import drishti_api

HOST = "127.0.0.1"


def free_port():
    with socket.socket() as s:
        s.bind((HOST, 0))
        return s.getsockname()[1]


def get(url):
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def post(url, obj):
    req = urllib.request.Request(
        url, data=json.dumps(obj).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def main():
    port = free_port()
    srv = ThreadingHTTPServer((HOST, port), drishti_api.DrishtiAPIHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://{HOST}:{port}"
    checks = 0

    try:
        # 1. directory traversal ------------------------------------------
        # Plant a file one level above the repo; the server must not hand it
        # over. Before the fix this came back with a 200.
        bait = os.path.join(os.path.dirname(drishti_api._BASE_DIR),
                            "drishti_selfcheck_bait.css")
        with open(bait, "w") as f:
            f.write("SECRET")
        try:
            for attack in ("/../drishti_selfcheck_bait.css",
                           "/%2e%2e/drishti_selfcheck_bait.css",
                           "/prototype-simple/../../drishti_selfcheck_bait.css"):
                status, body = get(base + attack)
                assert b"SECRET" not in body, f"TRAVERSAL LEAK via {attack}"
                assert status == 404, f"{attack} -> {status}, expected 404"
                checks += 1
        finally:
            os.remove(bait)

        # 2. input validation at the trust boundary ------------------------
        bad = {"bus_id": "DTC-402", "hazard_type": "Pothole",
               "confidence": "banana", "lat": 28.6, "lng": 77.2}
        status, body = post(base + "/api/edge/telemetry", bad)
        assert status == 400, f"confidence='banana' -> {status}, expected 400"
        assert "details" in body, body
        checks += 1

        for field, value in (("lat", 999), ("lng", -400), ("confidence", 1.7),
                             ("depth_mm", -5), ("bus_id", "")):
            payload = {"bus_id": "DTC-402", "hazard_type": "Pothole",
                       "confidence": 0.9, "lat": 28.6, "lng": 77.2}
            payload[field] = value
            status, _ = post(base + "/api/edge/telemetry", payload)
            assert status == 400, f"{field}={value!r} -> {status}, expected 400"
            checks += 1

        # 3. every endpoint the dashboard polls must answer ----------------
        for ep in ("/api/health", "/api/detections", "/api/ticker",
                   "/api/segments/state", "/api/segments/coverage",
                   "/api/equinox/workorders"):
            status, _ = get(base + ep)
            assert status == 200, f"{ep} -> {status}"
            checks += 1

        # 4. the 12-layer stack is reachable, and honest when it is not ----
        flat = {"bus_id": "DTC-402", "hazard_type": "Pothole", "confidence": 0.91,
                "lat": 28.6315, "lng": 77.2167, "depth_mm": 70,
                "segment_id": "DEL-RING-01"}
        status, body = post(base + "/api/edge/telemetry", flat)
        assert status == 201, status
        assert body["urban_ai"]["status"] == "NOT_RUN", body["urban_ai"]
        checks += 1

        rich = dict(flat, gps={"speed_kmh": 18.0, "prev_speed_kmh": 44.0},
                    imu={"az_g": 1.9, "ax_g": 0.4, "vibration_rms_g": 0.55},
                    can={"brake_pressure_bar": 6.2, "rpm_drop": 900},
                    camera={"pothole_probability": 0.88,
                            "detections": {"two_wheeler": 6, "person": 3}})
        status, body = post(base + "/api/edge/telemetry", rich)
        assert status == 201, status
        ai = body["urban_ai"]
        assert ai.get("status") != "LAYER_ERROR", ai
        for layer in ("layer_4_road_health", "layer_8_explainable_ai",
                      "layer_9_pwd_work_order", "layer_12_route_delay"):
            assert layer in ai, f"missing {layer}"
            checks += 1
        assert ai["streams_present"] == ["gps", "imu", "can", "camera"], ai

        # 5. a road outside the seeded registry must still reach the belief
        #    model. It used to be dropped silently: stored in /api/detections
        #    but never counted as a pass anywhere.
        off = dict(flat, segment_id="SEG-UNLISTED-77", lat=28.7041, lng=77.1025)
        status, body = post(base + "/api/edge/telemetry", off)
        assert status == 201, status
        state = body["road_segment_state"]
        assert state, "pass on an unlisted road was dropped"
        assert state.get("discovered_by_fleet") is True, state
        checks += 1

        # ...and the coverage report must survive it (it used to KeyError).
        status, raw = get(base + "/api/segments/coverage")
        assert status == 200, status
        rows = json.loads(raw)["coverage"]
        assert any(r["segment_id"] == "SEG-UNLISTED-77" for r in rows), rows
        checks += 1

        print(f"selfcheck_api: {checks} checks passed")
    finally:
        srv.shutdown()


if __name__ == "__main__":
    main()
