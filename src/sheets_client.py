"""Google Sheets API client for writing KPI data."""

import os
from typing import Any, Optional
from datetime import datetime

from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle


class GoogleSheetsClient:
    """Client for writing KPI data to Google Sheets."""

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    def __init__(self, spreadsheet_id: str, credentials_file: str):
        """Initialize the Google Sheets client.

        Args:
            spreadsheet_id: ID of the Google Spreadsheet
            credentials_file: Path to credentials JSON file
        """
        self.spreadsheet_id = spreadsheet_id
        self.credentials_file = credentials_file
        self.service = None
        self._creds = None

    def authenticate(self) -> bool:
        """Authenticate with Google Sheets API.

        Returns:
            True if authentication successful
        """
        try:
            creds = None
            token_file = "token.pickle"

            # Check for service account credentials
            if self.credentials_file.endswith(".json"):
                try:
                    # Try service account first
                    creds = ServiceAccountCredentials.from_service_account_file(
                        self.credentials_file, scopes=self.SCOPES
                    )
                    print("Authenticated using service account")
                except Exception:
                    # Fall back to OAuth flow
                    pass

            if not creds:
                # Try to load saved credentials
                if os.path.exists(token_file):
                    with open(token_file, "rb") as token:
                        creds = pickle.load(token)

                # If no valid credentials, do OAuth flow
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                    else:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.credentials_file, self.SCOPES
                        )
                        creds = flow.run_local_server(port=0)

                    # Save credentials
                    with open(token_file, "wb") as token:
                        pickle.dump(creds, token)

            self._creds = creds
            self.service = build("sheets", "v4", credentials=creds)
            print("Successfully connected to Google Sheets API")
            return True

        except Exception as e:
            print(f"Failed to authenticate with Google Sheets: {e}")
            return False

    def get_spreadsheet_info(self) -> Optional[dict]:
        """Get spreadsheet metadata.

        Returns:
            Spreadsheet metadata or None on error
        """
        try:
            result = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            return result
        except HttpError as e:
            print(f"Error getting spreadsheet info: {e}")
            return None

    def get_sheet_names(self) -> list[str]:
        """Get all sheet names in the spreadsheet.

        Returns:
            List of sheet names
        """
        info = self.get_spreadsheet_info()
        if not info:
            return []

        return [sheet["properties"]["title"] for sheet in info.get("sheets", [])]

    def create_sheet(self, sheet_name: str) -> bool:
        """Create a new sheet in the spreadsheet.

        Args:
            sheet_name: Name for the new sheet

        Returns:
            True if successful
        """
        try:
            request = {
                "requests": [{
                    "addSheet": {
                        "properties": {
                            "title": sheet_name
                        }
                    }
                }]
            }
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=request
            ).execute()
            print(f"Created sheet: {sheet_name}")
            return True
        except HttpError as e:
            if "already exists" in str(e):
                print(f"Sheet already exists: {sheet_name}")
                return True
            print(f"Error creating sheet: {e}")
            return False

    def clear_sheet(self, sheet_name: str) -> bool:
        """Clear all data from a sheet.

        Args:
            sheet_name: Name of the sheet to clear

        Returns:
            True if successful
        """
        try:
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!A:Z"
            ).execute()
            return True
        except HttpError as e:
            print(f"Error clearing sheet: {e}")
            return False

    def write_data(
        self,
        sheet_name: str,
        data: list[list[Any]],
        start_cell: str = "A1",
        clear_first: bool = False
    ) -> bool:
        """Write data to a sheet.

        Args:
            sheet_name: Name of the sheet
            data: 2D list of values to write
            start_cell: Starting cell (e.g., "A1")
            clear_first: Whether to clear the sheet first

        Returns:
            True if successful
        """
        try:
            if clear_first:
                self.clear_sheet(sheet_name)

            range_name = f"'{sheet_name}'!{start_cell}"
            body = {"values": data}

            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()

            updated_cells = result.get("updatedCells", 0)
            print(f"Updated {updated_cells} cells in {sheet_name}")
            return True

        except HttpError as e:
            print(f"Error writing data: {e}")
            return False

    def append_data(self, sheet_name: str, data: list[list[Any]]) -> bool:
        """Append data to the end of a sheet.

        Args:
            sheet_name: Name of the sheet
            data: 2D list of values to append

        Returns:
            True if successful
        """
        try:
            range_name = f"'{sheet_name}'!A:Z"
            body = {"values": data}

            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body
            ).execute()

            updates = result.get("updates", {})
            updated_rows = updates.get("updatedRows", 0)
            print(f"Appended {updated_rows} rows to {sheet_name}")
            return True

        except HttpError as e:
            print(f"Error appending data: {e}")
            return False

    def read_data(self, sheet_name: str, range_spec: str = "A:Z") -> list[list[Any]]:
        """Read data from a sheet.

        Args:
            sheet_name: Name of the sheet
            range_spec: Range to read (e.g., "A:Z" or "A1:D10")

        Returns:
            2D list of values
        """
        try:
            range_name = f"'{sheet_name}'!{range_spec}"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            return result.get("values", [])

        except HttpError as e:
            print(f"Error reading data: {e}")
            return []

    def format_header_row(self, sheet_name: str, sheet_id: int = 0) -> bool:
        """Format the header row with bold text and background color.

        Args:
            sheet_name: Name of the sheet
            sheet_id: Numeric ID of the sheet

        Returns:
            True if successful
        """
        try:
            requests = [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 1
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {
                                    "red": 0.9,
                                    "green": 0.9,
                                    "blue": 0.9
                                },
                                "textFormat": {
                                    "bold": True
                                }
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat)"
                    }
                },
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet_id,
                            "gridProperties": {
                                "frozenRowCount": 1
                            }
                        },
                        "fields": "gridProperties.frozenRowCount"
                    }
                }
            ]

            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={"requests": requests}
            ).execute()
            return True

        except HttpError as e:
            print(f"Error formatting header: {e}")
            return False

    def ensure_sheet_exists(self, sheet_name: str) -> bool:
        """Ensure a sheet exists, creating it if necessary.

        Args:
            sheet_name: Name of the sheet

        Returns:
            True if sheet exists or was created
        """
        existing_sheets = self.get_sheet_names()
        if sheet_name not in existing_sheets:
            return self.create_sheet(sheet_name)
        return True
