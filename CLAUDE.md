# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MovieClubSched is a Python-based system to manage movies, sessions, and generate schedules for a Movie Club. The system tracks movies, directors, screening sessions, and hosts using a SQLite database.

## Database Architecture

The system uses SQLite database (`data/movie_club.db`) with the following schema:

- **MOVIES**: Stores movie information (id, title, year_release, country_origina)
- **DIRECTORS**: Director information (id, fname, lname, mname)
- **MOVIEDIRECTOR**: Junction table linking movies to directors (movie_id, director_id, director_ord) - supports multiple directors per movie
- **SESSION**: Screening sessions (id, date, movie_id, host_id)
- **HOST**: Host information (id, fname, lname)

Key relationships:
- Movies can have multiple directors (N:M via MOVIEDIRECTOR)
- Sessions screen one movie (N:1)
- Hosts can host multiple sessions (1:N)

See `docs/database.md` for the ER diagram and `docs/classes.md` for class design.

## Development Commands

This project uses `uv` for Python package management (Python >=3.12 required).

**Setup:**
```bash
uv sync
```

**Database Migration (if needed):**
```bash
uv run migrate_db.py
```
Migrates the old simple schema to the normalized schema. Creates a backup before migration.

**Ingest CSV data:**
```bash
uv run ingest.py <csv_file>
```
Example: `uv run ingest.py data/schedule.csv`

**Query commands:**
```bash
# Generate schedule for next month (default) or specific month
uv run query.py schedule
uv run query.py schedule --month 1 --year 2025

# Search for a movie
uv run query.py search "Jaws"

# List movies by director
uv run query.py director "Spielberg"

# List movies in a date range
uv run query.py daterange "2025-01-01" "2025-12-31"
```

**Export schedule to CSV (legacy):**
```bash
uv run movieclubsched.py
```
Generates `data/movie_sched.csv`

**Export directors table:**
```bash
sqlite3 data/movie_club.db < export_dirs.sql
```

## Code Structure

- `migrate_db.py`: Database migration script (old schema → normalized schema)
- `ingest.py`: CSV ingestion script to add movies/sessions to database
- `query.py`: Query script for searching and generating reports
- `movieclubsched.py`: Legacy script that exports movie schedule to CSV
- `data/`: Contains SQLite database and CSV files
- `docs/`: Architecture documentation (database ER diagram, class diagrams)
- `export_dirs.sql`: SQL script to export directors table to CSV

## Key Requirements

The system should support:
- Adding movies to the database
- Querying if a movie was already shown (date, attendance, host)
- Reports: movies exhibited last month, average attendance

## Implementation Notes

**Database Schema:**
- The database has been migrated to a normalized schema with separate tables for directors, movies, sessions, and hosts
- Movies and directors have a many-to-many relationship via the MOVIEDIRECTOR junction table
- The `director_ord` field preserves the order of directors for movies with multiple directors

**Ingestion:**
- The ingestion script (`ingest.py`) is idempotent - running it multiple times won't create duplicates
- Movies are identified by `title + year` combination
- Directors are identified by `fname + mname + lname` combination
- Country names are normalized using a mapping (US → USA, UK → United Kingdom, etc.)
- Director names with 4+ words are skipped and require manual intervention
- Host names can be empty (sessions can be created without a host)

**Queries:**
- `query.py schedule` generates the next month's schedule by default (most important query)
- All queries support partial string matching for flexible searching
- Date formats are converted to human-readable format (e.g., "Mon, Jan 20, 2025")

## Requirements

How the script work:

1. **Ingestion** Read a csv file with the new schedule and feed the database.
    1. The fields in the csv file are, in this order: title, director, year, country of origin, screen date, host.
    1. Add the movie_id and director_id to junction table `MOVIEDIRECTOR`.
    1. In case of multiple directors, the names will be separated by ";".
    1. The system needs to be aware that some directors have middle name.
    1. In case of multiple middle names or compound last names, manual intervention will necessary. This entry **should not** be added to the database. Instead, skip the line and alert in the logs of the problems with the entry.
    1. Create a mapping for countries like United States: "USA", or "US" or "United States of America". Create another mapping for "UK", where can be "UK" or "England." Like this:  {"US": "USA", "United States": "USA", "United States of America": "USA"}
    1. Duplicate prevention: Movies are checked by `title`+`year` combination. Duplicate movies are skipped with a log message.
1. **Queries** It shoudl be possible to query by director, title and year.
1. **Update** It should be possible to update the schedule in case we need to move a movie to another date or if the host change.

## Ingestion

Sample data for explain the ingestion

```
title, director, year, country of origin, screen date, host
Sin City, Frank Miller; Robert Rodriguez; Quentin Tarantino, 2005, USA, 2024-12-10, Marcelo
Jaws, Steven Spielberg, 1975, USA, 2024-10-15, Marcelo
The Phantom Hour, Brian Patrick Butler, 2016, USA, 2025-01-24, Andrew 
```

* The first line is the header.
* The movie "Sin City" has multiple directors separated by ";": Frank Miller; Robert Rodriguez; Quentin Tarantino. This should be handled by the junction table.
* the director of the movie "The Phantom Hour" has a middle name: the first name, `fname`, is "Brian", the middle name, `mname`, is "Patrick" and a last name, `lname`, "Butler"
* The movie "Jaws" is the perfect example of a well behaved entry: the director name's is easy to decompose in first name, `fname`, and last name, `lname`.

Other considerations:

* Check if the date of screening is valid.
* The date will be ingested in the format "YYYY-MM-DD" (ISO 8601).
* A missing `host` should be valid. I can add the name of the `host` later. Assuming the ingestion is idempotent.

### Preventing Duplication

**Implementation:** Duplicate prevention is implemented using:
- **Movies**: `title + year` combination
- **Directors**: `fname + mname + lname` combination
- **Hosts**: `fname + lname` combination

The ingestion script checks for duplicates before inserting and skips duplicate movies with a log message.

## Queries

* This is the **most** important part of the project: to generate a schedule of the movie club for the next month. The output of the query should be ordered by date is ascending order.
* It should be possible to search for a movie. I want to answer the question: did we already show the movie "Jaws?"
* List the movies directed by a given director: list the movies directed by Steven Spielberg.
* List movies in a date range: list the movies shown in 2024.

## Updates

To update the host or the showing date maybe it's easier to edit the sqlite3 file directly.