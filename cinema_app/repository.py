from datetime import datetime, timedelta

from db import DatabaseError

CLEANING_BREAK_MIN = 15


class CinemaRepository:
    def __init__(self, db):
        self.db = db

    def genres(self):
        return self.db.fetch_all("SELECT id, name FROM genres ORDER BY name")

    def add_genre(self, name):
        return self.db.execute("INSERT INTO genres (name) VALUES (%s)", (name,))

    def movies(self, search="", genre_id=None):
        sql = """
            SELECT m.id, m.title, m.genre_id, g.name AS genre, m.duration_min,
                   m.age_rating, m.release_year, m.description
            FROM movies m
            JOIN genres g ON g.id = m.genre_id
            WHERE m.title LIKE %s
        """
        params = [f"%{search}%"]
        if genre_id:
            sql += " AND m.genre_id = %s"
            params.append(genre_id)
        sql += " ORDER BY m.title"
        return self.db.fetch_all(sql, params)

    def add_movie(self, data):
        return self.db.execute(
            """INSERT INTO movies (title, genre_id, duration_min, age_rating, release_year, description)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (data["title"], data["genre_id"], data["duration_min"], data["age_rating"],
             data["release_year"], data["description"]),
        )

    def update_movie(self, movie_id, data):
        self.db.execute(
            """UPDATE movies SET title = %s, genre_id = %s, duration_min = %s, age_rating = %s,
                      release_year = %s, description = %s
               WHERE id = %s""",
            (data["title"], data["genre_id"], data["duration_min"], data["age_rating"],
             data["release_year"], data["description"], movie_id),
        )

    def delete_movie(self, movie_id):
        self.db.execute("DELETE FROM movies WHERE id = %s", (movie_id,))

    def halls(self, search=""):
        return self.db.fetch_all(
            """SELECT h.id, h.name, h.hall_type, h.rows_count, h.seats_per_row,
                      h.rows_count * h.seats_per_row AS capacity,
                      (SELECT COUNT(*) FROM sessions s WHERE s.hall_id = h.id) AS sessions_count
               FROM halls h
               WHERE h.name LIKE %s OR h.hall_type LIKE %s
               ORDER BY h.name""",
            (f"%{search}%", f"%{search}%"),
        )

    def add_hall(self, data):
        return self.db.execute(
            "INSERT INTO halls (name, hall_type, rows_count, seats_per_row) VALUES (%s, %s, %s, %s)",
            (data["name"], data["hall_type"], data["rows_count"], data["seats_per_row"]),
        )

    def update_hall(self, hall_id, data):
        row = self.db.fetch_one(
            "SELECT MAX(row_num) AS max_row, MAX(seat_num) AS max_seat FROM tickets t "
            "JOIN sessions s ON s.id = t.session_id WHERE s.hall_id = %s",
            (hall_id,),
        )
        if row and row["max_row"] and (row["max_row"] > data["rows_count"] or row["max_seat"] > data["seats_per_row"]):
            raise DatabaseError("Нельзя уменьшить зал: на крайние места уже проданы билеты.")
        self.db.execute(
            "UPDATE halls SET name = %s, hall_type = %s, rows_count = %s, seats_per_row = %s WHERE id = %s",
            (data["name"], data["hall_type"], data["rows_count"], data["seats_per_row"], hall_id),
        )

    def delete_hall(self, hall_id):
        self.db.execute("DELETE FROM halls WHERE id = %s", (hall_id,))

    def sessions(self, date_from=None, date_to=None, movie_id=None, hall_id=None):
        sql = """
            SELECT s.id, s.movie_id, s.hall_id, s.start_time, s.price,
                   m.title, m.duration_min, h.name AS hall, h.hall_type,
                   h.rows_count * h.seats_per_row AS capacity,
                   COUNT(t.id) AS sold
            FROM sessions s
            JOIN movies m ON m.id = s.movie_id
            JOIN halls h ON h.id = s.hall_id
            LEFT JOIN tickets t ON t.session_id = s.id
            WHERE 1 = 1
        """
        params = []
        if date_from:
            sql += " AND s.start_time >= %s"
            params.append(date_from)
        if date_to:
            sql += " AND s.start_time < %s"
            params.append(date_to + timedelta(days=1))
        if movie_id:
            sql += " AND s.movie_id = %s"
            params.append(movie_id)
        if hall_id:
            sql += " AND s.hall_id = %s"
            params.append(hall_id)
        sql += " GROUP BY s.id ORDER BY s.start_time, h.name"
        return self.db.fetch_all(sql, params)

    def find_overlap(self, hall_id, start, duration, exclude_id=None):
        end = start + timedelta(minutes=duration + CLEANING_BREAK_MIN)
        sql = """
            SELECT s.id, s.start_time, m.title
            FROM sessions s
            JOIN movies m ON m.id = s.movie_id
            WHERE s.hall_id = %s
              AND s.start_time < %s
              AND DATE_ADD(s.start_time, INTERVAL m.duration_min + %s MINUTE) > %s
        """
        params = [hall_id, end, CLEANING_BREAK_MIN, start]
        if exclude_id:
            sql += " AND s.id <> %s"
            params.append(exclude_id)
        return self.db.fetch_one(sql, params)

    def check_session(self, data, exclude_id=None):
        movie = self.db.fetch_one("SELECT duration_min FROM movies WHERE id = %s", (data["movie_id"],))
        if movie is None:
            raise DatabaseError("Фильм не найден.")
        overlap = self.find_overlap(data["hall_id"], data["start_time"], movie["duration_min"], exclude_id)
        if overlap:
            raise DatabaseError(
                f"Зал занят: в {overlap['start_time']:%d.%m %H:%M} идёт «{overlap['title']}».\n"
                f"Между сеансами нужно {CLEANING_BREAK_MIN} минут на уборку."
            )

    def add_session(self, data):
        self.check_session(data)
        return self.db.execute(
            "INSERT INTO sessions (movie_id, hall_id, start_time, price) VALUES (%s, %s, %s, %s)",
            (data["movie_id"], data["hall_id"], data["start_time"], data["price"]),
        )

    def update_session(self, session_id, data):
        self.check_session(data, exclude_id=session_id)
        sold = self.db.fetch_one("SELECT COUNT(t.id) AS cnt, s.hall_id FROM sessions s "
                                 "LEFT JOIN tickets t ON t.session_id = s.id WHERE s.id = %s GROUP BY s.id",
                                 (session_id,))
        if sold and sold["cnt"] > 0 and sold["hall_id"] != data["hall_id"]:
            raise DatabaseError("На сеанс уже проданы билеты, поменять зал нельзя.")
        self.db.execute(
            "UPDATE sessions SET movie_id = %s, hall_id = %s, start_time = %s, price = %s WHERE id = %s",
            (data["movie_id"], data["hall_id"], data["start_time"], data["price"], session_id),
        )

    def delete_session(self, session_id):
        self.db.execute("DELETE FROM sessions WHERE id = %s", (session_id,))

    def session(self, session_id):
        return self.db.fetch_one(
            """SELECT s.id, s.start_time, s.price, m.title, m.duration_min, m.age_rating,
                      h.name AS hall, h.hall_type, h.rows_count, h.seats_per_row
               FROM sessions s
               JOIN movies m ON m.id = s.movie_id
               JOIN halls h ON h.id = s.hall_id
               WHERE s.id = %s""",
            (session_id,),
        )

    def taken_seats(self, session_id):
        rows = self.db.fetch_all(
            "SELECT id, row_num, seat_num, customer_name, customer_phone, status FROM tickets WHERE session_id = %s",
            (session_id,),
        )
        return {(r["row_num"], r["seat_num"]): r for r in rows}

    def book_seats(self, session_id, seats, customer_name, phone, paid):
        session = self.session(session_id)
        if session is None:
            raise DatabaseError("Сеанс не найден.")
        if session["start_time"] <= datetime.now():
            raise DatabaseError("Сеанс уже начался, продажа билетов на него закрыта.")
        status = "Оплачен" if paid else "Забронирован"
        rows = [(session_id, r, s, customer_name, phone, session["price"], status) for r, s in seats]
        try:
            self.db.execute_many(
                """INSERT INTO tickets (session_id, row_num, seat_num, customer_name, customer_phone, price, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                rows,
            )
        except DatabaseError as e:
            if e.code == 1062:
                raise DatabaseError("Одно из выбранных мест только что заняли. Обновите схему зала.", 1062) from e
            raise

    def tickets(self, search="", status=None, date_from=None, date_to=None):
        sql = """
            SELECT t.id, t.session_id, t.row_num, t.seat_num, t.customer_name, t.customer_phone,
                   t.price, t.status, t.created_at, s.start_time, m.title, h.name AS hall
            FROM tickets t
            JOIN sessions s ON s.id = t.session_id
            JOIN movies m ON m.id = s.movie_id
            JOIN halls h ON h.id = s.hall_id
            WHERE (t.customer_name LIKE %s OR t.customer_phone LIKE %s OR m.title LIKE %s)
        """
        like = f"%{search}%"
        params = [like, like, like]
        if status:
            sql += " AND t.status = %s"
            params.append(status)
        if date_from:
            sql += " AND s.start_time >= %s"
            params.append(date_from)
        if date_to:
            sql += " AND s.start_time < %s"
            params.append(date_to + timedelta(days=1))
        sql += " ORDER BY s.start_time DESC, t.row_num, t.seat_num LIMIT 1000"
        return self.db.fetch_all(sql, params)

    def update_ticket(self, ticket_id, customer_name, phone, status):
        self.db.execute(
            "UPDATE tickets SET customer_name = %s, customer_phone = %s, status = %s WHERE id = %s",
            (customer_name, phone, status, ticket_id),
        )

    def cancel_ticket(self, ticket_id):
        self.db.execute("DELETE FROM tickets WHERE id = %s", (ticket_id,))

    def revenue_by_sessions(self, date_from, date_to, movie_id=None):
        sql = """
            SELECT s.id, s.start_time, m.title, h.name AS hall,
                   h.rows_count * h.seats_per_row AS capacity,
                   COUNT(t.id) AS sold,
                   COALESCE(SUM(t.price), 0) AS revenue,
                   COALESCE(SUM(CASE WHEN t.status = 'Оплачен' THEN t.price END), 0) AS paid
            FROM sessions s
            JOIN movies m ON m.id = s.movie_id
            JOIN halls h ON h.id = s.hall_id
            LEFT JOIN tickets t ON t.session_id = s.id
            WHERE s.start_time >= %s AND s.start_time < %s
        """
        params = [date_from, date_to + timedelta(days=1)]
        if movie_id:
            sql += " AND s.movie_id = %s"
            params.append(movie_id)
        sql += " GROUP BY s.id ORDER BY s.start_time"
        return self.db.fetch_all(sql, params)

    def revenue_by_movies(self, date_from, date_to):
        return self.db.fetch_all(
            """SELECT m.title, COUNT(t.id) AS sold, COALESCE(SUM(t.price), 0) AS revenue
               FROM movies m
               JOIN sessions s ON s.movie_id = m.id
               LEFT JOIN tickets t ON t.session_id = s.id
               WHERE s.start_time >= %s AND s.start_time < %s
               GROUP BY m.id
               ORDER BY revenue DESC""",
            (date_from, date_to + timedelta(days=1)),
        )
