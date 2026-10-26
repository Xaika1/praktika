import customtkinter as ctk

import validators as v
from ui import theme
from ui.widgets import DataTable, FormDialog, Page, ask

AGE_RATINGS = ["0+", "6+", "12+", "16+", "18+"]
ALL_GENRES = "Все жанры"


class MoviesPage(Page):
    title = "Фильмы"
    subtitle = "Каталог фильмов, которые идут в кинотеатре"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.genre_map = {}
        self.search, self.search_var = self.search_entry(self.toolbar, "Поиск по названию…", self.refresh)
        self.search.pack(side="left")
        self.genre_filter = ctk.CTkComboBox(self.toolbar, values=[ALL_GENRES], width=170, height=36,
                                            state="readonly", command=lambda _v: self.refresh(),
                                            font=theme.font(13), dropdown_font=theme.font(13))
        self.genre_filter.set(ALL_GENRES)
        self.genre_filter.pack(side="left", padx=10)
        self.button(self.toolbar, "Удалить", self.delete, "danger", 100).pack(side="right")
        self.button(self.toolbar, "Изменить", self.edit, "light", 110).pack(side="right", padx=8)
        self.button(self.toolbar, "+ Добавить", self.add, width=130).pack(side="right")
        self.button(self.toolbar, "+ Жанр", self.add_genre, "light", 90).pack(side="right", padx=8)

        self.table = DataTable(self.body, [
            ("title", "Название", 260, "w"),
            ("genre", "Жанр", 120, "w"),
            ("duration", "Длительность", 110, "center"),
            ("age", "Возраст", 80, "center"),
            ("year", "Год", 70, "center"),
            ("description", "Описание", 320, "w"),
        ])
        self.table.pack(fill="both", expand=True)
        self.table.on_double_click(self.edit)

    def load_genres(self):
        genres = self.run(self.repo.genres) or []
        self.genre_map = {g["name"]: g["id"] for g in genres}
        current = self.genre_filter.get()
        self.genre_filter.configure(values=[ALL_GENRES] + list(self.genre_map))
        if current not in self.genre_map:
            self.genre_filter.set(ALL_GENRES)

    def refresh(self):
        if not self.genre_map:
            self.load_genres()
        genre_id = self.genre_map.get(self.genre_filter.get())
        movies = self.run(lambda: self.repo.movies(self.search_var.get().strip(), genre_id))
        if movies is None:
            return
        self.table.fill(movies, lambda m: (
            m["title"], m["genre"], f"{m['duration_min']} мин", m["age_rating"], m["release_year"],
            (m["description"] or "")[:60],
        ))

    def form(self, title, initial=None):
        self.load_genres()
        fields = [
            ("title", "Название", "entry", "Например: Интерстеллар"),
            ("genre", "Жанр", "combo", list(self.genre_map)),
            ("duration_min", "Длительность, мин", "entry", "от 1 до 400"),
            ("age_rating", "Возрастное ограничение", "combo", AGE_RATINGS),
            ("release_year", "Год выпуска", "entry", "Например: 2024"),
            ("description", "Описание", "textbox", None),
        ]

        def validate(raw):
            return {
                "title": v.text(raw["title"], "Название", 150),
                "genre_id": self.genre_map[v.required(raw["genre"], "Жанр")],
                "duration_min": v.integer(raw["duration_min"], "Длительность", 1, 400),
                "age_rating": raw["age_rating"],
                "release_year": v.integer(raw["release_year"], "Год выпуска", 1895, 2100),
                "description": raw["description"][:2000],
            }

        return FormDialog(self, title, fields, initial, validate).show()

    def add(self):
        data = self.form("Новый фильм")
        if data and self.run(lambda: self.repo.add_movie(data), "Фильм добавлен") is not None:
            self.refresh()

    def edit(self):
        movie = self.table.selected()
        if movie is None:
            self.app.toast("Сначала выберите фильм в таблице")
            return
        initial = dict(movie, genre=movie["genre"])
        data = self.form("Изменить фильм", initial)
        if data:
            self.run(lambda: self.repo.update_movie(movie["id"], data), "Изменения сохранены")
            self.refresh()

    def delete(self):
        movie = self.table.selected()
        if movie is None:
            self.app.toast("Сначала выберите фильм в таблице")
            return
        if ask(self, f"Удалить фильм «{movie['title']}»?", ok_text="Удалить"):
            self.run(lambda: self.repo.delete_movie(movie["id"]), "Фильм удалён")
            self.refresh()

    def add_genre(self):
        data = FormDialog(self, "Новый жанр", [("name", "Название жанра", "entry", "Например: Ужасы")],
                          validate=lambda raw: {"name": v.text(raw["name"], "Название жанра", 50)}).show()
        if data and self.run(lambda: self.repo.add_genre(data["name"]), "Жанр добавлен") is not None:
            self.genre_map = {}
            self.refresh()
