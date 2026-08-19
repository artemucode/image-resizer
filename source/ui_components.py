from tkinter import ttk

def setup_styles():
    style = ttk.Style()
    style.configure("TLabel", padding=4)
    style.configure("TButton", padding=6)
    style.configure("TLabelframe", padding=8)
    style.configure("Action.TButton", font=("Segoe UI", 10, "bold"))
    return style
