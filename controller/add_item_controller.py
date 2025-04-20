import logging
from model.database_model import DatabaseError

logger = logging.getLogger(__name__)

OVERALL_CRITERION_NAME = "Total score"

class AddItemController:
    def __init__(self, models, view, app):
        self.data_model = models['database']    # Link to DatabaseModel
        self.session_model = models['session']  # Link to SessionModel
        self.view = view                        # Link to AddItemScreen
        self.app = app                          # Link to the main application class (for navigation)

        logger.debug("AddItemController initialized.")

    def save_new_item(self, name, alt_name, item_type, status, review, rating_data):
        """
        Saves a new item and its criteria ratings.
        rating_data is a dictionary:
          - {'Total score': 8.0} if overall rating was used
          - {'Criterion A': 7.5, 'Criterion B': 9.0, ...} if criteria were rated
          - None or {} if no rating was provided.
        """
        logger.info(f"Attempting to save new item: '{name}' with rating data: {rating_data}")
        self.view.show_error("")

        current_user_id = self.session_model.get_current_user_id()
        if not current_user_id:
            logger.error("Cannot save item: User is not authorized.")
            self.view.show_error("Error: User session expired. Please log in again.")
            self.app.screen_manager.current = "login"
            return

        if not name or not name.strip():
            logger.warning("Add item failed: Item name is required.")
            self.view.show_error("Error: Item name is required.")
            return

        clean_name = name.strip()
        clean_alt_name = alt_name.strip() if alt_name else None
        clean_review = review.strip() if review else None

        if not item_type or item_type == "Select type":
            logger.warning("Add item failed: Item type must be selected.")
            self.view.show_error("Error: Item type must be selected.")
            return

        if not status or status == "Select status":
            logger.warning("Add item failed: Status must be selected.")
            self.view.show_error("Error: Status must be selected.")
            return

        if not rating_data:
             logger.warning(f"Add item failed: Rating data is missing for '{clean_name}'.")
             self.view.show_error("Error: Rating must be provided (either overall or by criteria).")
             return

        new_item_id = None
        try:
            new_item_id = self.data_model.add_rated_item(
                user_id=current_user_id,
                name=clean_name,
                alt_name=clean_alt_name,
                item_type=item_type,
                status=status,
                review=clean_review
            )

            if not new_item_id:
                raise DatabaseError("Failed to get item_id after insertion.")

            logger.info(f"Basic info for item '{clean_name}' saved with ID: {new_item_id}.")

            overall_rating_value = rating_data.get(OVERALL_CRITERION_NAME)

            if overall_rating_value is not None:
                logger.info(f"Processing direct overall rating for item {new_item_id}.")
                overall_criterion = self.data_model.get_overall_criterion()
                if not overall_criterion:
                     logger.error(f"Cannot save overall rating: '{OVERALL_CRITERION_NAME}' criterion not found in DB!")
                     self.view.show_error("Error: Could not find 'Total score' definition.")
                     return

                overall_criterion_id = overall_criterion['criterion_id']

                self.data_model.add_or_update_criterion_rating(
                    item_id=new_item_id,
                    criterion_id=overall_criterion_id,
                    rating=float(overall_rating_value)
                )

                self.data_model.update_overall_rating(
                    item_id=new_item_id,
                    direct_overall_rating=float(overall_rating_value)
                )
                logger.info(f"Saved direct overall rating {overall_rating_value} for item {new_item_id}.")

            else:
                logger.info(f"Processing criteria ratings for item {new_item_id}.")
                if not isinstance(rating_data, dict) or not rating_data:
                     logger.warning(f"No valid criteria ratings provided for item {new_item_id}, but overall was not set either.")
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
                            self.data_model.add_or_update_criterion_rating(
                                item_id=new_item_id,
                                criterion_id=criterion_id,
                                rating=rating_val
                            )
                            saved_count += 1
                        else:
                            logger.warning(f"Criterion '{criterion_name}' not found in DB. Skipping rating.")

                    logger.info(f"Saved {saved_count} criteria ratings for item {new_item_id}.")
                    self.data_model.update_overall_rating(item_id=new_item_id)


            logger.info(f"Item '{clean_name}' and ratings saved successfully for user {current_user_id}")
            self.view.clear_fields()
            self.app.screen_manager.current = "ratings"

        except DatabaseError as e:
             logger.exception(f"Database error while saving item '{clean_name}' or its ratings: {e}")
             self.view.show_error("Failed to save item or ratings. A database error occurred.")
        except Exception as e:
             logger.exception(f"Unexpected error while saving item '{clean_name}': {e}")
             self.view.show_error("An unexpected error occurred while saving.")
