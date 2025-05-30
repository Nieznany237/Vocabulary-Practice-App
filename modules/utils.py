import os
import sys
import json
from tkinter import messagebox

def get_program_path(show_messagebox=False, status_flag=None):
    """
    Prints and optionally shows a messagebox with debug info about the current program path and environment.
    Args:
        show_messagebox (bool): If True, shows a messagebox with the info.
        status_flag (str, optional): Status string to display (e.g., JSON loaded status). If None, omits this line.
    """
    print("\n=== Debug: Program Path ===")
    print("Current program directory:", os.getcwd())
    if status_flag is not None:
        print(f"Status flag: {status_flag}")
    print("Frozen? (PyInstaller)", getattr(sys, 'frozen', False))
    print("Compiled? (Nuitka)", "__compiled__" in globals())
    print("=== Debug: Program Path ===\n")
    if show_messagebox:
        msg = f"Current program directory: {os.getcwd()}\n\n"
        if status_flag is not None:
            msg += f"Status flag: {status_flag}\n"
        msg += f"Frozen? (PyInstaller) - {getattr(sys, 'frozen', False)}\n"
        msg += f"Compiled? (Nuitka) - {'__compiled__' in globals()}"
        messagebox.showinfo("Program Path", msg)

def load_settings_from_json(file_path, target_dict=None, version_key="VERSION", required_version=None, ignore_version_error_key="IGNORE_VERSION_ERROR", settings_key="APP_SETTINGS", show_errors=True):
    """
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