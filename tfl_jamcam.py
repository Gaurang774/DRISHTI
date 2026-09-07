"""
DRISHTI — TfL JamCam Live Feed Connector
Fetches live traffic camera images from Transport for London (890 cameras),
runs YOLOv8 detection on each frame, and posts results to /api/edge/telemetry.

Why TfL JamCam for a Delhi-focused system?
  - The COCO vehicle classes (car/bus/truck/motorcycle/person) are universal.
  - Vehicle density, congestion bands, and pedestrian alerts are geometry-agnostic.
  - It proves the pipeline works on LIVE camera data, not simulated data.
  - In production, swap the source URL for DTC/BMTC camera feeds.

Usage:
    python tfl_jamcam.py --list              # list all 890 cameras
    python tfl_jamcam.py --fetch 10          # fetch + detect from 10 cameras
    python tfl_jamcam.py --stream            # continuous feed (every 90s refresh)
    python tfl_jamcam.py --self-check        # verify API + backend connectivity
"""

import argparse
import io
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

API_URL     = "http://localhost:8080/api/edge/telemetry"
TFL_BASE    = "https://api.tfl.gov.uk"
HEADERS     = {"User-Agent": "DRISHTI-Urban-Intelligence/1.0",
               "Accept":     "application/json"}
REFRESH_S   = 90          # TfL images update every ~60-90 seconds
CONF_THRESH = 0.35        # match detect.py Config
FRAME_LIMIT = 1           # 1 frame per camera image (it's a JPEG, not video)


# ---------------------------------------------------------------------------
# TfL API helpers
# ---------------------------------------------------------------------------

def _get(url, timeout=10):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def fetch_cameras():
    """Return list of all available JamCam dicts with id, lat, lon, imageUrl."""
    data = _get(f"{TFL_BASE}/Place/Type/JamCam")
    cameras = []
    for cam in data:
        props = {p["key"]: p["value"] for p in cam.get("additionalProperties", [])}
        if props.get("available") == "true" and props.get("imageUrl"):
            cameras.append({
                "id":       cam["id"],
                "lat":      cam["lat"],
                "lon":      cam["lon"],
                "imageUrl": props["imageUrl"],
                "videoUrl": props.get("videoUrl"),
                "view":     props.get("view", "unknown"),
            })
    return cameras


def fetch_image_bytes(url, timeout=8):
    """Download a JPEG from S3 and return raw bytes."""
    req = urllib.request.Request(
        url, headers={"User-Agent": "DRISHTI-Urban-Intelligence/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


# ---------------------------------------------------------------------------
# YOLO detection on a JPEG image (not a video file)
# ---------------------------------------------------------------------------

def detect_frame(image_bytes):
    """
    Run YOLOv8n on a single JPEG image (from JamCam).
    Returns (labels, orig_shape) where labels is a list of COCO class names.
    """
    from ultralytics import YOLO
    import numpy as np

    # Lazy-load model once
    if not hasattr(detect_frame, "_model"):
        detect_frame._model = YOLO("yolov8n.pt")
        detect_frame._names = detect_frame._model.names

    model = detect_frame._model
    names = detect_frame._names

    # Decode JPEG bytes to numpy array
    try:
        import cv2
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            return [], (0, 0)
    except ImportError:
        from PIL import Image
        frame = Image.open(io.BytesIO(image_bytes))

    results = model.predict(
        source=frame,
        imgsz=640,
        conf=CONF_THRESH,
        iou=0.45,
        verbose=False,
    )
    if not results:
        return [], getattr(frame, "shape", (0, 0))[:2]

    result = results[0]
    labels = [names[int(c)] for c in result.boxes.cls]
    shape = result.orig_shape  # (h, w)
    return labels, shape


# ---------------------------------------------------------------------------
# Scoring (mirrors detect.py logic exactly)
# ---------------------------------------------------------------------------

PCU = {"bicycle": 0.5, "motorcycle": 0.5, "car": 1.0, "bus": 3.0, "truck": 3.0}
CONGESTION_BANDS = [(0.0, "FREE_FLOW"), (8.0, "MODERATE"),
                    (18.0, "HEAVY"), (30.0, "JAMMED")]
VEHICLE_CLASSES  = frozenset(PCU)
PEDESTRIAN_ALERT_COUNT = 3


def score_labels(labels):
    counts = {}
    for name in labels:
        counts[name] = counts.get(name, 0) + 1
    pcu = sum(PCU.get(n, 0.0) * c for n, c in counts.items())
    band = CONGESTION_BANDS[0][1]
    for threshold, name in CONGESTION_BANDS:
        if pcu >= threshold:
            band = name
    pedestrians = counts.get("person", 0)
    vehicles = sum(c for n, c in counts.items() if n in VEHICLE_CLASSES)
    return {
        "counts":           counts,
        "pcu":              round(pcu, 2),
        "band":             band,
        "pedestrians":      pedestrians,
        "pedestrian_alert": pedestrians >= PEDESTRIAN_ALERT_COUNT,
        "vehicle_total":    vehicles,
    }


# ---------------------------------------------------------------------------
# Telemetry POST
# ---------------------------------------------------------------------------

def post_telemetry(cam, scores):
    """Build and POST an edge telemetry event from a JamCam observation."""
    # Map congestion band to a confidence score for the fusion engine
    band_conf = {"FREE_FLOW": 0.0, "MODERATE": 0.45,
                 "HEAVY": 0.75, "JAMMED": 0.92}
    conf = band_conf.get(scores["band"], 0.0)

    if scores["vehicle_total"] == 0 and not scores["pedestrian_alert"]:
        hazard = None  # clean pass — no defect detected
    elif scores["band"] in ("HEAVY", "JAMMED"):
        hazard = "Traffic Congestion"
    elif scores["pedestrian_alert"]:
        hazard = "Pedestrian Hazard"
    else:
        hazard = None

    payload = {
        "bus_id":    f"JamCam_{cam['id'].split('_')[-1]}",
        "route_id":  f"TfL-JamCam-{cam['view']}",
        "segment_id": cam["id"],
        "lat":        cam["lat"],
        "lng":        cam["lon"],
        "traffic_context": {
            "pcu":              scores["pcu"],
            "band":             scores["band"],
            "pedestrians":      scores["pedestrians"],
            "pedestrian_alert": scores["pedestrian_alert"],
            "vehicle_counts":   scores["counts"],
        },
    }
    if hazard:
        payload["hazard_type"] = hazard
        payload["confidence"]  = conf

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL, data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

def cmd_list(args):
    print("[DRISHTI] Fetching JamCam camera list from TfL API...")
    cameras = fetch_cameras()
    print(f"  {len(cameras)} available cameras\n")
    for cam in cameras[:20]:
        print(f"  {cam['id']:30s}  lat={cam['lat']:.5f}  lon={cam['lon']:.6f}  view={cam['view']}")
    if len(cameras) > 20:
        print(f"  ... and {len(cameras)-20} more")


def cmd_fetch(args):
    n = args.fetch
    print(f"\n[DRISHTI] Fetching + detecting from {n} TfL JamCam cameras...\n")

    cameras = fetch_cameras()
    from random import sample, seed
    seed(42)  # reproducible selection for demo
    selected = sample(cameras, min(n, len(cameras)))

    results = []
    for i, cam in enumerate(selected):
        print(f"  [{i+1}/{n}] {cam['id']}  ({cam['view']})")
        try:
            img = fetch_image_bytes(cam["imageUrl"])
            labels, shape = detect_frame(img)
            scores = score_labels(labels)
            status = post_telemetry(cam, scores)

            line = (f"      Band={scores['band']:<10} PCU={scores['pcu']:5.1f}  "
                    f"Vehicles={scores['vehicle_total']}  "
                    f"Pedestrians={scores['pedestrians']}  "
                    f"→ API: {status.get('message', status.get('error','?'))}")
            print(line)
            results.append({"cam": cam["id"], "scores": scores, "api": status})

        except Exception as e:
            print(f"      ERROR: {e}")

    # Summary
    print(f"\n{'='*60}")
    print(f"  Processed {len(results)} cameras")
    if results:
        valid = [r for r in results if "scores" in r]
        avg_pcu = sum(r["scores"]["pcu"] for r in valid) / max(len(valid), 1)
        alerts  = sum(1 for r in valid if r["scores"]["pedestrian_alert"])
        heavy   = sum(1 for r in valid if r["scores"]["band"] in ("HEAVY","JAMMED"))
        print(f"  Average PCU: {avg_pcu:.1f}")
        print(f"  Heavy/Jammed corridors: {heavy}/{len(valid)}")
        print(f"  Pedestrian alerts: {alerts}")

    # Save results
    out = Path("jamcam_results.json")
    out.write_text(json.dumps(results, indent=2))
    print(f"  Results saved: {out}")


def cmd_stream(args):
    print(f"\n[DRISHTI] Starting continuous JamCam stream (refresh every {REFRESH_S}s)...")
    print("  Press Ctrl+C to stop\n")
    cameras = fetch_cameras()
    iteration = 0
    try:
        while True:
            iteration += 1
            ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
            print(f"\n[{ts}] Round {iteration} — sampling 5 cameras")
            from random import sample
            selected = sample(cameras, min(5, len(cameras)))
            for cam in selected:
                try:
                    img    = fetch_image_bytes(cam["imageUrl"])
                    labels, _ = detect_frame(img)
                    scores = score_labels(labels)
                    post_telemetry(cam, scores)
                    print(f"  {cam['id']:<30} {scores['band']:<12} PCU={scores['pcu']}")
                except Exception as e:
                    print(f"  {cam['id']:<30} ERROR: {e}")
            print(f"  Next refresh in {REFRESH_S}s...")
            time.sleep(REFRESH_S)
    except KeyboardInterrupt:
        print("\n[DRISHTI] Stream stopped.")


def cmd_selfcheck(args):
    print("\n[DRISHTI] Self-check: TfL JamCam connector\n")

    # 1. TfL API
    try:
        cameras = fetch_cameras()
        print(f"  OK | TfL API reachable — {len(cameras)} cameras available")
    except Exception as e:
        print(f"  FAIL | TfL API: {e}")
        return

    # 2. Image download
    cam = cameras[0]
    try:
        img = fetch_image_bytes(cam["imageUrl"])
        print(f"  OK | Image download ({len(img)//1024}KB from {cam['id']})")
    except Exception as e:
        print(f"  FAIL | Image download: {e}")
        return

    # 3. YOLO detection
    try:
        labels, shape = detect_frame(img)
        print(f"  OK | YOLO detection — {len(labels)} objects in {shape}")
        if labels:
            from collections import Counter
            print(f"       Detected: {dict(Counter(labels))}")
    except Exception as e:
        print(f"  FAIL | YOLO: {e}")
        return

    # 4. Backend
    try:
        urllib.request.urlopen("http://localhost:8080/api/health", timeout=2)
        print("  OK | Backend at http://localhost:8080")
    except:
        print("  DOWN | Backend not running — start: python drishti_api.py")

    print("\n  Ready to run: python tfl_jamcam.py --fetch 10")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--list",       action="store_true",  help="List all cameras")
    g.add_argument("--fetch",      type=int, metavar="N", help="Fetch+detect from N cameras")
    g.add_argument("--stream",     action="store_true",  help="Continuous feed")
    g.add_argument("--self-check", action="store_true",  dest="selfcheck")
    args = ap.parse_args()

    if args.list:       cmd_list(args)
    elif args.fetch:    cmd_fetch(args)
    elif args.stream:   cmd_stream(args)
    elif args.selfcheck: cmd_selfcheck(args)


if __name__ == "__main__":
    main()
