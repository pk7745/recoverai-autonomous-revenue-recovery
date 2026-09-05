#!/bin/bash
echo "Starting RecoverAI Fullstack System..."

# Start backend
(cd backend && .venv/bin/python -m uvicorn app.main:app --reload --port 8000) &

# Start frontend
(cd frontend && npm run dev) &

wait
