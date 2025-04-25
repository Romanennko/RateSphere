import logging

from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemTertiaryText
from kivymd.uix.screen import MDScreen
from kivymd.uix.menu import MDDropdownMenu

from kivy.metrics import dp
from kivymd.app import MDApp
from kivy.properties import ColorProperty

logger = logging.getLogger(__name__)

ALLOWED_SORT_COLUMNS = {
     'created_at': 'Date Added',
     'name': 'Name',
     'item_type': 'Type',
     'status': 'Status',
     'rating': 'Rating',
     'updated_at': 'Date Updated'
 }
ALLOWED_SORT_ORDERS = ['ASC', 'DESC']

class ProfileScreen(MDScreen):
    feedback_color = ColorProperty(None)

    sort_column_menu = None
    sort_order_menu = None

    def on_pre_enter(self, *args):
        """Load profile data, clear password fields, and update sort settings."""
        logger.debug(f"=====>> ENTERING screen: {self.name}")
        app = MDApp.get_running_app()

        self.clear_password_fields()
        self.show_password_feedback("")
        self.show_settings_feedback("")

        if hasattr(app, 'profile_controller'):
            app.profile_controller.load_profile_data()
            self._load_and_display_current_sort_settings()
        else:
             logger.error("ProfileScreen Error: profile_controller not found in app.")
        return super().on_pre_enter(*args)

    def display_profile_data(self, user_info, stats):
        """Updates widgets on the screen with user data and statistics."""
        logger.debug(f"Displaying profile data: User={user_info}, Stats={stats}")

        if hasattr(self.ids, 'username_label'):
            self.ids.username_label.text = user_info.get('username', 'N/A')
        if hasattr(self.ids, 'email_label'):
            self.ids.email_label.text = user_info.get('email', 'N/A')
        if hasattr(self.ids, 'joined_label'):
            self.ids.joined_label.text = f"Joined: {user_info.get('created_at', 'N/A')}"

        if hasattr(self.ids, 'total_items_label'):
            self.ids.total_items_label.text = str(stats.get('total_items', 0))
        if hasattr(self.ids, 'avg_rating_label'):
            avg_rating = stats.get('average_rating')
            self.ids.avg_rating_label.text = f"{avg_rating:.1f}/10" if avg_rating is not None else "N/A"

        if hasattr(self.ids, 'type_stats_list'):
            type_list_widget = self.ids.type_stats_list
            type_list_widget.clear_widgets()
            count_by_type = stats.get('count_by_type', {})
            if count_by_type:
                sorted_types = sorted(count_by_type.items(), key=lambda item: item[1], reverse=True)
                for item_type, count in sorted_types:
                     list_item = MDListItem(
                         MDListItemHeadlineText(text=str(item_type)),
                         MDListItemTertiaryText(text=str(count)),
                     )
                     type_list_widget.add_widget(list_item)
            else:
                 type_list_widget.add_widget(
                     MDListItem(MDListItemHeadlineText(text="No items rated yet.", italic=True))
                 )

        if hasattr(self.ids, 'status_stats_list'):
            status_list_widget = self.ids.status_stats_list
            status_list_widget.clear_widgets()
            count_by_status = stats.get('count_by_status', {})
            if count_by_status:
                sorted_statuses = sorted(count_by_status.items(), key=lambda item: item[1], reverse=True)
                for status, count in sorted_statuses:
                     list_item = MDListItem(
                         MDListItemHeadlineText(text=str(status)),
                         MDListItemTertiaryText(text=str(count)),
                     )
                     status_list_widget.add_widget(list_item)
            else:
                 status_list_widget.add_widget(
                     MDListItem(MDListItemHeadlineText(text="No items rated yet.", italic=True))
                 )

        if hasattr(self.ids, 'type_avg_rating_list'):
            avg_list_widget = self.ids.type_avg_rating_list
            avg_list_widget.clear_widgets()
            avg_rating_by_type = stats.get('avg_rating_by_type', {})
            if avg_rating_by_type:
                sorted_avg_types = sorted(avg_rating_by_type.items(), key=lambda item: item[0])
                for item_type, avg_rating in sorted_avg_types:
                    rating_text = f"{avg_rating:.1f}/10"
                    list_item = MDListItem(
                        MDListItemHeadlineText(text=str(item_type)),
                        MDListItemTertiaryText(text=rating_text)
                    )
                    avg_list_widget.add_widget(list_item)
            else:
                avg_list_widget.add_widget(
                    MDListItem(
                        MDListItemHeadlineText(text="No ratings available for average calculation.", italic=True))
                )

        if hasattr(self.ids, 'rating_dist_list'):
            dist_list_widget = self.ids.rating_dist_list
            dist_list_widget.clear_widgets()
            rating_distribution = stats.get('rating_distribution', {})

            if rating_distribution:
                sorted_ratings = sorted(rating_distribution.keys(), reverse=True)

                for rating_group in sorted_ratings:
                    count = rating_distribution[rating_group]
                    text_headline = f"Rating {rating_group}:"
                    text_tertiary = f"{count} item{'s' if count != 1 else ''}"

                    list_item = MDListItem(
                        MDListItemHeadlineText(text=text_headline),
                        MDListItemTertiaryText(text=text_tertiary)
                    )
                    dist_list_widget.add_widget(list_item)
            else:
                dist_list_widget.add_widget(
                    MDListItem(MDListItemHeadlineText(text="No ratings available.", italic=True))
                )

    def show_password_feedback(self, message, is_error=False):
        """Displays a feedback message below the password fields."""
        if hasattr(self.ids, 'password_feedback_label'):
            feedback_label = self.ids.password_feedback_label
            feedback_label.text = message
            if is_error:
                feedback_label.text_color = MDApp.get_running_app().theme_cls.errorColor
            else:
                feedback_label.text_color = MDApp.get_running_app().theme_cls.primaryColor
            feedback_label.height = feedback_label.texture_size[1] if message else 0
        else:
            logger.warning("password_feedback_label ID not found in ProfileScreen.")

    def show_settings_feedback(self, message, is_error=False):
        """Displays a feedback message for settings actions."""
        if hasattr(self.ids, 'settings_feedback_label'):
            feedback_label = self.ids.settings_feedback_label
            feedback_label.text = message
            if is_error:
                feedback_label.text_color = MDApp.get_running_app().theme_cls.errorColor
            else:
                feedback_label.text_color = MDApp.get_running_app().theme_cls.primaryColor
            feedback_label.height = feedback_label.texture_size[1] if message else 0
        else:
            logger.warning("settings_feedback_label ID not found in ProfileScreen.")

    def clear_password_fields(self):
        """Clears the password input fields."""
        if hasattr(self.ids, 'current_password'):
            self.ids.current_password.text = ""
        if hasattr(self.ids, 'new_password'):
            self.ids.new_password.text = ""
        if hasattr(self.ids, 'confirm_password'):
            self.ids.confirm_password.text = ""
        logger.debug("Password fields cleared.")

    def _load_and_display_current_sort_settings(self):
        """Loads from the controller and shows the current sort settings."""
        app = MDApp.get_running_app()
        if not hasattr(app, 'profile_controller'): return

        try:
            current_settings = app.profile_controller.get_current_default_sort()
            column_db_name = current_settings.get('column', 'created_at')
            order = current_settings.get('order', 'DESC')

            column_display_name = ALLOWED_SORT_COLUMNS.get(column_db_name, column_db_name)

            if hasattr(self.ids, 'sort_column_button_text'):
                self.ids.sort_column_button_text.text = column_display_name
            if hasattr(self.ids, 'sort_order_button_text'):
                self.ids.sort_order_button_text.text = order
            logger.debug(f"Displayed current sort settings: {column_display_name} ({column_db_name}), {order}")
        except Exception as e:
            logger.exception("Error loading/displaying sort settings.")
            self.show_settings_feedback("Error loading settings.", is_error=True)

    def open_sort_column_menu(self, caller_widget):
        """Opens the sorting column selection menu."""
        if not self.sort_column_menu:
            menu_items = [
                {
                    "text": display_name,
                    "on_release": lambda x=db_name: self._set_default_sort_column(x),
                } for db_name, display_name in ALLOWED_SORT_COLUMNS.items()
            ]
            self.sort_column_menu = MDDropdownMenu(
                caller=caller_widget, items=menu_items, max_height=dp(200)
            )
        self.sort_column_menu.caller = caller_widget
        self.sort_column_menu.open()

    def open_sort_order_menu(self, caller_widget):
        """Opens the sort order selection menu."""
        if not self.sort_order_menu:
            menu_items = [
                {
                    "text": order,
                    "on_release": lambda x=order: self._set_default_sort_order(x),
                } for order in ALLOWED_SORT_ORDERS
            ]
            self.sort_order_menu = MDDropdownMenu(
                caller=caller_widget, items=menu_items
            )
        self.sort_order_menu.caller = caller_widget
        self.sort_order_menu.open()

    def _set_default_sort_column(self, selected_column_db_name):
        """Called when a column is selected. Updates the button and saves it."""
        display_name = ALLOWED_SORT_COLUMNS.get(selected_column_db_name, selected_column_db_name)
        if hasattr(self.ids, 'sort_column_button_text'):
            self.ids.sort_column_button_text.text = display_name

        current_order = "DESC"
        if hasattr(self.ids, 'sort_order_button_text'):
            current_order = self.ids.sort_order_button_text.text

        app = MDApp.get_running_app()
        if hasattr(app, 'profile_controller'):
            app.profile_controller.save_default_sort(selected_column_db_name, current_order)
        self.sort_column_menu.dismiss()

    def _set_default_sort_order(self, selected_order):
        """Called when an order is selected. Updates the button and saves it."""
        if hasattr(self.ids, 'sort_order_button_text'):
            self.ids.sort_order_button_text.text = selected_order
        current_column_display_name = "Date Added"

        if hasattr(self.ids, 'sort_column_button_text'):
            current_column_display_name = self.ids.sort_column_button_text.text
        current_column_db_name = 'created_at'

        for db_name, display_name in ALLOWED_SORT_COLUMNS.items():
            if display_name == current_column_display_name:
                current_column_db_name = db_name
                break

        app = MDApp.get_running_app()
        if hasattr(app, 'profile_controller'):
            app.profile_controller.save_default_sort(current_column_db_name, selected_order)
        self.sort_order_menu.dismiss()