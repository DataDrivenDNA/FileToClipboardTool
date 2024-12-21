import logging
import json
import threading
from pathlib import Path
from typing import List, Tuple, Dict, TypedDict, Any
import tkinter as tk
from tkinter import ttk, messagebox
from tkinterdnd2 import DND_FILES  # type: ignore

from tooltip import ToolTip

logger = logging.getLogger(__name__)

class FileItem(TypedDict):
    path: Path
    type: str
    selected: tk.BooleanVar

class FilesSummarizer:
    """A GUI application to summarize Python, TypeScript, TSX, CSS files and README.md content."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Files Summarizer")
        self.root.geometry("900x650")
        self.root.minsize(800, 600)
        self.root.configure(bg="#ffffff")

        self.settings_file = Path.home() / '.filesummarizer_settings.json'
        
        self.file_items: Dict[str, FileItem] = {}  # Changed to use tree IDs
        self.path_to_id: Dict[Path, str] = {}  # Map paths to tree IDs
        
        self.xml_format_enabled = tk.BooleanVar(value=True)
        self.filepath_enabled = tk.BooleanVar(value=True)
        
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
    
        # Add these style configurations
        style.configure("Treeview.Heading",
        font=("Segoe UI", 10, "bold"),
        padding=5
        )
        style.configure("Treeview",
        font=("Segoe UI", 10),
        rowheight=25  # Increase row height to better show icons
        )
        
        style.theme_use('clam')
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("TLabel", font=("Segoe UI", 11))
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), background="#ffffff")
        style.configure("Status.TLabel", font=("Segoe UI", 10), background="#d9d9d9")
        style.configure("TCheckbutton", font=("Segoe UI", 10))
        style.configure("Hovered.TButton", background='#e0e0e0')
        style.configure("Treeview", font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

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

        # Tree Frame with Scrollbars
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create TreeView
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("type", "path"),
            show="tree headings",  # Show both tree and column headings
            selectmode="extended"
        )
        
        # Configure columns and headings
        self.tree.column("#0", width=400, stretch=True)
        self.tree.column("type", width=50, stretch=False, anchor="center")
        self.tree.column("path", width=400, stretch=True)
        
        # Add column headings
        self.tree.heading("#0", text="File Name", anchor="w")
        self.tree.heading("type", text="Type", anchor="center")
        self.tree.heading("path", text="Path", anchor="w")
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid layout for tree and scrollbars
        self.tree.grid(column=0, row=0, sticky='nsew')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        # Configure columns
        self.tree.column("#0", width=400, stretch=True)
        self.tree.column("type", width=50, stretch=False)
        self.tree.column("path", width=400, stretch=True)

        # Progress Bar
        self.progress = ttk.Progressbar(self.root, orient='horizontal', mode='determinate')
        self.progress.pack(fill=tk.X, padx=10, pady=10)
        self.progress['value'] = 0

        # Control Buttons Frame
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        # Copy Button
        self.copy_button = ttk.Button(
            button_frame,
            text="📋 Copy to Clipboard",
            command=self.copy_to_clipboard
        )
        self.copy_button.pack(side=tk.LEFT, padx=5)
        ToolTip(self.copy_button, "Copy the selected content to clipboard (Ctrl+C)")
        self.add_hover_effect(self.copy_button)

        # Remove Button
        self.remove_button = ttk.Button(
            button_frame,
            text="🗑️ Remove Selected",
            command=self.remove_selected
        )
        self.remove_button.pack(side=tk.LEFT, padx=5)
        ToolTip(self.remove_button, "Remove selected items from the list (Del)")
        self.add_hover_effect(self.remove_button)

        # Clear Button
        self.clear_button = ttk.Button(
            button_frame,
            text="❌ Clear All",
            command=self.clear_all
        )
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

        # Status Bar
        status_frame = ttk.Frame(self.root, style="Status.TLabel")
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.status_var = tk.StringVar(value="Welcome! Drag and drop files to begin.")
        self.status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            style="Status.TLabel",
            anchor="w"
        )
        self.status_label.pack(fill=tk.X, expand=True)

        # Keyboard Shortcuts
        self.root.bind('<Control-c>', lambda event: self.copy_to_clipboard())
        self.root.bind('<Delete>', lambda event: self.remove_selected())
        self.root.bind('<Control-x>', lambda event: self.clear_all())
        
        self.tree.bind('<Delete>', self.handle_delete_key)  # Add keyboard binding
        self.tree.bind('<Button-3>', self.show_context_menu)  # Add right-click binding


    def handle_delete_key(self, event=None):
        """Handle delete key press."""
        selected_items = self.tree.selection()
        if selected_items:
            for item_id in selected_items:
                self.remove_item(item_id)
            self.update_status("Selected items deleted.", 'info')

    def show_context_menu(self, event):
        """Show context menu on right click."""
        item_id = self.tree.identify_row(event.y)
        
        if item_id:
            self.tree.selection_set(item_id)
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(
                label="Delete",
                command=lambda: self.remove_item(item_id)
            )
            
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

    def remove_item(self, item_id: str):
        """Remove a single item and its empty parent folders."""
        try:
            if not self.tree.exists(item_id):
                return

            parent_id = self.tree.parent(item_id)
            items_to_remove = [item_id]
            items_to_remove.extend(self.get_all_children(item_id))

            for item in items_to_remove:
                # If the item is a file, remove it from file_items
                if item in self.file_items:
                    path = self.file_items[item]['path']
                    del self.file_items[item]
                    if path in self.path_to_id:
                        del self.path_to_id[path]
                else:
                    # If the item is a folder, get the path from the tree's values
                    values = self.tree.item(item, 'values')
                    if values:
                        folder_path = Path(values[-1])
                        if folder_path in self.path_to_id:
                            del self.path_to_id[folder_path]

                if self.tree.exists(item):
                    self.tree.delete(item)

            # Clean up empty parents
            self.cleanup_empty_parents(parent_id)

        except Exception as e:
            logger.error(f"Error removing item: {e}")
            self.update_status("Error removing item.", 'error')


    def cleanup_empty_parents(self, parent_id: str):
        """Remove empty parent folders after deleting items."""
        try:
            current_parent = parent_id
            while current_parent:
                if not self.tree.exists(current_parent):
                    break

                if not self.tree.get_children(current_parent):
                    next_parent = self.tree.parent(current_parent)
                    
                    # Get path from values
                    values = self.tree.item(current_parent)['values']
                    if values and len(values) > 1:
                        parent_path = Path(values[1])
                        if parent_path in self.path_to_id:
                            del self.path_to_id[parent_path]
                    
                    # Delete the empty parent
                    self.tree.delete(current_parent)
                    current_parent = next_parent
                else:
                    break

        except Exception as e:
            logger.error(f"Error cleaning up parents: {e}")

    def get_all_children(self, item_id: str) -> List[str]:
        """Recursively get all children of an item."""
        children = []
        try:
            for child in self.tree.get_children(item_id):
                children.append(child)
                children.extend(self.get_all_children(child))
        except Exception as e:
            logger.error(f"Error getting children: {e}")
        return children
    
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
        """Handle drag and drop events."""
        logger.debug(f"Drop event triggered with data: {event.data}")
        paths = self.root.tk.splitlist(event.data)
        
        # Convert paths to Path objects and remove duplicates
        unique_paths = {Path(path.strip('"')) for path in paths}
        existing_paths = {path for path in unique_paths if path in self.path_to_id}
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
        
        # **Option B Correction**: Set maximum to 100 for percentage-based progress
        self.progress['maximum'] = 100
        self.progress['value'] = 0
        
        # Process files in a separate thread
        threading.Thread(
            target=self._process_dropped_items,
            args=(new_paths, total_files),  # Pass total_files for percentage calculation
            daemon=True
        ).start()
        
        return "break"


    def _process_dropped_items(self, paths: set[Path], total_files: int):
        """Process dropped items in a separate thread."""
        try:
            # Collect all valid files
            files_to_add = []
            for path in paths:
                if path.is_dir():
                    files_to_add.extend(self.get_valid_files(path))
                elif self._is_valid_file(path):
                    files_to_add.append(path)

            # Sort files by path
            sorted_files = sorted(files_to_add, key=lambda p: str(p).lower())

            # Add files to tree
            for idx, file_path in enumerate(sorted_files, 1):
                self.root.after(0, self.add_path_to_tree, file_path)
                # **Option B Correction**: Calculate percentage based on total_files
                progress_percent = (idx / total_files) * 100 if total_files > 0 else 100
                self.progress['value'] = progress_percent
                self.root.update_idletasks()

            status_message = f"Added {len(sorted_files)} file{'s' if len(sorted_files) != 1 else ''}"
            self.root.after(0, self.update_status, status_message, 'info')
            logger.info(f"Successfully processed drop event: {status_message}")

        except Exception as e:
            error_msg = f"Error processing dropped items: {str(e)}"
            self.root.after(0, self.show_error, error_msg)
            self.root.after(0, self.update_status, error_msg, 'error')
            logger.error(error_msg, exc_info=True)

        finally:
            # **Option B Correction**: Set progress to 100% upon completion
            self.root.after(0, lambda: setattr(self.progress, 'value', 100))


    def add_path_to_tree(self, path: Path) -> None:
        """Add a path to the tree view, creating parent folders as needed."""
        try:
            if path in self.path_to_id:
                return

            # Start with an empty string to use in the Treeview parent argument
            current_parent = ""
            current_path = Path()

            # Use ALL parts, not just from [1:]
            for part in path.parts:
                current_path = current_path / part

                # Check if this part already exists in the tree
                existing_id = self.path_to_id.get(current_path)

                if existing_id and self.tree.exists(existing_id):
                    # Use existing node
                    current_parent = existing_id
                else:
                    # Create new node
                    is_final = (current_path == path)

                    if is_final:
                        # This is the actual file
                        symbol = self.determine_file_type(current_path)  # Get symbol for UI
                        file_type = self.get_file_type_text(
                            current_path
                        )  # Get text type for internal use

                        new_id = self.tree.insert(
                            current_parent,
                            "end",
                            text=part,
                            values=(symbol, str(current_path)),  # Use symbol for UI
                        )

                        self.path_to_id[current_path] = new_id
                        self.file_items[new_id] = {
                            "path": current_path,
                            "type": file_type,  # Store text representation
                            "selected": tk.BooleanVar(value=True),
                        }
                    else:
                        # This is a folder
                        new_id = self.tree.insert(
                            current_parent,
                            "end",
                            text=part,
                            values=(self.symbols["folder"], str(current_path)),
                            open=True,
                        )
                        self.path_to_id[current_path] = new_id

                    current_parent = new_id

        except Exception as e:
            logger.error(f"Error adding path to tree: {path} - {str(e)}")
            self.update_status(f"Error adding: {path.name}", "error")

    def update_item_selection(self, item_id: str) -> None:
        """Update the selection state of an item and its children."""
        selected = self.file_items[item_id]['selected'].get()
        for child_id in self.tree.get_children(item_id):
            if child_id in self.file_items:
                self.file_items[child_id]['selected'].set(selected)

    def get_valid_files(self, directory: Path) -> List[Path]:
        """Get all valid files from a directory recursively."""
        valid_files = []
        try:
            for item in directory.rglob('*'):
                if self._should_skip_path(item):
                    continue
                if item.is_file() and self._is_valid_file(item):
                    valid_files.append(item)
        except PermissionError:
            logger.warning(f"Permission denied accessing {directory}")
        except Exception as e:
            logger.error(f"Error accessing {directory}: {e}")
        return valid_files

    def _should_skip_path(self, path: Path) -> bool:
        """Check if a path should be skipped."""
        if path.name.startswith('.'):
            return True
        
        system_dirs = {
            'node_modules', '__pycache__', 'venv', 'env',
            'build', 'dist', '.git', '.svn', '.hg'
        }
        
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

    def determine_file_type(self, file_path: Path) -> str:
        """Determine the type of file and return the corresponding symbol."""
        if file_path.is_dir():
            return self.symbols['folder']
        elif file_path.suffix.lower() == ".py":
            return self.symbols['python']
        elif file_path.suffix.lower() == ".ts":
            return self.symbols['typescript']
        elif file_path.suffix.lower() == ".tsx":
            return self.symbols['typescriptx']
        elif file_path.suffix.lower() == ".css":
            return self.symbols['css']
        elif file_path.name.lower() == "readme.md":
            return self.symbols['readme']
        else:
            return self.symbols['unknown']
        
    def copy_to_clipboard(self):
        """Copy selected files to clipboard."""
        selected_paths = self.get_selected_paths()
        if not selected_paths:
            self.show_error("Please select files to copy.")
            self.update_status("No items selected to copy.", 'error')
            logger.error("No files or folders selected.")
            return

        self.toggle_buttons(state='disabled')
        # **Option B Correction**: Set maximum to 100 for percentage-based progress
        self.progress['maximum'] = 100
        self.progress['value'] = 0
        self.update_status("Processing files...", 'info')
        logger.info(f"Starting processing of {len(selected_paths)} items.")

        threading.Thread(
            target=self._process_and_copy,
            args=(selected_paths,),
            daemon=True
        ).start()


    def get_selected_paths(self) -> List[Path]:
        """Get all selected file paths in correct order."""
        selected = []
        for item_id, item_data in self.file_items.items():
            if item_data['selected'].get():
                selected.append(item_data['path'])
        return sorted(selected)

    def _process_and_copy(self, selected_paths: List[Path]):
        """Process selected files and copy to clipboard."""
        try:
            py_content, ts_content, css_content, readme_content, file_count, total_characters = \
                self.process_files(selected_paths)
        except Exception as e:
            logger.exception("An unexpected error occurred during file processing.")
            self.root.after(0, self.show_error, "An unexpected error occurred during processing.")
            self.root.after(0, self.update_status, "Error during processing.", 'error')
            self.root.after(0, self.toggle_buttons, 'normal')
            return

        combined_content = "\n\n".join(filter(None, [
            "\n\n".join(py_content),
            "\n\n".join(ts_content),
            "\n\n".join(css_content),
            readme_content
        ]))

        if combined_content:
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(combined_content)
                status_msg = f"Copied content from {file_count} files, totaling {total_characters} characters."
                logger.info(status_msg)
                self.root.after(0, self.update_status, status_msg, 'info')
            except Exception as e:
                logger.exception("Failed to copy content to clipboard.")
                self.root.after(0, self.show_error, f"Failed to copy to clipboard: {e}")
                self.root.after(0, self.update_status, "Failed to copy to clipboard.", 'error')
        else:
            self.root.after(0, self.show_warning, "No eligible files found, or all files were unreadable.")
            self.root.after(0, self.update_status, "No content was copied to clipboard.", 'warning')
            logger.warning("No eligible content to copy.")

        # **Option B Correction**: Update progress as percentage
        self.root.after(0, lambda: setattr(self.progress, 'value', 100))
        self.root.after(0, self.toggle_buttons, 'normal')


    def process_files(self, file_paths: List[Path]) -> Tuple[List[str], List[str], List[str], str, int, int]:
        """Process files and return their contents."""
        py_contents = []
        ts_contents = []
        css_contents = []
        readme_content = ""
        file_count = 0
        total_characters = 0

        for idx, path in enumerate(file_paths, start=1):
            self.progress['value'] = idx - 1
            self.root.update_idletasks()

            try:
                with path.open("r", encoding="utf-8") as f:
                    content = f.read()

                content_with_header = self.format_content(path, content, self.determine_file_type(path))
                
                if path.suffix.lower() == ".py":
                    py_contents.append(content_with_header)
                elif path.suffix.lower() in (".ts", ".tsx"):
                    ts_contents.append(content_with_header)
                elif path.suffix.lower() == ".css":
                    css_contents.append(content_with_header)
                elif path.name.lower() == "readme.md":
                    readme_content = content_with_header

                file_count += 1
                total_characters += len(content)
                logger.debug(f"Processed file: {path}")
                
            except UnicodeDecodeError:
                logger.warning(f"Unable to read {path} with UTF-8 encoding. Skipping this file.")
                self.root.after(0, self.show_error, f"Unable to read {path} with UTF-8 encoding. Skipping this file.")
            except Exception as e:
                logger.error(f"Error processing file {path}: {e}")
                self.root.after(0, self.show_error, f"Error processing file {path}: {e}")

        return py_contents, ts_contents, css_contents, readme_content, file_count, total_characters

    def format_content(self, file_path: Path, content: str, file_type: str) -> str:
        """Format file content with header information."""
        # Get text representation for the file type
        type_text = self.get_file_type_text(file_path)
        
        if self.xml_format_enabled.get():
            header = f'<file_info>\n'
            if self.filepath_enabled.get():
                header += f'  <path>{file_path.absolute()}</path>\n'
            header += f'  <type>{type_text}</type>\n'  # Use text representation here
            header += f'</file_info>\n'
            return f'{header}<content>\n{content}\n</content>\n'
        else:
            header = f'# {file_path.absolute()}\n' if self.filepath_enabled.get() else ''
            return f'{header}{content}\n'

    def remove_selected(self):
        """Remove selected items from the tree."""
        selected = [item_id for item_id, item in self.file_items.items() 
                   if item['selected'].get()]
        if not selected:
            self.show_warning("No items selected to remove.")
            self.update_status("No items selected for removal.", 'warning')
            return
        
        for item_id in selected:
            self.remove_item(item_id)
        
        self.update_status("Selected items removed.", 'info')
        logger.info(f"Removed {len(selected)} items")

    def clear_all(self):
        """Clear all items from the tree."""
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to remove all items?"):
            self.tree.delete(*self.tree.get_children())
            self.file_items.clear()
            self.path_to_id.clear()
            self.update_status("All items cleared.", 'info')
            logger.info("All items cleared from the list.")

    def toggle_buttons(self, state: str = 'normal'):
        """Toggle the state of all buttons."""
        for button in [self.copy_button, self.remove_button, self.clear_button]:
            button.config(state=state)

    def update_status(self, message: str, status_type: str = 'info'):
        """Update the status bar with a message."""
        status_symbol = self.symbols.get(status_type, '')
        self.status_var.set(f"{status_symbol} {message}")

    def show_info(self, message: str):
        """Show an info message."""
        messagebox.showinfo("Information", message)

    def show_warning(self, message: str):
        """Show a warning message."""
        messagebox.showwarning("Warning", message)

    def show_error(self, message: str):
        """Show an error message."""
        messagebox.showerror("Error", message)

    def toggle_xml_format(self):
        """Toggle XML format setting."""
        if self.xml_format_enabled.get():
            self.update_status("XML format enabled.", 'info')
        else:
            self.update_status("XML format disabled.", 'info')
        self.save_settings()

    def toggle_filepath(self):
        """Toggle filepath display setting."""
        if self.filepath_enabled.get():
            self.update_status("Filepath enabled.", 'info')
        else:
            self.update_status("Filepath disabled.", 'info')
        self.save_settings()
        
    def get_file_type_text(self, file_path: Path) -> str:
        """Get the text representation of the file type."""
        if file_path.is_dir():
            return "Folder"
        elif file_path.suffix.lower() == ".py":
            return "Python"
        elif file_path.suffix.lower() == ".ts":
            return "TypeScript"
        elif file_path.suffix.lower() == ".tsx":
            return "TSX"
        elif file_path.suffix.lower() == ".css":
            return "CSS"
        elif file_path.name.lower() == "readme.md":
            return "README"
        else:
            return "Unknown"