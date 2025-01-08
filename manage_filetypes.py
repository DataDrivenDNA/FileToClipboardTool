import tkinter as tk
from tkinter import ttk, messagebox
from typing import Set, Callable
import logging

logger = logging.getLogger(__name__)

class ManageFileTypesUI(tk.Toplevel):
    """
    A separate Toplevel window that allows the user to manage allowed file types.
    The user can add, remove, or reset file types to their default state.
    """

    def __init__(
        self,
        parent: tk.Tk,
        allowed_file_types: Set[str],
        default_file_types: Set[str],
        save_settings_callback: Callable[[], None],
        *args, 
        **kwargs
    ):
        super().__init__(parent, *args, **kwargs)
        self.title("Manage Allowed File Types")

        self.geometry("350x450")
        self.minsize(350, 450)
        self.grab_set()  # Modal

        self.allowed_file_types = allowed_file_types
        self.default_file_types = default_file_types
        self.save_settings_callback = save_settings_callback

        label = ttk.Label(self, text="Allowed File Types:", font=("Segoe UI", 11, "bold"))
        label.pack(pady=10)

        lb_frame = ttk.Frame(self)
        lb_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.listbox = tk.Listbox(lb_frame, selectmode=tk.EXTENDED)
        self.listbox.pack(fill=tk.BOTH, expand=True)

        for ext in sorted(self.allowed_file_types):
            self.listbox.insert(tk.END, ext)

        self.listbox.bind('<Delete>', self.on_listbox_delete)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        remove_btn = ttk.Button(btn_frame, text="Remove Selected", command=self.remove_selected_types)
        remove_btn.pack(side=tk.LEFT, padx=5)

        self.simple_entry = ttk.Entry(btn_frame)
        self.simple_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        add_btn = ttk.Button(btn_frame, text="Add", command=self.add_new_type)
        add_btn.pack(side=tk.LEFT, padx=5)

        reset_btn = ttk.Button(self, text="Reset to Defaults", command=self.reset_defaults)
        reset_btn.pack(pady=(0,10))

        close_btn = ttk.Button(self, text="Close", command=self.on_close)
        close_btn.pack(pady=5)

    def on_listbox_delete(self, event=None):
        """Handle Delete key press inside the listbox."""
        self.remove_selected_types()

    def remove_selected_types(self):
        '''Remove selected file types from the listbox and the allowed_file_types set.'''
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showinfo("Information", "No file types selected.")
            return

        # Remove from listbox in reverse so indexes don't shift
        for idx in reversed(selection):
            ext = self.listbox.get(idx)
            if ext in self.allowed_file_types:
                self.allowed_file_types.remove(ext)
            self.listbox.delete(idx)

        self.save_settings_callback()
        logger.info("Removed selected file types.")

    def add_new_type(self):
        '''Add a new file type to the listbox and the allowed_file_types set.'''
        new_type = self.simple_entry.get().strip().lower()
        if not new_type:
            return
        if not new_type.startswith('.'):
            new_type = '.' + new_type
        if new_type not in self.allowed_file_types:
            self.allowed_file_types.add(new_type)
            self.listbox.insert(tk.END, new_type)
            self.simple_entry.delete(0, tk.END)
            self.save_settings_callback()
            logger.info(f"Added new file type: {new_type}")

    def reset_defaults(self):
        '''Reset the allowed file types to their default state.'''
        self.allowed_file_types.clear()
        self.allowed_file_types.update(self.default_file_types)
        self.listbox.delete(0, tk.END)
        for ext in sorted(self.allowed_file_types):
            self.listbox.insert(tk.END, ext)
        self.save_settings_callback()
        logger.info("Reset file types to default.")

    def on_close(self):
        '''Close the window and save the settings.'''
        self.save_settings_callback()
        self.destroy()
