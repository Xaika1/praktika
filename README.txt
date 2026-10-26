Бронирование билетов в кинотеатр
Учебная практика УП.02, индивидуальное задание № 11

Состав
  cinema_app/        исходный код (Python 3.12, CustomTkinter, mysql-connector-python)
  cinema.sql         структура базы данных MySQL и тестовые данные
  requirements.txt   библиотеки
  cinema.spec        настройки сборки PyInstaller
  build_exe.bat      сборка Cinema.exe на Windows
  .vscode/           задачи сборки и запуска для VS Code
  screenshots/       скриншоты программы

Быстрый старт (готовый exe)
  1. Установить MySQL Server 8.0 (https://dev.mysql.com/downloads/installer/)
     и запомнить пароль пользователя root.
  2. Запустить Cinema.exe.
  3. Если пароль root не пустой, откроется окно «Подключение к MySQL»:
     ввести пароль и нажать «Подключиться». Настройки сохранятся в config.ini
     рядом с программой.
  4. Программа предложит создать базу cinema с демонстрационными данными —
     нажать «Создать».

Запуск из исходников
  pip install -r requirements.txt
  python cinema_app/main.py

Создание базы вручную (по желанию)
  mysql -u root -p < cinema.sql

Сборка exe (PyInstaller)
  В VS Code: открыть папку проекта, Терминал -> Запустить задачу ->
  «Установить библиотеки», затем Ctrl+Shift+B («Собрать exe (PyInstaller)»).
  То же самое без VS Code: python -m PyInstaller --noconfirm cinema.spec
  или двойной щелчок по build_exe.bat.
  Готовый файл появится в папке dist (на Windows — Cinema.exe).
