import os
import importlib
import logging

from kivy.core.window import Window
from kivy.lang import Builder
from kivymd.app import MDApp

from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivymd.uix.menu import MDDropdownMenu

from config import BASE_DIR, KV_DIR, VIEW_DIR, CONTROLLER_DIR

from model.session_model import SessionModel
from model.database_model import DatabaseModel, initialize_pool, close_pool

log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)

SCREENS = {
    "ratings": "Ratings",
    "signup": "SignUp",
    "login": "Login",
    "profile": "Profile",
    "add_item": "AddItem",
}

class RateSphere(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.menu_navigation_data = []
        self.menu_profile_data = []

        Window.fullscreen = "auto"
        self.icon = "assets/icons/icon.icon"
        logger.info("-----------------------------------")

    def build(self):
        logger.info("Building the application UI...")
        try:
            initialize_pool()
            self.models = {
                'session': SessionModel(),
                'database': DatabaseModel(),
            }
        except Exception as e:
            logger.exception("FATAL: Failed to initialize models or database pool during build!")
            raise RuntimeError("Failed to initialize critical components.") from e

        saved_theme = self.models['session'].get_preferred_theme_style()
        logger.info(f"Applying initial theme: {saved_theme}")
        self.theme_cls.theme_style = saved_theme
        self.theme_cls.primary_palette = "Darkgrey"
        self.theme_cls.accent_palette = "Indigo"

        self.menu_navigation_data = [
            {
                "text": "Ratings",
                "on_release": lambda: self.open_screen("ratings", "navigation"),
                "leading_icon": "star-outline",
            },
            {
                "text": "Add item",
                "on_release": lambda: self.open_screen("add_item", "navigation"),
                "leading_icon": "plus-circle-outline",
            },
            {
                "text": "Exit",
                "on_release": self.exit_app,
                "leading_icon": "logout",
            },
        ]

        self.menu_profile_data = [
            {
                "text": "Profile",
                "on_release": lambda: self.open_screen("profile", "profile"),
                "leading_icon": "account-circle-outline",
            },
            {
                "text": "Switch theme",
                "on_release": lambda: self.switch_theme_style(),
                "leading_icon": "theme-light-dark",
            },
            {
                "text": "Logout",
                "on_release": lambda: self.logout(),
                "leading_icon": "logout",
            },
        ]

        self.screen_manager = ScreenManager(transition=NoTransition())

        logger.info("--- Loading KV Files ---")
        for screen_name in SCREENS.keys():
             kv_file_path = os.path.join(KV_DIR, f"{screen_name}_screen.kv")
             if os.path.exists(kv_file_path):
                 try:
                     Builder.load_file(kv_file_path)
                     logger.info(f"KV file loaded: {kv_file_path}")
                 except Exception as e:
                     logger.exception(f"Loading KV file: {kv_file_path}: {e}")
             else:
                 logger.warning(f"KV file not found: {kv_file_path}")
        logger.info("--- KV Loading Complete ---")

        logger.info("--- Registering Screens ---")
        created_screens = []
        for screen_name, class_prefix in SCREENS.items():
            view_instance = self._register_screen_modules(screen_name, class_prefix)
            if view_instance:
                created_screens.append(view_instance)
        logger.info("--- Screen Module Registration Complete ---")

        logger.info(f"--- Adding {len(created_screens)} screens to ScreenManager (Phase 2) ---")
        for screen_instance in created_screens:
             try:
                 self.screen_manager.add_widget(screen_instance)
                 logger.info(f"Added screen: {screen_instance.name}")
             except Exception as e:
                 logger.exception(f"FAILED to add screen {screen_instance.name} to manager: {e}")
        logger.info(f"--- ScreenManager final screens: {self.screen_manager.screen_names} ---")

        logger.info("Build process completed.")
        return self.screen_manager

    def _register_screen_modules(self, screen_name: str, class_prefix: str):
        """
        Imports View and Controller, creates their instances, and associates them.
        Returns the created view_instance or None on failure.
        Assumes KV file has already been loaded in the build() method.
        DOES NOT add the widget to the screen manager.
        """
        logger.debug(f"Registering modules for: '{screen_name}' (Classes: {class_prefix}...)")
        view_instance = None

        view_module_name = f"view.screens.{screen_name}_screen"
        view_class_name = f"{class_prefix}Screen"
        controller_module_name = f"controller.{screen_name}_controller"
        controller_class_name = f"{class_prefix}Controller"
        controller_attr_name = f"{screen_name}_controller"

        try:
            view_module = importlib.import_module(view_module_name)
            ViewClass = getattr(view_module, view_class_name)
            view_instance = ViewClass(name=screen_name)
            logger.debug(f"View created: {view_class_name}")

            controller_module = importlib.import_module(controller_module_name)
            ControllerClass = getattr(controller_module, controller_class_name)
            controller_instance = ControllerClass(
                models=self.models,
                view=view_instance,
                app=self
            )
            logger.debug(f"Controller created: {controller_class_name}")

            setattr(self, controller_attr_name, controller_instance)
            logger.debug(f"Controller available as: app.{controller_attr_name}")

        except ImportError as e:
            logger.error(f"IMPORT FAILED for screen '{screen_name}': {e}")
            logger.error(f"Please check: {view_module_name.replace('.', '/')}.py (Class {view_class_name}) or {controller_module_name.replace('.', '/')}.py (Class {controller_class_name})")
            view_instance = None
        except AttributeError as e:
            logger.error(f"ATTRIBUTE ERROR for screen '{screen_name}': {e}")
            logger.error(f"Check that the classes '{view_class_name}' and '{controller_class_name}' exist in the corresponding files.")
            view_instance = None
        except Exception as e:
            logger.exception(f"  - UNKNOWN ERROR while registering screen modules for '{screen_name}': {e}")
            view_instance = None

        return view_instance

    def on_start(self):
        """Set the initial screen depending on the login status."""
        logger.info("Application starting, checking login status...")
        try:
            session = self.models['session']
            if session.is_logged_in():
                logger.info(f"User '{session.get_current_username()}' is already logged in. Navigating to 'ratings'.")
                self.root.current = "ratings"
            else:
                logger.info("No user logged in. Navigating to 'login'.")
                self.root.current = "login"
        except Exception as e:
            logger.exception("Error in on_start determining initial screen")
            try:
                self.root.current = "login"
                logger.warning("Setting screen to 'login' due to error in on_start.")
            except Exception as e2:
                logger.critical(f"Failed to set screen to login after error in on_start: {e2}")

    def on_stop(self):
        logger.info("Application stopping.")
        close_pool()
        logger.info("Database connection pool closed.")

    def logout(self):
        """Performs user logout: clears the session and goes to the login screen."""
        logger.info("Executing app logout sequence...")
        if 'session' in self.models:
            current_user = self.models['session'].get_current_username()
            self.models['session'].logout()
            logger.info(f"User '{current_user}' logged out.")

        if self.root and hasattr(self.root, 'current'):
            self.root.current = 'login'
            logger.info("Switched to login screen.")
        else:
            logger.error("Cannot switch screen, root widget or screen_manager not found/ready during logout.")

        if hasattr(self, 'profileMenu') and self.profileMenu:
            self.profileMenu.dismiss()
            logger.debug("Profile menu dismissed during logout.")

        if hasattr(self, 'appBarMenu') and self.appBarMenu:
            self.appBarMenu.dismiss()
            logger.debug("App bar menu dismissed during logout.")

    def open_app_bar_menu(self, menu_button):
        self.appBarMenu = MDDropdownMenu(
            caller=menu_button,
            items=self.menu_navigation_data,
        )
        self.appBarMenu.open()
        logger.debug("Opening app bar menu")

    def open_profile_menu(self, menu_button):
        self.profileMenu = MDDropdownMenu(
            caller=menu_button,
            items=self.menu_profile_data,
        )
        self.profileMenu.open()
        logger.debug("Opening profile menu")

    def open_screen(self, screen_name, menu_type):
        logger.debug(f"Opening screen: {screen_name}")
        self.screen_manager.current = screen_name
        menu_to_dismiss = None
        if menu_type == "navigation" and hasattr(self, 'appBarMenu') and self.appBarMenu:
            menu_to_dismiss = self.appBarMenu
        elif menu_type == "profile" and hasattr(self, 'profileMenu') and self.profileMenu:
            menu_to_dismiss = self.profileMenu

        if menu_to_dismiss:
            menu_to_dismiss.dismiss()
            logger.debug(f"Dismissed '{menu_type}' menu.")
        elif menu_to_dismiss is None and menu_type in ["navigation", "profile"]:
            logger.warning(f"Tried to dismiss menu '{menu_type}' but it wasn't found or initialized.")

    def switch_theme_style(self):
        """Switches the theme style (Light/Dark) and saves the selection."""
        current_style = self.theme_cls.theme_style
        new_style = "Dark" if current_style == "Light" else "Light"
        self.theme_cls.theme_style = new_style
        logger.info(f"Theme switched from {current_style} to: {new_style}")

        try:
            self.models['session'].save_theme_style(new_style)
        except Exception as e:
            logger.exception("Failed to save theme style preference.")

        if hasattr(self, 'profileMenu') and self.profileMenu:
            self.profileMenu.dismiss()
            logger.debug("Profile menu dismissed after theme switch.")

    @staticmethod
    def exit_app():
        logger.info("Exit requested by user.")
        MDApp.get_running_app().stop()


if __name__ == '__main__':
    logger.info("Starting RateSphere application...")
    try:
        RateSphere().run()
    except Exception as e:
        logger.critical("Unhandled exception caused application to crash.", exc_info=True)
    finally:
        logger.info("RateSphere application finished.")
