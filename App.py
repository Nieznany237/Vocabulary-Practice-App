import customtkinter as ctk
from CTkMenuBar import *
import os
from PIL import Image, ImageTk
from functools import lru_cache
import random
from tkinter import filedialog, messagebox
import sys
import webbrowser
import platform
import json

# temp
from pprint import pprint
REQUIRED_JSON_VERSION = 1
# Application version and release date
APP_VERSION = {
    "version": "1.2.0",
    "release_date": "04.05.2025"
}

RESOURCE_FILE_PATHS = {
    "json_config": "Assets/Vocabulary-Practice-App/settingsV2.json"
}

APP_SETTINGS = {
    "title": "Vocabulary Practice App",
    "window_size": "535x520",
    "SetIcon": False,
    "resizable": [True, True],
    "Language": "en",
    "appearance_mode": "dark",
    "color_theme": "blue",
    "ui_zoom_factor": 1.075,
}

# Stan programu
words = []
selected_word = None  # Initialize selected_word as None
mode = "mixed"  # Initialize mode with a default value
hint_shown = False  # Initialize hint_shown as False

available_words = ""  # Initialize available_words as an empty string

# Lista blokowanych numerów linii
blocked_lines = set()

def set_window_icon(app):
    """
    Function: set_window_icon(app)

    Sets the application window icon based on the current system appearance mode (dark/light).
    The function automatically selects the appropriate version of the icon (white for dark mode, dark for light mode).

    Error Handling:
    - Prints warning if icon file is not found
    - Prints error if icon loading fails
    - Silently continues if icon cannot be set (The default CTk icon will be used instead)
    """

    # Determine the appearance mode of the application
    appearance_mode = ctk.get_appearance_mode()
    
    # Selecting the appropriate icon
    if appearance_mode == "Dark":
        icon_path = "Assets/Vocabulary-Practice-App/Icons/book_pink.png"
    else:
        icon_path = "Assets/Vocabulary-Practice-App/Icons/book_pink.png"
    
    # Flag to check if the icon has been loaded
    icon_loaded = False
    
    # Checking if the icon file exists
    if os.path.exists(icon_path):
        try:
            icon_image = Image.open(icon_path)
            icon_photo = ImageTk.PhotoImage(icon_image)
            app.root.iconphoto(False, icon_photo)  # Setting the icon on the main window
            icon_loaded = True
        except Exception as e:
            print(f"[ERROR] Failed to load icon: {e}")
    else:
        print(f"[WARNING] File {icon_path} has not been found.")
    
    # Set icon only if loaded correctly
    if icon_loaded:
        app.root.wm_iconbitmap()

def get_program_path(show_messagebox=False):
    # Print the current working directory (for debug purposes)
    print("\n=== Debug: Program Path ===")
    print("Current program directory:", os.getcwd())
    print("Frozen? (PyInstaller)",getattr(sys, 'frozen', False))
    print("Compiled? (Nuitka)", "__compiled__" in globals())
    print("=== Debug: Program Path ===\n")
    if show_messagebox:
        messagebox.showinfo(
            "Program Path", 
            f"Current program directory: {os.getcwd()}\n\n"
            f"Frozen? (PyInstaller) - {getattr(sys, 'frozen', False)}\n"
            f"Compiled? (Nuitka) - {'__compiled__' in globals()}"
            )

get_program_path()


# Function to convert lists to tuples for fonts
def convert_font_lists_to_tuples(font_settings):
    for key, value in font_settings.items():
        if isinstance(value, list):
            font_settings[key] = tuple(value)
    return font_settings

# Function to load settings from a JSON file
def load_settings_from_json(file_path = RESOURCE_FILE_PATHS["json_config"]):
    """
    Function: load_settings_from_json(file_path)
    Loads application settings from a JSON file into global variables.

    Args:
        file_path: Path to JSON settings file RESOURCE_FILE_PATHS["json_config"]

    Behavior:
    - Validates JSON version
    - Loads one setting categories:
    - APP_SETTINGS (merged with existing)
    - Falls back to default settings on errors

    Error Handling:
    - Version mismatch (unless IGNORE_VERSION_ERROR=True)
    - Missing file
    - JSON decode errors
    - Other unexpected errors

    Globals Modified:
    - APP_SETTINGS 
    """
    global APP_SETTINGS
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        # Check the JSON version
        if "VERSION" in settings:
            json_version = settings["VERSION"]
            if json_version != REQUIRED_JSON_VERSION:
                if "IGNORE_VERSION_ERROR" in settings and settings["IGNORE_VERSION_ERROR"]:
                    print(f"[WARNING]: The JSON version ({json_version}) does not match the required version ({REQUIRED_JSON_VERSION}), but the error is ignored. The settings will not be loaded.")
                else:
                    print(f"[ERROR]: JSON version ({json_version}) does not match required version ({REQUIRED_JSON_VERSION}). Default settings will be applied.")
                    messagebox.showerror("Error", f"[ERROR]: JSON version ({json_version}) does not match required version ({REQUIRED_JSON_VERSION}). Default settings will be applied.")
                return
        else:
            print("[WARNING]: JSON version information missing. Default settings will be applied.")
            return

        # Merge application settings with existing ones
        if "APP_SETTINGS" in settings:
            APP_SETTINGS.update(settings["APP_SETTINGS"])

        print("[INFO]: Loaded settings from file.")

    except FileNotFoundError:
        print(f"[WARNING]: File {file_path} not found. Using default settings.")
    except json.JSONDecodeError as e:
        print(f"[ERROR]: JSON decoding error: {e}")
        print("Using default settings.")
    except Exception as e:
        print(f"[ERROR]: Unexpected error: {e}")

# Loading settings
# If you don't want to load settings from JSON, then comment out the function call
load_settings_from_json()

if APP_SETTINGS["Language"] == "pl":
    # Load Right_Lang translations
    from translation import TRANSLATIONS_PL as TRANSLATIONS
else:
    # Load Left_Lang translations
    from translation import TRANSLATIONS_EN as TRANSLATIONS

# JSON DEBUG
'''
print("FONT_SETTINGS:", FONT_SETTINGS)
print("APP_SETTINGS:", APP_SETTINGS)
print("COLOR_SETTINGS:", COLOR_SETTINGS)
'''


def change_ui_scale(scale=0):
    APP_SETTINGS["ui_zoom_factor"] += scale
    
    APP_SETTINGS["ui_zoom_factor"] = round(APP_SETTINGS["ui_zoom_factor"], 3)
    print(f"UI zoom factor: {APP_SETTINGS['ui_zoom_factor']}")
    ctk.set_window_scaling(APP_SETTINGS["ui_zoom_factor"])
    ctk.set_widget_scaling(APP_SETTINGS["ui_zoom_factor"])

@lru_cache(maxsize=None)
def t_path(path):

    """
    Retrieves a translation value from the TRANSLATIONS dictionary using a dot-separated path.
    This is a helper function to easily access nested translation values.
    Args:
        path (str): Dot-separated path to the translation (e.g., "menubar.file.file")
    Returns:
        str: The translated string if found, or a placeholder string in format "[path]" if not found
    Example:
        >>> t_path("menubar.file.file")
        "File"
        >>> t_path("invalid.path")
        "[invalid.path]"
        
    Note:
        The function is a shortened version of get_translation_by_path (as suggested by the name)
    """
    keys = path.split(".")
    value = TRANSLATIONS
    try:
        for key in keys:
            value = value[key]
        return value
    except KeyError:
        return f"[{path}]"

def get_cache_info():
    print(t_path.cache_info())


class MainApp():
    def __init__(self, root):
        super().__init__()


        def set_app_appearance_mode(theme):
            ctk.set_appearance_mode(theme)

            if APP_SETTINGS["SetIcon"]:
                set_window_icon(self)

        # ==========================================================================
        # Main functions

        def load_words_from_file(file_path=None):
            """Returns only a list of vocabulary words from the file, ignoring the first line."""
            words_list = []
            if not file_path:
                return words_list

            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    lines = file.readlines()

                    for line_number, line in enumerate(lines[1:], start=2):
                        if " - " in line:
                            Left_Lang, Right_Lang = line.strip().split(" - ")
                            if Left_Lang != Right_Lang:
                                words_list.append({
                                    "Left_Lang": Left_Lang,
                                    "Right_Lang": Right_Lang,
                                    "line_number": line_number
                                })
            except FileNotFoundError:
                print(f"File {file_path} not found.")
            if file_path:
                get_language_names(file_path)
            pprint(words_list, width=130)
            return words_list


        def get_language_names(file_path):
            """Returns the language names from the first line of the file and updates the text of the radiobuttons."""
            language_names = ("Left", "Right") 

            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    first_line = file.readline()
                    if " - " in first_line:
                        language_names = tuple(first_line.strip().split(" - "))
            except FileNotFoundError:
                print(f"File {file_path} not found.")

            # Update radiobutton text
            self.radio_Left_Lang_to_Right_Lang.configure(
                text = f"{language_names[0]} ► {language_names[1]}"
            )

            self.radio_Right_Lang_to_Left_Lang.configure(
                text = f"{language_names[1]} ► {language_names[0]}"
            )

            return language_names

        def pick_new_word():
            """Losuje nowe słowo zgodnie z wybranym trybem, z uwzględnieniem blokady."""
            global selected_word, mode, hint_shown, available_words
            if not words:
                # Brak załadowanych słówek!
                self.question_label.configure(text=t_path("main_window.question_label.Not_loaded"))
                return

            hint_shown = False

            # Filter words by blocklist
            available_words = words if not self.block_repeated_questions.get() else [
                word for word in words if word["line_number"] not in blocked_lines
            ]

            if not available_words:
                # Brak dostępnych słówek do wyświetlenia!
                self.question_label.configure(text=t_path("main_window.question_label.No_words"))
                self.check_button.configure(state="disabled")
                self.hint_button.configure(state="disabled")
                return

            selected_word = random.choice(available_words)

            # Dodaj numer linii do blokady
            if self.block_repeated_questions.get():
                blocked_lines.add(selected_word["line_number"])

            question_text = selected_word["Left_Lang"] if mode == "Left_Lang_to_Right_Lang" else selected_word["Right_Lang"]
            if mode == "mixed":
                mode = random.choice(["Left_Lang_to_Right_Lang", "Right_Lang_to_Left_Lang"])
                print(f"Mode: {mode}")
                question_text = selected_word["Left_Lang"] if mode == "Left_Lang_to_Right_Lang" else selected_word["Right_Lang"]

            # Podaj tłumaczenie słowa:
            self.question_label.configure(text=f"{t_path("main_window.question_label.TranslateIt")} {question_text}")
            self.line_info_label.configure(text=f"{t_path("main_window.line_info_label")} {selected_word['line_number']}", text_color="gray")
            self.entry.delete(0, ctk.END)
            self.result_label.configure(text="")

        def set_buttons_state(state):
            """Sets the status of all buttons and radiobuttons."""
            self.check_button.configure(state=state)
            self.hint_button.configure(state=state)
            self.skip_button.configure(state=state)
            self.radio_Left_Lang_to_Right_Lang.configure(state=state)
            self.radio_Right_Lang_to_Left_Lang.configure(state=state)
            self.radio_mixed.configure(state=state)
            self.clear_button.configure(state=state)

        def disable_all_buttons():
            """Deactivates all buttons and radiobuttons."""
            set_buttons_state("disabled")

        def enable_all_buttons():
            """Activates all buttons and radiobuttons."""
            set_buttons_state("normal")

        def calculate_accuracy(correct, user_input):
            """
            Calculates the accuracy of the user's input compared to the correct answer.

            Args:
                correct (str): The correct answer.
                user_input (str): The user's input.

            Returns:
                float: The accuracy percentage (0 to 100).
            """
            # Convert both strings to lowercase for case-insensitive comparison
            correct = correct.lower()
            user_input = user_input.lower()

            # Determine the minimum length to avoid index errors during comparison
            min_length = min(len(correct), len(user_input))

            # Count the number of matching characters at the same positions
            match_count = sum(1 for i in range(min_length) if correct[i] == user_input[i])

            # Calculate accuracy as a percentage of matching characters in the correct answer
            accuracy = (match_count / len(correct)) * 100 if len(correct) > 0 else 0

            return accuracy

        def show_hint():
            """Reveals the first letters (3) of the correct translation.""" 
            global hint_shown
            if not hint_shown:
                if mode == "Left_Lang_to_Right_Lang":
                    hint = selected_word["Right_Lang"][:3] + "..."
                else:
                    hint = selected_word["Left_Lang"][:3] + "..."
                self.result_label.configure(text=f"{t_path('main_window.result_label.hint_text')} {hint}")
                hint_shown = True

        def check_answer():
            """Checks the correctness of the entered translation.""" 
            if not selected_word:
                self.result_label.configure(text=t_path('main_window.result_label.No_words'))
                return
            user_translation = self.entry.get()
            if mode == "Left_Lang_to_Right_Lang":
                correct = selected_word["Right_Lang"]
            else:
                correct = selected_word["Left_Lang"]
            
            accuracy = calculate_accuracy(correct, user_translation)
            self.result_label.configure(text=f"{t_path('main_window.result_label.percent')} {accuracy:.2f}%\n{t_path('main_window.result_label.correct')} {correct}")

        def skip_word():
            """Skips the current word and moves on to the next one.""" 
            pick_new_word()

        def set_mode(new_mode):
            """Changes the application mode.""" 
            global mode
            mode = new_mode
            pick_new_word()

        def open_file_dialog():
            """Opens the file explorer and loads the selected file."""
            global words
            file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
            if file_path:
                words = load_words_from_file(file_path)
                if words:
                    enable_all_buttons()
                    clear_blocked_lines()
                    pick_new_word()
                else:
                    # Plik jest pusty lub niewłaściwy!
                    self.question_label.configure(text=t_path("main_window.question_label.File_error"))
                    disable_all_buttons()


        def toggle_block_repeated():
            """Enables or disables the blocking of repeated questions."""
            if self.block_repeated_questions.get():
                print("Blocking repeated questions enabled.")
            else:
                print("Blocking repeated questions disabled.")

        def clear_blocked_lines():
            """Clears the list of blocked line numbers."""
            global blocked_lines
            print(f"Blocked lines: {blocked_lines}")
            blocked_lines.clear()
            print("Block list cleared.")

            skip_word()
            if not available_words:
                print("N/A")
                return
        
            self.check_button.configure(state="normal")
            self.hint_button.configure(state="normal")


        # ==========================================================================
        # UI

        ctk.set_appearance_mode(APP_SETTINGS["appearance_mode"])
        try:
            ctk.set_default_color_theme(APP_SETTINGS["color_theme"])
        except:
            print(f"[ERROR]: Color theme {APP_SETTINGS['color_theme']} not found. Using default theme.")
            ctk.set_default_color_theme("blue")

        self.root = root
        self.root.title(APP_SETTINGS["title"])
        self.root.geometry(APP_SETTINGS["window_size"])
        self.root.resizable(*APP_SETTINGS["resizable"])

        # Binding keyboard events to functions
        self.root.bind("<Return>", lambda event: check_answer()) # Enter key
        self.root.bind("<Right>", lambda event: skip_word()) # Right arrow key
        self.root.bind("<Control-c>", lambda event: clear_blocked_lines()) # C key
        self.root.bind("<Control-o>", lambda event: open_file_dialog()) # O key

        # Better scaling of UI elements
        change_ui_scale()

        # Setting the app icon
        if APP_SETTINGS["SetIcon"]:
            set_window_icon(self)

        self.menu = CTkMenuBar(root, padx=0)

        # Sekcja File
        file_button = self.menu.add_cascade(t_path("menubar.file.file"))
        file_dropdown = CustomDropdownMenu(widget=file_button)
        file_dropdown.add_option(option=t_path("menubar.file.load_file"), command=lambda: open_file_dialog())
        file_dropdown.add_option(option=t_path('main_window.buttons.clear_button'), command=lambda: clear_blocked_lines())
        file_dropdown.add_separator()
        file_dropdown.add_option(option=t_path("menubar.file.exit"), command=lambda: self.root.quit())

        # Sekcja Appearance
        appearance_button = self.menu.add_cascade(t_path("menubar.appearance.appearance"))
        appearance_dropdown = CustomDropdownMenu(widget=appearance_button)
        appearance_dropdown.add_option(option=t_path("menubar.appearance.dark_mode"), command=lambda: set_app_appearance_mode("Dark"))
        appearance_dropdown.add_option(option=t_path("menubar.appearance.light_mode"), command=lambda: set_app_appearance_mode("Light"))
        appearance_dropdown.add_separator()
        appearance_dropdown.add_option(option=t_path("menubar.appearance.zoom_in"), command=lambda: change_ui_scale(0.1))
        appearance_dropdown.add_option(option=t_path("menubar.appearance.zoom_out"), command=lambda: change_ui_scale(-0.1))

        # Sekcja About
        about_button = self.menu.add_cascade(t_path("menubar.about.about"))
        about_dropdown = CustomDropdownMenu(widget=about_button)
        about_dropdown.add_option(option=t_path("menubar.about.about_this_app"), command=lambda: AboutWindow(root))
        about_dropdown.add_separator()
        about_dropdown.add_option(option=t_path("menubar.about.get_program_path_debug"), command=lambda: get_program_path(show_messagebox=True))
        about_dropdown.add_option(option=t_path("menubar.about.get_cache_info"), command=lambda: get_cache_info())

        # Main Frame
        self.main_frame = ctk.CTkFrame(
            root, 
            border_width=1,
        )
        self.main_frame.pack_propagate(False)
        self.main_frame.pack(padx=(5), pady=(5,5), fill="both", expand=True)

        # Question Label
        self.question_label = ctk.CTkLabel(
            self.main_frame,
            # Załaduj plik, aby rozpocząć
            text=t_path("main_window.question_label.default"),
            font=("Arial", 20, "bold"),
            )
        self.question_label.pack(pady=10)

        # Line information label
        self.line_info_label = ctk.CTkLabel(
            self.main_frame, 
            text=t_path("main_window.line_info_label"), # Dane pobrane z linijki:
            font=("Arial", 14)
            )
        self.line_info_label.pack(pady=0)

        # Field to enter the translation
        self.entry = ctk.CTkEntry(
            self.main_frame, 
            placeholder_text=t_path("main_window.entry_placeholder"), # Wpisz tutaj tłumaczenie
            font=("Arial", 16), 
            width=360
            )
        self.entry.pack(pady=(10, 10))

        # Frame for buttons
        self.button_frame = ctk.CTkFrame(
            self.main_frame,
            border_width=1,)
        self.button_frame.pack(pady=(10, 10))

        # Button to reveal hints
        self.hint_button = ctk.CTkButton(
            self.button_frame,
            text=t_path("main_window.buttons.hint_button"), # Ujawnij pierwsze litery
            font=("Arial", 16),
            command=lambda: show_hint(),
            state="disabled"
            )
        self.hint_button.pack(side="left", padx=(5,5), pady=(5,5))

        # Button to check answers
        self.check_button = ctk.CTkButton(
            self.button_frame, 
            text=t_path("main_window.buttons.check_button"), # Sprawdź
            font=("Arial", 16),
            command=lambda: check_answer(),
            state="disabled"
            )
        self.check_button.pack(side="left", padx=(0,0), pady=(5,5))

        # Button to skip a word
        self.skip_button = ctk.CTkButton(
            self.button_frame,
            text=t_path("main_window.buttons.skip_button"), # Pomiń/Przejdź dalej
            font=("Arial", 16),
            command=lambda: skip_word(),
            state="disabled"
            )
        self.skip_button.pack(side="left", padx=(5,5), pady=(5,5))

        self.mode_label = ctk.CTkLabel(
            self.main_frame,
            text=t_path("main_window.mode_label"), # Wybierz tryb tłumaczenia:
            font=("Arial", 17)
            )
        self.mode_label.pack(pady=(5, 0))

        # frame for radiobuttons
        self.radio_frame = ctk.CTkFrame(self.main_frame, border_width=1,)
        self.radio_frame.pack(pady=5)

        self.mode_var = ctk.StringVar(value="mixed")

        self.radio_Left_Lang_to_Right_Lang = ctk.CTkRadioButton(
            self.radio_frame,
            text=f"{t_path('main_window.Radiobuttons.left')} ► {t_path('main_window.Radiobuttons.right')}", # Lewy ► Prawy
            font=("Arial", 13),
            variable=self.mode_var,
            value="Left_Lang_to_Right_Lang",
            command=lambda: set_mode(self.mode_var.get()),
            state="disabled"
            )
        self.radio_Left_Lang_to_Right_Lang.pack(side="left", padx=(10,5), pady=(10,10))

        self.radio_Right_Lang_to_Left_Lang = ctk.CTkRadioButton(
            self.radio_frame,
            text=f"{t_path('main_window.Radiobuttons.right')} ► {t_path('main_window.Radiobuttons.left')}",
            font=("Arial", 13),
            variable=self.mode_var,
            value="Right_Lang_to_Left_Lang",
            command=lambda: set_mode(self.mode_var.get()),
            state="disabled"
            )
        self.radio_Right_Lang_to_Left_Lang.pack(side="left", padx=(5,5), pady=(10,10))

        self.radio_mixed = ctk.CTkRadioButton(
            self.radio_frame,
            text=f"{t_path('main_window.Radiobuttons.both')}", # mixed
            font=("Arial", 13),
            variable=self.mode_var,
            value="mixed",
            command=lambda: set_mode(self.mode_var.get()),
            state="disabled"
            )
        self.radio_mixed.pack(side="left", padx=(5,10), pady=(10,10))

        # flag
        self.block_repeated_questions = ctk.BooleanVar(value=False)

        # frame for buttons and checkbox
        self.button_frame2 = ctk.CTkFrame(self.main_frame, border_width=1)
        self.button_frame2.pack(pady=(5,5))

        # button to load a file
        self.file_button = ctk.CTkButton(
            self.button_frame2,
            text=t_path('main_window.buttons.file_button'), # "Załaduj plik .txt"
            command=lambda: open_file_dialog()
        )
        self.file_button.grid(row=0, column=0, padx=(5,3), pady=5, sticky="w")

        # Buton to clear the block list
        self.clear_button = ctk.CTkButton(
            self.button_frame2,
            text=t_path('main_window.buttons.clear_button'), # "Wyczyść listę blokady",
            command=lambda: clear_blocked_lines(),
            state="disabled"
        )
        self.clear_button.grid(row=0, column=1, padx=(0,5), pady=5, sticky="e")

        # Checkbox to block repeated questions
        self.checkbox = ctk.CTkCheckBox(
            self.button_frame2,
            text=t_path('main_window.checkbox.block_list'), # Blokuj powtarzające się pytania
            variable=self.block_repeated_questions,
            command=lambda: toggle_block_repeated()
        )
        self.checkbox.grid(row=1, column=0, columnspan=2, pady=4)

        # Result label
        self.result_label = ctk.CTkLabel(
            self.main_frame,
            text=t_path('main_window.result_label.default'),
            font=("Arial", 19))
        self.result_label.pack(pady=(15,0))

class AboutWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title(t_path("about_window.about_window_title"))
        self.geometry("495x340")
        self.resizable(True, True)

        # Main container
        self.main_container = ctk.CTkFrame(
            self, 
            border_width=1,
        )
        self.main_container.pack(padx=5, pady=5, fill="both", expand=True)
        self.main_container.pack_propagate(False)
        
        # Content frame with two columns
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Left side: logo/image
        self.left_panel = ctk.CTkFrame(self.content_frame, width=150, height=250, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, padx=(0, 15), pady=10, sticky="nsew")
        
        try:
            app_icon_path = "Assets/Vocabulary-Practice-App/Icons/book_pink.png"
            app_icon_image = Image.open(app_icon_path)
            
            self.app_icon = ctk.CTkImage(
                light_image=app_icon_image,
                dark_image=app_icon_image,
                size=(110, 110)
            )
            
            self.icon_label = ctk.CTkLabel(self.left_panel, image=self.app_icon, text="")
            self.icon_label.pack(pady=10)
            
        except Exception as e:
            print(f"Image loading error: {e}")
            self.icon_label = ctk.CTkLabel(
                self.left_panel, 
                text="Logo", 
                width=150, 
                height=150, 
                corner_radius=10, 
                fg_color="#f0f0f0", 
                text_color="#333"
            )
            self.icon_label.pack(pady=10)

        # GitHub icon and link

        self.github_profile_label = self._create_clickable_link(
            " Nieznany237", 
            "https://github.com/Nieznany237"
        )

        self.github_repo_label = self._create_clickable_link(
            " GitHub Repository", 
            "https://github.com/Nieznany237/Vocabulary-Practice-App"
        )
        '''
        self.other_link_label = self._create_clickable_link(
            " Placeholder", 
            "https://example.com",
            "OtherIconLight.png",  # Ścieżki do alternatywnych ikon
            "OtherIconDark.png"
        )
        '''
        # Right side: information
        self.right_panel = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.right_panel.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="nsew")
        
        # Header
        self.title_label = ctk.CTkLabel(
            self.right_panel, 
            text=APP_SETTINGS["title"], 
            font=("Arial", 18, "bold")
        )
        self.title_label.pack(pady=(0, 0), anchor="w")
        
        # Program information
        program_info = f"""
        {t_path("about_window.program_info_description.program_name")}: {APP_SETTINGS["title"]}
        {t_path("about_window.program_info_description.version")}: {APP_VERSION["version"]}
        {t_path("about_window.program_info_description.author")}: Niez | Nieznany237
        {t_path("about_window.program_info_description.release_date")}: {APP_VERSION["release_date"]}
        {t_path("about_window.program_info_description.first_release")}: 19.11.2024
        {t_path("about_window.program_info_description.licence")}: MIT
        
        Python: {self.get_python_version()}
        System: {self.get_system_info()}
        
        {t_path("about_window.program_info_description.description")}:
        A simple and effective app for practicing
        vocabulary in two languages
        using custom word lists.
        """
        self.info_label = ctk.CTkLabel(
            self.right_panel, 
            font=("Arial", 14),
            text=program_info,  
            justify="left")
        self.info_label.pack(pady=(0,0), anchor="w")
    
    def get_system_info(self):
        """Returns operating system information with try-except protection"""
        try:
            system = platform.system()
            version = ""
            if system == "Windows":
                version = platform.win32_ver()[1]
            elif system == "Linux":
                try:
                    # For newer Linux systems
                    version = platform.freedesktop_os_release().get('PRETTY_NAME', 'Linux')
                except:
                    # Fallback for older systems
                    version = platform.linux_distribution()[0] or 'Linux'
            elif system == "Darwin":
                version = f"macOS {platform.mac_ver()[0]}"
            else:
                version = ""
                
            return f"{system} {version}".strip()
            
        except Exception as e:
            print(f"Error getting system information: {e}")
            return platform.system() or "Unknown system"
    
    def get_python_version(self):
        """Returns Python version with try-except protection"""
        try:
            return sys.version.split()[0]
        except Exception as e:
            print(f"Error getting Python version: {e}")
            return "Unknown Python version"
    
    def _create_clickable_link(self, text, url, icon_light_path="Assets/Vocabulary-Practice-App/Icons/GitHubV2Dark.png", icon_dark_path="Assets/Vocabulary-Practice-App/Icons/GitHubV2White.png"):
        """Helper function to create clickable link label with optional icon"""
        try:
            icon_light = Image.open(icon_light_path)
            icon_dark = Image.open(icon_dark_path)
            icon = ctk.CTkImage(
                light_image=icon_light,
                dark_image=icon_dark,
                size=(22, 22)
            )
            
            label = ctk.CTkLabel(
                self.left_panel,
                text=text,
                font=("Arial", 13, "bold"),
                image=icon,
                compound="left",
                cursor="hand2",
                text_color=("#E60000", "#db143c")
                #("#1a73e8", "#8ab4f8") # Legacy
            )
        except Exception as e:
            print(f"Icon loading error: {e}")
            label = ctk.CTkLabel(
                self.left_panel,
                text=text,
                font=("Arial", 13),
                cursor="hand2",
                text_color=("#E60000","#db143c")
            )
    
        label.pack(padx=(0, 0), pady=(0, 0), anchor="w")
        label.bind("<Button-1>", lambda e: webbrowser.open_new_tab(url))
        return label

root = ctk.CTk()
app = MainApp(root)
root.mainloop()