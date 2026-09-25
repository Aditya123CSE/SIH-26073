#!/usr/bin/env bash
# ==============================================================================
# VAYU-GUARD: SIH 26073 Automated Launcher with Browser Auto-Open
# ==============================================================================

PROJECT_DIR="/home/aadi/.gemini/antigravity/scratch/sih_aws_anomaly_detection"
PORT=8080
URL="http://localhost:${PORT}"

cd "$PROJECT_DIR"

echo "======================================================================"
echo "   VAYU-GUARD: AI/ML AWS Anomaly Detection & Self-Healing Network     "
echo "   SIH 26073 | Ministry of Earth Sciences (MoES) / IMD Prototype     "
echo "======================================================================"
echo "-> Working Directory: $PROJECT_DIR"
echo "-> Target URL: $URL"
echo ""

# Function to open the browser
open_browser() {
    echo "-> Opening VAYU-GUARD in your web browser..."
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$URL" >/dev/null 2>&1 &
    elif command -v python3 >/dev/null 2>&1; then
        python3 -m webbrowser "$URL" >/dev/null 2>&1 &
    else
        echo "Please open $URL manually in your browser."
    fi
}

# Check if server is already running on PORT
if curl -s -f "http://127.0.0.1:${PORT}/healthz" >/dev/null 2>&1; then
    echo "✓ VAYU-GUARD backend server is already running on port ${PORT}!"
    open_browser
    echo ""
    echo "The application is now open in your browser."
    echo "Press Enter or close this window when done."
    read -r
    exit 0
fi

# Not running -> start uvicorn
echo "-> Starting Uvicorn backend server on port ${PORT}..."
python3 -m uvicorn backend_server:app --host 0.0.0.0 --port "$PORT" --reload &
SERVER_PID=$!

# Cleanup server on script exit
cleanup() {
    echo ""
    echo "-> Stopping VAYU-GUARD server (PID: $SERVER_PID)..."
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
    echo "✓ Server stopped."
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Wait for server to become responsive
echo "-> Waiting for server to initialize..."
MAX_WAIT=20
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -s -f "http://127.0.0.1:${PORT}/healthz" >/dev/null 2>&1; then
        echo "✓ Backend server initialized and healthy!"
        break
    fi
    sleep 1
    WAITED=$((WAITED + 1))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo "⚠️ Server took longer than expected to start. Check logs above."
fi

# Open browser
open_browser

echo ""
echo "======================================================================"
echo "   VAYU-GUARD is running live at $URL"
echo "   Press Ctrl+C in this terminal to stop the server at any time.      "
echo "======================================================================"
echo ""

# Keep running and showing logs
wait "$SERVER_PID"
