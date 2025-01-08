import logging
import json
import threading
from pathlib import Path
from typing import List, Tuple, Dict, TypedDict, Any
import tkinter as tk
from tkinter import ttk, messagebox
from tkinterdnd2 import DND_FILES  # type: ignore

from tooltip import ToolTip
from manage_filetypes import ManageFileTypesUI

logger = logging.getLogger(__name__)

class FileItem(TypedDict):
    path: Path
    type: str
    selected: tk.BooleanVar

class FilesSummarizer:
    """A GUI application to summarize and copy text from allowed file types."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Files Summarizer")
        self.root.geometry("900x650")
        self.root.minsize(800, 600)
        self.root.configure(bg="#ffffff")

        self.settings_file = Path.home() / '.filesummarizer_settings.json'
        
        self.file_items: Dict[str, FileItem] = {}
        self.path_to_id: Dict[Path, str] = {}
        
        self.xml_format_enabled = tk.BooleanVar(value=True)
        self.filepath_enabled = tk.BooleanVar(value=True)

        # Default file types (allowed)
        self.default_file_types = {'.py', '.ts', '.tsx', '.css', '.lua', 'readme.md'}
        self.allowed_file_types = set(self.default_file_types)

        # a blacklist set of file types we never want to read
        self.blacklisted_file_types = {
            '.png', '.jpg', '.jpeg', '.gif', '.bmp',
            '.tif', '.tiff', '.pdf', '.doc', '.docx', 
            '.xls', '.xlsx', '.ppt', '.pptx',
            # add more types as needed
        }

        # Cache for user decisions about unknown extensions to avoid repeated prompts
        self.extension_decisions: Dict[str, bool] = {}

        self.symbols = {
            'folder': "📁",
            'python': "🐍",
            'typescript': "📘",
            'typescriptx': "📗",
            'css': "🎨",
            'readme': "📄",
            'lua': "🐬",
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
        '''Load settings from a JSON file.'''
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.xml_format_enabled.set(settings.get('xml_format', True))
                    self.filepath_enabled.set(settings.get('filepath', True))

                    saved_extensions = settings.get('allowed_file_types', [])
                    for ext in saved_extensions:
                        self.allowed_file_types.add(ext)

                    logger.info("Settings loaded successfully")
        except Exception as e:
            logger.error(f"Error loading settings: {e}")

    def save_settings(self):
        '''Save settings to a JSON file.'''
        try:
            settings = {
                'xml_format': self.xml_format_enabled.get(),
                'filepath': self.filepath_enabled.get(),
                'allowed_file_types': list(self.allowed_file_types),
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
        '''Create all widgets for the application.'''
        style = ttk.Style(self.root)
        style.theme_use('clam')
    
        style.configure("Treeview.Heading",
                        font=("Segoe UI", 10, "bold"),
                        padding=5)
        style.configure("Treeview",
                        font=("Segoe UI", 10),
                        rowheight=25)
        
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("TLabel", font=("Segoe UI", 11))
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), background="#ffffff")
        style.configure("Status.TLabel", font=("Segoe UI", 10), background="#d9d9d9")
        style.configure("TCheckbutton", font=("Segoe UI", 10))
        style.configure("Hovered.TButton", background='#e0e0e0')

        # Header
        header = ttk.Label(self.root, text="Files Summarizer", style="Header.TLabel")
        header.pack(pady=(10, 5), padx=10, anchor="w")

        # Instruction
        instruction = ttk.Label(
            self.root,
            text="Drag and drop .py, .ts, .tsx, .css, .lua, .txt files, folders, or README.md here:",
            style="TLabel"
        )
        instruction.pack(pady=(0, 10), padx=10, anchor="w")

        # Tree Frame with Scrollbars
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("type", "path"),
            show="tree headings",
            selectmode="extended"
        )
        
        self.tree.column("#0", width=400, stretch=True)
        self.tree.column("type", width=100, stretch=False, anchor="center") 
        self.tree.column("path", width=400, stretch=True)
        
        self.tree.heading("#0", text="File Name", anchor="w")
        self.tree.heading("type", text="Type", anchor="center")
        self.tree.heading("path", text="Path", anchor="w")
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(column=0, row=0, sticky='nsew')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

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
        ToolTip(self.copy_button, "Copy all files in the list to clipboard (Ctrl+C)")
        self.add_hover_effect(self.copy_button)

        # Remove Button
        self.remove_button = ttk.Button(
            button_frame,
            text="🗑️ Remove Selected",
            command=self.remove_selected
        )
        self.remove_button.pack(side=tk.LEFT, padx=5)
        ToolTip(self.remove_button, "Remove highlighted items from the list (Del)")
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

        # Manage Allowed File Types Button
        manage_button = ttk.Button(
            button_frame,
            text="⚙️ Manage File Types",
            command=self.manage_file_types
        )
        manage_button.pack(side=tk.LEFT, padx=5)
        ToolTip(manage_button, "Add/remove allowed file types")

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
        self.root.bind('<Control-x>', lambda event: self.clear_all())
        
        self.tree.bind('<Delete>', self.handle_delete_key)
        self.tree.bind('<Button-3>', self.show_context_menu)

    def handle_delete_key(self, event=None):
        """Handle delete key press from the TreeView."""
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
        """
        Remove a file or folder (and all nested contents) from both
        the TreeView and internal dictionaries. If removing a folder,
        all subfolders and files below it are also removed.
        """
        try:
            if not self.tree.exists(item_id):
                return

            parent_id = self.tree.parent(item_id)
            items_to_remove = [item_id]
            items_to_remove.extend(self.get_all_children(item_id))  # Recursively gather subfolders/files

            for child_id in items_to_remove:
                # Remove from file_items if present
                if child_id in self.file_items:
                    path = self.file_items[child_id]['path']
                    del self.file_items[child_id]
                    if path in self.path_to_id:
                        del self.path_to_id[path]
                else:
                    values = self.tree.item(child_id, 'values')
                    if values:
                        folder_path_str = values[-1]
                        folder_path = Path(folder_path_str)
                        if folder_path in self.path_to_id:
                            del self.path_to_id[folder_path]

                # Remove from the TreeView
                if self.tree.exists(child_id):
                    self.tree.delete(child_id)

            # Remove any empty parents up the chain
            self.cleanup_empty_parents(parent_id)

        except Exception as e:
            logger.error(f"Error removing item: {e}")
            self.update_status("Error removing item.", "error")


    def cleanup_empty_parents(self, parent_id: str):
        """
        After removing an item, walk upward. If any folders are now empty,
        remove them, continuing until we reach a non-empty or root node.
        """
        try:
            while parent_id:
                if not self.tree.exists(parent_id):
                    break  # Already gone

                if not self.tree.get_children(parent_id):
                    # Remove from self.file_items/path_to_id
                    if parent_id in self.file_items:
                        path = self.file_items[parent_id]['path']
                        del self.file_items[parent_id]
                        if path in self.path_to_id:
                            del self.path_to_id[path]
                    else:
                        values = self.tree.item(parent_id, 'values')
                        if values:
                            folder_path = Path(values[-1])
                            if folder_path in self.path_to_id:
                                del self.path_to_id[folder_path]

                    grandparent_id = self.tree.parent(parent_id)
                    self.tree.delete(parent_id)
                    parent_id = grandparent_id
                else:
                    # Folder is not empty; we're done
                    break

        except Exception as e:
            logger.error(f"Error cleaning up parents: {e}")


    def get_all_children(self, item_id: str) -> List[str]:
        """
        Recursively retrieve all child item IDs from the TreeView,
        so that removing a parent folder also removes everything below it.
        """
        descendants = []
        try:
            for child in self.tree.get_children(item_id):
                descendants.append(child)
                descendants.extend(self.get_all_children(child))
        except Exception as e:
            logger.error(f"Error getting children of item {item_id}: {e}")
        return descendants

    
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
        
        unique_paths = {Path(path.strip('"')) for path in paths}
        existing_paths = {path for path in unique_paths if path in self.path_to_id}
        new_paths = unique_paths - existing_paths
        
        if not new_paths:
            self.update_status("No new files were added.", 'warning')
            return "break"
        
        total_files = 0
        for path in new_paths:
            if path.is_dir():
                total_files += sum(1 for _ in self.get_valid_files(path))
            else:
                total_files += 1
        
        self.progress['maximum'] = 100
        self.progress['value'] = 0
        
        threading.Thread(
            target=self._process_dropped_items,
            args=(new_paths, total_files),
            daemon=True
        ).start()
        
        return "break"

    def _process_dropped_items(self, paths: set[Path], total_files: int):
        """Process dropped items in a separate thread."""
        try:
            files_to_add = []
            for path in paths:
                if path.is_dir():
                    files_to_add.extend(self.get_valid_files(path))
                elif self._is_valid_file(path):
                    files_to_add.append(path)

            sorted_files = sorted(files_to_add, key=lambda p: str(p).lower())

            for idx, file_path in enumerate(sorted_files, 1):
                self.root.after(0, self.add_path_to_tree, file_path)
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
            self.root.after(0, lambda: setattr(self.progress, 'value', 100))

    def add_path_to_tree(self, path: Path) -> None:
        """
        Add a path to the tree view, creating parent folders as needed.
        Every folder node is also stored in file_items and path_to_id,
        so that removing an upstream folder will remove everything below it.
        """
        try:
            if path in self.path_to_id:
                return  # Already in the tree

            current_parent = ""
            current_path = Path()

            for part in path.parts:
                current_path = current_path / part
                existing_id = self.path_to_id.get(current_path)

                if existing_id and self.tree.exists(existing_id):
                    # Reuse existing node
                    current_parent = existing_id
                else:
                    is_final = (current_path == path)
                    if is_final:
                        # It's the actual file
                        symbol = self.determine_file_type(current_path)
                        file_type = self.get_file_type_text(current_path)
                        new_id = self.tree.insert(
                            current_parent,
                            "end",
                            text=part,
                            values=(symbol, str(current_path))
                        )
                        self.path_to_id[current_path] = new_id
                        self.file_items[new_id] = {
                            "path": current_path,
                            "type": file_type,
                            "selected": tk.BooleanVar(value=False),
                        }
                    else:
                        # It's an intermediate folder
                        new_id = self.tree.insert(
                            current_parent,
                            "end",
                            text=part,
                            values=(self.symbols["folder"], str(current_path)),
                            open=True
                        )
                        self.path_to_id[current_path] = new_id

                        # Also store the folder node in file_items
                        self.file_items[new_id] = {
                            "path": current_path,
                            "type": "Folder",
                            "selected": tk.BooleanVar(value=False),
                        }

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
        """Check if a path should be skipped entirely."""
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
        """Check if a file is valid for processing or blacklisted. 
           Only ask the user once per unique unknown extension."""
        ext_lower = file_path.suffix.lower()
        name_lower = file_path.name.lower()

        # Skip blacklisted
        if ext_lower in self.blacklisted_file_types:
            return False

        # README.md is always allowed
        if name_lower == 'readme.md':
            return True

        # If extension is already allowed, proceed
        if ext_lower in self.allowed_file_types:
            return True

        # If we've already asked the user about this extension in the current session
        if ext_lower in self.extension_decisions:
            # Return whatever the user decided (True = yes, False = no)
            return self.extension_decisions[ext_lower]

        # Otherwise, ask the user if they want to allow this extension in the future
        answer = messagebox.askyesno(
            "Unknown File Type",
            f"Do you want to allow *{ext_lower}* files?\n\nFile: {file_path}"
        )
        # Cache the user's decision to avoid repeated prompts for this extension
        self.extension_decisions[ext_lower] = answer

        if answer:
            # User said yes -> add to allowed_file_types and save to settings
            self.allowed_file_types.add(ext_lower)
            self.save_settings()
            return True
        else:
            # User said no -> skip files of this extension
            return False

    def determine_file_type(self, file_path: Path) -> str:
        """Return an icon or symbol for the file type in the TreeView."""
        if file_path.is_dir():
            return self.symbols['folder']
        elif file_path.name.lower() == "readme.md":
            return self.symbols['readme']
        elif file_path.suffix.lower() == ".py":
            return self.symbols['python']
        elif file_path.suffix.lower() == ".ts":
            return self.symbols['typescript']
        elif file_path.suffix.lower() == ".tsx":
            return self.symbols['typescriptx']
        elif file_path.suffix.lower() == ".css":
            return self.symbols['css']
        elif file_path.suffix.lower() == ".lua":
            return self.symbols['lua']
        else:
            return self.symbols['unknown']
        
    def copy_to_clipboard(self):
        """Copy all files in the list to clipboard."""
        if not self.file_items:
            self.show_error("No files in the list to copy.")
            self.update_status("No items available to copy.", 'error')
            logger.error("No files or folders in the list.")
            return

        all_paths = [item_data['path'] for item_data in self.file_items.values()]
        if not all_paths:
            self.show_error("No files in the list to copy.")
            self.update_status("No items available to copy.", 'error')
            logger.error("No files or folders in the list.")
            return

        self.toggle_buttons(state='disabled')
        self.progress['maximum'] = 100
        self.progress['value'] = 0
        self.update_status("Processing files...", 'info')
        logger.info(f"Starting processing of {len(all_paths)} items.")

        threading.Thread(
            target=self._process_and_copy,
            args=(all_paths,),
            daemon=True
        ).start()

    def _process_and_copy(self, selected_paths: List[Path]):
        """Process files and copy to clipboard."""
        try:
            py_content, ts_content, css_content, lua_content, readme_content, file_count, total_characters = \
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
            "\n\n".join(lua_content),
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

        self.root.after(0, lambda: setattr(self.progress, 'value', 100))
        self.root.after(0, self.toggle_buttons, 'normal')

    def process_files(self, file_paths: List[Path]) -> Tuple[List[str], List[str], List[str], List[str], str, int, int]:
        """
        Read each file from file_paths (skipping directories),
        build content lists, and return combined info.
        """
        py_contents = []
        ts_contents = []
        css_contents = []
        lua_contents = []
        readme_content = ""
        file_count = 0
        total_characters = 0

        for idx, path in enumerate(file_paths, start=1):
            # Skip directories to avoid "Permission denied" or "No such file" errors
            if path.is_dir():
                logger.debug(f"Skipping directory: {path}")
                continue

            self.progress['value'] = (idx - 1) / len(file_paths) * 100
            self.root.update_idletasks()

            try:
                with path.open("r", encoding="utf-8") as f:
                    content = f.read()

                content_with_header = self.format_content(path, content, self.get_file_type_text(path))
                
                # Route by extension for grouping
                ext_lower = path.suffix.lower()
                name_lower = path.name.lower()

                if name_lower == "readme.md":
                    readme_content = content_with_header
                elif ext_lower == ".py":
                    py_contents.append(content_with_header)
                elif ext_lower in (".ts", ".tsx"):
                    ts_contents.append(content_with_header)
                elif ext_lower == ".css":
                    css_contents.append(content_with_header)
                elif ext_lower == ".lua":
                    lua_contents.append(content_with_header)
                else:
                    # For any other extension (like .txt),
                    # we just append to py_contents for now
                    py_contents.append(content_with_header)

                file_count += 1
                total_characters += len(content)
                logger.debug(f"Processed file: {path}")
                
            except UnicodeDecodeError:
                logger.warning(f"Unable to read {path} with UTF-8 encoding. Skipping.")
                self.root.after(0, self.show_error, f"Unable to read {path} (UTF-8). Skipping.")
            except Exception as e:
                logger.error(f"Error processing file {path}: {e}")
                self.root.after(0, self.show_error, f"Error processing file {path}: {e}")

        return py_contents, ts_contents, css_contents, lua_contents, readme_content, file_count, total_characters


    def format_content(self, file_path: Path, content: str, file_type: str) -> str:
        """Format file content with header information."""
        if self.xml_format_enabled.get():
            header = f'<file_info>\n'
            if self.filepath_enabled.get():
                header += f'  <path>{file_path.absolute()}</path>\n'
            header += f'  <type>{file_type}</type>\n'
            header += f'</file_info>\n'
            return f'{header}<content>\n{content}\n</content>\n'
        else:
            header = f'# {file_path.absolute()}\n' if self.filepath_enabled.get() else ''
            return f'{header}{content}\n'

    def remove_selected(self):
        """Remove items highlighted in the TreeView."""
        selected_items = self.tree.selection()
        if not selected_items:
            self.show_warning("No items selected to remove.")
            self.update_status("No items selected for removal.", 'warning')
            return
        
        for item_id in selected_items:
            self.remove_item(item_id)
        
        self.update_status("Selected items removed.", 'info')
        logger.info(f"Removed {len(selected_items)} items")

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
        """
        Return the actual extension (e.g., ".txt", ".css", ".py") 
        or ".md" for readme.md, or "Unknown" if none.
        """
        if file_path.name.lower() == "readme.md":
            return ".md"
        ext = file_path.suffix.lower()
        return ext if ext else "Unknown"

    def manage_file_types(self):
        """Open a new window for managing allowed file types."""
        ManageFileTypesUI(
            parent=self.root,
            allowed_file_types=self.allowed_file_types,
            default_file_types=self.default_file_types,
            save_settings_callback=self.save_settings
        )