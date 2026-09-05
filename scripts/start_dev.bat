@echo off
echo Starting RecoverAI Fullstack System...

start "RecoverAI Backend" cmd /k "cd backend && .venv\Scripts\python -m uvicorn app.main:app --reload --port 8000"
start "RecoverAI Frontend" cmd /k "cd frontend && npm run dev"

echo RecoverAI Backend: http://127.0.0.1:8000
echo RecoverAI Frontend: http://localhost:5173
