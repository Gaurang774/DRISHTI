# DRISHTI: Project Handover & Deployment Guide

## 1. Work Completed (What We Built)

We successfully developed a comprehensive, end-to-end prototype for **DRISHTI** (Mobile Urban Intelligence & Data OS) designed specifically for the SIH presentation. As a "pure software" solution, we focused on architecture, simulated edge-processing, data fusion, and a highly polished UI.

### 🧠 Core Architecture & Algorithms
*   **Defined the 3-Tier Architecture:** Structured the system into Edge Telemetry (Bus YOLO) ➡️ Drishti Fusion Engine ➡️ BEL Equinox ICCC.
*   **Correlation Discount Formula:** Designed and mathematically modelled the evidence fusion algorithm to handle environmental noise (e.g., shared rain on cameras). We implemented the formula: $N_{eff} = N / [ 1 + (N - 1) \\times \\rho ]$ (where $\\rho=0.72$).
*   **OSINT Integration Logic:** Built the conceptual framework for cross-referencing AI detections with MCD 311 citizen complaints and Open-Meteo weather data.

### 💻 Backend & Integration (The "Data OS")
*   **BEL Equinox API Mock (`drishti_api.py`):** Created a Python Flask REST gateway that perfectly mimics standard NGSI-LD endpoints used by smart city brokers.
*   **Automated Work Order Dispatch:** Built the pipeline to take corroborated hazards (like a pothole or waterlogging) and automatically dispatch a JSON payload to the mock Equinox API.
*   **CORS & Live Connection:** Configured the backend to seamlessly accept POST requests from the local frontend for the live judge demonstration.

### 🎨 Frontend Prototype (The ICCC Dashboard)
*   **Premium "DRISHTI" UI:** Built a highly professional, dark-mode dashboard using standard HTML/CSS/JS. 
*   **Responsive Grid Architecture:** Transitioned from a static floating layout to a robust CSS Flexbox/Grid architecture that scales beautifully across 1080p monitors and 1366x768 laptops without overlapping.
*   **Interactive "1-Click Judge Demo":** Wired up an interactive sequence that allows judges to trigger a simulated network-wide hazard detection, watch the fusion engine aggregate evidence, and view the final Equinox work-order modal.
*   **Cinematic Map & Overlays:** Integrated Leaflet.js with custom CSS filters to create a tactical, dark-mode smart-city map.

---

## 2. Future Scope (Where It Goes Next)

The current prototype successfully proves the concept. The future scope focuses on expanding its capabilities from a localized demo to a city-wide intelligence network.

1.  **True Multi-Modal AI:** Expanding beyond visual YOLO models to incorporate audio analytics (detecting crashes or honking) and accelerometer data (corroborating potholes via physical bus bounce).
2.  **Predictive Maintenance:** Using historical hazard data to train models that predict road degradation *before* a pothole forms (e.g., identifying micro-cracking patterns over time).
3.  **Dynamic Route Optimization:** Feeding choking point and waterlogging data back into DTC navigation systems to automatically reroute buses away from emerging hazards.
4.  **Citizen Facing App:** Creating a public dashboard where citizens can see real-time road conditions verified by the DRISHTI network.

---

## 3. Professional Deployment (Going to Production)

To take this from a hackathon prototype to a fully deployed enterprise solution for the government, several architectural upgrades are required:

### A. Edge Infrastructure
*   **Hardware:** Deploying physical Edge AI accelerators (like NVIDIA Jetson Orin Nanos or even utilizing the NPUs on standard Android smartphones acting as dashcams) on the DTC buses.
*   **Quantization:** Converting standard YOLOv8 models into highly optimized TensorRT or TFLite formats to run at 30+ FPS on edge hardware without melting the devices.

### B. Video & Telemetry Pipeline
*   **Streaming Servers:** Replacing static image feeds with actual real-time RTSP streams from the bus DVRs using a scalable media server like Kurento, WebRTC, or AWS Kinesis Video Streams.
*   **Message Broker (Kafka/RabbitMQ):** Implementing a robust pub/sub message broker. Thousands of buses will generate massive amounts of telemetry; an API alone will bottleneck. Kafka is required to queue and process this data stream efficiently.

### C. Cloud & Database
*   **Containerization (Docker/Kubernetes):** The Python fusion engine (`drishti_api.py`) must be containerized and orchestrated via Kubernetes to auto-scale based on traffic (e.g., spinning up more pods during rush hour).
*   **Spatial Database:** Implementing a robust geospatial database like PostgreSQL with PostGIS extensions. Storing spatial data is required to run the "bounding box intersection" logic efficiently across thousands of reports.

### D. True BEL Equinox Integration
*   **Authentication & Security:** Moving from our open mock API to authenticating with the real BEL Equinox servers using OAuth2, JWT tokens, and strictly adhering to their specific NGSI-LD schema requirements.
*   **Rate Limiting & Retries:** Implementing robust network error handling for when buses lose 4G/5G connection, ensuring telemetry is cached locally and uploaded when the connection returns.
