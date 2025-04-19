import logging

logger = logging.getLogger(__name__)

class ProfileController:
    def __init__(self, models, view, app):
        self.data_model = models['database']    # Link to DatabaseModel
        self.session_model = models['session']  # Link to SessionModel
        self.view = view                        # Link to ProfileScreen
        self.app = app                          # Link to the main application class (for navigation)

        logger.debug('ProfileController initialized.')