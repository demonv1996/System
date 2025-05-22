import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from db.database import initialize_database

# from ui.tabs.brackets_tab import BracketsTab


if __name__ == "__main__":
    app = QApplication(sys.argv)

    initialize_database()  # создаёт таблицы, если их нет
    window = MainWindow()
    window.show()

    # При запуске программы создадим сетку для категории ID 1 (если она есть)
    # generate_bracket(1)

    sys.exit(app.exec())
