#!/usr/bin/env python3
"""
Slack KPI Integration for Life Partner

This script syncs KPI data from Slack individual channels (個人_名前 format)
to a Google Spreadsheet for tracking and analysis.

Usage:
    python main.py [command] [options]

Commands:
    sync        Sync all individual KPI channels to Google Sheets
    list        List all available individual channels
    status      Show current sync status

Examples:
    python main.py sync
    python main.py sync --limit 50
    python main.py list
    python main.py status
"""

import argparse
import sys
from src.config import Config
from src.kpi_sync import KPISynchronizer


def cmd_sync(synchronizer: KPISynchronizer, args: argparse.Namespace) -> int:
    """Execute sync command."""
    print("Starting KPI synchronization...")
    print(f"Message limit per channel: {args.limit}")

    stats = synchronizer.sync_all_individual_kpi(
        message_limit=args.limit,
        create_detail_sheets=not args.no_details
    )

    print("\n" + "=" * 50)
    print("Sync completed!")
    print(f"  Channels processed: {stats['channels_processed']}")
    print(f"  Messages synced: {stats['messages_synced']}")
    print(f"  Errors: {stats['errors']}")
    print("=" * 50)

    return 0 if stats["errors"] == 0 else 1


def cmd_list(synchronizer: KPISynchronizer, args: argparse.Namespace) -> int:
    """Execute list command."""
    print("Fetching available individual channels...\n")

    channels = synchronizer.list_available_channels()

    if not channels:
        print("No individual channels found (個人_名前 format)")
        return 0

    print(f"Found {len(channels)} individual channels:")
    print("-" * 40)

    for channel in sorted(channels, key=lambda c: c.name):
        privacy = "🔒" if channel.is_private else "📢"
        person_name = synchronizer.slack_client.extract_person_name(channel.name)
        print(f"  {privacy} {channel.name} ({person_name})")

    return 0


def cmd_status(synchronizer: KPISynchronizer, args: argparse.Namespace) -> int:
    """Execute status command."""
    print("Fetching sync status...\n")

    status = synchronizer.get_sync_status()

    print("Current Sync Status:")
    print("-" * 40)
    print(f"  Last sync: {status['last_sync'] or 'Never'}")
    print(f"  Channels synced: {status['channels_synced']}")
    print(f"  Total messages: {status['total_messages']}")

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Slack KPI Integration - Sync Slack channel data to Google Sheets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync KPI data to Google Sheets")
    sync_parser.add_argument(
        "--limit", "-l",
        type=int,
        default=100,
        help="Maximum messages to fetch per channel (default: 100)"
    )
    sync_parser.add_argument(
        "--no-details",
        action="store_true",
        help="Skip creating individual detail sheets"
    )

    # List command
    subparsers.add_parser("list", help="List available individual channels")

    # Status command
    subparsers.add_parser("status", help="Show current sync status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Load configuration
    config = Config.from_env()
    errors = config.validate()

    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease check your .env file and credentials.")
        return 1

    # Initialize synchronizer
    synchronizer = KPISynchronizer(config)

    if not synchronizer.initialize():
        print("Failed to initialize connections")
        return 1

    # Execute command
    commands = {
        "sync": cmd_sync,
        "list": cmd_list,
        "status": cmd_status,
    }

    return commands[args.command](synchronizer, args)


if __name__ == "__main__":
    sys.exit(main())
