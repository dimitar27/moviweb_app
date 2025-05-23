import os

import requests
from dotenv import load_dotenv
from flask import Flask, render_template
from flask import flash
from flask import request, redirect, url_for

from datamanager.sqlite_data_manager import SQLiteDataManager

# Initialize Flask app
app = Flask(__name__, instance_relative_config=True)
app.secret_key = "dev"
os.makedirs(app.instance_path, exist_ok=True)

# Set up database and data manager
db_path = os.path.join(app.instance_path, "moviwebapp.db")
data_manager = SQLiteDataManager(app, db_path)

# Load OMDb API key
load_dotenv()
OMDB_API_KEY = os.getenv("OMDB_API_KEY")


@app.route('/')
def home():
    """Display the homepage with a list of top-rated movies."""
    movies = data_manager.get_top_movies()
    return render_template('home.html', recent_movies=movies)


@app.route('/users')
def list_users():
    """Display a list of all users."""
    try:
        users = data_manager.get_all_users()
        return render_template('users.html', users=users)
    except Exception as e:
        return f"Error loading users: {str(e)}", 500


@app.route('/users/<int:user_id>')
def user_movies(user_id):
    """
    Display movies for a specific user.

    Args:
        user_id (int): The ID of the user.

    Returns:
            Rendered template for user's movie list.
    """
    try:
        user = None
        movies = data_manager.get_user_movies(user_id)
        movies = list(reversed(movies))
        users = data_manager.get_all_users()
        for u in users:
            if u["id"] == user_id:
                user = u
                break
        return render_template('user_movies.html', user=user, movies=movies)
    except Exception as e:
        return f"Error loading user's movies: {str(e)}", 500


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    """
    Add a new user.

    GET: Render the user creation form.
    POST: Add user to database and redirect to user list.
    """
    try:
        if request.method == 'POST':
            username = request.form['username']
            data_manager.add_user(username)
            return redirect(url_for('list_users'))
        return render_template('add_user.html')
    except Exception as e:
        return f"Error adding user: {str(e)}", 500


@app.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    """
    Delete a user by ID.

    Args:
        user_id (int): The ID of the user to delete.
    """
    try:
        data_manager.delete_user(user_id)
        flash("User deleted successfully!", "success")
        return redirect(url_for('list_users'))
    except Exception as e:
        flash(f"Error deleting user: {str(e)}", "danger")
        return redirect(url_for('list_users'))


@app.route('/users/<int:user_id>/add_movie', methods=['GET', 'POST'])
def add_movie(user_id):
    """
    Add a movie to a user's collection.

    GET: Render the movie addition form.
    POST: Validate, fetch data from OMDb API, and add the movie.
    """
    all_users = data_manager.get_all_users()
    user = None
    for u in all_users:
        if u["id"] == user_id:
            user = u
            break

    if user is None:
        return "User not found", 404

    if request.method == 'POST':
        title = request.form['title'].strip().lower()
        existing_movies = data_manager.get_user_movies(user_id)

        for movie in existing_movies:
            if movie['name'].strip().lower() == title:
                flash('Movie already exists for this user.', 'warning')
                return redirect(url_for('add_movie', user_id=user_id))

        try:
            url = (
                f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}"
            )
            response = requests.get(url)
            data = response.json()
        except Exception as e:
            return f"Error fetching movie from OMDb: {str(e)}", 500

        if data.get('Response') == 'True':
            movie_title = data.get('Title', title)
            director = data.get('Director', 'Unknown')
            year = data.get('Year', '0')
            rating = data.get('imdbRating', '0')
            poster = data.get('Poster', '')

            year = int(year) if year.isdigit() else 0
            try:
                rating = float(rating)
            except ValueError:
                rating = 0.0

            movie = {
                "user_id": user_id,
                "name": movie_title,
                "director": director,
                "year": year,
                "rating": rating,
                "poster": poster
            }

            data_manager.add_movie(movie)
            # flash('Movie added successfully!', 'success')
            return redirect(url_for('user_movies', user_id=user_id))
        else:
            flash(f"Movie '{title}' not found in OMDb!", 'danger')
            return redirect(url_for('add_movie', user_id=user_id))

    return render_template('add_movie.html', user=user)


@app.route(
    '/users/<int:user_id>/update_movie/<int:movie_id>',
    methods=['GET', 'POST']
)
def update_movie(user_id, movie_id):
    """
    Update a specific movie in a user's collection.

    GET: Display pre-filled form.
    POST: Validate and save updated movie data.
    """
    try:
        user = None
        for u in data_manager.get_all_users():
            if u['id'] == user_id:
                user = u
                break
        if user is None:
            return "User not found", 404

        movies = data_manager.get_user_movies(user_id)
        movie = None
        for m in movies:
            if m['id'] == movie_id:
                movie = m
                break
        if movie is None:
            return "Movie not found", 404

        if request.method == 'POST':
            movie['name'] = request.form['name']
            movie['director'] = request.form['director']
            movie['year'] = int(request.form['year'])

            try:
                rating = float(request.form['rating'])
                if rating < 0 or rating > 10:
                    flash("Rating must be between 0 and 10.", "danger")
                    return redirect(request.url)
                movie['rating'] = rating
            except ValueError:
                flash("Invalid rating format.", "danger")
                return redirect(request.url)

            try:
                year = int(request.form['year'])
                if year < 1888 or year > 2100:
                    flash("Year must be between 1888 and 2100.", "danger")
                    return redirect(request.url)
                movie['year'] = year
            except ValueError:
                flash("Invalid year format.", "danger")
                return redirect(request.url)

            data_manager.update_movie(movie)
            return redirect(url_for('user_movies', user_id=user_id))

        return render_template('update_movie.html', user=user, movie=movie)

    except Exception as e:
        return f"Error updating movie: {str(e)}", 500


@app.route(
    '/users/<int:user_id>/delete_movie/<int:movie_id>',
    methods=['POST']
)
def delete_movie(user_id, movie_id):
    """
    Delete a specific movie from a user's collection.

    Args:
        user_id (int): The ID of the user.
        movie_id (int): The ID of the movie to delete.
    """
    try:
        data_manager.delete_movie(movie_id)
        return redirect(url_for('user_movies', user_id=user_id))
    except Exception as e:
        return f"Error deleting movie: {str(e)}", 500


@app.errorhandler(404)
def page_not_found(e):
    """Custom handler for 404 errors."""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    """Custom handler for 500 errors."""
    return render_template('500.html'), 500


if __name__ == "__main__":
    app.run(debug=True)
