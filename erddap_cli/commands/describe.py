# erddap_cli/commands/describe.py
import argparse
from erddap_cli.client.session import get_dataset_info

def setup_describe_command(subparsers):
    """
    Register the 'describe' subcommand to show dataset metadata, dimensions, and variables.
    """
    parser = subparsers.add_parser(
        "describe",
        help="Show dataset metadata, dimensions, and variables."
    )
    parser.add_argument(
        "--server",
        required=True,
        help="ERDDAP server URL"
    )
    parser.add_argument(
        "--dataset-id",
        required=True,
        help="Dataset ID"
    )
    parser.add_argument(
        "--section",
        choices=["all", "vars", "dims"],
        default="all",
        help="Section to display: all, vars (variables only), or dims (dimensions only)"
    )
    parser.add_argument(
        "--output-format",
        choices=["text", "json", "yaml"],
        default="text",
        help="Output format: text (default), json, or yaml"
    )
    parser.set_defaults(func=handle_describe)

def _print_unified_block(item, info_dict):
    # Use 'or' to default to 'N/A' if the value is an empty string
    name = item.get('name') or 'N/A'
    is_time = name.lower() == 'time'

    # Data Type Handling:
    dtype = item.get('data_type') or 'N/A'

    # Determine Min/Max (Handling Time specifically)
    if is_time:
        min_v_raw = info_dict.get('time_coverage_start', '')
        max_v_raw = info_dict.get('time_coverage_end', '')
    else:
        min_v_raw = str(item.get('min', '')).rstrip(',')
        max_v_raw = str(item.get('max', '')).rstrip(',')

    # Apply N/A fallback for Min/Max
    min_v = min_v_raw or 'N/A'
    max_v = max_v_raw or 'N/A'
    
    # Standard metadata fields with 'or' fallback
    long_name = item.get('long_name') or 'N/A'
    std_name = item.get('standard_name') or 'N/A'
    units = item.get('units') or 'N/A'

    # Print the unified block
    print(f"- {name}")
    print(f"    Long Name:     {long_name}")
    print(f"    Standard Name: {std_name}")
    print(f"    Data Type:     {dtype}")
    print(f"    Units:         {units}")
    if min_v == 'N/A' and max_v == 'N/A':
        print(f"    Value Range:   N/A")
    else:
        print(f"    Value Range:   {min_v} to {max_v}")
    
    # Optionally add dimension-specific info if available
    if 'nvalues' in item and item.get('nvalues'):
        print(f"    nValues:       {item.get('nvalues')}")
    if 'average_spacing' in item and item.get('average_spacing'):
        print(f"    Avg Spacing:   {item.get('average_spacing')}")
        
    # Optionally add variable-specific flag info if available
    if 'flag_values' in item and item.get('flag_values'):
        print(f"    Flag Values:   {item.get('flag_values')}")
    if 'flag_meanings' in item and item.get('flag_meanings'):
        print(f"    Flag Meanings: {', '.join(item.get('flag_meanings').split())}")

def handle_describe(args):
    """
    Handle the 'describe' command: fetch and print selected sections of dataset info.
    """
    info = get_dataset_info(args.server, args.dataset_id)
    protocol = 'griddap' if info.get('cdm_data_type', '').lower() == 'grid' else 'tabledap'
    section = args.section
    output_format = getattr(args, "output_format", "text")

    if output_format == "json":
        import json
        if section == "all":
            print(json.dumps(info, indent=2))
        elif section == "dims":
            print(json.dumps(info.get("dimensions", []), indent=2))
        elif section == "vars":
            print(json.dumps(info.get("variables", []), indent=2))
        return
    elif output_format == "yaml":
        try:
            import yaml
        except ImportError:
            print("PyYAML is required for YAML output. Please install with 'pip install pyyaml'.")
            return
        if section == "all":
            print(yaml.dump(info, sort_keys=False, allow_unicode=True))
        elif section == "dims":
            print(yaml.dump(info.get("dimensions", []), sort_keys=False, allow_unicode=True))
        elif section == "vars":
            print(yaml.dump(info.get("variables", []), sort_keys=False, allow_unicode=True))
        return

    # Default: text output
    # Print metadata (only for 'all')
    if section == "all":
        print("\n==============================")
        print(f"Dataset ID: {info['dataset_id']} (Data Type: {info['cdm_data_type']})")
        print(f"Title: {info['title']}")
        print(f"Institution: {info['institution']}")
        print(f"Time Coverage: {info['time_coverage_start']} to {info['time_coverage_end']}")
        print(f"Summary: {info['summary']}")
        print("------------------------------")
        print(f"North/East/South/West:")
        print(f"  Northernmost: {info.get('nmost_northing', '')}")
        print(f"  Easternmost:  {info.get('emost_easting', '')}")
        print(f"  Southernmost: {info.get('smost_northing', '')}")
        print(f"  Westernmost:  {info.get('wmost_easting', '')}")
        print("==============================")

    # Print dimensions (for 'all' and 'dims')
    if section in ("all", "dims"):
        print("\n[Dimensions]")
        dims = info.get('dimensions', [])
        if dims:
            for dim in dims:
                _print_unified_block(dim, info)
        else:
            print("No dimensions found.")

    # Print variables (for 'all' and 'vars')
    if section in ("all", "vars"):
        print("\n[Variables]")
        vars_list = info.get('variables', [])
        if vars_list:
            for var in vars_list:
                _print_unified_block(var, info)
        else:
            print("No variables found.")

    # Data Access Facilitation Section
    if section == "all":
        print("\n==============================")
        print("Data Access Facilitation")
        print("------------------------------")

        # Get all variable names for the sample URL
        all_vars = [v['name'] for v in info.get('variables', [])]

        # Use the protocol variable you defined in Step 1
        # It's assumed to be available here, e.g., protocol = 'griddap' or 'tabledap'
        try:
            from erddap_cli.client.session import get_download_url
            url = get_download_url(
                args.server,
                args.dataset_id,
                all_vars,
                None,          # No constraints for sample
                "csv",
                protocol       # Use the determined protocol
            )
            print(f"Sample Download URL ({protocol}: All dimensions/variables, no constraints):\n  {url}")
        except Exception as e:
            print(f"Could not build sample download URL: {e}")

# --- Protocol-Specific Constraint Hints ---
        protocol_dims = info.get('dimensions', [])

        if protocol == 'griddap':
            if not protocol_dims:
                print("\nWarning: Griddap dataset has no dimensions listed.")
            else:
                print("\nConstraint Hints (Griddap Slicing):")
                for dim in protocol_dims:
                    spacing = dim.get('average_spacing')
                    name = dim.get('name', 'N/A')
                    is_time = name.lower() == 'time'
                    if is_time:
                        min_v = info.get('time_coverage_start', '')
                        max_v = info.get('time_coverage_end', '')
                    else:
                        min_v = str(dim.get('min', '')).rstrip(',')
                        max_v = str(dim.get('max', '')).rstrip(',')
                    try:
                        max_index = int(dim.get('nvalues', 1)) - 1
                    except (ValueError, TypeError):
                        max_index = "N/A"
                    print(f"- {name} (Data Spacing: {spacing})")
                    print(f"    Index Range Example: {name}[0:1:{max_index}]")
                    print(f"    Value Range Example: {name}[({min_v}):1:({max_v})]")
                    
            print(f"\nNOTE: Use the erddap-cli fetch command to interactively build and optionally fetch/save the output from an URL query.")

        else:  # Tabledap Logic
            all_vars = info.get('variables', [])
            hint_variables = []
            # Use a set to keep track of variable names we've already added
            # to avoid duplicates.
            added_names = set()

            # --- Pass 1: Add primary dimension-like variables first ---
            # This ensures they appear in the hints even if their min/max are the same.
            primary_dims = {'time', 'depth', 'altitude', 'latitude', 'longitude', 'lat', 'lon'}
            for var in all_vars:
                name = var.get('name', '').lower()
                if name in primary_dims:
                    hint_variables.append(var)
                    added_names.add(name)

            # --- Pass 2: Add other variables that have a usable numeric range ---
            for var in all_vars:
                name = var.get('name', '').lower()
                if name in added_names:
                    continue  # Skip if it was already added as a primary dimension

                min_v_str = str(var.get('min', '')).rstrip(',')
                max_v_str = str(var.get('max', '')).rstrip(',')

                # Check if both values exist and are different
                if min_v_str and max_v_str and min_v_str != max_v_str:
                    try:
                        # Ensure they are numbers before adding
                        float(min_v_str)
                        float(max_v_str)
                        hint_variables.append(var)
                        added_names.add(name)
                    except (ValueError, TypeError):
                        # It's not a numeric range, so we skip it
                        continue

            # --- Now, print the hints from our combined list ---
            if not hint_variables:
                print("\nNo variables with filterable ranges found.")
            else:
                print("\nConstraint Hints (Tabledap Filtering):")
                for var in hint_variables:
                    name = var.get('name', 'N/A')
                    units = var.get('units', 'N/A')
                    is_time = name.lower() == 'time'

                    if is_time:
                        # Use the global coverage for time for better formatting
                        min_v = info.get('time_coverage_start', '')
                        max_v = info.get('time_coverage_end', '')
                    else:
                        min_v = str(var.get('min', '')).rstrip(',')
                        max_v = str(var.get('max', '')).rstrip(',')

                    print(f"- {name} (Units: {units})")
                    print(f"    Example: {name}>={min_v}&{name}<={max_v}")
                    if min_v and max_v and min_v == max_v:
                        print(f"    NOTE: No min/max delta detected. No constraint specification required.")
                        
            print(f"\nNOTE: Use the erddap-cli fetch command to interactively build and optionally fetch/save the output from an URL query.")

    # # --- Data Access Facilitation ---
    # if section == "all":
        # from erddap_cli.client.session import get_download_url
        # print("\n--- Data Access Facilitation ---")
        # # Sample download URL (all variables, no constraints)
        # all_var_names = [v['name'] for v in info.get('variables', [])]
        # try:
            # url = get_download_url(
                # args.server,
                # args.dataset_id,
                # all_var_names if all_var_names else None,
                # None,
                # "csv",
                # "grid" if info['cdm_data_type'].lower() == "grid" else "tabledap"
            # )
            # print(f"\nSample Download URL (all variables, no constraints):\n{url}")
        # except Exception as e:
            # print(f"\nCould not build sample download URL: {e}")

        # # Constraint hints
        # dims = info.get('dimensions', [])
        # if dims:
            # print("\nConstraint Hints:")
            # for dim in dims:
                # name = dim.get('name', 'N/A')
                # is_time = name.lower() == 'time'
                # if is_time:
                    # min_v = {info['time_coverage_start']}
                    # max_v = {info['time_coverage_end']}
                # else:
                    # min_v = dim.get('min', '')
                    # max_v = dim.get('max', '')
                # dtype = dim.get('data_type', '')
                # print(f"- {name} (type: {dtype}, min: {min_v}, max: {max_v})")
                # print(f"    Example: {name}>={min_v}&{name}<={max_v}")
        # else:
            # print("No dimensions available for constraints.")