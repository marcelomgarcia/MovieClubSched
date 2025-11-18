# MovieClubSched

A Python-based system to manage movies, sessions, and generate schedules for a Movie Club. The system tracks movies, directors, screening sessions, and hosts using a SQLite database.

## Features

- **CSV Ingestion**: Import movie schedules from CSV files
- **Duplicate Prevention**: Automatically detects and skips duplicate movies
- **Multiple Directors Support**: Handle movies with multiple directors
- **Flexible Queries**: Search by title, director, or date range
- **Schedule Generation**: Generate monthly movie schedules
- **Country Normalization**: Automatically normalize country names (US → USA, UK → United Kingdom)

## Requirements

- Python 3.12 or higher
- `uv` package manager

## Installation

```bash
# Install dependencies
uv sync
```

## Database Schema

The system uses a normalized SQLite database with the following tables:

- **MOVIES**: Movie information (id, title, year, country, url)
- **DIRECTORS**: Director information (id, fname, mname, lname)
- **MOVIEDIRECTOR**: Junction table linking movies to directors (supports multiple directors per movie)
- **SESSION**: Screening sessions (id, date, movie_id, host_id, attendance)
- **HOST**: Host information (id, fname, lname)

### Key Relationships
- Movies can have multiple directors (many-to-many via MOVIEDIRECTOR)
- Sessions screen one movie (many-to-one)
- Hosts can host multiple sessions (one-to-many)

## Usage

### Importing Movie Data

Create a CSV file with the following format:

```csv
title,director,year,country of origin,screen date,host
Sin City,Frank Miller; Robert Rodriguez; Quentin Tarantino,2005,USA,2024-12-10,Marcelo
Jaws,Steven Spielberg,1975,USA,2024-10-15,Marcelo
The Phantom Hour,Brian Patrick Butler,2016,USA,2025-01-24,Andrew
```

**CSV Format Notes:**
- Multiple directors should be separated by semicolons (`;`)
- Dates must be in ISO 8601 format (YYYY-MM-DD)
- Host field can be empty (will be NULL in database)
- Director names with 2 words: first name + last name
- Director names with 3 words: first name + middle name + last name
- Director names with 4+ words will be skipped (requires manual intervention)

**Import the data:**

```bash
uv run ingest.py data/schedule.csv
```

**Example output:**
```
2025-11-18 22:04:24,531 - INFO - Starting ingestion from test_data.csv
2025-11-18 22:04:24,556 - INFO - Row 2: Movie 'Sin City' (2005) already exists - skipping
2025-11-18 22:04:24,556 - INFO - Row 3: Movie 'Jaws' (1975) already exists - skipping
2025-11-18 22:04:24,557 - INFO - Row 4: Inserted movie 'The Phantom Hour' (2016)
2025-11-18 22:04:24,557 - INFO - Row 4: Inserted session for 'The Phantom Hour' on 2025-01-24
2025-11-18 22:04:24,559 - INFO - Ingestion complete: 1 rows processed, 2 duplicates skipped, 0 rows skipped due to errors
```

### Querying the Database

#### Generate Movie Schedule

Generate a schedule for the next month (default):

```bash
uv run query.py schedule
```

Generate a schedule for a specific month:

```bash
uv run query.py schedule --month 1 --year 2025
```

**Example output:**
```
Movie Schedule for January 2025
================================================================================

Fri, Jan 24, 2025
  The Phantom Hour (2016)
  Director(s): Brian Patrick Butler
  Country: USA
  Host: Andrew

Tue, Jan 28, 2025
  Pulp Fiction (1994)
  Director(s): Quentin Tarantino
  Country: USA
  Host: Marcelo
  Attendance: 0
```

#### Search for a Movie

```bash
uv run query.py search "Jaws"
```

**Example output:**
```
Searching for movies matching: 'Jaws'
================================================================================

Jaws (1975)
  Director(s): Steven Spielberg
  Country: USA
  Screenings:
    - Tue, Feb 25, 2025, Host: Marcelo
```

#### List Movies by Director

```bash
uv run query.py director "Spielberg"
```

**Example output:**
```
Movies directed by 'Spielberg'
================================================================================
  Jaws (1975) - Steven Spielberg - USA
```

#### List Movies in a Date Range

```bash
uv run query.py daterange "2025-01-01" "2025-12-31"
```

**Example output:**
```
Movies screened between 2025-01-01 and 2025-12-31
================================================================================

Fri, Jan 24, 2025
  The Phantom Hour (2016) - USA
  Director(s): Brian Patrick Butler
  Host: Andrew

Tue, Jan 28, 2025
  Pulp Fiction (1994) - USA
  Director(s): Quentin Tarantino
  Host: Marcelo, Attendance: 0
```

### Legacy Commands

**Export schedule to CSV:**
```bash
uv run movieclubsched.py
```
Generates `data/movie_sched.csv` with the movie club schedule.

**Export directors table:**
```bash
sqlite3 data/movie_club.db < export_dirs.sql
```
Exports directors to `directors.csv`.

## Database Migration

If you have an older database schema, migrate it to the normalized schema:

```bash
uv run migrate_db.py
```

This will:
1. Create a backup of your current database
2. Create new tables (DIRECTORS, MOVIEDIRECTOR, SESSION, HOST, MOVIES)
3. Migrate existing data to the new schema
4. Replace old tables with new ones

## Country Normalization

The system automatically normalizes country names:

- `US`, `United States`, `United States of America` → `USA`
- `UK`, `England` → `United Kingdom`

You can add more mappings in `ingest.py` by editing the `COUNTRY_MAPPING` dictionary.

## Duplicate Prevention

The system prevents duplicates using:

- **Movies**: `title + year` combination
- **Directors**: `fname + mname + lname` combination
- **Hosts**: `fname + lname` combination

Running the ingestion script multiple times with the same data is safe (idempotent).

## Error Handling

The ingestion script will:
- Skip rows with missing required fields (logs warning)
- Skip rows with invalid date formats (logs warning)
- Skip directors with 4+ word names (logs warning, requires manual intervention)
- Skip duplicate movies (logs info message)
- Roll back failed row insertions (logs error)

Check the logs for details on skipped rows.

## Project Structure

```
MovieClubSched/
├── data/
│   ├── movie_club.db          # SQLite database
│   ├── movies.csv             # Movie data
│   ├── directors.csv          # Directors export
│   └── movie_sched.csv        # Schedule export
├── docs/
│   ├── database.md            # ER diagram
│   └── classes.md             # Class diagrams
├── ingest.py                  # CSV ingestion script
├── query.py                   # Query/search script
├── migrate_db.py              # Database migration script
├── movieclubsched.py          # Legacy schedule export
├── export_dirs.sql            # SQL export script
├── CLAUDE.md                  # Developer guide
└── README.md                  # This file
```

## Examples

### Example 1: Import New Schedule

```bash
# Create a CSV file with new movies
cat > new_schedule.csv << EOF
title,director,year,country of origin,screen date,host
The Matrix,Lana Wachowski; Lilly Wachowski,1999,USA,2025-03-15,Sarah
Blade Runner,Ridley Scott,1982,USA,2025-03-22,John
EOF

# Import the schedule
uv run ingest.py new_schedule.csv

# Verify the import
uv run query.py search "Matrix"
```

### Example 2: Check Movie Schedule

```bash
# Get next month's schedule
uv run query.py schedule

# Get schedule for March 2025
uv run query.py schedule --month 3 --year 2025
```

### Example 3: Research a Director

```bash
# Find all movies by a director
uv run query.py director "Kubrick"

# Check if a specific movie was shown
uv run query.py search "2001"
```

## Troubleshooting

### Import Issues

**Problem**: Director name not parsing correctly
**Solution**: Director names with 4+ words require manual intervention. Add the director to the database manually or simplify the name to 2-3 words.

**Problem**: Duplicate movies being inserted
**Solution**: Check that the `title` and `year` exactly match existing entries. The check is case-sensitive.

### Query Issues

**Problem**: No results found
**Solution**: Queries use partial matching (LIKE). Try searching with fewer characters or different parts of the title/name.

## Contributing

See `CLAUDE.md` for developer documentation and architecture details.

## License

See LICENSE file for details.
