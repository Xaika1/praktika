import mysql.connector
from mysql.connector import errorcode

from config import resource_path

ERROR_TEXTS = {
    errorcode.ER_DUP_ENTRY: "Такая запись уже существует.",
    errorcode.ER_ROW_IS_REFERENCED_2: "Запись нельзя удалить: на неё ссылаются другие данные.",
    errorcode.ER_NO_REFERENCED_ROW_2: "Связанная запись не найдена.",
    errorcode.ER_ACCESS_DENIED_ERROR: "Неверный логин или пароль MySQL.",
    errorcode.ER_BAD_DB_ERROR: "База данных не найдена.",
    errorcode.CR_CONN_HOST_ERROR: "Не удалось подключиться к серверу MySQL. Проверьте, что он запущен.",
    errorcode.CR_CONNECTION_ERROR: "Не удалось подключиться к серверу MySQL. Проверьте, что он запущен.",
    errorcode.ER_CHECK_CONSTRAINT_VIOLATED: "Значение не прошло проверку в базе данных.",
}


class DatabaseError(Exception):
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code


def to_database_error(error):
    text = ERROR_TEXTS.get(error.errno, f"Ошибка базы данных: {error.msg}")
    return DatabaseError(text, error.errno)


class Database:
    def __init__(self, settings):
        self.settings = settings
        self.connection = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.settings["host"],
                port=self.settings["port"],
                user=self.settings["user"],
                password=self.settings["password"],
                database=self.settings["database"],
                charset="utf8mb4",
                collation="utf8mb4_unicode_ci",
                autocommit=False,
                connection_timeout=5,
            )
        except mysql.connector.Error as e:
            raise to_database_error(e) from e

    def close(self):
        if self.connection is not None and self.connection.is_connected():
            self.connection.close()

    def _cursor(self):
        if self.connection is None or not self.connection.is_connected():
            self.connect()
        return self.connection.cursor(dictionary=True)

    def fetch_all(self, sql, params=()):
        try:
            cursor = self._cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            cursor.close()
            self.connection.commit()
            return rows
        except mysql.connector.Error as e:
            raise to_database_error(e) from e

    def fetch_one(self, sql, params=()):
        rows = self.fetch_all(sql, params)
        return rows[0] if rows else None

    def execute(self, sql, params=()):
        try:
            cursor = self._cursor()
            cursor.execute(sql, params)
            self.connection.commit()
            last_id = cursor.lastrowid
            cursor.close()
            return last_id
        except mysql.connector.Error as e:
            self.connection.rollback()
            raise to_database_error(e) from e

    def execute_many(self, sql, rows):
        try:
            cursor = self._cursor()
            cursor.executemany(sql, rows)
            self.connection.commit()
            cursor.close()
        except mysql.connector.Error as e:
            self.connection.rollback()
            raise to_database_error(e) from e


def check_server(settings):
    try:
        conn = mysql.connector.connect(
            host=settings["host"],
            port=settings["port"],
            user=settings["user"],
            password=settings["password"],
            connection_timeout=5,
        )
    except mysql.connector.Error as e:
        raise to_database_error(e) from e
    cursor = conn.cursor()
    cursor.execute("SHOW DATABASES LIKE %s", (settings["database"],))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def split_sql(script):
    lines = [line for line in script.splitlines() if not line.strip().startswith("--")]
    statements = "\n".join(lines).split(";\n")
    return [s.strip() for s in statements if s.strip()]


def create_database(settings):
    script = resource_path("cinema.sql").read_text(encoding="utf-8")
    name = settings["database"]
    if name != "cinema":
        script = script.replace("DATABASE IF EXISTS cinema", f"DATABASE IF EXISTS `{name}`")
        script = script.replace("CREATE DATABASE cinema", f"CREATE DATABASE `{name}`")
        script = script.replace("USE cinema", f"USE `{name}`")
    try:
        conn = mysql.connector.connect(
            host=settings["host"],
            port=settings["port"],
            user=settings["user"],
            password=settings["password"],
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci",
        )
        cursor = conn.cursor()
        for statement in split_sql(script):
            cursor.execute(statement)
        conn.commit()
        conn.close()
    except mysql.connector.Error as e:
        raise to_database_error(e) from e
