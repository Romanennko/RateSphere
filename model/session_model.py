import os
from kivy.storage.jsonstore import JsonStore
from kivy.app import App

class SessionModel:
    def __init__(self):
        self._current_user_id = None
        self._current_username = None
        self.store = None

        try:
            app = App.get_running_app()
            if app:
                user_data_dir = app.user_data_dir
                if not os.path.exists(user_data_dir):
                    os.makedirs(user_data_dir)
                store_path = os.path.join(user_data_dir, 'session.json')
                self.store = JsonStore(store_path)
                print(f"Session store initialized at: {store_path}")

                self._load_session()
            else:
                print("Warning: Could not get running app instance in SessionModel.__init__")

        except Exception as e:
            print(f"Error initializing session store: {e}")
            self.store = None

    def _load_session(self):
        """Loads session data from the repository."""
        if self.store and self.store.exists('user_info'):
            try:
                user_info = self.store.get('user_info')
                user_id = user_info.get('user_id')
                username = user_info.get('username')
                if user_id and username:
                    self._current_user_id = user_id
                    self._current_username = username
                    print(f"Session loaded for user '{self._current_username}' (ID: {self._current_user_id})")
                else:
                    print("Loaded session data is incomplete.")
                    self._clear_session_data()
            except Exception as e:
                print(f"Error loading session data from store: {e}")
                self._clear_session_data()

    def _save_session(self):
        """Saves the current session data to the repository."""
        if self.store and self._current_user_id and self._current_username:
            try:
                self.store.put('user_info',
                               user_id=self._current_user_id,
                               username=self._current_username)
                print(f"Session data saved for user '{self._current_username}'.")
            except Exception as e:
                print(f"Error saving session data: {e}")

    def _clear_session_data(self):
        """Clears session data in memory and storage."""
        self._current_user_id = None
        self._current_username = None
        if self.store and self.store.exists('user_info'):
            try:
                self.store.delete('user_info')
                print("Stored session data deleted.")
            except Exception as e:
                print(f"Error deleting session data from store: {e}")


    def login(self, username, user_id):
        """Saves the data of the logged-in user and writes it to the repository."""
        self._current_username = username
        self._current_user_id = user_id
        print(f"Session: User '{username}' (ID: {user_id}) logged in.")
        self._save_session()

    def logout(self):
        """Resets session data."""
        print(f"Session: User '{self._current_username}' logging out.")
        self._clear_session_data()

    def is_logged_in(self):
        """Checks if someone is logged in."""
        return self._current_user_id is not None

    def get_current_user_id(self):
        return self._current_user_id

    def get_current_username(self):
        return self._current_username