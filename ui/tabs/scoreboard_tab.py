from PyQt6.QtWidgets import QApplication
from ui.windows.settings_dialog import SettingsDialog
from ui.windows.audience_display import AudienceDisplay
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QGridLayout, QVBoxLayout, QHBoxLayout,
    QFrame, QDialog, QApplication
)
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QGridLayout, QVBoxLayout, QHBoxLayout,
    QFrame, QDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from ui.windows.audience_display import AudienceDisplay
from ui.windows.settings_dialog import SettingsDialog
import requests
import socket
import winsound
import threading


class ClickableButton(QPushButton):
    rightClicked = pyqtSignal()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.RightButton:
            self.rightClicked.emit()
        else:
            super().mousePressEvent(e)


class ScoreboardTab(QWidget):
    def __init__(self):
        super().__init__()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_scoreboard)
        self.timer.start(600)
        self.settings = {'round_time': 15, 'rest_time': 13, 'num_rounds': 2}
        self.original_settings = dict(self.settings)
        self.scores_red = [0, 0, 0, 0]
        self.scores_blue = [0, 0, 0, 0]
        self.previous_scores_red = [0, 0, 0, 0]
        self.previous_scores_blue = [0, 0, 0, 0]
        self.chuy_red = 0
        self.chuy_blue = 0
        self.yc_red = 0
        self.yc_blue = 0
        self.r1_red = False
        self.r2_red = False
        self.r1_blue = False
        self.r2_blue = False
        self.name_red = 'Спортсмен'
        self.name_blue = 'Спортсмен'
        self.club_red = 'Клуб'
        self.club_blue = 'Клуб'
        self.category = 'Категория'
        self.raund = 1
        self.extra_active = False
        self.style_btn = ("""
        QPushButton {
            background-color: white;
            color: black;
            font-size: 14px;
            border-radius: 10px;
            padding: 5px 10px;
        }
        QPushButton:hover {
            background-color: black;
                          color: white
        }
        QPushButton:pressed {
            background-color: #d39e00;
        }
    """)

        # состояние таймера
        self.current_round = 1
        self.phase = 'stopped'  # 'stopped', 'round', 'rest'
        self.remaining = self.settings['round_time']

        # Qt‑таймер
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(5)

        # Верхняя панель
        top = QHBoxLayout()
        self.btn_show = QPushButton("Показать экран")
        self.btn_show.setStyleSheet(self.style_btn)
        # self.btn_hide = QPushButton("Скрыть экран")
        # self.btn_hide.setStyleSheet(self.style_btn)
        # self.btn_hide.clicked.connect(self.off_show_screen)
        # self.btn_hide.hide()
        self.btn_show.clicked.connect(self.on_show_screen)
        self.btn_reset = QPushButton("Сброс")
        self.btn_reset.setStyleSheet(self.style_btn)
        self.btn_reset.clicked.connect(self.all_reset)
        self.btn_sett = QPushButton("Настройки")
        self.btn_sett.setStyleSheet(self.style_btn)
        self.btn_sett.clicked.connect(self.open_settings)
        self.btn_extra = QPushButton("Экстра раунд")
        self.btn_extra.clicked.connect(self.extra_raund)
        self.btn_extra.setStyleSheet(self.style_btn)

        top.addWidget(self.btn_show)
        # top.addWidget(self.btn_hide)
        top.addStretch()
        top.addWidget(self.btn_reset)
        top.addWidget(self.btn_sett)
        top.addWidget(self.btn_extra)
        main_layout.addLayout(top)

        # Категория и раунд
        cat_lbl = QLabel(self.category)
        cat_lbl.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        cat_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(cat_lbl)
        self.round_lbl = QLabel(
            f"Раунд {self.current_round}/{self.settings['num_rounds']}")
        self.round_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.round_lbl)

        # Имена + таймер
        names = QHBoxLayout()
        lcol = QVBoxLayout()
        lcol.addWidget(self._make_name(f"{self.name_red} ({self.club_red})"))
        lcol.addWidget(self._make_line("red"))
        names.addLayout(lcol)

        tcol = QVBoxLayout()
        tro = QHBoxLayout()
        self.btn_start = QPushButton("Старт")
        self.btn_start.setFixedHeight(40)
        self.btn_start.setFont(QFont('Arial', 20))
        self.btn_start.setStyleSheet(
            """QPushButton{ background:white;color:black;border:1px solid black;padding:6px;border-radius:6px;}
            QPushButton:hover {
            background-color: black;
                          color: white}""")
        self.btn_start.clicked.connect(self.start_timer)

        self.btn_stop = QPushButton("Стоп")
        self.btn_stop.setFixedHeight(40)
        self.btn_stop.setFont(QFont('Arial', 20))
        self.btn_stop.setStyleSheet("""QPushButton{ background:white;color:black;border:1px solid black;padding:6px;border-radius:6px;}
            QPushButton:hover {
            background-color: black;
                          color: white}""")
        self.btn_stop.clicked.connect(self.stop_timer)
        self.btn_stop.hide()

        self.time_lbl = QLabel(self._format_time(self.remaining))
        self.time_lbl.setFixedHeight(40)
        self.time_lbl.setFont(QFont('Arial', 20))
        self.time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_lbl.setStyleSheet(
            "background:white;color:black;border:1px solid black;padding:6px;border-radius:6px;")

        tro.addWidget(self.btn_start)
        tro.addWidget(self.btn_stop)
        tro.addWidget(self.time_lbl)
        tro.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tcol.addLayout(tro)
        tcol.addWidget(self.round_lbl)
        names.addLayout(tcol)
        # main_layout.addLayout(names)

        rcol = QVBoxLayout()
        rcol.addWidget(self._make_name(f"{self.name_blue} ({self.club_blue})"))
        rcol.addWidget(self._make_line("#5AA9E6"))
        names.addLayout(rcol)
        main_layout.addLayout(names)

        # Панель судей
        panel = QGridLayout()
        panel.setHorizontalSpacing(50)
        panel.setVerticalSpacing(10)
        self.judge_red_labels = []
        self.judge_blue_labels = []
        for i in range(4):
            r = self.scores_red[i]
            b = self.scores_blue[i]
            rc, bc = "#DDDDDD", "#DDDDDD"
            if r > b:
                rc = "#FF6666"
            elif b > r:
                bc = "#6699FF"

            lbl_r = self._make_score(str(r), rc)
            lbl_b = self._make_score(str(b), bc)
            panel.addWidget(lbl_r, i, 1)
            panel.addWidget(lbl_b, i, 2)
            self.judge_red_labels.append(lbl_r)
            self.judge_blue_labels.append(lbl_b)

        # Чуй/YC и R1/R2 кнопки
        red_ctrl = QGridLayout()
        self.btn_w_r = ClickableButton(f"W:{self.chuy_red}", )
        self.btn_w_r.setFixedSize(60, 60)
        self.btn_w_r .setStyleSheet(
            "background-color:#E74C3C; color:white; border-radius:10px; font-size:18px;")
        self.btn_w_r .clicked.connect(self.on_w_red)
        self.btn_w_r .rightClicked.connect(self.on_w_red_remove)
        self.btn_yc_r = ClickableButton(f"YC:{self.yc_red}")
        self.btn_yc_r.setFixedSize(60, 60)
        self.btn_yc_r.setStyleSheet(
            "background-color:#E74C3C; color:white; border-radius:10px; font-size:18px;")
        self.btn_yc_r.clicked.connect(self.on_yc_red)
        self.btn_yc_r.rightClicked.connect(self.on_yc_red_remove)
        red_ctrl.addWidget(self.btn_w_r,  0, 1)
        red_ctrl.addWidget(self.btn_yc_r, 0, 0)

        self.btn_r1_red = ClickableButton('R1')
        self.btn_r1_red.setFixedSize(60, 60)
        self.btn_r1_red.setStyleSheet(
            "background-color:#D3D3D3; color:white; border-radius:10px; font-size:18px;")
        self.btn_r1_red.clicked.connect(self.r1_red_on)
        self.btn_r1_red.rightClicked.connect(self.r1_red_off)
        red_ctrl.addWidget(self.btn_r1_red, 1, 0)

        self.btn_r2_red = ClickableButton('R2')
        self.btn_r2_red.setFixedSize(60, 60)
        self.btn_r2_red.setStyleSheet(
            "background-color:#D3D3D3; color:white; border-radius:10px; font-size:18px;")
        self.btn_r2_red.clicked.connect(self.r2_red_on)
        self.btn_r2_red.rightClicked.connect(self.r2_red_off)
        red_ctrl.addWidget(self.btn_r2_red, 1, 1)
# ///////////////////////////////////////////////////

        self.btn_four_point_r = ClickableButton('4')
        self.btn_four_point_r.setFixedSize(60, 60)
        self.btn_four_point_r.setStyleSheet(
            "background-color:#E74C3C; color:white; border-radius:10px; font-size:18px;")
        self.btn_four_point_r.clicked.connect(self.four_point_plus_r)
        self.btn_four_point_r.rightClicked.connect(self.four_point_minus_r)
        red_ctrl.addWidget(self.btn_four_point_r, 2, 0)

        self.btn_five_point_r = ClickableButton('5')
        self.btn_five_point_r.setFixedSize(60, 60)
        self.btn_five_point_r.setStyleSheet(
            "background-color:#E74C3C; color:white; border-radius:10px; font-size:18px;")
        self.btn_five_point_r.clicked.connect(self.five_point_plus_r)
        self.btn_five_point_r.rightClicked.connect(self.five_point_minus_r)
        red_ctrl.addWidget(self.btn_five_point_r, 2, 1)

        blue_ctrl = QGridLayout()
        self.btn_yc_b = ClickableButton(f"YC:{self.yc_blue}")
        self.btn_yc_b.setFixedSize(60, 60)
        self.btn_yc_b.setStyleSheet(
            "background-color:#5AA9E6; color:white; border-radius:10px; font-size:18px;")
        self.btn_yc_b.clicked.connect(self.on_yc_blue)
        self.btn_yc_b.rightClicked.connect(self.on_yc_blue_remove)
        self.btn_w_b = ClickableButton(f"W:{self.chuy_blue}")
        self.btn_w_b.setStyleSheet(
            "background-color:#5AA9E6; color:white; border-radius:10px; font-size:18px;")
        self.btn_w_b .clicked.connect(self.on_w_blue)
        self.btn_w_b.setFixedSize(60, 60)
        self.btn_w_b .rightClicked.connect(self.on_w_blue_remove)
        blue_ctrl.addWidget(self.btn_yc_b, 0, 1)
        blue_ctrl.addWidget(self.btn_w_b,  0, 0)

        self.btn_r1_blue = ClickableButton('R1')
        self.btn_r1_blue.setFixedSize(60, 60)
        self.btn_r1_blue.setStyleSheet(
            "background-color:#D3D3D3; color:white; border-radius:10px; font-size:18px;")
        self.btn_r1_blue.clicked.connect(self.r1_blue_on)
        self.btn_r1_blue.rightClicked.connect(self.r1_blue_off)
        blue_ctrl.addWidget(self.btn_r1_blue, 1, 0)

        self.btn_r2_blue = ClickableButton('R2')
        self.btn_r2_blue.setFixedSize(60, 60)
        self.btn_r2_blue.setStyleSheet(
            "background-color:#D3D3D3; color:white; border-radius:10px; font-size:18px;")
        self.btn_r2_blue.clicked.connect(self.r2_blue_on)
        self.btn_r2_blue.rightClicked.connect(self.r2_blue_off)
        blue_ctrl.addWidget(self.btn_r2_blue, 1, 1)

        self.btn_four_point_b = ClickableButton('4')
        self.btn_four_point_b.setFixedSize(60, 60)
        self.btn_four_point_b.setStyleSheet(
            "background-color:#5AA9E6; color:white; border-radius:10px; font-size:18px;")
        self.btn_four_point_b.clicked.connect(self.four_point_plus_b)
        self.btn_four_point_b.rightClicked.connect(self.four_point_minus_b)
        blue_ctrl.addWidget(self.btn_four_point_b, 2, 0)

        self.btn_five_point_b = ClickableButton('5')
        self.btn_five_point_b.setFixedSize(60, 60)
        self.btn_five_point_b.setStyleSheet(
            "background-color:#5AA9E6; color:white; border-radius:10px; font-size:18px;")
        self.btn_five_point_b.clicked.connect(self.five_point_plus_b)
        self.btn_five_point_b.rightClicked.connect(self.five_point_minus_b)
        blue_ctrl.addWidget(self.btn_five_point_b, 2, 1)

        # blue_ctrl.addWidget(self._make_btn("4", "#5AA9E6"), 2, 0)
        # blue_ctrl.addWidget(self._make_btn("5", "#5AA9E6"), 2, 1)

        bottom = QHBoxLayout()
        bottom.addLayout(red_ctrl)
        bottom.addLayout(panel)
        bottom.addLayout(blue_ctrl)
        main_layout.addLayout(bottom)

        # if self.phase == 'round':
        #     self.start_round()
        # elif self.phase == 'finished' or self.phase == 'rest' or self.phase == 'stoped':
        #     self.end_round()

    def play_beep(self):
        threading.Thread(target=lambda: winsound.Beep(1000, 300)).start()

    def palay_final_beep(self):
        threading.Thread(target=lambda: winsound.Beep(2000, 1000)).start()

    def get_scores_from_server(self):
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            response = requests.get(f'http://{local_ip}:5000/scores')
            if response.status_code == 200:
                # print('oK')
                return response.json()
        except Exception as e:
            print("Ошибка при получении баллов:", e)
        return {}

    def update_scoreboard(self):
        scores = self.get_scores_from_server()
        if not scores:
            return

        log_lines = []
        # print(f'=== Обновляеи табло Scores:{scores}')

        for judge_id_str, judge_scores in scores.items():
            # print(
            # f"Обрабатывается судья: {judge_id_str}, баллы{judge_scores}")
            judge_index = int(judge_id_str) - 1
            if not (0 <= judge_index < 4):
                continue

            red = judge_scores.get("red", 0)
            blue = judge_scores.get("blue", 0)

            prev_red = self.previous_scores_red[judge_index]
            prev_blue = self.previous_scores_blue[judge_index]

            delta_red = red - prev_red
            delta_blue = blue - prev_blue

        # Обновляем только если есть изменения
            if delta_red > 0:
                self.scores_red[judge_index] += delta_red
                print(f"Судья {judge_index + 1} дал {delta_red} за КРАСНОГО")

            if delta_blue > 0:
                self.scores_blue[judge_index] += delta_blue
                print(f"Судья {judge_index + 1} дал {delta_blue} за СИНЕГО")

        # Обновляем "старые" значения, чтобы не прибавлять заново
            self.previous_scores_red[judge_index] = red
            self.previous_scores_blue[judge_index] = blue

        self.sync_audience_display()
        self.sync_judges_to_audience()
        # self._update_labels()
        self.refresh_scores()

    def sync_audience_display(self, formatted_time=None):
        if hasattr(self, "aud_win"):
            if formatted_time is None:
                formatted_time = self._format_time(self.remaining)
            self.aud_win.time_label.setText(formatted_time)
            if hasattr(self, 'aud_win'):
                aud = self.aud_win
                aud.lbl_chui_l.setText(str(self.chuy_red))
                aud.lbl_chui_r.setText(str(self.chuy_blue))
                aud.lbl_score_l.setText(str(self.yc_red))
                aud.lbl_score_r.setText(str(self.yc_blue))

                aud.r1_l.setStyleSheet("background-color:{}; color:white; border-radius:30px;".format(
                    "#90ee90" if self.r1_red else "gray"))
                aud.r2_l.setStyleSheet("background-color:{}; color:white; border-radius:30px;".format(
                    "#90ee90" if self.r2_red else "gray"))
                aud.r1_r.setStyleSheet("background-color:{}; color:white; border-radius:30px;".format(
                    "#90ee90" if self.r1_blue else "gray"))
                aud.r2_r.setStyleSheet("background-color:{}; color:white; border-radius:30px;".format(
                    "#90ee90" if self.r2_blue else "gray"))

                aud.lbl_round.setText(f"Раунд: {self.current_round}")
                aud.time_label.setText(self._format_time(self.remaining))
                aud.lbl_cat.setText(f"Категория: {self.category}")
                aud.lbl_ath_l.setText(self.name_red)
                aud.lbl_ath_r.setText(self.name_blue)
                aud.club_l.setText(self.club_red)
                aud.club_r.setText(self.club_blue)

                # Добавляем синхронизацию текста Раунд/Отдых
            if self.phase == 'round':
                round_text = f"Раунд {self.current_round}/{self.settings['num_rounds']}"
            elif self.phase == 'rest':
                round_text = f"Отдых — раунд {self.current_round}/{self.settings['num_rounds']}"
            else:
                round_text = f"Раунд {self.current_round}/{self.settings['num_rounds']}"
            if self.phase == 'finished':
                round_text = 'Поединок завершен'

            self.aud_win.update_round_label(round_text)

    def calculate_differences(self):
        return [r - b for r, b in zip(self.scores_red, self.scores_blue)]

    def sync_judges_to_audience(self):
        if not hasattr(self, 'aud_win') or not self.aud_win:
            return

        diffs = self.calculate_differences()

        for i, diff in enumerate(diffs):
            if diff > 0:
                self.aud_win.update_judge_display(i, f"+{diff}", "red")
            elif diff < 0:
                self.aud_win.update_judge_display(i, f"+{-diff}", "blue")
            else:
                self.aud_win.update_judge_display(i, "0", "gray")

    def on_show_screen(self):
        self.aud_win = AudienceDisplay()
        self.aud_win.show()
        self.sync_audience_display()
        self.sync_judges_to_audience()

    def off_show_screen(self):
        self.aud_win = AudienceDisplay()
        self.aud_win.hide()

    def open_settings(self):
        # Сначала создаём диалог
        dlg = SettingsDialog(self, current_settings=self.settings)
        dlg.scoreChanged.connect(
            self.update_score_from_dialog)     # Подключаем сигнал

        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.settings.update(dlg.get_settings())
            self.original_settings = dict(self.settings)
            self.refresh_ui()

    def update_score_from_dialog(self, corner: str, judge_index: int, value: int):
        if corner == 'red':
            self.scores_red[judge_index] += value
        elif corner == 'blue':
            self.scores_blue[judge_index] += value
        self.refresh_scores()

    def extra_raund(self):
        self.extra_active = True
        self.settings['round_time'] = 60
        self.settings['num_rounds'] = 1

    # Стиль активной кнопки (зелёный)
        self.btn_extra.setStyleSheet("""
        QPushButton {
            background-color: #90ee90;
            color: black;
            font-size: 14px;
            border-radius: 10px;
            padding: 5px 10px;
        }
        QPushButton:hover {
            background-color: #7fd87f;
        }
        QPushButton:pressed {
            background-color: #6fc66f;
        }
    """)
        self.refresh_ui()

    def all_reset(self):
        self.settings = dict(self.original_settings)
        self.scores_red = [0, 0, 0, 0]
        self.scores_blue = [0, 0, 0, 0]
        self.previous_scores_blue = [0, 0, 0, 0]
        self.previous_scores_red = [0, 0, 0, 0]
        self.chuy_red = 0
        self.chuy_blue = 0
        self.yc_red = 0
        self.yc_blue = 0
        self.r1_red = False
        self.r2_red = False
        self.r1_blue = False
        self.r2_blue = False
        self.name_red = 'Спортсмен'
        self.name_blue = 'Спортсмен'
        self.club_red = 'Клуб'
        self.club_blue = 'Клуб'
        self.category = 'Категория'
        self.raund = 1
        self.extra_active = False

        # состояние таймера
        self.current_round = 1
        self.phase = 'stopped'  # 'stopped', 'round', 'rest'
        self.remaining = self.settings['round_time']

        # Qt‑таймер
        # self.timer = QTimer(self)
        # self.timer.setInterval(1000)
        # self.timer.timeout.connect(self._tick)
        self.refresh_scores()
        self._update_labels()
        self.stop_timer()
        # Вернуть стиль кнопки к обычному
        self.btn_extra.setStyleSheet(self.style_btn)

        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            requests.post(f'http://{local_ip}:5000/reset_scores', timeout=1)
        except Exception as e:
            print('Не смог сбросить баллы на сервере:', e)

        self.btn_r1_red.setStyleSheet(
            "background-color:#D3D3D3; color:white; border-radius:10px; font-size:18px;")
        self.btn_r2_red.setStyleSheet(
            "background-color:#D3D3D3; color:white; border-radius:10px; font-size:18px;")
        self.btn_r1_blue.setStyleSheet(
            "background-color:#D3D3D3; color:white; border-radius:10px; font-size:18px;")
        self.btn_r2_blue.setStyleSheet(
            "background-color:#D3D3D3; color:white; border-radius:10px; font-size:18px;")
        self.refresh_ui()

    # Логика выпадания правым кликом:

    # red five and four minus

    def start_round(self):
        local_ip = socket.gethostbyname(socket.gethostname())
        requests.post(f"http://{local_ip}:5000/set_fight_state",
                      json={"fight_active": True})

    def end_round(self):
        local_ip = socket.gethostbyname(socket.gethostname())
        requests.post(f"http://{local_ip}:5000/set_fight_state",
                      json={"fight_active": False})

    def four_point_minus_r(self):
        for i in range(4):
            self.scores_red[i] -= 4
        self.refresh_scores()

    def five_point_minus_r(self):
        for i in range(4):
            self.scores_red[i] -= 5
        self.refresh_scores()
    # blue five and five minus

    def four_point_minus_b(self):
        for i in range(4):
            self.scores_blue[i] -= 4
        self.refresh_scores()

    def five_point_minus_b(self):
        for i in range(4):
            self.scores_blue[i] -= 5
        self.refresh_scores()

    def on_w_red_remove(self):
        if self.chuy_red > 0:
            old = self.chuy_red
            self.chuy_red -= 1
            if old % 3 == 0:
                for i in range(4):
                    self.scores_red[i] += 1
            self.refresh_scores()
            self.sync_audience_display

    def on_yc_red_remove(self):
        if self.yc_red > 0:
            self.yc_red -= 1
            for i in range(4):
                self.scores_red[i] += 1
            self.refresh_scores()

    def on_w_blue_remove(self):
        if self.chuy_blue > 0:
            old = self.chuy_blue
            self.chuy_blue -= 1
            if old % 3 == 0:
                for i in range(4):
                    self.scores_blue[i] += 1
            self.refresh_scores()

    def on_yc_blue_remove(self):
        if self.yc_blue > 0:
            self.yc_blue -= 1
            for i in range(4):
                self.scores_blue[i] += 1
            self.refresh_scores()

# R1 R2 off red

    def r1_red_off(self):
        if self.r1_red == True:
            self.r1_red = False
            for i in range(4):
                self.scores_red[i] -= 2
                self.btn_r1_red.setStyleSheet(
                    "background-color: #D3D3D3; color:white; border-radius:10px; font-size:18px;")
        self.refresh_scores()

    def r2_red_off(self):
        if self.r2_red == True:
            self.r2_red = False
            for i in range(4):
                self.scores_red[i] -= 2
                self.btn_r2_red.setStyleSheet(
                    "background-color: #D3D3D3; color:white; border-radius:10px; font-size:18px;")
        self.refresh_scores()

    # R1 R2 off blublue
    def r1_blue_off(self):
        if self.r1_blue == True:
            self.r1_blue = False
            for i in range(4):
                self.scores_blue[i] -= 2
                self.btn_r1_blue.setStyleSheet(
                    "background-color: #D3D3D3; color:white; border-radius:10px; font-size:18px;")
        self.refresh_scores()

    def r2_blue_off(self):
        if self.r2_blue == True:
            self.r2_blue = False
            for i in range(4):
                self.scores_blue[i] -= 2
                self.btn_r2_blue.setStyleSheet(
                    "background-color: #D3D3D3; color:white; border-radius:10px; font-size:18px;")
        self.refresh_scores()
    # Логика W/YC добавления

    def on_w_red(self):
        self.chuy_red += 1
        if self.chuy_red % 3 == 0:
            for i in range(4):
                self.scores_red[i] -= 1
        self.refresh_scores()
        self.sync_audience_display()

    def on_yc_red(self):
        self.yc_red += 1
        for i in range(4):
            self.scores_red[i] -= 1
        self.refresh_scores()
        self.sync_audience_display()

    def on_w_blue(self):
        self.chuy_blue += 1
        if self.chuy_blue % 3 == 0:
            for i in range(4):
                self.scores_blue[i] -= 1
        self.refresh_scores()
        self.sync_audience_display()

    def on_yc_blue(self):
        self.yc_blue += 1
        for i in range(4):
            self.scores_blue[i] -= 1
        self.refresh_scores()
        self.sync_audience_display()

    def refresh_scores(self):
        self.btn_w_r .setText(f"W:{self.chuy_red}")
        self.btn_yc_r.setText(f"YC:{self.yc_red}")
        self.btn_w_b .setText(f"W:{self.chuy_blue}")
        self.btn_yc_b.setText(f"YC:{self.yc_blue}")
        for i in range(4):
            r, b = self.scores_red[i], self.scores_blue[i]
            if r > b:
                rc, bc = "#FF6666", "#CCCCCC"
            elif b > r:
                rc, bc = "#CCCCCC", "#6699FF"
            else:
                rc, bc = "#DDDDDD", "#DDDDDD"
            self.judge_red_labels[i].setText(str(r))
            self.judge_red_labels[i].setStyleSheet(
                f"background-color:{rc}; font-size:24px; border-radius:10px; padding:6px;")
            self.judge_blue_labels[i].setText(str(b))
            self.judge_blue_labels[i].setStyleSheet(

                f"background-color:{bc}; font-size:24px; border-radius:10px; padding:6px;")
            if hasattr(self, 'aud_win') and self.aud_win:
                score_diff = [r - b for r,
                              b in zip(self.scores_red, self.scores_blue)]
                self.aud_win.update_wing_colors(score_diff)
            self.sync_judges_to_audience()
# red five and four

    def four_point_plus_r(self):
        for i in range(4):
            self.scores_red[i] += 4
        self.refresh_scores()

    def five_point_plus_r(self):
        for i in range(4):
            self.scores_red[i] += 5
        self.refresh_scores()

# blue five and foy
    def four_point_plus_b(self):
        for i in range(4):
            self.scores_blue[i] += 4
        self.refresh_scores()

    def five_point_plus_b(self):
        for i in range(4):
            self.scores_blue[i] += 5
        self.refresh_scores()

    # R1 R2 on
    def r1_red_on(self):
        if self.current_round == 1 and self.r1_red == False:
            self.r1_red = True
            for i in range(4):
                self.scores_red[i] += 2
                self.btn_r1_red.setStyleSheet(
                    "background-color: #90ee90; color:white; border-radius:10px; font-size:18px;")
        self.refresh_scores()

    def r2_red_on(self):
        if self.current_round > 1 and self.r2_red == False:
            self.r2_red = True
            for i in range(4):
                self.scores_red[i] += 2
                self.btn_r2_red.setStyleSheet(
                    "background-color: #90ee90; color:white; border-radius:10px; font-size:18px;")
        self.refresh_scores()
# R1 R2 blue

    def r1_blue_on(self):
        if self.current_round == 1 and self.r1_blue == False:
            self.r1_blue = True
            for i in range(4):
                self.scores_blue[i] += 2
                self.btn_r1_blue.setStyleSheet(
                    "background-color: #90ee90; color:white; border-radius:10px; font-size:18px;")
        self.refresh_scores()

    def r2_blue_on(self):
        if self.current_round > 1 and self.r2_blue == False:
            self.r2_blue = True
            for i in range(4):
                self.scores_blue[i] += 2
                self.btn_r2_blue.setStyleSheet(
                    "background-color: #90ee90; color:white; border-radius:10px; font-size:18px;")
        self.refresh_scores()

    def _make_btn(self, txt, color):
        btn = QPushButton(txt)
        btn.setFixedSize(60, 60)
        btn.setStyleSheet(
            f"border-radius:10px; font-size:18px; background-color:{color}; color:white;")
        return btn

    def _make_score(self, txt, bg):
        lbl = QLabel(txt)
        lbl.setFixedSize(80, 60)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            f"background-color:{bg}; font-size:24px; border-radius:10px; padding:6px;")
        return lbl

    def _make_name(self, txt):
        lbl = QLabel(txt)
        lbl.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return lbl

    def _make_line(self, color):
        ln = QFrame()
        ln.setFixedHeight(3)
        ln.setStyleSheet(f"background-color:{color}; border:none;")
        return ln

    def refresh_ui(self):
        # Обновляем время
        self.remaining = self.settings['round_time']
        self.time_lbl.setText(self._format_time(self.remaining))

    # Обновляем номер текущего раунда
        self.current_round = 1

    # Обновляем надписи (категория, спортсмены, клубы и пр.)
        self._update_labels()

    # Если есть логика с фазой таймера — сбрасываем её
        self.phase = 'stopped'

    # Если нужно — можно также скрыть или показать кнопки
    # self.btn_start.show()
    # self.btn_stop.hide()

    def start_timer(self):
        # If stopped, start first round
        if self.phase in ('stopped', 'finished'):
            self.phase = 'round'
            self.current_round = 1
            self.remaining = self.settings['round_time']
            # restore start button text if it was changed in “finished”
            self.btn_start.setText("Старт")
        # show/hide controls
        self.btn_start.hide()
        self.btn_stop.show()
        # update labels immediately
        self._update_labels()
        # show the first second right away
        self.time_lbl.setText(self._format_time(self.remaining))
        # start ticking
        self.timer.start()
        self.start_round()

    def stop_timer(self):
        self.timer.stop()
        self.btn_stop.hide()
        self.btn_start.show()
        self.end_round()

    def _tick(self):

        self.remaining -= 1

        # countdown beeps 10 → 1
        if 1 <= self.remaining <= 10:
            self.play_beep()

        # update the displayed clock
        formatted_time = self._format_time(self.remaining)
        self.sync_audience_display(formatted_time)
        self.time_lbl.setText(formatted_time)

        if self.remaining > 0:
            return

        # Phase just ended:
        if self.phase == 'round':

            # three quick beeps at round end
            for _ in range(3):
                self.palay_final_beep()

            if self.current_round < self.settings['num_rounds']:
                # enter rest
                self.phase = 'rest'
                self.remaining = self.settings['rest_time']
                self._update_labels()
                self.end_round()
                # continue timer
                return
            else:
                # final round ended
                self.phase = 'finished'
                self.timer.stop()
                self.btn_stop.hide()
                self.btn_start.setText("Старт")
                self.btn_start.show()
                self.end_round()
                # show “Поединок завершён”
                self.round_lbl.setText("Поединок завершён")
                if hasattr(self, "aud_win"):
                    self.aud_win.set_fight_finished()
                return

        elif self.phase == 'rest':
            # long beep at rest end
            self.palay_final_beep()

            # next round
            self.current_round += 1
            self.phase = 'round'
            self.remaining = self.settings['round_time']
            self._update_labels()
            self.start_round()
            # continue timer
            return

    # def _long_beep(self):
    #     # ~1 s continuous beep by firing 20 beeps @ 50 ms
    #     self._lb_count = 0

    #     def on_lb():
    #         if self._lb_count < 20:
    #             QApplication.beep()
    #             self._lb_count += 1
    #         else:
    #             self._lb_timer.stop()

    #     self._lb_timer = QTimer(self)
    #     self._lb_timer.setInterval(50)
    #     self._lb_timer.timeout.connect(on_lb)
    #     self._lb_timer.start()

    def _update_labels(self):
        if self.phase == 'round':
            text = f"Раунд {self.current_round}/{self.settings['num_rounds']}"
        elif self.phase == 'rest':
            text = f"Отдых — раунд {self.current_round}/{self.settings['num_rounds']}"
        else:
            text = f"Раунд {self.current_round}/{self.settings['num_rounds']}"
        self.round_lbl.setText(text)
        if self.phase == 'finished':
            self.round_lbl.setText('Поединок завершен')
        # если есть вторая метка:
        # self.round_lbl_bottom.setText(text)
        self.time_lbl.setText(self._format_time(self.remaining))
        self.sync_audience_display()

    def _format_time(self, sec: int) -> str:
        m, s = divmod(max(sec, 0), 60)
        return f"{m:02d}:{s:02d}"
