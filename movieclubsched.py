# Print the Movie Club schedule as CSV.
#

import csv
from sqlite3 import connect


def main():
    with connect("movie_club.db") as conn:
        cur = conn.cursor()
        query = """
        select movies.title, directors.name, movies.year, movies.country from movies 
        INNER JOIN directors on movies.director_id=directors.id 
        ORDER by screen_date;"""
        cur.execute(query)
        rows = cur.fetchall()
        print(len(rows))
        for row in rows:
            print(row)


if __name__ == "__main__":
    main()
