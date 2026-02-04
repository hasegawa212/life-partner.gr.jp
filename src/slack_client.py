"""Slack API client for extracting KPI data from channels."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


@dataclass
class KPIMessage:
    """Represents a KPI message from Slack."""

    channel_id: str
    channel_name: str
    user_name: str
    timestamp: datetime
    text: str
    kpi_values: dict[str, str]


@dataclass
class ChannelInfo:
    """Represents a Slack channel."""

    id: str
    name: str
    is_private: bool


class SlackKPIClient:
    """Client for extracting KPI data from Slack channels."""

    # Pattern to match individual channels (個人_名前 format)
    INDIVIDUAL_CHANNEL_PATTERN = re.compile(r"^個人_(.+)$")

    def __init__(self, bot_token: str):
        """Initialize the Slack client.

        Args:
            bot_token: Slack Bot OAuth token
        """
        self.client = WebClient(token=bot_token)
        self._channel_cache: dict[str, ChannelInfo] = {}

    def test_connection(self) -> bool:
        """Test the Slack API connection.

        Returns:
            True if connection is successful
        """
        try:
            response = self.client.auth_test()
            print(f"Connected to Slack workspace: {response['team']}")
            return True
        except SlackApiError as e:
            print(f"Failed to connect to Slack: {e.response['error']}")
            return False

    def get_all_channels(self, include_private: bool = True) -> list[ChannelInfo]:
        """Get all channels in the workspace.

        Args:
            include_private: Whether to include private channels

        Returns:
            List of channel information
        """
        channels = []

        try:
            # Get public channels
            cursor = None
            while True:
                response = self.client.conversations_list(
                    types="public_channel,private_channel" if include_private else "public_channel",
                    limit=200,
                    cursor=cursor
                )

                for channel in response["channels"]:
                    info = ChannelInfo(
                        id=channel["id"],
                        name=channel["name"],
                        is_private=channel.get("is_private", False)
                    )
                    channels.append(info)
                    self._channel_cache[channel["id"]] = info

                cursor = response.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break

        except SlackApiError as e:
            print(f"Error fetching channels: {e.response['error']}")

        return channels

    def get_individual_channels(self) -> list[ChannelInfo]:
        """Get all individual KPI channels (個人_名前 format).

        Returns:
            List of individual channel information
        """
        all_channels = self.get_all_channels()
        individual_channels = []

        for channel in all_channels:
            if self.INDIVIDUAL_CHANNEL_PATTERN.match(channel.name):
                individual_channels.append(channel)

        return individual_channels

    def extract_person_name(self, channel_name: str) -> Optional[str]:
        """Extract person name from channel name.

        Args:
            channel_name: Channel name in 個人_名前 format

        Returns:
            Person name or None if not matching pattern
        """
        match = self.INDIVIDUAL_CHANNEL_PATTERN.match(channel_name)
        if match:
            return match.group(1)
        return None

    def get_channel_messages(
        self,
        channel_id: str,
        limit: int = 100,
        oldest: Optional[datetime] = None,
        latest: Optional[datetime] = None
    ) -> list[dict]:
        """Get messages from a channel.

        Args:
            channel_id: Channel ID
            limit: Maximum number of messages to retrieve
            oldest: Only messages after this timestamp
            latest: Only messages before this timestamp

        Returns:
            List of message dictionaries
        """
        messages = []

        try:
            kwargs = {
                "channel": channel_id,
                "limit": min(limit, 200)
            }

            if oldest:
                kwargs["oldest"] = str(oldest.timestamp())
            if latest:
                kwargs["latest"] = str(latest.timestamp())

            cursor = None
            fetched = 0

            while fetched < limit:
                if cursor:
                    kwargs["cursor"] = cursor

                response = self.client.conversations_history(**kwargs)

                for msg in response["messages"]:
                    if fetched >= limit:
                        break
                    messages.append(msg)
                    fetched += 1

                cursor = response.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break

        except SlackApiError as e:
            print(f"Error fetching messages from channel {channel_id}: {e.response['error']}")

        return messages

    def parse_kpi_message(self, message: dict, channel_info: ChannelInfo) -> Optional[KPIMessage]:
        """Parse a message and extract KPI data.

        Args:
            message: Raw message dictionary from Slack
            channel_info: Channel information

        Returns:
            KPIMessage if KPI data found, None otherwise
        """
        text = message.get("text", "")

        # Extract KPI values using common patterns
        kpi_values = self._extract_kpi_values(text)

        if not kpi_values and not text.strip():
            return None

        timestamp = datetime.fromtimestamp(float(message.get("ts", 0)))
        person_name = self.extract_person_name(channel_info.name) or channel_info.name

        return KPIMessage(
            channel_id=channel_info.id,
            channel_name=channel_info.name,
            user_name=person_name,
            timestamp=timestamp,
            text=text,
            kpi_values=kpi_values
        )

    def _extract_kpi_values(self, text: str) -> dict[str, str]:
        """Extract KPI values from message text.

        Args:
            text: Message text

        Returns:
            Dictionary of KPI names to values
        """
        kpi_values = {}

        # Common KPI patterns
        patterns = [
            # Pattern: "KPI名: 値" or "KPI名：値"
            (r"([^\s:：]+)[:\s：]+(\d+(?:\.\d+)?(?:%|件|円|人|回)?)", r"\1", r"\2"),
            # Pattern: "【KPI名】値"
            (r"【([^】]+)】\s*(\d+(?:\.\d+)?(?:%|件|円|人|回)?)", r"\1", r"\2"),
            # Pattern with specific KPI keywords
            (r"(売上|契約|アポ|架電|面談|成約)[数件率]?\s*[:\s：]*(\d+(?:\.\d+)?(?:%|件|円|人|回)?)", r"\1", r"\2"),
        ]

        for pattern, _, _ in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    key, value = match[0], match[1]
                    kpi_values[key.strip()] = value.strip()

        return kpi_values

    def get_kpi_data_from_channel(
        self,
        channel_info: ChannelInfo,
        limit: int = 100
    ) -> list[KPIMessage]:
        """Get all KPI data from a channel.

        Args:
            channel_info: Channel information
            limit: Maximum number of messages to process

        Returns:
            List of KPI messages
        """
        messages = self.get_channel_messages(channel_info.id, limit=limit)
        kpi_messages = []

        for msg in messages:
            kpi_msg = self.parse_kpi_message(msg, channel_info)
            if kpi_msg:
                kpi_messages.append(kpi_msg)

        return kpi_messages

    def get_all_individual_kpi_data(self, message_limit: int = 100) -> dict[str, list[KPIMessage]]:
        """Get KPI data from all individual channels.

        Args:
            message_limit: Maximum messages per channel

        Returns:
            Dictionary mapping person names to their KPI messages
        """
        individual_channels = self.get_individual_channels()
        all_kpi_data = {}

        print(f"Found {len(individual_channels)} individual channels")

        for channel in individual_channels:
            person_name = self.extract_person_name(channel.name)
            if person_name:
                print(f"Processing channel: {channel.name}")
                kpi_messages = self.get_kpi_data_from_channel(channel, limit=message_limit)
                all_kpi_data[person_name] = kpi_messages
                print(f"  Found {len(kpi_messages)} messages")

        return all_kpi_data
