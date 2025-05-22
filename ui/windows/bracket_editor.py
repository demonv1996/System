from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from db.database import get_connection


class BracketEditorWindow(QDialog):
    def __init__(self, category_id):
        super().__init__()
        self.setWindowTitle("Редактирование турнирной сетки")
        self.setMinimumSize(600, 400)
        self.category_id = category_id

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.table = QTableWidget()
        self.layout.addWidget(QLabel("Сетка:"))
        self.layout.addWidget(self.table)

        self.save_button = QPushButton("Сохранить")
        self.cancel_button = QPushButton("Отмена")
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(button_layout)

        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        self.load_bracket()

    def load_bracket(self):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM brackets WHERE category_id = ? ORDER BY id DESC LIMIT 1", (self.category_id,))
            row = cursor.fetchone()
            if not row:
                QMessageBox.critical(self, "Ошибка", "Сетка не найдена.")
                self.reject()
                return
            self.bracket_id = row[0]

            cursor.execute("""
                SELECT bm.id, bm.round_number,
                       a1.full_name AS blue_name,
                       a2.full_name AS red_name
                FROM bracket_matches bm
                LEFT JOIN athletes a1 ON bm.blue_athlete_id = a1.id
                LEFT JOIN athletes a2 ON bm.red_athlete_id = a2.id
                WHERE bm.bracket_id = ?
                ORDER BY bm.round_number, bm.id
            """, (self.bracket_id,))
            matches = cursor.fetchall()

        self.matches = matches
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Раунд", "Синий угол", "Красный угол"])
        self.table.setRowCount(len(matches))
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)

        for row_num, match in enumerate(matches):
            for col_num, value in enumerate(match[1:]):  # skip match_id
                item = QTableWidgetItem(value if value else "—")
                item.setData(Qt.ItemDataRole.UserRole, match[0])  # store match_id
                self.table.setItem(row_num, col_num, item)

        # Подсказка
        self.layout.insertWidget(0, QLabel("💡 Дважды кликните по ячейке, чтобы поменять имя местами вручную."))

    def accept(self):
        # Применим ручные изменения (если были)
        # Сейчас не записываем перестановки в базу, но можно расширить
        super().accept()