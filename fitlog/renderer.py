from datetime import datetime, timedelta

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .models import Pushup, Run

console = Console()


def format_time(t: datetime) -> str:
    return t.strftime("%A %m/%d/%y")


def format_duration(t: datetime) -> str:
    return t.strftime("%H:%M:%S")


def render_stats(stats: dict) -> None:
    table = Table(title="📊 Activity Statistics (Last 30 Days)")

    table.add_column("Activity", style="cyan")
    table.add_column("Total Sessions", style="magenta")
    table.add_column("Total Amount", style="green")
    table.add_column("Average", style="yellow")

    # Add runs stats
    table.add_row(
        "🏃 Running",
        str(stats["runs"]["total"]),
        f"{stats['runs']['total_distance']:.1f} miles",
        f"{stats['runs']['avg_distance']:.1f} miles/run",
    )

    # Add pushups stats
    table.add_row(
        "💪 Pushups",
        str(stats["pushups"]["total"]),
        str(stats["pushups"]["total_count"]),
        f"{stats['pushups']['avg_count']:.0f} pushups/day",
    )

    console.print(table)


def render_recent_activities(
    runs: list[Run], pushups: list[Pushup], days: int = 7
) -> None:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    table = Table(title=f"📅 Recent Activities (Last {days} Days)")

    table.add_column("Date", style="cyan")
    table.add_column("Distance (mi)", style="green", justify="right")
    table.add_column("Duration", style="blue", justify="right")
    table.add_column("Pace (/mi)", style="yellow", justify="right")
    table.add_column("Pushups", style="magenta", justify="right")

    # Create a dictionary to store daily activities
    daily_activities = {}

    # Process runs
    for run in runs:
        if start_date <= run.date <= end_date:
            date_key = run.date.date()
            if date_key not in daily_activities:
                daily_activities[date_key] = {
                    "date": run.date,
                    "distance": run.distance_miles,
                    "duration": run.duration,
                    "pace": run.pace_per_mile
                    if hasattr(run, "pace_per_mile")
                    else None,
                    "pushups": 0,
                }
            else:
                daily_activities[date_key]["distance"] = run.distance_miles
                daily_activities[date_key]["duration"] = run.duration
                daily_activities[date_key]["pace"] = (
                    run.pace_per_mile if hasattr(run, "pace_per_mile") else None
                )

    # Process pushups
    for pushup in pushups:
        if start_date <= pushup.date <= end_date:
            date_key = pushup.date.date()
            if date_key not in daily_activities:
                daily_activities[date_key] = {
                    "date": pushup.date,
                    "distance": 0,
                    "duration": None,
                    "pace": None,
                    "pushups": pushup.count,
                }
            else:
                daily_activities[date_key]["pushups"] = pushup.count

    # Sort by date descending
    sorted_dates = sorted(daily_activities.keys(), reverse=True)

    # Add rows to table
    for date_key in sorted_dates:
        activity = daily_activities[date_key]
        table.add_row(
            format_time(activity["date"]),
            f"{activity['distance']:.1f}" if activity["distance"] > 0 else "-",
            format_duration(activity["duration"]) if activity["duration"] else "-",
            format_duration(activity["pace"]) if activity["pace"] else "-",
            str(activity["pushups"]) if activity["pushups"] > 0 else "-",
        )

    console.print(table)


def render_success(message: str) -> None:
    console.print(
        Panel(Text(message, style="green"), title="✅ Success", border_style="green")
    )


def render_error(message: str) -> None:
    console.print(
        Panel(Text(message, style="red"), title="❌ Error", border_style="red")
    )
