import sys
from tkinter import ttk

import customtkinter as ctk

BG = "#FFF5F8"
SURFACE = "#FFFFFF"
SIDEBAR = "#FCE4EC"
BORDER = "#F8BBD0"
PINK = "#E91E63"
PINK_HOVER = "#C2185B"
PINK_LIGHT = "#F8BBD0"
PINK_SOFT = "#FDE7EF"
TEXT = "#3B2433"
TEXT_MUTED = "#8C6B7C"
DANGER = "#D32F2F"
DANGER_HOVER = "#B71C1C"
SEAT_FREE = "#FFFFFF"
SEAT_TAKEN = "#E8B4C8"
SEAT_PAID = "#9E8A94"
SEAT_SELECTED = PINK

FONT_FAMILY = "Segoe UI" if sys.platform == "win32" else "Noto Sans"


def font(size=13, weight="normal"):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def apply():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    theme = ctk.ThemeManager.theme
    theme["CTkButton"].update(fg_color=[PINK, PINK], hover_color=[PINK_HOVER, PINK_HOVER], corner_radius=10)
    theme["CTkEntry"].update(border_color=[BORDER, BORDER], fg_color=[SURFACE, SURFACE], text_color=[TEXT, TEXT],
                             corner_radius=8)
    theme["CTkComboBox"].update(border_color=[BORDER, BORDER], button_color=[PINK_LIGHT, PINK_LIGHT],
                                button_hover_color=[PINK, PINK], fg_color=[SURFACE, SURFACE], text_color=[TEXT, TEXT],
                                corner_radius=8)
    theme["CTkOptionMenu"].update(fg_color=[PINK, PINK], button_color=[PINK_HOVER, PINK_HOVER],
                                  button_hover_color=[PINK_HOVER, PINK_HOVER])
    theme["CTkCheckBox"].update(fg_color=[PINK, PINK], hover_color=[PINK_HOVER, PINK_HOVER],
                                border_color=[PINK, PINK])
    theme["CTkSegmentedButton"].update(selected_color=[PINK, PINK], selected_hover_color=[PINK_HOVER, PINK_HOVER],
                                       unselected_color=[PINK_SOFT, PINK_SOFT],
                                       unselected_hover_color=[PINK_LIGHT, PINK_LIGHT],
                                       fg_color=[PINK_SOFT, PINK_SOFT], text_color=[TEXT, TEXT])
    theme["CTkScrollbar"].update(button_color=[PINK_LIGHT, PINK_LIGHT], button_hover_color=[PINK, PINK])
    theme["CTkLabel"].update(text_color=[TEXT, TEXT])
    theme["CTkTextbox"].update(border_color=[BORDER, BORDER], fg_color=[SURFACE, SURFACE], text_color=[TEXT, TEXT])
    theme["CTkFrame"].update(fg_color=[SURFACE, SURFACE])
    theme["CTk"].update(fg_color=[BG, BG])
    theme["CTkToplevel"].update(fg_color=[BG, BG])


def style_treeview(root):
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(
        "Pink.Treeview",
        background=SURFACE,
        fieldbackground=SURFACE,
        foreground=TEXT,
        rowheight=30,
        borderwidth=0,
        font=(FONT_FAMILY, -13),
    )
    style.configure(
        "Pink.Treeview.Heading",
        background=PINK_SOFT,
        foreground=TEXT,
        relief="flat",
        font=(FONT_FAMILY, -13, "bold"),
        padding=(6, 6),
    )
    style.map("Pink.Treeview.Heading", background=[("active", PINK_LIGHT)])
    style.map("Pink.Treeview", background=[("selected", PINK)], foreground=[("selected", "#FFFFFF")])
    style.layout("Pink.Treeview", [("Pink.Treeview.treearea", {"sticky": "nswe"})])
    style.configure("Pink.Vertical.TScrollbar", background=PINK_LIGHT, troughcolor=BG, borderwidth=0,
                    arrowcolor=PINK_HOVER)
