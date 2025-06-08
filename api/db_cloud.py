"""
Cloud database implementation for fitlog API using DuckDB with S3 backend.
"""

import os

# Import models from local fitlog package
import sys
from datetime import UTC, datetime, timedelta

import boto3
import duckdb

sys.path.append("..")
from fitlog.models import Pushup, Run, Split


class CloudDatabase:
    """
    Cloud-compatible database implementation using DuckDB with S3 backend.

    This class adapts the local Database implementation to work with:
    - S3-hosted DuckDB files
    - Lambda environment constraints
    - Serverless execution model
    """

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.db_path = os.getenv("DUCKDB_PATH", "s3://fitlog-dev-data/fitlog.db")
        self.local_db_path = "/tmp/fitlog.db"

        if self.debug:
            print(f"Initializing CloudDatabase with path: {self.db_path}")

        # Download database from S3 if needed
        if self.db_path.startswith("s3://"):
            self._download_db_from_s3()

        # Initialize connection to local file
        self.conn = self._connect()

    def _download_db_from_s3(self):
        """Download the database file from S3 to local temp storage."""
        try:
            if self.debug:
                print(
                    f"Downloading database from {self.db_path} to {self.local_db_path}"
                )

            # Parse S3 URL
            s3_url = self.db_path.replace("s3://", "")
            bucket, key = s3_url.split("/", 1)

            # Use boto3 to download the file
            s3_client = boto3.client("s3")
            s3_client.download_file(bucket, key, self.local_db_path)

            if self.debug:
                file_size = os.path.getsize(self.local_db_path)
                print(f"✅ Database downloaded successfully ({file_size} bytes)")

        except Exception as e:
            if self.debug:
                print(f"Error downloading database: {str(e)}")
            raise Exception(f"Failed to download database from S3: {str(e)}")

    def _upload_db_to_s3(self):
        """Upload the local database file back to S3."""
        try:
            if self.debug:
                print(f"Uploading database from {self.local_db_path} to {self.db_path}")

            # Parse S3 URL
            s3_url = self.db_path.replace("s3://", "")
            bucket, key = s3_url.split("/", 1)

            # Use boto3 to upload the file
            s3_client = boto3.client("s3")
            s3_client.upload_file(self.local_db_path, bucket, key)

            if self.debug:
                print("✅ Database uploaded successfully to S3")

        except Exception as e:
            if self.debug:
                print(f"Error uploading database: {str(e)}")
            raise Exception(f"Failed to upload database to S3: {str(e)}")

    def _connect(self) -> duckdb.DuckDBPyConnection:
        """Establish connection to local DuckDB file."""
        try:
            if self.debug:
                print(f"Connecting to local DuckDB at {self.local_db_path}")

            # Connect to the local database file
            conn = duckdb.connect(self.local_db_path)

            if self.debug:
                print("DuckDB connection established successfully")

            return conn

        except Exception as e:
            if self.debug:
                print(f"Connection failed: {str(e)}")
            raise Exception(f"Could not connect to DuckDB: {str(e)}")

    def get_runs(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[Run]:
        """
        Get runs from the database with optional date filtering.
        """
        if self.debug:
            print(
                f"Getting runs: start_date={start_date}, end_date={end_date}, limit={limit}"
            )

        try:
            # Build query for local database
            query = """
                SELECT activity_id, date, duration, distance_miles, pace_per_mile,
                       heart_rate_avg, heart_rate_max, heart_rate_min,
                       cadence_avg, cadence_max, cadence_min,
                       temperature, weather_type, humidity, wind_speed
                FROM runs
            """

            params = []
            conditions = []

            if start_date:
                if start_date.tzinfo is None:
                    start_date = start_date.replace(tzinfo=UTC)
                conditions.append("substr(date, 1, 10) >= ?")
                params.append(start_date.strftime("%Y-%m-%d"))

            if end_date:
                if end_date.tzinfo is None:
                    end_date = end_date.replace(tzinfo=UTC)
                conditions.append("substr(date, 1, 10) <= ?")
                params.append(end_date.strftime("%Y-%m-%d"))

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += f" ORDER BY date DESC LIMIT {limit}"

            if self.debug:
                print(f"Executing query: {query}")
                print(f"With params: {params}")

            result = self.conn.execute(query, params).fetchall()
            if self.debug:
                print(f"Found {len(result)} runs")

            runs = []
            for r in result:
                # Create run object
                run = Run(
                    activity_id=r[0],
                    date=r[1],
                    duration=r[2],
                    distance_miles=r[3],
                    pace_per_mile=r[4],
                    heart_rate_avg=r[5],
                    heart_rate_max=r[6],
                    heart_rate_min=r[7],
                    cadence_avg=r[8],
                    cadence_max=r[9],
                    cadence_min=r[10],
                    temperature=r[11],
                    weather_type=r[12],
                    humidity=r[13],
                    wind_speed=r[14],
                )

                # Get splits for this run
                if r[0]:  # If we have an activity_id
                    run.splits = self._get_splits_for_run(r[0])

                runs.append(run)

            return runs

        except Exception as e:
            if self.debug:
                print(f"Error getting runs: {str(e)}")
            raise Exception(f"Failed to get runs: {str(e)}")

    def _get_splits_for_run(self, activity_id: int) -> list[Split]:
        """Get splits for a specific run."""
        try:
            query = """
                SELECT mile_number, duration, pace, heart_rate_avg, cadence_avg
                FROM splits
                WHERE activity_id = ?
                ORDER BY mile_number
            """

            result = self.conn.execute(query, [activity_id]).fetchall()

            return [
                Split(
                    mile_number=s[0],
                    duration=s[1],
                    pace=s[2],
                    heart_rate_avg=s[3],
                    cadence_avg=s[4],
                )
                for s in result
            ]

        except Exception as e:
            if self.debug:
                print(f"Error getting splits for run {activity_id}: {str(e)}")
            return []

    def create_run(self, run: Run) -> Run:
        """Create a new run in the database."""
        if self.debug:
            print(
                f"Creating run: activity_id={run.activity_id}, date={run.date}, distance={run.distance_miles}"
            )

        try:
            # Generate activity_id if not provided
            if not run.activity_id:
                # Use a smaller ID that fits in INT32 range
                # Use seconds since epoch (not milliseconds) to keep it smaller
                run.activity_id = int(datetime.now().timestamp())

            # Insert run data
            query = """
                INSERT INTO runs (
                    activity_id, date, duration, distance_miles, pace_per_mile,
                    heart_rate_avg, heart_rate_max, heart_rate_min,
                    cadence_avg, cadence_max, cadence_min,
                    temperature, weather_type, humidity, wind_speed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            self.conn.execute(
                query,
                [
                    run.activity_id,
                    run.date.strftime("%Y-%m-%d %H:%M:%S"),
                    run.duration,
                    run.distance_miles,
                    run.pace_per_mile,
                    run.heart_rate_avg,
                    run.heart_rate_max,
                    run.heart_rate_min,
                    run.cadence_avg,
                    run.cadence_max,
                    run.cadence_min,
                    run.temperature,
                    run.weather_type,
                    run.humidity,
                    run.wind_speed,
                ],
            )

            # Insert splits if available
            if run.splits:
                for split in run.splits:
                    split_query = """
                        INSERT INTO splits (
                            activity_id, mile_number, duration, pace,
                            heart_rate_avg, cadence_avg
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """

                    self.conn.execute(
                        split_query,
                        [
                            run.activity_id,
                            split.mile_number,
                            split.duration,
                            split.pace,
                            split.heart_rate_avg,
                            split.cadence_avg,
                        ],
                    )

            # Upload the updated database back to S3
            if self.db_path.startswith("s3://"):
                self._upload_db_to_s3()

            if self.debug:
                print(f"Run created successfully with ID: {run.activity_id}")

            return run

        except Exception as e:
            if self.debug:
                print(f"Error creating run: {str(e)}")
            raise Exception(f"Failed to create run: {str(e)}")

    def get_pushups(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[Pushup]:
        """Get pushups from the database with optional date filtering."""
        if self.debug:
            print(
                f"Getting pushups: start_date={start_date}, end_date={end_date}, limit={limit}"
            )

        try:
            query = "SELECT date, count FROM pushups"
            params = []
            conditions = []

            if start_date:
                conditions.append("substr(date, 1, 10) >= ?")
                params.append(start_date.strftime("%Y-%m-%d"))

            if end_date:
                conditions.append("substr(date, 1, 10) <= ?")
                params.append(end_date.strftime("%Y-%m-%d"))

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += f" ORDER BY date DESC LIMIT {limit}"

            result = self.conn.execute(query, params).fetchall()
            if self.debug:
                print(f"Found {len(result)} pushup entries")

            return [Pushup(date=p[0], count=p[1]) for p in result]

        except Exception as e:
            if self.debug:
                print(f"Error getting pushups: {str(e)}")
            raise Exception(f"Failed to get pushups: {str(e)}")

    def create_pushup(self, pushup: Pushup) -> Pushup:
        """Create a new pushup entry in the database."""
        if self.debug:
            print(f"Creating pushup: date={pushup.date}, count={pushup.count}")

        try:
            query = """
                INSERT INTO pushups (date, count)
                VALUES (?, ?)
            """

            self.conn.execute(
                query, [pushup.date.strftime("%Y-%m-%d %H:%M:%S"), pushup.count]
            )

            # Upload the updated database back to S3
            if self.db_path.startswith("s3://"):
                self._upload_db_to_s3()

            if self.debug:
                print("Pushup created successfully")

            return pushup

        except Exception as e:
            if self.debug:
                print(f"Error creating pushup: {str(e)}")
            raise Exception(f"Failed to create pushup: {str(e)}")

    def get_stats(self, days: int = 30) -> dict:
        """Get activity statistics for the specified number of days."""
        if self.debug:
            print(f"Getting stats for last {days} days")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        try:
            runs = self.get_runs(start_date, end_date)
            pushups = self.get_pushups(start_date, end_date)

            stats = {
                "runs": {
                    "total": len(runs),
                    "total_distance": sum(r.distance_miles for r in runs),
                    "avg_distance": (
                        sum(r.distance_miles for r in runs) / len(runs) if runs else 0
                    ),
                },
                "pushups": {
                    "total": len(pushups),
                    "total_count": sum(p.count for p in pushups),
                    "avg_count": (
                        sum(p.count for p in pushups) / len(pushups) if pushups else 0
                    ),
                },
                "period": {
                    "days": days,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
            }

            if self.debug:
                print(f"Stats calculated: {stats}")

            return stats

        except Exception as e:
            if self.debug:
                print(f"Error getting stats: {str(e)}")
            raise Exception(f"Failed to get stats: {str(e)}")

    def close(self):
        """Close the database connection."""
        if hasattr(self, "conn") and self.conn:
            self.conn.close()
            if self.debug:
                print("Database connection closed")
