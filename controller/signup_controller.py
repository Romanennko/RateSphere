import bcrypt
import re
import logging
from model.database_model import DatabaseError

logger = logging.getLogger(__name__)

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

class SignUpController:
    def __init__(self, models, view, app):
        self.data_model = models['database']    # Link to DatabaseModel
        self.session_model = models['session']  # Link to SessionModel
        self.view = view                        # Link to SignUpScreen
        self.app = app                          # Link to the main application class (for navigation)

        logger.debug("SignUpController initialized.")

    def do_signup(self, username, email, password, confirm_password):
        """Processes a registration attempt."""
        logger.info(f"Processing signup attempt for username: {username}")
        self.view.show_error("")

        if not all([username, email, password, confirm_password]):
            logger.warning("Signup failed: Not all fields were filled.")
            self.view.show_error("Please fill in all the fields")
            return

        if not re.match(EMAIL_REGEX, email):
             logger.warning(f"Signup failed: Invalid email format for {email}")
             self.view.show_error("Invalid email format")
             return

        if password != confirm_password:
            logger.warning("Signup failed: Passwords do not match.")
            self.view.show_error("Passwords do not match")
            return

        if len(password) < 6:
             logger.warning("Signup failed: Password too short.")
             self.view.show_error("Password must be at least 6 characters long")
             return

        try:
            if self.data_model.get_user_by_username(username):
                logger.warning(f"Signup failed: Username '{username}' is already taken.")
                self.view.show_error("This username is already taken")
                return

            if self.data_model.get_user_by_email(email):
                logger.warning(f"Signup failed: Email '{email}' is already registered.")
                self.view.show_error("This email is already registered")
                return

        except DatabaseError as e:
             logger.exception(f"Database error during signup validation for '{username}': {e}")
             self.view.show_error("Error checking user data. Please try again later.")
             return
        except Exception as e:
             logger.exception(f"Unexpected error during signup validation for '{username}': {e}")
             self.view.show_error("An unexpected error occurred. Please try again later.")
             return

        try:
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            hashed_pw_str = hashed_pw.decode('utf-8')
            logger.debug(f"Password hashed successfully for user '{username}'.")
        except Exception as e:
             logger.exception(f"Password hashing error for user '{username}': {e}")
             self.view.show_error("Password processing error. Please try again.")
             return

        try:
            user_id = self.data_model.add_user(username, email, hashed_pw_str)

            if user_id:
                logger.info(f"User '{username}' registered successfully with ID: {user_id}")
                self.session_model.login(username, user_id)
                logger.info(f"User '{username}' automatically logged in after registration.")
                self.app.screen_manager.current = "ratings"
            else:
                logger.error(f"User registration failed for '{username}' - add_user returned no ID.")
                self.view.show_error("Registration failed unexpectedly. Please try again later.")

        except DatabaseError as e:
             logger.exception(f"Database error during user insertion for '{username}': {e}")
             self.view.show_error("Failed to save user data. The username or email might already exist, or there was a server issue.")
             return
        except Exception as e:
             logger.exception(f"Unexpected error during user insertion for '{username}': {e}")
             self.view.show_error("An unexpected error occurred during registration. Please try again later.")
             return

    def go_to_login(self):
        """Transition to the login screen."""
        logger.debug("Navigating from signup to login screen.")
        self.view.show_error("")
        self.app.screen_manager.current = "login"