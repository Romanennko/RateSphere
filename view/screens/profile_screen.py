import logging

from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemTertiaryText
from kivymd.uix.screen import MDScreen

from kivymd.app import MDApp
from kivy.properties import ColorProperty

logger = logging.getLogger(__name__)

class ProfileScreen(MDScreen):
    feedback_color = ColorProperty(None)

    def on_pre_enter(self, *args):
        """Called before the screen becomes active. Load data and clear the password fields."""
        logger.debug(f"=====>> ENTERING screen: {self.name}")
        app = MDApp.get_running_app()

        self.clear_password_fields()
        self.show_password_feedback("")

        if hasattr(app, 'profile_controller'):
            app.profile_controller.load_profile_data()
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

    def clear_password_fields(self):
        """Clears the password input fields."""
        if hasattr(self.ids, 'current_password'):
            self.ids.current_password.text = ""
        if hasattr(self.ids, 'new_password'):
            self.ids.new_password.text = ""
        if hasattr(self.ids, 'confirm_password'):
            self.ids.confirm_password.text = ""
        logger.debug("Password fields cleared.")