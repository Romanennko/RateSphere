import logging

from model.database_model import DatabaseError

from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogHeadlineText,
    MDDialogContentContainer,
    MDDialogButtonContainer,
    MDDialogSupportingText,
)
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.divider import MDDivider

from kivymd.app import MDApp

from kivy.metrics import dp
from kivy.core.window import Window
from kivy.properties import StringProperty, DictProperty

OVERALL_CRITERION_NAME = "Total score"

logger = logging.getLogger(__name__)

class RatingRowWidget(MDBoxLayout):
    name_text = StringProperty("")
    type_text = StringProperty("")
    status_text = StringProperty("")
    rating_text = StringProperty("")

    item_data = DictProperty({})

class RatingsScreen(MDScreen):
    dialog = None
    confirm_dialog = None

    def on_enter(self, *args):
        logger.debug(f"=====>> ENTERING screen: {self.name}")
        app = MDApp.get_running_app()
        if hasattr(app, 'ratings_controller'):
            app.ratings_controller.load_items()
        else:
             logger.debug("RatingsScreen Error: ratings_controller not found in app.")
        return super().on_enter(*args)

    def on_leave(self, *args):
        if self.dialog:
            self.dialog.dismiss()
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
                formatted_data.append({
                    "name_text": str(item_dict.get('name', '')),
                    "type_text": str(item_dict.get('item_type', '')),
                    "status_text": str(item_dict.get('status', '')),
                    "rating_text": str(item_dict.get('rating', '')),
                    "item_data": item_dict,
                })

            logger.debug(f"RatingsScreen: Updating RecycleView data with {len(formatted_data)} items.")
            self.ids.ratings_rv.data = formatted_data
            self.ids.ratings_rv.refresh_from_data()
        else:
             logger.error("RatingsScreen Error: ratings_rv ID not found.")

    def show_item_details_dialog(self, item_data):
        """
        Creates and displays a dialog with complete information about the item,
        including criterion scores.
        """

        self._dismiss_all_dialogs()

        if not item_data:
            logger.warning("Tried to show details for empty item_data.")
            return

        app = MDApp.get_running_app()
        db_model = app.models.get('database')
        item_id = item_data.get('item_id')

        if not db_model or not item_id:
            logger.error(f"Cannot show details: missing model or item_id. Item data: {item_data}")
            return

        dialog_content = MDBoxLayout(
            orientation="vertical",
            padding="10dp",
            spacing="10dp",
            adaptive_height=True,
        )

        overall_rating_display = f"{item_data.get('rating'):.1f}/10" if item_data.get('rating') is not None else "N/A"
        details_text = f"""
            [b]Name:[/b] {item_data.get('name', 'N/A')}
            [b]Alternative Name:[/b] {item_data.get('alt_name', '-')}
            [b]Type:[/b] {item_data.get('item_type', 'N/A')}
            [b]Status:[/b] {item_data.get('status', 'N/A')}
            [b]Overall Rating:[/b] {overall_rating_display}
        """
        dialog_content.add_widget(
            MDLabel(
                text=details_text,
                markup=True,
                adaptive_height=True,
            )
        )

        try:
            criteria_ratings = db_model.get_criterion_ratings_for_item(item_id)

            if criteria_ratings:
                dialog_content.add_widget(MDDivider())
                dialog_content.add_widget(
                    MDLabel(
                        text="[b]Criteria Ratings:[/b]",
                        markup=True,
                        adaptive_height=True,
                    )
                )

                is_only_total_score = len(criteria_ratings) == 1 and criteria_ratings[0].get('is_overall')

                if is_only_total_score:
                    total_score_value = criteria_ratings[0].get('rating')
                    dialog_content.add_widget(
                        MDLabel(
                            text=f"- {OVERALL_CRITERION_NAME}: {total_score_value:.1f}/10",
                            adaptive_height=True,
                            italic=True
                        )
                    )
                else:
                    criteria_box = MDBoxLayout(orientation='vertical', adaptive_height=True, spacing='2dp',
                                               padding=['10dp', 0, 0, 0])
                    count = 0
                    for rating_info in criteria_ratings:
                        if rating_info.get('is_overall'):
                            continue
                        criterion_name = rating_info.get('criterion_name', 'Unknown')
                        criterion_score = rating_info.get('rating')
                        criteria_box.add_widget(
                            MDLabel(
                                text=f"- {criterion_name}: {criterion_score:.1f}/10",
                                adaptive_height=True
                            )
                        )
                        count += 1
                    if count > 0:
                        dialog_content.add_widget(criteria_box)
                    elif not criteria_ratings[0].get(
                            'is_overall'):
                        dialog_content.add_widget(
                            MDLabel(text="- No specific criteria rated.", adaptive_height=True, italic=True))

        except DatabaseError as e:
            logger.exception(f"Failed to load criteria ratings for item {item_id}")
            dialog_content.add_widget(MDDivider())
            dialog_content.add_widget(
                MDLabel(
                    text="[color=ff0000]Error loading criteria ratings.[/color]",
                    markup=True,
                    adaptive_height=True
                )
            )

        review = item_data.get('review')
        if review:
            dialog_content.add_widget(MDDivider())
            dialog_content.add_widget(
                MDLabel(
                    text="[b]Review:[/b]",
                    markup=True,
                    adaptive_height=True,
                )
            )
            dialog_content.add_widget(
                MDLabel(
                    text=review,
                    adaptive_height=True,
                )
            )

        content_scroll_view = MDScrollView(
            size_hint_y=None,
            height=Window.height * 0.6
        )
        content_scroll_view.add_widget(dialog_content)

        self.dialog = MDDialog(
            MDDialogHeadlineText(text="Item Details"),
            MDDialogContentContainer(content_scroll_view),
            MDDialogButtonContainer(
                MDButton(
                    MDButtonText(text="DELETE", theme_text_color="Error"),
                    style="text",
                    on_release=lambda *args: self.confirm_delete_item(item_data)
                ),
                MDButton(
                    MDButtonText(text="Close"),
                    style="text",
                    on_release=lambda *args: self.dialog.dismiss()
                ),
                spacing="8dp",
                pos_hint={'center_x': 0.9}
            ),
            size_hint=(0.8, None),
            on_dismiss=lambda *args: setattr(self, 'dialog', None)
        )

        logger.debug(f"Showing details for item: {item_data.get('name')}")
        self.dialog.open()

    def confirm_delete_item(self, item_data):
        """Shows a confirmation dialog before deleting an item."""

        if not item_data or not item_data.get('item_id'):
            logger.error("Cannot confirm deletion: Invalid item_data.")
            self.show_error("Cannot delete item: Invalid data.")
            return

        item_id = item_data['item_id']
        item_name = item_data.get('name', 'this item')

        app = MDApp.get_running_app()

        self.confirm_dialog = MDDialog(
            MDDialogHeadlineText(text="Confirm Deletion"),
            MDDialogSupportingText(
                f"Are you sure you want to permanently delete '{item_name}'? This action cannot be undone."),
            MDDialogButtonContainer(
                MDButton(
                    MDButtonText(text="Cancel"),
                    style="text",
                    on_release=lambda *args: self.confirm_dialog.dismiss()
                ),
                MDButton(
                    MDButtonText(text="DELETE", theme_text_color="Error"),
                    style="filled",
                    theme_bg_color = "Custom",
                    md_bg_color=app.theme_cls.errorColor,
                    on_release=lambda *args: self._execute_delete(item_id)
                ),
                spacing="8dp",
            ),
            on_dismiss=lambda *args: setattr(self, 'confirm_dialog', None)
        )
        logger.debug(f"Showing delete confirmation for item: {item_name} (ID: {item_id})")
        self.confirm_dialog.open()

    def _execute_delete(self, item_id):
        """Calls the controller to delete the item after confirmation."""
        if self.confirm_dialog:
            self.confirm_dialog.dismiss()

        logger.info(f"Delete confirmed for item {item_id}. Calling controller...")
        app = MDApp.get_running_app()
        if hasattr(app, 'ratings_controller'):
            app.ratings_controller.delete_item(item_id)
        else:
            logger.error("Cannot execute delete: ratings_controller not found in app.")
            self.show_error("Error: Could not perform deletion.")

        self._dismiss_all_dialogs()

    def _dismiss_all_dialogs(self):
        """Closes all active dialogs on this screen."""
        for dialog_attr in ['dialog', 'confirm_dialog']:
            dialog = getattr(self, dialog_attr, None)
            if dialog:
                try:
                    dialog.dismiss()
                except Exception as e:
                    logger.warning(f"Error dismissing dialog '{dialog_attr}': {e}")
                finally:
                    setattr(self, dialog_attr, None)

    def show_error(self, message):
        """Displays an error message."""
        logger.error(f"RatingsScreen Error: {message}")