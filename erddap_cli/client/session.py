import pandas as pd
import re
import requests
import urllib.error
import os
import json
from erddapy import ERDDAP

def build_search_url(server, query, page=1, items_per_page=25, 
                     min_lon=None, max_lon=None, min_lat=None, max_lat=None,
                     min_time=None, max_time=None):
    """
    Build an ERDDAP advanced.csv search URL with optional bounding box and time filters.
    """
    base_url = f"{server.rstrip('/')}/search/advanced.csv"
    params = [
        f"searchFor={query}",
        f"page={page}",
        f"itemsPerPage={items_per_page}",
        "protocol=(ANY)",
        "cdm_data_type=(ANY)",
        "institution=(ANY)",
        "ioos_category=(ANY)",
        "keywords=(ANY)",
        "long_name=(ANY)",
        "standard_name=(ANY)",
        "variableName=(ANY)"
    ]

    # Optional spatial/time filters
    if min_lon is not None:
        params.append(f"minLon={min_lon}")
    else:
        params.append("minLon=")
    if max_lon is not None:
        params.append(f"maxLon={max_lon}")
    else:
        params.append("maxLon=")

    if min_lat is not None:
        params.append(f"minLat={min_lat}")
    else:
        params.append("minLat=")
    if max_lat is not None:
        params.append(f"maxLat={max_lat}")
    else:
        params.append("maxLat=")

    if min_time is not None:
        params.append(f"minTime={min_time}")
    else:
        params.append("minTime=")
    if max_time is not None:
        params.append(f"maxTime={max_time}")
    else:
        params.append("maxTime=")

    query_string = "&".join(params)
    return f"{base_url}?{query_string}"


def search_datasets(server, query, page=1, items_per_page=25,
                     min_lon=None, max_lon=None, min_lat=None, max_lat=None,
                     min_time=None, max_time=None):
    """
    Fetch one page of search results as records.
    """
    url = build_search_url(
        server, query, page, items_per_page,
        min_lon, max_lon, min_lat, max_lat, min_time, max_time
    )
    print(f"\nUsing search URL -> {url}\n")
    print(f"Page {page}, {items_per_page} items:\n(Dataset ID : Title)\n")
    df = pd.read_csv(url)
    return df.to_dict(orient="records")


def get_total_count(server, query,
                    min_lon=None, max_lon=None, min_lat=None, max_lat=None,
                    min_time=None, max_time=None):
    """
    Get total count by fetching large page with advanced filters.
    """
    url = build_search_url(
        server, query, page=1, items_per_page=100000,
        min_lon=min_lon, max_lon=max_lon,
        min_lat=min_lat, max_lat=max_lat,
        min_time=min_time, max_time=max_time
    )
    print(f"\nFetching ALL results for count from -> {url}\n")

    try:
        df = pd.read_csv(url, comment='#')
        return len(df)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("Server returned 404 for total count request, possible URL encoding error or network issues.")
            return 0
        else:
            raise
    except Exception as ex:
        print(f"Unexpected error fetching total count: {ex}")
        return None

def get_dataset_info(server: str, dataset_id: str) -> dict[str, any]:
    """
    Fetch global metadata and per-variable attributes for a dataset.
    """
    # Build the ERDDAP info CSV URL
    e = ERDDAP(server=server)
    e.dataset_id = dataset_id
    info_url = e.get_info_url(response="csv")

    try:
        df = pd.read_csv(
            info_url,
            comment='#',
            engine='python',
            skip_blank_lines=True
        )
    except Exception as err:
        raise RuntimeError(f"Failed to parse dataset info CSV from {info_url!r}: {err}")

    df = df.fillna('')

    # Global attributes
    global_df = df[(df['Row Type']=='attribute') & (df['Variable Name']=='NC_GLOBAL')]
    global_attrs = {row['Attribute Name']: row['Value'] for _, row in global_df.iterrows()}

    # Dimensions
    dim_df = df[df['Row Type']=='dimension']
    dim_names = dim_df['Variable Name'].unique()
    dimensions = []
    for dim in dim_names:
        dim_row = dim_df[dim_df['Variable Name'] == dim]
        nvalues = None
        spacing = None
        dtype = None
        if not dim_row.empty:
            dtype = dim_row.iloc[0].get('Data Type', '')
            val = dim_row.iloc[0].get('Value', '')
            if val:
                m = re.search(r"nValues=(\d+)", val)
                if m:
                    nvalues = int(m.group(1))
                m2 = re.search(r"averageSpacing=([^,]+)", val)
                if m2:
                    spacing = m2.group(1).strip()
        dim_attr_rows = df[(df['Row Type'] == 'attribute') & (df['Variable Name'] == dim)]
        def get_attr(name):
            vals = dim_attr_rows[dim_attr_rows['Attribute Name'] == name]['Value'].values
            return vals[0] if len(vals) else ''
        min_val = get_attr('actual_range')
        min_v, max_v = '', ''
        if min_val and isinstance(min_val, str) and ' ' in min_val:
            min_v, max_v = min_val.split(' ', 1)
        dimensions.append({
            'name':            dim,
            'data_type':       dtype,
            'nvalues':         nvalues,
            'average_spacing': spacing,
            'min':             min_v,
            'max':             max_v,
            'long_name':       get_attr('long_name'),
            'standard_name':   get_attr('standard_name'),
            'units':           get_attr('units')
        })

    # Variables
    vars_df = df[df['Row Type']=='variable']
    var_names = vars_df['Variable Name'].unique()
    variables = []
    for var in var_names:
        attr_rows = df[
            (df['Row Type'] == 'attribute') &
            (df['Variable Name'] == var)
        ]
        def get_attr(name):
            vals = attr_rows[attr_rows['Attribute Name'] == name]['Value'].values
            return vals[0] if len(vals) else ''
        min_val = get_attr('actual_range')
        min_v, max_v = '', ''
        if min_val and isinstance(min_val, str) and ' ' in min_val:
            min_v, max_v = min_val.split(' ', 1)
        variables.append({
            'name':          var,
            'units':         get_attr('units'),
            'standard_name': get_attr('standard_name'),
            'long_name':     get_attr('long_name'),
            'comment':       get_attr('comment'),
            'min':           min_v,
            'max':           max_v,
            'actual_range':  get_attr('actual_range'),
            'flag_meanings': get_attr('flag_meanings'),
            'flag_values':   get_attr('flag_values')
        })

    return {
        'dataset_id':          dataset_id,
        'title':               global_attrs.get('title', ''),
        'summary':             global_attrs.get('summary', ''),
        'institution':         global_attrs.get('institution', ''),
        'time_coverage_start': global_attrs.get('time_coverage_start', ''),
        'time_coverage_end':   global_attrs.get('time_coverage_end', ''),
        'nmost_northing':      global_attrs.get('Northernmost_Northing', ''),
        'emost_easting':       global_attrs.get('Easternmost_Easting', ''),
        'smost_northing':      global_attrs.get('Southernmost_Northing', ''),
        'wmost_easting':       global_attrs.get('Westernmost_Easting', ''),
        'cdm_data_type':       global_attrs.get('cdm_data_type', ''),
        'data_type':           global_attrs.get('data_type', ''),
        'global_attrs':        global_attrs,
        'dimensions':          dimensions,
        'variables':           variables
    }
    
def get_download_url(server, dataset_id, variables=None, constraints=None, response_format="csv", protocol="tabledap"):
    e = ERDDAP(server=server)
    e.dataset_id = dataset_id
    e.protocol = protocol
    e.response = response_format

    if variables:
        e.variables = variables
    if constraints:
        e.constraints = constraints

    return e.get_download_url()

DEFAULT_SERVERS = [
    {"name": "NOAA CoastWatch", "url": "https://coastwatch.pfeg.noaa.gov/erddap"},
    {"name": "IOOS Glider DAC", "url": "https://data.ioos.us/gliders/erddap"},
    {"name": "NOAA NCEI", "url": "https://www.ncei.noaa.gov/erddap"},
    {"name": "NOAA PMEL", "url": "https://ferret.pmel.noaa.gov/pmel/erddap"},
    {"name": "NOAA SWFSC", "url": "https://oceanview.pfeg.noaa.gov/erddap"},
    {"name": "NOAA GOES", "url": "https://coastwatch.noaa.gov/erddap"},
    {"name": "PacIOOS", "url": "https://oos.soest.hawaii.edu/erddap"},
    {"name": "CeNCOOS", "url": "https://erddap.cencoos.org/erddap"},
    {"name": "SECOORA", "url": "https://erddap.secoora.org/erddap"},
    {"name": "NERACOOS", "url": "https://www.neracoos.org/erddap"}
]

def get_servers_config_path():
    return os.path.expanduser("~/.erddap_cli_servers.json")

def load_custom_servers():
    path = get_servers_config_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_custom_servers(servers):
    path = get_servers_config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(servers, f, indent=2)

def list_known_servers():
    custom = load_custom_servers()
    names = {s["name"] for s in custom}
    merged = custom[:]
    for s in DEFAULT_SERVERS:
        if s["name"] not in names:
            merged.append(s)
    return merged

def add_custom_server(name, url):
    servers = load_custom_servers()
    for s in servers:
        if s["name"] == name:
            s["url"] = url
            save_custom_servers(servers)
            return
    servers.append({"name": name, "url": url})
    save_custom_servers(servers)

def remove_custom_server(name):
    servers = load_custom_servers()
    servers = [s for s in servers if s["name"] != name]
    save_custom_servers(servers)
