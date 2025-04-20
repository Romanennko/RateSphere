import logging
from model.database_model import DatabaseError, DatabaseModel
from view.screens.add_item_screen import AddItemScreen

logger = logging.getLogger(__name__)

OVERALL_CRITERION_NAME = "Total score"

class AddItemController:
    data_model: DatabaseModel
    view: AddItemScreen

    def __init__(self, models, view, app):
        self.data_model = models['database']    # Link to DatabaseModel
        self.session_model = models['session']  # Link to SessionModel
        self.view = view                        # Link to AddItemScreen
        self.app = app                          # Link to the main application class (for navigation)

        logger.debug("AddItemController initialized.")

    def save_item(self, name, alt_name, item_type, status, review, rating_data):
        """
        Saves a new item or updates an existing one based on view.edit_mode.
        Handles basic info and criteria ratings.
        """
        if self.view.edit_mode:
            logger.info(f"Attempting to UPDATE item ID: {self.view.item_to_edit_id}")
            self._update_existing_item(name, alt_name, item_type, status, review, rating_data)
        else:
            logger.info(f"Attempting to ADD new item: '{name}'")
            self._add_new_item(name, alt_name, item_type, status, review, rating_data)

    def _add_new_item(self, name, alt_name, item_type, status, review, rating_data):
        """Handles logic for adding a completely new item."""
        current_user_id = self.session_model.get_current_user_id()
        if not current_user_id:
            logger.error("Cannot add item: User is not authorized.")
            self.view.show_error("Error: User session expired. Please log in again.")
            self.app.screen_manager.current = "login"
            return

        if not name or not name.strip():
            self.view.show_error("Error: Item name is required.")
            return
        clean_name = name.strip()
        clean_alt_name = alt_name.strip() if alt_name else None
        clean_review = review.strip() if review else None
        if not item_type or item_type == "Select type":
            self.view.show_error("Error: Item type must be selected.")
            return
        if not status or status == "Select status":
            self.view.show_error("Error: Status must be selected.")
            return
        if not rating_data:
            self.view.show_error("Error: Rating must be provided.")
            return

        item_id = None
        try:
            item_id = self.data_model.add_rated_item(
                user_id=current_user_id, name=clean_name, alt_name=clean_alt_name,
                item_type=item_type, status=status, review=clean_review
            )
            if not item_id: raise DatabaseError("Failed to get item_id after insertion.")

            self._process_and_save_ratings(item_id, rating_data)

            logger.info(f"New item '{clean_name}' (ID: {item_id}) added successfully.")
            self.view.clear_fields()
            self.app.screen_manager.current = "ratings"

        except DatabaseError as e:
            logger.exception(f"Database error while adding item '{clean_name}': {e}")
            self.view.show_error("Failed to save item or ratings. Database error.")
        except Exception as e:
            logger.exception(f"Unexpected error while adding item '{clean_name}': {e}")
            self.view.show_error("An unexpected error occurred during saving.")

    def _update_existing_item(self, name, alt_name, item_type, status, review, rating_data):
        """Handles logic for updating an existing item."""
        item_id = self.view.item_to_edit_id
        if not item_id:
            logger.error("Cannot update item: item_to_edit_id is not set in the view.")
            self.view.show_error("Error: Cannot update item, ID missing.")
            return

        if not name or not name.strip():
            self.view.show_error("Error: Item name is required.")
            return
        clean_name = name.strip()
        clean_alt_name = alt_name.strip() if alt_name else None
        clean_review = review.strip() if review else None
        if not item_type or item_type == "Select type":
            self.view.show_error("Error: Item type must be selected.")
            return
        if not status or status == "Select status":
            self.view.show_error("Error: Status must be selected.")
            return
        if not rating_data:
            self.view.show_error("Error: Rating must be provided.")
            return

        try:
            self.data_model.update_rated_item(
                item_id=item_id, name=clean_name, alt_name=clean_alt_name,
                item_type=item_type, status=status, review=clean_review
            )
            logger.info(f"Basic info for item {item_id} updated.")

            overall_criterion = self.data_model.get_overall_criterion()
            overall_criterion_id = overall_criterion['criterion_id'] if overall_criterion else -1

            criteria_names_to_keep = set(rating_data.keys())
            criteria_ids_to_keep = set()
            if overall_criterion_id != -1:
                criteria_ids_to_keep.add(overall_criterion_id)

            for name in criteria_names_to_keep:
                criterion = self.data_model.get_criterion_by_name(name, use_dict_cursor=True)
                if criterion:
                    criteria_ids_to_keep.add(criterion['criterion_id'])

            self.data_model.delete_criteria_ratings_except(item_id, list(criteria_ids_to_keep))

            self._process_and_save_ratings(item_id, rating_data)

            logger.info(f"Item {item_id} updated successfully.")
            self.app.screen_manager.current = "ratings"

        except DatabaseError as e:
            logger.exception(f"Database error while updating item {item_id}: {e}")
            self.view.show_error("Failed to update item or ratings. Database error.")
        except Exception as e:
            logger.exception(f"Unexpected error while updating item {item_id}: {e}")
            self.view.show_error("An unexpected error occurred during update.")

    def _process_and_save_ratings(self, item_id, rating_data):
        """
        Processes rating_data (overall or criteria), saves individual criterion ratings,
        and updates the overall calculated rating.
        Raises DatabaseError on failure.
        """
        if not rating_data:
            logger.warning(f"No rating data provided for item {item_id}. Overall rating might become NULL.")
            self.data_model.update_overall_rating(item_id)
            return

        overall_rating_value = rating_data.get(OVERALL_CRITERION_NAME)

        if overall_rating_value is not None:
            logger.info(f"Processing direct overall rating for item {item_id}.")
            overall_criterion = self.data_model.get_overall_criterion()
            if not overall_criterion:
                logger.error(f"Cannot save overall rating: '{OVERALL_CRITERION_NAME}' criterion not found!")
                raise DatabaseError(f"'{OVERALL_CRITERION_NAME}' criterion definition missing.")

            overall_criterion_id = overall_criterion['criterion_id']
            try:
                rating_val = float(overall_rating_value)
                if not (1.0 <= rating_val <= 10.0):
                    raise ValueError("Rating out of range")
            except (ValueError, TypeError):
                logger.error(f"Invalid value '{overall_rating_value}' provided for {OVERALL_CRITERION_NAME}.")
                raise ValueError(f"Invalid value for {OVERALL_CRITERION_NAME}.")

            self.data_model.add_or_update_criterion_rating(item_id, overall_criterion_id, rating_val)
            self.data_model.update_overall_rating(item_id, direct_overall_rating=rating_val)
            logger.info(f"Saved direct overall rating {rating_val} for item {item_id}.")

        else:
            logger.info(f"Processing criteria ratings for item {item_id}.")
            if not isinstance(rating_data, dict) or not rating_data:
                logger.warning(
                    f"No valid criteria ratings provided for item {item_id}. Updating overall rating (might become NULL).")
            else:
                saved_count = 0
                for criterion_name, criterion_rating in rating_data.items():
                    if criterion_rating is None: continue
                    try:
                        rating_val = float(criterion_rating)
                        if not (1.0 <= rating_val <= 10.0): continue
                    except (ValueError, TypeError):
                        continue

                    criterion = self.data_model.get_criterion_by_name(criterion_name)
                    if criterion:
                        criterion_id = criterion['criterion_id']
                        self.data_model.add_or_update_criterion_rating(item_id, criterion_id, rating_val)
                        saved_count += 1
                    else:
                        logger.warning(
                            f"Criterion '{criterion_name}' not found in DB. Skipping rating for item {item_id}.")

                logger.info(f"Saved/Updated {saved_count} criteria ratings for item {item_id}.")

            self.data_model.update_overall_rating(item_id)