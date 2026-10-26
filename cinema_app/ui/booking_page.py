from datetime import date, datetime, timedelta

import customtkinter as ctk

import validators as v
from ui import theme
from ui.sessions_page import WEEKDAYS
from ui.widgets import FormDialog, MessageDialog, Page, show_info


class BookingPage(Page):
    title = "Бронирование"
    subtitle = "Выберите сеанс, отметьте свободные места и оформите билеты"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.day = date.today()
        self.session_map = {}
        self.session_id = None
        self.session = None
        self.taken = {}
        self.selected = set()
        self.seat_buttons = {}

        days = [date.today() + timedelta(days=i) for i in range(-2, 6)]
        self.day_map = {f"{WEEKDAYS[d.weekday()]} {d:%d.%m}": d for d in days}
        self.days = ctk.CTkSegmentedButton(self.toolbar, values=list(self.day_map), command=self.choose_day,
                                           height=36, font=theme.font(13))
        self.days.pack(side="left")
        self.days.set(f"{WEEKDAYS[self.day.weekday()]} {self.day:%d.%m}")
        self.session_box = ctk.CTkComboBox(self.toolbar, values=[], width=330, height=36, state="readonly",
                                           command=self.choose_session, font=theme.font(13),
                                           dropdown_font=theme.font(13))
        self.session_box.pack(side="left", padx=12)

        self.body.grid_columnconfigure(0, weight=1)
        self.body.grid_rowconfigure(0, weight=1)
        self.hall_card = ctk.CTkFrame(self.body, fg_color=theme.SURFACE, corner_radius=14, border_width=1,
                                      border_color=theme.BORDER)
        self.hall_card.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        self.side = ctk.CTkFrame(self.body, fg_color=theme.SURFACE, corner_radius=14, border_width=1,
                                 border_color=theme.BORDER, width=290)
        self.side.grid(row=0, column=1, sticky="ns")
        self.side.grid_propagate(False)
        self.build_side()

    def build_side(self):
        self.info_title = ctk.CTkLabel(self.side, text="Сеанс не выбран", font=theme.font(17, "bold"),
                                       wraplength=250, justify="left")
        self.info_title.pack(anchor="w", padx=20, pady=(20, 2))
        self.info_text = ctk.CTkLabel(self.side, text="", font=theme.font(13), text_color=theme.TEXT_MUTED,
                                      justify="left")
        self.info_text.pack(anchor="w", padx=20)

        legend = ctk.CTkFrame(self.side, fg_color=theme.BG, corner_radius=10)
        legend.pack(fill="x", padx=20, pady=16)
        for color, label in [
            (theme.PINK_SOFT, "свободно"),
            (theme.SEAT_SELECTED, "выбрано"),
            (theme.SEAT_TAKEN, "забронировано"),
            (theme.SEAT_PAID, "оплачено"),
        ]:
            row = ctk.CTkFrame(legend, fg_color="transparent")
            row.pack(anchor="w", padx=12, pady=3)
            ctk.CTkLabel(row, text="", width=18, height=18, fg_color=color, corner_radius=5).pack(side="left")
            ctk.CTkLabel(row, text=label, font=theme.font(12)).pack(side="left", padx=8)

        self.free_label = ctk.CTkLabel(self.side, text="", font=theme.font(13))
        self.free_label.pack(anchor="w", padx=20)
        ctk.CTkLabel(self.side, text="Выбранные места", font=theme.font(13, "bold")).pack(anchor="w", padx=20,
                                                                                         pady=(16, 4))
        self.selected_label = ctk.CTkLabel(self.side, text="—", font=theme.font(13), wraplength=250,
                                           justify="left", text_color=theme.TEXT_MUTED)
        self.selected_label.pack(anchor="w", padx=20)
        self.total_label = ctk.CTkLabel(self.side, text="0 ₽", font=theme.font(28, "bold"),
                                        text_color=theme.PINK)
        self.total_label.pack(anchor="w", padx=20, pady=(10, 0))

        self.book_button = ctk.CTkButton(self.side, text="Оформить билеты", height=42, font=theme.font(14, "bold"),
                                         command=self.book, state="disabled")
        self.book_button.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkButton(self.side, text="Сбросить выбор", height=36, fg_color=theme.PINK_SOFT,
                      hover_color=theme.PINK_LIGHT, text_color=theme.PINK_HOVER, font=theme.font(13),
                      command=self.clear_selection).pack(fill="x", padx=20)
        ctk.CTkLabel(self.side, text="Нажмите на занятое место,\nчтобы посмотреть или отменить билет.",
                     font=theme.font(11), text_color=theme.TEXT_MUTED, justify="left").pack(anchor="w", padx=20,
                                                                                           pady=16)

    def refresh(self):
        self.load_sessions()

    def choose_day(self, value):
        self.day = self.day_map[value]
        self.session_id = None
        self.load_sessions()

    def load_sessions(self):
        sessions = self.run(lambda: self.repo.sessions(self.day, self.day)) or []
        self.session_map = {}
        for s in sessions:
            label = f"{s['start_time']:%H:%M}  ·  {s['title']}  ·  {s['hall']}  ({s['capacity'] - s['sold']} своб.)"
            self.session_map[label] = s["id"]
        labels = list(self.session_map)
        self.session_box.configure(values=labels)
        if not labels:
            self.session_box.set("На этот день сеансов нет")
            self.session_id = None
            self.draw_hall()
            return
        upcoming = [lbl for lbl, s in zip(labels, sessions) if s["start_time"] > datetime.now()]
        default = upcoming[0] if upcoming else labels[0]
        current = next((lbl for lbl, sid in self.session_map.items() if sid == self.session_id), default)
        self.session_box.set(current)
        self.choose_session(current)

    def open_session(self, session_id):
        session = self.run(lambda: self.repo.session(session_id))
        if session is None:
            return
        self.day = session["start_time"].date()
        label = f"{WEEKDAYS[self.day.weekday()]} {self.day:%d.%m}"
        if label not in self.day_map:
            self.day_map[label] = self.day
            self.days.configure(values=list(self.day_map))
        self.days.set(label)
        self.session_id = session_id
        self.load_sessions()

    def choose_session(self, label):
        self.session_id = self.session_map.get(label)
        self.selected.clear()
        self.load_hall()

    def load_hall(self):
        if self.session_id is None:
            self.draw_hall()
            return
        self.session = self.run(lambda: self.repo.session(self.session_id))
        self.taken = self.run(lambda: self.repo.taken_seats(self.session_id)) or {}
        self.draw_hall()

    def draw_hall(self):
        for child in self.hall_card.winfo_children():
            child.destroy()
        self.seat_buttons = {}
        if self.session_id is None or self.session is None:
            self.info_title.configure(text="Сеанс не выбран")
            self.info_text.configure(text="")
            self.free_label.configure(text="")
            ctk.CTkLabel(self.hall_card, text="Выберите день и сеанс сверху", font=theme.font(15),
                         text_color=theme.TEXT_MUTED).place(relx=0.5, rely=0.5, anchor="center")
            self.update_summary()
            return

        s = self.session
        self.info_title.configure(text=f"{s['title']}  {s['age_rating']}")
        self.info_text.configure(text=f"{s['start_time']:%d.%m.%Y, %H:%M} · {s['duration_min']} мин\n"
                                      f"{s['hall']} ({s['hall_type']}) · {s['price']:.0f} ₽ за место")
        capacity = s["rows_count"] * s["seats_per_row"]
        self.free_label.configure(text=f"Свободно {capacity - len(self.taken)} из {capacity}")

        wrapper = ctk.CTkFrame(self.hall_card, fg_color="transparent")
        wrapper.place(relx=0.5, rely=0.5, anchor="center")
        size = 30 if s["seats_per_row"] <= 14 else 24
        screen = ctk.CTkFrame(wrapper, fg_color=theme.PINK_LIGHT, height=8, corner_radius=4)
        screen.grid(row=0, column=1, columnspan=s["seats_per_row"], sticky="ew", pady=(0, 2))
        ctk.CTkLabel(wrapper, text="ЭКРАН", font=theme.font(11), text_color=theme.TEXT_MUTED).grid(
            row=1, column=1, columnspan=s["seats_per_row"], pady=(0, 18))
        for r in range(1, s["rows_count"] + 1):
            ctk.CTkLabel(wrapper, text=str(r), width=26, font=theme.font(11), text_color=theme.TEXT_MUTED).grid(
                row=r + 1, column=0)
            for seat in range(1, s["seats_per_row"] + 1):
                button = ctk.CTkButton(wrapper, text=str(seat), width=size, height=size, corner_radius=7,
                                       font=theme.font(10), border_width=1,
                                       command=lambda place=(r, seat): self.click_seat(place))
                button.grid(row=r + 1, column=seat, padx=2, pady=2)
                self.seat_buttons[(r, seat)] = button
                self.paint_seat((r, seat))
            ctk.CTkLabel(wrapper, text=str(r), width=26, font=theme.font(11), text_color=theme.TEXT_MUTED).grid(
                row=r + 1, column=s["seats_per_row"] + 1)
        self.update_summary()

    def paint_seat(self, place):
        button = self.seat_buttons[place]
        if place in self.taken:
            color = theme.SEAT_PAID if self.taken[place]["status"] == "Оплачен" else theme.SEAT_TAKEN
            button.configure(fg_color=color, hover_color=color, border_color=color, text_color="#FFFFFF")
        elif place in self.selected:
            button.configure(fg_color=theme.PINK, hover_color=theme.PINK_HOVER, border_color=theme.PINK,
                             text_color="#FFFFFF")
        else:
            button.configure(fg_color=theme.PINK_SOFT, hover_color=theme.PINK_LIGHT, border_color=theme.PINK_LIGHT,
                             text_color=theme.TEXT)

    def click_seat(self, place):
        if place in self.taken:
            self.show_ticket(place)
            return
        if place in self.selected:
            self.selected.remove(place)
        else:
            if len(self.selected) >= 10:
                self.app.toast("За один раз можно оформить не больше 10 мест")
                return
            self.selected.add(place)
        self.paint_seat(place)
        self.update_summary()

    def clear_selection(self):
        places = list(self.selected)
        self.selected.clear()
        for place in places:
            self.paint_seat(place)
        self.update_summary()

    def update_summary(self):
        if not self.selected or self.session is None:
            self.selected_label.configure(text="—")
            self.total_label.configure(text="0 ₽")
            self.book_button.configure(state="disabled")
            return
        places = sorted(self.selected)
        self.selected_label.configure(text=", ".join(f"ряд {r} место {s}" for r, s in places))
        self.total_label.configure(text=f"{self.session['price'] * len(places):.0f} ₽")
        self.book_button.configure(state="normal")

    def book(self):
        if not self.selected:
            return
        places = sorted(self.selected)
        fields = [
            ("name", "ФИО покупателя", "entry", "Например: Иванова Анна"),
            ("phone", "Телефон", "entry", "+7 912 345-67-89"),
            ("paid", "Оплата", "check", "Билеты оплачены сразу"),
        ]

        def validate(raw):
            return {"name": v.person_name(raw["name"]), "phone": v.phone(raw["phone"]), "paid": raw["paid"]}

        total = self.session["price"] * len(places)
        data = FormDialog(self, f"Оформление: {len(places)} мест на {total:.0f} ₽", fields, validate=validate,
                          ok_text="Оформить").show()
        if not data:
            return
        result = self.run(lambda: self.repo.book_seats(self.session_id, places, data["name"], data["phone"],
                                                       data["paid"]) or True)
        self.selected.clear()
        self.load_hall()
        if result:
            seats = ", ".join(f"{r}/{s}" for r, s in places)
            show_info(self, f"Билеты оформлены на имя {data['name']}.\nРяд/место: {seats}\nСумма: {total:.0f} ₽")
            self.load_sessions()

    def show_ticket(self, place):
        ticket = self.taken[place]
        text = (f"Ряд {place[0]}, место {place[1]}\n"
                f"Покупатель: {ticket['customer_name']}\n"
                f"Телефон: {ticket['customer_phone']}\n"
                f"Статус: {ticket['status']}")
        dialog = MessageDialog(self, "Билет", text, kind="question", ask=True, ok_text="Отменить билет")
        if dialog.show():
            if self.run(lambda: self.repo.cancel_ticket(ticket["id"]) or True, "Бронь отменена"):
                self.load_sessions()
