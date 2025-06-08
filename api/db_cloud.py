"""
Cloud database implementation for fitlog API using DuckDB with S3 backend.
"""

import os

# Import models from local fitlog package
import sys
import time
from datetime import UTC, datetime, timedelta

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

        if self.debug:
            print(f"Initializing CloudDatabase with path: {self.db_path}")

        # Initialize connection
        self.conn = self._connect()

    def _connect(self) -> duckdb.DuckDBPyConnection:
        """Establish connection to DuckDB with S3 backend."""
        max_retries = 3
        retry_delay = 1
        last_error = None

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    if self.debug:
                        print(f"Retry attempt {attempt + 1} of {max_retries}...")
                    time.sleep(retry_delay)

                if self.debug:
                    print(f"Connecting to DuckDB at {self.db_path}")

                # Create DuckDB connection with Lambda-compatible settings
                conn = duckdb.connect()

                # Set home directory for Lambda environment
                conn.execute("SET home_directory='/tmp';")
                if self.debug:
                    print("Set home directory to /tmp")

                # Configure S3 settings for AWS Lambda environment
                if self.db_path.startswith("s3://"):
                    if self.debug:
                        print("Configuring S3 settings for DuckDB...")

                    try:
                        # Install and load httpfs extension for S3 support
                        conn.execute("INSTALL httpfs;")
                        if self.debug:
                            print("✅ httpfs extension installed")
                    except Exception as e:
                        if self.debug:
                            print(f"httpfs install warning: {e}")
                        # Extension might already be available, continue

                    try:
                        conn.execute("LOAD httpfs;")
                        if self.debug:
                            print("✅ httpfs extension loaded")
                    except Exception as e:
                        if self.debug:
                            print(f"httpfs load warning: {e}")
                        # Extension might already be loaded, continue

                    # Use AWS credentials from Lambda environment
                    # Lambda automatically provides these via IAM role
                    region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
                    conn.execute(f"SET s3_region='{region}';")
                    if self.debug:
                        print(f"Set S3 region to {region}")

                    # For Lambda, we rely on IAM role credentials
                    # No need to set access keys explicitly

                if self.debug:
                    print("DuckDB connection established successfully")

                return conn

            except Exception as e:
                last_error = e
                if self.debug:
                    print(f"Connection attempt {attempt + 1} failed: {str(e)}")

                if attempt == max_retries - 1:
                    raise Exception(
                        f"Could not connect to DuckDB after {max_retries} attempts: {str(e)}"
                    )

        raise Exception(f"Unexpected error in connection loop: {str(last_error)}")

    def _tables_exist(self) -> bool:
        """Check if the required tables exist in the database."""
        try:
            # For S3-hosted databases, we need to open the database file first
            if self.db_path.startswith("s3://"):
                # Try to access the S3 database and check tables
                result = self.conn.execute(
                    f"""
                    ATTACH '{self.db_path}' AS s3db;
                    SELECT count(*) FROM information_schema.tables
                    WHERE table_schema = 'main'
                    AND table_name IN ('runs', 'pushups', 'splits');
                """
                ).fetchone()
            else:
                result = self.conn.execute(
                    """
                    SELECT count(*) FROM information_schema.tables
                    WHERE table_name IN ('runs', 'pushups', 'splits')
                """
                ).fetchone()

            exists = result is not None and result[0] == 3
            if self.debug:
                print(
                    f"Tables exist check: {exists} (found {result[0] if result else 0} tables)"
                )
            return exists

        except Exception as e:
            if self.debug:
                print(f"Error checking tables: {str(e)}")
            # If we can't check tables, assume they exist (since we migrated the database)
            return True

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
            # For S3 databases, attach the database first
            if self.db_path.startswith("s3://"):
                self.conn.execute(f"ATTACH '{self.db_path}' AS s3db;")
                table_prefix = "s3db.main"
            else:
                table_prefix = ""

            # Build query
            query = f"""
                SELECT activity_id, date, duration, distance_miles, pace_per_mile,
                       heart_rate_avg, heart_rate_max, heart_rate_min,
                       cadence_avg, cadence_max, cadence_min,
                       temperature, weather_type, humidity, wind_speed
                FROM {table_prefix}.runs
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
            # Use the already attached database
            table_prefix = "s3db.main" if self.db_path.startswith("s3://") else ""

            query = f"""
                SELECT mile_number, duration, pace, heart_rate_avg, cadence_avg
                FROM {table_prefix}.splits
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
                # Use timestamp-based ID
                run.activity_id = int(datetime.now().timestamp() * 1000)

            # For S3 databases, attach the database first
            if self.db_path.startswith("s3://"):
                self.conn.execute(f"ATTACH '{self.db_path}' AS s3db;")
                table_prefix = "s3db.main"
            else:
                table_prefix = ""

            # Insert run data
            query = f"""
                INSERT INTO {table_prefix}.runs (
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
                    split_query = f"""
                        INSERT INTO {table_prefix}.splits (
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
            # For S3 databases, attach the database first
            if self.db_path.startswith("s3://"):
                self.conn.execute(f"ATTACH '{self.db_path}' AS s3db;")
                table_prefix = "s3db.main"
            else:
                table_prefix = ""

            query = f"SELECT date, count FROM {table_prefix}.pushups"
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
            # For S3 databases, attach the database first
            if self.db_path.startswith("s3://"):
                self.conn.execute(f"ATTACH '{self.db_path}' AS s3db;")
                table_prefix = "s3db.main"
            else:
                table_prefix = ""

            query = f"""
                INSERT INTO {table_prefix}.pushups (date, count)
                VALUES (?, ?)
            """

            self.conn.execute(
                query, [pushup.date.strftime("%Y-%m-%d %H:%M:%S"), pushup.count]
            )

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
