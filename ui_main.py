"""
ui_main.py
MainWindow の UI構築部分（レイアウト・スタイル・描画）
状態管理・タイマー・シグナル接続は app.py で行う。
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDialog, QComboBox, QSpinBox, QDialogButtonBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QPen, QBrush

from constants import WINDOW_WIDTH, WINDOW_HEIGHT, THEMES
from theme import ThemeManager
from ui_cup import CupWidget


# ============================================================
# 設定ダイアログ
# ============================================================
class SettingsDialog(QDialog):
    """設定ポップアップダイアログ"""

    def __init__(self, current_interval: int, current_theme: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("設定")
        self.setFixedSize(320, 200)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        # 親ウィンドウから ThemeManager を取得
        self._theme: ThemeManager = parent.theme if parent and hasattr(parent, "theme") else ThemeManager(current_theme)
        self._build_ui(current_interval, current_theme)

    def _build_ui(self, current_interval: int, current_theme: str):
        theme = self._theme
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(14)

        label_style = f"""
            color: {theme.get_color("text")};
            font-family: 'Yu Gothic UI';
            font-size: 12px;
            font-weight: bold;
        """

        # ---- 通知間隔 ----
        interval_row = QHBoxLayout()
        interval_label = QLabel("通知間隔（分）：")
        interval_label.setStyleSheet(label_style)
        interval_row.addWidget(interval_label)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(5, 45)
        self.interval_spin.setSingleStep(5)
        self.interval_spin.setValue(current_interval)
        self.interval_spin.setSuffix(" 分")
        self.interval_spin.setStyleSheet(f"""
            QSpinBox {{
                color: {theme.get_color("text")};
                font-family: 'Yu Gothic UI';
                font-size: 12px;
                border: 1px solid {theme.get_color("cup_outline")};
                border-radius: 6px;
                padding: 4px 8px;
                min-width: 80px;
            }}
        """)
        interval_row.addStretch()
        interval_row.addWidget(self.interval_spin)
        layout.addLayout(interval_row)

        # ---- カラーテーマ ----
        theme_row = QHBoxLayout()
        theme_label = QLabel("カラーテーマ：")
        theme_label.setStyleSheet(label_style)
        theme_row.addWidget(theme_label)

        self.theme_combo = QComboBox()
        for name in THEMES.keys():
            self.theme_combo.addItem(name)
        if current_theme in THEMES:
            self.theme_combo.setCurrentText(current_theme)
        self.theme_combo.setStyleSheet(f"""
            QComboBox {{
                color: {theme.get_color("text")};
                font-family: 'Yu Gothic UI';
                font-size: 12px;
                border: 1px solid {theme.get_color("cup_outline")};
                border-radius: 6px;
                padding: 4px 8px;
                min-width: 160px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """)
        theme_row.addStretch()
        theme_row.addWidget(self.theme_combo)
        layout.addLayout(theme_row)

        layout.addStretch()

        # ---- OK / キャンセルボタン ----
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.setStyleSheet(f"""
            QPushButton {{
                background: {theme.get_color("btn_bg")};
                color: #FFFFFF;
                font-family: 'Yu Gothic UI';
                font-size: 12px;
                font-weight: bold;
                border: none;
                border-radius: 14px;
                padding: 6px 20px;
                min-width: 70px;
            }}
            QPushButton:hover {{
                background: {theme.get_color("btn_hover")};
            }}
        """)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_settings(self) -> dict:
        """設定値を辞書で返す"""
        return {
            "interval": self.interval_spin.value(),
            "theme": self.theme_combo.currentText(),
        }


# ============================================================
# メインウィンドウ UI
# ============================================================
class MainWindowUI(QWidget):
    """
    MainWindow の UI構築・描画を担当するクラス。
    状態管理・タイマー・シグナル接続は app.py の MainWindow で行う。
    """

    def __init__(self, theme: ThemeManager):
        self._theme = theme
        super().__init__()
        self._setup_window()
        self._build_ui()

    # ----------------------------------------------------------
    # ウィンドウ設定
    # ----------------------------------------------------------
    def _setup_window(self):
        self.setWindowTitle("水飲みリマインド")
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._drag_pos = None

    # ----------------------------------------------------------
    # ドラッグ移動
    # ----------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    # ----------------------------------------------------------
    # 背景描画
    # ----------------------------------------------------------
    def paintEvent(self, event):
        """角丸ウィンドウ背景を描画"""
        theme = self._theme
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 影（外側）
        shadow_color = QColor(theme.get_color("shadow"))
        shadow_color.setAlpha(80)
        for i in range(6, 0, -1):
            shadow_color.setAlpha(15 * i)
            painter.setBrush(QBrush(shadow_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(
                i, i, WINDOW_WIDTH - i * 2, WINDOW_HEIGHT - i * 2, 20, 20
            )

        # 背景グラデーション
        grad = QLinearGradient(0, 0, 0, WINDOW_HEIGHT)
        grad.setColorAt(0.0, QColor(theme.get_color("bg")))
        grad.setColorAt(1.0, QColor(theme.get_color("bg2")))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(4, 4, WINDOW_WIDTH - 8, WINDOW_HEIGHT - 8, 18, 18)

        # 上部アクセントバー
        accent_grad = QLinearGradient(0, 0, WINDOW_WIDTH, 0)
        accent_grad.setColorAt(0.0, QColor(theme.get_color("primary")))
        accent_grad.setColorAt(1.0, QColor(theme.get_color("accent")))
        painter.setBrush(QBrush(accent_grad))
        painter.drawRoundedRect(4, 4, WINDOW_WIDTH - 8, 6, 3, 3)

    # ----------------------------------------------------------
    # UI構築
    # ----------------------------------------------------------
    def _build_ui(self):
        theme = self._theme
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(0)

        # ---- 上部ボタン行（歯車＋閉じる） ----
        top_row = QHBoxLayout()

        self.gear_btn = QPushButton("⚙")
        self.gear_btn.setFixedSize(28, 28)
        self.gear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.gear_btn.setToolTip("設定")
        self.gear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {theme.get_color("text_light")};
                font-size: 16px;
                border: none;
                border-radius: 14px;
            }}
            QPushButton:hover {{
                background: {theme.get_color("shadow")};
                color: {theme.get_color("text")};
            }}
        """)
        top_row.addWidget(self.gear_btn)
        top_row.addStretch()

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {theme.get_color("text_light")};
                font-size: 14px;
                border: none;
                border-radius: 14px;
            }}
            QPushButton:hover {{
                background: {theme.get_color("shadow")};
                color: {theme.get_color("text")};
            }}
        """)
        top_row.addWidget(self.close_btn)
        root_layout.addLayout(top_row)

        # ---- 飲水回数 ----
        count_frame = QVBoxLayout()
        count_frame.setSpacing(2)

        self.label_title = QLabel("本日の飲水回数")
        self.label_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_title.setStyleSheet(f"""
            color: {theme.get_color("text_light")};
            font-family: 'Yu Gothic UI';
            font-size: 11px;
            letter-spacing: 1px;
        """)
        count_frame.addWidget(self.label_title)

        self.count_label = QLabel("0 回")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label.setStyleSheet(f"""
            color: {theme.get_color("primary_dark")};
            font-family: 'Yu Gothic UI';
            font-size: 32px;
            font-weight: bold;
        """)
        count_frame.addWidget(self.count_label)
        root_layout.addLayout(count_frame)

        root_layout.addSpacing(8)

        # ---- コップビジュアル ----
        cup_row = QHBoxLayout()
        cup_row.addStretch()
        self.cup_widget = CupWidget(theme=theme)
        cup_row.addWidget(self.cup_widget)
        cup_row.addStretch()
        root_layout.addLayout(cup_row)

        root_layout.addSpacing(8)

        # ---- 残り時間 ----
        time_frame = QVBoxLayout()
        time_frame.setSpacing(2)

        self.label_time_title = QLabel("次の通知まで")
        self.label_time_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_time_title.setStyleSheet(f"""
            color: {theme.get_color("text_light")};
            font-family: 'Yu Gothic UI';
            font-size: 11px;
            letter-spacing: 1px;
        """)
        time_frame.addWidget(self.label_time_title)

        self.time_label = QLabel("00:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet(f"""
            color: {theme.get_color("primary")};
            font-family: 'Yu Gothic UI';
            font-size: 26px;
            font-weight: bold;
        """)
        time_frame.addWidget(self.time_label)
        root_layout.addLayout(time_frame)

        root_layout.addSpacing(12)

        # ---- 手動「飲んだ」ボタン ----
        self.drink_btn = QPushButton("💧 飲んだ")
        self.drink_btn.setFixedHeight(40)
        self.drink_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.drink_btn.setStyleSheet(f"""
            QPushButton {{
                background: {theme.get_color("btn_bg")};
                color: {theme.get_color("btn_fg")};
                font-family: 'Yu Gothic UI';
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-radius: 20px;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background: {theme.get_color("btn_hover")};
            }}
            QPushButton:pressed {{
                background: {theme.get_color("primary_dark")};
            }}
        """)
        root_layout.addWidget(self.drink_btn)

        root_layout.addStretch()

        # 初期水位
        self.cup_widget.set_level(0.0, animate=False)

    # ----------------------------------------------------------
    # テーマ適用（UI全体を再スタイリング）
    # ----------------------------------------------------------
    def apply_theme_to_ui(self):
        """ThemeManager の現在テーマを使ってUI全体のスタイルを更新する"""
        theme = self._theme
        self.gear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {theme.get_color("text_light")};
                font-size: 16px;
                border: none;
                border-radius: 14px;
            }}
            QPushButton:hover {{
                background: {theme.get_color("shadow")};
                color: {theme.get_color("text")};
            }}
        """)
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {theme.get_color("text_light")};
                font-size: 14px;
                border: none;
                border-radius: 14px;
            }}
            QPushButton:hover {{
                background: {theme.get_color("shadow")};
                color: {theme.get_color("text")};
            }}
        """)
        self.label_title.setStyleSheet(f"""
            color: {theme.get_color("text_light")};
            font-family: 'Yu Gothic UI';
            font-size: 11px;
            letter-spacing: 1px;
        """)
        self.count_label.setStyleSheet(f"""
            color: {theme.get_color("primary_dark")};
            font-family: 'Yu Gothic UI';
            font-size: 32px;
            font-weight: bold;
        """)
        self.label_time_title.setStyleSheet(f"""
            color: {theme.get_color("text_light")};
            font-family: 'Yu Gothic UI';
            font-size: 11px;
            letter-spacing: 1px;
        """)
        self.time_label.setStyleSheet(f"""
            color: {theme.get_color("primary")};
            font-family: 'Yu Gothic UI';
            font-size: 26px;
            font-weight: bold;
        """)
        self.drink_btn.setStyleSheet(f"""
            QPushButton {{
                background: {theme.get_color("btn_bg")};
                color: {theme.get_color("btn_fg")};
                font-family: 'Yu Gothic UI';
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-radius: 20px;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background: {theme.get_color("btn_hover")};
            }}
            QPushButton:pressed {{
                background: {theme.get_color("primary_dark")};
            }}
        """)
        self.cup_widget.update()
        self.update()
