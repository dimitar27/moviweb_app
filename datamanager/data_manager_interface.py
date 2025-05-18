from abc import ABC, abstractmethod
class DataManagerInterface(ABC):
    """Interface for user and movie data operations."""

    @abstractmethod
    def get_all_users(self):
        """Get all users."""
        pass

    @abstractmethod
    def get_user_movies(self, user_id):
        """Get all movies for a user."""
        pass

    @abstractmethod
    def add_user(self, username):
        """Add a new user."""
        pass

    @abstractmethod
    def add_movie(self, movie):
        """Add a new movie."""
        pass

    @abstractmethod
    def update_movie(self, movie):
        """Update a movie."""
        pass

    @abstractmethod
    def delete_movie(self, movie_id):
        """Delete a movie."""
        pass