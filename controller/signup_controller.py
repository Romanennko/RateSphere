import bcrypt
import re

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

class SignUpController:
    def __init__(self, models, view, app):
        self.data_model = models['database']    # Link to DatabaseModel
        self.session_model = models['session']  # Link to SessionModel
        self.view = view                        # Link to SignUpScreen
        self.app = app                          # Link to the main application class (for navigation)

    def do_signup(self, username, email, password, confirm_password):
        """Processes a registration attempt."""
        self.view.show_error("")

        if not all([username, email, password, confirm_password]):
            self.view.show_error("Please fill in all the fields")
            return

        if not re.match(EMAIL_REGEX, email):
             self.view.show_error("Invalid email format")
             return

        if password != confirm_password:
            self.view.show_error("Passwords do not match")
            return

        if len(password) < 6:
             self.view.show_error("Password must be at least 6 characters long")
             return

        if self.data_model.get_user_by_username(username):
            self.view.show_error("This username is already taken")
            return

        if self.data_model.get_user_by_email(email):
            self.view.show_error("This email is already registered")
            return

        try:
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            hashed_pw_str = hashed_pw.decode('utf-8')
        except Exception as e:
             print(f"Password hashing error: {e}")
             self.view.show_error("Password processing error")
             return

        user_id = self.data_model.add_user(username, email, hashed_pw_str)

        if user_id:
            print(f"User '{username}' registered successfully with ID: {user_id}")

            self.session_model.login(username, user_id)

            self.app.screen_manager.current = "ratings"
        else:
            self.view.show_error("An error occurred during registration. Please try again later.")

    def go_to_login(self):
        """Transition to the login screen."""
        self.view.show_error("")
        self.app.screen_manager.current = "login"