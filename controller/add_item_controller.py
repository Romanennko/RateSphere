from view.screens.add_item_screen import AddItemScreen

class AddItemController:
    def __init__(self, models, view, app):
        self.data_model = models['database']    # Link to DatabaseModel
        self.session_model = models['session']  # Link to SessionModel
        self.view = view                        # Link to AddItemScreen
        self.app = app                          # Link to the main application class (for navigation)

    def save_new_item(self, name, alt_name, item_type, status, rating, review):
        """Saves a new element entered by the user."""
        current_user_id = self.session_model.get_current_user_id()
        status_fields = False
        if not current_user_id:
            self.view.show_error("Error: User is not authorized.")
            return

        if not name or not name.strip():
            self.view.show_error("Error: Element name is required.")
            return

        if not item_type:
            self.view.show_error("Error: Element type must be selected.")
            return

        if not status:
            self.view.show_error("Error: Status must be selected.")
            return

        if not rating:
            self.view.show_error("Error: Rating must be selected.")
            return

        new_item_id = self.data_model.add_rated_item(
            user_id=current_user_id,
            name=name.strip(),
            alt_name=alt_name.strip() if alt_name else None,
            item_type=item_type,
            status=status,
            rating=rating,
            review=review.strip() if review else None
        )

        if new_item_id:
            print(f"New element added successfully with ID: {new_item_id}")
            self.app.screen_manager.current = "ratings"
            # TODO add update list
            # if hasattr(self.app, 'ratings_controller'):
            #    self.app.ratings_controller.load_items()
            status_fields = True
        else:
            self.view.show_error("Failed to add element. Please try again later.")

        if status_fields:
            AddItemScreen.clear_fields(self.view)