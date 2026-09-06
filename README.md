# 👁️ DRISHTI — Mobile Intelligence & Urban Data OS
> **Problem Statement 26124:** AI-Powered Mobile Urban Intelligence Platform Using Public Transport Fleet  
> **Organization:** Bharat Electronics Limited (BEL) • Smart India Hackathon (SIH)

---

## 📌 Executive Summary

**DRISHTI** is an Evidence-Fusion and Operational Intelligence platform that turns regular city bus fleets (DTC) into a persistent, opportunistic urban sensing network. 

Rather than wasting public funds streaming raw 4K CCTV video over 4G/5G, DRISHTI runs **YOLOv8 inference at the edge (on-bus)**, transmitting only lightweight **~280-byte JSON telemetry**. Crucially, DRISHTI solves the **Correlated False Positive Problem**: it discounts multi-camera errors during bad weather (rain/fog) and cross-corroborates visual detections with **DTC transit delays** and **MCD 311 citizen grievances** before dispatching automated work orders into **BEL Equinox ICCC**.

---

## 🏛️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DRISHTI 3-TIER ARCHITECTURE                     │
└────────────────────────────────────────────────────────────────────────┘

 [ TIER 1: ON-BUS EDGE AI ]
  • Dashcams (Front Road, Side Curb, Rear ANPR)
  • Hailo-8 (26 TOPS, 2.5W) / NVIDIA Jetson Orin Nano
  • INT8-Quantized YOLOv8-RDD (Pothole, Waterlogging, Signage)
  • 280-Byte JSON Telemetry (99.8% Bandwidth Reduction vs Video)
                │
                ▼ (MQTT / 4G-5G REST)
 [ TIER 2: DRISHTI FUSION ENGINE & REST GATEWAY ]
  • Mathematical Correlated Evidence Discount: N_eff = N / [1 + (N - 1) * ρ]
  • Multi-Domain Context Matrix (Traffic Density + Pedestrian Risk + Choke Delay)
  • Live OSINT Fusion (Open-Meteo Satellite Weather + MCD 311 Grievance Portal)
  • Spatial Clustering & Coordinate Alignment
                │
                ▼ (ETSI NGSI-LD Standards)
 [ TIER 3: BEL EQUINOX ICCC DISPATCH ]
  • NGSI-LD Context Broker v1.6 Entity Creation
  • Automated PWD Work Order Generation (Bitumen calculation & crew routing)
  • Common Operating Picture (COP) Dashboard
```

---

## ⚡ The Core Technical Contribution: Correlated Evidence Discount

When 7 buses pass a flooded pothole during monsoon rain, a naive AI multiplies probabilities and reports 99.9% certainty. In reality, all 7 cameras were impaired by the exact same wet lens and water glare.

DRISHTI models this environmental correlation dynamically:

$$N_{\text{eff}} = \frac{N}{1 + (N - 1) \cdot \rho}$$

* **$N$**: Raw number of vehicle passes (e.g., 7 buses).
* **$\rho$**: Weather correlation coefficient ($\rho = 0.72$ automatically engaged when Open-Meteo detects relative humidity > 80% or precipitation).
* **$N_{\text{eff}}$**: Effective independent observations (**4.2** instead of 7.0), successfully preventing false alarms and budget wastage.

---

## 🚀 Live Data Sources & Integrations

| Data Stream | Source | Purpose | Protocol |
| :--- | :--- | :--- | :--- |
| **Live Weather** | Open-Meteo Global API | Ambient temperature, humidity, rain | HTTPS REST |
| **Vector Map** | OpenStreetMap (OSM) | Street networks, arterial corridors | Leaflet TileLayer |
| **Bus Routes** | DTC GTFS Corridors | 6 arterial corridors across Delhi NCR | 200ms GPS Interpolation |
| **Citizen Reports** | MCD 311 Grievance Portal | Independent civic corroboration | OSINT REST |
| **ICCC Dispatch** | BEL Equinox Context Broker | Municipal PWD work orders | ETSI NGSI-LD REST |

---

## 🛠️ Quick Start Guide

### Prerequisites
* Python 3.8+ (Zero external dependencies needed for standard run)
* Modern web browser (Chrome, Edge, Firefox)

### 1. Start the Backend API Gateway (Port 8080)
```bash
python drishti_api.py
```
*Health Check:* Open `http://localhost:8080/api/health`

### 2. Start the Frontend Dashboard (Port 8000)
```bash
cd prototype-simple
python -m http.server 8000
```
*Access UI:* Open `http://localhost:8000`

---

## 🧪 REST API Endpoints

* `GET /api/health` — System status, uptime, and connected broker status.
* `GET /api/detections` — List of all ingested edge hazard detections.
* `POST /api/edge/telemetry` — Ingest 280-byte JSON telemetry from on-bus edge AI.
* `GET /api/equinox/workorders` — Retrieve all active dispatched civic work orders.
* `POST /api/equinox/dispatch` — Generate and dispatch an ETSI NGSI-LD compliant PWD work order.

---

## 🏆 SIH Problem Statement 26124 Alignment

* **Zero Fleet Acquisition Cost**: Capitalizes on existing public transit buses (DTC) instead of expensive dedicated survey vehicles.
* **10–15 Min Refresh Cycle**: Persistent urban monitoring across 90%+ of city corridors.
* **True Smart City Middleware**: Built specifically as a plug-and-play intelligence layer for **Bharat Electronics Limited (BEL) Equinox ICCC**.
