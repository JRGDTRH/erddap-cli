import argparse
from erddap_cli.commands.search import setup_search_command
from erddap_cli.commands.servers import setup_servers_command
from erddap_cli.commands.describe import setup_describe_command
from erddap_cli.commands.fetch import setup_fetch_command

def main():
    parser = argparse.ArgumentParser(
        description="ERDDAP CLI - Query and download ERDDAP datasets from terminal."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Setup individual commands
    setup_search_command(subparsers)
    setup_servers_command(subparsers)
    setup_describe_command(subparsers)
    setup_fetch_command(subparsers)
    # future commands setup here

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()