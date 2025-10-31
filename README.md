MovieClubSched
==============

A system to manage the movies, sessions and generate the schedule of Movie Club.

# Requirements

The system should:

* Add movies to the database.
* Query if a movie was already shown.
    * When the movie was exbited?
    * What was the attenance?
    * Who was the host?
* Reports:
    * Which movies were exibited last month?
    * Which is the average attendance?

# Entity Relationship

Diagram of the database tables:

```mermaid
erDiagram
    direction LR
    MOVIES ||--|{ MOVIEDIRECTOR  : directs
    MOVIES {
        id int
        title string
        year_release string
        country_origina string
    }
    MOVIEDIRECTOR }|--|| DIRECTORS: directs
    MOVIEDIRECTOR {
        movie_id int
        director_id int
        director_ord int
    }
    DIRECTORS {
        id int
        fname string
        lname string
    }
    SESSION }|--|| MOVIES : screens
    SESSION {
        id int
        date timedate
        movie_id int
        host_id int

    }
    HOST ||..|{ SESSION : hosts
    HOST {
        id int
        fname string
        lname string
    }
```


# Classes

* Director
* Movie
* Session
* Host

## Class Diretor

* Fields:
    * First and last names.
    * Movies

* Methods:
    * Add (init) director object with name.
    * Add movie.
