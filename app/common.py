"""Common helpers and utilities shared by examples."""

import argparse
import zeroconf

def add_log_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments to control logging to the parser."""
    parser.add_argument("--show-debug", help="Enable debug log", action="store_true")
    parser.add_argument(
        "--show-discovery-debug", help="Enable discovery debug log", action="store_true"
    )
    parser.add_argument(
        "--show-zeroconf-debug", help="Enable zeroconf debug log", action="store_true"
    )

def configure_logging(args: argparse.Namespace) -> None:
    """Configure logging according to command line arguments."""
    if args.show_debug:
        print("Debug log enabled")
    if args.show_discovery_debug:
        print("Discovery debug log enabled")
    if args.show_zeroconf_debug:
        print("Zeroconf version:", zeroconf.__version__)
        print("Zeroconf debug log enabled")
