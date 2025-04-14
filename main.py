import os
import importlib

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivymd.app import MDApp

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

        Window.fullscreen = "auto"
        # TODO create icon for program

        self.theme_cls.theme_style_switch_animation = True
        self.theme_cls.theme_style_switch_animation_duration = 0.8
        self.theme_cls.theme_style = "Dark"          # Light
        self.theme_cls.primary_palette = "Darkgrey"  # Indigo

    def build(self):
        initialize_pool()
        self.models = {
            'session': SessionModel(),
            'database': DatabaseModel(),
        }

        self.screen_manager = ScreenManager(transition=NoTransition())

        for screen_name, class_prefix in SCREENS.items():
            self._register_screen(screen_name, class_prefix)

        return self.screen_manager

    def _register_screen(self, screen_name: str, class_prefix: str):
        """
        Dynamically loads KV, imports View and Controller,
        creates their instances and registers.
        """
        print(f"Screen registration: '{screen_name}' (Classes: {class_prefix}...)")

        kv_file_path = os.path.join(KV_DIR, f"{screen_name}_screen.kv")
        if os.path.exists(kv_file_path):
            Builder.load_file(kv_file_path)
            print(f"  - KV file uploaded: {kv_file_path}")
        else:
            print(f"  - WARNING: KV file not found: {kv_file_path}")

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
            print(f"  - The controller is available as: app.{controller_attr_name}")

            self.screen_manager.add_widget(view_instance)
            print(f"  - Screen '{screen_name}' added to ScreenManager")

        except ImportError as e:
            print(f"  - IMPORT FAILED for screen '{screen_name}': {e}")
            print(f"    Please check the availability of files and the correctness of their names.:")
            print(f"    - {view_module_name.replace('.', '/')}.py (Class {view_class_name})")
            print(f"    - {controller_module_name.replace('.', '/')}.py (Class {controller_class_name})")
        except AttributeError as e:
            print(f"  - ATTRIBUTE ERROR for screen '{screen_name}': {e}")
            print(f"    Check that the classes '{view_class_name}' and '{controller_class_name}' exist in the corresponding files.")
        except Exception as e:
            print(f"  - UNKNOWN ERROR while registering the screen '{screen_name}': {e}")


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


if __name__ == '__main__':
    RateSphere().run()