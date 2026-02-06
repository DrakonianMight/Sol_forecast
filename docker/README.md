# Weather Forecast Dashboard

A Streamlit-based weather forecasting visualization dashboard featuring both deterministic and ensemble forecasts with advanced threshold analysis.

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Note: You'll also need the `om_extract` module for data extraction.

## Running the Application

To run the Streamlit app locally:

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

## Features

- **Forecast Types**:
  - **Deterministic**: Traditional single-value forecasts from multiple weather models
  - **Ensemble**: Probabilistic forecasts with percentile bands and ensemble members
- **Threshold Analysis**: Configure up to 3 custom thresholds and calculate exceedance probabilities
- **Timezone Support**: View forecasts in your local timezone (UTC, Australia, US, Europe, Asia)
- **Site Selection**: Choose locations from dropdown and interactive map
- **Variable Selection**: Multi-select weather parameters (temperature, wind, radiation, cloud cover)
- **Large Visualizations**: Map and plots optimized to fill the page for better visibility
- **Observational Data**: Integrated Meteostat data overlay for validation

## Technical Details

- **Ensemble Support**: Fetches and visualizes ensemble forecast data with percentile calculations
- **Probability Analytics**: Calculates exceedance probabilities for user-defined thresholds
- **Timezone Conversion**: Uses pytz for accurate timezone handling
- **Caching**: Implements `@st.cache_data` for optimized data fetching
- **Wide Layout**: 2-column layout maximizes screen real estate for maps and plots
- **Reactive Updates**: Streamlit automatically reruns on user interaction

## File Requirements

Make sure these files are in the same directory:
- `app.py` - Main application file
- `om_extract.py` - Data extraction module
- `siteList.csv` - List of weather station sites

## Docker Deployment

Build and run the application using Docker:

```bash
docker build -t helios-forecast .
docker run -p 8501:8501 helios-forecast
```

The Dockerfile is already configured for Streamlit deployment.

## Configuration

You can customize the app by modifying these variables in `app.py`:

- `hourly_params`: List of hourly weather parameters
- `daily_params`: List of daily weather parameters
- `color_map`: Color scheme for different forecast models
- `column_mapping`: Mapping between model and observational data columns
