"""Configuration management for Slack KPI Integration."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration."""

    slack_bot_token: str
    slack_workspace: str
    google_spreadsheet_id: str
    google_credentials_file: str

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        load_dotenv()

        return cls(
            slack_bot_token=os.getenv("SLACK_BOT_TOKEN", ""),
            slack_workspace=os.getenv("SLACK_WORKSPACE", "martial-arts-ghd"),
            google_spreadsheet_id=os.getenv(
                "GOOGLE_SPREADSHEET_ID",
                "1-2FD8zY5lCPudym8GYo7faYpT7U0ok7YqhV9WX8IfKc"
            ),
            google_credentials_file=os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json"),
        )

    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []

        if not self.slack_bot_token:
            errors.append("SLACK_BOT_TOKEN is required")

        if not self.google_spreadsheet_id:
            errors.append("GOOGLE_SPREADSHEET_ID is required")

        if not os.path.exists(self.google_credentials_file):
            errors.append(f"Google credentials file not found: {self.google_credentials_file}")

        return errors
