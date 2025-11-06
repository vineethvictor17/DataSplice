#!/bin/bash
# Start DataSplice Backend

cd "$(dirname "$0")"
source venv/bin/activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

