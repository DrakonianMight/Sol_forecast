#!/bin/bash

# Start Dash application locally
echo "🚀 Starting Weather Forecast Dashboard (Dash)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📦 Installing/checking dependencies..."
pip install -r requirements_dash.txt

echo ""
echo "🌐 Starting server on http://localhost:8050"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Set environment variables
export CACHE_TTL=3600
export DEBUG_MODE=true
export PORT=8050

# Run the app
python app_dash.py
