import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from db import DatabaseError
from validators import ValidationError
from ui import theme


class DataTable(ctk.CTkFrame):
    def __init__(self, master, columns, **kwargs):
        super().__init__(master, fg_color=theme.SURFACE, corner_radius=12, border_width=1,
                         border_color=theme.BORDER, **kwargs)
        self.columns = columns
        self.tree = ttk.Treeview(self, columns=[c[0] for c in columns], show="headings",
                                 style="Pink.Treeview", selectmode="browse")
        for key, title, width, anchor in columns:
            self.tree.heading(key, text=title, anchor=anchor)
            self.tree.column(key, width=width, minwidth=40, anchor=anchor, stretch=True)
        self.tree.tag_configure("odd", background=theme.BG)
        self.tree.tag_configure("muted", foreground=theme.TEXT_MUTED)
        scroll = ctk.CTkScrollbar(self, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)
        scroll.grid(row=0, column=1, sticky="ns", padx=4, pady=8)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.rows = {}

    def fill(self, rows, values_func, tags_func=None):
        self.tree.delete(*self.tree.get_children())
        self.rows = {}
        for index, row in enumerate(rows):
            tags = ["odd"] if index % 2 else []
            if tags_func:
                tags += tags_func(row)
            item = self.tree.insert("", "end", values=values_func(row), tags=tags)
            self.rows[item] = row

    def selected(self):
        selection = self.tree.selection()
        return self.rows.get(selection[0]) if selection else None

    def on_double_click(self, callback):
        self.tree.bind("<Double-1>", lambda _e: callback())


class Page(ctk.CTkFrame):
    title = ""
    subtitle = ""

    def __init__(self, master, app):
        super().__init__(master, fg_color=theme.BG, corner_radius=0)
        self.app = app
        self.repo = app.repo
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 4))
        ctk.CTkLabel(header, text=self.title, font=theme.font(26, "bold"), text_color=theme.TEXT).pack(anchor="w")
        ctk.CTkLabel(header, text=self.subtitle, font=theme.font(13), text_color=theme.TEXT_MUTED).pack(anchor="w")
        self.toolbar = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar.pack(fill="x", padx=28, pady=(12, 8))
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=28, pady=(0, 24))

    def refresh(self):
        pass

    def run(self, action, success_text=None):
        try:
            result = action()
        except (DatabaseError, ValidationError) as e:
            show_error(self, str(e))
            return None
        if success_text:
            self.app.toast(success_text)
        return result

    def button(self, master, text, command, kind="primary", width=120):
        colors = {
            "primary": dict(fg_color=theme.PINK, hover_color=theme.PINK_HOVER, text_color="#FFFFFF"),
            "light": dict(fg_color=theme.PINK_SOFT, hover_color=theme.PINK_LIGHT, text_color=theme.PINK_HOVER),
            "danger": dict(fg_color=theme.SURFACE, hover_color="#FDECEA", text_color=theme.DANGER,
                           border_width=1, border_color=theme.DANGER),
        }[kind]
        return ctk.CTkButton(master, text=text, command=command, width=width, height=36,
                             font=theme.font(13, "bold"), **colors)

    def search_entry(self, master, placeholder, on_change, width=260):
        var = tk.StringVar()
        entry = ctk.CTkEntry(master, textvariable=var, placeholder_text=placeholder, width=width, height=36,
                             font=theme.font(13))
        var.trace_add("write", lambda *_: on_change())
        return entry, var


class Dialog(ctk.CTkToplevel):
    def __init__(self, master, title, width=440):
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)
        self.configure(fg_color=theme.BG)
        self.transient(master.winfo_toplevel())
        self.result = None
        self.width = width
        self.content = ctk.CTkFrame(self, fg_color=theme.SURFACE, corner_radius=14, border_width=1,
                                    border_color=theme.BORDER)
        self.content.pack(fill="both", expand=True, padx=16, pady=16)
        ctk.CTkLabel(self.content, text=title, font=theme.font(18, "bold")).pack(anchor="w", padx=20, pady=(16, 8))
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.bind("<Escape>", lambda _e: self.cancel())

    def show(self):
        self.update_idletasks()
        parent = self.master.winfo_toplevel()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_reqwidth()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.after(150, self._grab)
        self.wait_window()
        return self.result

    def _grab(self):
        try:
            self.grab_set()
            self.focus_force()
        except tk.TclError:
            pass

    def cancel(self):
        self.result = None
        self.destroy()

    def buttons(self, ok_text, ok_command, ok_kind="primary"):
        bar = ctk.CTkFrame(self.content, fg_color="transparent")
        bar.pack(fill="x", padx=20, pady=(8, 18))
        ok_colors = dict(fg_color=theme.DANGER, hover_color=theme.DANGER_HOVER) if ok_kind == "danger" else {}
        ctk.CTkButton(bar, text=ok_text, command=ok_command, width=130, height=36,
                      font=theme.font(13, "bold"), **ok_colors).pack(side="right")
        ctk.CTkButton(bar, text="Отмена", command=self.cancel, width=100, height=36, fg_color=theme.PINK_SOFT,
                      hover_color=theme.PINK_LIGHT, text_color=theme.PINK_HOVER,
                      font=theme.font(13)).pack(side="right", padx=(0, 8))
        self.bind("<Return>", lambda _e: ok_command())


class FormDialog(Dialog):
    def __init__(self, master, title, fields, initial=None, validate=None, ok_text="Сохранить"):
        super().__init__(master, title)
        self.validate = validate
        self.widgets = {}
        initial = initial or {}
        form = ctk.CTkFrame(self.content, fg_color="transparent")
        form.pack(fill="x", padx=20)
        for key, label, kind, extra in fields:
            ctk.CTkLabel(form, text=label, font=theme.font(12), text_color=theme.TEXT_MUTED).pack(anchor="w",
                                                                                                  pady=(6, 2))
            value = initial.get(key, "")
            if kind == "combo":
                widget = ctk.CTkComboBox(form, values=extra, width=380, height=34, state="readonly",
                                         font=theme.font(13), dropdown_font=theme.font(13))
                widget.set(value or (extra[0] if extra else ""))
            elif kind == "textbox":
                widget = ctk.CTkTextbox(form, width=380, height=80, border_width=1, font=theme.font(13))
                widget.insert("1.0", value)
            elif kind == "check":
                widget = ctk.CTkCheckBox(form, text=extra, font=theme.font(13))
                if value:
                    widget.select()
            else:
                widget = ctk.CTkEntry(form, width=380, height=34, placeholder_text=extra or "", font=theme.font(13),
                                      show="•" if kind == "password" else "")
                if value != "":
                    widget.insert(0, str(value))
            widget.pack(anchor="w")
            self.widgets[key] = (kind, widget)
        self.error = ctk.CTkLabel(self.content, text="", text_color=theme.DANGER, font=theme.font(12),
                                  wraplength=380, justify="left")
        self.error.pack(anchor="w", padx=20, pady=(8, 0))
        self.buttons(ok_text, self.submit)

    def values(self):
        result = {}
        for key, (kind, widget) in self.widgets.items():
            if kind == "textbox":
                result[key] = widget.get("1.0", "end").strip()
            elif kind == "check":
                result[key] = bool(widget.get())
            else:
                result[key] = widget.get()
        return result

    def submit(self):
        raw = self.values()
        try:
            data = self.validate(raw) if self.validate else raw
        except (ValidationError, DatabaseError) as e:
            self.error.configure(text=str(e))
            return
        self.result = data
        self.destroy()


class MessageDialog(Dialog):
    def __init__(self, master, title, message, kind="info", ask=False, ok_text="OK"):
        super().__init__(master, title, width=380)
        icon = {"info": "✓", "error": "!", "question": "?"}[kind]
        color = theme.DANGER if kind == "error" else theme.PINK
        row = ctk.CTkFrame(self.content, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 6))
        ctk.CTkLabel(row, text=icon, width=36, height=36, corner_radius=18, fg_color=color, text_color="#FFFFFF",
                     font=theme.font(18, "bold")).pack(side="left", anchor="n")
        ctk.CTkLabel(row, text=message, wraplength=300, justify="left", font=theme.font(13)).pack(
            side="left", padx=12, anchor="w")
        if ask:
            self.buttons(ok_text, self.confirm, "danger" if kind == "error" else "primary")
        else:
            bar = ctk.CTkFrame(self.content, fg_color="transparent")
            bar.pack(fill="x", padx=20, pady=(8, 18))
            ctk.CTkButton(bar, text="OK", width=100, height=36, command=self.confirm,
                          font=theme.font(13, "bold")).pack(side="right")
            self.bind("<Return>", lambda _e: self.confirm())

    def confirm(self):
        self.result = True
        self.destroy()


def show_error(master, message):
    MessageDialog(master, "Ошибка", message, kind="error").show()


def show_info(master, message, title="Готово"):
    MessageDialog(master, title, message, kind="info").show()


def ask(master, message, title="Подтверждение", ok_text="Да", danger=True):
    return bool(MessageDialog(master, title, message, kind="error" if danger else "question", ask=True,
                              ok_text=ok_text).show())


def stat_card(master, title, value, accent=False):
    card = ctk.CTkFrame(master, fg_color=theme.PINK if accent else theme.SURFACE, corner_radius=14,
                        border_width=0 if accent else 1, border_color=theme.BORDER)
    text_color = "#FFFFFF" if accent else theme.TEXT
    muted = "#FFE3EE" if accent else theme.TEXT_MUTED
    ctk.CTkLabel(card, text=title, font=theme.font(12), text_color=muted).pack(anchor="w", padx=18, pady=(14, 0))
    value_label = ctk.CTkLabel(card, text=value, font=theme.font(24, "bold"), text_color=text_color)
    value_label.pack(anchor="w", padx=18, pady=(0, 14))
    return card, value_label
