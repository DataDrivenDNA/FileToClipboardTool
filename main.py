import logging
from tkinterdnd2 import TkinterDnD  # type: ignore
from filesummarizer import FilesSummarizer


def main():
    # Initialize the TkinterDnD root window and start the application
    root = TkinterDnD.Tk()
    app = FilesSummarizer(root)
    logging.getLogger(__name__).debug("Starting GUI event loop.")
    root.mainloop()


if __name__ == "__main__":
    main()
