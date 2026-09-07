import time
import json
import urllib.request
import random

API_URL = "http://localhost:8080/api/edge/telemetry"

BUS_ROUTES = [
    {"bus": "Bus 402", "route": "Route 402"},
    {"bus": "Bus 119", "route": "Route 119"},
    {"bus": "Bus 880", "route": "Route 880"},
    {"bus": "Bus 221", "route": "Route 221"},
    {"bus": "Bus 534", "route": "Route 534"}
]

SEGMENTS = [
    {"id": "SEG-001", "lat": 28.6315, "lng": 77.2167},
    {"id": "SEG-002", "lat": 28.6280, "lng": 77.2750},
    {"id": "SEG-003", "lat": 28.5680, "lng": 77.2090},
    {"id": "SEG-006", "lat": 28.6139, "lng": 77.2179},
    {"id": "SEG-007", "lat": 28.6394, "lng": 77.1635}
]

HAZARDS = ["Pothole", "Waterlogging", "Signage Defect", "Illegal Parking"]

def simulate_telemetry():
    while True:
        try:
            bus = random.choice(BUS_ROUTES)
            segment = random.choice(SEGMENTS)
            
            # Most passes detect nothing (clean road)
            has_detection = random.random() < 0.35
            
            payload = {
                "bus_id": bus["bus"],
                "route_id": bus["route"],
                "segment_id": segment["id"]
            }

            if has_detection:
                payload.update({
                    "hazard_type": random.choice(HAZARDS),
                    "confidence": round(random.uniform(0.60, 0.98), 2),
                    "lat": segment["lat"] + random.uniform(-0.001, 0.001),
                    "lng": segment["lng"] + random.uniform(-0.001, 0.001),
                    "depth_mm": random.randint(10, 80) if random.random() < 0.5 else None
                })
            
            req = urllib.request.Request(API_URL, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
            try:
                with urllib.request.urlopen(req) as response:
                    res = json.loads(response.read().decode('utf-8'))
                    print(f"[{bus['bus']}] Pass on {segment['id']} -> {res['message']}")
            except Exception as e:
                print(f"Failed to post to backend: {e}")

        except Exception as e:
            print(f"Error: {e}")
        
        # Fire every 3-6 seconds
        time.sleep(random.uniform(3, 6))

if __name__ == "__main__":
    print("Starting DRISHTI Edge AI Simulator...")
    print("Simulating 5 active buses feeding data to the Context Broker...")
    simulate_telemetry()
