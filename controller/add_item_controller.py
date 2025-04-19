import logging
from model.database_model import DatabaseError

logger = logging.getLogger(__name__)

class AddItemController:
    def __init__(self, models, view, app):
        self.data_model = models['database']    # Link to DatabaseModel
        self.session_model = models['session']  # Link to SessionModel
        self.view = view                        # Link to AddItemScreen
        self.app = app                          # Link to the main application class (for navigation)

        logger.debug("AddItemController initialized.")

    def save_new_item(self, name, alt_name, item_type, status, rating, review):
        """Saves a new item entered by the user."""
        logger.info(f"Attempting to save new item: '{name}'")
        self.view.show_error("")

        current_user_id = self.session_model.get_current_user_id()
        if not current_user_id:
            logger.error("Cannot save item: User is not authorized (no user_id in session).")
            self.view.show_error("Error: User session expired or invalid. Please log in again.")
            self.app.screen_manager.current = "login"
            return

        if not name or not name.strip():
            logger.warning("Add item failed: Item name is required.")
            self.view.show_error("Error: Item name is required.")
            return

        clean_name = name.strip()
        clean_alt_name = alt_name.strip() if alt_name else None
        clean_review = review.strip() if review else None

        if not item_type:
            logger.warning("Add item failed: Item type must be selected.")
            self.view.show_error("Error: Item type must be selected.")
            return

        if not status:
            logger.warning("Add item failed: Status must be selected.")
            self.view.show_error("Error: Status must be selected.")
            return

        if rating is None:
            logger.warning("Add item failed: Rating must be selected.")
            self.view.show_error("Error: Rating must be selected.")
            return
        try:
             rating_float = float(rating)
             if not (1 <= rating_float <= 10):
                  raise ValueError("Rating out of range 1-10")
        except (ValueError, TypeError):
             logger.warning(f"Add item failed: Invalid rating value '{rating}'.")
             self.view.show_error("Error: Invalid rating value (must be 1-10).")
             return


        try:
            new_item_id = self.data_model.add_rated_item(
                user_id=current_user_id,
                name=clean_name,
                alt_name=clean_alt_name,
                item_type=item_type,
                status=status,
                rating=rating_float,
                review=clean_review
            )

            logger.info(f"New item '{clean_name}' added successfully with ID: {new_item_id} for user {current_user_id}")
            self.view.clear_fields()
            self.app.screen_manager.current = "ratings"

        except DatabaseError as e:
             logger.exception(f"Database error while adding item '{clean_name}' for user {current_user_id}: {e}")
             self.view.show_error("Failed to save item. A database error occurred. Please try again later.")
        except Exception as e:
             logger.exception(f"Unexpected error while adding item '{clean_name}' for user {current_user_id}: {e}")
             self.view.show_error("An unexpected error occurred while saving. Please try again later.")