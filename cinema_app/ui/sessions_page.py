from datetime import date, timedelta

import customtkinter as ctk

import validators as v
from ui import theme
from ui.widgets import DataTable, FormDialog, Page, ask, show_error

ALL_MOVIES = "Все фильмы"
ALL_HALLS = "Все залы"
WEEKDAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]


class SessionsPage(Page):
    title = "Сеансы"
    subtitle = "Расписание показов по залам"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.movie_map = {}
        self.hall_map = {}

        filters = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        filters.pack(side="left")
        ctk.CTkLabel(filters, text="с", font=theme.font(13)).pack(side="left", padx=(0, 6))
        self.date_from = ctk.CTkEntry(filters, width=110, height=36, font=theme.font(13))
        self.date_from.pack(side="left")
        ctk.CTkLabel(filters, text="по", font=theme.font(13)).pack(side="left", padx=6)
        self.date_to = ctk.CTkEntry(filters, width=110, height=36, font=theme.font(13))
        self.date_to.pack(side="left")
        today = date.today()
        self.date_from.insert(0, f"{today - timedelta(days=3):%d.%m.%Y}")
        self.date_to.insert(0, f"{today + timedelta(days=7):%d.%m.%Y}")
        self.movie_filter = ctk.CTkComboBox(filters, values=[ALL_MOVIES], width=190, height=36, state="readonly",
                                            command=lambda _v: self.refresh(), font=theme.font(13),
                                            dropdown_font=theme.font(13))
        self.movie_filter.set(ALL_MOVIES)
        self.movie_filter.pack(side="left", padx=(10, 0))
        self.hall_filter = ctk.CTkComboBox(filters, values=[ALL_HALLS], width=120, height=36, state="readonly",
                                           command=lambda _v: self.refresh(), font=theme.font(13),
                                           dropdown_font=theme.font(13))
        self.hall_filter.set(ALL_HALLS)
        self.hall_filter.pack(side="left", padx=8)
        self.button(filters, "Показать", self.refresh, "light", 100).pack(side="left")

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=28, pady=(0, 10), before=self.body)
        self.button(actions, "+ Новый сеанс", self.add, width=140).pack(side="left")
        self.button(actions, "Изменить", self.edit, "light", 110).pack(side="left", padx=8)
        self.button(actions, "Удалить", self.delete, "danger", 100).pack(side="left")
        self.button(actions, "Открыть схему зала →", self.open_booking, "light", 190).pack(side="right")

        self.table = DataTable(self.body, [
            ("date", "Дата", 110, "center"),
            ("time", "Время", 80, "center"),
            ("title", "Фильм", 240, "w"),
            ("hall", "Зал", 130, "w"),
            ("price", "Цена", 90, "e"),
            ("sold", "Продано", 100, "center"),
            ("load", "Заполненность", 120, "center"),
        ])
        self.table.pack(fill="both", expand=True)
        self.table.on_double_click(self.open_booking)

    def load_lists(self):
        movies = self.run(self.repo.movies) or []
        halls = self.run(self.repo.halls) or []
        self.movie_map = {m["title"]: m for m in movies}
        self.hall_map = {h["name"]: h for h in halls}
        self.movie_filter.configure(values=[ALL_MOVIES] + list(self.movie_map))
        self.hall_filter.configure(values=[ALL_HALLS] + list(self.hall_map))

    def period(self):
        return v.date(self.date_from.get(), "Дата с"), v.date(self.date_to.get(), "Дата по")

    def refresh(self):
        self.load_lists()
        try:
            date_from, date_to = self.period()
        except v.ValidationError as e:
            show_error(self, str(e))
            return
        movie = self.movie_map.get(self.movie_filter.get())
        hall = self.hall_map.get(self.hall_filter.get())
        sessions = self.run(lambda: self.repo.sessions(date_from, date_to, movie and movie["id"],
                                                       hall and hall["id"]))
        if sessions is None:
            return
        self.table.fill(sessions, lambda s: (
            f"{s['start_time']:%d.%m.%Y} {WEEKDAYS[s['start_time'].weekday()]}",
            f"{s['start_time']:%H:%M}",
            s["title"],
            f"{s['hall']} · {s['hall_type']}",
            f"{s['price']:.0f} ₽",
            f"{s['sold']} / {s['capacity']}",
            f"{100 * s['sold'] / s['capacity']:.0f} %",
        ), lambda s: ["muted"] if s["start_time"].date() < date.today() else [])

    def form(self, title, initial=None, session_id=None):
        self.load_lists()
        if not self.movie_map or not self.hall_map:
            show_error(self, "Сначала добавьте хотя бы один фильм и один зал.")
            return None
        fields = [
            ("movie", "Фильм", "combo", list(self.movie_map)),
            ("hall", "Зал", "combo", list(self.hall_map)),
            ("start_time", "Начало сеанса", "entry", "ДД.ММ.ГГГГ ЧЧ:ММ"),
            ("price", "Цена билета, ₽", "entry", "Например: 450"),
        ]

        def validate(raw):
            data = {
                "movie_id": self.movie_map[raw["movie"]]["id"],
                "hall_id": self.hall_map[raw["hall"]]["id"],
                "start_time": v.date_time(raw["start_time"]),
                "price": v.price(raw["price"]),
            }
            if initial is None and data["start_time"].date() < date.today():
                raise v.ValidationError("Нельзя создать сеанс на прошедшую дату.")
            self.repo.check_session(data, exclude_id=session_id)
            return data

        return FormDialog(self, title, fields, initial, validate).show()

    def add(self):
        data = self.form("Новый сеанс")
        if data and self.run(lambda: self.repo.add_session(data), "Сеанс добавлен") is not None:
            self.refresh()

    def edit(self):
        session = self.table.selected()
        if session is None:
            self.app.toast("Сначала выберите сеанс в таблице")
            return
        initial = {
            "movie": session["title"],
            "hall": session["hall"],
            "start_time": f"{session['start_time']:%d.%m.%Y %H:%M}",
            "price": f"{session['price']:.2f}",
        }
        data = self.form("Изменить сеанс", initial, session["id"])
        if data:
            self.run(lambda: self.repo.update_session(session["id"], data), "Сеанс изменён")
            self.refresh()

    def delete(self):
        session = self.table.selected()
        if session is None:
            self.app.toast("Сначала выберите сеанс в таблице")
            return
        text = f"Удалить сеанс «{session['title']}» {session['start_time']:%d.%m %H:%M}?"
        if session["sold"]:
            text += f"\nВместе с ним будут удалены проданные билеты: {session['sold']} шт."
        if ask(self, text, ok_text="Удалить"):
            self.run(lambda: self.repo.delete_session(session["id"]), "Сеанс удалён")
            self.refresh()

    def open_booking(self):
        session = self.table.selected()
        if session is None:
            self.app.toast("Сначала выберите сеанс в таблице")
            return
        self.app.open_booking(session["id"])
