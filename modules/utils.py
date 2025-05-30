import os
import sys
import json
from tkinter import messagebox
from PIL import Image, ImageTk
import platform
import customtkinter as ctk

def get_program_path(show_messagebox=False, status_flag=None):
    """
    v1.0.1 (2025-05-30)
    Prints and optionally shows a messagebox with debug info about the current program path and environment.
    Args:
        show_messagebox (bool): If True, shows a messagebox with the info.
        status_flag (str, optional): Status string to display (e.g., JSON loaded status). If None, omits this line.
    """
    print("\n=== Debug: Program Path ===")
    print("Current program directory:", os.getcwd())
    if status_flag is not None:
        print(f"JSON status: {status_flag}")
    else:
        print("JSON status: Not provided")
    print("Frozen? (PyInstaller)", getattr(sys, 'frozen', False))
    print("Compiled? (Nuitka)", "__compiled__" in globals())
    print("=== Debug: Program Path ===\n")
    if show_messagebox:
        msg = f"Current program directory: {os.getcwd()}\n\n"
        if status_flag is not None:
            msg += f"JSON status: {status_flag}\n"
        msg += f"Frozen? (PyInstaller) - {getattr(sys, 'frozen', False)}\n"
        msg += f"Compiled? (Nuitka) - {'__compiled__' in globals()}"
        messagebox.showinfo("Program Path", msg)

def load_settings_from_json(file_path, target_dict=None, version_key="VERSION", required_version=None, ignore_version_error_key="IGNORE_VERSION_ERROR", settings_key="APP_SETTINGS", show_errors=True):
    """
    v1.0.2 (2025-05-30)
    Loads settings from a JSON file and updates a target dictionary (if provided).
    Args:
        file_path (str): Path to the JSON file.
        target_dict (dict, optional): Dictionary to update with loaded settings. If None, returns loaded settings.
        version_key (str): Key for version in JSON.
        required_version (int, optional): If set, checks for version match.
        ignore_version_error_key (str): Key to ignore version error in JSON.
        settings_key (str): Key in JSON for the settings dict to merge.
        show_errors (bool): If True, prints or shows errors.
    Returns:
        tuple: (status_flag, updated_dict or loaded_settings)
    """
    status_flag = "False - Unknown"
    loaded_settings = None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        # Version check
        if required_version is not None and version_key in settings:
            json_version = settings[version_key]
            if json_version != required_version:
                status_flag = "False - Version mismatch"
                if ignore_version_error_key in settings and settings[ignore_version_error_key]:
                    if show_errors:
                        print(f"[WARNING]: The JSON version ({json_version}) does not match the required version ({required_version}), but the error is ignored. The settings will not be loaded.")
                else:
                    if show_errors:
                        print(f"[ERROR]: JSON version ({json_version}) does not match required version ({required_version}). Default settings will be applied.")
                        try:
                            messagebox.showerror("Error", f"[ERROR]: JSON version ({json_version}) does not match required version ({required_version}). Default settings will be applied.")
                        except:
                            pass
                    return status_flag, target_dict if target_dict is not None else None
        # Merge or return settings
        if settings_key in settings:
            loaded_settings = settings[settings_key]
            if target_dict is not None:
                target_dict.update(loaded_settings)
                status_flag = "True"
                return status_flag, target_dict
            else:
                status_flag = "True"
                return status_flag, loaded_settings
        else:
            if show_errors:
                print(f"[WARNING]: Settings key '{settings_key}' not found in JSON. Returning all settings.")
            status_flag = "True"
            return status_flag, settings
    except FileNotFoundError:
        if show_errors:
            print(f"[WARNING]: File {file_path} not found. Using default settings.")
        status_flag = "False - File not found"
    except json.JSONDecodeError as e:
        if show_errors:
            print(f"[ERROR]: JSON decoding error: {e}")
            print("Using default settings.")
        status_flag = "False - JSON decode error"
    except Exception as e:
        if show_errors:
            print(f"[ERROR]: Unexpected error: {e}")
        status_flag = "False - Unexpected error"
    return status_flag, target_dict if target_dict is not None else None

def set_app_icon(app, icon_dark_path="Assets/Vocabulary-Practice-App/Icons/book_pink.png", icon_light_path="Assets/Vocabulary-Practice-App/Icons/book_pink.png"):
    """
    v1.1.1 (2025-05-30)
    Sets the application window icon based on the current system appearance mode (dark/light).
    Automatically selects the appropriate icon version. On Windows, works around CustomTkinter bug by resetting icon after 200ms.
    Args:
        app: The application or window instance. If it has .root, uses app.root, else uses app itself.
        icon_dark_path (str): Path to the icon for dark mode
        icon_light_path (str): Path to the icon for light mode
    ! https://github.com/TomSchimansky/CustomTkinter/issues/1163
    """
    appearance_mode = ctk.get_appearance_mode()
    icon_path = icon_dark_path if appearance_mode == "Dark" else icon_light_path
    icon_loaded = False
    # Use .root if present, else use app itself
    window = getattr(app, 'root', app)
    if os.path.exists(icon_path):
        try:
            icon_image = Image.open(icon_path)
            icon_photo = ImageTk.PhotoImage(icon_image)
            window.iconphoto(False, icon_photo)
            icon_loaded = True
        except Exception as e:
            print(f"[ERROR] Failed to load icon: {e}")
    else:
        print(f"[WARNING] File {icon_path} has not been found.")
    # Workaround for CustomTkinter Windows bug
    if icon_loaded and platform.system().lower().startswith("win"):
        def reset_icon():
            try:
                window.iconphoto(False, icon_photo)
            except Exception as e:
                print(f"[ERROR] Failed to reset icon after delay: {e}")
        window.after(200, reset_icon)