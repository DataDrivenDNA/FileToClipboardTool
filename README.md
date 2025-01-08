# Files Summarizer

A user-friendly GUI application that allows you to easily collect and copy content from multiple file types. Perfect for developers who need to quickly gather code snippets or documentation from various files.

## Features

- **Drag and Drop Interface**: Easily add files and folders by dragging them into the application
- **Multiple File Type Support**: 
  - Default support for `.py`, `.ts`, `.tsx`, `.css`, `.lua`, and `README.md` files
  - Customizable file type support through the Manage File Types interface
  - Smart filtering of binary and system files
- **File Management**:
  - View files in a tree structure
  - Remove files via right-click context menu or Delete key
  - Clear all files with one click
  - Bulk file operations
- **Output Formatting Options**:
  - Toggle XML format for structured output
  - Toggle filepath inclusion in output
- **User-Friendly Interface**:
  - Progress bar shows processing status
  - Status messages with icons
  - Tooltips provide helpful hints
  - Keyboard shortcuts for common actions
- **Error Handling**:
  - Graceful handling of unreadable files
  - UTF-8 encoding support
  - Comprehensive error messages
  - Detailed logging with rotation

## Installation

1. **Ensure you have Python 3.x installed**

2. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the application:**
   ```bash
   python main.py
   ```

2. **Add files/folders:**
   - Drag and drop files/folders into the application window
   - Supports multiple items simultaneously
   - Files are organized in a tree structure

3. **Configure output:**
   - Toggle "XML Format" for structured output
   - Toggle "Filepath" to include file paths
   - Use "Manage File Types" to customize accepted file types

4. **Manage files:**
   - Remove items using Delete key or right-click menu
   - Clear all items using the Clear All button
   - View file paths and types in the tree view

5. **Copy content:**
   - Click "Copy to Clipboard" or press `Ctrl+C`
   - Content is formatted based on your settings

## Keyboard Shortcuts

- `Ctrl+C`: Copy content to clipboard
- `Delete`: Remove selected items
- `Ctrl+X`: Clear all items

## File Type Management

- **Default Supported Types**: `.py`, `.ts`, `.tsx`, `.css`, `.lua`, `README.md`
- **Blacklisted Types**: Binary files (images, PDFs, Office documents)
- **Custom Types**: Add your own file types through the Manage File Types interface
- **Smart Filtering**: Automatically skips system directories like `.git`, `node_modules`

## Technical Details

- Built with Python's `tkinter` and `tkinterdnd2`
- Tree-based file visualization
- UTF-8 file reading
- Settings persistence between sessions
- Rotating log system (5MB max size, 2 backups)

## Logging

The application maintains logs in `app.log`:
- Rotates at 5MB size
- Keeps 2 backup files
- Console output: INFO level
- File output: DEBUG level

## Requirements

- Python 3.x
- Required libraries (see requirements.txt)
- Operating System: Windows/Linux/MacOS

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is open source and available under the MIT License.

---

For bug reports or feature requests, please open an issue on the project repository.
