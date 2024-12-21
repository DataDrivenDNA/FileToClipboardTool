# Python Files Summarizer

A user-friendly GUI application that allows you to easily collect and copy content from multiple Python files and README.md files. Perfect for developers who need to quickly gather code snippets or documentation from various files.

## Features

- **Drag and Drop Interface**: Easily add Python files and folders by dragging them into the application
- **Smart File Processing**: 
  - Automatically processes `.py` files and `README.md` files
  - Handles both individual files and entire folders
- **Flexible Selection**:
  - Select/deselect individual files using checkboxes
  - Remove single files via right-click context menu
  - Clear all files with one click
- **Output Formatting Options**:
  - Toggle XML format for structured output
  - Toggle filepath inclusion in output
- **User-Friendly Interface**:
  - Progress bar shows processing status
  - Status messages keep you informed
  - Tooltips provide helpful hints
  - Keyboard shortcuts for common actions
- **Error Handling**:
  - Graceful handling of unreadable files
  - Comprehensive error messages
  - Detailed logging with rotation to prevent log bloat

## Installation

1. **Ensure you have Python 3.x installed**

2. **Install required dependencies:**

    ```bash
    pip install tkinterdnd2
    ```
    
    or
   
   ```bash
    pip install -r requirements.txt
    ```

## Usage

1. **Run the application:**

    ```bash
    python main.py
    ```

2. **Add files/folders using any of these methods:**
   - Drag and drop files/folders into the application window
   - Drag and drop multiple items simultaneously

3. **Configure output format:**
   - Use "XML Format" checkbox to toggle XML-style output
   - Use "Filepath" checkbox to toggle inclusion of file paths

4. **Manage your files:**
   - Use checkboxes to select/deselect items
   - Right-click items to remove them
   - Use the buttons at the bottom to perform actions

5. **Copy content:**
   - Select the desired files using checkboxes
   - Click "Copy to Clipboard" or press `Ctrl+C`
   - The content is now ready to paste elsewhere

## Keyboard Shortcuts

- `Ctrl+C`: Copy selected content to clipboard
- `Delete`: Remove selected items
- `Ctrl+X`: Clear all items

## Technical Details

- Built with Python's `tkinter` library
- Uses `tkinterdnd2` for drag-and-drop functionality
- Implements UTF-8 encoding for file reading
- Includes rotating log system to prevent log file bloat
- Saves user preferences between sessions

## Logging

The application creates a log file (`app.log`) that:
- Rotates when reaching 5MB in size
- Keeps up to 2 backup files
- Tracks file processing activities, errors, and user actions
- Outputs INFO level to console and DEBUG level to file

## Requirements

- Python 3.x
- `tkinterdnd2` library
- Operating System: Windows/Linux/MacOS

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is open source and available under the MIT License.

## Author

[DataDrivenDNA]

---

For bug reports or feature requests, please open an issue on the project repository.
