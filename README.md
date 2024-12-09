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
- **User-Friendly Interface**:
  - Progress bar shows processing status
  - Status messages keep you informed
  - Tooltips provide helpful hints
  - Keyboard shortcuts for common actions
- **Error Handling**:
  - Graceful handling of unreadable files
  - Comprehensive error messages
  - Detailed logging for troubleshooting

## Installation

1. **Ensure you have Python 3.x installed**

2. **(Optional) Set Up a Virtual Environment**

    Setting up a virtual environment is recommended to manage dependencies and avoid conflicts with other Python projects.

    ```bash
    # Create a virtual environment named 'venv'
    python -m venv venv

    # Activate the virtual environment
    # On Windows:
    venv\Scripts\activate

    # On Unix or MacOS:
    source venv/bin/activate
    ```

3. **Install required dependencies:**

    ```bash
    pip install tkinterdnd2
    ```

## Usage

1. **Run the application:**

    ```bash
    python pythonfilesummarizer_UI.py
    ```

2. **Add files/folders using any of these methods:**
   - Drag and drop files/folders into the application window
   - Drag and drop multiple items simultaneously

3. **Manage your files:**
   - Use checkboxes to select/deselect items
   - Right-click items for additional options
   - Use the buttons at the bottom to perform actions

4. **Copy content:**
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
- Includes comprehensive logging for debugging

## Logging

The application creates a log file (`app.log`) that tracks:
- File processing activities
- Errors and exceptions
- User actions
- General application flow

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

---

# Optional: Setting Up a Virtual Environment (venv)

Setting up a virtual environment is an optional but recommended step to manage project dependencies effectively. This helps in isolating the project's dependencies from other Python projects on your system.

### Steps to Create and Activate a Virtual Environment

1. **Create a Virtual Environment**

    Open your terminal or command prompt and navigate to the project directory. Then, run the following command to create a virtual environment named `venv`:

    ```bash
    python -m venv venv
    ```

    This command creates a new directory called `venv` in your project folder, containing the virtual environment.

2. **Activate the Virtual Environment**

    - **On Windows:**

        ```bash
        venv\Scripts\activate
        ```

    - **On Unix or MacOS:**

        ```bash
        source venv/bin/activate
        ```

    After activation, your terminal prompt will typically change to indicate that the virtual environment is active, e.g., `(venv) yourname@machine:~/project$`

3. **Install Dependencies**

    With the virtual environment activated, install the required dependencies:

    ```bash
    pip install tkinterdnd2
    ```