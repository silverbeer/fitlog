import os
from datetime import UTC, datetime, time, timedelta

import requests
from dotenv import load_dotenv, set_key
from rich import print

from .models import Run, Split


class SmashrunClient:
    """Client for interacting with the Smashrun API."""

    BASE_URL = "https://api.smashrun.com/v1"
    AUTH_URL = "https://secure.smashrun.com/oauth2"

    def __init__(self, access_token: str = None, refresh_token: str = None):
        """Initialize the Smashrun client.

        Args:
            access_token: OAuth access token for Smashrun API
            refresh_token: OAuth refresh token for getting new access tokens
        """
        load_dotenv()

        self.access_token = access_token or os.getenv("SMASHRUN_ACCESS_TOKEN")
        self.refresh_token = refresh_token or os.getenv("SMASHRUN_REFRESH_TOKEN")
        self.client_id = os.getenv("SMASHRUN_CLIENT_ID")
        self.client_secret = os.getenv("SMASHRUN_CLIENT_SECRET")
        self.token_expires = os.getenv("SMASHRUN_TOKEN_EXPIRES")

        if not self.access_token:
            raise ValueError(
                "No access token provided. Set SMASHRUN_ACCESS_TOKEN in .env"
            )

        self.headers = self._get_headers()

    def _get_headers(self) -> dict:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }

    def _refresh_token(self) -> bool:
        """Refresh the access token using the refresh token.

        Returns:
            bool: True if token was refreshed successfully
        """
        if not self.refresh_token:
            print("[red]No refresh token available[/red]")
            return False

        if not (self.client_id and self.client_secret):
            print(
                "[red]Missing client credentials. Set SMASHRUN_CLIENT_ID and SMASHRUN_CLIENT_SECRET in .env[/red]"
            )
            return False

        try:
            response = requests.post(
                f"{self.AUTH_URL}/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            response.raise_for_status()
            token_data = response.json()

            # Update tokens and expiry
            self.access_token = token_data["access_token"]
            if "refresh_token" in token_data:
                self.refresh_token = token_data["refresh_token"]

            # Calculate expiry (12 weeks from now)
            expires = datetime.now(UTC) + timedelta(weeks=12)
            expires_str = expires.isoformat()

            # Update .env file
            env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
            set_key(env_path, "SMASHRUN_ACCESS_TOKEN", self.access_token)
            set_key(env_path, "SMASHRUN_REFRESH_TOKEN", self.refresh_token)
            set_key(env_path, "SMASHRUN_TOKEN_EXPIRES", expires_str)

            # Update headers with new token
            self.headers = self._get_headers()
            return True

        except Exception as e:
            print(f"[red]Failed to refresh token: {str(e)}[/red]")
            return False

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make an API request with automatic token refresh if needed.

        Args:
            method: HTTP method (get, post, etc)
            url: URL to request
            **kwargs: Additional arguments for requests

        Returns:
            Response object
        """
        try:
            response = requests.request(method, url, **kwargs)

            # If unauthorized and we have refresh capability, try refreshing token
            if response.status_code == 401 and self.refresh_token:
                print("[yellow]Token expired, attempting refresh...[/yellow]")
                if self._refresh_token():
                    # Update instance headers with new token
                    self.headers = self._get_headers()
                    # Update headers in kwargs if they exist
                    if "headers" in kwargs:
                        kwargs["headers"] = self.headers
                    # Retry request with new token
                    response = requests.request(method, url, **kwargs)

            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            print(f"[red]API request failed: {str(e)}[/red]")
            raise

    def get_detailed_run(self, activity_id: int) -> dict:
        """Fetch detailed data for a specific run including splits.

        Args:
            activity_id: The ID of the run to fetch

        Returns:
            Detailed run data including splits
        """
        url = f"{self.BASE_URL}/my/activities/{activity_id}"
        response = self._make_request("get", url, headers=self.headers)
        return response.json()

    def get_runs(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> list[Run]:
        """Fetch runs from Smashrun API.

        Args:
            start_date: Optional start date to filter runs
            end_date: Optional end date to filter runs

        Returns:
            List of Run objects
        """
        # Build the URL with optional date filters
        url = f"{self.BASE_URL}/my/activities/search"
        params = {}

        if start_date:
            # Convert to Unix timestamp (seconds since epoch)
            params["fromDateUTC"] = int(start_date.timestamp())
        if end_date:
            # Convert to Unix timestamp (seconds since epoch)
            params["toDateUTC"] = int(end_date.timestamp())

        print(
            f"[blue]Fetching runs from {start_date.strftime('%Y-%m-%d') if start_date else 'beginning'} to {end_date.strftime('%Y-%m-%d') if end_date else 'now'}[/blue]"
        )

        response = self._make_request("get", url, headers=self.headers, params=params)

        runs_data = response.json()
        if not runs_data:
            print("[yellow]No runs found in the specified date range[/yellow]")
            return []

        print(f"[green]Found {len(runs_data)} runs[/green]")

        # Debug: Print the first run's data structure
        if runs_data:
            print("\n[blue]Sample run data structure:[/blue]")
            print(runs_data[0])
            print("\n[blue]Available fields:[/blue]")
            print(list(runs_data[0].keys()))

            # Print the actual URL and parameters being used
            print("\n[blue]API Request:[/blue]")
            print(f"URL: {response.url}")
            print(f"Headers: {self.headers}")
            print(f"Params: {params}")

        # Try to parse the first run to see if it works
        if runs_data:
            print("\n[blue]Attempting to parse first run:[/blue]")
            first_run = self._parse_run(runs_data[0])
            if first_run:
                print("[green]Successfully parsed first run![/green]")
            else:
                print("[red]Failed to parse first run![/red]")

        return [
            parsed_run
            for run in runs_data
            if (parsed_run := self._parse_run(run)) is not None
        ]

    def _parse_run(self, run_data: dict) -> Run | None:
        """Parse a run from the Smashrun API response.

        Args:
            run_data: Run data from the API

        Returns:
            Run object
        """
        try:
            # Extract date and time in local time
            date_str = run_data.get("startDateTimeLocal")
            if not date_str:
                print(
                    f"[yellow]Warning: No local date found for run: {run_data}[/yellow]"
                )
                return None

            # Parse local date
            run_date = datetime.fromisoformat(date_str)

            # Extract duration (in seconds)
            duration_seconds = float(run_data.get("duration") or 0)
            if not duration_seconds:
                print(
                    f"[yellow]Warning: No duration found for run on {run_date}[/yellow]"
                )
                return None

            hours = int(duration_seconds // 3600)
            minutes = int((duration_seconds % 3600) // 60)
            seconds = int(duration_seconds % 60)
            duration = time(hour=hours, minute=minutes, second=seconds)

            # Extract distance (convert from kilometers/meters to miles)
            distance = float(run_data.get("distance") or 0)
            if not distance:
                print(
                    f"[yellow]Warning: No distance found for run on {run_date}[/yellow]"
                )
                return None

            # If distance is in meters (Garmin), convert to km first
            if distance > 1000:  # Assume if > 1000, it's in meters
                distance = distance / 1000
            distance_miles = distance * 0.621371

            # Create Run object with additional fields
            run = Run(
                activity_id=run_data.get("activityId"),
                date=run_date,
                duration=duration,
                distance_miles=distance_miles,
                heart_rate_avg=run_data.get("heartRateAverage"),
                heart_rate_max=run_data.get("heartRateMax"),
                heart_rate_min=run_data.get("heartRateMin"),
                cadence_avg=run_data.get("cadenceAverage"),
                cadence_max=run_data.get("cadenceMax"),
                cadence_min=run_data.get("cadenceMin"),
                temperature=run_data.get("temperature"),
                weather_type=run_data.get("weatherType"),
                humidity=run_data.get("humidity"),
                wind_speed=run_data.get("windSpeed"),
            )

            # Try to get detailed data including splits
            if run.activity_id:
                try:
                    detailed_data = self.get_detailed_run(run.activity_id)
                    if detailed_data and "splits" in detailed_data:
                        splits = []
                        for i, split_data in enumerate(detailed_data["splits"], 1):
                            # Parse split duration
                            split_duration_secs = float(split_data.get("duration") or 0)
                            split_mins = int(split_duration_secs // 60)
                            split_secs = int(split_duration_secs % 60)
                            split_duration = time(minute=split_mins, second=split_secs)

                            # Parse split pace
                            pace_secs = float(split_data.get("pace") or 0)
                            pace_mins = int(pace_secs // 60)
                            pace_secs = int(pace_secs % 60)
                            split_pace = time(minute=pace_mins, second=pace_secs)

                            splits.append(
                                Split(
                                    mile_number=i,
                                    duration=split_duration,
                                    pace=split_pace,
                                    heart_rate_avg=split_data.get("heartRate"),
                                    cadence_avg=split_data.get("cadence"),
                                )
                            )
                        run.splits = splits
                except Exception as e:
                    print(
                        f"[yellow]Warning: Could not fetch split data: {str(e)}[/yellow]"
                    )

            return run
        except Exception as e:
            print(f"[red]Error parsing run data: {run_data}[/red]")
            print(f"[red]Error details: {str(e)}[/red]")
            return None

    def get_user_info(self) -> dict:
        """Get information about the authenticated user.

        Returns:
            User information dictionary
        """
        url = f"{self.BASE_URL}/my/userinfo"
        response = self._make_request("get", url, headers=self.headers)
        return response.json()
