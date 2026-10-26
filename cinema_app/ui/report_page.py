import csv
from datetime import date, timedelta
from tkinter import filedialog

import customtkinter as ctk

import validators as v
from ui import theme
from ui.widgets import DataTable, Page, show_error, show_info, stat_card

ALL_MOVIES = "Все фильмы"


class ReportPage(Page):
    title = "Отчёт по выручке"
    subtitle = "Выручка и заполняемость залов по сеансам за выбранный период"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.rows = []
        self.movie_map = {}
        ctk.CTkLabel(self.toolbar, text="с", font=theme.font(13)).pack(side="left", padx=(0, 6))
        self.date_from = ctk.CTkEntry(self.toolbar, width=110, height=36, font=theme.font(13))
        self.date_from.pack(side="left")
        ctk.CTkLabel(self.toolbar, text="по", font=theme.font(13)).pack(side="left", padx=6)
        self.date_to = ctk.CTkEntry(self.toolbar, width=110, height=36, font=theme.font(13))
        self.date_to.pack(side="left")
        today = date.today()
        self.date_from.insert(0, f"{today - timedelta(days=6):%d.%m.%Y}")
        self.date_to.insert(0, f"{today:%d.%m.%Y}")
        self.movie_filter = ctk.CTkComboBox(self.toolbar, values=[ALL_MOVIES], width=200, height=36,
                                            state="readonly", font=theme.font(13), dropdown_font=theme.font(13))
        self.movie_filter.set(ALL_MOVIES)
        self.movie_filter.pack(side="left", padx=10)
        self.button(self.toolbar, "Сформировать", self.refresh, width=140).pack(side="left")
        self.button(self.toolbar, "Экспорт в CSV", self.export, "light", 140).pack(side="right")

        cards = ctk.CTkFrame(self.body, fg_color="transparent")
        cards.pack(fill="x", pady=(0, 14))
        self.cards = {}
        for i, (key, title) in enumerate([("revenue", "Выручка"), ("paid", "Из неё оплачено"),
                                          ("tickets", "Продано билетов"), ("load", "Средняя заполняемость")]):
            card, label = stat_card(cards, title, "—", accent=i == 0)
            card.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 12, 0))
            cards.grid_columnconfigure(i, weight=1)
            self.cards[key] = label

        bottom = ctk.CTkFrame(self.body, fg_color="transparent")
        bottom.pack(fill="both", expand=True)
        bottom.grid_columnconfigure(0, weight=3)
        bottom.grid_columnconfigure(1, weight=2)
        bottom.grid_rowconfigure(0, weight=1)
        self.table = DataTable(bottom, [
            ("date", "Сеанс", 120, "center"),
            ("title", "Фильм", 190, "w"),
            ("hall", "Зал", 70, "center"),
            ("sold", "Билетов", 80, "center"),
            ("load", "Заполн.", 80, "center"),
            ("revenue", "Выручка", 100, "e"),
        ])
        self.table.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        chart_card = ctk.CTkFrame(bottom, fg_color=theme.SURFACE, corner_radius=12, border_width=1,
                                  border_color=theme.BORDER)
        chart_card.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(chart_card, text="Выручка по фильмам", font=theme.font(14, "bold")).pack(anchor="w", padx=16,
                                                                                            pady=(12, 0))
        self.chart = ctk.CTkCanvas(chart_card, bg=theme.SURFACE, highlightthickness=0)
        self.chart.pack(fill="both", expand=True, padx=12, pady=12)
        self.chart.bind("<Configure>", lambda _e: self.draw_chart())
        self.by_movie = []

    def load_movies(self):
        movies = self.run(self.repo.movies) or []
        self.movie_map = {m["title"]: m["id"] for m in movies}
        self.movie_filter.configure(values=[ALL_MOVIES] + list(self.movie_map))

    def refresh(self):
        self.load_movies()
        try:
            date_from = v.date(self.date_from.get(), "Дата с")
            date_to = v.date(self.date_to.get(), "Дата по")
            if date_from > date_to:
                raise v.ValidationError("Начало периода позже его конца.")
        except v.ValidationError as e:
            show_error(self, str(e))
            return
        movie_id = self.movie_map.get(self.movie_filter.get())
        rows = self.run(lambda: self.repo.revenue_by_sessions(date_from, date_to, movie_id))
        by_movie = self.run(lambda: self.repo.revenue_by_movies(date_from, date_to))
        if rows is None or by_movie is None:
            return
        self.rows = rows
        self.by_movie = by_movie
        self.table.fill(rows, lambda r: (
            f"{r['start_time']:%d.%m %H:%M}", r["title"], r["hall"], r["sold"],
            f"{100 * r['sold'] / r['capacity']:.0f} %", money(r["revenue"]),
        ))
        revenue = sum(r["revenue"] for r in rows)
        paid = sum(r["paid"] for r in rows)
        sold = sum(r["sold"] for r in rows)
        load = sum(r["sold"] / r["capacity"] for r in rows) / len(rows) * 100 if rows else 0
        self.cards["revenue"].configure(text=money(revenue))
        self.cards["paid"].configure(text=money(paid))
        self.cards["tickets"].configure(text=f"{sold}")
        self.cards["load"].configure(text=f"{load:.0f} %")
        self.draw_chart()

    def draw_chart(self):
        canvas = self.chart
        canvas.delete("all")
        data = self.by_movie[:8]
        width = canvas.winfo_width()
        if not data or width < 50:
            canvas.create_text(width // 2, 60, text="Нет данных за период", fill=theme.TEXT_MUTED,
                               font=(theme.FONT_FAMILY, -13))
            return
        top = max(float(d["revenue"]) for d in data) or 1
        bar_height = 22
        gap = 18
        for i, d in enumerate(data):
            y = 8 + i * (bar_height + gap + 14)
            canvas.create_text(4, y, text=d["title"], anchor="nw", fill=theme.TEXT, font=(theme.FONT_FAMILY, -12))
            length = max(4, (width - 110) * float(d["revenue"]) / top)
            color = theme.PINK if i == 0 else theme.PINK_LIGHT
            canvas.create_rectangle(4, y + 16, 4 + length, y + 16 + bar_height, fill=color, outline="")
            canvas.create_text(10 + length, y + 16 + bar_height // 2, text=money(d["revenue"]), anchor="w",
                               fill=theme.TEXT_MUTED, font=(theme.FONT_FAMILY, -12))

    def export(self):
        if not self.rows:
            show_error(self, "Сначала сформируйте отчёт.")
            return
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".csv",
                                            initialfile=f"выручка_{date.today():%Y-%m-%d}.csv",
                                            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["Дата и время", "Фильм", "Зал", "Мест в зале", "Продано", "Заполняемость, %",
                                 "Выручка, руб.", "Оплачено, руб."])
                for r in self.rows:
                    writer.writerow([f"{r['start_time']:%d.%m.%Y %H:%M}", r["title"], r["hall"], r["capacity"],
                                     r["sold"], round(100 * r["sold"] / r["capacity"]),
                                     f"{r['revenue']:.2f}".replace(".", ","), f"{r['paid']:.2f}".replace(".", ",")])
        except OSError as e:
            show_error(self, f"Не удалось сохранить файл: {e}")
            return
        show_info(self, f"Отчёт сохранён:\n{path}")


def money(value):
    return f"{value:,.0f} ₽".replace(",", " ")
