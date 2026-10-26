import customtkinter as ctk

import validators as v
from ui import theme
from ui.widgets import DataTable, FormDialog, Page, ask

STATUSES = ["Все статусы", "Забронирован", "Оплачен"]


class TicketsPage(Page):
    title = "Билеты"
    subtitle = "Поиск проданных и забронированных билетов"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.search, self.search_var = self.search_entry(self.toolbar, "ФИО, телефон или фильм…", self.refresh, 300)
        self.search.pack(side="left")
        self.status = ctk.CTkSegmentedButton(self.toolbar, values=STATUSES, command=lambda _v: self.refresh(),
                                             height=36, font=theme.font(13))
        self.status.set(STATUSES[0])
        self.status.pack(side="left", padx=12)
        self.button(self.toolbar, "Отменить билет", self.cancel, "danger", 140).pack(side="right")
        self.button(self.toolbar, "Изменить", self.edit, "light", 110).pack(side="right", padx=8)

        self.table = DataTable(self.body, [
            ("session", "Сеанс", 130, "center"),
            ("title", "Фильм", 200, "w"),
            ("hall", "Зал", 80, "center"),
            ("place", "Ряд / место", 100, "center"),
            ("customer", "Покупатель", 170, "w"),
            ("phone", "Телефон", 140, "w"),
            ("price", "Цена", 80, "e"),
            ("status", "Статус", 120, "center"),
        ])
        self.table.pack(fill="both", expand=True)
        self.table.tree.tag_configure("booked", foreground=theme.PINK_HOVER)
        self.table.on_double_click(self.edit)
        self.count_label = ctk.CTkLabel(self, text="", font=theme.font(12), text_color=theme.TEXT_MUTED)
        self.count_label.pack(anchor="w", padx=30, pady=(0, 12))

    def refresh(self):
        status = self.status.get()
        status = None if status == STATUSES[0] else status
        tickets = self.run(lambda: self.repo.tickets(self.search_var.get().strip(), status))
        if tickets is None:
            return
        self.table.fill(tickets, lambda t: (
            f"{t['start_time']:%d.%m.%Y %H:%M}", t["title"], t["hall"], f"{t['row_num']} / {t['seat_num']}",
            t["customer_name"], t["customer_phone"], f"{t['price']:.0f} ₽", t["status"],
        ), lambda t: ["booked"] if t["status"] == "Забронирован" else [])
        suffix = " (показаны первые 1000)" if len(tickets) == 1000 else ""
        self.count_label.configure(text=f"Найдено билетов: {len(tickets)}{suffix}")

    def edit(self):
        ticket = self.table.selected()
        if ticket is None:
            self.app.toast("Сначала выберите билет в таблице")
            return
        fields = [
            ("name", "ФИО покупателя", "entry", ""),
            ("phone", "Телефон", "entry", ""),
            ("status", "Статус", "combo", STATUSES[1:]),
        ]
        initial = {"name": ticket["customer_name"], "phone": ticket["customer_phone"], "status": ticket["status"]}

        def validate(raw):
            return {"name": v.person_name(raw["name"]), "phone": v.phone(raw["phone"]), "status": raw["status"]}

        data = FormDialog(self, "Изменить билет", fields, initial, validate).show()
        if data:
            self.run(lambda: self.repo.update_ticket(ticket["id"], data["name"], data["phone"], data["status"]),
                     "Билет обновлён")
            self.refresh()

    def cancel(self):
        ticket = self.table.selected()
        if ticket is None:
            self.app.toast("Сначала выберите билет в таблице")
            return
        text = (f"Отменить билет на «{ticket['title']}» "
                f"({ticket['start_time']:%d.%m %H:%M}, ряд {ticket['row_num']}, место {ticket['seat_num']})?\n"
                f"Место снова станет свободным.")
        if ask(self, text, ok_text="Отменить билет"):
            self.run(lambda: self.repo.cancel_ticket(ticket["id"]), "Билет отменён")
            self.refresh()
