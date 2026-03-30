"""Command-line interface for TickTick MCP server."""

from __future__ import annotations

import argparse
import logging
import os
import sys

from dotenv import load_dotenv

from .authenticate import main as auth_main
from .src.server import main as server_main


def check_auth_setup() -> bool:
    load_dotenv()
    return os.getenv("TICKTICK_ACCESS_TOKEN") is not None


def main() -> None:
    parser = argparse.ArgumentParser(description="TickTick MCP Server")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    run_parser = subparsers.add_parser("run", help="Run the TickTick MCP server")
    run_parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    subparsers.add_parser("auth", help="Authenticate with TickTick")

    args = parser.parse_args()

    if not args.command:
        args.command = "run"

    if args.command == "run" and not check_auth_setup():
        print(
            "\nAuthentication required!\n"
            "Run 'uv run -m ticktick_mcp.cli auth' to set up authentication.\n"
        )
        sys.exit(1)

    if args.command == "auth":
        sys.exit(auth_main())
    elif args.command == "run":
        log_level = logging.DEBUG if getattr(args, "debug", False) else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        try:
            server_main()
        except KeyboardInterrupt:
            print("Server stopped by user", file=sys.stderr)
            sys.exit(0)
        except Exception as e:
            print(f"Error starting server: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
