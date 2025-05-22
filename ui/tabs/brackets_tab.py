from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt
from db.database import get_connection
from ui.windows.bracket_viewer import BracketViewerWindow


class BracketsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        self.layout.addWidget(QLabel("Сформированные сетки по категориям:"))

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Категория", "Участников", "Открыть", "Действия"])
        header = self.table.horizontalHeader()

# 0 — Категория (максимально занимает свободное место)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

# 1 — Участников (минимальная ширина по содержимому)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

# 2, 3, 4 — кнопки (минимальная ширина по содержимому)
        for col in range(2, 5):
            header.setSectionResizeMode(
                col, QHeaderView.ResizeMode.ResizeToContents)

# 5 — кнопка «Удалить» (минимальная ширина по содержимому)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setColumnWidth(0, 300)
        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.clicked.connect(self.load_brackets)
        self.layout.addWidget(self.refresh_button)
        self.layout.addWidget(self.table)

        self.load_brackets()

    def load_brackets(self):
        self.table.setRowCount(0)
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.id, c.name, c.id,
                       (SELECT COUNT(*) FROM category_athletes WHERE category_id = c.id)
                FROM brackets b
                JOIN categories c ON b.category_id = c.id
                GROUP BY b.id
            """)
            brackets = cursor.fetchall()

        for row_num, (bracket_id, category_name, category_id, athlete_count) in enumerate(brackets):
            self.table.insertRow(row_num)
            self.table.setItem(row_num, 0, QTableWidgetItem(category_name))
            self.table.setItem(
                row_num, 1, QTableWidgetItem(str(athlete_count)))

            # Кнопка "Открыть"
            open_btn = QPushButton("Открыть")
            open_btn.clicked.connect(
                lambda _, cid=category_id: self.open_bracket(cid))
            self.table.setCellWidget(row_num, 2, open_btn)

            # Кнопки "Удалить" и "Запустить"
            actions_layout = QHBoxLayout()
            actions_widget = QWidget()
            delete_btn = QPushButton("Удалить")
            delete_btn.clicked.connect(
                lambda _, bid=bracket_id: self.delete_bracket(bid))

            launch_btn = QPushButton("Запустить")
            launch_btn.clicked.connect(
                lambda _, cid=category_id: self.launch_bracket(cid))

            actions_layout.addWidget(delete_btn)
            actions_layout.addWidget(launch_btn)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_widget.setLayout(actions_layout)
            self.table.setCellWidget(row_num, 3, actions_widget)

    def open_bracket(self, category_id):
        dialog = BracketViewerWindow(category_id)
        dialog.exec()

    def delete_bracket(self, bracket_id):
        reply = QMessageBox.question(self, "Удалить сетку", "Вы уверены, что хотите удалить сетку?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM bracket_matches WHERE bracket_id = ?", (bracket_id,))
                cursor.execute(
                    "DELETE FROM brackets WHERE id = ?", (bracket_id,))
                conn.commit()
            self.load_brackets()

    def launch_bracket(self, category_id):
        QMessageBox.information(
            self, "Запуск", f"Бой по категории ID {category_id} будет запущен (функция в разработке).")
