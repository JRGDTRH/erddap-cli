# erddap_cli/commands/search.py
import argparse
from erddap_cli.client.session import (
    build_search_url,
    search_datasets,
    get_total_count,
)

def setup_search_command(subparsers):
    parser = subparsers.add_parser(
        "search", help="Search datasets on an ERDDAP server."
    )
    parser.add_argument("--server", required=True, help="Base ERDDAP server URL")
    parser.add_argument("--query",  required=True, help="Search term")
    parser.add_argument("--page",            type=int,   default=1,  help="Page number")
    parser.add_argument("--items-per-page",  type=int,   default=25, help="Number of items per page")
    parser.add_argument("--min-lon",         type=float,           help="Minimum Longitude")
    parser.add_argument("--max-lon",         type=float,           help="Maximum Longitude")
    parser.add_argument("--min-lat",         type=float,           help="Minimum Latitude")
    parser.add_argument("--max-lat",         type=float,           help="Maximum Latitude")
    parser.add_argument("--min-time",        type=str,             help="Minimum Time (ISO format)")
    parser.add_argument("--max-time",        type=str,             help="Maximum Time (ISO format)")
    parser.add_argument(
        "--no-show-total", action="store_false", dest="show_total",
        help="Skip fetching total matching-dataset count"
    )
    parser.set_defaults(func=handle_search)

def handle_search(args):
    if args.show_total:
        total = get_total_count(
            args.server, args.query,
            min_lon=args.min_lon, max_lon=args.max_lon,
            min_lat=args.min_lat, max_lat=args.max_lat,
            min_time=args.min_time, max_time=args.max_time,
        )
        if total is not None:
            print(f"Found {total} datasets (showing page {args.page}, {args.items_per_page} items)")
        else:
            print("Could not determine total matching datasets.")

    results = search_datasets(
        args.server, args.query, args.page, args.items_per_page,
        min_lon=args.min_lon, max_lon=args.max_lon,
        min_lat=args.min_lat, max_lat=args.max_lat,
        min_time=args.min_time, max_time=args.max_time,
    )
    if not results:
        print("No datasets found.")
        return

    for item in results:
        did = item.get("Dataset ID") or item.get("dataset_id", "N/A")
        title = item.get("Title")    or item.get("title",     "N/A")
        print(f"- {did}: {title}")
