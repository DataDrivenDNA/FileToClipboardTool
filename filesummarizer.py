import logging
import json
import io
import threading
from pathlib import Path
from typing import List, Tuple, Dict, TypedDict, Optional, Any, Generator
import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage
from tkinterdnd2 import DND_FILES  # type: ignore
from PIL import Image, ImageTk  # Ensure Pillow is installed

from tooltip import ToolTip
from scrollable_frame import ScrollableFrame

logger = logging.getLogger(__name__)

class FileItem(TypedDict):
    var: tk.BooleanVar
    frame: ttk.Frame
    type: str

class FilesSummarizer:
    """A GUI application to summarize Python, TypeScript, TSX, CSS files and README.md content."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Files Summarizer")
        self.root.geometry("900x650")
        self.root.minsize(800, 600)
        self.root.configure(bg="#ffffff")

        self.settings_file = Path.home() / '.filesummarizer_settings.json'
        
        self.file_items: Dict[Path, FileItem] = {}
        self.xml_format_enabled = tk.BooleanVar(value=True)
        self.filepath_enabled = tk.BooleanVar(value=True)
        
        self.load_settings()
        
        self.create_widgets()
        self.setup_drag_and_drop()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_settings(self):
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.xml_format_enabled.set(settings.get('xml_format', True))
                    self.filepath_enabled.set(settings.get('filepath', True))
                    logger.info("Settings loaded successfully")
        except Exception as e:
            logger.error(f"Error loading settings: {e}")

    def save_settings(self):
        try:
            settings = {
                'xml_format': self.xml_format_enabled.get(),
                'filepath': self.filepath_enabled.get()
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
            logger.info("Settings saved successfully")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")

    def on_closing(self):
        self.save_settings()
        self.root.destroy()

    def create_widgets(self):
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("TLabel", font=("Segoe UI", 11))
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), background="#ffffff")
        style.configure("Status.TLabel", font=("Segoe UI", 10), background="#d9d9d9")
        style.configure("TCheckbutton", font=("Segoe UI", 10))
        style.configure("Hovered.TButton", background='#e0e0e0')

        self.symbols = {
            'folder': "📁",
            'python': "🐍",
            'typescript': "📘",
            'typescriptx': "📗",
            'css': "🎨",
            'readme': "📄",
            'unknown': "❓",
            'info': "ℹ️",
            'warning': "⚠️",
            'error': "❌",
        }

        # Header
        header = ttk.Label(self.root, text="Files Summarizer", style="Header.TLabel")
        header.pack(pady=(10, 5), padx=10, anchor="w")

        # Instruction
        instruction = ttk.Label(
            self.root,
            text="Drag and drop .py, .ts, .tsx, .css files, folders, or README.md here:",
            style="TLabel"
        )
        instruction.pack(pady=(0, 10), padx=10, anchor="w")

        # Initialize ScrollableFrame
        self.scrollable_frame = ScrollableFrame(self.root)
        self.scrollable_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Progress Bar
        self.progress = ttk.Progressbar(self.root, orient='horizontal', mode='determinate')
        self.progress.pack(fill=tk.X, padx=10, pady=10)
        self.progress['value'] = 0

        # Control Buttons Frame
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        # Copy Button
        self.copy_button = ttk.Button(button_frame, text="📋 Copy to Clipboard", command=self.copy_to_clipboard)
        self.copy_button.pack(side=tk.LEFT, padx=5)
        ToolTip(self.copy_button, "Copy the selected content to clipboard (Ctrl+C)")
        self.add_hover_effect(self.copy_button)

        # Remove Button
        self.remove_button = ttk.Button(button_frame, text="🗑️ Remove Selected", command=self.remove_selected)
        self.remove_button.pack(side=tk.LEFT, padx=5)
        ToolTip(self.remove_button, "Remove selected items from the list (Del)")
        self.add_hover_effect(self.remove_button)

        # Clear Button
        self.clear_button = ttk.Button(button_frame, text="❌ Clear All", command=self.clear_all)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        ToolTip(self.clear_button, "Clear all items from the list (Ctrl+X)")
        self.add_hover_effect(self.clear_button)

        # XML Format Toggle
        self.xml_toggle_button = ttk.Checkbutton(
            button_frame,
            text="XML Format",
            variable=self.xml_format_enabled,
            command=self.toggle_xml_format
        )
        self.xml_toggle_button.pack(side=tk.LEFT, padx=5)
        ToolTip(self.xml_toggle_button, "Toggle XML format for output")

        # Filepath Toggle
        self.filepath_toggle_button = ttk.Checkbutton(
            button_frame,
            text="Filepath",
            variable=self.filepath_enabled,
            command=self.toggle_filepath
        )
        self.filepath_toggle_button.pack(side=tk.LEFT, padx=5)
        ToolTip(self.filepath_toggle_button, "Toggle filepath in output")

        # Keyboard Shortcuts
        self.root.bind('<Control-c>', lambda event: self.copy_to_clipboard())  # type: ignore
        self.root.bind('<Delete>', lambda event: self.remove_selected())  # type: ignore
        self.root.bind('<Control-x>', lambda event: self.clear_all())  # type: ignore

        # Status Bar
        status_frame = ttk.Frame(self.root, style="Status.TLabel")
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.status_icon_label = ttk.Label(status_frame, image=None)
        self.status_icon_label.pack(side=tk.LEFT, padx=(0, 5))

        self.status_var = tk.StringVar(value="Welcome! Drag and drop files to begin.")
        self.status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            style="Status.TLabel",
            anchor="w"
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def add_hover_effect(self, widget: ttk.Button):
        def on_enter(e):
            widget['style'] = 'Hovered.TButton'

        def on_leave(e):
            widget['style'] = 'TButton'

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def setup_drag_and_drop(self):
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.handle_drop)

    def handle_drop(self, event):
        logger.debug(f"Drop event triggered with data: {event.data}")
        paths = self.root.tk.splitlist(event.data)
        
        # Convert paths to Path objects and remove duplicates
        unique_paths = {Path(path.strip('"')) for path in paths}
        existing_paths = {path for path in unique_paths if path in self.file_items}
        new_paths = unique_paths - existing_paths
        
        if not new_paths:
            self.update_status("No new files were added.", 'warning')
            return "break"
        
        # Process new paths
        total_files = 0
        for path in new_paths:
            if path.is_dir():
                total_files += sum(1 for _ in self.get_valid_files(path))
            else:
                total_files += 1
        
        self.progress['maximum'] = total_files
        self.progress['value'] = 0
        
        # Process files in a separate thread
        threading.Thread(target=self._process_dropped_items, 
                        args=(new_paths,), 
                        daemon=True).start()
        
        return "break"

    def _process_dropped_items(self, paths: set[Path]):
        """Process dropped items in a separate thread."""
        try:
            files_added = 0
            for path in paths:
                if path.is_dir():
                    files_added += self._process_directory(path)
                else:
                    if self._is_valid_file(path):
                        self.root.after(0, self.add_file_item, path)
                        files_added += 1
                        self.progress['value'] += 1
            
            status_message = f"Added {files_added} file{'s' if files_added != 1 else ''}"
            self.root.after(0, self.update_status, status_message, 'info')
            logger.info(f"Successfully processed drop event: {status_message}")
        
        except Exception as e:
            error_msg = f"Error processing dropped items: {str(e)}"
            self.root.after(0, self.show_error, error_msg)
            self.root.after(0, self.update_status, error_msg, 'error')
            logger.error(error_msg, exc_info=True)
        
        finally:
            self.root.after(0, lambda: setattr(self.progress, 'value', 0))

    def _process_directory(self, directory: Path) -> int:
        """Process a directory and return the number of files added."""
        files_added = 0
        try:
            for file_path in self.get_valid_files(directory):
                self.root.after(0, self.add_file_item, file_path)
                files_added += 1
                self.progress['value'] += 1
                self.root.update_idletasks()
        except Exception as e:
            logger.error(f"Error processing directory {directory}: {e}")
        return files_added

    def get_valid_files(self, directory: Path):
        """Generator that yields valid files from a directory, including subdirectories."""
        try:
            for item in directory.rglob('*'):
                # Skip system directories and hidden files
                if self._should_skip_path(item):
                    continue
                
                if item.is_file() and self._is_valid_file(item):
                    yield item
        except PermissionError:
            logger.warning(f"Permission denied accessing {directory}")
        except Exception as e:
            logger.error(f"Error accessing {directory}: {e}")

    def _should_skip_path(self, path: Path) -> bool:
        """Check if a path should be skipped."""
        # Skip hidden files and directories
        if path.name.startswith('.'):
            return True
        
        # Skip common system directories
        system_dirs = {
            'node_modules', '__pycache__', 'venv', 'env',
            'build', 'dist', '.git', '.svn', '.hg'
        }
        
        # Check if any parent directory should be skipped
        current = path
        while current != current.parent:
            if current.name in system_dirs:
                return True
            current = current.parent
        
        return False

    def _is_valid_file(self, file_path: Path) -> bool:
        """Check if a file is valid for processing."""
        valid_extensions = {'.py', '.ts', '.tsx', '.css'}
        return (
            file_path.suffix.lower() in valid_extensions or
            file_path.name.lower() == 'readme.md'
        )

    def add_file_item(self, path: Path):
        frame = ttk.Frame(self.scrollable_frame.scrollable_frame, padding=5, relief=tk.RIDGE)
        frame.pack(fill=tk.X, padx=5, pady=2)

        is_folder = path.is_dir()

        if is_folder:
            file_type = 'folder'
            symbol = self.symbols['folder']
        elif path.suffix.lower() == ".py":
            file_type = 'python'
            symbol = self.symbols['python']
        elif path.suffix.lower() == ".ts":
            file_type = 'typescript'
            symbol = self.symbols['typescript']
        elif path.suffix.lower() == ".tsx":
            file_type = 'typescriptx'
            symbol = self.symbols['typescriptx']
        elif path.suffix.lower() == ".css":
            file_type = 'css'
            symbol = self.symbols['css']
        elif path.name.lower() == "readme.md":
            file_type = 'readme'
            symbol = self.symbols['readme']
        else:
            file_type = 'unknown'
            symbol = self.symbols['unknown']

        symbol_label = ttk.Label(frame, text=symbol)
        symbol_label.pack(side=tk.LEFT, padx=(0, 10))

        var = tk.BooleanVar(value=True)
        check = ttk.Checkbutton(frame, variable=var)
        check.pack(side=tk.LEFT, padx=(0, 10))

        name = path.name if not is_folder else path.name.rstrip('/')
        name_label = ttk.Label(frame, text=name, font=("Segoe UI", 10))
        name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        name_label.bind("<Button-3>", lambda e, p=path: self.show_context_menu(e, p))

        self.file_items[path] = {'var': var, 'frame': frame, 'type': file_type}


    def show_context_menu(self, event, path: Path):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Remove", command=lambda p=path: self.remove_single(p))  # type: ignore
        menu.post(event.x_root, event.y_root)

    def remove_single(self, path: Path):
        item = self.file_items.pop(path, None)
        if item:
            item['frame'].destroy()
            self.update_status(f"Removed: {path.name}", 'info')
            logger.info(f"Removed: {path}")

    def remove_selected(self):
        to_remove = [path for path, item in self.file_items.items() if item['var'].get()]
        if not to_remove:
            self.show_warning("No items selected to remove.")
            self.update_status("No items selected for removal.", 'warning')
            return
        for path in to_remove:
            self.remove_single(path)
        self.update_status("Selected items removed.", 'info')
        logger.info(f"Removed selected items: {[path for path in to_remove]}")

    def clear_all(self):
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to remove all items?"):
            paths = list(self.file_items.keys())
            for path in paths:
                self.remove_single(path)
            self.update_status("All items cleared.", 'info')
            logger.info("All items cleared from the list.")

    def copy_to_clipboard(self):
        selected_paths = [path for path, item in self.file_items.items() if item['var'].get()]
        if not selected_paths:
            self.show_error("Please select files or folders to copy.")
            self.update_status("No items selected to copy.", 'error')
            logger.error("No files or folders selected.")
            return

        self.toggle_buttons(state='disabled')
        self.progress['maximum'] = len(selected_paths)
        self.progress['value'] = 0
        self.update_status("Processing files...", 'info')
        logger.info(f"Starting processing of {len(selected_paths)} items.")

        threading.Thread(target=self._process_and_copy, args=(selected_paths,), daemon=True).start()

    def _process_and_copy(self, selected_paths: List[Path]):
        try:
            py_content, ts_content, css_content, readme_content, file_count, total_characters = self.process_files(selected_paths)
        except Exception as e:
            logger.exception("An unexpected error occurred during file processing.")
            self.show_error("An unexpected error occurred during processing.")
            self.update_status("Error during processing.", 'error')
            self.toggle_buttons(state='normal')
            return

        combined_content = "\n\n".join(py_content + ts_content + css_content)
        if readme_content:
            combined_content += "\n\n" + readme_content

        if combined_content:
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(combined_content)
                logger.info(f"Copied content from {file_count} files, totaling {total_characters} characters.")
                self.update_status(f"Copied content from {file_count} files, totaling {total_characters} characters.", 'info')
            except Exception as e:
                logger.exception("Failed to copy content to clipboard.")
                self.show_error(f"Failed to copy to clipboard: {e}")
                self.update_status("Failed to copy to clipboard.", 'error')
        else:
            self.show_warning("No eligible files found, or all files were unreadable.")
            self.update_status("No content was copied to clipboard.", 'warning')
            logger.warning("No eligible content to copy.")

        self.progress['value'] = len(selected_paths)
        self.toggle_buttons(state='normal')

    def process_files(self, file_paths: List[Path]) -> Tuple[List[str], List[str], List[str], str, int, int]:
        py_contents = []
        ts_contents = []
        css_contents = []
        readme_content = ""
        file_count = 0
        total_characters = 0

        for idx, path in enumerate(file_paths, start=1):
            self.progress['value'] = idx - 1
            self.root.update_idletasks()

            logger.debug(f"Examining file or folder: {path}")

            if path.is_dir():
                for item in path.rglob('*'):
                    if item.is_file():
                        file_type = self.determine_file_type(item)
                        if file_type in ['python', 'typescript', 'typescriptx', 'css', 'readme']:
                            file_count, total_characters, py_contents, ts_contents, css_contents, readme_content = \
                                self.process_single_file(item, py_contents, ts_contents, css_contents, readme_content, file_count, total_characters, file_type)
            else:
                file_type = self.determine_file_type(path)
                if file_type in ['python', 'typescript', 'typescriptx', 'css', 'readme']:
                    file_count, total_characters, py_contents, ts_contents, css_contents, readme_content = \
                        self.process_single_file(path, py_contents, ts_contents, css_contents, readme_content, file_count, total_characters, file_type)

        logger.debug(f"Processed {file_count} files with {total_characters} total characters.")
        return py_contents, ts_contents, css_contents, readme_content, file_count, total_characters

    def determine_file_type(self, file_path: Path) -> str:
        if file_path.is_dir():
            return 'folder'
        elif file_path.suffix.lower() == ".py":
            return 'python'
        elif file_path.suffix.lower() == ".ts":
            return 'typescript'
        elif file_path.suffix.lower() == ".tsx":
            return 'typescriptx'
        elif file_path.suffix.lower() == ".css":
            return 'css'
        elif file_path.name.lower() == "readme.md":
            return 'readme'
        else:
            return 'unknown'

    def process_single_file(
        self,
        file_path: Path,
        py_contents: List[str],
        ts_contents: List[str],
        css_contents: List[str],
        readme_content: str,
        file_count: int,
        total_characters: int,
        file_type: str
    ) -> Tuple[int, int, List[str], List[str], List[str], str]:
        try:
            with file_path.open("r", encoding="utf-8") as f:
                content = f.read()

            content_with_header = self.format_content(file_path, content, file_type)
            if file_type == 'python':
                py_contents.append(content_with_header)
            elif file_type in ['typescript', 'typescriptx']:
                ts_contents.append(content_with_header)
            elif file_type == 'css':
                css_contents.append(content_with_header)
            elif file_type == 'readme':
                readme_content = content_with_header

            file_count += 1
            total_characters += len(content)
            logger.debug(f"Processed {file_type} file {file_path}")
        except UnicodeDecodeError:
            logger.warning(f"Unable to read {file_path} with UTF-8 encoding. Skipping this file.")
            self.show_error(f"Unable to read {file_path} with UTF-8 encoding. Skipping this file.")
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            self.show_error(f"Error processing file {file_path}: {e}")
        return file_count, total_characters, py_contents, ts_contents, css_contents, readme_content

    def format_content(self, file_path: Path, content: str, file_type: str) -> str:
        content_with_header = ""
        if self.xml_format_enabled.get():
            content_with_header += f'<file_info>\n'
            if self.filepath_enabled.get():
                content_with_header += f'  <path>{file_path.absolute()}</path>\n'
            content_with_header += f'  <type>{file_type}</type>\n'
            content_with_header += f'</file_info>\n'
            content_with_header += f'<content>\n{content}\n</content>\n\n'
        else:
            if self.filepath_enabled.get():
                content_with_header += f'# {file_path.absolute()}\n'
            content_with_header += f'{content}\n\n'
        return content_with_header

    def toggle_xml_format(self):
        if self.xml_format_enabled.get():
            self.update_status("XML format enabled.", 'info')
            logger.info("XML format enabled.")
        else:
            self.update_status("XML format disabled.", 'info')
            logger.info("XML format disabled.")
        self.save_settings()

    def toggle_filepath(self):
        if self.filepath_enabled.get():
            self.update_status("Filepath enabled.", 'info')
            logger.info("Filepath enabled.")
        else:
            self.update_status("Filepath disabled.", 'info')
            logger.info("Filepath disabled.")
        self.save_settings()

    def toggle_buttons(self, state: str = 'normal'):
        for button in [self.copy_button, self.remove_button, self.clear_button]:
            button.config(state=state)

    # Update the status update method
    def update_status(self, message: str, status_type: str = 'info'):
        status_symbol = self.symbols.get(status_type, '')
        self.status_var.set(f"{status_symbol} {message}")

    def show_info(self, message: str):
        messagebox.showinfo("Success", message)

    def show_warning(self, message: str):
        messagebox.showwarning("Warning", message)

    def show_error(self, message: str):
        messagebox.showerror("Error", message)

