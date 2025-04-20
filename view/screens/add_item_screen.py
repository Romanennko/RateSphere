import logging

from kivymd.uix.screen import MDScreen
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.dialog import MDDialog, MDDialogButtonContainer, MDDialogContentContainer, MDDialogHeadlineText
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.slider import MDSlider
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import MDList, MDListItem, MDListItemTrailingCheckbox, MDListItemHeadlineText, MDListItemSupportingText
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.divider import MDDivider

from kivy.clock import Clock
from kivy.properties import DictProperty
from kivymd.app import MDApp

from model.database_model import DatabaseError

logger = logging.getLogger(__name__)

OVERALL_CRITERION_NAME = "Total score"

ITEM_STATUSES = ['Completed', 'In Progress', 'Planned', 'Dropped', 'Ongoing']
ITEM_TYPES = ['Movie', 'Manga', 'Manhwa', 'Manhua', 'Game', 'Anime', 'Cartoon', 'Series', 'Book', 'Board game']

class AddItemScreen(MDScreen):
    rating_data = DictProperty({})

    rating_choice_dialog = None
    total_score_dialog = None
    criteria_rating_dialog = None
    add_criteria_dialog = None

    criteria_rows = DictProperty({})
    displayed_criterion_ids = set()
    criteria_content_box = None

    edit_mode = False
    item_to_edit_id = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.status_menu = None
        self.status_menu_items = self._create_menu_items(ITEM_STATUSES, self._set_status)
        self.type_menu = None
        self.type_menu_items = self._create_menu_items(ITEM_TYPES, self._set_type)

    def on_pre_enter(self, *args):
        """Called before the screen becomes active."""
        if not self.edit_mode:
            self.clear_fields()

    def on_leave(self, *args):
        """Called when you leave the screen."""
        self._dismiss_all_dialogs()
        self.edit_mode = False
        self.item_to_edit_id = None
        logger.debug("Leaving AddItemScreen, edit mode reset.")
        return super().on_leave(*args)

    def _dismiss_all_dialogs(self):
        """Closes all active dialogs on this screen."""
        for dialog_attr in ['rating_choice_dialog', 'total_score_dialog', 'criteria_rating_dialog',
                            'add_criteria_dialog']:
            dialog = getattr(self, dialog_attr, None)
            if dialog:
                dialog.dismiss()
                setattr(self, dialog_attr, None)

    def clear_fields(self):
        """Clears all fields and resets the state (including edit mode)."""
        self.ids.item_name.text = ''
        self.ids.item_alt_name.text = ''
        self.ids.item_review.text = ''

        if hasattr(self.ids, 'type_button_text'):
            self.ids.type_button_text.text = "Select type"
        if hasattr(self.ids, 'status_button_text'):
            self.ids.status_button_text.text = "Select status"

        self.rating_data = {}
        if hasattr(self.ids, 'rating_button_text'):
            self.ids.rating_button_text.text = "Set Rating"

        self.criteria_rows = {}
        self.displayed_criterion_ids = set()
        self.criteria_content_box = None

        self.edit_mode = False
        self.item_to_edit_id = None

        self.ids.top_app_bar_title.text = "Add Item"
        if hasattr(self.ids, 'save_button_text'):
            self.ids.save_button_text.text = "Save"

        if hasattr(self.ids, 'error_label'):
            self.ids.error_label.text = ''
        logger.debug("AddItemScreen fields cleared and edit mode reset.")

    def _create_criterion_row_widget(self, criterion_data, current_rating):
        """Creates a row widget (BoxLayout) for a single criteria with a slider."""
        criterion_id = criterion_data['criterion_id']
        criterion_name = criterion_data['name']

        row = MDBoxLayout(adaptive_height=True, spacing="10dp", padding="5dp")
        row.criterion_id = criterion_id
        row.criterion_name = criterion_name

        label_name = MDLabel(text=criterion_name, size_hint_x=0.4, adaptive_height=True, pos_hint={"center_y": 0.5})

        internal_min = 2
        internal_max = 20
        internal_step = 1
        initial_slider_value = int(current_rating * 2) if current_rating >= 1 else 0

        slider = MDSlider(
            min=internal_min, max=internal_max, step=internal_step,
            value=initial_slider_value, size_hint_x=0.5, value_track=True
        )

        initial_label_text = f"{(slider.value / 2.0):.1f}" if slider.value >= internal_min else "N/A"
        label_value = MDLabel(
            text=initial_label_text, size_hint_x=0.1, halign="right",
            adaptive_height=True, pos_hint={"center_y": 0.5}
        )

        def _update_row_rating(slider_instance, value, lbl=label_value, min_val=internal_min):
            actual_value = value / 2.0
            lbl.text = f"{actual_value:.1f}" if actual_value >= 1.0 else "N/A"

        slider.bind(value=_update_row_rating)

        row.add_widget(label_name)
        row.add_widget(slider)
        row.add_widget(label_value)
        row.slider_widget = slider

        return row

    def load_item_for_edit(self, item_data):
        """Prepares the screen for editing an existing item."""
        logger.info(f"Loading item data for editing: ID {item_data.get('item_id')}")
        self.clear_fields()
        self._dismiss_all_dialogs()

        self.edit_mode = True
        self.item_to_edit_id = item_data.get('item_id')

        if not self.item_to_edit_id:
            logger.error("Cannot load item for edit: item_id is missing.")
            self.show_error("Error: Invalid item data for editing.")
            self.edit_mode = False
            return

        self.ids.item_name.text = item_data.get('name', '') or ''
        self.ids.item_alt_name.text = item_data.get('alt_name') or ''
        self.ids.item_review.text = item_data.get('review') or ''
        item_type = item_data.get('item_type')
        if item_type and hasattr(self.ids, 'type_button_text'):
            self.ids.type_button_text.text = item_type
        item_status = item_data.get('status')
        if item_status and hasattr(self.ids, 'status_button_text'):
            self.ids.status_button_text.text = item_status

        app = MDApp.get_running_app()
        db_model = app.models.get('database')
        if not db_model:
            logger.error("Cannot load criteria ratings: DB model not found.")
            self.show_error("Error loading rating details.")
            return

        try:
            criteria_ratings_list = db_model.get_criterion_ratings_for_item(self.item_to_edit_id)
            loaded_rating_data = {}
            calculated_average = 0
            rated_count = 0
            has_only_total = False

            if criteria_ratings_list:
                if len(criteria_ratings_list) == 1 and criteria_ratings_list[0].get('is_overall'):
                    total_score_rating = criteria_ratings_list[0].get('rating')
                    loaded_rating_data[OVERALL_CRITERION_NAME] = float(total_score_rating)
                    has_only_total = True
                else:
                    sum_ratings = 0
                    for rating_info in criteria_ratings_list:
                        name = rating_info.get('criterion_name')
                        rating_val = rating_info.get('rating')
                        if name and rating_val is not None:
                            loaded_rating_data[name] = float(rating_val)
                            if not rating_info.get('is_overall'):
                                sum_ratings += float(rating_val)
                                rated_count += 1
                    if rated_count > 0:
                        calculated_average = round(sum_ratings / rated_count, 1)

            self.rating_data = loaded_rating_data
            logger.debug(f"Loaded rating data for edit: {self.rating_data}")

            if hasattr(self.ids, 'rating_button_text'):
                if has_only_total:
                    self.ids.rating_button_text.text = f"Rating: {loaded_rating_data[OVERALL_CRITERION_NAME]:.1f}/10"
                elif rated_count > 0:
                    self.ids.rating_button_text.text = f"Rating: {calculated_average:.1f}/10 ({rated_count} criteria)"
                else:
                    self.ids.rating_button_text.text = "Set Rating"

        except DatabaseError as e:
            logger.exception(f"Failed to load criteria ratings for item {self.item_to_edit_id} during edit load.")
            self.show_error("Error loading rating details.")
            self.rating_data = {}
            if hasattr(self.ids, 'rating_button_text'):
                self.ids.rating_button_text.text = "Set Rating (Error)"

        if hasattr(self.ids, 'top_app_bar_title'):
            self.ids.top_app_bar_title.text = f"Edit: {item_data.get('name', '')}"
        if hasattr(self.ids, 'save_button_text'):
            self.ids.save_button_text.text = "Update"

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

    def open_rating_dialog(self):
        """Displays the dialog box for selecting the evaluation type."""
        self._dismiss_all_dialogs()

        self.rating_choice_dialog = MDDialog(
            MDDialogHeadlineText(text="Rating Method"),
            MDDialogContentContainer(
                MDBoxLayout(
                    MDButton(
                        MDButtonText(text="Rate 'Total Score'"),
                        on_release=lambda *args: self.open_total_score_dialog(),
                        style="filled",
                    ),
                    MDButton(
                        MDButtonText(text="Rate by Criteria"),
                        on_release=lambda *args: self.open_criteria_rating_dialog(),
                        style="filled",
                    ),
                    orientation="vertical",
                    spacing="10dp",
                    padding="10dp",
                    adaptive_height=True,
                )
            ),
            MDDialogButtonContainer(
                MDButton(
                    MDButtonText(text="Cancel"),
                    style="text",
                    on_release=lambda *args: self.rating_choice_dialog.dismiss(),
                ),
                spacing="8dp",
            )
        )
        self.rating_choice_dialog.open()

    def open_total_score_dialog(self):
        """Displays a dialog for entering a single total score."""
        self._dismiss_all_dialogs()

        current_score_1_to_10 = self.rating_data.get(OVERALL_CRITERION_NAME, 5.0)

        content_cls = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing="10dp")

        internal_min = 2
        internal_max = 20
        internal_step = 1
        initial_slider_value = int(current_score_1_to_10 * 2)
        initial_slider_value = max(internal_min, min(internal_max, initial_slider_value))

        slider = MDSlider(
            min=internal_min,
            max=internal_max,
            step=internal_step,
            value=initial_slider_value,
            value_track=True
        )

        value_label = MDLabel(text=f"{(slider.value / 2.0):.1f}", halign="center")

        def update_label(instance, value):
            value_label.text = f"{(value / 2.0):.1f}"

        slider.bind(value=update_label)

        content_cls.add_widget(slider)
        content_cls.add_widget(value_label)

        self.total_score_dialog = MDDialog(
            MDDialogHeadlineText(text="Set Total Score (1-10)"),
            MDDialogContentContainer(content_cls),
            MDDialogButtonContainer(
                MDButton(
                    MDButtonText(text="Cancel"),
                    style="text",
                    on_release=lambda *args: self.total_score_dialog.dismiss(),
                ),
                MDButton(
                    MDButtonText(text="Save Score"),
                    style="filled",
                    on_release=lambda *args: self._save_total_score(slider.value / 2.0),
                ),
                spacing="8dp",
            ),
        )
        self.total_score_dialog.open()

    def _save_total_score(self, value):
        """Saves the total score and updates the button."""
        self.rating_data = {OVERALL_CRITERION_NAME: round(value, 2)}
        logger.debug(f"Total score set: {self.rating_data}")

        if hasattr(self.ids, 'rating_button_text'):
            self.ids.rating_button_text.text = f"Rating: {value:.1f}/10"
        self.total_score_dialog.dismiss()

    def open_criteria_rating_dialog(self):
        """Displays a dialog for evaluation. First, only the recommended criteria."""
        self._dismiss_all_dialogs()

        app = MDApp.get_running_app()
        db_model = app.models.get('database')
        if not db_model:
            logger.error("Database model not found!")
            self.show_error("Error: Cannot access database.")
            return

        selected_type = self.ids.type_button_text.text
        if selected_type == "Select type":
            self.show_error("Please select item type first to see suggested criteria.")
            return

        try:
            suggested_criteria = db_model.get_suggested_criteria(selected_type)
            self.all_criteria_list = db_model.get_all_criteria()

            if not self.all_criteria_list:
                logger.warning("No criteria found in the database.")
                self.show_error("No criteria defined yet.")
                return

            dialog_main_content = MDBoxLayout(orientation='vertical', adaptive_height=True, spacing='10dp')

            self.criteria_content_box = MDBoxLayout(orientation='vertical', adaptive_height=True, spacing='5dp')
            self.criteria_rows = {}
            self.displayed_criterion_ids = set()

            if suggested_criteria:
                dialog_main_content.add_widget(
                    MDLabel(text="Suggested Criteria:", adaptive_height=True, font_style="Title"))
                for criterion in suggested_criteria:
                    criterion_id = criterion['criterion_id']
                    if criterion.get('is_overall'): continue

                    current_rating = self.rating_data.get(criterion['name'], 0.0)
                    row_widget = self._create_criterion_row_widget(criterion, current_rating)
                    self.criteria_content_box.add_widget(row_widget)
                    self.criteria_rows[criterion_id] = row_widget
                    self.displayed_criterion_ids.add(criterion_id)
            else:
                dialog_main_content.add_widget(
                    MDLabel(text="No specific criteria suggested for this type.", adaptive_height=True, italic=True))

            scroll_view = MDScrollView(size_hint_y=None, height="300dp")
            scroll_view.add_widget(self.criteria_content_box)
            dialog_main_content.add_widget(scroll_view)

            dialog_main_content.add_widget(MDDivider())
            add_more_button = MDButton(
                MDButtonText(text="Add/View Other Criteria"),
                style="text",
                on_release=lambda *args: self.open_add_more_criteria_dialog()
            )
            dialog_main_content.add_widget(add_more_button)

            self.criteria_rating_dialog = MDDialog(
                MDDialogHeadlineText(text="Rate by Criteria (1-10)"),
                MDDialogContentContainer(dialog_main_content),
                MDDialogButtonContainer(
                    MDButton(MDButtonText(text="Cancel"), style="text",
                             on_release=lambda *args: self._dismiss_all_dialogs()),
                    MDButton(MDButtonText(text="Save Criteria"), style="filled",
                             on_release=lambda *args: self._save_criteria_ratings()),
                    spacing="8dp",
                ),
                size_hint=(0.9, 0.8),
            )
            self.criteria_rating_dialog.open()

        except DatabaseError as e:
            logger.exception("Database error loading criteria.")
            self.show_error("Error loading criteria from database.")
        except Exception as e:
            logger.exception("Unexpected error opening criteria dialog.")
            self.show_error("An unexpected error occurred.")

    def _save_criteria_ratings(self):
        """Collects ratings from sliders and stores them in self.rating_data."""
        new_rating_data = {}
        total_rating_sum = 0
        rated_criteria_count = 0

        for criterion_id, row_widget in self.criteria_rows.items():
            slider_internal_value = row_widget.slider_widget.value
            actual_rating = slider_internal_value / 2.0

            if 1.0 <= actual_rating <= 10.0:
                criterion_name = row_widget.criterion_name
                rating_to_save = round(actual_rating, 2)
                new_rating_data[criterion_name] = rating_to_save
                total_rating_sum += rating_to_save
                rated_criteria_count += 1

        if not new_rating_data:
            self.rating_data = {}
            button_text = "Set Rating"
            logger.debug("No criteria were rated.")
        else:
            self.rating_data = new_rating_data
            average = round(total_rating_sum / rated_criteria_count, 1) if rated_criteria_count > 0 else 0
            button_text = f"Rating: {average:.1f}/10 ({rated_criteria_count} criteria)"
            logger.debug(f"Criteria ratings saved: {self.rating_data}")

        if hasattr(self.ids, 'rating_button_text'):
            self.ids.rating_button_text.text = button_text

        self.criteria_rating_dialog.dismiss()
        self.criteria_rows = {}

    def open_add_more_criteria_dialog(self):
        """Displays a dialog with a list of the remaining criteria to add."""
        logger.debug("--> Entering open_add_more_criteria_dialog")
        logger.debug(f"    Value of self.add_criteria_dialog BEFORE check: {self.add_criteria_dialog}")

        if self.add_criteria_dialog:
            logger.debug("    Dialog reference exists, returning early.")
            return

        other_criteria = [
            c for c in self.all_criteria_list
            if not c.get('is_overall') and c['criterion_id'] not in self.displayed_criterion_ids
        ]

        logger.debug(f"Opening 'Add More Criteria' dialog. Found {len(other_criteria)} other criteria to display.")
        if other_criteria:
            logger.debug(f"First few other criteria: {[c['name'] for c in other_criteria[:3]]}")

        if not other_criteria:
            self.show_error("No more criteria to add.")
            return

        list_content = MDList(spacing="8dp", size_hint_y=None)

        list_content.bind(minimum_height=list_content.setter('height'))

        self.add_criteria_checkboxes = {}

        for criterion in other_criteria:
            criterion_id = criterion['criterion_id']
            item = MDListItem(
                MDListItemHeadlineText(text=criterion['name']),
                MDListItemSupportingText(text=criterion.get('description', '')[:75] + "..."),
            )
            checkbox = MDListItemTrailingCheckbox()
            checkbox.criterion_id = criterion_id
            item.add_widget(checkbox)
            list_content.add_widget(item)
            self.add_criteria_checkboxes[criterion_id] = checkbox

        scroll = MDScrollView(height="350dp", size_hint_y=None)
        scroll.add_widget(list_content)

        self.add_criteria_dialog = MDDialog(
            MDDialogHeadlineText(text="Select Criteria to Add"),
            MDDialogContentContainer(scroll),
            MDDialogButtonContainer(
                MDButton(MDButtonText(text="Cancel"), style="text",
                         on_release=lambda *args: (self.add_criteria_dialog.dismiss(), setattr(self, 'add_criteria_dialog', None))),
                MDButton(MDButtonText(text="Add Selected"), style="filled", on_release=lambda *args: self._add_selected_criteria()),
                spacing="8dp",
            ),
            size_hint=(0.8, 0.7),
        )
        logger.debug(f"    Value of self.add_criteria_dialog AFTER creation: {self.add_criteria_dialog}")
        self.add_criteria_dialog.open()
        logger.debug("<-- Exiting open_add_more_criteria_dialog (after open)")

    def _add_selected_criteria(self):
        """Adds the selected criteria to the main dialog."""
        if not self.criteria_content_box:
            self.add_criteria_dialog.dismiss()
            return

        added_count = 0
        ids_to_add = []
        for criterion_id, checkbox in self.add_criteria_checkboxes.items():
            if checkbox.active:
                ids_to_add.append(criterion_id)

        if not ids_to_add:
            self.add_criteria_dialog.dismiss()
            return

        criteria_to_add_data = [c for c in self.all_criteria_list if c['criterion_id'] in ids_to_add]

        def do_add(*args):
            nonlocal added_count
            for criterion in criteria_to_add_data:
                criterion_id = criterion['criterion_id']
                if criterion_id not in self.displayed_criterion_ids:
                    current_rating = self.rating_data.get(criterion['name'], 0.0)
                    row_widget = self._create_criterion_row_widget(criterion, current_rating)
                    self.criteria_content_box.add_widget(row_widget)
                    self.criteria_rows[criterion_id] = row_widget
                    self.displayed_criterion_ids.add(criterion_id)
                    added_count += 1
            if added_count > 0:
                logger.debug(f"Added {added_count} criteria to the rating dialog.")
            else:
                logger.debug("Selected criteria were already displayed.")

        Clock.schedule_once(do_add)

        self.add_criteria_dialog.dismiss()
        self.add_criteria_dialog = None

    def show_error(self, message):
        """Displays an error message."""
        self.ids.error_label.text = message