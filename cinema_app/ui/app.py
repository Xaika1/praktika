import customtkinter as ctk

import config
import validators as v
from db import Database, DatabaseError, check_server, create_database
from repository import CinemaRepository
from ui import theme
from ui.booking_page import BookingPage
from ui.halls_page import HallsPage
from ui.movies_page import MoviesPage
from ui.report_page import ReportPage
from ui.sessions_page import SessionsPage
from ui.tickets_page import TicketsPage
from ui.widgets import FormDialog, ask, show_error

PAGES = [
    ("booking", "Бронирование", BookingPage),
    ("sessions", "Сеансы", SessionsPage),
    ("movies", "Фильмы", MoviesPage),
    ("halls", "Залы", HallsPage),
    ("tickets", "Билеты", TicketsPage),
    ("report", "Отчёт", ReportPage),
]


class App(ctk.CTk):
    def __init__(self):
        theme.apply()
        super().__init__()
        theme.style_treeview(self)
        self.title("Кинотеатр «Розовый экран» — бронирование билетов")
        self.geometry("1320x800")
        self.minsize(1180, 700)
        self.settings = config.load_settings()
        self.db = None
        self.repo = None
        self.pages = {}
        self.nav_buttons = {}
        self.current = None
        self._toast_job = None

        self.sidebar = ctk.CTkFrame(self, fg_color=theme.SIDEBAR, corner_radius=0, width=230)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.container = ctk.CTkFrame(self, fg_color=theme.BG, corner_radius=0)
        self.container.pack(side="left", fill="both", expand=True)
        self.toast_label = ctk.CTkLabel(self, text="", fg_color=theme.TEXT, text_color="#FFFFFF", corner_radius=10,
                                        font=theme.font(13), height=38)
        self.build_sidebar()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(200, self.start)

    def build_sidebar(self):
        logo = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo.pack(fill="x", padx=20, pady=(26, 30))
        ctk.CTkLabel(logo, text="●", font=theme.font(30), text_color=theme.PINK).pack(side="left")
        names = ctk.CTkFrame(logo, fg_color="transparent")
        names.pack(side="left", padx=8)
        ctk.CTkLabel(names, text="Розовый экран", font=theme.font(17, "bold")).pack(anchor="w")
        ctk.CTkLabel(names, text="касса кинотеатра", font=theme.font(12), text_color=theme.TEXT_MUTED).pack(anchor="w")
        for key, label, _cls in PAGES:
            button = ctk.CTkButton(self.sidebar, text=label, anchor="w", height=42, corner_radius=10,
                                   font=theme.font(14), fg_color="transparent", text_color=theme.TEXT,
                                   hover_color=theme.PINK_LIGHT, command=lambda k=key: self.show(k))
            button.pack(fill="x", padx=14, pady=3)
            self.nav_buttons[key] = button
        self.db_label = ctk.CTkLabel(self.sidebar, text="", font=theme.font(11), text_color=theme.TEXT_MUTED,
                                     justify="left")
        self.db_label.pack(side="bottom", anchor="w", padx=20, pady=(4, 18))
        ctk.CTkButton(self.sidebar, text="Настройки подключения", height=32, fg_color="transparent",
                      border_width=1, border_color=theme.PINK_LIGHT, text_color=theme.PINK_HOVER,
                      hover_color=theme.PINK_SOFT, font=theme.font(12),
                      command=self.change_connection).pack(side="bottom", fill="x", padx=14)

    def start(self):
        if not self.connect():
            self.destroy()
            return
        for key, _label, cls in PAGES:
            self.pages[key] = cls(self.container, self)
        self.show("booking")

    def connect(self):
        error = None
        while True:
            if error:
                if not self.connection_dialog(error):
                    return False
            try:
                exists = check_server(self.settings)
                if not exists:
                    text = (f"На сервере нет базы «{self.settings['database']}».\n"
                            f"Создать её и заполнить демонстрационными данными?")
                    if not ask(self, text, "Первый запуск", ok_text="Создать", danger=False):
                        return False
                    create_database(self.settings)
                self.db = Database(self.settings)
                self.db.connect()
                self.repo = CinemaRepository(self.db)
                config.save_settings(self.settings)
                self.db_label.configure(text=f"MySQL: {self.settings['user']}@{self.settings['host']}\n"
                                             f"база: {self.settings['database']}")
                return True
            except DatabaseError as e:
                error = str(e)

    def connection_dialog(self, error=""):
        fields = [
            ("host", "Сервер", "entry", "localhost"),
            ("port", "Порт", "entry", "3306"),
            ("user", "Пользователь", "entry", "root"),
            ("password", "Пароль", "password", ""),
            ("database", "База данных", "entry", "cinema"),
        ]

        def validate(raw):
            return {
                "host": v.text(raw["host"], "Сервер", 100),
                "port": v.integer(raw["port"], "Порт", 1, 65535),
                "user": v.text(raw["user"], "Пользователь", 64),
                "password": raw["password"],
                "database": v.text(raw["database"], "База данных", 64),
            }

        dialog = FormDialog(self, "Подключение к MySQL", fields, self.settings, validate, ok_text="Подключиться")
        if error:
            dialog.error.configure(text=error)
        data = dialog.show()
        if data:
            self.settings = data
        return data is not None

    def change_connection(self):
        old_settings = dict(self.settings)
        if not self.connection_dialog():
            return
        if self.db:
            self.db.close()
        try:
            check_server(self.settings)
            self.db.settings = self.settings
            self.db.connect()
        except DatabaseError as e:
            show_error(self, f"{e}\nОставлено прежнее подключение.")
            self.settings = old_settings
            self.db.settings = old_settings
            return
        config.save_settings(self.settings)
        self.db_label.configure(text=f"MySQL: {self.settings['user']}@{self.settings['host']}\n"
                                     f"база: {self.settings['database']}")
        if self.current:
            self.pages[self.current].refresh()
        self.toast("Подключение обновлено")

    def show(self, key):
        if key not in self.pages:
            return
        if self.current:
            self.pages[self.current].pack_forget()
            self.nav_buttons[self.current].configure(fg_color="transparent", text_color=theme.TEXT)
        self.current = key
        self.nav_buttons[key].configure(fg_color=theme.PINK, text_color="#FFFFFF")
        self.pages[key].pack(fill="both", expand=True)
        self.pages[key].refresh()

    def open_booking(self, session_id):
        self.show("booking")
        self.pages["booking"].open_session(session_id)

    def toast(self, text):
        self.toast_label.configure(text=f"   {text}   ")
        self.toast_label.place(relx=0.5, rely=0.97, anchor="s")
        self.toast_label.lift()
        if self._toast_job:
            self.after_cancel(self._toast_job)
        self._toast_job = self.after(2500, self.toast_label.place_forget)

    def on_close(self):
        if self.db:
            self.db.close()
        self.destroy()
