import logging

from model.database_model import DatabaseError

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogHeadlineText,
    MDDialogContentContainer,
    MDDialogButtonContainer,
)
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.divider import MDDivider

from kivymd.app import MDApp

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
                review_display = "..." if item_dict.get('review') else "" # Show ... if there is a review
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
        if not item_data:
            logger.warning("Tried to show details for empty item_data.")
            return

        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None

        app = MDApp.get_running_app()
        db_model = app.models.get('database')
        if not db_model:
            logger.error("Database model not found!")
            return

        item_id = item_data.get('item_id')
        if not item_id:
            logger.error("Item data is missing item_id.")
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

        self.dialog = MDDialog(
            MDDialogHeadlineText(text="Item Details"),
            MDDialogContentContainer(dialog_content),
            MDDialogButtonContainer(
                MDButton(MDButtonText(text="Close"), style="text", on_release=lambda *args: self.dialog.dismiss()),
                spacing="8dp",
            ),
            size_hint=(0.8, None)
        )

        logger.debug(f"Showing details for item: {item_data.get('name')}")
        self.dialog.open()

    def show_error(self, message):
        """Displays an error message."""
        logger.error(f"RatingsScreen Error: {message}")