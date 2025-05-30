"""
GUI Console Library for CustomTkinter
Version: 1.1.0
Author: Nieznany237
Reusable console output redirection and window for CustomTkinter-based apps.
"""
import sys
import customtkinter as ctk
from modules.utils import set_app_icon 
__version__ = "1.1.0"

class ConsoleRedirector:
    """
    Redirects console output to a CTkTextbox widget in a thread-safe, read-only manner.
    """
    def __init__(self, widget):
        self.widget = widget

    def write(self, text):
        self.widget.configure(state="normal")
        self.widget.insert(ctk.END, text)
        self.widget.see(ctk.END)
        self.widget.configure(state="disabled")

    def flush(self):
        pass  # For compatibility

class GUIConsole:
    """
    GUI Console window for redirecting stdout/stderr to a CustomTkinter Textbox.
    * Usage: 
    *     gui_console = GUIConsole(parent)
    *     gui_console.open()
    """
    def __init__(self, root, APP_SETTINGS ,title="Console Output", width=600, height=400, font=("Cascadia Code", 12)):
        self.root = root
        self.title = title
        self.APP_SETTINGS = APP_SETTINGS
        self.width = width
        self.height = height
        self.font = font
        self.console_window = None
        self.console_textbox = None
        self._stdout_backup = sys.stdout
        self._stderr_backup = sys.stderr

    def set_icon(self, app_settings):
        """Set AboutWindow icon with Windows workaround (uses set_app_icon from utils if available)."""
        if app_settings.get("SetIcon", False):
            try:
                from modules.utils import set_app_icon
                set_app_icon(self.console_window)
            except Exception as e:
                print(f"[AboutWindow] set_app_icon failed: {e}")

    def open(self):
        if self.console_window is not None and self.console_window.winfo_exists():
            self.console_window.focus()
            print("Console window already open.")
            return
        else:
            print("Opening console window... All event output will be redirected here.")

        self.console_window = ctk.CTkToplevel(self.root)
        self.console_window.title(self.title)
        self.console_window.geometry(f"{self.width}x{self.height}")
        
        self.console_frame = ctk.CTkFrame(self.console_window)
        self.console_frame.pack(padx=5, pady=5, fill="both", expand=True)

        self.clear_console_button = ctk.CTkButton(
            self.console_frame,
            text="Clear",
            command=self.clear,
            width=60,
        )
        self.clear_console_button.pack(padx=2, pady=(2, 0), anchor="ne")

        self.console_textbox = ctk.CTkTextbox(
            master=self.console_frame,
            width=self.width-20,
            height=self.height-50,
            border_width=1,
            wrap=ctk.WORD,
            state="disabled",
        )
        self.console_textbox.pack(padx=2, pady=2, fill="both", expand=True)
        self.console_textbox.configure(font=self.font)

        sys.stdout = ConsoleRedirector(self.console_textbox)
        sys.stderr = ConsoleRedirector(self.console_textbox)
        print("Caution: When big files are loaded, the console may freeze for a moment.")
        print("Console output redirected to the console window.")

        self.console_window.protocol("WM_DELETE_WINDOW", self.close)
        self.set_icon(self.APP_SETTINGS)

    def clear(self):
        if self.console_textbox is not None:
            self.console_textbox.configure(state="normal")
            self.console_textbox.delete("1.0", ctk.END)
            self.console_textbox.configure(state="disabled")

    def revert(self):
        try:
            sys.stdout = self._stdout_backup
            sys.stderr = self._stderr_backup
            print("Console output reverted to original stdout and stderr.")
        except Exception as e:
            print(f"[ERROR] Failed to revert console output: {e}")

    def close(self):
        try:
            self.revert()
            if self.console_window is not None:
                self.console_window.destroy()
            print("Console closed..")
        except Exception as e:
            print(f"[ERROR] Failed to close console window: {e}")
