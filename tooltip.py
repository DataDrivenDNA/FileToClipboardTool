import tkinter as tk
from typing import Optional, Any


class ToolTip:
    """A tooltip that appears when hovering over a widget."""

    def __init__(self, widget: tk.Widget, text: str, delay: int = 500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tip_window: Optional[tk.Toplevel] = None
        self.id = ""
        self.widget.bind("<Enter>", self.schedule)
        self.widget.bind("<Leave>", self.unschedule)

    def schedule(self, event: Optional[Any] = None):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.show_tip)

    def unschedule(self, event: Optional[Any] = None):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = ""
        self.hide_tip()

    def show_tip(self, event: Optional[Any] = None):
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height()
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tip_window,
            text=self.text,
            justify=tk.LEFT,
            background="#FFFFE0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Segoe UI", 10)
        )
        label.pack(ipadx=1)

    def hide_tip(self):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
