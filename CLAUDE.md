# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MovieClubSched is a Python-based system to manage movies, sessions, and generate schedules for a Movie Club. The system tracks movies, directors, screening sessions, and hosts using a SQLite database.

## Database Architecture

The system uses SQLite database (`data/movie_club.db`) with the following schema:

- **MOVIES**: Stores movie information (id, title, year_release, country_origina)
- **DIRECTORS**: Director information (id, fname, lname)
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

**Run the main script:**
```bash
uv run movieclubsched.py
```
This generates `data/movie_sched.csv` with the movie club schedule from the database.

**Query database directly:**
```bash
sqlite3 data/movie_club.db
```

**Export directors table:**
```bash
sqlite3 data/movie_club.db < export_dirs.sql
```

## Code Structure

- `movieclubsched.py`: Main script that queries the database and exports movie schedule to CSV
  - `date2screen()`: Converts ISO date format to human-readable format
  - `main()`: Queries movies joined with directors, formats dates, writes to CSV
- `data/`: Contains SQLite database and CSV files
- `docs/`: Architecture documentation (database ER diagram, class diagrams)
- `export_dirs.sql`: SQL script to export directors to CSV

## Key Requirements

The system should support:
- Adding movies to the database
- Querying if a movie was already shown (date, attendance, host)
- Reports: movies exhibited last month, average attendance

## Notes

- The current implementation in `movieclubsched.py` queries movies with directors and screen dates, but the schema shows `SESSION` table should contain screening dates (not movies table directly)
