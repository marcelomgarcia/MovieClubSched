CREATE TABLE IF NOT EXISTS "directors" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fname TEXT NOT NULL,
            mname TEXT,
            lname TEXT NOT NULL
        );
CREATE TABLE host (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fname TEXT NOT NULL,
            lname TEXT NOT NULL
        );
CREATE TABLE moviedirector (
            movie_id INTEGER NOT NULL,
            director_id INTEGER NOT NULL,
            director_ord INTEGER NOT NULL,
            PRIMARY KEY (movie_id, director_id),
            FOREIGN KEY (movie_id) REFERENCES movies(id),
            FOREIGN KEY (director_id) REFERENCES "directors"(id)
        );
CREATE TABLE IF NOT EXISTS "movies" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            year INTEGER,
            country TEXT,
            url TEXT
        );
CREATE TABLE session (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            movie_id INTEGER NOT NULL,
            host_id INTEGER,
            attendance INTEGER,
            FOREIGN KEY (movie_id) REFERENCES movies(id),
            FOREIGN KEY (host_id) REFERENCES host(id)
        );
