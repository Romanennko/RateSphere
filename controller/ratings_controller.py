class RatingsController:
    def __init__(self, models, view, app):
        self.data_model = models['database']    # Link to DatabaseModel
        self.session_model = models['session']  # Link to SessionModel
        self.view = view                        # Link to RatingsScreen
        self.app = app                          # Link to the main application class (for navigation)

        self.current_sort_column = 'created_at'
        self.current_sort_order = 'DESC'

    def load_items(self):
        """Loads the rated user items and updates the View."""
        user_id = self.session_model.get_current_user_id()
        if not user_id:
            print("RatingsController Error: Cannot load items, user not logged in.")
            self.view.update_data([])
            return

        try:
            items_raw = self.data_model.get_user_items(
                user_id=user_id,
                # TODO sort_by=self.current_sort_column, # We'll pass it on later
                # TODO sort_order=self.current_sort_order # We'll pass it on later
            )
            # The order of columns in get_user_items: item_id, name, alt_name, item_type, status, rating, review, created_at, updated_at
            rv_data = []
            if items_raw:
                for row in items_raw:
                    rv_data.append({
                        'item_id': row[0], # ID may be required for actions with the line
                        'name': row[1],
                        'alt_name': row[2],
                        'item_type': row[3],
                        'status': row[4],
                        'rating': row[5],
                        'review': row[6],
                        # 'created_at': row[7], # Can be added if you need to display
                        # 'updated_at': row[8], # Can be added if you need to display
                        'viewclass': 'RatingRowWidget'
                    })

            self.view.update_data(rv_data)

        except Exception as e:
            print(f"RatingsController Error loading items: {e}")
            self.view.update_data([])