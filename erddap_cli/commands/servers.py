# erddap_cli/commands/servers.py

from erddap_cli.client.session import list_known_servers, add_custom_server, remove_custom_server
import requests


def setup_servers_command(subparsers):
    """
    Register the 'servers' subcommand and its subcommands.
    """
    parser = subparsers.add_parser(
        "servers",
        help="Manage ERDDAP server URLs (list/add/remove)."
    )
    servers_subparsers = parser.add_subparsers(dest="servers_command", required=False)

    # List
    parser.set_defaults(func=handle_servers)

    # Add
    add_parser = servers_subparsers.add_parser(
        "add",
        help="Add or update a custom ERDDAP server."
    )
    add_parser.add_argument("--name", required=True, help="Server name")
    add_parser.add_argument("--url", required=True, help="Server URL")
    add_parser.set_defaults(func=handle_servers_add)


    # Remove
    remove_parser = servers_subparsers.add_parser(
        "remove",
        help="Remove a custom ERDDAP server by name."
    )
    remove_parser.add_argument("--name", required=True, help="Server name to remove")
    remove_parser.set_defaults(func=handle_servers_remove)

    # Status
    status_parser = servers_subparsers.add_parser(
        "status",
        help="Check status and capabilities of all known ERDDAP servers."
    )
    status_parser.set_defaults(func=handle_servers_status)
    
def handle_servers_status(args):
    servers = list_known_servers()
    print("\nERDDAP Server Status:\n")
    for server in servers:
        name = server.get("name", "Unknown")
        url = server.get("url", "")
        base_url = url.rstrip("/")
        version_url = f"{base_url}/version"
        capabilities_url = f"{base_url}/info/index.html"
        try:
            resp = requests.get(version_url, timeout=5)
            if resp.status_code == 200:
                version = resp.text.strip()
            else:
                version = f"HTTP {resp.status_code}"
        except Exception as e:
            version = f"Error: {e}"
        try:
            cap_resp = requests.get(capabilities_url, timeout=5)
            if cap_resp.status_code == 200:
                capabilities = "OK"
            else:
                capabilities = f"HTTP {cap_resp.status_code}"
        except Exception as e:
            capabilities = f"Error: {e}"
        print(f"- {name}: {url}\n    Version: {version}\n    Capabilities: {capabilities}\n")


def handle_servers(args):
    """
    Handle the 'servers' command: print out each server name and URL.
    """
    servers = list_known_servers()
    print("\nKnown ERDDAP Servers:\n")
    for server in servers:
        name = server.get("name", "Unknown")
        url = server.get("url", "")
        print(f"- {name}: {url}")

def handle_servers_add(args):
    add_custom_server(args.name, args.url)
    print(f"Added/updated server: {args.name} -> {args.url}")

def handle_servers_remove(args):
    remove_custom_server(args.name)
    print(f"Removed server: {args.name}")
