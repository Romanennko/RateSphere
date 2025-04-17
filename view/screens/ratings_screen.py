from kivymd.uix.screen import MDScreen

class RatingsScreen(MDScreen):
    def show_error(self, message):
        """Displays an error message."""
        try:
            self.ids.error_label.text = message
        except KeyError:
             print(f"RatingsScreen: No id 'error_label' for message: {message}")