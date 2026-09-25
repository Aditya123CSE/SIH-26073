# 🚀 HOW TO RUN VAYU-GUARD SERVER
**SIH Problem Statement 26073**  
*AI/ML Automated Weather Station Quality Control & Self-Healing Network (MoES / IMD)*

---

## ⚡ Quick Start Options

### Option 1: 1-Click Desktop Icon (Easiest)
A desktop launcher shortcut has been created on your Linux Desktop:
- Simply double-click **`VAYU-GUARD (SIH 26073)`** on your Desktop.
- It will verify the server status, start it if not running, and automatically pop open the application in your default web browser.

---

### Option 2: Automatic Browser Launch Script
Run the automated launcher from terminal:
```bash
./launch_browser.sh
```
*(Starts the backend server and automatically opens `http://localhost:8080` in your web browser).*

---

### Option 3: Using the Terminal Server Launcher
```bash
./run_demo.sh
```
*(Runs the backend web server with live logging on port 8080).*

---

### Option B: Using Python Directly

#### 1. Activate the Virtual Environment (Recommended):
```bash
# On Linux / macOS:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

#### 2. Start the Uvicorn Web Server:
```bash
# Using Python directly in virtual environment:
.venv/bin/python -m uvicorn backend_server:app --host 0.0.0.0 --port 8080 --reload
```
*Or, if your virtual environment is activated:*
```bash
uvicorn backend_server:app --host 0.0.0.0 --port 8080 --reload
```

---

## 🌐 Accessing the Application

Once the server starts and prints:
```
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

Open your web browser and navigate to:
👉 **[http://localhost:8080](http://localhost:8080)**  
*(or `http://127.0.0.1:8080`)*

---

## 🧭 Navigating the 6 Platform Pages

| Page | URL Hash | Highlights & Key Features |
|---|---|---|
| **1. Guide & Mission** | `http://localhost:8080/#guide` | **Part 1:** Full project context, IMD / Mission Mausam mandates, 4 failure modes.<br>**Part 2:** Benchmark comparison matrix (vs. IMD Pune, NOAA MADIS, Vaisala).<br>**Part 3:** Interactive feature tour with 1-click `[Show Feature in ... →]` buttons and floating presenter return badge. |
| **2. Executive Overview** | `http://localhost:8080/#overview` | High-level national KPI cards, 44 monitored observatories, incident triage console, and 30-day activity calendar. |
| **3. 3D Globe & 2D Map Grid** | `http://localhost:8080/#map` | **Dual-Mode Visualization**: Instant 1-click toggle between **3D Future-Tech Digital Globe** (WebGL earth sphere, orbital satellite, altitude pins, and IDW arcs) and **2D Synoptic Map** (Leaflet dark night canvas, satellite, terrain, and regional filters). Pin click opens holographic station HUD with direct Tech Machine launch. |
| **4. Fault Sandbox** | `http://localhost:8080/#sandbox` | Interactive fault injection bench right on the page with **3-trace oscilloscope graph** showing Before (Cyan), After (Neon Pink), and Self-Healed (Violet), plus a 1-click **`[⚡ Pop out as Cybernetic Tech Machine Console]`** button with pneumatic audio effects. |
| **5. Station Deep Dive** | `http://localhost:8080/#inspector` | Granular sensor telemetry curves, 4-tier QC check breakdown, and 1-click printable Government of India WMO-No. 8 compliance certificate. |
| **6. XAI Physics Engine** | `http://localhost:8080/#xai` | **Multivariate AI Feature Space & Cluster Constellation** (Cyan vs Magenta scatter plot), interactive station-by-station thermodynamic decision boundary inspector, and deterministic atmospheric physics proofs (Magnus-Tetens, Nocturnal Solar Zenith, Hypsometric, Mahalanobis Distance). |

---

## 🛑 How to Stop the Server

### In the terminal running the server:
Press:
```
Ctrl + C
```

### If the server is running in the background (Linux):
```bash
# Find and stop the process on port 8080:
fuser -k 8080/tcp
```
*Or kill by process name:*
```bash
pkill -f "uvicorn backend_server:app"
```

---

## 🧪 Running Automated Quality & Regression Tests

To verify all 4 quality control tiers, spatial neighbor consensus, storm disambiguation, and self-healing ML imputation:

```bash
.venv/bin/python test_system.py
```
Expected output:
```
Ran 7 tests in ~20s
OK
```

---

## 🔧 Environment Setup (If installing on a new machine)

If setting up on a fresh machine without `.venv`:

```bash
# 1. Create a virtual environment
python3 -m venv .venv

# 2. Activate it
source .venv/bin/activate    # Linux/Mac
# or: .venv\Scripts\activate # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the server
uvicorn backend_server:app --host 0.0.0.0 --port 8080 --reload
```

---

## ⚠️ Troubleshooting

1. **Port 8080 already in use**:
   - Run on another port:
     ```bash
     ./run_demo.sh 8081
     ```
     or
     ```bash
     .venv/bin/python -m uvicorn backend_server:app --host 0.0.0.0 --port 8081 --reload
     ```
     Then open `http://localhost:8081`.

2. **ModuleNotFoundError**:
   - Ensure you are using `.venv/bin/python` or have activated the virtual environment where `fastapi`, `uvicorn`, `scikit-learn`, `pandas`, and `numpy` are installed.

3. **Offline Mode**:
   - The platform includes `real_telemetry_cache.json` which automatically provides authentic ground observations for all 44 observatories even with zero internet access during presentations.
