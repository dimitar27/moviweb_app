import os
from flask import Flask, render_template
from datamanager.sqlite_data_manager import SQLiteDataManager

app = Flask(__name__, instance_relative_config=True)
os.makedirs(app.instance_path, exist_ok=True)

db_path = os.path.join(app.instance_path, "moviwebapp.db")
data_manager = SQLiteDataManager(app, db_path)

@app.route('/')
def home():
    return "Hello"

@app.route('/users')
def list_users():
    users = data_manager.get_all_users()
    return render_template('users.html', users=users)

@app.route('/users/<int:user_id>')
def user_movies(user_id):
    pass

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    pass

@app.route('/users/<int:user_id>/add_movie', methods=['GET', 'POST'])
def add_movie(user_id):
    pass

@app.route('/users/<int:user_id>/update_movie/<int:movie_id>', methods=['GET', 'POST'])
def update_movie(user_id, movie_id):
    pass

@app.route('/users/<int:user_id>/delete_movie/<int:movie_id>', methods=['POST'])
def delete_movie(user_id, movie_id):
    pass

if __name__ == "__main__":
    app.run(debug=True)