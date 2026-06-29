"""
ui_popup.py
通知ポップアップウィンドウ（UI構築・描画部分）
シグナル接続は app.py で行う。
"""

import random
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QPen, QBrush

from constants import (
    POPUP_AUTO_CLOSE_SEC,
    RANDOM_MESSAGES, IGNORED_MESSAGES,
)
from theme import ThemeManager


class PopupWindow(QWidget):
    drink_signal = pyqtSignal()
    snooze_signal = pyqtSignal()
    ignored_signal = pyqtSignal()

    def __init__(self, parent=None, ignore_count: int = 0, theme: ThemeManager = None):
        super().__init__(
            parent,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._ignore_count = ignore_count
        self._action_taken = False  # 「飲んだ」or「あと5分」が押されたか
        self._theme = theme if theme is not None else ThemeManager()

        # 無視回数に応じてポップアップの高さを調整
        popup_height = 200 if ignore_count >= 1 else 170
        self.setFixedSize(320, popup_height)
        self._build_ui()

        # 自動消去タイマー
        self._auto_close_timer = QTimer(self)
        self._auto_close_timer.setSingleShot(True)
        self._auto_close_timer.setInterval(POPUP_AUTO_CLOSE_SEC * 1000)
        self._auto_close_timer.timeout.connect(self._on_auto_close)

    # ----------------------------------------------------------
    # UI構築
    # ----------------------------------------------------------
    def _build_ui(self):
        theme = self._theme
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(6)

        # メインメッセージ（無視回数に応じて変化）
        if self._ignore_count == 0:
            main_msg = "💧 水を飲みましょう"
        elif self._ignore_count == 1:
            main_msg = "🌿 少し休憩しませんか？"
        elif self._ignore_count == 2:
            main_msg = "😊 お水、飲めましたか？"
        else:
            main_msg = "💙 お体のために水を飲んでください"

        msg_label = QLabel(main_msg)
        msg_label.setStyleSheet(f"""
            color: {theme.get_color("primary_dark")};
            font-family: 'Yu Gothic UI';
            font-size: 14px;
            font-weight: bold;
        """)
        layout.addWidget(msg_label)

        # サブメッセージ（無視回数に応じて変化）
        if self._ignore_count == 0:
            sub_text = random.choice(RANDOM_MESSAGES)
        else:
            idx = min(self._ignore_count - 1, len(IGNORED_MESSAGES) - 1)
            sub_text = random.choice(IGNORED_MESSAGES[idx])

        sub_label = QLabel(sub_text)
        sub_label.setWordWrap(True)
        sub_label.setStyleSheet(f"""
            color: {theme.get_color("text")};
            font-family: 'Yu Gothic UI';
            font-size: 10px;
        """)
        layout.addWidget(sub_label)

        layout.addStretch()

        # ボタン行1：「飲んだ」＋「あと5分」
        btn_row1 = QHBoxLayout()
        btn_row1.setSpacing(8)

        drink_btn = QPushButton("✔ 飲んだ")
        drink_btn.setFixedHeight(34)
        drink_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        drink_btn.setStyleSheet(f"""
            QPushButton {{
                background: {theme.get_color("btn_bg")};
                color: {theme.get_color("btn_fg")};
                font-family: 'Yu Gothic UI';
                font-size: 12px;
                font-weight: bold;
                border: none;
                border-radius: 17px;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background: {theme.get_color("btn_hover")};
            }}
            QPushButton:pressed {{
                background: {theme.get_color("primary_dark")};
            }}
        """)
        drink_btn.clicked.connect(self._on_drink)
        btn_row1.addWidget(drink_btn)

        snooze_btn = QPushButton("⏱ あと5分")
        snooze_btn.setFixedHeight(34)
        snooze_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        snooze_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {theme.get_color("primary_dark")};
                font-family: 'Yu Gothic UI';
                font-size: 11px;
                font-weight: bold;
                border: 2px solid {theme.get_color("primary")};
                border-radius: 17px;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background: {theme.get_color("bg")};
                border-color: {theme.get_color("btn_hover")};
            }}
            QPushButton:pressed {{
                background: {theme.get_color("bg2")};
            }}
        """)
        snooze_btn.clicked.connect(self._on_snooze)
        btn_row1.addWidget(snooze_btn)

        layout.addLayout(btn_row1)

        # 閉じるボタン行
        btn_row2 = QHBoxLayout()
        btn_row2.addStretch()

        close_btn = QPushButton("✕ 閉じる")
        close_btn.setFixedHeight(28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {theme.get_color("text_light")};
                font-family: 'Yu Gothic UI';
                font-size: 10px;
                border: 1px solid {theme.get_color("shadow")};
                border-radius: 14px;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background: {theme.get_color("bg")};
                color: {theme.get_color("text")};
            }}
        """)
        close_btn.clicked.connect(self.close)
        btn_row2.addWidget(close_btn)

        layout.addLayout(btn_row2)

    # ----------------------------------------------------------
    # 描画
    # ----------------------------------------------------------
    def paintEvent(self, event):
        """角丸カード型の背景を描画（無視回数に応じて枠を強調）"""
        theme = self._theme
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()

        # 影
        for i in range(8, 0, -1):
            shadow = QColor(theme.get_color("primary_dark"))
            shadow.setAlpha(8 * i)
            painter.setBrush(QBrush(shadow))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(i, i, w - i * 2, h - i * 2, 16, 16)

        # 白背景
        painter.setBrush(QBrush(QColor(theme.get_color("white"))))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(4, 4, w - 8, h - 8, 14, 14)

        # 上部アクセントライン（無視回数に応じて太さ変化）
        accent_grad = QLinearGradient(0, 0, w, 0)
        accent_grad.setColorAt(0.0, QColor(theme.get_color("primary")))
        accent_grad.setColorAt(1.0, QColor(theme.get_color("accent")))
        painter.setBrush(QBrush(accent_grad))
        accent_h = 5 + min(self._ignore_count * 2, 6)  # 無視回数で太くなる（最大11px）
        painter.drawRoundedRect(4, 4, w - 8, accent_h, 3, 3)

        # 枠線（無視回数に応じて強調）
        if self._ignore_count == 0:
            border_color = QColor(theme.get_color("cup_outline"))
            border_width = 1.5
        elif self._ignore_count == 1:
            border_color = QColor(theme.get_color("primary"))
            border_width = 2.0
        elif self._ignore_count == 2:
            border_color = QColor(theme.get_color("accent"))
            border_width = 2.5
        else:
            border_color = QColor(theme.get_color("primary_dark"))
            border_width = 3.0

        border_pen = QPen(border_color, border_width)
        painter.setPen(border_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(4, 4, w - 8, h - 8, 14, 14)

    # ----------------------------------------------------------
    # 表示・タイマー制御
    # ----------------------------------------------------------
    def show_at_bottom_right(self):
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.right() - self.width() - 20
        y = screen.bottom() - self.height() - 60
        self.move(x, y)
        self.show()
        self._auto_close_timer.start()

    # ----------------------------------------------------------
    # 内部スロット（シグナル発行のみ、ロジックなし）
    # ----------------------------------------------------------
    def _on_drink(self):
        self._action_taken = True
        self.drink_signal.emit()
        self.close()

    def _on_snooze(self):
        """「あと5分」ボタン押下：スヌーズシグナルを発行して閉じる"""
        self._action_taken = True
        self.snooze_signal.emit()
        self.close()

    def _on_auto_close(self):
        """自動消去タイマー満了：無操作なので無視シグナルを発行"""
        if not self._action_taken:
            self.ignored_signal.emit()
        self.close()
