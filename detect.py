"""
DRISHTI perception — vehicle density + pedestrian presence from bus video.

Covers three PS 26124 requirements with no training: vehicle detection,
classification and counting, plus pedestrian presence. COCO-pretrained YOLO
already knows car/bus/truck/motorcycle/bicycle/person.

Split by responsibility: the scoring functions below are pure (no video, no
GPU, no network) so they can be unit-checked on a laptop with `--self-check`.
Video I/O lives in `analyse_video` only.

Usage:
    python detect.py --self-check
    python detect.py --source path/to/road.mp4
    python detect.py --source path/to/road.mp4 --events events.jsonl
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path


# ---------------------------------------------------------------------------
# Config. Per c1.txt: these are knobs, not magic numbers buried in the code.
# ---------------------------------------------------------------------------

class Config:
    MODEL = "yolov8n.pt"        # n-size: fits 6GB VRAM and matches Jetson target
    IMG_SIZE = 640
    CONF_THRESHOLD = 0.35       # below this a detection is not reported at all
    IOU_THRESHOLD = 0.45        # NMS overlap

    # An edge device does not run inference on every frame. Stride models that.
    FRAME_STRIDE = 5

    # Passenger Car Unit weights (IRC:106 style). A bus occupies far more road
    # than a scooter, so a raw object count is a poor density measure.
    PCU = {
        "bicycle": 0.5,
        "motorcycle": 0.5,
        "car": 1.0,
        "bus": 3.0,
        "truck": 3.0,
    }

    # Congestion bands in PCU per analysed frame. Tunable per corridor; these
    # are a starting point, not a calibrated result. Say so out loud.
    CONGESTION_BANDS = [
        (0.0, "FREE_FLOW"),
        (8.0, "MODERATE"),
        (18.0, "HEAVY"),
        (30.0, "JAMMED"),
    ]

    # A pedestrian near a bus corridor is the safety signal the PS asks about.
    PEDESTRIAN_ALERT_COUNT = 3


VEHICLE_CLASSES = frozenset(Config.PCU)
PERSON_CLASS = "person"


# ---------------------------------------------------------------------------
# Pure scoring logic — unit-checkable without a video file or a GPU.
# ---------------------------------------------------------------------------

def count_by_class(labels):
    """Tally detection labels. Returns a plain dict, sorted for stable output."""
    counts = {}
    for name in labels:
        counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items()))


def pcu_density(counts):
    """Weighted vehicle density in Passenger Car Units.

    Non-vehicle classes (person, traffic light, ...) are ignored here on
    purpose: pedestrians are a safety signal, not a congestion signal.
    """
    return sum(Config.PCU.get(name, 0.0) * n for name, n in counts.items())


def congestion_band(pcu):
    """Map a PCU density onto a named band. Highest matching threshold wins."""
    if pcu < 0:
        raise ValueError(f"pcu must be non-negative, got {pcu}")
    band = Config.CONGESTION_BANDS[0][1]
    for threshold, name in Config.CONGESTION_BANDS:
        if pcu >= threshold:
            band = name
    return band


@dataclass
class FrameObservation:
    """One analysed frame. This is the unit we would send from the bus."""
    frame_index: int
    timestamp_s: float
    counts: dict = field(default_factory=dict)
    pcu: float = 0.0
    band: str = "FREE_FLOW"
    pedestrians: int = 0
    pedestrian_alert: bool = False

    @classmethod
    def from_labels(cls, frame_index, timestamp_s, labels):
        counts = count_by_class(labels)
        pcu = pcu_density(counts)
        pedestrians = counts.get(PERSON_CLASS, 0)
        return cls(
            frame_index=frame_index,
            timestamp_s=round(timestamp_s, 3),
            counts=counts,
            pcu=round(pcu, 2),
            band=congestion_band(pcu),
            pedestrians=pedestrians,
            pedestrian_alert=pedestrians >= Config.PEDESTRIAN_ALERT_COUNT,
        )

    def to_event(self):
        """Compact uplink payload — this is what costs bandwidth, not video."""
        return json.dumps(asdict(self), separators=(",", ":"))


def summarise(observations):
    """Aggregate per-frame observations into a segment-level summary."""
    if not observations:
        return {"frames": 0}
    pcus = [o.pcu for o in observations]
    return {
        "frames": len(observations),
        "pcu_mean": round(statistics.mean(pcus), 2),
        "pcu_peak": round(max(pcus), 2),
        "band_mean": congestion_band(statistics.mean(pcus)),
        "band_peak": congestion_band(max(pcus)),
        "pedestrian_frames": sum(1 for o in observations if o.pedestrians),
        "pedestrian_alerts": sum(1 for o in observations if o.pedestrian_alert),
        "vehicle_total": sum(
            n for o in observations for k, n in o.counts.items()
            if k in VEHICLE_CLASSES
        ),
    }


# ---------------------------------------------------------------------------
# Video I/O — the only part that needs the model, a GPU or a file.
# ---------------------------------------------------------------------------

def analyse_video(source, events_path=None, limit=None):
    """Run detection over a video, returning (observations, bandwidth_stats)."""
    src = Path(source)
    if not src.exists():
        raise FileNotFoundError(f"video not found: {src}")

    from ultralytics import YOLO  # imported late: keeps --self-check dependency-free

    model = YOLO(Config.MODEL)
    names = model.names

    observations = []
    raw_bytes = 0
    event_bytes = 0
    sink = open(events_path, "w", encoding="utf-8") if events_path else None

    try:
        stream = model.predict(
            source=str(src),
            imgsz=Config.IMG_SIZE,
            conf=Config.CONF_THRESHOLD,
            iou=Config.IOU_THRESHOLD,
            vid_stride=Config.FRAME_STRIDE,
            stream=True,
            verbose=False,
        )
        for i, result in enumerate(stream):
            if limit is not None and i >= limit:
                break
            labels = [names[int(c)] for c in result.boxes.cls]
            fps = 30.0  # only used to timestamp; replaced by GPS clock on a real bus
            obs = FrameObservation.from_labels(i, i * Config.FRAME_STRIDE / fps, labels)
            observations.append(obs)

            event = obs.to_event()
            event_bytes += len(event.encode("utf-8"))
            if result.orig_shape:
                h, w = result.orig_shape
                raw_bytes += h * w * 3  # uncompressed frame, the thing we do NOT send
            if sink:
                sink.write(event + "\n")
    finally:
        if sink:
            sink.close()

    bandwidth = {
        "analysed_frames": len(observations),
        "raw_frame_bytes": raw_bytes,
        "event_bytes": event_bytes,
        "mean_event_bytes": round(event_bytes / len(observations), 1) if observations else 0,
        "reduction_pct": round(100 * (1 - event_bytes / raw_bytes), 4) if raw_bytes else 0.0,
    }
    return observations, bandwidth


# ---------------------------------------------------------------------------
# Self-check. Runs without ultralytics, a video, or a GPU.
# ---------------------------------------------------------------------------

def self_check():
    assert count_by_class([]) == {}
    assert count_by_class(["car", "car", "bus"]) == {"bus": 1, "car": 2}

    # PCU weighting: a bus must not count the same as a car.
    assert pcu_density({"car": 1}) == 1.0
    assert pcu_density({"bus": 1}) == 3.0
    assert pcu_density({"motorcycle": 2}) == 1.0
    # Pedestrians are a safety signal, never a congestion signal.
    assert pcu_density({"person": 10}) == 0.0
    # Unknown COCO classes must not silently inflate density.
    assert pcu_density({"traffic light": 5}) == 0.0

    assert congestion_band(0.0) == "FREE_FLOW"
    assert congestion_band(7.9) == "FREE_FLOW"
    assert congestion_band(8.0) == "MODERATE"
    assert congestion_band(25.0) == "HEAVY"
    assert congestion_band(999.0) == "JAMMED"
    try:
        congestion_band(-1.0)
    except ValueError:
        pass
    else:
        raise AssertionError("negative PCU must be rejected")

    obs = FrameObservation.from_labels(0, 0.0, ["car", "car", "bus", "person"])
    assert obs.pcu == 5.0, obs.pcu
    assert obs.band == "FREE_FLOW"
    assert obs.pedestrians == 1
    assert obs.pedestrian_alert is False

    alert = FrameObservation.from_labels(1, 1.0, ["person"] * 4)
    assert alert.pedestrian_alert is True
    assert alert.pcu == 0.0

    # The bandwidth claim rests on this: an event must be ~1KB, not a frame.
    event = obs.to_event()
    assert len(event.encode()) < 1024, f"event too large: {len(event)}B"
    assert json.loads(event)["pcu"] == 5.0

    assert summarise([]) == {"frames": 0}
    s = summarise([obs, alert])
    assert s["frames"] == 2
    assert s["vehicle_total"] == 3          # 2 cars + 1 bus; the 5 people excluded
    assert s["pedestrian_alerts"] == 1
    assert s["pcu_peak"] == 5.0

    print("self-check: all assertions passed")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--source", help="video file to analyse")
    ap.add_argument("--events", help="write one JSON event per line to this file")
    ap.add_argument("--limit", type=int, help="stop after N analysed frames")
    ap.add_argument("--self-check", action="store_true", help="run assertions and exit")
    args = ap.parse_args(argv)

    if args.self_check:
        self_check()
        return 0
    if not args.source:
        ap.error("--source is required (or use --self-check)")

    observations, bandwidth = analyse_video(args.source, args.events, args.limit)
    print(json.dumps({"summary": summarise(observations), "bandwidth": bandwidth}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
