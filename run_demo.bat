@echo off
title VAYU-GUARD: AI/ML AWS Anomaly Detection Platform
echo ======================================================================
echo    VAYU-GUARD: AI/ML AWS Anomaly Detection ^& Self-Healing Network
echo    SIH 26073 ^| Ministry of Earth Sciences (MoES) / IMD Prototype
echo ======================================================================

set PORT=8080
if not "%~1"=="" set PORT=%~1
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

cd /d "%~dp0"
echo -^> Working Directory: %CD%
echo -^> Starting Backend Web Server on http://127.0.0.1:%PORT% ...
echo.

py -m uvicorn backend_server:app --host 0.0.0.0 --port %PORT% --reload
pause
