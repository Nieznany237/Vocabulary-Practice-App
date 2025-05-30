import customtkinter as ctk
from CTkMenuBar import *
from PIL import Image
import random
from tkinter import filedialog
import sys
import webbrowser
import platform
import difflib

from modules.translation_utils import t_path, load_translations
import modules.translation_utils
from modules.utils import get_program_path, load_settings_from_json, set_app_icon
from modules.gui_console import GUIConsole

# temp
from pprint import pprint
REQUIRED_JSON_VERSION = 1
# Application version and release date
APP_VERSION = {
    "version": "1.4.0-DEV",
    "release_date": "30.05.2025"
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
vocab_word_list = []
selected_word = None  # Initialize selected_word as None
selected_mode = "mixed"  # Initialize mode with a default value
hint_shown = False  # Initialize hint_shown as False

available_words = ""  # Initialize available_words as an empty string

JSON_Loaded_flag = "False - Unknown"  # Flag to check if JSON settings were loaded successfully

# Lista blokowanych numerów linii
blocked_lines = set()

def change_ui_scale(scale=0):
    MIN_ZOOM = 0.6
    MAX_ZOOM = 3.0
    new_zoom = round(APP_SETTINGS["ui_zoom_factor"] + scale, 3)
    if new_zoom < MIN_ZOOM:
        print(f"[WARNING] UI zoom factor too small: {new_zoom} (min: {MIN_ZOOM})")
        return
    if new_zoom > MAX_ZOOM:
        print(f"[WARNING] UI zoom factor too large: {new_zoom} (max: {MAX_ZOOM})")
        return
    APP_SETTINGS["ui_zoom_factor"] = new_zoom
    print(f"UI zoom factor: {APP_SETTINGS['ui_zoom_factor']}")
    ctk.set_window_scaling(APP_SETTINGS["ui_zoom_factor"])
    ctk.set_widget_scaling(APP_SETTINGS["ui_zoom_factor"])

# Loading settings from JSON file
temp_status, _ = load_settings_from_json(
    file_path=RESOURCE_FILE_PATHS["json_config"],
    target_dict=APP_SETTINGS,
    version_key="VERSION",
    required_version=REQUIRED_JSON_VERSION,
    ignore_version_error_key="IGNORE_VERSION_ERROR",
    settings_key="APP_SETTINGS",
    show_errors=True
)
JSON_Loaded_flag = temp_status

TRANSLATIONS = load_translations(APP_SETTINGS.get("Language", "en"))
modules.translation_utils.TRANSLATIONS = TRANSLATIONS

# ==========================================================================
# Debugging functions

get_program_path(show_messagebox=False, status_flag=JSON_Loaded_flag)

def pprint_list_of_dicts(list_of_dicts, width=130):
    try:
        pprint(list_of_dicts, width=width)
    except Exception as e:
        print(f"[ERROR] Failed to pretty-print list of dictionaries: {e}")
def get_cache_info():
    print(t_path.cache_info())

def print_status():
    print("\n=== Debug: Vocabulary Status ===")
    print(f"\nLoaded words: {len(vocab_word_list)}")
    print(f"Selected word: {selected_word}")
    print(f"Selected mode: {selected_mode}")
    print(f"Hint shown: {hint_shown}")
    print(f"Available words: {len(available_words)}")
    print(f"Blocked lines: {blocked_lines}\n")

    pprint_list_of_dicts(available_words, width=130)
    print("\n=== Debug: Vocabulary Status ===\n")

class MainApp():
    def __init__(self, root):
        # ==========================================================================
        self.gui_console = GUIConsole(root)

        def open_console(self):
            self.gui_console.open()
        # ==========================================================================

        def load_words_from_file(file_path=None):
            """
            Reads a vocabulary file and returns a list of word pairs, ignoring the first line.
            Each line after the first is expected to be in the format "Left_Lang - Right_Lang".
            Lines where the left and right words are identical are skipped.
            Args:
                file_path (str, optional): Path to the vocabulary file. Defaults to None.
            Returns:
                list[dict]: A list of dictionaries, each containing:
                    - "Left_Lang": The word in the left language.
                    - "Right_Lang": The word in the right language.
                    - "line_number": The line number in the file (starting from 2).
            """
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
                pprint_list_of_dicts(words_list, width=130)
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
            """
            Selects a new word for the vocabulary practice session according to the current mode and blocklist settings.
            This function:
            - Checks if any words are loaded; if not, updates the UI to indicate this and returns.
            - Resets the hint display state.
            - Filters available words based on whether repeated questions are blocked.
            - If no words are available after filtering, updates the UI and disables relevant buttons.
            - Randomly selects a word from the available pool.
            - If blocking repeated questions, adds the selected word's line number to the blocklist.
            - Determines the question text based on the current mode (left-to-right, right-to-left, or mixed).
            - Updates the UI with the new question, line info, and resets input/result fields.
            """
            global selected_word, selected_mode, current_mode, hint_shown, available_words
            if not vocab_word_list:
                # Brak załadowanych słówek!
                self.question_label.configure(text=t_path("main_window.question_label.Not_loaded"))
                return

            hint_shown = False

            # Filter words by blocklist
            available_words = vocab_word_list if not self.block_repeated_questions.get() else [
                word for word in vocab_word_list if word["line_number"] not in blocked_lines
            ]

            if not available_words:
                # Brak dostępnych słówek do wyświetlenia!
                self.question_label.configure(text=t_path("main_window.question_label.No_words"))

                self.check_button.configure(state="disabled")
                self.hint_button.configure(state="disabled")
                self.skip_button.configure(state="disabled")
                return

            selected_word = random.choice(available_words)

            # Dodaj numer linii do blokady
            if self.block_repeated_questions.get():
                blocked_lines.add(selected_word["line_number"])

            question_text = selected_word["Left_Lang"] if selected_mode == "Left_Lang_to_Right_Lang" else selected_word["Right_Lang"]

            # Always pick a random direction if mode is "mixed"
            current_mode = selected_mode
            if selected_mode == "mixed":
                current_mode = random.choice(["Left_Lang_to_Right_Lang", "Right_Lang_to_Left_Lang"])
            question_text = selected_word["Left_Lang"] if current_mode == "Left_Lang_to_Right_Lang" else selected_word["Right_Lang"]

            print("\n=== Next word selected ===")
            print(f"Selected word: {selected_word['Left_Lang']} - {selected_word['Right_Lang']}")
            print("Showing question:", question_text)
            print(f"Line number: {selected_word['line_number']}")
            print(f"Mode: {current_mode}")

            # Podaj tłumaczenie słowa:
            self.question_label.configure(text=f"{t_path('main_window.question_label.TranslateIt')} {question_text}")
            self.line_info_label.configure(text=f"{t_path('main_window.line_info_label')} {selected_word['line_number']}", text_color="gray")
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
            self.entry.configure(state=state)

            # MenuBar
            file_clear_blocklist_option.configure(state=state)

        def disable_all_buttons():
            """Deactivates all buttons and radiobuttons."""
            set_buttons_state("disabled")

        def enable_all_buttons():
            """Activates all buttons and radiobuttons."""
            set_buttons_state("normal")
        
        def calculate_accuracy(correct_answer, user_input):
            """
            Calculates the percentage match between the correct answer and the user's answer.
            """
            correct_answer = correct_answer.lower()
            user_input = user_input.lower()
            
            ratio = difflib.SequenceMatcher(None, correct_answer, user_input).ratio()
            return ratio * 100

        def show_hint():
            """Reveals the first letters (3) of the correct translation.""" 
            global hint_shown
            if not hint_shown:
                if current_mode == "Left_Lang_to_Right_Lang":
                    hint = selected_word["Right_Lang"][:3] + "..."
                else:
                    hint = selected_word["Left_Lang"][:3] + "..."
                self.result_label.configure(text=f"{t_path('main_window.result_label.hint_text')} {hint}")
                hint_shown = True

        def check_answer():
            """Checks the correctness of the entered translation."""
            if not vocab_word_list:
                return print("Action blocked - [CheckAnswer]")
            if not selected_word:
                self.result_label.configure(text=t_path('main_window.result_label.No_words'))
                return
            user_translation = self.entry.get()
            if current_mode == "Left_Lang_to_Right_Lang":
                correct_answer = selected_word["Right_Lang"]
            else:
                correct_answer = selected_word["Left_Lang"]
            
            # Debug
            print("\n=== Checking answer ===")
            print(f"User input: {user_translation}")
            print(f"Correct answer: {correct_answer}")
            print("precentage:", calculate_accuracy(correct_answer, user_translation))
            print(f"Mode: {current_mode}\n")
            

            accuracy = calculate_accuracy(correct_answer, user_translation)
            self.result_label.configure(
                text=f"{t_path('main_window.result_label.percent')} {accuracy:.2f}%\n{t_path('main_window.result_label.correct')} {correct_answer}")

        def skip_word():
            if not vocab_word_list:
                return print("Action blocked - [SkipWord]")
            """Skips the current word and moves on to the next one.""" 
            pick_new_word()

        def set_mode(new_mode):
            """Changes the application mode.""" 
            global selected_mode
            selected_mode = new_mode
            pick_new_word()

        def open_file_dialog():
            """Opens the file explorer and loads the selected file."""
            global vocab_word_list
            file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
            if file_path:
                vocab_word_list = load_words_from_file(file_path)
                if vocab_word_list:
                    enable_all_buttons()
                    clear_blocked_lines()
                    #pick_new_word()
                else:
                    # Plik jest pusty lub niewłaściwy!
                    self.question_label.configure(text=t_path("main_window.question_label.File_error"))
                    print("[open_file_dialog] - File is empty or invalid!")
                    disable_all_buttons()

        def toggle_block_repeated():
            """Enables or disables the blocking of repeated questions."""
            if self.block_repeated_questions.get():
                print("Blocking repeated questions enabled.")
            else:
                print("Blocking repeated questions disabled.")

        def clear_blocked_lines():
            """Clears the list of blocked line numbers."""
            if not vocab_word_list:
                return print("Action blocked - [ClearBlockList]")
            
            global blocked_lines
            print(f"\nBlocked lines: {blocked_lines}")
            blocked_lines.clear()
            print("Block list cleared.")

            skip_word()
            #enable_all_buttons()
            self.check_button.configure(state="normal")
            self.hint_button.configure(state="normal")
            self.skip_button.configure(state="normal")


        # ==========================================================================
        # UI

        def set_app_appearance_mode(theme):
            ctk.set_appearance_mode(theme)

            if APP_SETTINGS["SetIcon"]:
                set_app_icon(self)

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
        self.root.bind("<Control-c>", lambda event: clear_blocked_lines()) # ctrl-C key
        self.root.bind("<Control-o>", lambda event: open_file_dialog()) # ctrl-O key

        # Better scaling of UI elements
        change_ui_scale()

        # Setting the app icon
        if APP_SETTINGS["SetIcon"]:
            set_app_icon(self)

        self.menu = CTkMenuBar(root, padx=0)
        #* https://github.com/Akascape/CTkMenuBar?tab=readme-ov-file#methods-1

        # Sekcja File
        # File menu
        file_button_MenuBar = self.menu.add_cascade(t_path("menubar.file.file"))
        file_dropdown = CustomDropdownMenu(widget=file_button_MenuBar)

        file_load_option = file_dropdown.add_option(option=f"{t_path('menubar.file.load_file'):<26} [Ctrl+O]",command=lambda: open_file_dialog())
        file_clear_blocklist_option = file_dropdown.add_option(option=f"{t_path('main_window.buttons.clear_button'):<25} [Ctrl+C]",command=lambda: clear_blocked_lines(), state="disabled")
        file_dropdown.add_separator()
        file_exit_option = file_dropdown.add_option(option=t_path("menubar.file.exit"),command=lambda: self.root.quit())

        # Appearance menu
        appearance_button_MenuBar = self.menu.add_cascade(t_path("menubar.appearance.appearance"))
        appearance_dropdown = CustomDropdownMenu(widget=appearance_button_MenuBar)

        appearance_dark_mode_option = appearance_dropdown.add_option(option=t_path("menubar.appearance.dark_mode"),command=lambda: set_app_appearance_mode("Dark"))
        appearance_light_mode_option = appearance_dropdown.add_option(option=t_path("menubar.appearance.light_mode"),command=lambda: set_app_appearance_mode("Light"))
        appearance_dropdown.add_separator()
        appearance_zoom_in_option = appearance_dropdown.add_option(option=t_path("menubar.appearance.zoom_in"),command=lambda: change_ui_scale(0.1))
        appearance_zoom_out_option = appearance_dropdown.add_option(option=t_path("menubar.appearance.zoom_out"),command=lambda: change_ui_scale(-0.1))

        # About menu
        about_button_MenuBar = self.menu.add_cascade(t_path("menubar.about.about"))
        about_dropdown = CustomDropdownMenu(widget=about_button_MenuBar)

        about_about_this_app_option = about_dropdown.add_option(option=t_path("menubar.about.about_this_app"),command=lambda: AboutWindow(root))

        # Debug menu
        debug_button_MenuBar = self.menu.add_cascade("Debug")
        debug_dropdown = CustomDropdownMenu(widget=debug_button_MenuBar)

        debug_get_program_path_option = debug_dropdown.add_option(option="Get Program Path",command=lambda: get_program_path(show_messagebox=True))
        debug_get_cache_info_option = debug_dropdown.add_option(option="Print Cache Info",command=lambda: get_cache_info())
        debug_print_status_option = debug_dropdown.add_option(option="Print Vocabulary Status",command=lambda: print_status())
        debug_dropdown.add_separator()
        debug_open_console_option = debug_dropdown.add_option(option="Open Console Output",command=lambda: open_console(self))
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
            corner_radius=8,
            border_width=1,
            placeholder_text=t_path("main_window.entry_placeholder"), # Wpisz tutaj tłumaczenie
            font=("Arial", 16), 
            width=380,
            state="disabled",
            )
        self.entry.pack(pady=(10, 10))

        # Frame for buttons
        self.top_controls_frame = ctk.CTkFrame(
            self.main_frame,
            border_width=1,)
        self.top_controls_frame.pack(pady=(10, 10))

        # Button to reveal hints
        self.hint_button = ctk.CTkButton(
            self.top_controls_frame,
            text=t_path("main_window.buttons.hint_button"), # Ujawnij pierwsze litery
            font=("Arial", 16),
            command=lambda: show_hint(),
            state="disabled"
            )
        self.hint_button.pack(side="left", padx=(5,5), pady=(5,5))

        # Button to check answers
        self.check_button = ctk.CTkButton(
            self.top_controls_frame, 
            text=t_path("main_window.buttons.check_button"), # Sprawdź
            font=("Arial", 16),
            command=lambda: check_answer(),
            state="disabled"
            )
        self.check_button.pack(side="left", padx=(0,0), pady=(5,5))

        # Button to skip a word
        self.skip_button = ctk.CTkButton(
            self.top_controls_frame,
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

        # Radio buttons for translation mode selection
        self.radio_Left_Lang_to_Right_Lang = ctk.CTkRadioButton(
            self.radio_frame,
            border_width_unchecked=3,
            border_width_checked=5,
            text=f"{t_path('main_window.Radiobuttons.left')} ► {t_path('main_window.Radiobuttons.right')}",  # Lewy ► Prawy
            font=("Arial", 13),
            variable=self.mode_var,
            value="Left_Lang_to_Right_Lang",
            command=lambda: set_mode(self.mode_var.get()),
            state="disabled"
        )
        self.radio_Right_Lang_to_Left_Lang = ctk.CTkRadioButton(
            self.radio_frame,
            border_width_unchecked=3,
            border_width_checked=5,
            text=f"{t_path('main_window.Radiobuttons.right')} ► {t_path('main_window.Radiobuttons.left')}", # Prawy ► Lewy
            font=("Arial", 13),
            variable=self.mode_var,
            value="Right_Lang_to_Left_Lang",
            command=lambda: set_mode(self.mode_var.get()),
            state="disabled"
        )
        self.radio_mixed = ctk.CTkRadioButton(
            self.radio_frame,
            width=20,
            border_width_unchecked=3,
            border_width_checked=5,
            text=f"{t_path('main_window.Radiobuttons.both')}",  # mixed
            font=("Arial", 13),
            variable=self.mode_var,
            value="mixed",
            command=lambda: set_mode(self.mode_var.get()),
            state="disabled"
        )

        # Pack radio buttons in order
        self.radio_Left_Lang_to_Right_Lang.pack(side="left", padx=(10, 5), pady=(10, 10))
        self.radio_Right_Lang_to_Left_Lang.pack(side="left", padx=(5, 5), pady=(10, 10))
        self.radio_mixed.pack(side="left", padx=(5, 10), pady=(10, 10))

        # flag
        self.block_repeated_questions = ctk.BooleanVar(value=False)

        # frame for buttons and checkbox
        self.bottom_controls_frame = ctk.CTkFrame(self.main_frame, border_width=1)
        self.bottom_controls_frame.pack(pady=(5,5))

        # button to load a file
        self.file_button = ctk.CTkButton(
            self.bottom_controls_frame,
            text=t_path('main_window.buttons.file_button'), # "Załaduj plik .txt"
            command=lambda: open_file_dialog()
        )
        self.file_button.grid(row=0, column=0, padx=(5,3), pady=5, sticky="w")

        # Buton to clear the block list
        self.clear_button = ctk.CTkButton(
            self.bottom_controls_frame,
            text=t_path('main_window.buttons.clear_button'), # "Wyczyść listę blokady",
            command=lambda: clear_blocked_lines(),
            state="disabled"
        )
        self.clear_button.grid(row=0, column=1, padx=(0,5), pady=5, sticky="e")

        # Checkbox to block repeated questions
        self.checkbox = ctk.CTkCheckBox(
            self.bottom_controls_frame,
            border_width=2,
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
    def set_icon(self):
        """Set AboutWindow icon with Windows workaround (uses set_app_icon from utils)."""
        
        if APP_SETTINGS["SetIcon"]:
            from modules.utils import set_app_icon
            set_app_icon(self)

    def __init__(self, master):
        super().__init__(master)
        self.title(t_path("about_window.about_window_title"))
        self.geometry("495x340")
        self.resizable(True, True)
        self.set_icon()

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