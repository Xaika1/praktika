import configparser
import sys
from pathlib import Path

DEFAULTS = {
    "host": "localhost",
    "port": "3306",
    "user": "root",
    "password": "",
    "database": "cinema",
}


def app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


def resource_path(name):
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / name
    return Path(__file__).resolve().parent.parent / name


CONFIG_FILE = app_dir() / "config.ini"


def load_settings():
    parser = configparser.ConfigParser()
    parser.read(CONFIG_FILE, encoding="utf-8")
    settings = dict(DEFAULTS)
    if parser.has_section("mysql"):
        settings.update(parser["mysql"])
    settings["port"] = int(settings["port"])
    return settings


def save_settings(settings):
    parser = configparser.ConfigParser()
    parser["mysql"] = {key: str(settings[key]) for key in DEFAULTS}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        parser.write(f)
