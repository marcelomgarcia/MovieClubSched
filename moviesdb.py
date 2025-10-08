import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    import sqlalchemy

    DATABASE_URL = "sqlite:///movie_club.db"
    engine = sqlalchemy.create_engine(DATABASE_URL)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# Managing Movies Database""")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
