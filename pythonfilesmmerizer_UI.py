import os
import io
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from typing import List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

class ToolTip:
    """Create a tooltip for a given widget."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        """Display the tooltip."""
        if self.tip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # Remove window decorations
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#FFFFE0", relief=tk.SOLID, borderwidth=1,
                         font=("Segoe UI", 10))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        """Hide the tooltip."""
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

class ScrollableFrame(ttk.Frame):
    """A scrollable frame that can contain multiple widgets."""
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self, borderwidth=0, background="#f0f0f0")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, style="TFrame")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

class PythonFilesSummarizer:
    """A GUI application to summarize Python files and README.md content."""

    def __init__(self, root: TkinterDnD.Tk):
        self.root = root
        self.root.title("Python Files Summarizer")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        self.root.configure(bg="#f0f0f0")

        self.create_widgets()
        self.setup_drag_and_drop()

    def create_widgets(self):
        """Create and arrange widgets in the main window."""
        # Style Configuration
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure("TButton",
                        font=("Segoe UI", 10),
                        padding=6)
        style.configure("TLabel",
                        font=("Segoe UI", 11))
        style.configure("Header.TLabel",
                        font=("Segoe UI", 16, "bold"),
                        background="#f0f0f0")
        style.configure("Status.TLabel",
                        font=("Segoe UI", 10),
                        background="#d9d9d9")
        style.configure("TCheckbutton",
                        font=("Segoe UI", 10))

        # Header Label
        header = ttk.Label(
            self.root,
            text="Python Files Summarizer",
            style="Header.TLabel"
        )
        header.pack(pady=(10, 5), padx=10, anchor="w")

        # Instruction Label
        instruction = ttk.Label(
            self.root,
            text="Drag and drop Python files, folders, or README.md here:",
            style="TLabel"
        )
        instruction.pack(pady=(0, 10), padx=10, anchor="w")

        # Scrollable Frame for File Icons
        self.scrollable_frame = ScrollableFrame(self.root)
        self.scrollable_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Progress Bar
        self.progress = ttk.Progressbar(self.root, orient='horizontal', mode='determinate')
        self.progress.pack(fill=tk.X, padx=10, pady=10)
        self.progress['value'] = 0

        # Frame for Buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        # Copy to Clipboard Button
        self.copy_button = ttk.Button(
            button_frame,
            text=" Copy to Clipboard",
            command=self.copy_to_clipboard
        )
        self.copy_button.pack(side=tk.LEFT, padx=5)
        ToolTip(self.copy_button, "Copy the selected content to clipboard (Ctrl+C)")

        # Remove Selected Button
        self.remove_button = ttk.Button(
            button_frame,
            text=" Remove Selected",
            command=self.remove_selected
        )
        self.remove_button.pack(side=tk.LEFT, padx=5)
        ToolTip(self.remove_button, "Remove selected items from the list (Del)")

        # Clear All Button
        self.clear_button = ttk.Button(
            button_frame,
            text=" Clear All",
            command=self.clear_all
        )
        self.clear_button.pack(side=tk.LEFT, padx=5)
        ToolTip(self.clear_button, "Clear all items from the list (Ctrl+X)")

        # Configure keyboard shortcuts
        self.root.bind('<Control-c>', lambda event: self.copy_to_clipboard())
        self.root.bind('<Delete>', lambda event: self.remove_selected())
        self.root.bind('<Control-x>', lambda event: self.clear_all())

        # Status Label
        self.status_var = tk.StringVar()
        self.status_var.set("Welcome! Drag and drop files to begin.")
        self.status_label = ttk.Label(
            self.root,
            textvariable=self.status_var,
            style="Status.TLabel",
            anchor="w"
        )
        self.status_label.pack(fill=tk.X, padx=10, pady=(0,10))

        # Dictionary to hold file items with their corresponding variables
        self.file_items = {}

    def setup_drag_and_drop(self):
        """Configure drag and drop functionality."""
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.handle_drop)

    def handle_drop(self, event):
        """Handle files/folders dropped into the application."""
        logging.debug(f"Drop event triggered with data: {event.data}")
        paths = self.root.tk.splitlist(event.data)
        added = False
        for path in paths:
            path = path.strip('"')
            if path not in self.file_items:
                self.add_file_item(path)
                added = True
        if added:
            self.status_var.set("Files added successfully.")
            logging.info(f"Added files/folders: {paths}")
        else:
            self.status_var.set("No new files were added.")
        return "break"

    def add_file_item(self, path: str):
        """Add a file or folder item to the scrollable frame."""
        frame = ttk.Frame(self.scrollable_frame.scrollable_frame, padding=5, relief=tk.RIDGE)
        frame.pack(fill=tk.X, padx=5, pady=2)

        # Determine if path is a file or folder
        is_folder = os.path.isdir(path)

        # Emoji Icon
        icon = "📁" if is_folder else "📄"
        icon_label = ttk.Label(frame, text=icon, font=("Segoe UI", 14))
        icon_label.pack(side=tk.LEFT, padx=(0, 10))

        # Checkbox
        var = tk.BooleanVar(value=True)
        check = ttk.Checkbutton(frame, variable=var)
        check.pack(side=tk.LEFT, padx=(0, 10))

        # File/Folder Name
        name = os.path.basename(path) if os.path.isfile(path) else os.path.basename(os.path.normpath(path))
        name_label = ttk.Label(frame, text=name, font=("Segoe UI", 10))
        name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Bind right-click for context menu
        name_label.bind("<Button-3>", lambda e, p=path: self.show_context_menu(e, p))

        # Store in dictionary
        self.file_items[path] = {'var': var, 'frame': frame}

    def show_context_menu(self, event, path):
        """Show a context menu for the given file/folder."""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Remove", command=lambda p=path: self.remove_single(p))
        menu.post(event.x_root, event.y_root)

    def remove_single(self, path: str):
        """Remove a single file/folder item."""
        if path in self.file_items:
            self.file_items[path]['frame'].destroy()
            del self.file_items[path]
            self.status_var.set(f"Removed: {os.path.basename(path)}")
            logging.info(f"Removed: {path}")

    def remove_selected(self):
        """Remove all selected items from the scrollable frame."""
        to_remove = [path for path, item in self.file_items.items() if item['var'].get()]
        if not to_remove:
            messagebox.showwarning("No Selection", "No items selected to remove.")
            return
        for path in to_remove:
            self.remove_single(path)
        self.status_var.set("Selected items removed.")

    def clear_all(self):
        """Clear all items from the scrollable frame."""
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to remove all items?"):
            for path in list(self.file_items.keys()):
                self.remove_single(path)
            self.status_var.set("All items cleared.")
            logging.info("All items cleared from the list.")

    def copy_to_clipboard(self):
        """Process the selected files/folders and copy their content to the clipboard."""
        selected_paths = [path for path, item in self.file_items.items() if item['var'].get()]
        if not selected_paths:
            messagebox.showerror("Error", "Please select files or folders to copy.")
            logging.error("No files or folders selected.")
            return

        self.progress['maximum'] = len(selected_paths)
        self.progress['value'] = 0
        self.status_var.set("Processing files...")
        self.root.update_idletasks()

        try:
            py_content, readme_content, file_count, total_characters = self.process_files(selected_paths)
        except Exception as e:
            logging.exception("An unexpected error occurred during file processing.")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            self.status_var.set("Error during processing.")
            return

        if py_content or readme_content:
            combined_py_content = "\n\n".join(py_content)
            combined_content = combined_py_content + ("\n\n" + readme_content if readme_content else "")
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(combined_content)
                self.status_var.set(f"Copied content from {file_count} files, totaling {total_characters} characters.")
                messagebox.showinfo("Success", f"Copied content from {file_count} files, totaling {total_characters} characters.")
                logging.info(f"Copied content from {file_count} files, totaling {total_characters} characters.")
            except Exception as e:
                logging.exception("Failed to copy content to clipboard.")
                messagebox.showerror("Error", f"Failed to copy to clipboard: {e}")
                self.status_var.set("Failed to copy to clipboard.")
        else:
            messagebox.showwarning("Warning", "No eligible .py files or README.md found, or all files were unreadable.")
            self.status_var.set("No content was copied to clipboard.")
            logging.warning("No eligible content to copy.")

        self.progress['value'] = len(selected_paths)

    def process_files(self, file_paths: List[str]) -> Tuple[List[str], str, int, int]:
        """
        Process the given file paths to extract content from .py files and README.md.

        Args:
            file_paths (List[str]): A list of file or directory paths.

        Returns:
            Tuple[List[str], str, int, int]: A tuple containing:
                - List of Python file contents.
                - README.md content.
                - Number of processed files.
                - Total number of characters processed.
        """
        py_content = []
        readme_content = ""
        file_count = 0
        total_characters = 0

        for idx, file_path in enumerate(file_paths, start=1):
            self.progress['value'] = idx - 1
            self.root.update_idletasks()

            file_path = file_path.strip('"')
            logging.debug(f"Examining file or folder: {file_path}")

            if os.path.isdir(file_path):
                logging.debug(f"Processing directory: {file_path}")
                for item in os.listdir(file_path):
                    full_path = os.path.join(file_path, item)
                    if os.path.isfile(full_path):
                        file_count, total_characters = self.process_single_file(
                            full_path, py_content, readme_content, file_count, total_characters
                        )
            else:
                file_count, total_characters = self.process_single_file(
                    file_path, py_content, readme_content, file_count, total_characters
                )

        logging.debug(f"Processed {file_count} files with {total_characters} total characters.")
        return py_content, readme_content, file_count, total_characters

    def process_single_file(
        self,
        file_path: str,
        py_content: List[str],
        readme_content: str,
        file_count: int,
        total_characters: int
    ) -> Tuple[int, int]:
        """
        Process a single file to extract content if it's a .py or README.md file.

        Args:
            file_path (str): The path to the file.
            py_content (List[str]): List to append Python file contents.
            readme_content (str): String to store README.md content.
            file_count (int): Current count of processed files.
            total_characters (int): Current total characters processed.

        Returns:
            Tuple[int, int]: Updated file count and total characters.
        """
        basename = os.path.basename(file_path)
        try:
            if file_path.endswith(".py") and basename != os.path.basename(__file__):
                with io.open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    py_content.append(content)
                    file_count += 1
                    total_characters += len(content)
                    logging.debug(f"Processed Python file: {file_path}")
            elif basename.lower() == "readme.md":
                with io.open(file_path, "r", encoding="utf-8") as f:
                    readme_content = f.read()
                    file_count += 1
                    total_characters += len(readme_content)
                    logging.debug(f"Processed README file: {file_path}")
        except UnicodeDecodeError:
            logging.warning(f"Unable to read {file_path} with UTF-8 encoding. Skipping this file.")
        except Exception as e:
            logging.error(f"Error processing file {file_path}: {e}")
        return file_count, total_characters

def main():
    """Main function to run the application."""
    root = TkinterDnD.Tk()
    app = PythonFilesSummarizer(root)
    logging.debug("Starting GUI event loop.")
    root.mainloop()

if __name__ == "__main__":
    main()
