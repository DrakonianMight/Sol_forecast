# Weather Forecast Dashboard - Dash Version

This is a Dash (Plotly) implementation of the Weather Forecast Dashboard, converted from Streamlit.

## Features

- **Interactive Map**: Click to select custom locations or choose from predefined sites
- **Deterministic Forecasts**: View forecasts from multiple weather models
- **Ensemble Forecasts**: Visualize ensemble predictions with percentiles and exceedance probabilities
- **Observational Data**: Compare forecasts with real weather station observations
- **Timezone Support**: View data in your local timezone
- **Production-Ready**: Built with caching, error handling, and performance optimizations

## Tech Stack

- **Dash 2.14+**: Modern Python web framework by Plotly
- **Dash Bootstrap Components**: Professional UI components
- **Dash Leaflet**: Interactive maps
- **Plotly**: Interactive charts
- **Flask-Caching**: Server-side caching for performance
- **Open-Meteo API**: Weather forecast data
- **Meteostat**: Historical observational data

## Advantages over Streamlit

1. **Better Performance**: No full-page reloads, true callbacks
2. **Production-Ready**: Flask-based, easy to scale
3. **More Control**: Fine-grained control over UI updates
4. **Better Caching**: Server-side caching with Flask-Caching
5. **Professional**: More like a traditional web app

## Local Development

### Prerequisites

- Python 3.11+
- pip

### Quick Start

```bash
# Run the startup script
./start_dash.sh
```

Or manually:

```bash
# Install dependencies
pip install -r requirements_dash.txt

# Set environment variables
export CACHE_TTL=3600
export DEBUG_MODE=true
export PORT=8050

# Run the app
python app_dash.py
```

The app will be available at `http://localhost:8050`

## Deployment to Render

### Using Docker

1. Push this branch to GitHub
2. In Render dashboard, create a new Web Service
3. Connect your GitHub repository
4. Select the `dash-conversion` branch
5. Choose "Docker" as runtime
6. Set Dockerfile path: `./docker/Dockerfile.dash`
7. Set Docker context: `./docker`
8. Add environment variables:
   - `CACHE_TTL=3600`
   - `DEBUG_MODE=false`
   - `PORT=8050`

### Using render.yaml

Alternatively, use the included `render_dash.yaml`:

```bash
# Deploy using Render Blueprint
render deploy --blueprint render_dash.yaml
```

## Environment Variables

- `CACHE_TTL`: Cache timeout in seconds (default: 3600)
- `DEBUG_MODE`: Enable debug mode (default: false)
- `PORT`: Port to run the server (default: 8050)

## Project Structure

```
docker/
├── app_dash.py              # Main Dash application
├── om_extract.py            # Weather API extraction module
├── siteList.csv             # Predefined locations
├── requirements_dash.txt    # Python dependencies
├── Dockerfile.dash          # Docker configuration
├── render_dash.yaml         # Render deployment config
├── start_dash.sh            # Local startup script
└── README_DASH.md           # This file
```

## Key Differences from Streamlit Version

### Architecture
- **Streamlit**: Single-threaded, stateful sessions, full page reloads
- **Dash**: Multi-threaded Flask app, stateless, reactive callbacks

### Caching
- **Streamlit**: `@st.cache_data` decorator
- **Dash**: Flask-Caching with `@cache.memoize`

### UI Updates
- **Streamlit**: Top-to-bottom script execution
- **Dash**: Callback-based reactive updates

### Interactivity
- **Streamlit**: Widgets trigger full reruns
- **Dash**: Callbacks update only affected components

## Performance Notes

- Server-side caching reduces API calls
- Dash callbacks only update necessary components
- No full page reloads = faster user experience
- Better suited for production with many concurrent users

## Migration Notes

If you're migrating from the Streamlit version:

1. **Same Data Sources**: Uses the same `om_extract.py` module
2. **Same Functionality**: All features preserved
3. **Better UX**: More responsive, no full page reloads
4. **Production-Ready**: Better scalability for multiple users

## Troubleshooting

### Port Already in Use
```bash
# Change the port
export PORT=8051
python app_dash.py
```

### Dependencies Not Installing
```bash
# Use virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements_dash.txt
```

### Map Not Loading
Check that `dash-leaflet` is installed:
```bash
pip install dash-leaflet==1.0.14
```

## License

Same as parent project (see root LICENSE file)

## Contributing

This is a branch conversion. To contribute:
1. Make changes in the `dash-conversion` branch
2. Test locally
3. Submit PR to merge into main

## Support

For issues specific to the Dash version, please open an issue on GitHub with the `dash-conversion` label.
