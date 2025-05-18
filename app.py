import os
from flask import Flask, render_template
from datamanager.sqlite_data_manager import SQLiteDataManager
from flask import request, redirect, url_for
from dotenv import load_dotenv
import requests
from flask import flash

app = Flask(__name__, instance_relative_config=True)
app.secret_key = "dev"
os.makedirs(app.instance_path, exist_ok=True)

db_path = os.path.join(app.instance_path, "moviwebapp.db")
data_manager = SQLiteDataManager(app, db_path)

load_dotenv()
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

@app.route('/')
def home():
    try:
        recent_movies = data_manager.get_recent_movies(limit=6)  # or whatever number you prefer
        return render_template('home.html', recent_movies=recent_movies)
    except Exception as e:
        return f"Error loading home page: {str(e)}", 500

@app.route('/users')
def list_users():
    try:
        users = data_manager.get_all_users()
        return render_template('users.html', users=users)
    except Exception as e:
        return f"Error loading users: {str(e)}", 500

@app.route('/users/<int:user_id>')
def user_movies(user_id):
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
    try:
        data_manager.delete_user(user_id)
        flash("User deleted successfully!", "success")
        return redirect(url_for('list_users'))
    except Exception as e:
        flash(f"Error deleting user: {str(e)}", "danger")
        return redirect(url_for('list_users'))

@app.route('/users/<int:user_id>/add_movie', methods=['GET', 'POST'])
def add_movie(user_id):
    all_users = data_manager.get_all_users()
    user = next((u for u in all_users if u["id"] == user_id), None)

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
            url = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}"
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
            flash('Movie added successfully!', 'success')
            return redirect(url_for('user_movies', user_id=user_id))
        else:
            flash(f"Movie '{title}' not found in OMDb!", 'danger')
            return redirect(url_for('add_movie', user_id=user_id))

    return render_template('add_movie.html', user=user)

@app.route('/users/<int:user_id>/update_movie/<int:movie_id>', methods=['GET', 'POST'])
def update_movie(user_id, movie_id):
    try:
        user = next((u for u in data_manager.get_all_users() if u['id'] == user_id), None)
        if user is None:
            return "User not found", 404

        movies = data_manager.get_user_movies(user_id)
        movie = next((m for m in movies if m['id'] == movie_id), None)
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


@app.route('/users/<int:user_id>/delete_movie/<int:movie_id>', methods=['POST'])
def delete_movie(user_id, movie_id):
    try:
        data_manager.delete_movie(movie_id)
        return redirect(url_for('user_movies', user_id=user_id))
    except Exception as e:
        return f"Error deleting movie: {str(e)}", 500


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == "__main__":
    app.run(debug=True)