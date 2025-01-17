# Print the Movie Club schedule as CSV.
#

from csv import writer
from sqlite3 import connect
from datetime import date

def date2screen(datedb: str) -> str:
    """Convert a date in format YYYY-DD-MM" to date for "humans"
    like 'Friday, Jan. 17, 2025'"""
    screen_date = date.fromisoformat(datedb)
    return screen_date.strftime("%a, %b %d, %Y")
    
    
def main():
    sched = []
    with connect("movie_club.db") as conn:
        cur = conn.cursor()
        cur.execute("""select movies.title, directors.name, movies.year, 
        movies.country, movies.screen_date from movies INNER JOIN directors on 
        movies.director_id=directors.id ORDER by screen_date;""")
        rows = cur.fetchall()
        for row in rows:
            ll = list(row)
            ll[4] = date2screen(row[4])
            sched.append(ll)
            print(ll)
    with open('movie_sched.csv', 'w', newline='') as csvfile:
        sched_writer = writer(csvfile, dialect='unix')
        for ll in sched:
            sched_writer.writerow(ll)
                    
if __name__ == "__main__":
    main()
