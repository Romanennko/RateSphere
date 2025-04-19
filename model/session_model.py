import os
import logging

from kivy.storage.jsonstore import JsonStore
from kivy.app import App

logger = logging.getLogger(__name__)

class SessionModel:
    def __init__(self):
        self._current_user_id = None
        self._current_username = None
        self.preferred_theme_style = "Light"
        self.store = None
        logger.debug("Initializing SessionModel...")

        try:
            app = App.get_running_app()
            if app:
                user_data_dir = app.user_data_dir
                logger.debug(f"Kivy user_data_dir: {user_data_dir}")
                if not os.path.exists(user_data_dir):
                    logger.info(f"Creating user_data_dir: {user_data_dir}")
                    try:
                        os.makedirs(user_data_dir)
                        logger.info("user_data_dir created.")
                    except OSError as e:
                        logger.error(f"Failed to create user_data_dir {user_data_dir}: {e}", exc_info=True)
                else:
                    logger.debug("user_data_dir already exists.")

                store_path = os.path.join(user_data_dir, 'session.json')
                logger.debug(f"Session store path: {store_path}")
                logger.debug("Initializing JsonStore...")
                self.store = JsonStore(store_path)
                logger.info(f"Session store initialized at: {store_path}")
                self._load_session()
                self._load_theme_preference()
            else:
                logger.warning(
                    "Could not get running app instance in SessionModel.__init__. Session/theme persistence might be disabled.")
                self.store = None

        except Exception as e:
            logger.exception("!!! ERROR initializing session store")
            self.store = None

    def _load_session(self):
        """Loads session data from storage. Logs errors."""
        if self.store and self.store.exists('user_info'):
            try:
                user_info = self.store.get('user_info')
                user_id = user_info.get('user_id')
                username = user_info.get('username')
                if user_id and username:
                    self._current_user_id = user_id
                    self._current_username = username
                    logger.info(f"Session loaded for user '{self._current_username}' (ID: {self._current_user_id})")
                else:
                    logger.warning("Loaded session data from store is incomplete or invalid. Clearing.")
                    self._clear_session_data()
            except Exception as e:
                logger.exception("Error loading session data from store. Clearing session.")
                self._clear_session_data()
        elif self.store:
            logger.info("No previous session data found in store.")
        else:
             logger.warning("Cannot load session, store is not available.")

    def _load_theme_preference(self):
        """Loads theme preference from storage. Logs errors."""
        if self.store and self.store.exists('theme_style'):
            try:
                stored_theme_data = self.store.get('theme_style')
                stored_theme = stored_theme_data.get('style')
                if stored_theme in ["Light", "Dark"]:
                    self.preferred_theme_style = stored_theme
                    logger.info(f"Theme preference loaded: {self.preferred_theme_style}")
                else:
                    logger.warning(f"Invalid theme style '{stored_theme}' found in store. Using default '{self.preferred_theme_style}' and saving default.")
                    self.save_theme_style(self.preferred_theme_style)
            except Exception as e:
                logger.exception(f"Error loading theme preference. Using default '{self.preferred_theme_style}'.")
        elif self.store:
             logger.info(f"No theme preference found in store. Using default '{self.preferred_theme_style}'.")
        else:
             logger.warning("Cannot load theme preference, store is not available.")

    def save_theme_style(self, theme_style):
        """Saves the selected theme style to storage. Logs errors."""
        if self.store is not None:
            try:
                self.store.put('theme_style', style=theme_style)
                logger.info(f"Theme preference saved: {theme_style}")
            except Exception as e:
                logger.exception(f"Error saving theme preference '{theme_style}'")
        else:
            logger.error("Cannot save theme, session store not initialized.")

    def get_preferred_theme_style(self):
        """Returns the loaded or default theme style."""
        return self.preferred_theme_style

    def _save_session(self):
        """Saves current session data to storage. Logs errors."""
        if self.store is not None and self._current_user_id and self._current_username:
            logger.debug("Attempting to save session data...")
            try:
                self.store.put('user_info',
                               user_id=self._current_user_id,
                               username=self._current_username)
                logger.info(f"Session data saved for user '{self._current_username}'.")
            except Exception as e:
                logger.exception(f"!!! ERROR saving session data for user '{self._current_username}'")
        elif self.store is None:
             logger.error("Cannot save session, store not initialized.")
        else:
            logger.debug("Session save condition not met (user data is None/empty). Session NOT saved.")

    def _clear_session_data(self):
        """Clears session data in memory and storage. Logs errors."""
        logger.debug("Clearing session data...")
        self._current_user_id = None
        self._current_username = None
        if self.store and self.store.exists('user_info'):
            try:
                self.store.delete('user_info')
                logger.info("Stored session data deleted.")
            except Exception as e:
                logger.exception("Error deleting session data from store.")
        elif self.store is None:
             logger.warning("Cannot clear session from store, store not initialized.")

    def login(self, username, user_id):
        """Saves logged-in user data and writes to storage."""
        logger.info(f"Session: User '{username}' (ID: {user_id}) attempting login.")
        self._current_username = username
        self._current_user_id = user_id
        self._save_session()

    def logout(self):
        """Resets session data."""
        if self._current_username:
            logger.info(f"Session: User '{self._current_username}' logging out.")
        else:
             logger.info("Session: Logout called, but no user was logged in.")
        self._clear_session_data()

    def is_logged_in(self):
        """Checks if a user is currently logged in."""
        logged_in = self._current_user_id is not None
        logger.debug(f"Checking login status: {logged_in}")
        return logged_in

    def get_current_user_id(self):
        return self._current_user_id

    def get_current_username(self):
        return self._current_username