from PyInstaller.utils.hooks import collect_data_files

a = Analysis(
    ["cinema_app/main.py"],
    pathex=["cinema_app"],
    datas=[("cinema.sql", ".")] + collect_data_files("customtkinter"),
    hiddenimports=["mysql.connector.locales.eng.client_error", "mysql.connector.plugins.mysql_native_password",
                   "mysql.connector.plugins.caching_sha2_password"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="Cinema",
    console=False,
    upx=False,
)
