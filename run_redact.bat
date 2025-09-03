@echo off
REM Ensure venv
IF NOT EXIST .venv (
    python -m venv .venv
)

call .venv\Scripts\activate
pip install -r requirements.txt

python src\run_redact.py
pause
