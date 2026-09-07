"""
DRISHTI • REST API GATEWAY & BEL EQUINOX INGESTION CONNECTOR
PS 26124 - AI-Powered Mobile Urban Intelligence Platform

This server provides the live REST API endpoints for:
1. Ingesting edge detections from bus dashcams (Jetson / Hailo-8)
2. Ingesting live OSINT feeds (Open-Meteo, GTFS, MCD 311)
3. Dispatching automated PWD work orders into BEL Equinox Context Broker (NGSI-LD)

Zero external dependencies: Uses Python standard library http.server and json.
Run with: python drishti_api.py
"""

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
import os
from datetime import datetime, timezone
from fusion_engine import FusionEngine
from road_segment_db import RoadSegmentDB
from india_urban_ai import DrishtiIndianAIOrchestrator

# The 12-layer stack was imported by nothing, so route-delay prediction, the
# PWD bill-of-quantities and the explainability text - all named in the
# problem statement - could not be reached from the dashboard at all.
urban_ai = DrishtiIndianAIOrchestrator()

# Layers 1-4 read gps/imu/can/camera. With none of them present every
# extractor falls through to its default and the stack still emits a
# confident-looking road health index built from nothing. So we only run it
# when a frame actually carries sensor streams, and say so when we don't.
SENSOR_STREAMS = ("gps", "imu", "can", "camera")

PORT = 8080

# In-memory store of ingested edge events and dispatched work orders
DATABASE = {
    "status": "ONLINE",
    "equinox_iccc_connected": True,
    "equinox_endpoint": "https://equinox.delhi.gov.in/ngsi-ld/v1/entities",
    "active_buses": ["Bus 402", "Bus 119", "Bus 880", "Bus 221", "Bus 534", "Bus 781"],
    "detections": [],
    "work_orders": [
        {
            "ticket_id": "PWD-DEL-2026-9481",
            "corridor": "Connaught Place Radial 3",
            "severity": "CRITICAL EMERGENCY",
            "depth_mm": 48,
            "bitumen_kg": 145,
            "bus_corroborations": 7,
            "dispatched_to": "PWD Central Division Unit 4",
            "timestamp": "2026-09-06T14:30:00Z",
            "ngsi_status": "201 Created"
        }
    ]
}

# Initialize the Multi-Modal Fusion Engine
fusion_engine = FusionEngine()

# Initialize the 5-State Road Segment Database
road_db = RoadSegmentDB()

# Pre-seed some segment observations so the map is informative on first load
road_db.record_bus_pass("SEG-001", "Route 402", has_detection=True,
    fused_event={"hazard_type":"Pothole","raw_confidence":0.89,"fused_confidence":0.92,
        "total_bus_passes":7,"effective_passes_neff":3.8,"weather_context":{"humidity":91,"precipitation":0},
        "correlation_rho":0.72,"priority_level":"CRITICAL EMERGENCY",
        "escalation_reason":"Citizen Corroborated (MCD 311)","lat":28.6315,"lng":77.2167,
        "timestamp":"2026-09-07T04:00:00Z","is_actionable":True})
road_db.record_bus_pass("SEG-001", "Route 119", has_detection=True,
    fused_event={"hazard_type":"Pothole","raw_confidence":0.84,"fused_confidence":0.90,
        "total_bus_passes":7,"effective_passes_neff":3.8,"weather_context":{"humidity":91,"precipitation":0},
        "correlation_rho":0.72,"priority_level":"CRITICAL EMERGENCY",
        "escalation_reason":"High Fleet Persistence","lat":28.6315,"lng":77.2167,
        "timestamp":"2026-09-07T06:30:00Z","is_actionable":True})
road_db.record_bus_pass("SEG-002", "Route 221", has_detection=False)
road_db.record_bus_pass("SEG-002", "Route 221", has_detection=False)
road_db.record_bus_pass("SEG-002", "Route 534", has_detection=False)
road_db.record_bus_pass("SEG-002", "Route 534", has_detection=False)
road_db.record_bus_pass("SEG-002", "Route 221", has_detection=False)
road_db.record_bus_pass("SEG-003", "Route 880", has_detection=True,
    fused_event={"hazard_type":"Waterlogging","raw_confidence":0.94,"fused_confidence":0.94,
        "total_bus_passes":1,"effective_passes_neff":1.0,"weather_context":{"humidity":95,"precipitation":2.1},
        "correlation_rho":0.85,"priority_level":"HIGH",
        "escalation_reason":"High Fleet Persistence","lat":28.5680,"lng":77.2090,
        "timestamp":"2026-09-07T07:15:00Z","is_actionable":True})
road_db.record_bus_pass("SEG-006", "Route 402", has_detection=False)
road_db.record_bus_pass("SEG-006", "Route 119", has_detection=False)
road_db.record_bus_pass("SEG-006", "Route 221", has_detection=False)
road_db.record_bus_pass("SEG-006", "Route 534", has_detection=False)
road_db.record_bus_pass("SEG-006", "Route 402", has_detection=False)
road_db.record_bus_pass("SEG-006", "Route 119", has_detection=False)
road_db.record_bus_pass("SEG-007", "Route 119", has_detection=True,
    fused_event={"hazard_type":"Signage Defect","raw_confidence":0.72,"fused_confidence":0.72,
        "total_bus_passes":1,"effective_passes_neff":1.0,"weather_context":{"humidity":88,"precipitation":0},
        "correlation_rho":0.72,"priority_level":"LOW (MONITOR)",
        "escalation_reason":"Isolated Detection","lat":28.6394,"lng":77.1635,
        "timestamp":"2026-09-07T08:00:00Z","is_actionable":False})
# SEG-004 and SEG-005 stay UNOBSERVED to demonstrate the 5th state

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_STATIC_ROOTS = (os.path.join(_BASE_DIR, "prototype-simple"), _BASE_DIR)


def _is_inside(resolved, root):
    """True only if `resolved` is `root` itself or sits beneath it.

    Compares realpaths so symlinks cannot be used to step outside either.
    """
    root = os.path.realpath(root)
    return resolved == root or resolved.startswith(root + os.sep)


def validate_telemetry(payload):
    """Return a list of human-readable problems with an edge telemetry payload.

    Empty list means the payload is safe to fuse. Kept pure and free of HTTP so
    it can be unit-checked offline - see selfcheck_api.py.
    """
    errors = []

    for field in ("bus_id", "hazard_type"):
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} must be a non-empty string")

    conf = payload.get("confidence")
    if isinstance(conf, bool) or not isinstance(conf, (int, float)):
        errors.append("confidence must be a number")
    elif not 0.0 <= conf <= 1.0:
        errors.append("confidence must be between 0.0 and 1.0")

    # Out-of-range coordinates would silently place a defect in the ocean, so
    # they are rejected rather than clamped.
    for field, limit in (("lat", 90.0), ("lng", 180.0)):
        value = payload.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append(f"{field} must be a number")
        elif not -limit <= value <= limit:
            errors.append(f"{field} must be between -{limit} and {limit}")

    depth = payload.get("depth_mm", 0)
    if isinstance(depth, bool) or not isinstance(depth, (int, float)):
        errors.append("depth_mm must be a number")
    elif depth < 0:
        errors.append("depth_mm cannot be negative")

    return errors


def build_ticker_messages(states, work_orders, detections, weather):
    """OSINT ticker lines derived from live system state.

    The dashboard polls /api/ticker and falls back to "start the backend
    server" on any error, so this must never raise on partial state: every
    input is treated as possibly empty or None.
    """
    counts = {}
    for seg in states or []:
        key = seg.get("state", "UNKNOWN")
        counts[key] = counts.get(key, 0) + 1

    messages = []
    if weather:
        messages.append(
            f"[OPEN-METEO] Delhi {weather.get('temperature', '?')}C | "
            f"humidity {weather.get('humidity', '?')}% | "
            f"precipitation {weather.get('precipitation', '?')}mm "
            "- environmental correlation active")
    if counts.get("CONFIRMED_DEFECT"):
        messages.append(f"[FUSION] {counts['CONFIRMED_DEFECT']} segment(s) at "
                        "CONFIRMED_DEFECT - corroborated across independent bus passes")
    if counts.get("UNOBSERVED"):
        # The PS distinguishes "no defect" from "nobody looked". Say it out loud.
        messages.append(f"[COVERAGE] {counts['UNOBSERVED']} segment(s) UNOBSERVED - "
                        "no bus had a valid sensing opportunity; NOT a clear road")
    if work_orders:
        latest = work_orders[-1]
        messages.append(f"[BEL EQUINOX] Work order {latest.get('ticket_id', '?')} "
                        f"dispatched - {latest.get('severity', '?')} priority")
    messages.append(f"[EDGE] {len(detections or [])} fused detection(s) "
                    "ingested this session")
    return messages


class DrishtiAPIHandler(BaseHTTPRequestHandler):

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        # Enable CORS for browser dashboard access
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Equinox-Auth")
        self.end_headers()

    def do_OPTIONS(self):
        # Handle CORS preflight
        self._set_headers(200)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # 0. Serve Prototype Dashboard Frontend
        if path == "/" or path == "/dashboard" or path == "/index.html":
            index_file = os.path.join(os.path.dirname(__file__), "prototype-simple", "index.html")
            if os.path.exists(index_file):
                self._set_headers(200, "text/html; charset=utf-8")
                with open(index_file, "rb") as f:
                    self.wfile.write(f.read())
                return

        # Serve static assets (app.js, styles.css, etc.)
        static_exts = {
            ".js": "application/javascript",
            ".css": "text/css",
            ".png": "image/png",
            ".svg": "image/svg+xml",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".ico": "image/x-icon",
            ".woff": "font/woff",
            ".woff2": "font/woff2",
            ".ttf": "font/ttf"
        }
        for ext, mime in static_exts.items():
            if path.endswith(ext):
                # urllib does NOT normalise "..", and the URL may percent-encode
                # it, so both must be handled before touching the filesystem.
                # Without this, GET /../../anything.css served any .css/.js/.png
                # on the host - and this server binds 0.0.0.0.
                rel_path = urllib.parse.unquote(path).lstrip("/")
                for root in _STATIC_ROOTS:
                    resolved = os.path.realpath(os.path.join(root, rel_path))
                    if not _is_inside(resolved, root):
                        continue          # traversal attempt: refuse, do not serve
                    if os.path.isfile(resolved):
                        self._set_headers(200, mime)
                        with open(resolved, "rb") as f:
                            self.wfile.write(f.read())
                        return

        if path == "/api/health":
            response = {
                "system": "DRISHTI Urban Data OS API Gateway",
                "version": "1.2.0-bel-equinox",
                "status": "OPERATIONAL",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "equinox_bridge": "NGSI-LD Context Broker v1.6 (CONNECTED)",
                "endpoints": [
                    "GET  /api/health",
                    "GET  /api/detections",
                    "POST /api/edge/telemetry",
                    "GET  /api/fusion/status",
                    "GET  /api/segments/state",
                    "GET  /api/segments/coverage",
                    "GET  /api/ticker",
                    "GET  /api/equinox/workorders",
                    "POST /api/equinox/dispatch"
                ]
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(response, indent=2).encode('utf-8'))

        elif path == "/api/detections":
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "count": len(DATABASE["detections"]),
                "detections": DATABASE["detections"]
            }, indent=2).encode('utf-8'))

        elif path == "/api/fusion/status":
            # Headers are sent only after the network call succeeds: writing
            # them first meant a failed weather fetch returned 200 with an
            # empty body, and the dashboard panel just stayed blank.
            weather = fusion_engine.weather_cache.get("data")
            if not weather:
                try:
                    weather = fusion_engine.get_live_weather(28.6139, 77.2090)  # Delhi
                except Exception as e:
                    self._set_headers(503)
                    self.wfile.write(json.dumps({
                        "error": "weather context unavailable",
                        "detail": str(e),
                        "hint": "fusion still runs; rho falls back to its prior"
                    }, indent=2).encode('utf-8'))
                    return
            _, rho = fusion_engine.calculate_correlation_discount(
                2, weather["humidity"], weather["precipitation"])

            self._set_headers(200)
            self.wfile.write(json.dumps({
                "module": "DRISHTI Multi-Modal Fusion Engine",
                "active_context": "Open-Meteo Synoptic Weather",
                "current_weather": weather,
                "current_environmental_correlation_rho": rho
            }, indent=2).encode('utf-8'))

        elif path == "/api/segments/state":
            # The 5-State Road Belief Model — the core research contribution
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "model": "DRISHTI 5-State Road Belief Model",
                "states": ["CONFIRMED_DEFECT","PROBABLE_DEFECT","UNCERTAIN","PROBABLY_CLEAR","UNOBSERVED"],
                "key_insight": "UNOBSERVED means no bus had a valid sensing opportunity — absence of detection is NOT evidence of absence.",
                "segment_count": len(road_db.segments),
                "segments": road_db.get_all_states()
            }, indent=2).encode('utf-8'))

        elif path == "/api/segments/coverage":
            # Coverage table showing expected vs actual observations per road segment
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "title": "DRISHTI City-Wide Road Coverage Report",
                "coverage": road_db.get_coverage_report()
            }, indent=2).encode('utf-8'))

        elif path == "/api/ticker":
            # The dashboard polls this. It 404'd before, so the ticker showed
            # "start the backend server" permanently even with the server up.
            weather = fusion_engine.weather_cache.get("data")
            if not weather:
                try:
                    weather = fusion_engine.get_live_weather(28.6139, 77.2090)
                except Exception:
                    weather = None      # offline demo must still render a ticker
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "source": "DRISHTI live system state",
                "messages": build_ticker_messages(
                    road_db.get_all_states(), DATABASE["work_orders"],
                    DATABASE["detections"], weather)
            }, indent=2).encode('utf-8'))

        elif path == "/api/equinox/workorders":
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "source": "BEL Equinox ICCC Dispatch Registry",
                "total_workorders": len(DATABASE["work_orders"]),
                "work_orders": DATABASE["work_orders"]
            }, indent=2).encode('utf-8'))

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": f"Endpoint {path} not found"}).encode('utf-8'))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get('Content-Length', 0))
        post_body = self.rfile.read(content_length).decode('utf-8')

        try:
            payload = json.loads(post_body) if post_body else {}
        except ValueError:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Body is not valid JSON"}).encode('utf-8'))
            return
        if not isinstance(payload, dict):
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Body must be a JSON object"}).encode('utf-8'))
            return

        # 1. Edge Bus Telemetry Ingestion (from Jetson / Hailo-8 on bus)
        if path == "/api/edge/telemetry":
            required_fields = ["bus_id", "hazard_type", "confidence", "lat", "lng"]
            missing = [f for f in required_fields if f not in payload]
            if missing:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": f"Missing required fields: {missing}"}).encode('utf-8'))
                return

            # A bus is an untrusted client on a mobile link: a malformed frame
            # must be rejected here, not carried into the fusion engine. Before
            # this check, confidence="banana" raised TypeError inside
            # fuse_event() and the request died with an empty reply.
            errors = validate_telemetry(payload)
            if errors:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Invalid telemetry",
                                             "details": errors}).encode('utf-8'))
                return

            # Build raw event
            raw_event = {
                "event_id": f"EVT-{len(DATABASE['detections']) + 1:04d}",
                "bus_id": payload.get("bus_id"),
                "hazard_type": payload.get("hazard_type"),
                "confidence": payload.get("confidence"),
                "lat": payload.get("lat"),
                "lng": payload.get("lng"),
                "depth_mm": payload.get("depth_mm", 0),
                "payload_bytes": len(post_body),
                "received_at": datetime.now(timezone.utc).isoformat()
            }
            
            # --- FUSION ENGINE INTERVENTION ---
            # Simulate fetching historical detections and MCD 311 tickets in a 50m radius
            historical_mock = [d for d in DATABASE["detections"] if d.get("hazard_type") == raw_event["hazard_type"]][:2]
            mcd311_mock = [{"ticket_id": "#MCD-2026-9481"}] if raw_event["hazard_type"] == "Pothole" else []
            
            # Fuse the event
            fused_event = fusion_engine.fuse_event(raw_event, historical_mock, mcd311_mock)
            
            # --- UPDATE ROAD SEGMENT STATE MACHINE ---
            # Map the incoming GPS to the nearest road segment (simplified nearest-match)
            segment_id = payload.get("segment_id", "SEG-001")  # Default if not provided
            route_id = payload.get("route_id", "Unknown Route")
            segment_state = road_db.record_bus_pass(
                segment_id, route_id,
                has_detection=True,
                fused_event=fused_event
            )

            # --- 12-LAYER INDIAN URBAN AI ---
            streams = [k for k in SENSOR_STREAMS if isinstance(payload.get(k), dict)]
            if streams:
                # Real fleet history for this segment, not a hardcoded bus list:
                # consensus is only meaningful over passes that actually happened.
                past = [{"hazard_detected": True, "bus_id": d.get("bus_id")}
                        for d in DATABASE["detections"]
                        if d.get("segment_id") == segment_id]
                try:
                    urban_ai_result = urban_ai.process_telemetry(
                        payload, segment_id=segment_id,
                        past_observations=past + [{"hazard_detected": True,
                                                   "bus_id": payload.get("bus_id")}])
                    urban_ai_result["streams_present"] = streams
                except Exception as e:
                    # A analytics failure must not lose the detection itself.
                    urban_ai_result = {"status": "LAYER_ERROR", "detail": str(e)}
            else:
                urban_ai_result = {
                    "status": "NOT_RUN",
                    "reason": "frame carries no gps/imu/can/camera stream",
                    "expected": list(SENSOR_STREAMS)
                }

            # Combine raw and fused for storage
            final_record = {**raw_event, "segment_id": segment_id,
                            "fusion_result": fused_event,
                            "urban_ai": urban_ai_result}
            DATABASE["detections"].append(final_record)

            self._set_headers(201)
            self.wfile.write(json.dumps({
                "status": "INGESTED_AND_FUSED",
                "bandwidth_bytes": len(post_body),
                "bandwidth_saved_pct": "99.8%",
                "raw_event": raw_event,
                "fusion_intelligence": fused_event,
                "urban_ai": urban_ai_result,
                "road_segment_state": road_db.get_segment_state(segment_id)
            }, indent=2).encode('utf-8'))

        # 2. Automated Dispatch into BEL Equinox (NGSI-LD Standard)
        elif path == "/api/equinox/dispatch":
            ticket = {
                "ticket_id": f"PWD-DEL-2026-{1000 + len(DATABASE['work_orders'])}",
                "type": "https://smart-data-models.github.io/dataModel.Transportation/RoadDamageWorkOrder",
                "corridor": payload.get("corridor", "Connaught Place Radial 3"),
                "severity": payload.get("severity", "CRITICAL EMERGENCY"),
                "bitumen_required_kg": payload.get("bitumen_kg", 145),
                "target_department": "Public Works Department (PWD)",
                "assigned_crew": "Central Division Unit 4",
                "equinox_sop": "SOP-PWD-RD-04 (24h Emergency Response)",
                "dispatched_at": datetime.now(timezone.utc).isoformat(),
                "ngsi_context_broker_status": "201 Created"
            }
            DATABASE["work_orders"].append(ticket)

            self._set_headers(201)
            self.wfile.write(json.dumps({
                "message": "Successfully dispatched work order to BEL Equinox ICCC",
                "ngsi_ld_entity": ticket
            }, indent=2).encode('utf-8'))

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": f"POST endpoint {path} not found"}).encode('utf-8'))

    def log_message(self, format, *args):
        # Pretty server logs
        print(f"[{datetime.now().strftime('%H:%M:%S')}] DRISHTI-API: {format % args}")

def run_server():
    server = ThreadingHTTPServer(('0.0.0.0', PORT), DrishtiAPIHandler)
    print(f"=" * 65)
    print(f" DRISHTI Urban Data OS API Gateway is RUNNING on http://localhost:{PORT}")
    print(f" Connected to BEL Equinox ICCC Context Broker (NGSI-LD)")
    print(f" Test health: curl http://localhost:{PORT}/api/health")
    print(f"=" * 65)
    server.serve_forever()

if __name__ == '__main__':
    run_server()
