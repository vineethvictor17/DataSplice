#!/bin/bash
# Start DataSplice Frontend

cd "$(dirname "$0")"
source venv/bin/activate
streamlit run frontend/app.py

