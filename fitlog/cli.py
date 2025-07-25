import os
from datetime import datetime, time, timedelta

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table

from .config import (
    get_database_client,
    setup_cloud_mode,
    setup_local_mode,
    show_config,
)
from .models import Pushup, Run
from .renderer import (
    render_error,
    render_recent_activities,
    render_stats,
    render_success,
)
from .smashrun import SmashrunClient

console = Console()

# Load environment variables from .env file
load_dotenv()

app = typer.Typer()


@app.command()
def log_run(
    duration: str = typer.Option(..., help="Run duration in HH:MM:SS format"),
    distance: float = typer.Option(..., help="Distance in miles"),
    date: str | None = typer.Option(
        None, help="Date in MM/DD/YY format (default: today)"
    ),
    debug: bool = typer.Option(False, "--debug", help="Show debug output"),
):
    """Log a run with duration and distance."""
    try:
        # Get database client (local or cloud based on config)
        db = get_database_client()

        # Parse duration string to time object
        h, m, s = map(int, duration.split(":"))
        duration_time = time(hour=h, minute=m, second=s)

        # Parse date if provided
        run_date = datetime.now()
        if date:
            try:
                run_date = datetime.strptime(date, "%m/%d/%y")
            except ValueError:
                raise ValueError("Date must be in MM/DD/YY format")

        run = Run(date=run_date, duration=duration_time, distance_miles=distance)
        db.log_run(run, debug=debug)
        render_success(
            f"Logged run: {distance} miles in {duration} on {run_date.strftime('%A %m/%d/%y')}"
        )
    except Exception as e:
        render_error(str(e))


@app.command()
def log_pushups(
    count: int = typer.Option(..., help="Number of pushups"),
    date: str | None = typer.Option(
        None, help="Date in MM/DD/YY format (default: today)"
    ),
    debug: bool = typer.Option(False, "--debug", help="Show debug output"),
):
    """Log pushups."""
    try:
        # Get database client (local or cloud based on config)
        db = get_database_client()

        # Parse date if provided
        pushup_date = datetime.now()
        if date:
            try:
                pushup_date = datetime.strptime(date, "%m/%d/%y")
            except ValueError:
                raise ValueError("Date must be in MM/DD/YY format")

        pushup = Pushup(date=pushup_date, count=count)
        db.log_pushups(pushup)
        render_success(
            f"Logged {count} pushups on {pushup_date.strftime('%A %m/%d/%y')}"
        )
    except Exception as e:
        render_error(str(e))


@app.command()
def status(
    days: int = typer.Option(7, help="Number of days to show"),
    debug: bool = typer.Option(
        False, "--debug", help="Show debug output including database queries"
    ),
):
    """Show recent activities and statistics."""
    try:
        # Get database client (local or cloud based on config)
        db = get_database_client()

        # Get recent activities
        runs = db.get_runs(debug=debug)
        pushups = db.get_pushups(debug=debug)
        render_recent_activities(runs, pushups, days)

        # Get and show statistics
        stats = db.get_stats(debug=debug)
        render_stats(stats)
    except Exception as e:
        render_error(str(e))


@app.command()
def import_smashrun(
    access_token: str = typer.Option(
        os.getenv("SMASHRUN_ACCESS_TOKEN"),
        help="Smashrun API access token (can be set via SMASHRUN_ACCESS_TOKEN env var)",
    ),
    days: int = typer.Option(30, help="Number of days of history to import"),
):
    """Import runs from Smashrun API."""
    if not access_token:
        render_error(
            "No access token provided. Please set SMASHRUN_ACCESS_TOKEN environment variable or provide --access-token"
        )
        raise typer.Exit(1)

    try:
        # Initialize Smashrun client
        client = SmashrunClient(access_token)

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Fetch runs from Smashrun
        runs = client.get_runs(start_date, end_date)

        # Get database client and import runs
        db = get_database_client()
        imported_count = 0
        failed_count = 0
        for run in runs:
            if run is not None:
                db.log_run(run)
                imported_count += 1
            else:
                failed_count += 1

        if imported_count > 0:
            render_success(f"Imported {imported_count} runs from Smashrun")
        if failed_count > 0:
            render_error(f"Failed to import {failed_count} runs due to parsing errors")
    except Exception as e:
        render_error(f"Failed to import runs: {str(e)}")


@app.command()
def get_run(
    days: int = typer.Option(1, help="Number of days back to look for runs"),
    show_splits: bool = typer.Option(False, help="Show per-mile split information"),
    debug: bool = typer.Option(
        False, "--debug", help="Show debug output including database queries"
    ),
):
    """Get runs from the database."""
    try:
        # Get database client (local or cloud based on config)
        db = get_database_client()

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Get runs from database
        runs = db.get_runs(start_date, end_date, debug=debug)

        if not runs:
            render_error(f"No runs found in the last {days} day(s)")
            return

        # Create table to display runs
        table = Table(
            title=f"🏃 Runs from {start_date.strftime('%m/%d/%y')} to {end_date.strftime('%m/%d/%y')}"
        )
        table.add_column("Date", style="cyan")
        table.add_column("Distance (mi)", style="green", justify="right")
        table.add_column("Duration", style="blue", justify="right")
        table.add_column("Pace (/mi)", style="yellow", justify="right")
        table.add_column("HR", style="red", justify="right")
        table.add_column("Cadence", style="magenta", justify="right")
        table.add_column("Weather", style="white")

        for run in runs:
            weather_info = []
            if run.temperature is not None:
                weather_info.append(f"{run.temperature:.1f}°")
            if run.weather_type:
                weather_info.append(run.weather_type)
            if run.wind_speed:
                weather_info.append(f"{run.wind_speed}mph wind")

            table.add_row(
                run.date.strftime("%A %m/%d/%y %I:%M %p"),
                f"{run.distance_miles:.1f}",
                run.duration.strftime("%H:%M:%S"),
                run.pace_per_mile.strftime("%M:%S") if run.pace_per_mile else "-",
                f"{run.heart_rate_avg}" if run.heart_rate_avg else "-",
                f"{run.cadence_avg}" if run.cadence_avg else "-",
                ", ".join(weather_info) if weather_info else "-",
            )

        console.print(table)

        # Show splits if requested and available
    except Exception as e:
        render_error(str(e))


@app.command()
def report(
    days: int = typer.Option(
        7, help="Number of days to report on (7=week, 30=month, 365=year)"
    ),
    debug: bool = typer.Option(
        False, "--debug", help="Show debug output including database queries"
    ),
):
    """Show a summary report of your runs."""
    # Get database client (local or cloud based on config)
    report_db = get_database_client()

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    try:
        # Get runs in date range
        runs = report_db.get_runs(start_date, end_date, debug=debug)

        if not runs:
            console.print("[yellow]No runs found for the specified period[/yellow]")
            return

        # Calculate statistics
        total_runs = len(runs)
        total_miles = sum(run.distance_miles for run in runs)
        # Convert time to timedelta for total_seconds calculation
        pace_runs = [r for r in runs if r.pace_per_mile is not None]
        if pace_runs:
            avg_pace = sum(
                timedelta(
                    hours=r.pace_per_mile.hour,  # type: ignore
                    minutes=r.pace_per_mile.minute,  # type: ignore
                    seconds=r.pace_per_mile.second,  # type: ignore
                ).total_seconds()
                for r in pace_runs
            ) / len(pace_runs)
        else:
            avg_pace = 0

        # Calculate averages for non-null values
        hr_runs = [run for run in runs if run.heart_rate_avg is not None]
        cadence_runs = [run for run in runs if run.cadence_avg is not None]
        if hr_runs:
            avg_hr = sum(run.heart_rate_avg for run in hr_runs) / len(hr_runs)  # type: ignore
        else:
            avg_hr = 0
        if cadence_runs:
            avg_cadence = sum(run.cadence_avg for run in cadence_runs) / len(cadence_runs)  # type: ignore
        else:
            avg_cadence = 0

        # Find records
        if pace_runs:
            fastest_run = min(
                pace_runs,
                key=lambda r: timedelta(
                    hours=r.pace_per_mile.hour,  # type: ignore
                    minutes=r.pace_per_mile.minute,  # type: ignore
                    seconds=r.pace_per_mile.second,  # type: ignore
                ).total_seconds(),
            )
        else:
            fastest_run = None
        highest_cadence_run = max(runs, key=lambda r: r.cadence_avg or 0)
        longest_run = max(runs, key=lambda r: r.distance_miles)

        # Overall stats
        stats_table = Table(show_header=False, box=None)
        stats_table.add_row("Total Runs", f"{total_runs}")
        stats_table.add_row("Total Miles", f"{total_miles:.1f}")
        stats_table.add_row(
            "Average Pace", str(timedelta(seconds=int(avg_pace))).split(".")[0]
        )
        if avg_hr > 0:
            stats_table.add_row("Average HR", f"{avg_hr:.0f} bpm")
        if avg_cadence > 0:
            stats_table.add_row("Average Cadence", f"{avg_cadence:.0f} spm")

        # Records table
        records_table = Table(show_header=False, box=None)
        if fastest_run and fastest_run.pace_per_mile:
            records_table.add_row(
                "Fastest Run",
                f"{fastest_run.distance_miles:.1f}mi at {fastest_run.pace_per_mile.strftime('%M:%S')}/mi on {fastest_run.date.strftime('%m/%d/%y')}",
            )
        records_table.add_row(
            "Longest Run",
            f"{longest_run.distance_miles:.1f}mi on {longest_run.date.strftime('%m/%d/%y')}",
        )
        if highest_cadence_run.cadence_avg:
            records_table.add_row(
                "Highest Cadence",
                f"{highest_cadence_run.cadence_avg} spm on {highest_cadence_run.date.strftime('%m/%d/%y')}",
            )

        # Layout
        layout = Layout()
        layout.split_column(
            Layout(Panel(stats_table, title="📊 Overall Statistics")),
            Layout(Panel(records_table, title="🏆 Personal Records")),
        )

        console.print(layout)

    except Exception as e:
        render_error(f"Failed to generate report: {str(e)}")


@app.command()
def drop_db(
    force: bool = typer.Option(
        False, "--force", "-f", help="Force drop without confirmation"
    ),
):
    """Drop and recreate all database tables."""
    if not force:
        confirm = typer.confirm("⚠️  This will delete all data. Are you sure?")
        if not confirm:
            render_error("Operation cancelled")
            return

    try:
        # Get database client (local or cloud based on config)
        db = get_database_client()
        db.drop_tables()
        db._create_tables()
        console.print(
            "[green]✓ Database tables dropped and recreated successfully[/green]"
        )
    except Exception as e:
        render_error(f"Failed to drop database: {str(e)}")


@app.command()
def config_show():
    """Show current configuration."""
    show_config()


@app.command()
def config_cloud():
    """Switch to cloud mode."""
    if setup_cloud_mode():
        console.print("[green]✅ Successfully switched to cloud mode[/green]")
        console.print(
            "[blue]💡 Make sure FITLOG_API_KEY is set in your environment[/blue]"
        )
    else:
        console.print("[red]❌ Failed to configure cloud mode[/red]")


@app.command()
def config_local():
    """Switch to local mode."""
    if setup_local_mode():
        console.print("[green]✅ Successfully switched to local mode[/green]")


@app.command()
def config_init():
    """Create example .env file with configuration."""
    try:
        from .config import Config

        config_obj = Config()
        env_file = config_obj.create_env_file()
        console.print(
            f"[green]✅ Created example configuration file: {env_file}[/green]"
        )
        console.print(
            "[blue]💡 Edit this file with your settings and rename to .env[/blue]"
        )
    except Exception as e:
        render_error(f"Failed to create config file: {str(e)}")


def main():
    app()


if __name__ == "__main__":
    main()
