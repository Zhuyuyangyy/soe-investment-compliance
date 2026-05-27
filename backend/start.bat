@echo off
cd /d "%~dp0"
echo Starting 国企经营投资合规审查与责任链风险追踪系统...
echo Backend will run on http://localhost:8017
echo.
pip install -r requirements.txt -q
python -m uvicorn app.main:app --host 0.0.0.0 --port 8017 --reload
pause