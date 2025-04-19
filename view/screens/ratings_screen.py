from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout

from kivymd.app import MDApp

import logging

from kivy.properties import StringProperty, NumericProperty

logger = logging.getLogger(__name__)

class RatingRowWidget(MDBoxLayout):
    name_text = StringProperty("")
    type_text = StringProperty("")
    status_text = StringProperty("")
    rating_text = StringProperty("")
    review_text = StringProperty("")
    # item_id = NumericProperty(0) # Can add an ID if needed for actions.

class RatingsScreen(MDScreen):
    def on_enter(self, *args):
        logger.debug(f"=====>> ENTERING screen: {self.name}")
        app = MDApp.get_running_app()
        if hasattr(app, 'ratings_controller'):
            app.ratings_controller.load_items()
        else:
             logger.debug("RatingsScreen Error: ratings_controller not found in app.")
        return super().on_enter(*args)

    def on_leave(self, *args):
        logger.debug(f"<<===== LEAVING screen: {self.name}")
        return super().on_leave(*args)

    def update_data(self, rv_data_from_controller):
        """
        Refreshes data in RecycleView.
        rv_data_from_controller is a list of dictionaries from the controller
        (keys: 'item_id', 'name', 'item_type', etc.).
        """
        if hasattr(self.ids, 'ratings_rv'):
            formatted_data = []
            for item_dict in rv_data_from_controller:
                review_display = "..." if item_dict.get('review') else "" # Show ... if there is a review
                formatted_data.append({
                    "name_text": str(item_dict.get('name', '')),
                    "type_text": str(item_dict.get('item_type', '')),
                    "status_text": str(item_dict.get('status', '')),
                    "rating_text": str(item_dict.get('rating', '')),
                    "review_text": review_display,
                    # "item_id": item_dict.get('item_id') # If add the item_id property
                })

            logger.debug(f"RatingsScreen: Updating RecycleView data with {len(formatted_data)} items.")
            self.ids.ratings_rv.data = formatted_data
            self.ids.ratings_rv.refresh_from_data()
        else:
             logger.error("RatingsScreen Error: ratings_rv ID not found.")

    def show_error(self, message):
        """Displays an error message."""
        logger.error(f"RatingsScreen Error: {message}")