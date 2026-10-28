@echo off
echo ========================================================
echo   IVF Implantation Success Predictor Web Application
echo ========================================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment 'venv' not found!
    echo Please make sure the venv is created.
    pause
    exit /b 1
)

echo Starting Flask server on http://127.0.0.1:5000 ...
echo Press Ctrl+C to stop the server anytime.
echo.

venv\Scripts\python.exe app.py
pause

