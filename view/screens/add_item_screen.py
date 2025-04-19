from kivymd.uix.screen import MDScreen
from kivymd.uix.menu import MDDropdownMenu

import logging

logger = logging.getLogger(__name__)

ITEM_STATUSES = ['Completed', 'In Progress', 'Planned', 'Dropped', 'Ongoing']
ITEM_TYPES = ['Movie', 'Manga', 'Manhwa', 'Manhua', 'Game', 'Anime', 'Cartoon', 'Series', 'Book', 'Board game']

class AddItemScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rating = None

        self.status_menu = None
        self.status_menu_items = self._create_menu_items(ITEM_STATUSES, self._set_status)

        self.type_menu = None
        self.type_menu_items = self._create_menu_items(ITEM_TYPES, self._set_type)

    def clear_fields(self):
        """Clears all input fields and resets states."""
        self.ids.item_name.text = ''
        self.ids.item_alt_name.text = ''
        self.ids.item_type.text = ''

        if hasattr(self.ids, 'status_button_text'):
            self.ids.status_button_text.text = "Select status"

        self.rating = None
        self.ids.item_review.text = ''

        if hasattr(self.ids, 'error_label'):
            self.ids.error_label.text = ''
        logger.debug("AddItemScreen fields cleared.")

    def _create_menu_items(self, items_list, callback):
        return [
            {
                "text": item,
                "on_release": lambda x=item: callback(x),
            } for item in items_list
        ]

    def open_status_menu(self, caller_widget):
        if not self.status_menu:
            self.status_menu = MDDropdownMenu(
                caller=caller_widget,
                items=self.status_menu_items,
            )
        self.status_menu.caller = caller_widget
        self.status_menu.open()

    def open_type_menu(self, caller_widget):
        if not self.type_menu:
            self.type_menu = MDDropdownMenu(
                caller=caller_widget,
                items=self.type_menu_items,
            )
        self.type_menu.caller = caller_widget
        self.type_menu.open()

    def _set_status(self, selected_status):
        if hasattr(self.ids, 'status_button_text'):
            self.ids.status_button_text.text = selected_status
        else:
            logger.warning("Status_button_text ID not found")
        if self.status_menu:
            self.status_menu.dismiss()

    def _set_type(self, selected_type):
        if hasattr(self.ids, 'type_button_text'):
            self.ids.type_button_text.text = selected_type
        else:
            logger.warning("Type_button_text ID not found")
        if self.type_menu:
            self.type_menu.dismiss()

    def on_rating_change(self, rating_value):
        self.rating = rating_value

    def get_rating(self):
        return self.rating

    def show_error(self, message):
        """Displays an error message."""
        self.ids.error_label.text = message