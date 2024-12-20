import tkinter as tk
from tkinter import ttk
import platform


class ScrollableFrame(ttk.Frame):
    """A scrollable frame that can contain multiple widgets with mouse wheel support."""

    def __init__(self, container: ttk.Frame, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self, borderwidth=0, background="#f0f0f0")
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas, padding=(0, 0, 0, 0))

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel events
        self.bind_mouse_wheel()

    def bind_mouse_wheel(self):
        operating_system = platform.system()
        if operating_system == 'Windows':
            self.canvas.bind_all("<MouseWheel>", self.on_mousewheel_windows)
        elif operating_system == 'Darwin':  # macOS
            self.canvas.bind_all("<MouseWheel>", self.on_mousewheel_mac)
        else:  # Linux and other systems
            self.canvas.bind_all("<Button-4>", self.on_mousewheel_linux)
            self.canvas.bind_all("<Button-5>", self.on_mousewheel_linux)

    def unbind_mouse_wheel(self):
        operating_system = platform.system()
        if operating_system == 'Windows':
            self.canvas.unbind_all("<MouseWheel>")
        elif operating_system == 'Darwin':  # macOS
            self.canvas.unbind_all("<MouseWheel>")
        else:  # Linux and other systems
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")

    def on_mousewheel_windows(self, event):
        # For Windows, event.delta is a multiple of 120
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_mousewheel_mac(self, event):
        # For macOS, event.delta is typically smaller
        self.canvas.yview_scroll(int(-1 * (event.delta)), "units")

    def on_mousewheel_linux(self, event):
        # For Linux, use Button-4 (scroll up) and Button-5 (scroll down)
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")

    def destroy(self):
        # Ensure that mouse wheel bindings are removed when the frame is destroyed
        self.unbind_mouse_wheel()
        super().destroy()
