# VAYU-GUARD: AI/ML AWS Intelligent Anomaly Detection & Self-Healing Network
### SIH Problem Statement ID: 26073
**Organization**: Ministry of Earth Sciences (MoES) / India Meteorological Department (IMD)  
**Theme**: Disaster Management / Software  

---

## 🚀 Quick Start (1-Minute Launch)

### On Windows:
Double-click `run_demo.bat` or run:
```powershell
cd D:\sih_aws_anomaly_detection
.\run_demo.bat
```
*(Or directly via Python: `py -m uvicorn backend_server:app --host 0.0.0.0 --port 8080 --reload`)*

### On Linux / macOS:
```bash
./run_demo.sh
```

Then open your browser and navigate to:
👉 **`http://127.0.0.1:8080`**

---

## 📁 Project Structure

```
sih_aws_anomaly_detection/
├── backend_server.py           # FastAPI REST server & orchestration layer
├── ml_engine.py                # 4-Tier Hybrid AI/ML Quality Control & Imputation Engine
├── data_generator.py           # Indian AWS network telemetry generator (11 stations)
├── static/
│   └── index.html              # Responsive interactive UI with Leaflet GIS & Chart.js
├── sample_telemetry.csv        # Pre-generated 1,000+ record realistic dataset for testing
├── test_system.py              # Automated test suite (all 7 tests passing)
├── run_demo.sh                 # One-click startup script
├── sih_presentation_guide.md   # Presentation script and faculty Q&A cheat sheet
└── README.md                   # This documentation
```

---

## 🌟 Key Innovations

1. **4-Tier Hybrid Quality Control Pipeline**:
   - **Tier 1 (Physical & Thermodynamic Laws)**: WMO limits, Magnus-Tetens Dew Point calculations (`T >= Td`), Nocturnal Solar Gating.
   - **Tier 2 (Temporal & Sensor Health)**: Flatline / stuck sensor variance filters (`std < 0.001`), rate-of-change step jump limits.
   - **Tier 3 (Multivariate ML Ensemble)**: Isolation Forest + Mahalanobis Distance for multi-sensor correlation breakdown.
   - **Tier 4 (Spatial Neighbor Cross-Validation)**: Regional AWS clustering using Haversine distance and Inverse Distance Weighting (IDW).

2. **Severe Weather vs. Sensor Failure Disambiguation**:
   - Intelligently recognizes when simultaneous multi-sensor shifts represent legitimate extreme atmospheric phenomena (monsoon squalls, thunderstorms, heatwaves) rather than hardware failure, suppressing false alarms.

3. **Self-Healing ML Imputation**:
   - Reconstructs corrupted or missing sensor readings in real time using multi-sensor regression and spatial interpolation so Numerical Weather Prediction (NWP) models never experience data gaps.

4. **Dynamic Station & Sensor Trust Scoring (0–100%)**:
   - Calculates real-time health metrics to alert maintenance crews before catastrophic failure occurs.

5. **Faculty Interactive Demo Sandbox**:
   - 1-click fault injection (Drift, Flatline, Impossible Physics, Solar Noise, Monsoon Squall) with real-time explainable AI (XAI) diagnostics.

---

## 🧪 Running Automated Tests

```bash
python3 test_system.py
```

All 7 test suites validate:
- Physical Boundary Checks
- Temporal Flatline & Jump Detectors
- Multivariate Isolation Forest Anomaly Scoring
- Spatial Neighbor Cross-Validation
- Severe Weather Disambiguation
- Self-Healing ML Imputation
- REST API & Sandbox Endpoints
