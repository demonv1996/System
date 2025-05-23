# если используешь свою функцию, оставь как есть
import math
from logic.brackets import generate_bracket
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QPen, QFont, QPainter, QLinearGradient
from PyQt6.QtWidgets import (
    QDialog, QGraphicsScene, QGraphicsView, QVBoxLayout, QPushButton, QHBoxLayout, QMessageBox
)
import random
import sqlite3


def get_connection():
    return sqlite3.connect("database.db")  # путь к твоей базе


def get_athlete(athlete):
    name = f"{athlete['full_name']}"
    club = f"({athlete['club']})" if athlete['club'] else ""
    return f"{name} {club}"


def get_athletes_by_category(category_id):
    # Подгоняем под твою структуру: берем full_name и club
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT a.id, a.full_name, COALESCE(c.name, '') as club
            FROM athletes AS a
            LEFT JOIN clubs c ON a.club_id = c.id
            JOIN category_athletes ca ON ca.athlete_id = a.id
            WHERE ca.category_id = ?
            ORDER BY a.full_name
        """, (category_id,))
        return [
            {"id": row[0], "full_name": row[1], "club": row[2]}
            for row in cur.fetchall()
        ]


def get_category_name(category_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM categories WHERE id = ?", (category_id,))
        row = cur.fetchone()
        return row[0] if row else ""


# from athletes_tab import get_athletes_by_category
# from categories_tab import get_category_name


class BracketViewerWindow(QDialog):
    def __init__(self, category_id, bracket, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Турнирная сетка")
        self.category_id = category_id
        # self.bracket = bracket
        self.athletes = get_athletes_by_category(self.category_id)
        # self.bracket = generate_bracket(self.athletes)
        self.slots = bracket

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.swap_btn = QPushButton("Поменять местами")
        self.swap_btn.clicked.connect(self.swap_selected)
        self.randomize_btn = QPushButton("Разбить пулю случайно")
        self.randomize_btn.clicked.connect(self.randomize)
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save)

        top = QHBoxLayout()
        top.addWidget(self.swap_btn)
        top.addWidget(self.randomize_btn)
        top.addWidget(self.save_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.view)

        self.selected_indexes = []
        self.load_data()

    def load_data(self):
        self.athletes = get_athletes_by_category(self.category_id)
        self.category_name = get_category_name(self.category_id)
        self.original_athletes = list(self.athletes)
        self.make_bracket()
        self.draw_bracket()

    def make_bracket(self):
        n = len(self.athletes)
        if n <= 8:
            self.size = 8
        elif n <= 16:
            self.size = 16
        elif n <= 32:
            self.size = 32
        else:
            self.size = 64
        if self.slots is None:
            self.slots = [None for _ in range(self.size)]
            self.slots[:n] = self.athletes

        self.rounds = int(math.log2(self.size))

    def draw_bracket(self):
        self.scene.clear()
        block_width = 180
        block_height = 40
        v_spacing = 30

        positions = {}

        # Название категории сверху
        title = f"{self.category_name} (Спортсменов: {len([a for a in self.slots if a])})"
        self.scene.addText(title, QFont(
            "Arial", 18, QFont.Weight.Bold)).setPos(0, 0)
        y_offset = 45

        # Подписи раундов
        round_labels = {
            3: ['1/4', '1/2', 'Финал'],
            4: ['1/8', '1/4', '1/2', 'Финал'],
            5: ['1/16', '1/8', '1/4', '1/2', 'Финал'],
            6: ['1/32', '1/16', '1/8', '1/4', '1/2', 'Финал'],
        }
        labels = round_labels.get(self.rounds, ['1/4', '1/2', 'Финал'])
        for r, text in enumerate(labels):
            t = self.scene.addText(text, QFont("Arial", 12))
            t.setDefaultTextColor(QColor("black"))
            t.setPos(30 + r * (block_width + 40), y_offset - 32)

        # Позиции
        x0 = 30
        y0 = y_offset + 10
        x_step = block_width + 50

        y_positions = {}
        for r in range(self.rounds + 1):
            count = self.size // (2 ** r)
            for i in range(count):
                x = x0 + r * x_step
                if r == 0:
                    y = y0 + i * (block_height + v_spacing)
                else:
                    prev1 = y_positions[(r-1, i*2)]
                    prev2 = y_positions[(r-1, i*2+1)]
                    y = (prev1 + prev2) / 2
                y_positions[(r, i)] = y

                # Градиенты
                if r == 0:
                    color1 = QColor(255, 90, 90, 120) if i % 2 == 0 else QColor(
                        80, 180, 255, 120)
                elif r == self.rounds:
                    # Золото (только финал)
                    color1 = QColor(255, 225, 50, 180)
                else:
                    color1 = QColor(255, 90, 90, 120) if i % 2 == 0 else QColor(
                        80, 180, 255, 120)
                rect = self.scene.addRect(x, y, block_width, block_height)
                gradient = QBrush(color1)
                rect.setBrush(gradient)
                rect.setPen(QPen(Qt.GlobalColor.black, 2))


# Создание прямоугольника


# # Прямоугольник
#                 rect = self.scene.addRect(x, y, block_width, block_height)

# # Горизонтальный градиент (слева направо)
#                 gradient = QLinearGradient(x, y, x + block_width, y)

#                 if r == 0:
#                     if i % 2 == 0:
#                         # Красный только на первых 10%
#                         gradient.setColorAt(0.0, QColor(255, 90, 90, 255))
#                         gradient.setColorAt(0.05, QColor(255, 90, 90, 255))
#                         gradient.setColorAt(0.1001, QColor(255, 90, 90, 0))
#                         gradient.setColorAt(1.0, QColor(255, 90, 90, 0))
#                     else:
#                         # Синий только на первых 10%
#                         gradient.setColorAt(0.0, QColor(80, 180, 255, 255))
#                         gradient.setColorAt(0.05, QColor(80, 180, 255, 255))
#                         gradient.setColorAt(0.1001, QColor(80, 180, 255, 0))
#                         gradient.setColorAt(1.0, QColor(80, 180, 255, 0))
#                 elif r == self.rounds:
#                     # Золотой (финал)
#                     gradient.setColorAt(0.0, QColor(255, 225, 50, 255))
#                     gradient.setColorAt(0.05, QColor(255, 225, 50, 255))
#                     gradient.setColorAt(0.1001, QColor(255, 225, 50, 0))
#                     gradient.setColorAt(1.0, QColor(255, 225, 50, 0))
#                 else:
#                     if i % 2 == 0:
#                         gradient.setColorAt(0.0, QColor(255, 90, 90, 255))
#                         gradient.setColorAt(0.05, QColor(255, 90, 90, 255))
#                         gradient.setColorAt(0.1001, QColor(255, 90, 90, 0))
#                         gradient.setColorAt(1.0, QColor(255, 90, 90, 0))
#                     else:
#                         gradient.setColorAt(0.0, QColor(80, 180, 255, 255))
#                         gradient.setColorAt(0.05, QColor(80, 180, 255, 255))
#                         gradient.setColorAt(0.1001, QColor(80, 180, 255, 0))
#                         gradient.setColorAt(1.0, QColor(80, 180, 255, 0))

# # Заливка
#                 rect.setBrush(QBrush(gradient))
#                 rect.setPen(QPen(Qt.GlobalColor.black, 2))

                # Текст спортсмена/bye/победителя
                # Текст спортсмена/bye/победителя
                text = ""
                if r == 0:
                    athlete = self.slots[i]
                    # Если участник есть и у него есть пара — пишем имя
                    if athlete:
                        # Проверяем, есть ли пара (i четный — смотрим i+1, i нечетный — смотрим i-1)
                        has_pair = False
                        if i % 2 == 0:
                            has_pair = (i + 1 < len(self.slots)
                                        and self.slots[i + 1] is not None)
                        else:
                            has_pair = (
                                i - 1 >= 0 and self.slots[i - 1] is not None)
                        if has_pair:
                            if isinstance(self.slots[i], dict):
                                text = get_athlete(athlete)
                        else:
                            text = ""  # Пустой блок если нет пары
                    else:
                        text = ""
                elif r == 1 and len([a for a in self.slots if a]) <= 3:
                    left = self.slots[i * 2]
                    right = self.slots[i * 2 + 1]
                    # Если один есть, а другой пустой — проходит тот, кто есть
                    if left is not None and right is None:
                        self.slots[i] = left
                        text = get_athlete(left)
                    elif left is None and right is not None:
                        self.slots[i] = right
                        text = get_athlete(right)

                    elif left is not None and right is not None:
                        # Обычная пара, победитель будет выбран по ходу турнира
                        text = " "  # Можно ничего не выводить, или писать "ПОБЕДИТЕЛЬ"
                    else:
                        self.slots[i] = None
                        text = " "  # оба пустые
                else:
                    if (self.slots[i * 2] is None) and not (self.slots[i * 2 + 1] is None):
                        self.slots[i] = self.slots[i * 2 + 1]
                        text = get_athlete(self.slots[i])
                    elif not (self.slots[i * 2] is None) and (self.slots[i * 2 + 1] is None):
                        self.slots[i] = self.slots[i * 2]
                        text = get_athlete(self.slots[i])
                    else:
                        self.slots[i] = ' '
                label = self.scene.addText(
                    text, QFont("Arial", 11, QFont.Weight.Bold))
                label.setDefaultTextColor(Qt.GlobalColor.black)
                label.setPos(x + 10, y + 6)
                positions[(r, i)] = (x, y, rect, label)
        # Линии между блоками
        # for r in range(self.rounds):
        #     count = self.size // (2 ** r)
        #     for i in range(count):
        #         x, y, _, _ = positions[(r, i)]
        #         x1 = x + block_width
        #         y1 = y + block_height / 2
        #         x2, y2, _, _ = positions[(r + 1, i // 2)]
        #         # До левого края следующего блока
                pen = QPen(QColor(80, 80, 80), 2)
        #         self.scene.addLine(x1, y1, x2, y2 + block_height / 2, pen)

        hor_len = 30  # длина горизонтальной линии

        for r in range(self.rounds):
            count = self.size // (2 ** r)
            for i in range(count):
                x, y, rect, label = positions[(r, i)]
                # 1. Горизонтальная линия от блока спортсмена
                x_hor_end = x + block_width + hor_len
                self.scene.addLine(
                    x + block_width, y + block_height // 2, x_hor_end, y + block_height // 2, pen)

                # 2. Вертикальная линия между парой (только для чётных i)
                if r < self.rounds - 1 and i % 2 == 0 and i + 1 < count:
                    _, y2, _, _ = positions[(r, i + 1)]
                    y1 = y + block_height // 2
                    y2 = y2 + block_height // 2
                    # Если хотя бы один блок не пустой, рисуем вертикальную
                    if self.slots[i] or self.slots[i + 1]:
                        self.scene.addLine(x_hor_end, y1, x_hor_end, y2, pen)

                        # 3. Горизонтальная линия к победителю (следующий раунд)
                        next_x, next_y, _, _ = positions[(r + 1, i // 2)]
                        y_c = (y1 + y2) // 2
                        self.scene.addLine(
                            x_hor_end, y_c, next_x, next_y + block_height // 2, pen)
        if r == self.rounds - 1:
            # Только для финала
            final_x = x0 + (self.rounds) * x_step
            final_y_top = positions[(r, 0)][1] + block_height // 2
            final_y_bottom = positions[(
                r, 1)][1] + block_height // 2

            # Длина горизонтальных отрезков
            hor_len_final = 0

    # 1. Горизонтальные линии от полуфиналов
            self.scene.addLine(
                final_x - hor_len_final, final_y_top, final_x, final_y_top, pen
            )
            self.scene.addLine(
                final_x - hor_len_final, final_y_bottom, final_x, final_y_bottom, pen
            )
    # 2. Вертикальная линия к победителю
            final_y_center = (final_y_top + final_y_bottom) // 2
            self.scene.addLine(
                final_x-20, final_y_top, final_x-20, final_y_bottom, pen
            )
    # 3. Горизонтальная линия к победителю
            self.scene.addLine(
                final_x-20, final_y_center, final_x + hor_len_final, final_y_center, pen
            )

    def swap_selected(self):
        if len(self.selected_indexes) == 2:
            i1, i2 = self.selected_indexes
            self.slots[i1], self.slots[i2] = self.slots[i2], self.slots[i1]
            self.selected_indexes = []
            self.draw_bracket()
        else:
            QMessageBox.warning(
                self, "Выберите", "Выберите двух спортсменов для замены.")

    def randomize(self):
        if not hasattr(self, 'athletes_all'):
            self.athletes_all = [a for a in self.slots if isinstance(
                a, dict) and 'full_name' in a]

        athletes = list(self.athletes_all)
        random.shuffle(athletes)

        self.athletes = athletes

        n = len(self.athletes)
        if n <= 8:
            self.size = 8
        elif n <= 16:
            self.size = 16
        elif n <= 32:
            self.size = 32
        else:
            self.size = 64

        self.slots = [None for _ in range(self.size)]
        self.slots[:n] = self.athletes
        self.rounds = int(math.log2(self.size))

        self.draw_bracket()

    def save(self):
        QMessageBox.information(
            self, "Сохранено", "Сетка сохранена!")  # Заглушка
