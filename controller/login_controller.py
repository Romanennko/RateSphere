import bcrypt

class LoginController:
    def __init__(self, models, view, app):
        self.data_model = models['database']    # Link to DatabaseModel
        self.session_model = models['session']  # Link to SessionModel
        self.view = view                        # Link to LoginScreen
        self.app = app                          # Link to the main application class (for navigation)

    def do_login(self, username, password):
        """Processes a user login attempt."""
        self.view.show_error("")

        if not username or not password:
            self.view.show_error("Please fill in all the fields")
            return

        user_data = self.data_model.get_user_by_username(username)

        if user_data:
            stored_user_id, stored_username, stored_email, stored_hash = user_data

            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                self.session_model.login(stored_username, stored_user_id)
                print(f"User '{username}' logged in successfully.")
                self.app.screen_manager.current = "ratings"
            else:
                self.view.show_error("Invalid username or password")
        else:
            self.view.show_error("Invalid username or password")

    def go_to_signup(self):
        """Transition to the registration screen."""
        self.view.show_error("")
        self.app.screen_manager.current = "signup"