import requests
import pandas as pd
import logging
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a session with connection pooling and retries (reused across requests)
_session = None

def get_session():
    """Get or create a requests session with connection pooling"""
    global _session
    if _session is None:
        logger.info("🔧 Initializing HTTP session with connection pooling")
        _session = requests.Session()
        
        # Configure retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"]
        )
        
        # Configure adapter with connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        
        _session.mount("https://", adapter)
        _session.mount("http://", adapter)
    
    return _session

def getData(lat, lon, sites, variables = ['temperature_2m','cloud_cover'], models = ['ecmwf_ifs025','ecmwf_aifs025','bom_access_global','gfs_global', 'cma_grapes_global','ukmo_global_deterministic_10km']):
    """Fetch hourly forecast data from Open-Meteo API with connection pooling

    Args:
        lat: Latitude(s)
        lon: Longitude(s)
        sites: Site name(s)
        variables: Weather variables to fetch
        models: Forecast models to use

    Returns:
        DataFrame with forecast data
    """
    start_time = time.time()
    
    if len(sites) > 1:
        lat = ','.join(lat)
        lon = ','.join(lon)
    else:
        lat = lat[0]
        lon = lon[0]
    variables = ','.join(variables)
    models = ','.join(models)

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly={variables}&models={models}&timezone=GMT"

    # Use session for connection pooling
    session = get_session()
    
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        duration = time.time() - start_time
        logger.info(f"✅ API call completed in {duration:.2f}s for {len(sites)} site(s)")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error retrieving data from Open Meteo API: {e}")
        raise

    def makeFrame(siteData):
        mdata = pd.DataFrame(siteData['hourly'])
        mdata.index = pd.to_datetime(mdata['time'])
        mdata = mdata.drop('time', axis =1)
        return mdata
    
    if len(sites) >1:
        dlist = []
        for d, site in zip(data, sites):
            df = makeFrame(d)
            df['site'] = site
            dlist.append(df)
        return pd.concat(dlist)

    return makeFrame(data)


def getDailyData(lat, lon, sites, variables = ['temperature_2m_max','temperature_2m_min'], models = ['ecmwf_ifs025','ecmwf_aifs025','bom_access_global','gfs_global', 'cma_grapes_global','ukmo_global_deterministic_10km']):
    """Fetch daily forecast data from Open-Meteo API with connection pooling

    Args:
        lat: Latitude(s)
        lon: Longitude(s)
        sites: Site name(s)
        variables: Daily weather variables to fetch
        models: Forecast models to use

    Returns:
        DataFrame with daily forecast data
    """
    start_time = time.time()
    
    if len(sites) > 1:
        lat = ','.join(lat)
        lon = ','.join(lon)
    else:
        lat = lat[0]
        lon = lon[0]
    variables = ','.join(variables)
    models = ','.join(models)

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily={variables}&models={models}&timezone=GMT"

    # Use session for connection pooling
    session = get_session()
    
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        duration = time.time() - start_time
        logger.info(f"✅ Daily API call completed in {duration:.2f}s for {len(sites)} site(s)")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error retrieving daily data from Open Meteo API: {e}")
        raise

    def makeFrame(siteData):
        mdata = pd.DataFrame(siteData['daily'])
        mdata.index = pd.to_datetime(mdata['time'])
        mdata = mdata.drop('time', axis =1)
        return mdata
    
    if len(sites) >1:
        dlist = []
        for d, site in zip(data, sites):
            df = makeFrame(d)
            df['site'] = site
            dlist.append(df)
        return pd.concat(dlist)

    return makeFrame(data)

import re
from typing import List, Dict
from functools import reduce

def getEnsembleData(lat_list: List[str], lon_list: List[str], site_list: List[str], 
                    variables: List[str], models: List[str]) -> pd.DataFrame:
    """
    Fetch ensemble forecast data from Open-Meteo Ensemble API
    
    Args:
        lat_list: List of latitude strings
        lon_list: List of longitude strings  
        site_list: List of site names
        variables: List of variable names to fetch (e.g., ['temperature_2m'])
        models: List of ensemble model names
    
    Returns:
        DataFrame with datetime index and columns following 'variable_model_member_XX' convention.
    """
    
    # Map model names to API parameters
    model_mapping: Dict[str, str] = {
        'ecmwf_ifs_ensemble': 'ecmwf_ifs025',
        'gfs_ensemble': 'gfs025',
    }
    
    all_site_model_data = []
    
    for lat, lon, site in zip(lat_list, lon_list, site_list):
        for model in models:
            api_model = model_mapping.get(model, model)
            
            # Build API URL
            base_url = "https://ensemble-api.open-meteo.com/v1/ensemble"
            
            params = {
                'latitude': lat,
                'longitude': lon,
                'hourly': ','.join(variables),
                'models': api_model,
                'timezone': 'auto'
            }
            
            try:
                session = get_session()
                response = session.get(base_url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if 'hourly' not in data:
                    logger.warning(f"No hourly data found for {site} with {model}")
                    continue
                
                # Parse the datetime index
                times = pd.to_datetime(data['hourly']['time'])
                df_temp = pd.DataFrame({'time': times, 'site': site})
                
                # Iterate through ALL keys returned in 'hourly' to find members
                for variable_key, var_values in data['hourly'].items():
                    if variable_key == 'time':
                        continue

                    # Check if the variable key is one of the variables we requested
                    base_variable = next((v for v in variables if variable_key.startswith(v)), None)
                    
                    if base_variable:
                        # Case A: Control member (e.g., 'temperature_2m')
                        if variable_key == base_variable:
                            col_name = f"{base_variable}_{model}"
                            df_temp[col_name] = var_values
                            
                        # Case B: Numbered member (e.g., 'temperature_2m_member01')
                        elif variable_key.startswith(f"{base_variable}_member"):
                            # Extract the member number
                            match = re.search(r'member(\d+)', variable_key)
                            if match:
                                member_idx = int(match.group(1))
                                col_name = f"{base_variable}_{model}_member_{member_idx:02d}"
                                df_temp[col_name] = var_values
                            
                # Append the resulting wide DataFrame for this site/model
                all_site_model_data.append(df_temp)
                logger.info(f"✅ Fetched ensemble data for {site} with {model}")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Error fetching ensemble data for {site} with {model}: {e}")
                continue
            except Exception as e:
                logger.error(f"❌ Error parsing ensemble data for {site} with {model}: {e}")
                continue
    
    if not all_site_model_data:
        return pd.DataFrame()
    
    # Use functools.reduce for robustly merging all wide DataFrames on 'time' and 'site'
    result_df = reduce(lambda left, right: pd.merge(left, right, on=['time', 'site'], how='outer'), 
                       all_site_model_data)

    # Final formatting: Set time as index and drop the site column
    result_df = result_df.set_index('time')
    result_df = result_df.drop(columns=['site'])
    return result_df
