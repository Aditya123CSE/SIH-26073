#!/usr/bin/env bash
# ==============================================================================
# VAYU-GUARD: AI/ML AWS Anomaly Detection Platform Launcher
# Problem Statement: SIH 26073 (Ministry of Earth Sciences / IMD)
# ==============================================================================

set -e

PORT=${1:-8080}
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "======================================================================"
echo "   VAYU-GUARD: AI/ML AWS Anomaly Detection & Self-Healing Network     "
echo "   SIH 26073 | Ministry of Earth Sciences (MoES) / IMD Prototype     "
echo "======================================================================"
echo "-> Working Directory: $PROJECT_DIR"
echo "-> Starting Backend Web Server on http://127.0.0.1:$PORT ..."
echo ""

if [ -f "$PROJECT_DIR/.venv/bin/python" ]; then
    PYTHON_CMD="$PROJECT_DIR/.venv/bin/python"
else
    PYTHON_CMD="python3"
fi

"$PYTHON_CMD" -m uvicorn backend_server:app --host 0.0.0.0 --port "$PORT" --reload

