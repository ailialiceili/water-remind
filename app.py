"""
水飲みリマインドデスクトップアプリ（PyQt6版）
- 30分ごとに通知ポップアップを表示
- 飲水回数をカウント
- テイクアウトカップ風水位ビジュアル（グラデーション・アニメーション付き）
- マリンテイストUI
"""

import sys
import random
import math
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    pyqtProperty, QRectF, QPointF,
)
from PyQt6.QtGui import (
    QPainter, QColor, QLinearGradient, QPen, QBrush,
    QFont, QPainterPath, QRadialGradient, QPalette,
)

# ============================================================
# 定数
# ============================================================
REMIND_INTERVAL_SEC = 30 * 60      # 30分（秒）
POPUP_AUTO_CLOSE_SEC = 25          # 通知自動消去（秒）
MAX_DRINK_COUNT = 8                # 満水とみなす回数
WINDOW_WIDTH = 300
WINDOW_HEIGHT = 400
ANIMATION_DURATION_MS = 500        # 水位アニメーション（ms）

# カラースキーム（マリンテイスト）
COLOR_BG = "#EAF6FB"
COLOR_BG2 = "#D6EEF8"
COLOR_PRIMARY = "#5BB8D4"
COLOR_PRIMARY_DARK = "#2A7FA8"
COLOR_ACCENT = "#3A9EC2"
COLOR_WATER_TOP = "#A8DDEF"
COLOR_WATER_BOT = "#3A9EC2"
COLOR_CUP_OUTLINE = "#88CCEE"
COLOR_WHITE = "#FFFFFF"
COLOR_TEXT = "#1A4A6B"
COLOR_TEXT_LIGHT = "#4A8AAA"
COLOR_BTN_BG = "#5BB8D4"
COLOR_BTN_HOVER = "#3A9EC2"
COLOR_BTN_FG = "#FFFFFF"
COLOR_SHADOW = "#B0D8EC"

# ランダムメッセージ
RANDOM_MESSAGES = [
    "あと一口飲みましょう 🌊",
    "集中していると水分不足になりがちです",
    "今日は少し多めに飲むとよいかもしれません",
    "こまめな水分補給が大切です 💧",
    "一杯の水で集中力がアップします",
    "水分補給で疲れを和らげましょう",
    "健康のために水を飲む習慣をつけましょう 🐚",
    "のどが渇く前に飲むのがポイントです",
]


# ============================================================
# コップビジュアルウィジェット
# ============================================================
class CupWidget(QWidget):
    """テイクアウトカップ風の水位ビジュアルウィジェット"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(160, 200)
        self._water_level = 0.0          # 0.0〜1.0（描画用・アニメーション中間値）
        self._target_level = 0.0
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)  # ~60fps
        self._anim_timer.timeout.connect(self._anim_step)
        self._anim_start = 0.0
        self._anim_elapsed = 0
        self._anim_duration = ANIMATION_DURATION_MS
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    # ---- アニメーション ----
    def set_level(self, level: float, animate: bool = True):
        """水位を設定（0.0〜1.0）"""
        self._target_level = max(0.0, min(1.0, level))
        if animate and abs(self._target_level - self._water_level) > 0.001:
            self._anim_start = self._water_level
            self._anim_elapsed = 0
            self._anim_timer.start()
        else:
            self._water_level = self._target_level
            self.update()

    def _anim_step(self):
        self._anim_elapsed += 16
        t = min(self._anim_elapsed / self._anim_duration, 1.0)
        # ease out cubic
        t_ease = 1 - (1 - t) ** 3
        self._water_level = self._anim_start + (self._target_level - self._anim_start) * t_ease
        self.update()
        if t >= 1.0:
            self._anim_timer.stop()
            self._water_level = self._target_level

    # ---- 描画 ----
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()

        # カップ形状パラメータ（テイクアウトカップ風：上が少し広い台形）
        margin_top = 20
        margin_bot = 10
        cup_top_w = 110
        cup_bot_w = 80
        cup_top_y = margin_top + 10
        cup_bot_y = h - margin_bot
        cup_cx = w // 2

        cup_tl = QPointF(cup_cx - cup_top_w / 2, cup_top_y)
        cup_tr = QPointF(cup_cx + cup_top_w / 2, cup_top_y)
        cup_br = QPointF(cup_cx + cup_bot_w / 2, cup_bot_y)
        cup_bl = QPointF(cup_cx - cup_bot_w / 2, cup_bot_y)

        # カップのクリップパス（角丸台形）
        cup_path = QPainterPath()
        cup_path.moveTo(cup_tl.x() + 8, cup_tl.y())
        cup_path.lineTo(cup_tr.x() - 8, cup_tr.y())
        cup_path.quadTo(cup_tr.x(), cup_tr.y(), cup_tr.x() - 2, cup_tr.y() + 6)
        cup_path.lineTo(cup_br.x() + 2, cup_br.y() - 8)
        cup_path.quadTo(cup_br.x(), cup_br.y(), cup_br.x() - 8, cup_br.y())
        cup_path.lineTo(cup_bl.x() + 8, cup_bl.y())
        cup_path.quadTo(cup_bl.x(), cup_bl.y(), cup_bl.x() + 2, cup_bl.y() - 8)
        cup_path.lineTo(cup_tl.x() - 2, cup_tl.y() + 6)
        cup_path.quadTo(cup_tl.x(), cup_tl.y(), cup_tl.x() + 8, cup_tl.y())
        cup_path.closeSubpath()

        # カップ背景（半透明白）
        painter.save()
        painter.setClipPath(cup_path)
        bg_color = QColor(255, 255, 255, 180)
        painter.fillPath(cup_path, QBrush(bg_color))

        # 水の描画（グラデーション）
        if self._water_level > 0.001:
            cup_inner_h = cup_bot_y - cup_top_y
            water_h = cup_inner_h * self._water_level
            water_top_y = cup_bot_y - water_h

            # 水位での左右x（線形補間）
            def x_at(y):
                t = (y - cup_top_y) / (cup_bot_y - cup_top_y)
                lx = (cup_cx - cup_top_w / 2) + ((cup_cx - cup_bot_w / 2) - (cup_cx - cup_top_w / 2)) * t
                rx = (cup_cx + cup_top_w / 2) + ((cup_cx + cup_bot_w / 2) - (cup_cx + cup_top_w / 2)) * t
                return lx, rx

            wl_top, wr_top = x_at(water_top_y)
            wl_bot, wr_bot = x_at(cup_bot_y)

            water_path = QPainterPath()
            water_path.moveTo(wl_top, water_top_y)
            water_path.lineTo(wr_top, water_top_y)
            water_path.lineTo(wr_bot, cup_bot_y)
            water_path.lineTo(wl_bot, cup_bot_y)
            water_path.closeSubpath()

            # グラデーション（上：薄い水色、下：濃い水色）
            grad = QLinearGradient(0, water_top_y, 0, cup_bot_y)
            grad.setColorAt(0.0, QColor(COLOR_WATER_TOP))
            grad.setColorAt(1.0, QColor(COLOR_WATER_BOT))
            painter.fillPath(water_path, QBrush(grad))

            # 水面ハイライト（白い半透明ライン）
            highlight_pen = QPen(QColor(255, 255, 255, 160), 2.5)
            painter.setPen(highlight_pen)
            painter.drawLine(
                QPointF(wl_top + 6, water_top_y + 3),
                QPointF(wr_top - 6, water_top_y + 3),
            )

            # 水面の波（サイン波風）
            wave_pen = QPen(QColor(255, 255, 255, 100), 1.5)
            painter.setPen(wave_pen)
            wave_path = QPainterPath()
            steps = 20
            for i in range(steps + 1):
                fx = wl_top + (wr_top - wl_top) * i / steps
                fy = water_top_y + math.sin(i / steps * math.pi * 2) * 2
                if i == 0:
                    wave_path.moveTo(fx, fy)
                else:
                    wave_path.lineTo(fx, fy)
            painter.drawPath(wave_path)

        painter.restore()

        # カップ枠線（角丸台形）
        outline_pen = QPen(QColor(COLOR_CUP_OUTLINE), 2.5)
        painter.setPen(outline_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(cup_path)

        # カップ上部の縁（太め）
        rim_pen = QPen(QColor(COLOR_CUP_OUTLINE), 4)
        rim_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(rim_pen)
        painter.drawLine(
            QPointF(cup_tl.x() + 4, cup_tl.y()),
            QPointF(cup_tr.x() - 4, cup_tr.y()),
        )

        # ストロー
        straw_x = cup_cx + cup_top_w / 2 - 22
        straw_pen = QPen(QColor(COLOR_PRIMARY_DARK), 5)
        straw_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(straw_pen)
        painter.drawLine(
            QPointF(straw_x, cup_top_y - 35),
            QPointF(straw_x + 4, cup_bot_y - 30),
        )

        # ワッペン風デコレーション（波モチーフ）
        self._draw_badge(painter, cup_cx, cup_top_y + (cup_bot_y - cup_top_y) * 0.55)

        # 満水テキスト
        if self._water_level >= 1.0:
            painter.setPen(QPen(QColor(COLOR_WHITE)))
            font = QFont("Yu Gothic UI", 11, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(
                QRectF(cup_cx - 40, cup_top_y + 10, 80, 30),
                Qt.AlignmentFlag.AlignCenter,
                "満水！",
            )

    def _draw_badge(self, painter: QPainter, cx: float, cy: float):
        """ワッペン風の波・水滴モチーフを描画"""
        painter.save()
        painter.translate(cx, cy)

        # 小さな水滴アイコン
        drop_color = QColor(COLOR_PRIMARY_DARK)
        drop_color.setAlpha(120)
        painter.setBrush(QBrush(drop_color))
        painter.setPen(Qt.PenStyle.NoPen)

        drop_path = QPainterPath()
        drop_path.moveTo(0, -12)
        drop_path.cubicTo(-8, -4, -8, 4, 0, 8)
        drop_path.cubicTo(8, 4, 8, -4, 0, -12)
        painter.drawPath(drop_path)

        # 小さな波線
        wave_color = QColor(COLOR_PRIMARY)
        wave_color.setAlpha(100)
        wave_pen = QPen(wave_color, 1.5)
        wave_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(wave_pen)
        for dy in [-18, -14]:
            wp = QPainterPath()
            wp.moveTo(-14, dy)
            wp.cubicTo(-8, dy - 3, -4, dy + 3, 0, dy)
            wp.cubicTo(4, dy - 3, 8, dy + 3, 14, dy)
            painter.drawPath(wp)

        painter.restore()


# ============================================================
# メインウィンドウ
# ============================================================
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.drink_count: int = 0
        self.remaining_time: int = REMIND_INTERVAL_SEC
        self.popup: "PopupWindow | None" = None

        self._setup_window()
        self._build_ui()
        self._start_timer()

    def _setup_window(self):
        self.setWindowTitle("水飲みリマインド")
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # ドラッグ移動用
        self._drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def paintEvent(self, event):
        """角丸ウィンドウ背景を描画"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 影（外側）
        shadow_color = QColor(COLOR_SHADOW)
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
        grad.setColorAt(0.0, QColor(COLOR_BG))
        grad.setColorAt(1.0, QColor(COLOR_BG2))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(4, 4, WINDOW_WIDTH - 8, WINDOW_HEIGHT - 8, 18, 18)

        # 上部アクセントバー
        accent_grad = QLinearGradient(0, 0, WINDOW_WIDTH, 0)
        accent_grad.setColorAt(0.0, QColor(COLOR_PRIMARY))
        accent_grad.setColorAt(1.0, QColor(COLOR_ACCENT))
        painter.setBrush(QBrush(accent_grad))
        painter.drawRoundedRect(4, 4, WINDOW_WIDTH - 8, 6, 3, 3)

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(0)

        # ---- 閉じるボタン（右上） ----
        close_row = QHBoxLayout()
        close_row.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLOR_TEXT_LIGHT};
                font-size: 14px;
                border: none;
                border-radius: 14px;
            }}
            QPushButton:hover {{
                background: {COLOR_SHADOW};
                color: {COLOR_TEXT};
            }}
        """)
        close_btn.clicked.connect(self.close)
        close_row.addWidget(close_btn)
        root_layout.addLayout(close_row)

        # ---- 上部：飲水回数 ----
        count_frame = QVBoxLayout()
        count_frame.setSpacing(2)

        label_title = QLabel("本日の飲水回数")
        label_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_title.setStyleSheet(f"""
            color: {COLOR_TEXT_LIGHT};
            font-family: 'Yu Gothic UI';
            font-size: 11px;
            letter-spacing: 1px;
        """)
        count_frame.addWidget(label_title)

        self.count_label = QLabel("0 回")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label.setStyleSheet(f"""
            color: {COLOR_PRIMARY_DARK};
            font-family: 'Yu Gothic UI';
            font-size: 32px;
            font-weight: bold;
        """)
        count_frame.addWidget(self.count_label)
        root_layout.addLayout(count_frame)

        root_layout.addSpacing(8)

        # ---- 中央：コップビジュアル ----
        cup_row = QHBoxLayout()
        cup_row.addStretch()
        self.cup_widget = CupWidget()
        cup_row.addWidget(self.cup_widget)
        cup_row.addStretch()
        root_layout.addLayout(cup_row)

        root_layout.addSpacing(8)

        # ---- 下部：残り時間 ----
        time_frame = QVBoxLayout()
        time_frame.setSpacing(2)

        label_time_title = QLabel("次の通知まで")
        label_time_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_time_title.setStyleSheet(f"""
            color: {COLOR_TEXT_LIGHT};
            font-family: 'Yu Gothic UI';
            font-size: 11px;
            letter-spacing: 1px;
        """)
        time_frame.addWidget(label_time_title)

        self.time_label = QLabel(self._format_time(REMIND_INTERVAL_SEC))
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet(f"""
            color: {COLOR_PRIMARY};
            font-family: 'Yu Gothic UI';
            font-size: 26px;
            font-weight: bold;
        """)
        time_frame.addWidget(self.time_label)
        root_layout.addLayout(time_frame)

        root_layout.addSpacing(12)

        # ---- 手動「飲んだ」ボタン（メイン画面） ----
        drink_btn = QPushButton("💧 飲んだ")
        drink_btn.setFixedHeight(40)
        drink_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        drink_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_BTN_BG};
                color: {COLOR_BTN_FG};
                font-family: 'Yu Gothic UI';
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-radius: 20px;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background: {COLOR_BTN_HOVER};
            }}
            QPushButton:pressed {{
                background: {COLOR_PRIMARY_DARK};
            }}
        """)
        drink_btn.clicked.connect(self._on_drink)
        root_layout.addWidget(drink_btn)

        root_layout.addStretch()

        # 初期水位
        self.cup_widget.set_level(0.0, animate=False)

    # ----------------------------------------------------------
    # タイマー
    # ----------------------------------------------------------
    def _start_timer(self):
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(1000)
        self._tick_timer.timeout.connect(self._tick)
        self._tick_timer.start()

    def _tick(self):
        self.remaining_time -= 1
        self.time_label.setText(self._format_time(self.remaining_time))
        if self.remaining_time <= 0:
            self._show_popup()
            self.remaining_time = REMIND_INTERVAL_SEC

    # ----------------------------------------------------------
    # 飲んだ処理
    # ----------------------------------------------------------
    def _on_drink(self):
        self.drink_count += 1
        self.remaining_time = REMIND_INTERVAL_SEC
        self.count_label.setText(f"{self.drink_count} 回")
        self.time_label.setText(self._format_time(self.remaining_time))
        level = min(self.drink_count / MAX_DRINK_COUNT, 1.0)
        self.cup_widget.set_level(level, animate=True)
        if self.popup and self.popup.isVisible():
            self.popup.close()

    # ----------------------------------------------------------
    # 通知ポップアップ
    # ----------------------------------------------------------
    def _show_popup(self):
        if self.popup and self.popup.isVisible():
            self.popup.close()
        self.popup = PopupWindow(self)
        self.popup.drink_signal.connect(self._on_drink)
        self.popup.show_at_bottom_right()

    # ----------------------------------------------------------
    # ユーティリティ
    # ----------------------------------------------------------
    @staticmethod
    def _format_time(seconds: int) -> str:
        seconds = max(0, seconds)
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"


# ============================================================
# 通知ポップアップウィンドウ
# ============================================================
class PopupWindow(QWidget):
    from PyQt6.QtCore import pyqtSignal
    drink_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(320, 170)
        self._build_ui()

        # 自動消去タイマー
        self._auto_close_timer = QTimer(self)
        self._auto_close_timer.setSingleShot(True)
        self._auto_close_timer.setInterval(POPUP_AUTO_CLOSE_SEC * 1000)
        self._auto_close_timer.timeout.connect(self.close)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        # メッセージ
        msg_label = QLabel("💧 水を飲みましょう")
        msg_label.setStyleSheet(f"""
            color: {COLOR_PRIMARY_DARK};
            font-family: 'Yu Gothic UI';
            font-size: 14px;
            font-weight: bold;
        """)
        layout.addWidget(msg_label)

        # ランダムサブメッセージ
        sub_label = QLabel(random.choice(RANDOM_MESSAGES))
        sub_label.setWordWrap(True)
        sub_label.setStyleSheet(f"""
            color: {COLOR_TEXT};
            font-family: 'Yu Gothic UI';
            font-size: 10px;
        """)
        layout.addWidget(sub_label)

        layout.addStretch()

        # ボタン行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        drink_btn = QPushButton("✔ 飲んだ")
        drink_btn.setFixedHeight(34)
        drink_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        drink_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_BTN_BG};
                color: {COLOR_BTN_FG};
                font-family: 'Yu Gothic UI';
                font-size: 12px;
                font-weight: bold;
                border: none;
                border-radius: 17px;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background: {COLOR_BTN_HOVER};
            }}
            QPushButton:pressed {{
                background: {COLOR_PRIMARY_DARK};
            }}
        """)
        drink_btn.clicked.connect(self._on_drink)
        btn_row.addWidget(drink_btn)

        btn_row.addStretch()

        close_btn = QPushButton("✕ 閉じる")
        close_btn.setFixedHeight(34)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLOR_TEXT_LIGHT};
                font-family: 'Yu Gothic UI';
                font-size: 11px;
                border: 1px solid {COLOR_SHADOW};
                border-radius: 17px;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background: {COLOR_BG};
                color: {COLOR_TEXT};
            }}
        """)
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def paintEvent(self, event):
        """角丸カード型の背景を描画"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()

        # 影
        for i in range(8, 0, -1):
            shadow = QColor(COLOR_PRIMARY_DARK)
            shadow.setAlpha(8 * i)
            painter.setBrush(QBrush(shadow))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(i, i, w - i * 2, h - i * 2, 16, 16)

        # 白背景
        painter.setBrush(QBrush(QColor(COLOR_WHITE)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(4, 4, w - 8, h - 8, 14, 14)

        # 上部アクセントライン
        accent_grad = QLinearGradient(0, 0, w, 0)
        accent_grad.setColorAt(0.0, QColor(COLOR_PRIMARY))
        accent_grad.setColorAt(1.0, QColor(COLOR_ACCENT))
        painter.setBrush(QBrush(accent_grad))
        painter.drawRoundedRect(4, 4, w - 8, 5, 3, 3)

        # 枠線
        border_pen = QPen(QColor(COLOR_CUP_OUTLINE), 1.5)
        painter.setPen(border_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(4, 4, w - 8, h - 8, 14, 14)

    def show_at_bottom_right(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.right() - self.width() - 20
        y = screen.bottom() - self.height() - 60
        self.move(x, y)
        self.show()
        self._auto_close_timer.start()

    def _on_drink(self):
        self.drink_signal.emit()
        self.close()


# ============================================================
# エントリーポイント
# ============================================================
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    # 画面中央に配置
    screen = QApplication.primaryScreen().availableGeometry()
    window.move(
        (screen.width() - WINDOW_WIDTH) // 2,
        (screen.height() - WINDOW_HEIGHT) // 2,
    )
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
