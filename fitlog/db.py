import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import duckdb

from .models import Pushup, Run, Split


class Database:
    def __init__(
        self,
        db_path: str = "data/fitlog.db",
        read_only: bool = False,
        debug: bool = False,
    ):
        self.db_path = db_path
        self.debug = debug

        # Ensure data directory exists
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        max_retries = 3
        retry_delay = 1  # seconds
        last_error = None

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"Retry attempt {attempt} of {max_retries}...")
                if self.debug:
                    print(f"Connecting to database at {db_path}")
                self.conn = duckdb.connect(db_path)
                # Only create tables if they don't exist
                if not self._tables_exist():
                    self._create_tables()
                    self.conn.commit()
                if self.debug:
                    print("Database initialized")
                return
            except duckdb.IOException as e:
                last_error = e
                if "Conflicting lock" in str(e):
                    if attempt < max_retries - 1:
                        print(f"Database is locked, waiting {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        continue
                    elif not read_only:
                        print("Failed to get write lock, trying read-only mode...")
                        break
                elif not read_only:
                    raise

        # If write access failed or read_only was requested, try read-only
        try:
            if self.debug:
                print(f"Connecting to database at {db_path} in read-only mode")
            self.conn = duckdb.connect(db_path, read_only=True)
            if self.debug:
                print("Database initialized in read-only mode")
        except Exception as e:
            raise Exception(
                f"Could not connect to database after {max_retries} attempts: {str(last_error or e)}\n"
                "Try closing any DuckDB shells or other programs that might be using the database."
            )

    def _tables_exist(self) -> bool:
        """Check if the required tables exist."""
        result = self.conn.execute(
            """
            SELECT count(*) FROM sqlite_master
            WHERE type='table' AND name IN ('runs', 'splits', 'pushups')
        """
        ).fetchone()[0]
        return result == 3

    def drop_tables(self):
        """Drop all tables in the correct order to respect foreign key constraints."""
        print("Dropping tables...")
        self.conn.execute("DROP TABLE IF EXISTS splits")
        print("Dropped splits table")
        self.conn.execute("DROP TABLE IF EXISTS runs")
        print("Dropped runs table")
        self.conn.execute("DROP TABLE IF EXISTS pushups")
        print("Dropped pushups table")

    def _create_tables(self):
        print("Creating tables...")

        # Create runs table with activity_id
        print("Creating runs table...")
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                activity_id INTEGER PRIMARY KEY,
                date VARCHAR,
                duration TIME,
                distance_miles DOUBLE,
                pace_per_mile TIME,
                heart_rate_avg INTEGER,
                heart_rate_max INTEGER,
                heart_rate_min INTEGER,
                cadence_avg INTEGER,
                cadence_max INTEGER,
                cadence_min INTEGER,
                temperature DOUBLE,
                weather_type VARCHAR,
                humidity DOUBLE,
                wind_speed DOUBLE
            )
        """
        )
        self.conn.commit()
        print("Created runs table")

        # Create splits table for per-mile data
        print("Creating splits table...")
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS splits (
                activity_id INTEGER,
                mile_number INTEGER,
                duration TIME,
                pace TIME,
                heart_rate_avg INTEGER,
                cadence_avg INTEGER,
                FOREIGN KEY (activity_id) REFERENCES runs(activity_id),
                PRIMARY KEY (activity_id, mile_number)
            )
        """
        )
        self.conn.commit()

        print("Created splits table")
        # Create pushups table
        self.conn.execute(
            """
            CREATE TABLE pushups (
                date VARCHAR,
                count INTEGER
            )
        """
        )
        print("Created pushups table")
        self.conn.commit()
        print("Tables committed")
        self.conn.commit()

    def log_run(self, run: Run, debug: bool = None):
        if debug is None:
            debug = self.debug
        if debug:
            print(
                f"Logging run: activity_id={run.activity_id}, date={run.date}, distance={run.distance_miles}"
            )
        # Insert or update run data
        self.conn.execute(
            """
            INSERT OR REPLACE INTO runs (
                activity_id, date, duration, distance_miles, pace_per_mile,
                heart_rate_avg, heart_rate_max, heart_rate_min,
                cadence_avg, cadence_max, cadence_min,
                temperature, weather_type, humidity, wind_speed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
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
        if debug:
            print("Run logged successfully")
        self.conn.commit()

        # Insert splits if available
        if run.splits:
            for split in run.splits:
                self.conn.execute(
                    """
                    INSERT OR REPLACE INTO splits (
                        activity_id, mile_number, duration, pace,
                        heart_rate_avg, cadence_avg
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                    [
                        run.activity_id,
                        split.mile_number,
                        split.duration,
                        split.pace,
                        split.heart_rate_avg,
                        split.cadence_avg,
                    ],
                )

        # Commit changes
        self.conn.commit()

    def log_pushups(self, pushup: Pushup):
        self.conn.execute(
            "INSERT INTO pushups (date, count) VALUES (?, ?)",
            [pushup.date.strftime("%Y-%m-%d %H:%M:%S"), pushup.count],
        )
        self.conn.commit()

    def get_runs(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        debug: bool = None,
    ) -> list[Run]:
        if debug is None:
            debug = self.debug
        # Get runs with all fields
        query = """
            SELECT activity_id, date, duration, distance_miles, pace_per_mile,
                   heart_rate_avg, heart_rate_max, heart_rate_min,
                   cadence_avg, cadence_max, cadence_min,
                   temperature, weather_type, humidity, wind_speed
            FROM runs
        """
        params = []

        if start_date or end_date:
            conditions = []
            if start_date:
                # Convert to UTC for comparison
                if start_date.tzinfo is None:
                    start_date = start_date.replace(tzinfo=UTC)
                conditions.append("substr(date, 1, 10) >= ?")
                params.append(start_date.strftime("%Y-%m-%d"))
                if debug:
                    print(f"Start date: {start_date.strftime('%Y-%m-%d')}")
            if end_date:
                # Convert to UTC for comparison
                if end_date.tzinfo is None:
                    end_date = end_date.replace(tzinfo=UTC)
                conditions.append("substr(date, 1, 10) <= ?")
                params.append(end_date.strftime("%Y-%m-%d"))
                if debug:
                    print(f"End date: {end_date.strftime('%Y-%m-%d')}")
            query += " WHERE " + " AND ".join(conditions)
            if debug:
                print(f"Query: {query}")
                print(f"Params: {params}")

        query += " ORDER BY date DESC"

        runs = []
        result = self.conn.execute(query, params).fetchall()

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
            splits_query = """
                SELECT mile_number, duration, pace, heart_rate_avg, cadence_avg
                FROM splits
                WHERE activity_id = ?
                ORDER BY mile_number
            """
            splits_result = self.conn.execute(
                splits_query, [run.activity_id]
            ).fetchall()

            # Add splits to run
            run.splits = [
                Split(
                    mile_number=s[0],
                    duration=s[1],
                    pace=s[2],
                    heart_rate_avg=s[3],
                    cadence_avg=s[4],
                )
                for s in splits_result
            ]

            runs.append(run)

        return runs

    def get_pushups(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        debug: bool = None,
    ) -> list[Pushup]:
        if debug is None:
            debug = self.debug
        query = "SELECT * FROM pushups"
        params = []

        if start_date or end_date:
            conditions = []
            if start_date:
                # Convert to string format for comparison with VARCHAR date column
                conditions.append("substr(date, 1, 10) >= ?")
                params.append(start_date.strftime("%Y-%m-%d"))
            if end_date:
                # Convert to string format for comparison with VARCHAR date column
                conditions.append("substr(date, 1, 10) <= ?")
                params.append(end_date.strftime("%Y-%m-%d"))
            query += " WHERE " + " AND ".join(conditions)
            if debug:
                print(f"Pushups Query: {query}")
                print(f"Pushups Params: {params}")

        query += " ORDER BY date DESC"

        result = self.conn.execute(query, params).fetchall()
        return [Pushup(date=p[0], count=p[1]) for p in result]

    def get_stats(self, days: int = 30, debug: bool = None):
        if debug is None:
            debug = self.debug
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        runs = self.get_runs(start_date, end_date, debug=debug)
        pushups = self.get_pushups(start_date, end_date, debug=debug)

        return {
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
        }
