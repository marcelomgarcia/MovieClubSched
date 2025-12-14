# CSV ingestion script for MovieClubSched
# Reads CSV files with movie schedule data and populates the database

import csv
import logging
import sys
from datetime import datetime
from sqlite3 import connect
from typing import Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Country normalization mapping
COUNTRY_MAPPING = {
    "US": "USA",
    "United States": "USA",
    "United States of America": "USA",
    "UK": "United Kingdom",
    "England": "United Kingdom",
}

DATABASE_PATH = "data/movie_club.db"


def parse_director_name(full_name: str) -> Optional[Tuple[str, str, str]]:
    """
    Parse a director's full name into first, middle, and last names.

    Args:
        full_name: The director's full name

    Returns:
        Tuple of (fname, mname, lname) or None if parsing fails

    Rules:
        - 2 words: fname + lname (mname is empty string)
        - 3 words: fname + mname + lname
        - 4+ words: Return None (requires manual intervention)
    """
    parts = full_name.strip().split()

    if len(parts) == 2:
        return (parts[0], "", parts[1])
    elif len(parts) == 3:
        return (parts[0], parts[1], parts[2])
    else:
        # 1 word or 4+ words - requires manual intervention
        logger.warning(f"Cannot parse director name '{full_name}' - requires manual intervention")
        return None


def split_directors(director_str: str) -> list[str]:
    """
    Split a string containing multiple directors separated by semicolons.

    Args:
        director_str: String with directors separated by ";"

    Returns:
        List of individual director names (stripped of whitespace)
    """
    return [d.strip() for d in director_str.split(";")]


def normalize_country(country: str) -> str:
    """
    Normalize country names using the COUNTRY_MAPPING.

    Args:
        country: Raw country name from CSV

    Returns:
        Normalized country name
    """
    country_stripped = country.strip()
    return COUNTRY_MAPPING.get(country_stripped, country_stripped)


def validate_date(date_str: str) -> bool:
    """
    Validate that a date string is in YYYY-MM-DD format.

    Args:
        date_str: Date string to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return True
    except ValueError:
        return False


def find_or_insert_director(cursor, fname: str, mname: str, lname: str) -> int:
    """
    Find an existing director or insert a new one.

    Args:
        cursor: Database cursor
        fname: First name
        mname: Middle name (can be empty string)
        lname: Last name

    Returns:
        Director ID
    """
    # Check if director already exists
    cursor.execute(
        "SELECT id FROM directors WHERE fname = ? AND mname = ? AND lname = ?",
        (fname, mname, lname)
    )
    result = cursor.fetchone()

    if result:
        return result[0]

    # Insert new director
    cursor.execute(
        "INSERT INTO directors (fname, mname, lname) VALUES (?, ?, ?)",
        (fname, mname, lname)
    )
    return cursor.lastrowid


def find_or_insert_host(cursor, host_name: str) -> Optional[int]:
    """
    Find an existing host or insert a new one.
    Handles empty/missing host names.

    Args:
        cursor: Database cursor
        host_name: Full name of the host

    Returns:
        Host ID or None if host_name is empty
    """
    if not host_name or not host_name.strip():
        return None

    # Parse host name (simple: first word is fname, rest is lname)
    parts = host_name.strip().split(maxsplit=1)
    if len(parts) == 2:
        fname, lname = parts[0], parts[1]
    elif len(parts) == 1:
        fname, lname = parts[0], ""
    else:
        return None

    # Check if host already exists
    cursor.execute(
        "SELECT id FROM host WHERE fname = ? AND lname = ?",
        (fname, lname)
    )
    result = cursor.fetchone()

    if result:
        return result[0]

    # Insert new host
    cursor.execute(
        "INSERT INTO host (fname, lname) VALUES (?, ?)",
        (fname, lname)
    )
    return cursor.lastrowid


def check_duplicate_movie(cursor, title: str, year: str) -> Optional[int]:
    """
    Check if a movie already exists in the database.

    Args:
        cursor: Database cursor
        title: Movie title
        year: Release year

    Returns:
        Movie ID if found, None otherwise
    """
    cursor.execute(
        "SELECT id FROM movies WHERE title = ? AND year = ?",
        (title, int(year))
    )
    result = cursor.fetchone()
    return result[0] if result else None


def insert_movie(cursor, title: str, year: str, country: str) -> int:
    """
    Insert a new movie into the database.

    Args:
        cursor: Database cursor
        title: Movie title
        year: Release year
        country: Country of origin

    Returns:
        Movie ID of inserted movie
    """
    cursor.execute(
        "INSERT INTO movies (title, year, country) VALUES (?, ?, ?)",
        (title, int(year), country)
    )
    return cursor.lastrowid


def insert_movie_directors(cursor, movie_id: int, director_ids: list[int]) -> None:
    """
    Insert movie-director relationships into MOVIEDIRECTOR junction table.

    Args:
        cursor: Database cursor
        movie_id: Movie ID
        director_ids: List of director IDs in order
    """
    for idx, director_id in enumerate(director_ids, start=1):
        cursor.execute(
            "INSERT INTO moviedirector (movie_id, director_id, director_ord) VALUES (?, ?, ?)",
            (movie_id, director_id, idx)
        )


def insert_session(cursor, movie_id: int, date: str, host_id: Optional[int]) -> int:
    """
    Insert a new session into the database.

    Args:
        cursor: Database cursor
        movie_id: Movie ID
        date: Screening date (YYYY-MM-DD)
        host_id: Host ID (can be None)

    Returns:
        Session ID
    """
    cursor.execute(
        "INSERT INTO session (date, movie_id, host_id) VALUES (?, ?, ?)",
        (date, movie_id, host_id)
    )
    return cursor.lastrowid


def ingest_csv(csv_path: str) -> None:
    """
    Main function to ingest CSV file into the database.

    Args:
        csv_path: Path to the CSV file
    """
    logger.info(f"Starting ingestion from {csv_path}")

    conn = connect(DATABASE_PATH)
    cursor = conn.cursor()

    rows_processed = 0
    rows_skipped = 0
    rows_duplicates = 0

    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is line 1)
                print(f"mg: {row}")
                try:
                    # Extract and validate fields
                    title = row.get('title', '').strip()
                    director_str = row.get('director', '').strip()
                    country = row.get('country of origin', '').strip()
                    year = row.get('year', '').strip()
                    screen_date = row.get('screen date', '').strip()
                    host_name = row.get('host', '').strip()

                    # Validate required fields
                    if not title or not director_str or not year or not country or not screen_date:
                        logger.warning(f"Row {row_num}: Missing required fields - skipping")
                        rows_skipped += 1
                        continue

                    # Validate date
                    if not validate_date(screen_date):
                        logger.warning(f"Row {row_num}: Invalid date format '{screen_date}' - skipping")
                        rows_skipped += 1
                        continue

                    # Normalize country
                    country = normalize_country(country)

                    # Check for duplicate movie
                    existing_movie_id = check_duplicate_movie(cursor, title, year)
                    if existing_movie_id:
                        logger.info(f"Row {row_num}: Movie '{title}' ({year}) already exists - skipping")
                        rows_duplicates += 1
                        continue

                    # Process directors
                    director_names = split_directors(director_str)
                    director_ids = []

                    for director_name in director_names:
                        parsed = parse_director_name(director_name)
                        if parsed is None:
                            logger.warning(f"Row {row_num}: Cannot parse director '{director_name}' - skipping entire row")
                            rows_skipped += 1
                            break

                        fname, mname, lname = parsed
                        director_id = find_or_insert_director(cursor, fname, mname, lname)
                        director_ids.append(director_id)
                    else:
                        # Only proceed if all directors were parsed successfully
                        # Insert movie
                        movie_id = insert_movie(cursor, title, year, country)
                        logger.info(f"Row {row_num}: Inserted movie '{title}' ({year})")

                        # Insert movie-director relationships
                        insert_movie_directors(cursor, movie_id, director_ids)

                        # Insert host (if provided)
                        host_id = find_or_insert_host(cursor, host_name)

                        # Insert session
                        session_id = insert_session(cursor, movie_id, screen_date, host_id)
                        logger.info(f"Row {row_num}: Inserted session for '{title}' on {screen_date}")

                        # Commit after each successful row
                        conn.commit()
                        rows_processed += 1

                except Exception as e:
                    logger.error(f"Row {row_num}: Error processing row - {e}")
                    conn.rollback()
                    rows_skipped += 1

    except FileNotFoundError:
        logger.error(f"File not found: {csv_path}")
        return
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        return
    finally:
        conn.close()

    logger.info(f"Ingestion complete: {rows_processed} rows processed, {rows_duplicates} duplicates skipped, {rows_skipped} rows skipped due to errors")


def main():
    """Entry point for the script."""
    if len(sys.argv) != 2:
        print("Usage: uv run ingest.py <csv_file>")
        sys.exit(1)

    csv_path = sys.argv[1]
    ingest_csv(csv_path)


if __name__ == "__main__":
    main()
