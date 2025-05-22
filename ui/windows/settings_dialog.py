from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel,
    QPushButton, QDialogButtonBox, QSpinBox
)
from PyQt6.QtCore import pyqtSignal, QTimer
import random
import qrcode
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QDialog, QLabel
import requests
from PyQt6.QtCore import Qt
import socket


class SettingsDialog(QDialog):
    scoreChanged = pyqtSignal(str, int, int)  # угол, индекс судьи, значение

    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки табло")
        hostname = socket.gethostname()
        self.local_ip = socket.gethostbyname(hostname)

        layout = QVBoxLayout(self)
        self.judge_pins = {}  # {номер_судьи: пин}
        self.judge_status_labels = []

        # Основные параметры: время раунда, отдых, раунды
        time_layout = QGridLayout()
        time_layout.addWidget(QLabel("Время раунда (сек):"), 0, 0)
        self.round_time = QSpinBox()
        self.round_time.setRange(30, 600)
        time_layout.addWidget(self.round_time, 0, 1)

        time_layout.addWidget(QLabel("Время отдыха (сек):"), 1, 0)
        self.rest_time = QSpinBox()
        self.rest_time.setRange(0, 600)
        time_layout.addWidget(self.rest_time, 1, 1)

        time_layout.addWidget(QLabel("Количество раундов:"), 2, 0)
        self.num_rounds = QSpinBox()
        self.num_rounds.setRange(1, 10)
        time_layout.addWidget(self.num_rounds, 2, 1)
        layout.addLayout(time_layout)

        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_judje_statuses)
        self.status_timer.start(20)

        # Настройка судей: кнопки + и - для каждой стороны
        judge_layout = QGridLayout()
        self.judge_buttons = []
        for i in range(4):
            judge_layout.addWidget(QLabel(f"Судья {i+1}"), i, 0)
            # красные кнопки + / - (большие прямоугольные с плавным скруглением)
            up_r = QPushButton("+", self)
            up_r.setFixedSize(40, 40)
            up_r.setStyleSheet(
                "background-color: #e74c3c; color: white; font-weight: bold;"
                "border-radius: 10px;"
            )
            down_r = QPushButton("-", self)
            down_r.setFixedSize(40, 40)
            down_r.setStyleSheet(
                "background-color: #c0392b; color: white; font-weight: bold;"
                "border-radius: 10px;"
            )
            judge_layout.addWidget(up_r,   i, 1)
            judge_layout.addWidget(down_r, i, 2)

            # синие кнопки + / - (большие прямоугольные с плавным скруглением)
            up_b = QPushButton("+", self)
            up_b.setFixedSize(40, 40)
            up_b.setStyleSheet(
                "background-color: #3498db; color: white; font-weight: bold;"
                "border-radius: 10px;"
            )
            down_b = QPushButton("-", self)
            down_b.setFixedSize(40, 40)
            down_b.setStyleSheet(
                "background-color: #2980b9; color: white; font-weight: bold;"
                "border-radius: 10px;"
            )
            judge_layout.addWidget(up_b,   i, 3)
            judge_layout.addWidget(down_b, i, 4)

            self.judge_buttons.append((up_r, down_r, up_b, down_b))
            layout.addLayout(judge_layout)
            up_r.clicked.connect(
                lambda _, idx=i: self.scoreChanged.emit('red', idx, 1))
            down_r.clicked.connect(
                lambda _, idx=i: self.scoreChanged.emit('red', idx, -1))
            up_b.clicked.connect(
                lambda _, idx=i: self.scoreChanged.emit('blue', idx, 1))
            down_b.clicked.connect(
                lambda _, idx=i: self.scoreChanged.emit('blue', idx, -1))

        for i in range(4):

            # ← после кнопок баллов
            status_label = QLabel("⛔", self)
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_label.setStyleSheet("font-size: 20px; color: red;")
            judge_layout.addWidget(status_label, i, 5)
            self.judge_status_labels.append(status_label)

            btn_connect = QPushButton("🔗", self)
            btn_connect.setFixedSize(40, 40)
            btn_connect.setToolTip("Подключить судью")
            btn_connect.clicked.connect(
                lambda _, idx=i: self.generate_qr_for_judge(idx))
            judge_layout.addWidget(btn_connect, i, 6)

        # Кнопки Ok/Cancel
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Инициализация значений
        if current_settings:
            self.round_time.setValue(current_settings.get('round_time', 120))
            self.rest_time.setValue(current_settings.get('rest_time', 60))
            self.num_rounds.setValue(current_settings.get('num_rounds', 2))

    def generate_qr_for_judge(self, judge_index):
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)

        pin = f"{random.randint(1000, 9999)}"
        url = f"http://{self.local_ip}:5000/judge/{pin}"
        qr = qrcode.make(url)
        pixmap = QPixmap.fromImage(qr.get_image().toqimage())

        dlg = QDialog(self)
        dlg.setWindowTitle(f"QR-код для Судьи {judge_index + 1}")
        layout = QVBoxLayout(dlg)

        label = QLabel(f"PIN-код: {pin}")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 20px;")
        layout.addWidget(label)

        qr_label = QLabel()
        qr_label.setPixmap(pixmap)
        qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(qr_label)
        self.judge_pins[judge_index] = pin

        try:
            response = requests.post(f"http://{self.local_ip}:5000/register_pin", json={
                "pin": pin,
                "judge": judge_index + 1
            })
            response.raise_for_status()
            pin = response.json()['pin']
            if response.status_code == 200:
                print(f"✅ PIN {pin} зарегистрирован")
                self.judge_status_labels[judge_index].setText("✅")
                self.judge_status_labels[judge_index].setStyleSheet(
                    "font-size: 20px; color: green;")
            else:
                print(
                    f"⚠️ Ответ сервера: {response.status_code} — {response.text}")
        except Exception as e:
            print("❌ Ошибка при отправке запроса на регистрацию PIN:", e)
        dlg.exec()

    def update_judje_statuses(self):
        try:
            resp = requests.get(f'http://{self.local_ip}:5000/active_judges')
            data = resp.json()
            active = set(data['active_judges'])
        except Exception:
            active = set()
        # перебираем всех судей по индексу и ставим/снимаем галочку
        for idx, label in enumerate(self.judge_status_labels):
            # у вас judge_index = 0…3, а API возвращает judge_id = 1…4p
            judge_id = idx + 1
            if judge_id in active:
                label.setText("✅")
                label.setStyleSheet("font-size:20px; color: green;")
            else:
                label.setText("❌")
                label.setStyleSheet("font-size:20px; color: red;")

    def get_settings(self):
        return {
            'round_time': self.round_time.value(),
            'rest_time': self.rest_time.value(),
            'num_rounds': self.num_rounds.value()
        }
