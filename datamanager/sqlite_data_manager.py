from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datamanager.data_manager_interface import DataManagerInterface

db = SQLAlchemy()

class SQLiteDataManager(DataManagerInterface):
    def __init__(self, app, db_file_name):
        self.app = app
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_file_name}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)

        with app.app_context():
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                  id       INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT NOT NULL UNIQUE
                );
            """))
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS movies (
                  id       INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id  INTEGER NOT NULL,
                  name     TEXT NOT NULL,
                  director TEXT NOT NULL,
                  year     INTEGER,
                  rating   REAL,
                  FOREIGN KEY(user_id) REFERENCES users(id)
                );
            """))
            db.session.commit()

    def get_all_users(self):
        rows = db.session.execute(text("SELECT id, username FROM users;")).fetchall()
        users = []
        for row in rows:
            users.append(dict(row._mapping))
        return users

    def get_user_movies(self, user_id):
        rows = db.session.execute(
            text("SELECT id, user_id, name, director, year, rating "
                 "FROM movies WHERE user_id = :user_id;"),
            {"user_id": user_id}
        ).fetchall()
        movies = []
        for row in rows:
            movies.append(dict(row._mapping))
        return movies

    def add_user(self, username):
        db.session.execute(
            text("INSERT INTO users (username) VALUES (:username);"),
            {"username": username}
        )
        db.session.commit()

    def add_movie(self, movie):
        db.session.execute(
            text("""
                   INSERT INTO movies (user_id, name, director, year, rating)
                   VALUES (:user_id, :name, :director, :year, :rating);
               """),
            {
                "user_id": movie["user_id"],
                "name": movie["name"],
                "director": movie["director"],
                "year": movie["year"],
                "rating": movie["rating"]
            }
        )
        db.session.commit()

    def update_movie(self, movie):
        db.session.execute(
            text("""
                UPDATE movies
                   SET user_id  = :user_id,
                       name     = :name,
                       director = :director,
                       year     = :year,
                       rating   = :rating
                 WHERE id = :id;
            """),
            {
                "id": movie["id"],
                "user_id": movie["user_id"],
                "name": movie["name"],
                "director": movie["director"],
                "year": movie["year"],
                "rating": movie["rating"]
            }
        )
        db.session.commit()

    def delete_movie(self, movie_id):
        db.session.execute(
            text("DELETE FROM movies WHERE id = :movie_id;"),
            {"movie_id": movie_id}
        )
        db.session.commit()
