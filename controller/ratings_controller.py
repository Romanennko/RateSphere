class RatingsController:
    def __init__(self, models, view, app):
        self.data_model = models['database']    # Link to DatabaseModel
        self.session_model = models['session']  # Link to SessionModel
        self.view = view                        # Link to RatingsScreen
        self.app = app                          # Link to the main application class (for navigation)