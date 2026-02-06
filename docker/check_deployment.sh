#!/bin/bash

# Deployment Checklist Script
# This script checks if all necessary files are in place for Render deployment

echo "🔍 Checking Render deployment readiness..."
echo ""

# Check for required files
FILES=("app.py" "requirements.txt" "om_extract.py" "siteList.csv" "render.yaml" ".python-version")
MISSING=0

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file - Found"
    else
        echo "❌ $file - Missing"
        MISSING=$((MISSING + 1))
    fi
done

# Check .streamlit directory
if [ -d ".streamlit" ]; then
    echo "✅ .streamlit/ - Found"
    if [ -f ".streamlit/config.toml" ]; then
        echo "  ✅ config.toml - Found"
    else
        echo "  ❌ config.toml - Missing"
        MISSING=$((MISSING + 1))
    fi
else
    echo "❌ .streamlit/ - Missing"
    MISSING=$((MISSING + 1))
fi

echo ""
echo "📦 Checking Python dependencies..."

# Check if pytz is in requirements
if grep -q "pytz" requirements.txt; then
    echo "✅ pytz - Listed in requirements.txt"
else
    echo "⚠️  pytz - Not found in requirements.txt (may be needed)"
fi

# Check if folium is in requirements
if grep -q "folium" requirements.txt; then
    echo "✅ folium - Listed in requirements.txt"
else
    echo "❌ folium - Not found in requirements.txt (required)"
    MISSING=$((MISSING + 1))
fi

# Check if streamlit-folium is in requirements
if grep -q "streamlit-folium" requirements.txt; then
    echo "✅ streamlit-folium - Listed in requirements.txt"
else
    echo "❌ streamlit-folium - Not found in requirements.txt (required)"
    MISSING=$((MISSING + 1))
fi

echo ""
echo "🔧 Render Configuration Check..."

if [ -f "render.yaml" ]; then
    if grep -q "startCommand" render.yaml && grep -q "\$PORT" render.yaml; then
        echo "✅ render.yaml has correct PORT configuration"
    else
        echo "⚠️  render.yaml may need PORT variable in startCommand"
    fi
fi

echo ""
if [ $MISSING -eq 0 ]; then
    echo "🎉 All checks passed! Your app is ready for Render deployment."
    echo ""
    echo "Next steps:"
    echo "1. Commit your changes: git add . && git commit -m 'Prepare for Render'"
    echo "2. Push to GitHub: git push"
    echo "3. Go to https://dashboard.render.com/"
    echo "4. Click 'New +' → 'Blueprint' and select your repository"
    echo ""
    echo "See RENDER_DEPLOYMENT.md for detailed instructions."
else
    echo "⚠️  Found $MISSING issue(s). Please fix them before deploying."
fi

echo ""
