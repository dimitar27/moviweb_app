import os
from flask import Flask, render_template
from datamanager.sqlite_data_manager import SQLiteDataManager
from flask import request, redirect, url_for
from dotenv import load_dotenv
import requests

app = Flask(__name__, instance_relative_config=True)
os.makedirs(app.instance_path, exist_ok=True)

db_path = os.path.join(app.instance_path, "moviwebapp.db")
data_manager = SQLiteDataManager(app, db_path)

load_dotenv()
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

@app.route('/')
def home():
    return "Hello"

@app.route('/users')
def list_users():
    users = data_manager.get_all_users()
    return render_template('users.html', users=users)

@app.route('/users/<int:user_id>')
def user_movies(user_id):
    user = None
    movies = data_manager.get_user_movies(user_id)
    users = data_manager.get_all_users()
    for u in users:
        if u["id"] == user_id:
            user = u
            break
    return render_template('user_movies.html', user=user, movies=movies)

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        data_manager.add_user(username)
        return redirect(url_for('list_users'))
    return render_template('add_user.html')

@app.route('/users/<int:user_id>/add_movie', methods=['GET', 'POST'])
def add_movie(user_id):
    all_users = data_manager.get_all_users()
    user = None
    for u in all_users:
        if u["id"] == user_id:
            user = u
            break

    if user is None:
        return "User not found", 404

    if request.method == 'POST':
        title = request.form['title']

        url = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}"
        response = requests.get(url)
        data = response.json()

        if data.get('Response') == 'True':
            movie_title = data.get('Title', title)
            director = data.get('Director', 'Unknown')
            year = data.get('Year', '0')
            rating = data.get('imdbRating', '0')

            if year.isdigit():
                year = int(year)
            else:
                year = 0

            try:
                rating = float(rating)
            except ValueError:
                rating = 0.0

            movie = {
                "user_id": user_id,
                "name": movie_title,
                "director": director,
                "year": year,
                "rating": rating
            }

            data_manager.add_movie(movie)

            return redirect(url_for('user_movies', user_id=user_id))

        else:
            return f"Movie '{title}' not found in OMDb!", 400

    return render_template('add_movie.html', user=user)

@app.route('/users/<int:user_id>/update_movie/<int:movie_id>', methods=['GET', 'POST'])
def update_movie(user_id, movie_id):
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
        movie['rating'] = float(request.form['rating'])

        data_manager.update_movie(movie)

        return redirect(url_for('user_movies', user_id=user_id))

    return render_template('update_movie.html', user=user, movie=movie)

@app.route('/users/<int:user_id>/delete_movie/<int:movie_id>', methods=['POST'])
def delete_movie(user_id, movie_id):
    data_manager.delete_movie(movie_id)
    return redirect(url_for('user_movies', user_id=user_id))


if __name__ == "__main__":
    app.run(debug=True)