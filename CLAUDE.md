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

## Requirements

How the script work:

1. **Ingestion** Read a csv file with the new schedule and feed the database.
    1. The fields in the csv file are, in this order: title, director, year, country of origin, screen date, host.
    1. Add the movie_id and director_id to junction table `MOVIEDIRECTOR`.
    1. In case of multiple directors, the names will be separated by ";".
    1. The system needs to be aware that some directors have middle name.
    1. In case of multiple middle names or compound last names, manual intervention will necessary. This entry **should not** be added to the database. Instead, skip the line and alert in the logs of the problems with the entry.
    1. Create a mapping for countries like United States: "USA", or "US" or "United States of America". Create another mapping for "UK", where can be "UK" or "England." Like this:  {"US": "USA", "United States": "USA", "United States of America": "USA"}
    1. **TODO** how to prevent duplicated movies? Possible solution: check by `title`+`year` or some hash like sha1 of the `title` to be the primary key of the movies table. Sha1 because it's computationally light and it's a simple verification, but this can be an overkill for a simple problem.
1. **Queries** It shoudl be possible to query by director, title and year.
1. **Update** It should be possible to update the schedule in case we need to move a movie to another date or if the host change.

### Ingestion

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

