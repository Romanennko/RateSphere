import bcrypt
import logging
from model.database_model import DatabaseError

logger = logging.getLogger(__name__)

class LoginController:
    def __init__(self, models, view, app):
        self.data_model = models['database']    # Link to DatabaseModel
        self.session_model = models['session']  # Link to SessionModel
        self.view = view                        # Link to LoginScreen
        self.app = app                          # Link to the main application class (for navigation)

        logger.debug("LoginController initialized.")

    def do_login(self, username, password):
        """Processes a user login attempt."""
        logger.info(f"Processing login attempt for user: {username}")
        self.view.show_error("")

        if not all([username, password]):
            logger.info(f"Login failed: Not all fields were filled.")
            self.view.show_error("Please fill in all the fields.")

        try:
            user_data = self.data_model.get_user_by_username(username)

            if user_data:
                stored_user_id = user_data['user_id']
                stored_username = user_data['username']
                stored_email = user_data['email']
                stored_hash = user_data['password_hash']

                if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                    self.session_model.login(stored_username, stored_user_id)
                    logger.info(f"User '{username}' logged in successfully.")
                    self.app.screen_manager.current = "ratings"
                else:
                    logger.warning(f"User '{username}' logged in failed.")
                    self.view.show_error("Invalid username or password")
            else:
                logger.warning(f"User '{username}' logged in failed.")
                self.view.show_error("Invalid username or password")
        except DatabaseError as e:
            logger.exception(f"Database error during login validation for '{username}': {e}")
            self.view.show_error("Error checking user data. Please try again later.")
            return
        except Exception as e:
            logger.exception(f"Unexpected error during login validation for '{username}': {e}")
            self.view.show_error("An unexpected error occurred. Please try again later.")
            return


    def go_to_signup(self):
        """Transition to the registration screen."""
        logger.info("Navigation from login to signup screen.")
        self.view.show_error("")
        self.app.screen_manager.current = "signup"