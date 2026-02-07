"""
Context Selection Window for Vocabulary Practice App.

Allows users to select which contexts/sections to practice.
"""
import customtkinter as ctk
from typing import Callable, Dict, List, Optional

class ContextSelectionWindow(ctk.CTkToplevel):
    def __init__(
        self, 
        master, 
        contexts_with_counts: Dict[Optional[str], int],
        selected_contexts: set,
        on_apply: Optional[Callable] = None,
        t_path: Optional[Callable] = None
    ):
        """
        Initialize the Context Selection Window.
        
        Args:
            master: Parent window
            contexts_with_counts: Dict mapping context names (or None) to entry counts
            selected_contexts: Set of currently selected contexts
            on_apply: Callback function when Apply is clicked
            t_path: Translation path function
        """
        super().__init__(master)
        self.title("Context Selection")
        self.geometry("500x600")
        self.resizable(True, True)
        
        # Callback function
        self.on_apply = on_apply
        self.t_path = t_path if t_path else lambda x: x
        
        # Store context data
        self.contexts_with_counts = contexts_with_counts
        self.selected_contexts = set(selected_contexts)  # Create a copy
        self.checkbox_vars: Dict[Optional[str], ctk.BooleanVar] = {}
        self.checkboxes: Dict[Optional[str], ctk.CTkCheckBox] = {}
        
        # Create UI
        self._create_widgets()
        
        # Make window modal
        self.transient(master)
        self.grab_set()
        
    def _create_widgets(self) -> None:
        """Create all UI widgets."""
        # Main container
        self.main_container = ctk.CTkFrame(self, border_width=1)
        self.main_container.pack(padx=5, pady=5, fill="both", expand=True)
        self.main_container.pack_propagate(False)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.main_container,
            text="Select Contexts for Learning",
            font=("Arial", 16, "bold")
        )
        self.title_label.pack(pady=(10, 5), padx=10)
        
        # Info label
        self.info_label = ctk.CTkLabel(
            self.main_container,
            text="Choose which sections/contexts you want to practice:",
            font=("Arial", 12),
            text_color="gray"
        )
        self.info_label.pack(pady=(0, 10), padx=10)
        
        # Mode selection frame
        self.mode_frame = ctk.CTkFrame(self.main_container)
        self.mode_frame.pack(pady=(5, 10), padx=10, fill="x")
        
        self.mode_label = ctk.CTkLabel(
            self.mode_frame,
            text="Selection Mode:",
            font=("Arial", 12, "bold")
        )
        self.mode_label.pack(side="left", padx=(0, 10))
        
        self.mode_var = ctk.StringVar(value="selected")
        self.mode_menu = ctk.CTkOptionMenu(
            self.mode_frame,
            values=["Everything", "Selected"],
            variable=self.mode_var,
            command=self._on_mode_changed
        )
        self.mode_menu.pack(side="left", fill="x", expand=True)
        
        # Contexts list frame with scrollbar
        self.list_container = ctk.CTkFrame(self.main_container)
        self.list_container.pack(pady=5, padx=10, fill="both", expand=True)
        
        # Create scrollable frame
        self.scrollable_frame = ctk.CTkScrollableFrame(self.list_container)
        self.scrollable_frame.pack(fill="both", expand=True)
        
        # Populate contexts
        if not self.contexts_with_counts:
            self.no_contexts_label = ctk.CTkLabel(
                self.scrollable_frame,
                text="No contexts found in loaded file.",
                font=("Arial", 12),
                text_color="gray"
            )
            self.no_contexts_label.pack(pady=20)
        else:
            self._create_context_checkboxes()
        
        # Separator
        self.separator = ctk.CTkFrame(self.main_container, height=2, fg_color="gray")
        self.separator.pack(pady=(10, 0), padx=10, fill="x")
        
        # Button frame
        self.button_frame = ctk.CTkFrame(self.main_container)
        self.button_frame.pack(pady=(10, 10), padx=10, fill="x")
        
        self.apply_button = ctk.CTkButton(
            self.button_frame,
            text="Apply",
            command=self._on_apply
        )
        self.apply_button.pack(side="right", padx=(5, 0))
        
        self.cancel_button = ctk.CTkButton(
            self.button_frame,
            text="Cancel",
            command=self.destroy
        )
        self.cancel_button.pack(side="right", padx=(0, 5))
        
        # Select all / Deselect all frame
        self.quick_select_frame = ctk.CTkFrame(self.button_frame)
        self.quick_select_frame.pack(side="left", fill="x", expand=True)
        
        self.select_all_button = ctk.CTkButton(
            self.quick_select_frame,
            text="Select All",
            command=self._select_all,
            width=80,
            fg_color="green"
        )
        self.select_all_button.pack(side="left", padx=(0, 5))
        
        self.deselect_all_button = ctk.CTkButton(
            self.quick_select_frame,
            text="Deselect All",
            command=self._deselect_all,
            width=80,
            fg_color="red"
        )
        self.deselect_all_button.pack(side="left", padx=(0, 5))
        
        # Update mode visibility
        self._update_mode_visibility()
    
    def _create_context_checkboxes(self) -> None:
        """Create checkboxes for each context."""
        for context, count in self.contexts_with_counts.items():
            context_name = context if context else "[No Context]"
            
            # Create frame for context item
            item_frame = ctk.CTkFrame(self.scrollable_frame)
            item_frame.pack(fill="x", pady=5, padx=5)
            
            # Create checkbox variable
            var = ctk.BooleanVar(value=(context in self.selected_contexts))
            self.checkbox_vars[context] = var
            
            # Create checkbox with label
            checkbox = ctk.CTkCheckBox(
                item_frame,
                text=f"{context_name}  ({count} entries)",
                variable=var,
                font=("Arial", 12)
            )
            checkbox.pack(side="left", fill="x", expand=True)
            self.checkboxes[context] = checkbox
    
    def _on_mode_changed(self, mode: str) -> None:
        """Handle mode selection change."""
        self._update_mode_visibility()
    
    def _update_mode_visibility(self) -> None:
        """Update checkbox visibility based on mode."""
        mode = self.mode_var.get()
        
        if mode == "Everything":
            # Disable all checkboxes
            for checkbox in self.checkboxes.values():
                checkbox.configure(state="disabled")
            self.select_all_button.configure(state="disabled")
            self.deselect_all_button.configure(state="disabled")
        else:
            # Enable all checkboxes
            for checkbox in self.checkboxes.values():
                checkbox.configure(state="normal")
            self.select_all_button.configure(state="normal")
            self.deselect_all_button.configure(state="normal")
    
    def _select_all(self) -> None:
        """Select all contexts."""
        for var in self.checkbox_vars.values():
            var.set(True)
    
    def _deselect_all(self) -> None:
        """Deselect all contexts."""
        for var in self.checkbox_vars.values():
            var.set(False)
    
    def _on_apply(self) -> None:
        """Apply the selected contexts and close the window."""
        mode = self.mode_var.get()
        
        if mode == "Everything":
            # Select all contexts
            selected = set(self.contexts_with_counts.keys())
        else:
            # Get selected contexts from checkboxes
            selected = set()
            for context, var in self.checkbox_vars.items():
                if var.get():
                    selected.add(context)
        
        # Call the callback if provided
        if self.on_apply:
            self.on_apply(selected)
        
        self.destroy()
