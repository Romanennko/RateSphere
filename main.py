import os
import importlib

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivymd.app import MDApp

from kivymd.uix.menu import MDDropdownMenu

from config import BASE_DIR, KV_DIR, VIEW_DIR, CONTROLLER_DIR

from model.session_model import SessionModel
from model.database_model import DatabaseModel, initialize_pool, close_pool

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
        self.icon = "assets/icons/icon.png"

        self.theme_cls.theme_style_switch_animation = True
        self.theme_cls.theme_style_switch_animation_duration = 0.8

    def build(self):
        initialize_pool()
        self.models = {
            'session': SessionModel(),
            'database': DatabaseModel(),
        }

        saved_theme = self.models['session'].get_preferred_theme_style()
        print(f"Applying initial theme: {saved_theme}")
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

        print("--- Loading KV Files ---")
        for screen_name in SCREENS.keys():
             kv_file_path = os.path.join(KV_DIR, f"{screen_name}_screen.kv")
             if os.path.exists(kv_file_path):
                 try:
                     Builder.load_file(kv_file_path)
                     print(f"  - KV file loaded: {kv_file_path}")
                 except Exception as e:
                     print(f"  - ERROR loading KV file {kv_file_path}: {e}")
             else:
                 print(f"  - WARNING: KV file not found: {kv_file_path}")
        print("--- KV Loading Complete ---")

        print("--- Registering Screens ---")
        created_screens = []
        for screen_name, class_prefix in SCREENS.items():
            view_instance = self._register_screen_modules(screen_name, class_prefix)
            if view_instance:
                created_screens.append(view_instance)
        print("--- Screen Module Registration Complete ---")

        print(f"--- Adding {len(created_screens)} screens to ScreenManager (Phase 2) ---")
        for screen_instance in created_screens:
             try:
                 self.screen_manager.add_widget(screen_instance)
                 print(f"  - Added screen: {screen_instance.name}")
             except Exception as e:
                 print(f"  - FAILED to add screen {screen_instance.name} to manager: {e}")
        print(f"--- ScreenManager final screens: {self.screen_manager.screen_names} ---")

        return self.screen_manager

    def _register_screen_modules(self, screen_name: str, class_prefix: str):
        """
        Imports View and Controller, creates their instances, and associates them.
        Returns the created view_instance or None on failure.
        Assumes KV file has already been loaded in the build() method.
        DOES NOT add the widget to the screen manager.
        """
        print(f"Registering modules for: '{screen_name}' (Classes: {class_prefix}...)")
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
            print(f"  - View created: {view_class_name}")

            controller_module = importlib.import_module(controller_module_name)
            ControllerClass = getattr(controller_module, controller_class_name)
            controller_instance = ControllerClass(
                models=self.models,
                view=view_instance,
                app=self
            )
            print(f"  - Controller created: {controller_class_name}")

            setattr(self, controller_attr_name, controller_instance)
            print(f"  - Controller available as: app.{controller_attr_name}")

        except ImportError as e:
            print(f"  - IMPORT FAILED for screen '{screen_name}': {e}")
            print(f"    Please check the availability of files and the correctness of their names:")
            print(f"    - {view_module_name.replace('.', '/')}.py (Class {view_class_name})")
            print(f"    - {controller_module_name.replace('.', '/')}.py (Class {controller_class_name})")
            view_instance = None
        except AttributeError as e:
            print(f"  - ATTRIBUTE ERROR for screen '{screen_name}': {e}")
            print(f"    Check that the classes '{view_class_name}' and '{controller_class_name}' exist in the corresponding files.")
            view_instance = None
        except Exception as e:
            print(f"  - UNKNOWN ERROR while registering screen modules for '{screen_name}': {e}")
            view_instance = None

        return view_instance


    def on_start(self):
        """Set the initial screen depending on the login status."""
        try:
            session = self.models['session']

            if session.is_logged_in():
                print(f"User '{session.get_current_username()}' is already logged in. Navigating to 'ratings'.")
                self.root.current = "ratings"
            else:
                print("No user logged in. Navigating to 'login'.")
                self.root.current = "login"
        except Exception as e:
             print(f"Error in on_start: {e}")
             try:
                 self.root.current = "login"
             except Exception as e2:
                 print(f"Failed to set screen to login after error: {e2}")

    def on_stop(self):
        close_pool()

    def logout(self):
        """Performs user logout: clears the session and goes to the login screen."""
        print("Executing app logout sequence...")
        if 'session' in self.models:
            self.models['session'].logout()

        if self.root and hasattr(self.root, 'current'):
            self.root.current = 'login'
        else:
            print("Error: Cannot switch screen, root widget or screen_manager not found/ready.")

        if hasattr(self, 'profileMenu') and self.profileMenu:
            self.profileMenu.dismiss()
            print("Profile menu dismissed.")

    def open_app_bar_menu(self, menu_button):
        self.appBarMenu = MDDropdownMenu(
            caller=menu_button,
            items=self.menu_navigation_data,
        )
        self.appBarMenu.open()

    def open_profile_menu(self, menu_button):
        self.profileMenu = MDDropdownMenu(
            caller=menu_button,
            items=self.menu_profile_data,
        )
        self.profileMenu.open()

    def open_screen(self, screen_name, menu):
        self.screen_manager.current = screen_name
        if menu == "navigation" and self.appBarMenu:
            self.appBarMenu.dismiss()
        elif menu == "profile" and self.profileMenu:
            self.profileMenu.dismiss()
        else:
            print(f"Warning: Trying to dismiss menu '{menu}' before it was created.")

    def switch_theme_style(self):
        """Switches the theme style (Light/Dark) and saves the selection."""
        current_style = self.theme_cls.theme_style
        self.theme_cls.theme_style = "Dark" if current_style == "Light" else "Light"
        print(f"Theme switched to: {self.theme_cls.theme_style}")

        self.models['session'].save_theme_style(self.theme_cls.theme_style)

        if hasattr(self, 'profileMenu') and self.profileMenu:
            self.profileMenu.dismiss()

    @staticmethod
    def exit_app():
        MDApp.get_running_app().stop()


if __name__ == '__main__':
    RateSphere().run()