import validators as v
from ui.widgets import DataTable, FormDialog, Page, ask

HALL_TYPES = ["Обычный", "VIP", "IMAX"]


class HallsPage(Page):
    title = "Залы"
    subtitle = "Кинозалы и их вместимость"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.search, self.search_var = self.search_entry(self.toolbar, "Поиск по названию или типу…", self.refresh)
        self.search.pack(side="left")
        self.button(self.toolbar, "Удалить", self.delete, "danger", 100).pack(side="right")
        self.button(self.toolbar, "Изменить", self.edit, "light", 110).pack(side="right", padx=8)
        self.button(self.toolbar, "+ Добавить", self.add, width=130).pack(side="right")

        self.table = DataTable(self.body, [
            ("name", "Зал", 160, "w"),
            ("type", "Тип", 120, "center"),
            ("rows", "Рядов", 90, "center"),
            ("seats", "Мест в ряду", 110, "center"),
            ("capacity", "Всего мест", 110, "center"),
            ("sessions", "Сеансов", 90, "center"),
        ])
        self.table.pack(fill="both", expand=True)
        self.table.on_double_click(self.edit)

    def refresh(self):
        halls = self.run(lambda: self.repo.halls(self.search_var.get().strip()))
        if halls is None:
            return
        self.table.fill(halls, lambda h: (
            h["name"], h["hall_type"], h["rows_count"], h["seats_per_row"], h["capacity"], h["sessions_count"],
        ))

    def form(self, title, initial=None):
        fields = [
            ("name", "Название зала", "entry", "Например: Зал 4"),
            ("hall_type", "Тип зала", "combo", HALL_TYPES),
            ("rows_count", "Количество рядов", "entry", "от 1 до 30"),
            ("seats_per_row", "Мест в ряду", "entry", "от 1 до 40"),
        ]

        def validate(raw):
            return {
                "name": v.text(raw["name"], "Название зала", 50),
                "hall_type": raw["hall_type"],
                "rows_count": v.integer(raw["rows_count"], "Количество рядов", 1, 30),
                "seats_per_row": v.integer(raw["seats_per_row"], "Мест в ряду", 1, 40),
            }

        return FormDialog(self, title, fields, initial, validate).show()

    def add(self):
        data = self.form("Новый зал")
        if data and self.run(lambda: self.repo.add_hall(data), "Зал добавлен") is not None:
            self.refresh()

    def edit(self):
        hall = self.table.selected()
        if hall is None:
            self.app.toast("Сначала выберите зал в таблице")
            return
        data = self.form("Изменить зал", hall)
        if data:
            self.run(lambda: self.repo.update_hall(hall["id"], data), "Изменения сохранены")
            self.refresh()

    def delete(self):
        hall = self.table.selected()
        if hall is None:
            self.app.toast("Сначала выберите зал в таблице")
            return
        if ask(self, f"Удалить «{hall['name']}»?", ok_text="Удалить"):
            self.run(lambda: self.repo.delete_hall(hall["id"]), "Зал удалён")
            self.refresh()
