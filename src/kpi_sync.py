"""Main KPI synchronization logic."""

from datetime import datetime
from typing import Optional

from .slack_client import SlackKPIClient, KPIMessage, ChannelInfo
from .sheets_client import GoogleSheetsClient
from .config import Config


class KPISynchronizer:
    """Synchronizes KPI data from Slack to Google Sheets."""

    # Default sheet name for the overview
    OVERVIEW_SHEET = "KPI概要"
    DETAIL_SHEET_PREFIX = "詳細_"

    def __init__(self, config: Config):
        """Initialize the KPI synchronizer.

        Args:
            config: Application configuration
        """
        self.config = config
        self.slack_client = SlackKPIClient(config.slack_bot_token)
        self.sheets_client = GoogleSheetsClient(
            config.google_spreadsheet_id,
            config.google_credentials_file
        )

    def initialize(self) -> bool:
        """Initialize connections to both Slack and Google Sheets.

        Returns:
            True if both connections successful
        """
        print("Initializing Slack connection...")
        if not self.slack_client.test_connection():
            print("Failed to connect to Slack")
            return False

        print("Initializing Google Sheets connection...")
        if not self.sheets_client.authenticate():
            print("Failed to connect to Google Sheets")
            return False

        return True

    def sync_all_individual_kpi(
        self,
        message_limit: int = 100,
        create_detail_sheets: bool = True
    ) -> dict[str, int]:
        """Sync KPI data from all individual channels to Google Sheets.

        Args:
            message_limit: Maximum messages to fetch per channel
            create_detail_sheets: Whether to create individual detail sheets

        Returns:
            Dictionary with sync statistics
        """
        stats = {
            "channels_processed": 0,
            "messages_synced": 0,
            "errors": 0
        }

        print("\nFetching KPI data from Slack...")
        all_kpi_data = self.slack_client.get_all_individual_kpi_data(message_limit)

        if not all_kpi_data:
            print("No KPI data found")
            return stats

        # Prepare overview data
        overview_data = self._prepare_overview_data(all_kpi_data)

        # Write overview sheet
        print("\nWriting overview sheet...")
        self.sheets_client.ensure_sheet_exists(self.OVERVIEW_SHEET)
        if self.sheets_client.write_data(
            self.OVERVIEW_SHEET,
            overview_data,
            clear_first=True
        ):
            stats["channels_processed"] = len(all_kpi_data)

        # Create detail sheets for each person
        if create_detail_sheets:
            for person_name, messages in all_kpi_data.items():
                if messages:
                    detail_sheet_name = f"{self.DETAIL_SHEET_PREFIX}{person_name}"
                    detail_data = self._prepare_detail_data(person_name, messages)

                    self.sheets_client.ensure_sheet_exists(detail_sheet_name)
                    if self.sheets_client.write_data(
                        detail_sheet_name,
                        detail_data,
                        clear_first=True
                    ):
                        stats["messages_synced"] += len(messages)
                    else:
                        stats["errors"] += 1

        return stats

    def sync_specific_channels(
        self,
        channel_names: list[str],
        message_limit: int = 100
    ) -> dict[str, int]:
        """Sync KPI data from specific channels.

        Args:
            channel_names: List of channel names to sync
            message_limit: Maximum messages per channel

        Returns:
            Dictionary with sync statistics
        """
        stats = {
            "channels_processed": 0,
            "messages_synced": 0,
            "errors": 0
        }

        all_channels = self.slack_client.get_all_channels()
        channel_map = {ch.name: ch for ch in all_channels}

        kpi_data = {}

        for name in channel_names:
            if name in channel_map:
                channel = channel_map[name]
                print(f"Processing: {name}")
                messages = self.slack_client.get_kpi_data_from_channel(channel, message_limit)
                person_name = self.slack_client.extract_person_name(name) or name
                kpi_data[person_name] = messages
                stats["channels_processed"] += 1
            else:
                print(f"Channel not found: {name}")
                stats["errors"] += 1

        if kpi_data:
            overview_data = self._prepare_overview_data(kpi_data)
            self.sheets_client.ensure_sheet_exists(self.OVERVIEW_SHEET)
            self.sheets_client.write_data(
                self.OVERVIEW_SHEET,
                overview_data,
                clear_first=True
            )

            for person_name, messages in kpi_data.items():
                if messages:
                    stats["messages_synced"] += len(messages)

        return stats

    def _prepare_overview_data(
        self,
        kpi_data: dict[str, list[KPIMessage]]
    ) -> list[list[str]]:
        """Prepare overview data for the spreadsheet.

        Args:
            kpi_data: Dictionary of person names to KPI messages

        Returns:
            2D list for spreadsheet
        """
        # Header row
        headers = [
            "氏名",
            "チャンネル名",
            "メッセージ数",
            "最新メッセージ日時",
            "最新メッセージ内容",
            "同期日時"
        ]

        data = [headers]
        sync_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for person_name, messages in sorted(kpi_data.items()):
            if messages:
                latest_msg = max(messages, key=lambda m: m.timestamp)
                latest_time = latest_msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                # Truncate long messages
                latest_text = latest_msg.text[:200] + "..." if len(latest_msg.text) > 200 else latest_msg.text
            else:
                latest_time = "-"
                latest_text = "-"

            row = [
                person_name,
                f"個人_{person_name}",
                str(len(messages)),
                latest_time,
                latest_text,
                sync_time
            ]
            data.append(row)

        return data

    def _prepare_detail_data(
        self,
        person_name: str,
        messages: list[KPIMessage]
    ) -> list[list[str]]:
        """Prepare detail data for a person's sheet.

        Args:
            person_name: Name of the person
            messages: List of KPI messages

        Returns:
            2D list for spreadsheet
        """
        # Header row
        headers = [
            "日時",
            "メッセージ内容",
            "抽出KPI"
        ]

        data = [headers]

        # Sort messages by timestamp (newest first)
        sorted_messages = sorted(messages, key=lambda m: m.timestamp, reverse=True)

        for msg in sorted_messages:
            timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")

            # Format KPI values
            if msg.kpi_values:
                kpi_str = ", ".join(f"{k}: {v}" for k, v in msg.kpi_values.items())
            else:
                kpi_str = "-"

            row = [
                timestamp,
                msg.text,
                kpi_str
            ]
            data.append(row)

        return data

    def list_available_channels(self) -> list[ChannelInfo]:
        """List all available individual channels.

        Returns:
            List of channel information
        """
        return self.slack_client.get_individual_channels()

    def get_sync_status(self) -> dict:
        """Get the current sync status from Google Sheets.

        Returns:
            Dictionary with status information
        """
        status = {
            "last_sync": None,
            "channels_synced": 0,
            "total_messages": 0
        }

        try:
            data = self.sheets_client.read_data(self.OVERVIEW_SHEET)
            if len(data) > 1:
                status["channels_synced"] = len(data) - 1  # Exclude header
                # Get last sync time from first data row
                if len(data[1]) >= 6:
                    status["last_sync"] = data[1][5]
                # Sum message counts
                status["total_messages"] = sum(
                    int(row[2]) for row in data[1:] if len(row) > 2 and row[2].isdigit()
                )
        except Exception as e:
            print(f"Error getting sync status: {e}")

        return status
