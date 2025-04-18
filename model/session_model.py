import os
from kivy.storage.jsonstore import JsonStore
from kivy.app import App

class SessionModel:
    def __init__(self):
        self._current_user_id = None
        self._current_username = None

        self.preferred_theme_style = "Light"

        self.store = None

        try:
            app = App.get_running_app()
            print("DEBUG: Got app instance:", app is not None)
            if app:
                user_data_dir = app.user_data_dir
                print("DEBUG: user_data_dir:", user_data_dir)
                if not os.path.exists(user_data_dir):
                    print("DEBUG: Creating user_data_dir...")
                    os.makedirs(user_data_dir)
                    print("DEBUG: user_data_dir created.")
                else:
                    print("DEBUG: user_data_dir already exists.")

                store_path = os.path.join(user_data_dir, 'session.json')
                print("DEBUG: store_path:", store_path)
                print("DEBUG: Initializing JsonStore...")
                self.store = JsonStore(store_path)
                print(f"Session store initialized at: {store_path}")
                self._load_session()
                self._load_theme_preference()
            else:
                print("Warning: Could not get running app instance in SessionModel.__init__")

        except Exception as e:
            print(f"!!! ERROR initializing session store: {e}")
            import traceback
            traceback.print_exc()
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

    def _load_theme_preference(self):
        """Loads the theme preference from the repository."""
        if self.store and self.store.exists('theme_style'):
            try:
                stored_theme_data = self.store.get('theme_style')
                stored_theme = stored_theme_data.get('style')
                if stored_theme in ["Light", "Dark"]:
                    self.preferred_theme_style = stored_theme
                    print(f"Theme preference loaded: {self.preferred_theme_style}")
                else:
                    print("Warning: Invalid theme style found in store.")
                    self.save_theme_style(self.preferred_theme_style)
            except Exception as e:
                print(f"Error loading theme preference: {e}")

    def save_theme_style(self, theme_style):
        """Saves the selected theme style to the repository."""
        if self.store is not None:
            try:
                self.store.put('theme_style', style=theme_style)
                print(f"Theme preference saved: {theme_style}")
            except Exception as e:
                print(f"Error saving theme preference: {e}")
        else:
            print("Error: Cannot save theme, session store not initialized.")

    def get_preferred_theme_style(self):
        """Returns the loaded or default theme style."""
        return self.preferred_theme_style

    def _save_session(self):
        """Saves the current session data to the repository."""
        if self.store is not None and self._current_user_id and self._current_username:
            print("  - Save condition met. Calling store.put...")
            try:
                self.store.put('user_info',
                               user_id=self._current_user_id,
                               username=self._current_username)
                print(f"Session data saved for user '{self._current_username}'.")
            except Exception as e:
                print(f"!!! ERROR saving session data: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("  - Save condition NOT met (store is None or user data is None/empty). Session NOT saved.")

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