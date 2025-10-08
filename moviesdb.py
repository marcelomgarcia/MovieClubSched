import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    import sqlite3
    import polars
    return


@app.cell
def _():
    import sqlalchemy

    DATABASE_URL = "sqlite:///movie_club.db"
    engine = sqlalchemy.create_engine(DATABASE_URL)
    return (engine,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# Managing Movies Database""")
    return


@app.cell
def _(engine, mo):
    df_dir = mo.sql(
        f"""
        SELECT * FROM directors LIMIT 10
        """,
        engine=engine
    )
    return


@app.cell
def _(engine, mo):
    df_moviesby = mo.sql(
        f"""
        SELECT movies.title,directors.name from movies INNER JOIN directors ON movies.director_id = directors.id
        """,
        engine=engine
    )
    return


if __name__ == "__main__":
    app.run()
