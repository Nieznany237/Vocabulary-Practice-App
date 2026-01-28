import customtkinter as ctk
from CTkMenuBar import *
import random
from tkinter import filedialog
import difflib
from typing import List, Dict, Optional

from modules.translation_utils import t_path, load_translations
import modules.translation_utils
from modules.utils import get_program_path, load_settings_from_json, set_app_icon
from modules.gui_console import GUIConsole
from modules.about_window import AboutWindow

# temp
from pprint import pprint
REQUIRED_JSON_VERSION = 1
# Application version and release date
APP_VERSION = {
    "version": "1.5.0 dev",
    "release_date": "28.01.2026"
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

# Initialize global variables
JSON_Loaded_flag = "False - Unknown"  # Flag to check if JSON settings were loaded successfully

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

class MainApp():
    def __init__(self, root: ctk.CTk):
        # State variables
        self.vocab_word_list: List[Dict[str, str | int]] = []
        self.selected_word: Optional[Dict[str, str | int]] = None
        self.selected_mode: str = "mixed"
        self.hint_shown: bool = False
        self.available_words: List[Dict[str, str | int]] = []
        self.blocked_lines: set[int] = set()
        self.current_mode: str = "mixed"

        # ==========================================================================
        self.gui_console = GUIConsole(root, APP_SETTINGS)

        # ==========================================================================

        self.root = root
        self.root.title(APP_SETTINGS["title"])
        self.root.geometry(APP_SETTINGS["window_size"])
        self.root.resizable(*APP_SETTINGS["resizable"])

        # Binding keyboard events to functions
        self.root.bind("<Return>", lambda event: self.check_answer()) # Enter key
        self.root.bind("<Right>", lambda event: self.skip_word()) # Right arrow key
        self.root.bind("<Control-c>", lambda event: self.clear_blocked_lines()) # ctrl-C key
        self.root.bind("<Control-o>", lambda event: self.open_file_dialog()) # ctrl-O key

        self.change_ui_scale()

        if APP_SETTINGS["SetIcon"]:
            set_app_icon(self)

        self.menu = CTkMenuBar(root, padx=0)
        #* https://github.com/Akascape/CTkMenuBar?tab=readme-ov-file#methods-1

        # Sekcja File
        # File menu
        self.file_button_MenuBar = self.menu.add_cascade(t_path("menubar.file.file"))
        self.file_dropdown = CustomDropdownMenu(widget=self.file_button_MenuBar)

        self.file_load_option = self.file_dropdown.add_option(option=f"{t_path('menubar.file.load_file'):<26} [Ctrl+O]",command=lambda: self.open_file_dialog())
        self.file_clear_blocklist_option = self.file_dropdown.add_option(option=f"{t_path('main_window.buttons.clear_button'):<25} [Ctrl+C]",command=lambda: self.clear_blocked_lines(), state="disabled")
        self.file_dropdown.add_separator()
        self.file_exit_option = self.file_dropdown.add_option(option=t_path("menubar.file.exit"),command=lambda: self.root.quit())

        # Appearance menu
        self.appearance_button_MenuBar = self.menu.add_cascade(t_path("menubar.appearance.appearance"))
        self.appearance_dropdown = CustomDropdownMenu(widget=self.appearance_button_MenuBar)

        self.appearance_dark_mode_option = self.appearance_dropdown.add_option(option=t_path("menubar.appearance.dark_mode"),command=lambda: self.set_app_appearance_mode("Dark"))
        self.appearance_light_mode_option = self.appearance_dropdown.add_option(option=t_path("menubar.appearance.light_mode"),command=lambda: self.set_app_appearance_mode("Light"))
        self.appearance_dropdown.add_separator()
        self.appearance_zoom_in_option = self.appearance_dropdown.add_option(option=t_path("menubar.appearance.zoom_in"),command=lambda: self.change_ui_scale(0.1))
        self.appearance_zoom_out_option = self.appearance_dropdown.add_option(option=t_path("menubar.appearance.zoom_out"),command=lambda: self.change_ui_scale(-0.1))

        # Settings menu
        self.settings_button_MenuBar = self.menu.add_cascade("Settings")
        self.settings_dropdown = CustomDropdownMenu(widget=self.settings_button_MenuBar)

        self.context_enabled = ctk.BooleanVar(value=True)
        self.context_enabled_checkbox = ctk.CTkCheckBox(
            self.settings_dropdown,
            text="Enable Context Display",
            variable=self.context_enabled
        )
        self.context_enabled_checkbox.pack(padx=5, pady=5)

        # About menu
        self.about_button_MenuBar = self.menu.add_cascade(t_path("menubar.about.about"))
        self.about_dropdown = CustomDropdownMenu(widget=self.about_button_MenuBar)

        self.about_about_this_app_option = self.about_dropdown.add_option(option=t_path("menubar.about.about_this_app"),command=lambda: AboutWindow(root, APP_SETTINGS, APP_VERSION, t_path))

        # Debug menu
        self.debug_button_MenuBar = self.menu.add_cascade("Debug")
        self.debug_dropdown = CustomDropdownMenu(widget=self.debug_button_MenuBar)

        self.debug_get_program_path_option = self.debug_dropdown.add_option(option="Get Program Path",command=lambda: get_program_path(show_messagebox=True, status_flag=JSON_Loaded_flag))
        self.debug_get_cache_info_option = self.debug_dropdown.add_option(option="Print Cache Info",command=lambda: self.get_cache_info())
        self.debug_print_status_option = self.debug_dropdown.add_option(option="Print Vocabulary Status",command=lambda: self.print_status())
        self.debug_dropdown.add_separator()
        self.debug_open_console_option = self.debug_dropdown.add_option(option="Open Console Output",command=lambda: self.open_console())

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
        self.question_label.pack(pady=(10, 5))

        # Context label (for group context)
        self.context_label = ctk.CTkLabel(
            self.main_frame,
            text="Context: ",
            font=("Arial", 15, "italic"),
            text_color="#888888"
        )
        self.context_label.pack(pady=(0, 0))

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
            text=t_path("main_window.buttons.hint_button"),
            font=("Arial", 16),
            command=lambda: self.show_hint(),
            state="disabled"
        )
        self.hint_button.pack(side="left", padx=(5,5), pady=(5,5))

        # Button to check answers
        self.check_button = ctk.CTkButton(
            self.top_controls_frame, 
            text=t_path("main_window.buttons.check_button"),
            font=("Arial", 16),
            command=lambda: self.check_answer(),
            state="disabled"
        )
        self.check_button.pack(side="left", padx=(0,0), pady=(5,5))

        # Button to skip a word
        self.skip_button = ctk.CTkButton(
            self.top_controls_frame,
            text=t_path("main_window.buttons.skip_button"),
            font=("Arial", 16),
            command=lambda: self.skip_word(),
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
            text=f"{t_path('main_window.Radiobuttons.left')} ► {t_path('main_window.Radiobuttons.right')}",
            font=("Arial", 13),
            variable=self.mode_var,
            value="Left_Lang_to_Right_Lang",
            command=lambda: self.set_mode(self.mode_var.get()),
            state="disabled"
        )
        self.radio_Right_Lang_to_Left_Lang = ctk.CTkRadioButton(
            self.radio_frame,
            border_width_unchecked=3,
            border_width_checked=5,
            text=f"{t_path('main_window.Radiobuttons.right')} ► {t_path('main_window.Radiobuttons.left')}",
            font=("Arial", 13),
            variable=self.mode_var,
            value="Right_Lang_to_Left_Lang",
            command=lambda: self.set_mode(self.mode_var.get()),
            state="disabled"
        )
        self.radio_mixed = ctk.CTkRadioButton(
            self.radio_frame,
            width=20,
            border_width_unchecked=3,
            border_width_checked=5,
            text=f"{t_path('main_window.Radiobuttons.both')}",
            font=("Arial", 13),
            variable=self.mode_var,
            value="mixed",
            command=lambda: self.set_mode(self.mode_var.get()),
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
            text=t_path('main_window.buttons.file_button'),
            command=lambda: self.open_file_dialog()
        )
        self.file_button.grid(row=0, column=0, padx=(5,3), pady=5, sticky="w")

        # Buton to clear the block list
        self.clear_button = ctk.CTkButton(
            self.bottom_controls_frame,
            text=t_path('main_window.buttons.clear_button'),
            command=lambda: self.clear_blocked_lines(),
            state="disabled"
        )
        self.clear_button.grid(row=0, column=1, padx=(0,5), pady=5, sticky="e")

        # Checkbox to block repeated questions
        self.checkbox = ctk.CTkCheckBox(
            self.bottom_controls_frame,
            border_width=2,
            text=t_path('main_window.checkbox.block_list'),
            variable=self.block_repeated_questions,
            command=lambda: self.toggle_block_repeated()
        )
        self.checkbox.grid(row=1, column=0, columnspan=2, pady=4)

        # Result label
        self.result_label = ctk.CTkLabel(
            self.main_frame,
            text=t_path('main_window.result_label.default'),
            font=("Arial", 19))
        self.result_label.pack(pady=(15,0))

        # Words info label (shows loaded/remaining words)
        self.words_info_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=("Arial", 13, "italic"),
            text_color="gray"
        )
        self.words_info_label.pack(pady=(2, 0))
        
    ctk.set_appearance_mode(APP_SETTINGS["appearance_mode"])
    try:
        ctk.set_default_color_theme(APP_SETTINGS["color_theme"])
    except:
        print(f"[ERROR]: Color theme {APP_SETTINGS['color_theme']} not found. Using default theme.")
        ctk.set_default_color_theme("blue")

    # Debug functions
    def get_cache_info(self) -> None:
        print(t_path.cache_info())

    def print_status(self) -> None:
        print("\n=== Debug: Vocabulary Status ===")
        print(f"\nLoaded words: {len(self.vocab_word_list)}")
        if self.block_repeated_questions.get():
            remaining = len([word for word in self.vocab_word_list if word["line_number"] not in self.blocked_lines])
            print(f"Words remaining (not repeated): {remaining}")
        if hasattr(self, 'failed_lines') and self.failed_lines:
            print(f"Failed to load lines: {self.failed_lines}")
        print(f"Selected word: {self.selected_word}")
        print(f"Selected mode: {self.selected_mode}")
        print(f"Hint shown: {self.hint_shown}")
        print(f"Available words: {len(self.available_words)}")
        print(f"Blocked lines: {self.blocked_lines}\n")
        pprint_list_of_dicts(self.available_words, width=130)
        print("\n=== Debug: Vocabulary Status ===\n")

    def update_words_info_label(self):
        loaded = len(self.vocab_word_list)
        if self.block_repeated_questions.get():
            remaining = len([word for word in self.vocab_word_list if word["line_number"] not in self.blocked_lines])
            self.words_info_label.configure(text=f"Loaded: {loaded} | Remaining: {remaining}")
        else:
            self.words_info_label.configure(text=f"Loaded: {loaded}")

    def open_console(self) -> None:
        self.gui_console.open()

    def load_words_from_file(self, file_path: Optional[str] = None) -> List[Dict[str, str | int]]:
        """
        Reads a vocabulary file and returns a list of word pairs, supporting context grouping.
        Each line after the first is expected to be in the format "Left_Lang - Right_Lang".
        Context is set by lines in the form $ context $ and applies to following words until next context or EOF.
        Lines where the left and right words are identical are skipped.
        Tracks failed lines (bad format, not comment/empty).
        Args:
            file_path (str, optional): Path to the vocabulary file. Defaults to None.
        Returns:
            list[dict]: A list of dictionaries, each containing:
                - "Left_Lang": The word in the left language.
                - "Right_Lang": The word in the right language.
                - "line_number": The line number in the file (starting from 2).
                - "context": The context/group string, or None if not set.
        """
        words_list: List[Dict[str, str | int | None]] = []
        language_names = ("Left", "Right")
        self.failed_lines = []  # Track failed lines for status/debug
        if not file_path:
            self.failed_lines = []
            return words_list

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                # Read the first line for language names
                first_line = file.readline()
                if " - " in first_line:
                    language_names = tuple(first_line.strip().split(" - "))
                # Update radiobutton text immediately
                self.radio_Left_Lang_to_Right_Lang.configure(
                    text = f"{language_names[0]} ► {language_names[1]}"
                )
                self.radio_Right_Lang_to_Left_Lang.configure(
                    text = f"{language_names[1]} ► {language_names[0]}"
                )
                # Read the rest of the file line by line
                current_context = None
                for line_number, line in enumerate(file, start=2):
                    line_strip = line.strip()
                    if not line_strip or line_strip.startswith('#'):
                        continue  # skip comments and empty lines
                    # Detect context line: $ ... $
                    if line_strip.startswith('$') and line_strip.endswith('$') and len(line_strip) > 2:
                        current_context = line_strip[1:-1].strip()
                        continue
                    if " - " in line_strip:
                        try:
                            Left_Lang, Right_Lang = line_strip.split(" - ")
                            if Left_Lang != Right_Lang:
                                # Always assign the current context (even if None)
                                words_list.append({
                                    "Left_Lang": Left_Lang,
                                    "Right_Lang": Right_Lang,
                                    "line_number": line_number,
                                    "context": current_context if current_context is not None else None
                                })
                        except Exception:
                            self.failed_lines.append(line_number)
                    else:
                        self.failed_lines.append(line_number)
        except FileNotFoundError:
            print(f"File {file_path} not found.")
            self.failed_lines = []
        pprint_list_of_dicts(words_list, width=130)
        return words_list

    def get_language_names(self, file_path: Optional[str]) -> tuple[str, str]:
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

    def pick_new_word(self) -> None:
        """
        Selects a new word for the vocabulary practice session according to the current mode and blocklist settings.
        Displays context if available.
        """
        if not self.vocab_word_list:
            # Brak załadowanych słówek!
            self.question_label.configure(text=t_path("main_window.question_label.Not_loaded"))
            self.context_label.configure(text="Context: N/A")
            self.update_words_info_label()
            return

        self.hint_shown = False

        # Filter words by blocklist
        if not self.block_repeated_questions.get():
            self.available_words = self.vocab_word_list
        else:
            self.available_words = [
                word for word in self.vocab_word_list if word["line_number"] not in self.blocked_lines
            ]

        if not self.available_words:
            # Brak dostępnych słówek do wyświetlenia!
            self.question_label.configure(text=t_path("main_window.question_label.No_words"))
            self.context_label.configure(text="")
            self.update_words_info_label()
            self.check_button.configure(state="disabled")
            self.hint_button.configure(state="disabled")
            self.skip_button.configure(state="disabled")
            return

        self.selected_word = random.choice(self.available_words)

        # Dodaj numer linii do blokady
        if self.block_repeated_questions.get():
            self.blocked_lines.add(self.selected_word["line_number"])

        self.update_words_info_label()

        question_text = self.selected_word["Left_Lang"] if self.selected_mode == "Left_Lang_to_Right_Lang" else self.selected_word["Right_Lang"]

        # Always pick a random direction if mode is "mixed"
        self.current_mode = self.selected_mode
        if self.selected_mode == "mixed":
            self.current_mode = random.choice(["Left_Lang_to_Right_Lang", "Right_Lang_to_Left_Lang"])
        question_text = self.selected_word["Left_Lang"] if self.current_mode == "Left_Lang_to_Right_Lang" else self.selected_word["Right_Lang"]

        print("\n=== Next word selected ===")
        print(f"Selected word: {self.selected_word['Left_Lang']} - {self.selected_word['Right_Lang']}")
        print("Showing question:", question_text)
        print(f"Line number: {self.selected_word['line_number']}")
        print(f"Mode: {self.current_mode}")
        print(f"Context: {self.selected_word.get('context')}")

        # Podaj tłumaczenie słowa:
        self.question_label.configure(text=f"{t_path('main_window.question_label.TranslateIt')} {question_text}")
        # Show context if enabled and available
        if hasattr(self, 'context_enabled') and not self.context_enabled.get():
            self.context_label.configure(text="")
        else:
            context = self.selected_word.get('context')
            if context:
                self.context_label.configure(text=f"Context: {context}")
            else:
                self.context_label.configure(text="")
        self.line_info_label.configure(text=f"{t_path('main_window.line_info_label')} {self.selected_word['line_number']}", text_color="gray")
        self.entry.delete(0, ctk.END)
        self.result_label.configure(text="\n")

    def set_buttons_state(self, state: str) -> None:
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
        self.file_clear_blocklist_option.configure(state=state)

    def disable_all_buttons(self) -> None:
        """Deactivates all buttons and radiobuttons."""
        self.set_buttons_state("disabled")

    def enable_all_buttons(self) -> None:
        """Activates all buttons and radiobuttons."""
        self.set_buttons_state("normal")

    def calculate_accuracy(self, correct_answer: str, user_input: str) -> float:
        """
        Calculates the percentage match between the correct answer and the user's answer.
        """
        correct_answer = correct_answer.lower()
        user_input = user_input.lower()
        
        ratio = difflib.SequenceMatcher(None, correct_answer, user_input).ratio()
        return ratio * 100

    def show_hint(self) -> None:
        """Reveals the first letters (3) of the correct translation.""" 
        if not self.hint_shown:
            if self.current_mode == "Left_Lang_to_Right_Lang":
                hint = self.selected_word["Right_Lang"][:3] + "..."
            else:
                hint = self.selected_word["Left_Lang"][:3] + "..."
            self.result_label.configure(text=f"{t_path('main_window.result_label.hint_text')} {hint}")
            self.hint_shown = True

    def check_answer(self) -> None:
        """Checks the correctness of the entered translation."""
        if not self.available_words:
            return print("Action blocked - [CheckAnswer]")
        if not self.selected_word:
            self.result_label.configure(text=t_path('main_window.result_label.No_words'))
            return
        user_translation = self.entry.get()
        if self.current_mode == "Left_Lang_to_Right_Lang":
            correct_answer = self.selected_word["Right_Lang"]
        else:
            correct_answer = self.selected_word["Left_Lang"]
        
        # Debug
        print("\n=== Checking answer ===")
        print(f"User input: {user_translation}")
        print(f"Correct answer: {correct_answer}")
        print("precentage:", self.calculate_accuracy(correct_answer, user_translation))
        print(f"Mode: {self.current_mode}\n")
        

        accuracy = self.calculate_accuracy(correct_answer, user_translation)
        self.result_label.configure(
            text=f"{t_path('main_window.result_label.percent')} {accuracy:.2f}%\n{t_path('main_window.result_label.correct')} {correct_answer}")

    def skip_word(self) -> None:
        if not self.vocab_word_list:
            return print("Action blocked - [SkipWord]")
        """Skips the current word and moves on to the next one.""" 
        self.pick_new_word()

    def set_mode(self, new_mode: str) -> None:
        """Changes the application mode.""" 
        self.selected_mode = new_mode
        self.pick_new_word()

    def open_file_dialog(self) -> None:
        """Opens the file explorer and loads the selected file."""
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            self.vocab_word_list = self.load_words_from_file(file_path)
            self.update_words_info_label()
            if self.vocab_word_list:
                self.enable_all_buttons()
                self.clear_blocked_lines()
            else:
                self.question_label.configure(text=t_path("main_window.question_label.File_error"))
                print("[open_file_dialog] - File is empty or invalid!")
                self.disable_all_buttons()

    def toggle_block_repeated(self) -> None:
        """Enables or disables the blocking of repeated questions."""
        if self.block_repeated_questions.get():
            print("Blocking repeated questions enabled.")
        else:
            print("Blocking repeated questions disabled.")

    def clear_blocked_lines(self) -> None:
        """Clears the list of blocked line numbers."""
        if not self.vocab_word_list:
            return print("Action blocked - [ClearBlockList]")
        
        print(f"\nBlocked lines: {self.blocked_lines}")
        self.blocked_lines.clear()
        print("Block list cleared.")
        self.update_words_info_label()
        self.skip_word()
        self.check_button.configure(state="normal")
        self.hint_button.configure(state="normal")
        self.skip_button.configure(state="normal")

    def change_ui_scale(self, scale: float = 0) -> None:
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

    def set_app_appearance_mode(self, theme: str) -> None:
        ctk.set_appearance_mode(theme)

        if APP_SETTINGS["SetIcon"]:
            set_app_icon(self)

root = ctk.CTk()
app = MainApp(root)
root.mainloop()