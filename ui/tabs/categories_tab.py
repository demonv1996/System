import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QDialog, QMessageBox, QListWidget, QListWidgetItem, QCompleter
)
from PyQt6.QtCore import Qt
from db.database import get_connection, initialize_database
from logic.brackets import generate_bracket
from ui.windows.bracket_viewer import BracketViewerWindow, get_athletes_by_category


class CategoriesTab(QWidget):
    def __init__(self):
        super().__init__()
        initialize_database()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.init_add_form()
        self.init_table()
        self.init_assignment_section()

        self.load_categories()
        self.load_categories_select()
        self.load_athletes_select()

    def init_add_form(self):
        form_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Название категории")

        self.add_button = QPushButton("Добавить")
        self.add_button.clicked.connect(self.add_category)

        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.add_button)
        self.delete_all_button = QPushButton("Удалить все категории")
        self.delete_all_button.clicked.connect(self.delete_all_categories)
        form_layout.addWidget(self.delete_all_button)
        form_layout.addWidget(self.delete_all_button)
        self.layout.addLayout(form_layout)

    def init_table(self):
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Категория", "Участников", "Участники", "Редактировать", "Разбить на сетку", "Удалить"
        ])
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

        self.layout.addWidget(QLabel("Список категорий:"))
        self.layout.addWidget(self.table)

    def init_assignment_section(self):
        group = QHBoxLayout()

        self.category_select = QComboBox()
        self.athlete_select = QComboBox()
        self.assign_button = QPushButton("Добавить в категорию")
        self.assign_button.clicked.connect(self.assign_athlete_to_category)

        group.addWidget(self.category_select)
        group.addWidget(self.athlete_select)
        group.addWidget(self.assign_button)

        self.layout.addLayout(group)

    def load_categories(self):
        self.table.setRowCount(0)
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.name,
                       COUNT(ca.athlete_id) as participant_count
                FROM categories c
                LEFT JOIN category_athletes ca ON c.id = ca.category_id
                GROUP BY c.id, c.name
            """)
            for row_data in cursor.fetchall():
                row_number = self.table.rowCount()
                self.table.insertRow(row_number)

                self.table.setItem(
                    row_number, 0, QTableWidgetItem(row_data[1]))
                self.table.setItem(
                    row_number, 1, QTableWidgetItem(str(row_data[2])))

                # "Участники"
                open_button = QPushButton("Открыть")
                open_button.clicked.connect(
                    lambda _, cid=row_data[0], cname=row_data[1]: self.open_participants_dialog(cid, cname))
                self.table.setCellWidget(row_number, 2, open_button)

                edit_button = QPushButton("Редактировать")
                # delete_button = QPushButton("Удалить")
                edit_button.clicked.connect(
                    lambda _, cid=row_data[0], cname=row_data[1]: self.edit_category_dialog(cid, cname))
                self.table.setCellWidget(row_number, 3, edit_button)
                # self.table.setCellWidget(row_number, 4, delete_button)

                # "Разбить на сетку"
                bracket_button = QPushButton("Разбить на сетку")
                bracket_button.clicked.connect(
                    lambda _, cid=row_data[0]: self.create_and_show_bracket(cid))
                self.table.setCellWidget(row_number, 4, bracket_button)

                delete_button = QPushButton("Удалить")
                delete_button.clicked.connect(
                    lambda _, cid=row_data[0]: self.delete_category(cid))
                self.table.setCellWidget(row_number, 5, delete_button)

    def load_categories_select(self):
        self.category_select.clear()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM categories")
            for row in cursor.fetchall():
                self.category_select.addItem(row[1], userData=row[0])

    def load_athletes_select(self):
        self.athlete_select.clear()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, full_name FROM athletes")
            for row in cursor.fetchall():
                self.athlete_select.addItem(row[1], userData=row[0])

    def add_category(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(
                self, "Ошибка", "Название не может быть пустым.")
            return
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
            conn.commit()
        self.name_input.clear()
        self.load_categories()
        self.load_categories_select()

    def assign_athlete_to_category(self):
        category_id = self.category_select.currentData()
        athlete_id = self.athlete_select.currentData()
        if not category_id or not athlete_id:
            return
        with get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO category_athletes (category_id, athlete_id)
                    VALUES (?, ?)
                """, (category_id, athlete_id))
                conn.commit()
            except Exception as e:
                print("Ошибка при добавлении:", e)
        self.load_categories()

    def create_and_show_bracket(self, category_id):

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM bracket_matches WHERE bracket_id IN (SELECT id FROM brackets WHERE category_id = ?)", (category_id,))
            cursor.execute(
                "DELETE FROM brackets WHERE category_id = ?", (category_id,))
            conn.commit()
        # generate_bracket(category_id)
        athletes = get_athletes_by_category(category_id)
        bracket = generate_bracket(athletes)

        dialog = BracketViewerWindow(category_id, bracket=bracket)
        dialog.exec()

    def open_participants_dialog(self, category_id: int, category_name: str):
        """Окно со списком участников выбранной категории и возможностью добавлять / удалять."""
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Участники: {category_name}")
        lay = QVBoxLayout(dlg)

        list_widget = QListWidget()
        lay.addWidget(list_widget)

        # ── Кнопка «Удалить выбранного» ─────────────────────────────
        del_btn = QPushButton("Удалить выбранного")
        lay.addWidget(del_btn)

        # ── Блок «Добавить спортсмена» ──────────────────────────────
        add_box = QHBoxLayout()
        self.search_line = QLineEdit()
        self.search_line.setPlaceholderText("Фамилия или имя")
        add_btn = QPushButton("Добавить спортсмена")
        add_box.addWidget(self.search_line)
        add_box.addWidget(add_btn)
        lay.addLayout(add_box)

        # ------------------------------------------------------------

        def refresh_list():
            list_widget.clear()
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT a.id, a.full_name, a.birth_date, c.name, a.belt
                    FROM category_athletes ca
                    JOIN athletes a ON ca.athlete_id = a.id
                    LEFT JOIN clubs c ON a.club_id = c.id
                    WHERE ca.category_id = ?
                    ORDER BY a.full_name
                """, (category_id,))
                for i, (aid, full_name, birth, club, belt) in enumerate(cur.fetchall(), 1):
                    txt = f"{i}. {full_name} | Д.р.: {birth or '–'} | Клуб: {club or '–'} | Пояс: {belt or '–'}"
                    item = QListWidgetItem(txt)
                    item.setData(Qt.ItemDataRole.UserRole, aid)
                    list_widget.addItem(item)

        # ---------- completer для поиска свободных спортсменов -----
        def update_completer():
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT full_name
                    FROM athletes
                    WHERE id NOT IN (SELECT athlete_id FROM category_athletes WHERE category_id = ?)
                    ORDER BY full_name
                """, (category_id,))
                names = [row[0] for row in cur.fetchall()]
            comp = QCompleter(names, self)
            comp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self.search_line.setCompleter(comp)

        # ---------- обработчики кнопок ------------------------------
        def add_athlete_to_category():
            name = self.search_line.text().strip()
            if not name:
                return
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT id FROM athletes WHERE full_name = ?", (name,))
                row = cur.fetchone()
                if not row:
                    QMessageBox.warning(dlg, "Не найдено",
                                        "Нет такого спортсмена.")
                    return
                ath_id = row[0]
                try:
                    cur.execute("INSERT INTO category_athletes(category_id, athlete_id) VALUES(?,?)",
                                (category_id, ath_id))
                    conn.commit()
                except Exception:
                    pass  # уже в категории
            self.search_line.clear()
            refresh_list()
            update_completer()
            self.load_categories()

        def delete_selected():
            it = list_widget.currentItem()
            if not it:
                return
            aid = it.data(Qt.ItemDataRole.UserRole)
            if QMessageBox.question(dlg, "Удалить", "Удалить выбранного?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) \
                    != QMessageBox.StandardButton.Yes:
                return
            with get_connection() as conn:
                conn.execute("DELETE FROM category_athletes WHERE category_id = ? AND athlete_id = ?",
                             (category_id, aid))
                conn.commit()
            refresh_list()
            update_completer()
            self.load_categories()

        # ---------- связываем ----------
        del_btn.clicked.connect(delete_selected)
        add_btn.clicked.connect(add_athlete_to_category)

        refresh_list()
        update_completer()
        dlg.exec()

        def delete_selected():
            selected_item = list_widget.currentItem()
            if selected_item:
                athlete_id = selected_item.data(Qt.ItemDataRole.UserRole)
                reply = QMessageBox.question(dlg, "Подтвердить", f"Удалить участника?",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            DELETE FROM category_athletes WHERE category_id = ? AND athlete_id = ?
                        """, (category_id, athlete_id))
                        conn.commit()
                    list_widget.takeItem(list_widget.row(selected_item))
                    self.load_categories()

        del_btn.clicked.connect(delete_selected)
        dlg.exec()

    def edit_category_dialog(self, category_id, current_name):
        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать категорию")
        layout = QVBoxLayout(dialog)

        name_input = QLineEdit()
        name_input.setText(current_name)
        layout.addWidget(QLabel("Новое название:"))
        layout.addWidget(name_input)

        save_button = QPushButton("Сохранить")
        layout.addWidget(save_button)

        def save_changes():
            new_name = name_input.text().strip()
            if new_name:
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE categories SET name = ? WHERE id = ?", (new_name, category_id))
                    conn.commit()
                dialog.accept()
                self.load_categories()
            else:
                QMessageBox.warning(
                    dialog, "Ошибка", "Название не может быть пустым.")

        save_button.clicked.connect(save_changes)
        dialog.exec()

    def delete_category(self, category_id):
        from db.database import get_connection
        reply = QMessageBox.question(self, "Удалить категорию", "Вы уверены, что хотите удалить эту категорию?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM categories WHERE id = ?", (category_id,))
                cursor.execute(
                    "DELETE FROM category_athletes WHERE category_id = ?", (category_id,))
                cursor.execute(
                    "DELETE FROM brackets WHERE category_id = ?", (category_id,))
                conn.commit()
            self.load_categories()

    def delete_all_categories(self):
        from db.database import get_connection
        reply = QMessageBox.question(self, "Удалить все категории", "Вы точно хотите удалить ВСЕ категории?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM categories")
                cursor.execute("DELETE FROM category_athletes")
                cursor.execute("DELETE FROM brackets")
                conn.commit()
            self.load_categories()

    def delete_category(self, category_id):
        reply = QMessageBox.question(self, "Удаление", "Вы точно хотите удалить категорию?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM categories WHERE id = ?", (category_id,))
                cursor.execute(
                    "DELETE FROM category_athletes WHERE category_id = ?", (category_id,))
                cursor.execute(
                    "DELETE FROM brackets WHERE category_id = ?", (category_id,))
                conn.commit()
            self.load_categories()
