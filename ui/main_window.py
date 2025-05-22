from PyQt6.QtWidgets import QMainWindow, QTabWidget
from ui.tabs.categories_tab import CategoriesTab  # 👈 добавим новую вкладку
from PyQt6.QtGui import QIcon
from ui.tabs.athletes_tab import AthletesTab
from ui.tabs.scoreboard_tab import ScoreboardTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Taekwon-Do ITF Scoring System")
        self.setGeometry(100, 100, 1000, 700)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.init_tabs()

    def init_tabs(self):
        self.tabs.addTab(CategoriesTab(), "📂 Категории")
        self.scoreboard_tab = ScoreboardTab()
        self.tabs.addTab(self.scoreboard_tab, "Табло")
        self.tabs.addTab(AthletesTab(), "🧍 Спортсмены")
        from ui.tabs.brackets_tab import BracketsTab
        self.tabs.addTab(BracketsTab(), "🎯 Сетки")
        self.tabs.addTab(self.placeholder_tab("⚙️ Настройки"), "⚙️ Настройки")

    def placeholder_tab(self, label_text):
        from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel(label_text))
        tab.setLayout(layout)
        return tab
