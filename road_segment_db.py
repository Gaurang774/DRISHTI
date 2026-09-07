"""
DRISHTI • ROAD SEGMENT STATE DATABASE
Implements the 5-State Road Belief Model from the DRISHTI research framework.

The key insight: absence of detection != absence of defect.
A road that was never observed cannot produce evidence of any kind.

5 States:
  CONFIRMED_DEFECT   - Multiple route-diverse, high-quality detections
  PROBABLE_DEFECT    - Some evidence but not yet corroborated
  UNCERTAIN          - Conflicting or insufficient evidence
  PROBABLY_CLEAR     - Multiple good passes, no detections
  UNOBSERVED         - No valid sensing opportunity has occurred yet
"""

from datetime import datetime, timezone

# --- Delhi NCR Road Segment Registry ---
# Each segment represents a monitored arterial corridor.
# routes: which DTC routes pass this segment
# expected_daily_passes: approximate bus passes per day based on headway

ROAD_SEGMENT_REGISTRY = {
    "SEG-001": {
        "name": "Connaught Place Radial 3",
        "corridor": "Connaught Place → Patel Chowk",
        "routes": ["Route 402", "Route 119", "Route 534"],
        "expected_daily_passes": 42,
        "lat": 28.6315, "lng": 77.2167
    },
    "SEG-002": {
        "name": "Vikas Marg (ITO to Laxmi Nagar)",
        "corridor": "ITO Junction → Laxmi Nagar Metro",
        "routes": ["Route 221", "Route 534"],
        "expected_daily_passes": 28,
        "lat": 28.6280, "lng": 77.2750
    },
    "SEG-003": {
        "name": "AIIMS Junction - Ring Road",
        "corridor": "AIIMS Flyover → Safdarjung",
        "routes": ["Route 880"],
        "expected_daily_passes": 12,
        "lat": 28.5680, "lng": 77.2090
    },
    "SEG-004": {
        "name": "Naraina Industrial Area Road",
        "corridor": "Naraina Flyover → Ring Road",
        "routes": ["Route 781"],
        "expected_daily_passes": 8,
        "lat": 28.6194, "lng": 77.1295
    },
    "SEG-005": {
        "name": "Outer Ring Road (Dhaula Kuan)",
        "corridor": "Dhaula Kuan → Vasant Vihar",
        "routes": [],  # No route currently covers this
        "expected_daily_passes": 0,
        "lat": 28.5952, "lng": 77.1673
    },
    "SEG-006": {
        "name": "Janpath (Connaught Place)",
        "corridor": "Connaught Place → India Gate",
        "routes": ["Route 402", "Route 119", "Route 221", "Route 534"],
        "expected_daily_passes": 55,
        "lat": 28.6139, "lng": 77.2179
    },
    "SEG-007": {
        "name": "Shivaji Marg (Patel Nagar)",
        "corridor": "Patel Nagar → Karol Bagh",
        "routes": ["Route 119"],
        "expected_daily_passes": 14,
        "lat": 28.6394, "lng": 77.1635
    },
}


class RoadSegmentDB:
    """
    Maintains the 5-state belief model for each road segment.
    Updated every time the Fusion Engine processes a detection event.
    """

    # State transition thresholds
    CONFIRMED_DEFECT_THRESHOLD = 3.0    # N_eff >= 3 from diverse routes
    PROBABLE_DEFECT_THRESHOLD = 1.5     # N_eff >= 1.5 (at least some corroboration)
    PROBABLY_CLEAR_THRESHOLD = 5        # 5+ high-quality passes with no detections
    
    def __init__(self):
        self.segments = {}
        self._initialize_segments()

    def _initialize_segments(self):
        """Initialize all registered segments in UNOBSERVED state."""
        for seg_id, meta in ROAD_SEGMENT_REGISTRY.items():
            self.segments[seg_id] = {
                "segment_id": seg_id,
                "name": meta["name"],
                "corridor": meta["corridor"],
                "lat": meta["lat"],
                "lng": meta["lng"],
                "routes": meta["routes"],
                "expected_daily_passes": meta["expected_daily_passes"],
                
                # Coverage tracking
                "actual_passes": 0,
                "usable_observations": 0,
                "positive_detections": [],   # List of fused events that found a defect
                "null_observations": 0,      # High-quality passes with NO detection
                
                # Route diversity tracking
                "routes_that_detected": set(),
                "routes_that_passed_clean": set(),
                
                # Temporal history
                "detection_history": [],     # (timestamp, n_eff, route)
                
                # Current state
                "state": "UNOBSERVED",
                "state_confidence": 0.0,
                "dominant_hazard": None,
                "last_updated": None,
            }

    def register_discovered_segment(self, segment_id, lat, lng, route_id):
        """Add a segment first seen by a bus rather than seeded from the registry.

        expected_daily_passes is 0 because nobody has surveyed the headway
        here: coverage_pct stays 0 and the segment reads UNOBSERVED until real
        passes accumulate. That is the honest answer - inventing an expected
        count would fabricate the denominator the coverage claim rests on.
        """
        self.segments[segment_id] = {
            "segment_id": segment_id,
            "name": f"Unsurveyed segment {segment_id}",
            "corridor": "Discovered by fleet",
            "lat": lat, "lng": lng,
            "routes": [route_id] if route_id else [],
            "expected_daily_passes": 0,
            "discovered_by_fleet": True,
            "actual_passes": 0,
            "usable_observations": 0,
            "positive_detections": [],
            "null_observations": 0,
            "routes_that_detected": set(),
            "routes_that_passed_clean": set(),
            "detection_history": [],
            "state": "UNOBSERVED",
            "state_confidence": 0.0,
            "dominant_hazard": None,
            "last_updated": None,
        }
        return self.segments[segment_id]

    def record_bus_pass(self, segment_id, route_id, has_detection, fused_event=None):
        """
        Record one bus pass on a road segment.
        
        has_detection: True if the bus detected a hazard
        fused_event: The full FusionEngine output dict (if has_detection=True)
        """
        if segment_id not in self.segments:
            # A fleet-sourced system discovers roads; the registry is a seed,
            # not the whole city. Returning None here silently threw the pass
            # away - the detection was stored but never reached the belief
            # model, so a real pothole on any unlisted road just vanished.
            if fused_event is None or fused_event.get("lat") is None:
                return None          # no position: nothing we could map it to
            self.register_discovered_segment(
                segment_id, fused_event["lat"], fused_event["lng"], route_id)
        
        seg = self.segments[segment_id]
        seg["actual_passes"] += 1
        seg["last_updated"] = datetime.now(timezone.utc).isoformat()

        if has_detection and fused_event:
            n_eff = fused_event.get("effective_passes_neff", 1.0)
            seg["usable_observations"] += 1
            seg["positive_detections"].append(fused_event)
            seg["routes_that_detected"].add(route_id)
            seg["detection_history"].append({
                "timestamp": fused_event.get("timestamp"),
                "n_eff": n_eff,
                "route": route_id,
                "hazard": fused_event.get("hazard_type"),
                "priority": fused_event.get("priority_level")
            })
        else:
            # A high-quality pass with NO detection is negative evidence
            seg["usable_observations"] += 1
            seg["null_observations"] += 1
            seg["routes_that_passed_clean"].add(route_id)

        # Recalculate state after every update
        self._recalculate_state(segment_id)
        return self.segments[segment_id]

    def _recalculate_state(self, segment_id):
        """
        Core state machine. Determines the 5-state belief for a road segment.
        """
        seg = self.segments[segment_id]
        
        num_detections = len(seg["positive_detections"])
        null_obs = seg["null_observations"]
        route_diversity = len(seg["routes_that_detected"])
        
        # Total N_eff across all detections (sum of individual n_eff values)
        total_n_eff = sum(
            d.get("effective_passes_neff", 1.0) for d in seg["positive_detections"]
        )

        # If no bus has ever passed this segment
        if seg["actual_passes"] == 0:
            seg["state"] = "UNOBSERVED"
            seg["state_confidence"] = 0.0
            return

        # If buses passed but no valid observations were possible
        if seg["usable_observations"] == 0:
            seg["state"] = "UNOBSERVED"
            seg["state_confidence"] = 0.0
            return

        # --- Decision Logic ---

        if num_detections == 0:
            # No hazard detected at all
            if null_obs >= self.PROBABLY_CLEAR_THRESHOLD:
                seg["state"] = "PROBABLY_CLEAR"
                seg["state_confidence"] = min(0.95, 0.5 + null_obs * 0.08)
            else:
                seg["state"] = "UNCERTAIN"
                seg["state_confidence"] = 0.4
        else:
            # Some detections exist — check against null observations
            if null_obs > num_detections * 2:
                # Many more clean passes than detections → probably a false positive
                seg["state"] = "UNCERTAIN"
                seg["state_confidence"] = 0.35
            elif total_n_eff >= self.CONFIRMED_DEFECT_THRESHOLD or route_diversity >= 2:
                seg["state"] = "CONFIRMED_DEFECT"
                seg["state_confidence"] = min(0.97, 0.70 + (total_n_eff - 1) * 0.05)
            elif total_n_eff >= self.PROBABLE_DEFECT_THRESHOLD or num_detections >= 1:
                seg["state"] = "PROBABLE_DEFECT"
                seg["state_confidence"] = min(0.80, 0.50 + total_n_eff * 0.10)
            else:
                seg["state"] = "UNCERTAIN"
                seg["state_confidence"] = 0.45

        # Set dominant hazard from most recent detection
        if seg["positive_detections"]:
            seg["dominant_hazard"] = seg["positive_detections"][-1].get("hazard_type")

    def get_segment_state(self, segment_id):
        """Get the full state of a single segment."""
        if segment_id not in self.segments:
            return None
        seg = dict(self.segments[segment_id])
        # Convert sets to lists for JSON serialization
        seg["routes_that_detected"] = list(seg["routes_that_detected"])
        seg["routes_that_passed_clean"] = list(seg["routes_that_passed_clean"])
        # Strip full detection objects from the summary to keep it lean
        seg["detection_count"] = len(seg.pop("positive_detections"))
        seg["detection_history"] = seg["detection_history"][-5:]  # Last 5 only
        return seg

    def get_all_states(self):
        """Return summary of all segment states — used by the API."""
        summary = []
        for seg_id in self.segments:
            state = self.get_segment_state(seg_id)
            if state:
                summary.append(state)
        return summary

    def get_coverage_report(self):
        """Returns a city-wide coverage table — the key insight from md.md."""
        report = []
        for seg_id, seg in self.segments.items():
            expected = seg.get("expected_daily_passes", 0)
            actual = seg["actual_passes"]
            coverage_pct = round((actual / expected * 100) if expected > 0 else 0, 1)
            report.append({
                "segment_id": seg_id,
                "name": seg["name"],
                "routes": seg["routes"],
                "expected_passes": expected,
                "actual_passes": actual,
                "coverage_pct": coverage_pct,
                "usable_observations": seg["usable_observations"],
                "defect_detections": len(seg["positive_detections"]) if isinstance(seg.get("positive_detections"), list) else seg.get("detection_count", 0),
                "state": seg["state"],
            })
        return report
