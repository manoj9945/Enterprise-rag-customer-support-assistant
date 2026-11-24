@echo off
cd /d "%~dp0"
if not exist .venv (
  echo Creating virtual environment...
  python -m venv .venv
)
call .venv\Scripts\activate
echo Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if not exist .env copy .env.example .env
if not exist data\ecommerce.db (
  echo Database will be created and seeded when the API starts.
)
start "RAG Backend API" cmd /k "cd /d %~dp0 && call .venv\Scripts\activate && uvicorn backend.main:app --reload"
timeout /t 4 >nul
start "RAG Frontend" cmd /k "cd /d %~dp0 && call .venv\Scripts\activate && streamlit run frontend\app.py"
echo.
echo Backend: http://127.0.0.1:8000
echo API docs: http://127.0.0.1:8000/docs
echo Frontend: http://localhost:8501
pause
