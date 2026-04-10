"""CLI entry point for netsight-ops.

Usage::

    netsight-ops list              # show registered services
    netsight-ops status            # running state of each
    netsight-ops serve api         # start a service
    netsight-ops serve mcp         # start runtime MCP
"""

from __future__ import annotations

import argparse
import sys


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="netsight-ops",
        description="NetSight runtime service platform",
    )
    sub = parser.add_subparsers(dest="command")

    # list
    sub.add_parser("list", help="List all registered services")

    # status
    sub.add_parser("status", help="Show running state of each service")

    # serve
    serve = sub.add_parser("serve", help="Start a service")
    serve.add_argument("service", help="Service name (e.g. api, mcp)")
    serve.add_argument("--host", default="0.0.0.0", help="Bind host (tcp services)")
    serve.add_argument("--port", type=int, default=8000, help="Bind port (tcp services)")

    return parser


def _run_list() -> int:
    from rich.console import Console
    from rich.table import Table

    from netsight_ops.registry import service_registry

    service_registry.ensure_loaded()

    services = service_registry.list()
    errors = service_registry.load_errors()

    if not services and not errors:
        print("No services registered.")
        return 0

    console = Console()
    table = Table(
        show_header=True,
        header_style="bold",
        title="Registered services",
        title_justify="left",
        expand=False,
    )
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Display", no_wrap=True)
    table.add_column("Transport", no_wrap=True)
    table.add_column("Version", style="dim", no_wrap=True)
    table.add_column("Status", no_wrap=True)

    for info in sorted(services, key=lambda s: s.name):
        table.add_row(
            info.name,
            info.display_name,
            info.transport,
            info.version,
            "[green]available[/green]",
        )

    for name in sorted(errors):
        exc = errors[name]
        table.add_row(
            name,
            "—",
            "—",
            "—",
            f"[bold red]LOAD_ERROR[/bold red]: {exc}",
        )

    console.print(table)
    return 0


def _run_serve(args: argparse.Namespace) -> int:
    from netsight_ops.registry import ServiceConfig, service_registry

    service_registry.ensure_loaded()

    name = args.service
    if not service_registry.has(name):
        available = [s.name for s in service_registry.list()]
        print(
            f"[error] Unknown service: {name!r}. "
            f"Available: {', '.join(available) or 'none'}",
            file=sys.stderr,
        )
        return 1

    info = service_registry.get(name)
    svc = info.factory()
    config = ServiceConfig(
        host=args.host,
        port=args.port,
        transport=info.transport,
    )
    print(f"Starting service '{info.display_name}' ({info.transport})...")
    try:
        svc.start(config=config)
    except KeyboardInterrupt:
        print("\nShutting down...")
        svc.stop()
    return 0


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "list":
        sys.exit(_run_list())
    elif args.command == "serve":
        sys.exit(_run_serve(args))
    elif args.command == "status":
        # Same as list for now — status tracking is a follow-up
        sys.exit(_run_list())
    else:
        parser.print_help()
        sys.exit(0)
