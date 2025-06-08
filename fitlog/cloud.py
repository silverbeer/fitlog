"""
Cloud client for fitlog API v2.

Provides the same interface as the local Database class but communicates
with the cloud API using authentication.
"""

import os
from datetime import datetime

import requests
from dotenv import load_dotenv

from .models import Pushup, Run

# Load environment variables
load_dotenv()


class CloudClient:
    """Cloud client that mirrors the Database interface for seamless CLI integration."""

    def __init__(self, debug: bool = False):
        self.debug = debug

        # Get configuration from environment variables
        self.base_url = os.getenv(
            "FITLOG_API_URL",
            "https://2054k0hh9j.execute-api.us-east-1.amazonaws.com/dev",
        )
        self.api_key = os.getenv("FITLOG_API_KEY")

        if not self.api_key:
            raise ValueError(
                "FITLOG_API_KEY environment variable is required. "
                "Set it to your API key: fitlog_z-e8yE_lWLIZAkRcKy6AVW5ZaJJ3qmaGS5eFVZjtnHw"
            )

        # Setup headers for authenticated requests
        self.headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

        if self.debug:
            print(f"CloudClient initialized with API URL: {self.base_url}")

    def _make_request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """Make an authenticated request to the API."""
        url = f"{self.base_url}{endpoint}"

        if self.debug:
            print(f"Making {method} request to {url}")
            if data:
                print(f"Request data: {data}")

        try:
            response = requests.request(
                method=method, url=url, headers=self.headers, json=data, timeout=30
            )

            if self.debug:
                print(f"Response status: {response.status_code}")

            response.raise_for_status()

            result = response.json()
            if self.debug:
                print(f"Response data: {result}")

            return result

        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_detail = e.response.json().get("detail", str(e))
                    error_msg = f"API error: {error_detail}"
                except Exception:
                    error_msg = f"API error (status {e.response.status_code}): {str(e)}"

            if self.debug:
                print(f"Request error: {error_msg}")
            raise Exception(error_msg)

    def log_run(self, run: Run, debug: bool = None):
        """Log a run to the cloud API."""
        if debug is None:
            debug = self.debug

        # Convert Run object to API format
        run_data = {
            "duration": str(run.duration),  # Convert time to HH:MM:SS string
            "distance": run.distance_miles,
            "date": (
                run.date.strftime("%m/%d/%y")
                if run.date != datetime.now().date()
                else None
            ),
        }

        if debug:
            print(f"Logging run: {run_data}")

        response = self._make_request("POST", "/runs", run_data)

        if debug:
            print("Run logged successfully to cloud")

        return response

    def log_pushups(self, pushup: Pushup):
        """Log pushups to the cloud API."""
        pushup_data = {
            "count": pushup.count,
            "date": (
                pushup.date.strftime("%m/%d/%y")
                if pushup.date != datetime.now().date()
                else None
            ),
        }

        if self.debug:
            print(f"Logging pushups: {pushup_data}")

        response = self._make_request("POST", "/pushups", pushup_data)

        if self.debug:
            print("Pushups logged successfully to cloud")

        return response

    def get_runs(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        debug: bool = None,
    ) -> list[Run]:
        """Get runs from the cloud API."""
        if debug is None:
            debug = self.debug

        # Build query parameters
        params = {}
        if start_date:
            params["start_date"] = start_date.strftime("%Y-%m-%d")
        if end_date:
            params["end_date"] = end_date.strftime("%Y-%m-%d")

        # Add params to URL
        endpoint = "/runs"
        if params:
            param_str = "&".join([f"{k}={v}" for k, v in params.items()])
            endpoint += f"?{param_str}"

        if debug:
            print(f"Getting runs from cloud API: {endpoint}")

        response = self._make_request("GET", endpoint)

        # Convert API response to Run objects
        runs = []
        for run_data in response:
            run = Run(
                activity_id=run_data.get("activity_id"),
                date=run_data["date"],
                duration=run_data["duration"],
                distance_miles=run_data["distance_miles"],
                pace_per_mile=run_data.get("pace_per_mile"),
                heart_rate_avg=run_data.get("heart_rate_avg"),
                heart_rate_max=run_data.get("heart_rate_max"),
                heart_rate_min=run_data.get("heart_rate_min"),
                cadence_avg=run_data.get("cadence_avg"),
                cadence_max=run_data.get("cadence_max"),
                cadence_min=run_data.get("cadence_min"),
                temperature=run_data.get("temperature"),
                weather_type=run_data.get("weather_type"),
                humidity=run_data.get("humidity"),
                wind_speed=run_data.get("wind_speed"),
            )

            # Handle splits if available
            if "splits" in run_data and run_data["splits"]:
                # Convert splits data to Split objects
                from .models import Split

                run.splits = [
                    Split(
                        mile_number=split["mile_number"],
                        duration=split["duration"],
                        pace=split["pace"],
                        heart_rate_avg=split.get("heart_rate_avg"),
                        cadence_avg=split.get("cadence_avg"),
                    )
                    for split in run_data["splits"]
                ]

            runs.append(run)

        if debug:
            print(f"Retrieved {len(runs)} runs from cloud")

        return runs

    def get_pushups(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        debug: bool = None,
    ) -> list[Pushup]:
        """Get pushups from the cloud API."""
        if debug is None:
            debug = self.debug

        # Build query parameters
        params = {}
        if start_date:
            params["start_date"] = start_date.strftime("%Y-%m-%d")
        if end_date:
            params["end_date"] = end_date.strftime("%Y-%m-%d")

        # Add params to URL
        endpoint = "/pushups"
        if params:
            param_str = "&".join([f"{k}={v}" for k, v in params.items()])
            endpoint += f"?{param_str}"

        if debug:
            print(f"Getting pushups from cloud API: {endpoint}")

        response = self._make_request("GET", endpoint)

        # Convert API response to Pushup objects
        pushups = []
        for pushup_data in response:
            pushup = Pushup(
                date=pushup_data["date"],
                count=pushup_data["count"],
            )
            pushups.append(pushup)

        if debug:
            print(f"Retrieved {len(pushups)} pushups from cloud")

        return pushups

    def get_stats(self, days: int = 30, debug: bool = None):
        """Get activity statistics from the cloud API."""
        if debug is None:
            debug = self.debug

        endpoint = f"/activities/status?days={days}"

        if debug:
            print(f"Getting stats from cloud API: {endpoint}")

        response = self._make_request("GET", endpoint)

        # Extract stats from response
        stats = response.get("stats", {})

        if debug:
            print(f"Retrieved stats: {stats}")

        return stats

    # Methods that don't apply to cloud client but are part of Database interface
    def drop_tables(self):
        """Not applicable for cloud client."""
        raise NotImplementedError("drop_tables() not supported for cloud client")

    def _create_tables(self):
        """Not applicable for cloud client."""
        pass

    def _tables_exist(self) -> bool:
        """Not applicable for cloud client - always return True."""
        return True
