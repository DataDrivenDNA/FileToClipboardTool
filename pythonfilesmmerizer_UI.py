import logging
import io
import threading
from pathlib import Path
from typing import List, Tuple, Dict

import tkinter as tk
from tkinter import ttk, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD

# Configure logging with rotation to prevent log file bloating
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# File handler with rotation
file_handler = RotatingFileHandler("app.log", maxBytes=5 * 1024 * 1024, backupCount=2)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

# Stream handler for console output
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)


class ToolTip:
    """A tooltip that appears when hovering over a widget."""

    def __init__(self, widget: tk.Widget, text: str, delay: int = 500):
        """
        Initialize the tooltip.

        Args:
            widget (tk.Widget): The widget to attach the tooltip to.
            text (str): The text to display in the tooltip.
            delay (int): Delay in milliseconds before the tooltip appears.
        """
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tip_window = None
        self.id = None
        self.widget.bind("<Enter>", self.schedule)
        self.widget.bind("<Leave>", self.unschedule)

    def schedule(self, event: tk.Event = None):
        """Schedule the tooltip to appear after a delay."""
        self.unschedule()
        self.id = self.widget.after(self.delay, self.show_tip)

    def unschedule(self, event: tk.Event = None):
        """Cancel the scheduled tooltip display."""
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
        self.hide_tip()

    def show_tip(self, event: tk.Event = None):
        """Display the tooltip."""
        if self.tip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#FFFFE0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Segoe UI", 10)
        )
        label.pack(ipadx=1)

    def hide_tip(self):
        """Hide the tooltip."""
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class ScrollableFrame(ttk.Frame):
    """A scrollable frame that can contain multiple widgets."""

    def __init__(self, container: ttk.Frame, *args, **kwargs):
        """
        Initialize the scrollable frame.

        Args:
            container (ttk.Frame): The parent container.
        """
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self, borderwidth=0, background="#f0f0f0")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


class PythonFilesSummarizer:
    """A GUI application to summarize Python files and README.md content."""

    def __init__(self, root: TkinterDnD.Tk):
        """
        Initialize the application.

        Args:
            root (TkinterDnD.Tk): The root Tkinter window with drag-and-drop support.
        """
        self.root = root
        self.root.title("Python Files Summarizer")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        self.root.configure(bg="#f0f0f0")

        self.file_items: Dict[Path, Dict[str, tk.Variable]] = {}

        self.create_widgets()
        self.setup_drag_and_drop()

    def create_widgets(self):
        """Create and arrange widgets in the main window."""
        # Style Configuration
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("TLabel", font=("Segoe UI", 11))
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), background="#f0f0f0")
        style.configure("Status.TLabel", font=("Segoe UI", 10), background="#d9d9d9")
        style.configure("TCheckbutton", font=("Segoe UI", 10))

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
        self.status_var = tk.StringVar(value="Welcome! Drag and drop files to begin.")
        self.status_label = ttk.Label(
            self.root,
            textvariable=self.status_var,
            style="Status.TLabel",
            anchor="w"
        )
        self.status_label.pack(fill=tk.X, padx=10, pady=(0, 10))

    def setup_drag_and_drop(self):
        """Configure drag and drop functionality."""
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.handle_drop)

    def handle_drop(self, event):
        """Handle files/folders dropped into the application."""
        logger.debug(f"Drop event triggered with data: {event.data}")
        paths = self.root.tk.splitlist(event.data)
        added = False
        for path_str in paths:
            path = Path(path_str.strip('"'))
            if path not in self.file_items:
                self.add_file_item(path)
                added = True
            else:
                logger.debug(f"Path already added: {path}")
        if added:
            self.status_var.set("Files added successfully.")
            logger.info(f"Added files/folders: {paths}")
        else:
            self.status_var.set("No new files were added.")
        return "break"

    def add_file_item(self, path: Path):
        """Add a file or folder item to the scrollable frame."""
        frame = ttk.Frame(self.scrollable_frame.scrollable_frame, padding=5, relief=tk.RIDGE)
        frame.pack(fill=tk.X, padx=5, pady=2)

        # Determine if path is a file or folder
        is_folder = path.is_dir()

        # Emoji Icon
        icon = "📁" if is_folder else "📄"
        icon_label = ttk.Label(frame, text=icon, font=("Segoe UI", 14))
        icon_label.pack(side=tk.LEFT, padx=(0, 10))

        # Checkbox
        var = tk.BooleanVar(value=True)
        check = ttk.Checkbutton(frame, variable=var)
        check.pack(side=tk.LEFT, padx=(0, 10))

        # File/Folder Name
        name = path.name if path.is_file() else path.name.rstrip('/')
        name_label = ttk.Label(frame, text=name, font=("Segoe UI", 10))
        name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Bind right-click for context menu
        name_label.bind("<Button-3>", lambda e, p=path: self.show_context_menu(e, p))

        # Store in dictionary
        self.file_items[path] = {'var': var, 'frame': frame}

    def show_context_menu(self, event, path: Path):
        """Show a context menu for the given file/folder."""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Remove", command=lambda p=path: self.remove_single(p))
        menu.post(event.x_root, event.y_root)

    def remove_single(self, path: Path):
        """Remove a single file/folder item."""
        item = self.file_items.pop(path, None)
        if item:
            item['frame'].destroy()
            self.status_var.set(f"Removed: {path.name}")
            logger.info(f"Removed: {path}")

    def remove_selected(self):
        """Remove all selected items from the scrollable frame."""
        to_remove = [path for path, item in self.file_items.items() if item['var'].get()]
        if not to_remove:
            messagebox.showwarning("No Selection", "No items selected to remove.")
            return
        for path in to_remove:
            self.remove_single(path)
        self.status_var.set("Selected items removed.")
        logger.info(f"Removed selected items: {[path for path in to_remove]}")

    def clear_all(self):
        """Clear all items from the scrollable frame."""
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to remove all items?"):
            paths = list(self.file_items.keys())
            for path in paths:
                self.remove_single(path)
            self.status_var.set("All items cleared.")
            logger.info("All items cleared from the list.")

    def copy_to_clipboard(self):
        """Process the selected files/folders and copy their content to the clipboard."""
        selected_paths = [path for path, item in self.file_items.items() if item['var'].get()]
        if not selected_paths:
            messagebox.showerror("Error", "Please select files or folders to copy.")
            logger.error("No files or folders selected.")
            return

        # Disable buttons to prevent multiple operations
        self.toggle_buttons(state='disabled')
        self.progress['maximum'] = len(selected_paths)
        self.progress['value'] = 0
        self.status_var.set("Processing files...")
        logger.info(f"Starting processing of {len(selected_paths)} items.")

        # Start processing in a separate thread
        threading.Thread(target=self._process_and_copy, args=(selected_paths,), daemon=True).start()

    def _process_and_copy(self, selected_paths: List[Path]):
        """Internal method to process files and copy content to clipboard."""
        try:
            py_content, readme_content, file_count, total_characters = self.process_files(selected_paths)
        except Exception as e:
            logger.exception("An unexpected error occurred during file processing.")
            self.show_error("An unexpected error occurred during processing.")
            self.update_status("Error during processing.")
            self.toggle_buttons(state='normal')
            return

        combined_content = "\n\n".join(py_content)
        if readme_content:
            combined_content += "\n\n" + readme_content

        if combined_content:
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(combined_content)
                self.show_info(
                    f"Copied content from {file_count} files, totaling {total_characters} characters."
                )
                logger.info(f"Copied content from {file_count} files, totaling {total_characters} characters.")
                self.update_status(f"Copied content from {file_count} files, totaling {total_characters} characters.")
            except Exception as e:
                logger.exception("Failed to copy content to clipboard.")
                self.show_error(f"Failed to copy to clipboard: {e}")
                self.update_status("Failed to copy to clipboard.")
        else:
            self.show_warning("No eligible .py files or README.md found, or all files were unreadable.")
            self.update_status("No content was copied to clipboard.")
            logger.warning("No eligible content to copy.")

        self.progress['value'] = len(selected_paths)
        self.toggle_buttons(state='normal')

    def process_files(self, file_paths: List[Path]) -> Tuple[List[str], str, int, int]:
        """
        Process the given file paths to extract content from .py files and README.md.

        Args:
            file_paths (List[Path]): A list of file or directory paths.

        Returns:
            Tuple[List[str], str, int, int]: A tuple containing:
                - List of Python file contents.
                - README.md content.
                - Number of processed files.
                - Total number of characters processed.
        """
        py_contents: List[str] = []
        readme_content: str = ""
        file_count = 0
        total_characters = 0

        for idx, path in enumerate(file_paths, start=1):
            self.progress['value'] = idx - 1
            self.root.update_idletasks()

            logger.debug(f"Examining file or folder: {path}")

            if path.is_dir():
                logger.debug(f"Processing directory: {path}")
                for item in path.iterdir():
                    if item.is_file():
                        file_count, total_characters, readme_content = self.process_single_file(
                            item, py_contents, readme_content, file_count, total_characters
                        )
            else:
                file_count, total_characters, readme_content = self.process_single_file(
                    path, py_contents, readme_content, file_count, total_characters
                )

        logger.debug(f"Processed {file_count} files with {total_characters} total characters.")
        return py_contents, readme_content, file_count, total_characters

    def process_single_file(
        self,
        file_path: Path,
        py_contents: List[str],
        readme_content: str,
        file_count: int,
        total_characters: int
    ) -> Tuple[int, int, str]:
        try:
            if file_path.suffix == ".py" and file_path.name != Path(__file__).name:
                with file_path.open("r", encoding="utf-8") as f:
                    content = f.read()
                    # Use absolute path instead of just filename
                    content_with_header = f'#{file_path.absolute()}\n###\n{content}\n###\n'
                    py_contents.append(content_with_header)
                    file_count += 1
                    total_characters += len(content)
                    logger.debug(f"Processed Python file: {file_path}")
            elif file_path.name.lower() == "readme.md":
                with file_path.open("r", encoding="utf-8") as f:
                    # Use absolute path for README as well
                    readme_content = f'#{file_path.absolute()}\n###\n{f.read()}\n###\n'
                    file_count += 1
                    total_characters += len(readme_content)
                    logger.debug(f"Processed README file: {file_path}")
        except UnicodeDecodeError:
            logger.warning(f"Unable to read {file_path} with UTF-8 encoding. Skipping this file.")
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
        return file_count, total_characters, readme_content


    def toggle_buttons(self, state: str = 'normal'):
        """
        Enable or disable buttons to prevent multiple operations.

        Args:
            state (str): The state to set for the buttons ('normal' or 'disabled').
        """
        for button in [self.copy_button, self.remove_button, self.clear_button]:
            button.config(state=state)

    def update_status(self, message: str):
        """
        Update the status label.

        Args:
            message (str): The message to display.
        """
        self.status_var.set(message)

    def show_info(self, message: str):
        """
        Show an information message box.

        Args:
            message (str): The message to display.
        """
        messagebox.showinfo("Success", message)

    def show_warning(self, message: str):
        """
        Show a warning message box.

        Args:
            message (str): The message to display.
        """
        messagebox.showwarning("Warning", message)

    def show_error(self, message: str):
        """
        Show an error message box.

        Args:
            message (str): The message to display.
        """
        messagebox.showerror("Error", message)


def main():
    """Main function to run the application."""
    root = TkinterDnD.Tk()
    app = PythonFilesSummarizer(root)
    logger.debug("Starting GUI event loop.")
    root.mainloop()


if __name__ == "__main__":
    main()
