#!/bin/bash

# Local development startup script
# Run this to test your app locally before deploying

echo "🚀 Starting Weather Forecast Dashboard locally..."
echo ""

# Check if requirements are installed
if ! python -c "import streamlit" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
else
    echo "✅ Dependencies already installed"
fi

echo ""
echo "🌐 Starting Streamlit app..."
echo "   Local URL: http://localhost:8501"
echo "   Press Ctrl+C to stop"
echo ""

# Start Streamlit with proper configuration
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
