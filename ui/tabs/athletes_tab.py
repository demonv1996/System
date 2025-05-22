from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QGroupBox, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt
from db.database import get_connection


class AthletesTab(QWidget):
    def __init__(self) -> None:
        super().__init__()

        # ─── Основной layout ───────────────────────────────────────────────
        self.layout = QVBoxLayout(self)

        # ─── Форма добавления клуба ────────────────────────────────────────
        self.init_club_box()

        # ─── Форма добавления спортсмена ───────────────────────────────────
        self.init_athlete_box()

        # ─── Поиск по ФИО ──────────────────────────────────────────────────
        self.init_search_bar()

        # ─── Таблица спортсменов ───────────────────────────────────────────
        self.init_table()

        # ─── Кнопки «Выделить / Удалить выбранных» ─────────────────────────
        self.init_mass_buttons()

        # ─── Первичная загрузка данных ─────────────────────────────────────
        self.load_clubs()
        self.load_athletes()

    # ╭───────────────────────── UI‑блоки ─────────────────────────╮
    def init_club_box(self):
        box = QGroupBox("Добавить клуб")
        lay = QHBoxLayout(box)

        self.club_name_input = QLineEdit()
        self.club_name_input.setPlaceholderText("Название клуба")
        self.club_city_input = QLineEdit()
        self.club_city_input.setPlaceholderText("Город")

        add_btn = QPushButton("Добавить клуб")
        add_btn.clicked.connect(self.add_club)

        lay.addWidget(self.club_name_input)
        lay.addWidget(self.club_city_input)
        lay.addWidget(add_btn)

        self.layout.addWidget(box)

    def init_athlete_box(self):
        box = QGroupBox("Добавить спортсмена")
        lay = QHBoxLayout(box)

        self.ath_name = QLineEdit()
        self.ath_name.setPlaceholderText("ФИО")
        self.ath_birth = QLineEdit()
        self.ath_birth.setPlaceholderText("Дата рождения YYYY‑MM‑DD")
        self.ath_belt = QLineEdit()
        self.ath_belt.setPlaceholderText("Пояс (гып)")
        self.club_drop = QComboBox()

        add_btn = QPushButton("Добавить спортсмена")
        add_btn.clicked.connect(self.add_athlete)

        for w in (self.ath_name, self.ath_birth, self.ath_belt, self.club_drop, add_btn):
            lay.addWidget(w)

        self.layout.addWidget(box)

    def init_search_bar(self):
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по ФИО")
        self.search_input.textChanged.connect(self.load_athletes)
        self.layout.addWidget(self.search_input)

    def init_table(self):
        self.table = QTableWidget()
        self.table.setColumnCount(6)   # ✓  ФИО  Д.р.  Клуб  Город  Удалить
        self.table.setHorizontalHeaderLabels(
            ["✓", "ФИО", "Дата рождения", "Клуб", "Город", "Удалить"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        for col in range(1, 5):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSortingEnabled(True)
        self.layout.addWidget(QLabel("Список спортсменов:"))
        self.layout.addWidget(self.table)

    def init_mass_buttons(self):
        h = QHBoxLayout()
        self.select_all_btn = QPushButton("Выделить всех")
        self.select_all_btn.clicked.connect(self.select_all)
        self.delete_sel_btn = QPushButton("Удалить выбранных")
        self.delete_sel_btn.clicked.connect(self.delete_selected)
        h.addWidget(self.select_all_btn)
        h.addWidget(self.delete_sel_btn)
        self.layout.addLayout(h)
    # ╰────────────────────────────────────────────────────────────╯

    # ╭───────────────────── Загрузка данных ─────────────────────╮
    def load_clubs(self):
        self.club_drop.clear()
        with get_connection() as conn:
            for cid, name in conn.execute("SELECT id, name FROM clubs").fetchall():
                self.club_drop.addItem(name, cid)

    def load_athletes(self):
        """Перезаполняет таблицу с учётом текста поиска."""
        search = self.search_input.text().lower().strip()

        self.table.setRowCount(0)
        qry = """
            SELECT a.id, a.full_name, a.birth_date,
                   COALESCE(c.name,''), COALESCE(c.city,'')
            FROM athletes a
            LEFT JOIN clubs c ON a.club_id = c.id
        """
        with get_connection() as conn:
            for aid, full_name, birth, club, city in conn.execute(qry).fetchall():

                if search and search not in full_name.lower():
                    continue

                row = self.table.rowCount()
                self.table.insertRow(row)

                # чек‑бокс
                cb = QTableWidgetItem()
                cb.setFlags(Qt.ItemFlag.ItemIsUserCheckable |
                            Qt.ItemFlag.ItemIsEnabled)
                cb.setCheckState(Qt.CheckState.Unchecked)
                self.table.setItem(row, 0, cb)

                # данные
                for col, val in enumerate((full_name, birth, club, city), start=1):
                    self.table.setItem(row, col, QTableWidgetItem(str(val)))

                # кнопка удаления
                btn = QPushButton("Удалить")
                btn.clicked.connect(
                    lambda _, a_id=aid: self.delete_single(a_id))
                self.table.setCellWidget(row, 5, btn)
    # ╰────────────────────────────────────────────────────────────╯

    # ╭──────────────────────── CRUD ──────────────────────────────╮
    def add_club(self):
        name, city = self.club_name_input.text().strip(), self.club_city_input.text().strip()
        if not name:
            QMessageBox.warning(
                self, "Ошибка", "Название клуба не может быть пустым.")
            return
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO clubs(name,city) VALUES (?,?)", (name, city))
            conn.commit()
        self.club_name_input.clear()
        self.club_city_input.clear()
        self.load_clubs()

    def add_athlete(self):
        name = self.ath_name.text().strip()
        birth = self.ath_birth.text().strip()
        belt = self.ath_belt.text().strip()
        club = self.club_drop.currentData()
        if not name:
            QMessageBox.warning(self, "Ошибка", "ФИО не может быть пустым.")
            return
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO athletes(full_name, birth_date, weight, club_id, belt)
                VALUES (?, ?, NULL, ?, ?)
            """, (name, birth, club, belt))
            conn.commit()
        self.ath_name.clear()
        self.ath_birth.clear()
        self.ath_belt.clear()
        self.load_athletes()

    def delete_single(self, athlete_id: int):
        if QMessageBox.question(self, "Удалить", "Удалить спортсмена?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) \
                != QMessageBox.StandardButton.Yes:
            return
        with get_connection() as conn:
            conn.execute(
                "DELETE FROM category_athletes WHERE athlete_id = ?", (athlete_id,))
            conn.execute("DELETE FROM athletes WHERE id = ?", (athlete_id,))
            conn.commit()
        self.load_athletes()
    # ╰────────────────────────────────────────────────────────────╯

    # ╭────────────────── Массовые операции ──────────────────────╮
    def select_all(self):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)

    def delete_selected(self):
        ids = []
        for row in range(self.table.rowCount()):
            cb = self.table.item(row, 0)
            if cb and cb.checkState() == Qt.CheckState.Checked:
                full_name = self.table.item(row, 1).text()
                ids.append(full_name)

        if not ids:
            QMessageBox.information(
                self, "Нет выбора", "Отметьте хотя бы одного спортсмена.")
            return

        if QMessageBox.question(self, "Удалить",
                                f"Удалить {len(ids)} спортсменов?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) \
                != QMessageBox.StandardButton.Yes:
            return

        with get_connection() as conn:
            for name in ids:
                conn.execute("DELETE FROM category_athletes WHERE athlete_id IN "
                             "(SELECT id FROM athletes WHERE full_name = ?)", (name,))
                conn.execute(
                    "DELETE FROM athletes WHERE full_name = ?", (name,))
            conn.commit()
        self.load_athletes()
    # ╰────────────────────────────────────────────────────────────╯
