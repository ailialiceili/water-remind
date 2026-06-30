"""
ui_popup.py
通知ポップアップウィンドウ（UI構築・描画部分）
シグナル接続は app.py で行う。
"""

import random
import math
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QPen, QBrush

from constants import (
    RANDOM_MESSAGES, IGNORED_MESSAGES,
)
from theme import ThemeManager

# 透明度を上げ始めるまでの秒数
_FADE_START_SEC = 25
# グロー（発光）アニメーションの更新間隔（ms）
_GLOW_INTERVAL_MS = 50
# グローの1サイクル時間（ms）
_GLOW_CYCLE_MS = 2000


class PopupWindow(QWidget):
    drink_signal = pyqtSignal()
    snooze_signal = pyqtSignal()
    close_signal = pyqtSignal()   # 「閉じる」ボタン（最終警告時）
    ignored_signal = pyqtSignal()

    def __init__(
        self,
        parent=None,
        ignore_count: int = 0,
        snooze_count: int = 0,
        theme: ThemeManager = None,
    ):
        super().__init__(
            parent,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._ignore_count = ignore_count
        self._snooze_count = snooze_count
        self._action_taken = False  # 「飲んだ」or「あとで」が押されたか
        self._theme = theme if theme is not None else ThemeManager()

        # 透明度・グロー状態
        self._opacity: float = 1.0          # ウィンドウ全体の不透明度
        self._glow_phase: float = 0.0       # グローアニメーション位相（0.0〜1.0）
        self._glow_active: bool = False     # グローアニメーション中か

        # 無視回数に応じてポップアップの高さを調整
        popup_height = 200 if ignore_count >= 1 else 170
        self.setFixedSize(320, popup_height)
        self._build_ui()

        # 25秒後に透明度を下げるタイマー
        self._fade_timer = QTimer(self)
        self._fade_timer.setSingleShot(True)
        self._fade_timer.setInterval(_FADE_START_SEC * 1000)
        self._fade_timer.timeout.connect(self._on_fade_start)

        # グローアニメーション用タイマー
        self._glow_timer = QTimer(self)
        self._glow_timer.setInterval(_GLOW_INTERVAL_MS)
        self._glow_timer.timeout.connect(self._on_glow_tick)

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
            font-size: 17px;
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
            font-size: 20px;
            line-height: 1.5;
        """)
        layout.addWidget(sub_label)

        # 最終警告時：ペナルティ警告メッセージを追加
        if self._snooze_count >= 2:
            penalty_label = QLabel("⚠ 閉じると水位が少し下がります")
            penalty_label.setStyleSheet(f"""
                color: {theme.get_color("accent")};
                font-family: 'Yu Gothic UI';
                font-size:14px;
            """)
            layout.addWidget(penalty_label)

        layout.addStretch()

        # ボタン行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        # 「飲んだ」メインボタン
        drink_btn = QPushButton("✔ 飲んだ")
        drink_btn.setFixedHeight(36)
        drink_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        drink_btn.setStyleSheet(f"""
            QPushButton {{
                background: {theme.get_color("btn_bg")};
                color: {theme.get_color("btn_fg")};
                font-family: 'Yu Gothic UI';
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 18px;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background: {theme.get_color("btn_hover")};
            }}
            QPushButton:pressed {{
                background: {theme.get_color("primary_dark")};
            }}
        """)
        drink_btn.clicked.connect(self._on_drink)
        btn_row.addWidget(drink_btn, stretch=1)

        if self._snooze_count >= 2:
            # 最終警告状態：「閉じる」ボタンを表示
            close_btn = QPushButton("閉じる")
            close_btn.setFixedHeight(28)
            close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            close_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {theme.get_color("accent")};
                    font-family: 'Yu Gothic UI';
                    font-size: 16px;
                    border: 1px solid {theme.get_color("accent")};
                    border-radius: 14px;
                    padding: 0 10px;
                }}
                QPushButton:hover {{
                    background: {theme.get_color("bg2")};
                    color: {theme.get_color("primary_dark")};
                    border-color: {theme.get_color("primary_dark")};
                }}
                QPushButton:pressed {{
                    background: {theme.get_color("bg")};
                }}
            """)
            close_btn.clicked.connect(self._on_close_btn)
            btn_row.addWidget(close_btn, stretch=1)
        else:
            # 通常状態（0〜1回目）：「あとで」ボタンを表示
            snooze_btn = QPushButton("あとで")
            snooze_btn.setFixedHeight(36)
            snooze_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            snooze_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {theme.get_color("primary")};
                    font-family: 'Yu Gothic UI';
                    font-size: 16px;
                    font-weight: bold;
                    border: 2px solid {theme.get_color("primary")};
                    border-radius: 18px;
                    padding: 0 20px;
                }}
                QPushButton:hover {{
                    background: {theme.get_color("bg")};
                }}
                QPushButton:pressed {{
                    background: {theme.get_color("bg2")};
                }}
            """)
            snooze_btn.clicked.connect(self._on_snooze)
            btn_row.addWidget(snooze_btn, stretch=1)

        layout.addLayout(btn_row)

    # ----------------------------------------------------------
    # 描画
    # ----------------------------------------------------------
    def paintEvent(self, event):
        """角丸カード型の背景を描画（無視回数・グロー状態に応じて枠を強調）"""
        theme = self._theme
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self._opacity)

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

        # 枠線（グロー中はアニメーション、通常は無視回数に応じて強調）
        if self._glow_active:
            # グロー：sin波でアルファ値を変化させた発光枠
            glow_alpha = int(120 + 100 * math.sin(self._glow_phase * 2 * math.pi))
            border_color = QColor(theme.get_color("primary"))
            border_color.setAlpha(glow_alpha)
            border_width = 2.5

            # 外側に薄いグロー層を追加
            glow_outer = QColor(theme.get_color("primary"))
            glow_outer.setAlpha(int(40 * math.sin(self._glow_phase * 2 * math.pi) + 40))
            outer_pen = QPen(glow_outer, 5.0)
            painter.setPen(outer_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(3, 3, w - 6, h - 6, 15, 15)
        else:
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
        self._fade_timer.start()

    # ----------------------------------------------------------
    # フェード・グローアニメーション
    # ----------------------------------------------------------
    def _on_fade_start(self):
        """25秒経過：少し透明にしてグローアニメーション開始"""
        self._opacity = 0.72
        self.setWindowOpacity(self._opacity)
        self._glow_active = True
        self._glow_phase = 0.0
        self._glow_timer.start()

    def _on_glow_tick(self):
        """グローアニメーションの1フレーム更新"""
        self._glow_phase = (self._glow_phase + _GLOW_INTERVAL_MS / _GLOW_CYCLE_MS) % 1.0
        self.update()

    # ----------------------------------------------------------
    # 内部スロット（シグナル発行のみ、ロジックなし）
    # ----------------------------------------------------------
    def _on_drink(self):
        self._action_taken = True
        self._stop_animations()
        self.drink_signal.emit()
        self.close()

    def _on_snooze(self):
        """「あとで」ボタン押下：スヌーズシグナルを発行して閉じる（5分後に再通知）"""
        self._action_taken = True
        self._stop_animations()
        self.snooze_signal.emit()
        self.close()

    def _on_close_btn(self):
        """「閉じる」ボタン押下（最終警告時）：close_signalを発行して閉じる"""
        self._action_taken = True
        self._stop_animations()
        self.close_signal.emit()
        self.close()

    def _stop_animations(self):
        """タイマー・アニメーションを全停止"""
        self._fade_timer.stop()
        self._glow_timer.stop()
        self._glow_active = False
