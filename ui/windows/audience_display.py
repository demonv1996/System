import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPainter, QColor, QPainterPath, QScreen
from ui.tabs.scoreboard_tab import *
import json
import os


class AudienceDisplay(QWidget):
    def __init__(self):
        super().__init__()

        # self.resize(1200, 700)

        # крылья по умолчанию одного цвета, но теперь можно задавать их отдельно
        self.left_wing_color = QColor("blue")
        self.right_wing_color = QColor("red")

        # — Верхние судьи —
        self.judge_tl = self._make_score("0", size=160, font_size=72)
        self.judge_tr = self._make_score("0", size=160, font_size=72)

        # — Категория и раунд —
        self.lbl_cat = QLabel("Категория: СПАРРИНГ ДО 35 КГ", self)
        self.lbl_cat.setFont(QFont("Arial", 40))
        self.lbl_cat.setStyleSheet("color: white;")
        self.lbl_cat.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_round = QLabel("Раунд: 1", self)
        self.lbl_round.setFont(QFont("Arial", 40))
        self.lbl_round.setStyleSheet("color: white;")
        self.lbl_round.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # — Чуй — W — Чуй —
        self.lbl_chui_l = QLabel("0", self)
        self._style_chui(self.lbl_chui_l, 70)
        self.lbl_w = QLabel("W",    self)
        self._style_win(self.lbl_w,      70)
        self.lbl_chui_r = QLabel("0", self)
        self._style_chui(self.lbl_chui_r, 70)

        # — Таймер —
        self.time_label = QLabel("02:00", self)
        self.time_label.setFont(QFont("Arial", 120, QFont.Weight.Bold))
        self.time_label.setStyleSheet("color: white;")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # — YC row —
        self.lbl_score_l = QLabel("0",  self)
        self._style_chui(self.lbl_score_l, 70)      # белый
        self.lbl_yc = QLabel("YC", self)
        self._style_yc(self.lbl_yc, 70)             # жёлтый
        self.lbl_score_r = QLabel("0",  self)
        self._style_chui(self.lbl_score_r, 70)
        # — Спортсмены + линия + клуб —
        self.lbl_ath_l = QLabel("Петренко Артем", self)
        self._style_ath(self.lbl_ath_l, 40)
        self.line_l = QLabel(self)
        self._style_line(self.line_l)
        self.club_l = QLabel("BRUCE", self)
        self._style_club(self.club_l, 32)

        self.lbl_ath_r = QLabel("Магомедов Ислам", self)
        self._style_ath(self.lbl_ath_r, 40)
        self.line_r = QLabel(self)
        self._style_line(self.line_r)
        self.club_r = QLabel("AHMETOV TEAM", self)
        self._style_club(self.club_r, 32)

        # — Нижние судьи —
        self.judge_bl = self._make_score("0", size=160, font_size=72)
        self.judge_br = self._make_score("0", size=160, font_size=72)

        # — R1/R2 кнопки —
        def mk(txt):
            b = QPushButton(txt, self)
            b.setFixedSize(60, 60)
            b.setStyleSheet(
                "background-color: gray; color:white; font-size:18px; border-radius:30px;"
            )
            return b

        self.r1_l, self.r2_l = mk("R1"), mk("R2")
        self.r1_r, self.r2_r = mk("R1"), mk("R2")

        # Первичное позиционирование
        self._reposition_all()
        self.load_state_from_file()

        screens = QApplication.screens()
        if len(screens) > 1:
            second_screen = screens[1]
            geometry = second_screen.geometry()
            self.setGeometry(geometry)
            self.is_primery_screen = False
        else:
            self.setGeometry(QApplication.primaryScreen().geometry())
            self.is_primery_screen = True
        self.setWindowTitle("Табло для зрителей")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.showFullScreen()
        self.setFocus
        self.raise_()
        self.activateWindow()

    def keyPressEvent(self, event):
        if self.is_primery_screen and event.key() == Qt.Key.Key_Escape:
            self.close()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_all()

    def _reposition_all(self):
        W, H = self.width(), self.height()
        m = 20

        # Верхние судьи
        self.judge_tl.setGeometry(m, m, 144, 144)
        self.judge_tr.setGeometry(W - m - 144, m, 144, 144)

        # Категория и раунд
        self.lbl_cat.setGeometry(0, m + 10, W, 60)
        self.lbl_round.setGeometry(0, m + 10 + 60, W, 40)

        # Таймер
        self.time_label.adjustSize()
        tw, th = self.time_label.width(), self.time_label.height()
        tx = (W - tw) // 2
        ty = (H - th) // 2
        self.time_label.move(tx, ty)

        # Зазор для Чуй/YC
        gap = 40

        # Чуй — W — Чуй (над таймером)
        ch_y = ty - gap - self.lbl_chui_l.height()
        for lbl, frac in ((self.lbl_chui_l, 0.4),
                          (self.lbl_w,       0.5),
                          (self.lbl_chui_r, 0.6)):
            lbl.adjustSize()
            lbl.move(int(W*frac - lbl.width()/2), ch_y)

        # YC row (под таймером)
        yc_y = ty + th + gap
        for lbl, frac in ((self.lbl_score_l, 0.4),
                          (self.lbl_yc,      0.5),
                          (self.lbl_score_r, 0.6)):
            lbl.adjustSize()
            lbl.move(int(W*frac - lbl.width()/2), yc_y)

        # Спортсмены + линия + клуб (на уровне таймера)
        ath_w, ath_h = 450, 50
        y0 = ty
        self.lbl_ath_l.setGeometry(m, y0, ath_w, ath_h)
        self.line_l   .setGeometry(m, y0 + ath_h + 5, ath_w, 3)
        self.club_l   .setGeometry(m, y0 + ath_h + 8, ath_w, 40)

        self.lbl_ath_r.setGeometry(W - m - ath_w, y0, ath_w, ath_h)
        self.line_r   .setGeometry(W - m - ath_w, y0 + ath_h + 5, ath_w, 3)
        self.club_r   .setGeometry(W - m - ath_w, y0 + ath_h + 8, ath_w, 40)

        # R1/R2 под спортсменами
        ry = y0 + ath_h + 60
        # левый
        self.r1_l.move(m + 20, ry)
        self.r2_l.move(m + 90, ry)
        # правый симметрично
        btn_w = 60
        self.r1_r.move(W - (m + 20) - btn_w, ry)
        self.r2_r.move(W - (m + 90) - btn_w, ry)

        # Нижние судьи
        self.judge_bl.setGeometry(m, H - m - 144, 144, 144)
        self.judge_br.setGeometry(W - m - 144, H - m - 144, 144, 144)

    def paintEvent(self, event):
        p = QPainter(self)
        W, H = self.width(), self.height()

        # Вычисление границ, чтобы крылья не мешали
        gap = self.time_label.width()//2 + 60
        lx, rx = W/2 - gap, W/2 + gap
        r = 30

        # Фон
        p.fillRect(0, 0, W, H, QColor("black"))
        p.setPen(Qt.PenStyle.NoPen)

        # Левая лопасть
        p.setBrush(self.left_wing_color)
        path_l = QPainterPath()
        path_l.moveTo(0, r)
        path_l.quadTo(0, 0, r, 0)
        path_l.lineTo(lx - r, H/2 - r)
        path_l.quadTo(lx,     H/2, lx - r, H/2 + r)
        path_l.lineTo(r, H)
        path_l.quadTo(0, H, 0, H - r)
        path_l.closeSubpath()
        p.drawPath(path_l)

        # Правая лопасть
        p.setBrush(self.right_wing_color)
        path_r = QPainterPath()
        path_r.moveTo(W, r)
        path_r.quadTo(W, 0, W - r, 0)
        path_r.lineTo(rx + r, H/2 - r)
        path_r.quadTo(rx,     H/2, rx + r, H/2 + r)
        path_r.lineTo(W - r, H)
        path_r.quadTo(W, H, W, H - r)
        path_r.closeSubpath()
        p.drawPath(path_r)

    # — Вспомогательные стили —
    def _make_score(self, txt, size=144, font_size=50):
        lbl = QLabel(txt, self)
        lbl.setFont(QFont("Arial", font_size, QFont.Weight.Bold))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            "background-color: gray;"
            "color: white;"
            "border: 3px solid black;"
            "border-radius: 20px;"
        )
        lbl.setFixedSize(size, size)
        return lbl

    def _make_small_score(self, lbl):
        lbl.setFont(QFont("Arial", 36))
        lbl.setStyleSheet("color: white;")
        lbl.adjustSize()

    def _style_yc(self, lbl, font_size):
        lbl.setFont(QFont("Arial", font_size))
        lbl.setStyleSheet("color: yellow;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _style_chui(self, lbl, font_size):
        lbl.setFont(QFont("Arial", font_size))
        lbl.setStyleSheet("color: white;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _style_win(self, lbl, font_size):
        lbl.setFont(QFont("Arial", font_size))
        lbl.setStyleSheet("color: red;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _style_ath(self, lbl, font_size):
        lbl.setFont(QFont("Arial", font_size))
        lbl.setStyleSheet("color: white; background: transparent;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _style_line(self, lbl):
        lbl.setStyleSheet("background-color: white;")

    def _style_club(self, lbl, font_size):
        lbl.setFont(QFont("Arial", font_size))
        lbl.setStyleSheet("color: white;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def update_chui_yc(self, chui_red, chui_blue, yc_red, yc_blue):
        self.lbl_chui_l.setText(str(chui_red))
        self.lbl_chui_r.setText(str(chui_blue))
        self.lbl_score_l.setText(str(yc_red))
        self.lbl_score_r.setText(str(yc_blue))

    def update_r_buttons(self, r1_red, r2_red, r1_blue, r2_blue):
        self.r1_l.setStyleSheet(
            "background-color: green;" if r1_red else "background-color: gray;")
        self.r2_l.setStyleSheet(
            "background-color: green;" if r2_red else "background-color: gray;")
        self.r1_r.setStyleSheet(
            "background-color: green;" if r1_blue else "background-color: gray;")
        self.r2_r.setStyleSheet(
            "background-color: green;" if r2_blue else "background-color: gray;")

    def update_names(self, cat, round_num, name_red, club_red, name_blue, club_blue):
        self.lbl_cat.setText(f"Категория: {cat}")
        self.lbl_round.setText(f"Раунд: {round_num}")
        self.lbl_ath_l.setText(name_red)
        self.club_l.setText(club_red)
        self.lbl_ath_r.setText(name_blue)
        self.club_r.setText(club_blue)

    def update_judge_display(self, index, value: str, color: str):
        label = [self.judge_tl, self.judge_tr,
                 self.judge_bl, self.judge_br][index]
        label.setText(value)

        if color == "red":
            label.setStyleSheet(
                "background-color:red; color:white; font-size:70px; border-radius:15px; border: 2px solid black;")
        elif color == "blue":
            label.setStyleSheet(
                "background-color:blue; color:white; font-size:70px; border-radius:15px; border: 2px solid black;")
        else:
            label.setStyleSheet(
                "background-color:#AAAAAA; color:white; font-size:70px; border-radius:15px; border: 2px solid black;")

    def update_round_label(self, text: str):
        self.lbl_round.setText(text)

    def set_fight_finished(self):
        self.lbl_round.setText("Поединок завершён")

    def update_wing_colors(self, score_diff):
        red_votes = sum(1 for s in score_diff if s > 0)
        blue_votes = sum(1 for s in score_diff if s < 0)

        if red_votes >= 2 and red_votes > blue_votes:
            self.right_wing_color = QColor("red")  # Красный выигрывает
            self.left_wing_color = QColor("#111111")
        elif blue_votes >= 2 and blue_votes > red_votes:
            self.left_wing_color = QColor("blue")   # Синий выигрывает
            self.right_wing_color = QColor("#111111")
        elif red_votes == 2 and blue_votes == 2:
            # ничья 2:2
            self.left_wing_color = QColor("blue")
            self.right_wing_color = QColor("red")

        else:
            # Ничья или недостаточно голосов
            self.left_wing_color = QColor("blue")
            self.right_wing_color = QColor("red")

        self.update()

    def load_state_from_file(self):
        path = "match_state.json"
        if not os.path.exists(path):
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

    # Таймер и раунд
        self.time_label.setText(data.get("time_str", "00:00"))
        self.lbl_round.setText(data.get("round_str", "Раунд: 1"))

    # Категория и имена
        self.lbl_cat.setText(f"Категория: {data.get('category', '')}")
        self.lbl_ath_l.setText(data.get("name_red", ""))
        self.lbl_ath_r.setText(data.get("name_blue", ""))
        self.club_l.setText(data.get("club_red", ""))
        self.club_r.setText(data.get("club_blue", ""))

    # Чуй и YC
        self.lbl_chui_l.setText(str(data.get("chuy_red", 0)))
        self.lbl_chui_r.setText(str(data.get("chuy_blue", 0)))
        self.lbl_score_l.setText(str(data.get("yc_red", 0)))
        self.lbl_score_r.setText(str(data.get("yc_blue", 0)))

    # R1/R2
        self.r1_l.setStyleSheet(
            "background-color: gray;" if not data.get("r1_red", False) else "background-color: green;")
        self.r2_l.setStyleSheet(
            "background-color: gray;" if not data.get("r2_red", False) else "background-color: green;")
        self.r1_r.setStyleSheet(
            "background-color: gray;" if not data.get("r1_blue", False) else "background-color: green;")
        self.r2_r.setStyleSheet(
            "background-color: gray;" if not data.get("r2_blue", False) else "background-color: green;")

    # Судейские баллы и разрывы
        diffs = data.get("judge_diffs", [0, 0, 0, 0])
        self.judge_tl.setText(f"{abs(diffs[0]):+}")
        self.judge_tr.setText(f"{abs(diffs[1]):+}")
        self.judge_bl.setText(f"{abs(diffs[2]):+}")
        self.judge_br.setText(f"{abs(diffs[3]):+}")

        for i, (label, diff) in enumerate(zip(
            [self.judge_tl, self.judge_tr, self.judge_bl, self.judge_br], diffs
        )):
            if diff > 0:
                label.setStyleSheet(
                    "background-color: red; color: white; border: 2px solid black; font-size: 64px; font-weight: bold;")
            elif diff < 0:
                label.setStyleSheet(
                    "background-color: blue; color: white; border: 2px solid black; font-size: 64px; font-weight: bold;")
            else:
                label.setStyleSheet(
                    "background-color: lightgray; color: black; border: 2px solid black; font-size: 64px; font-weight: bold;")

    # Крылья
        wing_color = QColor("#e74c3c") if data.get("winner") == "red" else QColor(
            "#3498db") if data.get("winner") == "blue" else QColor("#111111")
        self.left_wing_color = wing_color if data.get(
            "winner") == "blue" else QColor("#111111")
        self.right_wing_color = wing_color if data.get(
            "winner") == "red" else QColor("#111111")

    def update_from_main(self, data):
        self.lbl_cat.setText(f"Категория: {data.get('category', 'Категория')}")
        self.lbl_round.setText(data.get('round_text', 'Раунд: 1'))
        self.time_label.setText(data.get('time', '00:00'))
        self.lbl_chui_l.setText(str(data.get('chuy_red', 0)))
        self.lbl_chui_r.setText(str(data.get('chuy_blue', 0)))
        self.lbl_score_l.setText(str(data.get('yc_red', 0)))
        self.lbl_score_r.setText(str(data.get('yc_blue', 0)))
        self.lbl_ath_l.setText(data.get('name_red', 'Спортсмен'))
        self.lbl_ath_r.setText(data.get('name_blue', 'Спортсмен'))
        self.club_l.setText(data.get('club_red', 'Клуб'))
        self.club_r.setText(data.get('club_blue', 'Клуб'))

        scores_red = data.get('scores_red', [0, 0, 0, 0])
        scores_blue = data.get('scores_blue', [0, 0, 0, 0])
        self.update_judges(scores_red, scores_blue)

    def update_judges(self, scores_red, scores_blue):
        self.judge_scores = []
        for i in range(4):
            diff = scores_red[i] - scores_blue[i]
            self.judge_scores.append(diff)

            label = [self.judge_tl, self.judge_tr,
                     self.judge_bl, self.judge_br][i]
            label.setText(str(abs(diff)))
            label.setFont(QFont("Arial", 48, QFont.Weight.Bold))
            if diff > 0:
                label.setStyleSheet(
                    "background-color: red; color: white; border: 2px solid black; font-size: 64px; font-weight: bold;")
            elif diff < 0:
                label.setStyleSheet(
                    "background-color: blue; color: white; border: 2px solid black; font-size: 64px; font-weight: bold;")
            else:
                label.setStyleSheet(
                    "background-color: lightgray; color: black; border: 2px solid black; font-size: 64px; font-weight: bold;")

    # Обновляем цвет крыльев в зависимости от большинства
        red_votes = sum(1 for d in self.judge_scores if d > 0)
        blue_votes = sum(1 for d in self.judge_scores if d < 0)

        if red_votes >= 2:
            self.right_wing_color = QColor("red")
            self.left_wing_color = QColor("#111111")
        elif blue_votes >= 2:
            self.left_wing_color = QColor("blue")
            self.right_wing_color = QColor("#111111")
        else:
            self.left_wing_color = QColor("blue")
            self.right_wing_color = QColor("red")

        self.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AudienceDisplay()
    win.show()
    sys.exit(app.exec())
