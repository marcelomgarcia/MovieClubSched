# Query script for MovieClubSched
# Provides various queries for searching and analyzing the movie database

import argparse
import sqlite3
import sys
from datetime import datetime, date
import calendar

DATABASE_PATH = "data/movie_club.db"


def format_director_name(fname: str, mname: str, lname: str) -> str:
    """Format director name with optional middle name."""
    if mname:
        return f"{fname} {mname} {lname}"
    return f"{fname} {lname}"


def format_host_name(fname: str, lname: str) -> str:
    """Format host name."""
    if lname:
        return f"{fname} {lname}"
    return fname


def generate_schedule(month: int = None, year: int = None) -> None:
    """
    Generate movie schedule for a given month (default: current month).
    Results ordered by date in ascending order.

    Args:
        month: Month number (1-12), defaults to current month
        year: Year, defaults to current year
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Default to current month if not specified
    if month is None or year is None:
        today = date.today()
        month = today.month
        year = today.year

    # Get first and last day of the month
    first_day = date(year, month, 1)
    last_day_of_month = calendar.monthrange(year, month)[1]
    last_day = date(year, month, last_day_of_month)

    print(f"\nMovie Schedule for {first_day.strftime('%B %Y')}")
    print("=" * 80)

    cursor.execute("""
        SELECT
            s.date,
            m.title,
            m.year,
            m.country,
            GROUP_CONCAT(d.fname || ' ' || IFNULL(d.mname || ' ', '') || d.lname, '; ') as directors,
            h.fname,
            h.lname,
            s.attendance
        FROM session s
        JOIN movies m ON s.movie_id = m.id
        LEFT JOIN moviedirector md ON m.id = md.movie_id
        LEFT JOIN directors d ON md.director_id = d.id
        LEFT JOIN host h ON s.host_id = h.id
        WHERE s.date >= ? AND s.date <= ?
        GROUP BY s.id
        ORDER BY s.date ASC
    """, (str(first_day), str(last_day)))

    rows = cursor.fetchall()

    if not rows:
        print(f"No sessions scheduled for {first_day.strftime('%B %Y')}")
    else:
        for row in rows:
            screen_date, title, year, country, directors, host_fname, host_lname = row[:7]

            print(f"{title}, {directors}, {country}, {year}, {screen_date}")

    conn.close()


def search_movie(title: str) -> None:
    """
    Search for a movie by title and show when it was screened.

    Args:
        title: Movie title to search for (partial match supported)
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    print(f"\nSearching for movies matching: '{title}'")
    print("=" * 80)

    cursor.execute("""
        SELECT
            m.title,
            m.year,
            m.country,
            GROUP_CONCAT(d.fname || ' ' || IFNULL(d.mname || ' ', '') || d.lname, '; ') as directors,
            s.date,
            h.fname,
            h.lname,
            s.attendance
        FROM movies m
        LEFT JOIN moviedirector md ON m.id = md.movie_id
        LEFT JOIN directors d ON md.director_id = d.id
        LEFT JOIN session s ON m.id = s.movie_id
        LEFT JOIN host h ON s.host_id = h.id
        WHERE m.title LIKE ?
        GROUP BY m.id, s.id
        ORDER BY m.title, s.date
    """, (f"%{title}%",))

    rows = cursor.fetchall()

    if not rows:
        print(f"No movies found matching '{title}'")
    else:
        current_movie = None
        for row in rows:
            movie_title, year, country, directors, screen_date, host_fname, host_lname, attendance = row

            if current_movie != movie_title:
                current_movie = movie_title
                print(f"\n{movie_title} ({year})")
                print(f"  Director(s): {directors}")
                print(f"  Country: {country}")

                if screen_date:
                    print(f"  Screenings:")

            if screen_date:
                date_obj = datetime.strptime(screen_date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%a, %b %d, %Y")
                host = format_host_name(host_fname, host_lname) if host_fname else "TBD"
                attendance_str = f", Attendance: {attendance}" if attendance else ""
                print(f"    - {formatted_date}, Host: {host}{attendance_str}")
            else:
                if current_movie == movie_title:
                    print(f"  Not yet screened")

    conn.close()


def list_movies_by_director(director_name: str) -> None:
    """
    List all movies by a given director.

    Args:
        director_name: Director name to search for (partial match on any part of name)
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    print(f"\nMovies directed by '{director_name}'")
    print("=" * 80)

    cursor.execute("""
        SELECT
            m.title,
            m.year,
            m.country,
            d.fname,
            d.mname,
            d.lname
        FROM movies m
        JOIN moviedirector md ON m.id = md.movie_id
        JOIN directors d ON md.director_id = d.id
        WHERE d.fname LIKE ? OR d.mname LIKE ? OR d.lname LIKE ?
        GROUP BY m.id
        ORDER BY m.year DESC, m.title
    """, (f"%{director_name}%", f"%{director_name}%", f"%{director_name}%"))

    rows = cursor.fetchall()

    if not rows:
        print(f"No movies found for director '{director_name}'")
    else:
        for row in rows:
            title, year, country, fname, mname, lname = row
            director = format_director_name(fname, mname, lname)
            print(f"  {title} ({year}) - {director} - {country}")

    conn.close()


def list_movies_by_date_range(start_date: str, end_date: str) -> None:
    """
    List all movies screened in a date range.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    print(f"\nMovies screened between {start_date} and {end_date}")
    print("=" * 80)

    cursor.execute("""
        SELECT
            s.date,
            m.title,
            m.year,
            m.country,
            GROUP_CONCAT(d.fname || ' ' || IFNULL(d.mname || ' ', '') || d.lname, '; ') as directors,
            h.fname,
            h.lname,
            s.attendance
        FROM session s
        JOIN movies m ON s.movie_id = m.id
        LEFT JOIN moviedirector md ON m.id = md.movie_id
        LEFT JOIN directors d ON md.director_id = d.id
        LEFT JOIN host h ON s.host_id = h.id
        WHERE s.date >= ? AND s.date <= ?
        GROUP BY s.id
        ORDER BY s.date DESC
    """, (start_date, end_date))

    rows = cursor.fetchall()

    if not rows:
        print(f"No movies screened between {start_date} and {end_date}")
    else:
        for row in rows:
            screen_date, title, year, country, directors, host_fname, host_lname, attendance = row

            date_obj = datetime.strptime(screen_date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%a, %b %d, %Y")
            host = format_host_name(host_fname, host_lname) if host_fname else "TBD"
            attendance_str = f", Attendance: {attendance}" if attendance else ""

            print(f"\n{formatted_date}")
            print(f"  {title} ({year}) - {country}")
            print(f"  Director(s): {directors}")
            print(f"  Host: {host}{attendance_str}")

    conn.close()


def main():
    """Entry point for the script."""
    parser = argparse.ArgumentParser(description="Query MovieClubSched database")

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Schedule command
    schedule_parser = subparsers.add_parser('schedule', help='Generate movie schedule for a month')
    schedule_parser.add_argument('--month', type=int, help='Month (1-12), default: current month')
    schedule_parser.add_argument('--year', type=int, help='Year, default: current year')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search for a movie by title')
    search_parser.add_argument('title', type=str, help='Movie title to search for')

    # Director command
    director_parser = subparsers.add_parser('director', help='List movies by director')
    director_parser.add_argument('name', type=str, help='Director name to search for')

    # Date range command
    daterange_parser = subparsers.add_parser('daterange', help='List movies in a date range')
    daterange_parser.add_argument('start', type=str, help='Start date (YYYY-MM-DD)')
    daterange_parser.add_argument('end', type=str, help='End date (YYYY-MM-DD)')

    args = parser.parse_args()

    if args.command == 'schedule':
        generate_schedule(args.month, args.year)
    elif args.command == 'search':
        search_movie(args.title)
    elif args.command == 'director':
        list_movies_by_director(args.name)
    elif args.command == 'daterange':
        list_movies_by_date_range(args.start, args.end)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
