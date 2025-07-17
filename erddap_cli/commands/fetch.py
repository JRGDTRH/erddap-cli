# erddap_cli/commands/fetch.py

import argparse
import pandas as pd
import urllib.error
from erddap_cli.client.session import get_dataset_info

# --- Low-Level Helper Functions ---

def _clean_val(val):
    """Cleans up metadata values to be consistent strings."""
    if isinstance(val, str):
        val = val.strip().rstrip(',')
        try:
            return str(float(val))
        except (ValueError, TypeError):
            return val
    try:
        return str(val)
    except (ValueError, TypeError):
        return ''

def _get_var_actual_range(varname, variables_list):
    """Finds the actual_range for a given variable from the metadata list."""
    for v in variables_list:
        if v.get('name') == varname:
            actual_range = v.get('actual_range')
            if isinstance(actual_range, list) and len(actual_range) == 2:
                return _clean_val(actual_range[0]), _clean_val(actual_range[1])
            
            if isinstance(actual_range, str):
                parts = actual_range.replace(',', ' ').split()
                if len(parts) == 2:
                    return _clean_val(parts[0]), _clean_val(parts[1])
    return '', ''

def _fetch_and_process_data(url: str, output_path: str = None):
    """Fetches data from the final URL, shows a preview, and optionally saves."""
    print(f"\nQuery URL:\n{url}\n")

    preview = input("Fetch and preview data? [y/N]: ").strip().lower()
    if preview != 'y':
        print("Fetch cancelled.")
        return

    try:
        encoded_url = url.replace('>=', '%3E=').replace('<=', '%3C=')
        df = pd.read_csv(encoded_url)

        if not df.empty:
            print("\nData preview (first 5 rows):")
            print(df.head().to_string(index=False))
            if output_path:
                df.to_csv(output_path, index=False)
                print(f"\nData successfully saved to {output_path}")
        else:
            print("Your query is valid but produced no matching results.")

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='ignore')
        final_message = f"Error fetching data: {e}"
        for line in error_body.splitlines():
            if '<b>Message</b>' in line:
                message = line.strip().replace('<p>', '').replace('</p>', '').replace('<b>Message</b>', '').strip()
                final_message = f"Server Error: {message}"
                break
        print(f"\n{final_message}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# --- Protocol-Specific Workflow Functions ---

def _tabledap_workflow(info: dict, server: str, dataset_id: str, selected_vars: list, output_path: str):
    """Handles the query-building and fetching process for tabledap."""
    print("\n--- Specify Tabledap Constraints (min/max) ---")
    print("Press Enter to skip any constraint.\n")

    variables = info.get('variables', [])
    global_attrs = info.get('global_attrs', {})
    constraints = {}

    for var_name in selected_vars:
        v_info = next((v for v in variables if v.get('name') == var_name), {})
        units = v_info.get('units', '')
        is_time = 'since' in units.lower() or var_name.lower() == 'time'

        min_v, max_v = '', ''
        # Re-integrate logic to find time coverage from global attributes
        if is_time:
            min_v = global_attrs.get('time_coverage_start', '')
            max_v = global_attrs.get('time_coverage_end', '')
        else:
            min_v, max_v = _get_var_actual_range(var_name, variables)

        if min_v and max_v and min_v != max_v:
            print(f"- Variable: {var_name} (Value Range: {min_v} to {max_v})")
            user_min = input(f"    Minimum value (>=): ").strip()
            if user_min:
                constraints[f"{var_name}>="] = user_min
            
            user_max = input(f"    Maximum value (<=): ").strip()
            if user_max:
                constraints[f"{var_name}<="] = user_max
        else:
            print(f"- Variable: {var_name}: No constraint range available.")

    # Build URL
    variable_string = ",".join(selected_vars)
    constraint_parts = []
    for key, value in constraints.items():
        constraint_parts.append(f"{key}{value}")

    constraint_string = "&" + "&".join(constraint_parts) if constraint_parts else ""
    url = f"{server.rstrip('/')}/tabledap/{dataset_id}.csv?{variable_string}{constraint_string}"

    _fetch_and_process_data(url, output_path)

def _griddap_workflow(info: dict, server: str, dataset_id: str, selected_vars: list, dims: list, output_path: str):
    """Handles the query-building and fetching process for griddap."""
    print("\n--- Specify Griddap Slices for Each Dimension ---")
    print("Use [start:stride:stop] index notation. You can use exact values for start/stop.\n Stride is based on data spacing.")
    print("Example for Index: [0:1:100]")
    print("      Coordinates: [(-70.5):1:(-68.2)]")
    print("             Time: [(2021-01-01T00:00:00Z:1:2021-12-31T00:00:00Z)]\n")

    global_attrs = info.get('global_attrs', {})
    slices = {}

    for dim in dims:
        nvalues = int(dim.get('nvalues')) - 1 # Subtract 1 to stay in slicing bounds
        spacing = dim.get('average_spacing')
        dim_name = dim.get('name', '')
        is_time = dim_name.lower() == 'time'
        min_v, max_v = '', ''

        # Get range for the dimension
        if is_time:
            min_v = global_attrs.get('time_coverage_start', '')
            max_v = global_attrs.get('time_coverage_end', '')
        else:
            min_from_meta = dim.get('min')
            max_from_meta = dim.get('max')

            if min_from_meta and max_from_meta:
                min_v = _clean_val(min_from_meta)
                max_v = _clean_val(max_from_meta)

        # Build the user prompt
        prompt_text = f"- Dimension: {dim_name} (data spacing: {spacing})"
        if min_v and max_v:
            prompt_text += f"\n    Value Range: [({min_v}):1:({max_v})]\n    Start:Stride:Stop Range: [0:1:{nvalues}]\n"
        prompt_text += f"    Enter slice for {dim_name}: "
        print()

        slice_val = input(prompt_text).strip()
        
        if slice_val:
            slices[dim_name] = slice_val
        else:
            # If user skips, apply a default slice for the full range of that dimension
            default_slice = f"[0:1:{nvalues}]"
            slices[dim_name] = default_slice
            print(f"    -> No input given, using default full range slice: {default_slice}")

    # Build URL
    slice_string = "".join(slices.values())
    sliced_vars = [f"{var}{slice_string}" for var in selected_vars]
    query_string = ",".join(sliced_vars)
    url = f"{server.rstrip('/')}/griddap/{dataset_id}.csv?{query_string}"

    _fetch_and_process_data(url, output_path)

# --- Main Command Logic ---

def setup_fetch_command(subparsers):
    """Register the 'fetch' subcommand."""
    parser = subparsers.add_parser(
        "fetch",
        help="Interactively build a query to fetch ERDDAP data."
    )
    parser.add_argument(
        "--output",
        help="Optional: Path to save the fetched data as a CSV file. (e.g. ./csvout.csv)"
    )
    parser.set_defaults(func=handle_fetch)

def handle_fetch(args):
    """Main dispatcher function for the interactive fetch command."""
    print("\n--- ERDDAP Interactive Query Builder ---")

    # 1. Common Steps: Get server, dataset, and metadata
    server = input("Enter ERDDAP server URL: ").strip()
    dataset_id = input("Enter dataset ID: ").strip()
    
    try:
        info = get_dataset_info(server, dataset_id)
    except Exception as e:
        print(f"Failed to fetch dataset info: {e}")
        return

    # 2. Common Steps: Determine protocol
    cdm_type = info.get('cdm_data_type', 'unknown').lower()
    suggestion = 'griddap' if cdm_type == 'grid' else 'tabledap'
    print(f"\nDetected data type: {cdm_type}. Suggested protocol: {suggestion}")
    protocol = input(f"Select protocol [tabledap/griddap] (default: {suggestion}): ").strip().lower() or suggestion

    # 3. Common Steps: Select variables
    variables = info.get('variables', [])
    print("\nAvailable variables:")
    for idx, var in enumerate(variables):
        print(f"  [{idx}] {var['name']}")
    
    var_idxs_str = input("\nSelect variables by number (comma-separated, or leave blank for all): ").strip()
    if not var_idxs_str:
        selected_vars = [v['name'] for v in variables]
    else:
        try:
            idxs = [int(i.strip()) for i in var_idxs_str.split(',')]
            selected_vars = [variables[i]['name'] for i in idxs]
        except (ValueError, IndexError):
            print("Invalid variable selection.")
            return

    # 4. Re-integrate fallback logic for identifying dimensions
    dims = info.get('dimensions', [])
    if not dims:
        dim_names = {'time', 'depth', 'altitude', 'latitude', 'longitude', 'lat', 'lon'}
        dims = [v for v in variables if v.get('name', '').lower() in dim_names]

    # 5. Diverge: Call the specific workflow based on protocol
    if protocol == 'tabledap':
        _tabledap_workflow(info, server, dataset_id, selected_vars, args.output)
    elif protocol == 'griddap':
        _griddap_workflow(info, server, dataset_id, selected_vars, dims, args.output)
    else:
        print(f"Error: Unknown protocol '{protocol}'. Please choose 'tabledap' or 'griddap'.")