from kivymd.uix.screen import MDScreen

class LoginScreen(MDScreen):
    def show_error(self, message):
        """Displays an error message."""
        self.ids.error_label.text = message