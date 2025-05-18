from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy

from datamanager.data_manager_interface import DataManagerInterface

db = SQLAlchemy()

class SQLiteDataManager(DataManagerInterface):
    """SQLite implementation of the data manager interface."""

    def __init__(self, app, db_file_name):
        """Initialize the database and create tables if they don't exist."""
        self.app = app
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_file_name}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)

        with app.app_context():
            # Create users table if it doesn't exist
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                  id       INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT NOT NULL UNIQUE
                );
            """))
            # Create movies table if it doesn't exist
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS movies (
                  id       INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id  INTEGER NOT NULL,
                  name     TEXT NOT NULL,
                  director TEXT NOT NULL,
                  year     INTEGER,
                  rating   REAL,
                  poster   TEXT,
                  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """))
            db.session.commit()

    def get_all_users(self):
        """Get all users."""
        query = text("SELECT id, username FROM users")
        rows = db.session.execute(query).fetchall()
        users = []
        for result_row in rows:
            # Convert row to dictionary
            user_dict = dict(result_row._mapping)
            users.append(user_dict)
        return users

    def get_user_movies(self, user_id):
        """Get movies for a specific user."""
        rows = db.session.execute(
            text(
                "SELECT id, user_id, name, director, year, rating, poster "
                 "FROM movies WHERE user_id = :user_id;"
            ),
            {"user_id": user_id}
        ).fetchall()
        movies = []
        for result_row in rows:
            # Convert row to dictionary
            movie_dict = dict(result_row._mapping)
            movies.append(movie_dict)
        return movies

    def add_user(self, username):
        """Add a new user."""
        db.session.execute(
            text("INSERT INTO users (username) VALUES (:username);"),
            {"username": username}
        )
        db.session.commit()

    def delete_user(self, user_id):
        """Delete a user."""
        db.session.execute(
            text("DELETE FROM users WHERE id = :user_id;"),
            {"user_id": user_id}
        )
        db.session.commit()

    def add_movie(self, movie):
        """Add a new movie."""
        db.session.execute(
            text("""
                INSERT INTO movies (
                    user_id, name, director, year, rating, poster
                ) VALUES (
                    :user_id, :name, :director, :year, :rating, :poster
                );
            """),
            {
                "user_id": movie["user_id"],
                "name": movie["name"],
                "director": movie["director"],
                "year": movie["year"],
                "rating": movie["rating"],
                "poster": movie["poster"]
            }
        )
        db.session.commit()

    def update_movie(self, movie):
        """Update a movie."""
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
        """Delete a movie."""
        db.session.execute(
            text("DELETE FROM movies WHERE id = :movie_id;"),
            {"movie_id": movie_id}
        )
        db.session.commit()

    def get_top_movies(self, limit=6):
        """Get top 6 rated movies."""
        rows = db.session.execute(
            text("""
                SELECT name, director, year, rating, poster
                FROM movies
                GROUP BY name
                ORDER BY rating DESC
                LIMIT :limit
            """),
            {"limit": limit}
        ).fetchall()

        movies = []
        for row in rows:
            movies.append(dict(row._mapping))
        return movies
