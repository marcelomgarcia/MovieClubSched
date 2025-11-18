# Database migration script
# Migrates the simple schema to the normalized schema described in CLAUDE.md

import sqlite3
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATABASE_PATH = "data/movie_club.db"
BACKUP_PATH = f"data/movie_club_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"


def backup_database():
    """Create a backup of the current database."""
    import shutil
    shutil.copy2(DATABASE_PATH, BACKUP_PATH)
    logger.info(f"Database backed up to {BACKUP_PATH}")


def create_new_schema(cursor):
    """Create the new normalized schema."""
    logger.info("Creating new schema...")

    # Create new DIRECTORS table with fname, mname, lname
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS directors_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fname TEXT NOT NULL,
            mname TEXT,
            lname TEXT NOT NULL
        )
    """)

    # Create MOVIEDIRECTOR junction table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS moviedirector (
            movie_id INTEGER NOT NULL,
            director_id INTEGER NOT NULL,
            director_ord INTEGER NOT NULL,
            PRIMARY KEY (movie_id, director_id),
            FOREIGN KEY (movie_id) REFERENCES movies(id),
            FOREIGN KEY (director_id) REFERENCES directors_new(id)
        )
    """)

    # Create HOST table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS host (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fname TEXT NOT NULL,
            lname TEXT NOT NULL
        )
    """)

    # Create SESSION table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            movie_id INTEGER NOT NULL,
            host_id INTEGER,
            attendance INTEGER,
            FOREIGN KEY (movie_id) REFERENCES movies(id),
            FOREIGN KEY (host_id) REFERENCES host(id)
        )
    """)

    # Create new MOVIES table (simplified, removing director_id, screen_date, host, attendance)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            year INTEGER,
            country TEXT,
            url TEXT
        )
    """)

    logger.info("New schema created successfully")


def parse_name(full_name):
    """Parse a full name into first and last name (simple 2-part split)."""
    parts = full_name.strip().split(maxsplit=1)
    if len(parts) == 2:
        return parts[0], "", parts[1]
    elif len(parts) == 1:
        return parts[0], "", ""
    else:
        return "", "", ""


def migrate_data(cursor):
    """Migrate data from old schema to new schema."""
    logger.info("Migrating data...")

    # Migrate directors
    cursor.execute("SELECT id, name FROM directors")
    old_directors = cursor.fetchall()

    director_id_mapping = {}
    for old_id, name in old_directors:
        fname, mname, lname = parse_name(name)
        cursor.execute(
            "INSERT INTO directors_new (fname, mname, lname) VALUES (?, ?, ?)",
            (fname, mname, lname)
        )
        new_id = cursor.lastrowid
        director_id_mapping[old_id] = new_id
        logger.info(f"Migrated director: {name} -> fname={fname}, lname={lname}")

    # Migrate movies
    cursor.execute("SELECT id, title, year, country, url FROM movies")
    old_movies = cursor.fetchall()

    movie_id_mapping = {}
    for old_id, title, year, country, url in old_movies:
        cursor.execute(
            "INSERT INTO movies_new (title, year, country, url) VALUES (?, ?, ?, ?)",
            (title, year, country, url)
        )
        new_id = cursor.lastrowid
        movie_id_mapping[old_id] = new_id
        logger.info(f"Migrated movie: {title}")

    # Migrate movie-director relationships
    cursor.execute("SELECT id, director_id FROM movies")
    movie_directors = cursor.fetchall()

    for old_movie_id, old_director_id in movie_directors:
        new_movie_id = movie_id_mapping[old_movie_id]
        new_director_id = director_id_mapping[old_director_id]
        cursor.execute(
            "INSERT INTO moviedirector (movie_id, director_id, director_ord) VALUES (?, ?, ?)",
            (new_movie_id, new_director_id, 1)
        )
    logger.info("Migrated movie-director relationships")

    # Migrate hosts and sessions
    cursor.execute("SELECT id, screen_date, host, attendance FROM movies WHERE screen_date IS NOT NULL")
    sessions_data = cursor.fetchall()

    host_mapping = {}
    for old_movie_id, screen_date, host_name, attendance in sessions_data:
        new_movie_id = movie_id_mapping[old_movie_id]

        # Handle host
        host_id = None
        if host_name and host_name.strip():
            fname, mname, lname = parse_name(host_name)

            # Check if host already exists
            if host_name in host_mapping:
                host_id = host_mapping[host_name]
            else:
                cursor.execute(
                    "INSERT INTO host (fname, lname) VALUES (?, ?)",
                    (fname, lname)
                )
                host_id = cursor.lastrowid
                host_mapping[host_name] = host_id

        # Insert session
        cursor.execute(
            "INSERT INTO session (date, movie_id, host_id, attendance) VALUES (?, ?, ?, ?)",
            (screen_date, new_movie_id, host_id, attendance)
        )

    logger.info(f"Migrated {len(sessions_data)} sessions")


def replace_old_tables(cursor):
    """Replace old tables with new ones."""
    logger.info("Replacing old tables with new schema...")

    # Drop old tables
    cursor.execute("DROP TABLE IF EXISTS directors")
    cursor.execute("DROP TABLE IF EXISTS movies")

    # Rename new tables
    cursor.execute("ALTER TABLE directors_new RENAME TO directors")
    cursor.execute("ALTER TABLE movies_new RENAME TO movies")

    logger.info("Old tables replaced successfully")


def main():
    """Main migration function."""
    logger.info("Starting database migration...")

    # Backup first
    backup_database()

    # Connect to database
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Create new schema
        create_new_schema(cursor)

        # Migrate data
        migrate_data(cursor)

        # Replace old tables
        replace_old_tables(cursor)

        # Commit changes
        conn.commit()
        logger.info("Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed: {e}")
        logger.error(f"Database restored from backup: {BACKUP_PATH}")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()
