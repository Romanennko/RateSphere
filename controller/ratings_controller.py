import logging
from model.database_model import DatabaseError

logger = logging.getLogger(__name__)

class RatingsController:
    def __init__(self, models, view, app):
        self.data_model = models['database']    # Link to DatabaseModel
        self.session_model = models['session']  # Link to SessionModel
        self.view = view                        # Link to RatingsScreen
        self.app = app                          # Link to the main application class (for navigation)

        self.current_sort_column = 'created_at'
        self.current_sort_order = 'DESC'

        logger.debug('RatingsController initialized.')

    def load_items(self):
        """Loads the rated user items and updates the View."""
        user_id = self.session_model.get_current_user_id()
        if not user_id:
            logger.warning("RatingsController Error: Cannot load items, user not logged in.")
            self.view.update_data([])
            return

        try:
            items_raw = self.data_model.get_user_items(
                user_id=user_id,
                sort_by=self.current_sort_column,
                sort_order=self.current_sort_order,
                use_dict_cursor=True,
            )

            rv_data = []
            if items_raw:
                for row in items_raw:
                    rv_data.append({
                        'item_id': row['item_id'], # ID may be required for actions with the line
                        'name': row['name'],
                        'alt_name': row['alt_name'],
                        'item_type': row['item_type'],
                        'status': row['status'],
                        'rating': row['rating'],
                        'review': row['review'],
                        'viewclass': 'RatingRowWidget'
                    })

            self.view.update_data(rv_data)
        except DatabaseError as e:
            logger.exception(f"Database error while loading items: {e}")
            self.view.show_error("Failed to load ratings. Check logs.")
            self.view.update_data([])
        except Exception as e:
            logger.exception(f"RatingsController Error loading items: {e}")
            self.view.show_error("An unexpected error occurred while loading ratings.")
            self.view.update_data([])

    def sort_by(self, column_name):
        """
        Sets the sorting column and order, then reloads items.
        Toggles order if the same column is clicked again.
        """
        logger.debug(f"Sort requested by column: {column_name}")

        allowed_sort_columns = ['name', 'item_type', 'status', 'rating', 'created_at', 'updated_at']
        if column_name not in allowed_sort_columns:
            logger.warning(f"Attempted to sort by invalid column: {column_name}")
            return

        if self.current_sort_column == column_name:
            self.current_sort_order = 'DESC' if self.current_sort_order == 'ASC' else 'ASC'
            logger.debug(f"Toggled sort order to: {self.current_sort_order}")
        else:
            self.current_sort_column = column_name
            if column_name in ['rating', 'created_at', 'updated_at']:
                self.current_sort_order = 'DESC'
            else:
                self.current_sort_order = 'ASC'
            logger.debug(f"Set sort column to: {self.current_sort_column}, order: {self.current_sort_order}")

        self.load_items()

    def delete_item(self, item_id):
        """Handles the item deletion process."""
        if not item_id:
            logger.error("Delete item called with invalid item_id (None or 0).")
            self.view.show_error("Cannot delete item: Invalid ID.")
            return

        logger.info(f"Attempting to delete item with id: {item_id}")
        try:
            success = self.data_model.delete_rated_item(item_id)

            if success:
                logger.info(f"Item {item_id} deleted successfully from database.")
                self.load_items()
            else:
                logger.error(f"Failed to delete item {item_id} (model returned False).")

        except DatabaseError as e:
            logger.exception(f"Database error occurred while deleting item {item_id}: {e}")
            self.view.show_error("Failed to delete item due to a database error.")
        except Exception as e:
            logger.exception(f"Unexpected error occurred while deleting item {item_id}: {e}")
            self.view.show_error("An unexpected error occurred during deletion.")