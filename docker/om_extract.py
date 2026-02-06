import requests
import pandas as pd

def getData(lat, lon, sites, variables = ['temperature_2m','cloud_cover'], models = ['ecmwf_ifs025','ecmwf_aifs025','bom_access_global','gfs_global', 'cma_grapes_global','ukmo_global_deterministic_10km']):
    """_summary_

    Args:
        lat (_type_): _description_
        lon (_type_): _description_
        sites (_type_): _description_
        variables (list, optional): _description_. Defaults to ['temperature_2m','cloud_cover'].

    Returns:
        _type_: _description_
    """
    if len(sites) > 1:
        lat = ','.join(lat)
        lon = ','.join(lon)
    else:
        lat = lat[0]
        lon = lon[0]
    variables = ','.join(variables)
    models = ','.join(models)

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly={variables}&models={models}&timezone=GMT"

    # Retrieve ECMWF temperatures
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()

    else:
        print("Error retrieving ACCESS data from Open Meteo API.")

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
    """_summary_

    Args:
        lat (_type_): _description_
        lon (_type_): _description_
        sites (_type_): _description_
        variables (list, optional): _description_. Defaults to ['temperature_2m','cloud_cover'].

    Returns:
        _type_: _description_
    """
    if len(sites) > 1:
        lat = ','.join(lat)
        lon = ','.join(lon)
    else:
        lat = lat[0]
        lon = lon[0]
    variables = ','.join(variables)
    models = ','.join(models)

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily={variables}&models={models}&timezone=GMT"

    # Retrieve ECMWF temperatures
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()

    else:
        print("Error retrieving ACCESS data from Open Meteo API.")

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
                response = requests.get(base_url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if 'hourly' not in data:
                    print(f"No hourly data found for {site} with {model}")
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
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching ensemble data for {site} with {model}: {e}")
                continue
            except Exception as e:
                print(f"Error parsing ensemble data for {site} with {model}: {e}")
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
