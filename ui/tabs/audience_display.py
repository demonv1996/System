import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPainter, QColor, QPainterPath
from ui.tabs.scoreboard_tab import *


class AudienceDisplay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Табло для зрителей")
        self.resize(1200, 700)

        # крылья по умолчанию одного цвета, но теперь можно задавать их отдельно
        self.left_wing_color = QColor("#111111")
        self.right_wing_color = QColor("#111111")

        # — Верхние судьи —
        self.judge_tl = self._make_score("0", size=144, font_size=72)
        self.judge_tr = self._make_score("0", size=144, font_size=72)

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
        self.judge_bl = self._make_score("0", size=144, font_size=72)
        self.judge_br = self._make_score("0", size=144, font_size=72)

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
    def _make_score(self, txt, size=120, font_size=36):
        lbl = QLabel(txt, self)
        lbl.setFont(QFont("Arial", font_size))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            "background-color: lightgray;"
            "border-radius:15px; border:1px solid black;"
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AudienceDisplay()
    win.show()
    sys.exit(app.exec())
