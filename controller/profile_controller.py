import logging
import bcrypt

from model.database_model import DatabaseModel, DatabaseError
from model.session_model import SessionModel

logger = logging.getLogger(__name__)

class ProfileController:
    data_model: DatabaseModel
    session_model: SessionModel
    view: object
    app: object

    def __init__(self, models, view, app):
        self.data_model = models['database']    # Link to DatabaseModel
        self.session_model = models['session']  # Link to SessionModel
        self.view = view                        # Link to ProfileScreen
        self.app = app                          # Link to the main application class (for navigation)

        logger.debug('ProfileController initialized.')

    def load_profile_data(self):
        """Loads user details and statistics and tells the view to display them."""
        logger.info("Loading profile data...")

        if not self.session_model.is_logged_in():
            logger.warning("Cannot load profile data: No user logged in.")
            if hasattr(self.view, 'show_error'):
                self.view.show_error("Please log in to view profile.")
            return

        user_id = self.session_model.get_current_user_id()
        username = self.session_model.get_current_username()

        user_info = {'username': username, 'email': 'N/A', 'created_at': 'N/A'}
        stats = {
            'total_items': 0,
            'count_by_type': {},
            'count_by_status': {},
            'average_rating': None
        }

        try:
            details = self.data_model.get_user_details(user_id)
            if details:
                user_info['email'] = self._mask_email(details.get('email', ''))
                user_info['created_at'] = self._format_datetime(details.get('created_at'))
            else:
                logger.warning(f"Could not fetch user details for user_id {user_id}.")

            stats = self.data_model.get_user_statistics(user_id)
            logger.debug(f"Loaded user stats: {stats}")

        except DatabaseError as e:
            logger.exception(f"Database error loading profile data for user_id {user_id}: {e}")
            if hasattr(self.view, 'show_error'):
                self.view.show_error("Error loading profile data.")
        except Exception as e:
            logger.exception(f"Unexpected error loading profile data for user_id {user_id}: {e}")
            if hasattr(self.view, 'show_error'):
                self.view.show_error("An unexpected error occurred.")

        if hasattr(self.view, 'display_profile_data'):
            self.view.display_profile_data(user_info, stats)
            logger.info("Profile data passed to view.")
        else:
            logger.error("View object for ProfileController does not have 'display_profile_data' method!")

    def _mask_email(self, email):
        """Masks email address, e.g., 'user@example.com' -> 'us***@example.com'."""
        if not email or '@' not in email:
            return email
        try:
            local_part, domain = email.split('@', 1)
            if len(local_part) <= 3:
                masked_local = local_part[0] + '***'
            else:
                masked_local = local_part[:2] + '***' + local_part[-1]
            return f"{masked_local}@{domain}"
        except Exception:
            logger.warning(f"Could not mask email: {email}", exc_info=True)
            return email

    def _format_datetime(self, dt):
        """Formats datetime object into a readable string."""
        if not dt:
            return "N/A"
        try:
            return dt.strftime("%d %B %Y, %H:%M")
        except (AttributeError, ValueError):
            logger.warning(f"Could not format datetime: {dt}", exc_info=True)
            return str(dt)

    def change_password(self, current_password, new_password, confirm_password):
        """Handles the password change request from the view."""
        logger.info("Password change attempt initiated.")
        self.view.show_password_feedback("", is_error=False)

        if not all([current_password, new_password, confirm_password]):
            logger.warning("Password change failed: Not all fields provided.")
            self.view.show_password_feedback("All password fields are required.", is_error=True)
            return

        if new_password != confirm_password:
            logger.warning("Password change failed: New passwords do not match.")
            self.view.show_password_feedback("New passwords do not match.", is_error=True)
            return

        if len(new_password) < 6:
            logger.warning("Password change failed: New password too short.")
            self.view.show_password_feedback("New password must be at least 6 characters.", is_error=True)
            return

        user_id = self.session_model.get_current_user_id()
        if not user_id:
            logger.error("Password change failed: Cannot get user_id from session.")
            self.view.show_password_feedback("Error: User session not found.", is_error=True)
            return

        try:
            current_hash = self.data_model.get_user_password_hash(user_id)
            if not current_hash:
                logger.error(f"Password change failed: Could not retrieve current password hash for user {user_id}.")
                self.view.show_password_feedback("Error retrieving user data.", is_error=True)
                return

        except DatabaseError as e:
            logger.exception(f"Database error fetching current password hash for user {user_id}: {e}")
            self.view.show_password_feedback("Database error checking password.", is_error=True)
            return
        except Exception as e:
            logger.exception(f"Unexpected error fetching current password hash for user {user_id}: {e}")
            self.view.show_password_feedback("An unexpected error occurred.", is_error=True)
            return

        try:
            if not bcrypt.checkpw(current_password.encode('utf-8'), current_hash.encode('utf-8')):
                logger.warning(f"Password change failed: Incorrect current password for user {user_id}.")
                self.view.show_password_feedback("Incorrect current password.", is_error=True)
                return
        except ValueError as e:
            logger.error(f"Password check error (ValueError) for user {user_id}: {e}. Hash might be invalid.")
            self.view.show_password_feedback("Error checking current password validity.", is_error=True)
            return
        except Exception as e:
            logger.exception(f"Unexpected error during password check for user {user_id}: {e}")
            self.view.show_password_feedback("An unexpected error occurred during password check.", is_error=True)
            return

        try:
            new_hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            new_hash_str = new_hashed_pw.decode('utf-8')
            logger.debug("New password hashed successfully.")
        except Exception as e:
            logger.exception(f"Password hashing error for new password (user {user_id}): {e}")
            self.view.show_password_feedback("Error processing new password.", is_error=True)
            return

        try:
            success = self.data_model.update_user_password(user_id, new_hash_str)
            if success:
                logger.info(f"Password updated successfully in DB for user {user_id}.")
                self.view.show_password_feedback("Password updated successfully.", is_error=False)
                self.view.clear_password_fields()
            else:
                 logger.error(f"Failed to update password in DB for user {user_id} (model returned False).")
                 self.view.show_password_feedback("Failed to save new password.", is_error=True)

        except DatabaseError as e:
            logger.exception(f"Database error updating password for user {user_id}: {e}")
            self.view.show_password_feedback("Database error saving new password.", is_error=True)
        except Exception as e:
            logger.exception(f"Unexpected error updating password for user {user_id}: {e}")
            self.view.show_password_feedback("An unexpected error occurred saving password.", is_error=True)