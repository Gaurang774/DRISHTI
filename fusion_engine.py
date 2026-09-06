"""
DRISHTI • MULTI-MODAL FUSION ENGINE
Implements the "Build on Top" philosophy by fusing edge AI telemetry
with OSINT (Weather) and Civic (MCD 311) data to eliminate false positives.
"""

import json
import urllib.request
import urllib.error
from datetime import datetime

class FusionEngine:
    def __init__(self):
        self.weather_cache = {"data": None, "timestamp": 0}
        self.cache_ttl = 300 # 5 minutes

    def get_live_weather(self, lat, lng):
        """Fetches live weather from Open-Meteo API to determine environmental correlation."""
        now = datetime.now().timestamp()
        if self.weather_cache["data"] and (now - self.weather_cache["timestamp"] < self.cache_ttl):
            return self.weather_cache["data"]

        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&current=temperature_2m,relative_humidity_2m,precipitation"
            req = urllib.request.Request(url, headers={'User-Agent': 'DRISHTI-Fusion-Engine/1.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode())
                current = data.get("current", {})
                
                weather_context = {
                    "temperature": current.get("temperature_2m", 25.0),
                    "humidity": current.get("relative_humidity_2m", 50),
                    "precipitation": current.get("precipitation", 0.0)
                }
                
                self.weather_cache = {"data": weather_context, "timestamp": now}
                return weather_context
                
        except Exception as e:
            print(f"[FUSION-ENGINE] Weather API Error: {e}. Using fallback.")
            # Fallback to a clear day if OSINT fails
            return {"temperature": 25.0, "humidity": 45, "precipitation": 0.0}

    def calculate_correlation_discount(self, observations_count, humidity, precipitation):
        """
        Calculates the effective number of independent observations (N_eff).
        If humidity > 80% or raining, cameras suffer from similar glare/water droplets.
        """
        if observations_count <= 1:
            return 1.0, 0.35
            
        rho = 0.35 # Default base correlation (same lighting/road layout)
        
        # Severe weather drastically increases camera failure correlation
        if precipitation > 0:
            rho = 0.85
        elif humidity > 80:
            rho = 0.72
            
        # The DRISHTI N_eff formula
        n_eff = observations_count / (1 + (observations_count - 1) * rho)
        return round(n_eff, 2), rho

    def fuse_event(self, edge_event, historical_events_in_radius, mcd311_tickets_in_radius):
        """
        Takes raw edge telemetry and fuses it with OSINT to produce a validated Work Order trigger.
        """
        lat = edge_event.get("lat")
        lng = edge_event.get("lng")
        raw_conf = edge_event.get("confidence", 0.0)
        hazard = edge_event.get("hazard_type", "UNKNOWN")
        
        # 1. Fetch OSINT Context
        weather = self.get_live_weather(lat, lng)
        
        # 2. Temporal/Spatial Clustering
        total_observations = 1 + len(historical_events_in_radius)
        
        # 3. Apply Correlation Discount
        n_eff, rho = self.calculate_correlation_discount(
            total_observations, 
            weather["humidity"], 
            weather["precipitation"]
        )
        
        # 4. Calculate Fused Confidence
        # Base confidence boosted by independent corroborations
        fused_confidence = min(0.99, raw_conf + (n_eff - 1) * 0.15)
        
        # 5. Cross-Domain Corroboration (The "5-Second Moment" Priority Flip)
        priority_level = "LOW (MONITOR)"
        escalation_reason = []
        
        if len(mcd311_tickets_in_radius) > 0:
            priority_level = "CRITICAL EMERGENCY"
            escalation_reason.append("Citizen Corroborated (MCD 311)")
            
        if n_eff >= 3.0:
            priority_level = "CRITICAL EMERGENCY" if priority_level == "CRITICAL EMERGENCY" else "HIGH"
            escalation_reason.append(f"High Fleet Persistence (N_eff: {n_eff})")
            
        if not escalation_reason:
            escalation_reason.append("Isolated Detection")

        fused_event = {
            "hazard_type": hazard,
            "raw_confidence": raw_conf,
            "fused_confidence": round(fused_confidence, 3),
            "total_bus_passes": total_observations,
            "effective_passes_neff": n_eff,
            "weather_context": weather,
            "correlation_rho": rho,
            "priority_level": priority_level,
            "escalation_reason": " + ".join(escalation_reason),
            "lat": lat,
            "lng": lng,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "is_actionable": priority_level in ["HIGH", "CRITICAL EMERGENCY"]
        }
        
        return fused_event
