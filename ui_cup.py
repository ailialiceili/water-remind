"""
ui_cup.py
テイクアウトカップ風水位ビジュアルウィジェット（描画含む全て）
"""

import math
import random
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QColor, QLinearGradient, QRadialGradient,
    QPen, QBrush, QFont, QPainterPath,
)

from constants import ANIMATION_DURATION_MS
from theme import ThemeManager


# ── リップル（水面跳ね）データクラス ──────────────────────────────────────
class _Ripple:
    """水面に発生する短命なリップルエフェクト"""
    LIFETIME = 600  # ms

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.age = 0  # ms

    @property
    def progress(self) -> float:
        return min(self.age / self.LIFETIME, 1.0)

    @property
    def alive(self) -> bool:
        return self.age < self.LIFETIME


# ── CupWidget ────────────────────────────────────────────────────────────────
class CupWidget(QWidget):
    """テイクアウトカップ風の水位ビジュアルウィジェット"""

    # カップ形状定数（固定値なのでクラス変数にキャッシュ）
    _MARGIN_TOP = 20
    _MARGIN_BOT = 10
    _CUP_TOP_W = 110
    _CUP_BOT_W = 80

    def __init__(self, parent=None, theme: ThemeManager = None):
        super().__init__(parent)
        self.setFixedSize(160, 200)
        self._theme = theme if theme is not None else ThemeManager()

        # ── 水位アニメーション ──
        self._water_level = 0.0
        self._target_level = 0.0
        self._anim_start = 0.0
        self._anim_elapsed = 0
        self._anim_duration = ANIMATION_DURATION_MS

        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)   # ~60fps（水位補間）
        self._anim_timer.timeout.connect(self._anim_step)

        # ── 波アニメーション（~30fps） ──
        self._wave_phase = 0.0             # 位相（ラジアン）
        self._wave_noise = [0.0] * 6       # 水面ランダム揺れ用ノイズ
        self._wave_timer = QTimer(self)
        self._wave_timer.setInterval(33)   # ~30fps
        self._wave_timer.timeout.connect(self._wave_step)
        self._wave_timer.start()

        # ── リップルエフェクト ──
        self._ripples: list[_Ripple] = []
        self._ripple_timer = QTimer(self)
        self._ripple_timer.setInterval(16)
        self._ripple_timer.timeout.connect(self._ripple_step)

        # ── キャッシュ ──
        self._cup_path: QPainterPath | None = None
        self._cached_size = (0, 0)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    # ────────────────────────────────────────────────────────────────────────
    # 公開 API
    # ────────────────────────────────────────────────────────────────────────
    def set_level(self, level: float, animate: bool = True):
        """水位を設定（0.0〜1.0）"""
        self._target_level = max(0.0, min(1.0, level))
        if animate and abs(self._target_level - self._water_level) > 0.001:
            self._anim_start = self._water_level
            self._anim_elapsed = 0
            self._anim_timer.start()
            # 水位が上がるときにリップルを発生させる
            if self._target_level > self._water_level:
                self._spawn_ripple()
        else:
            self._water_level = self._target_level
            self.update()

    # ────────────────────────────────────────────────────────────────────────
    # 内部タイマーコールバック
    # ────────────────────────────────────────────────────────────────────────
    def _anim_step(self):
        self._anim_elapsed += 16
        t = min(self._anim_elapsed / self._anim_duration, 1.0)
        t_ease = 1 - (1 - t) ** 3          # ease-out cubic
        self._water_level = (
            self._anim_start
            + (self._target_level - self._anim_start) * t_ease
        )
        self.update()
        if t >= 1.0:
            self._anim_timer.stop()
            self._water_level = self._target_level

    def _wave_step(self):
        """波の位相を進め、ランダムノイズを更新する"""
        self._wave_phase += 0.08            # 速度調整
        # ノイズを少しずつ変化させる（スムーズなランダム揺れ）
        for i in range(len(self._wave_noise)):
            self._wave_noise[i] += random.uniform(-0.3, 0.3)
            self._wave_noise[i] = max(-1.5, min(1.5, self._wave_noise[i]))
        if self._water_level > 0.001:
            self.update()

    def _ripple_step(self):
        """リップルの経過時間を更新し、消えたものを除去する"""
        dt = 16
        for r in self._ripples:
            r.age += dt
        self._ripples = [r for r in self._ripples if r.alive]
        if not self._ripples:
            self._ripple_timer.stop()
        self.update()

    def _spawn_ripple(self):
        """水面にリップルを生成する"""
        w = self.width()
        h = self.height()
        cup_top_y, cup_bot_y, cup_cx = self._cup_geometry(w, h)
        cup_inner_h = cup_bot_y - cup_top_y
        water_h = cup_inner_h * self._target_level
        water_top_y = cup_bot_y - water_h
        lx, rx = self._x_at(water_top_y, cup_top_y, cup_bot_y, cup_cx, w)
        cx = (lx + rx) / 2 + random.uniform(-10, 10)
        self._ripples.append(_Ripple(cx, water_top_y))
        if not self._ripple_timer.isActive():
            self._ripple_timer.start()

    # ────────────────────────────────────────────────────────────────────────
    # ジオメトリヘルパー
    # ────────────────────────────────────────────────────────────────────────
    def _cup_geometry(self, w: int, h: int):
        cup_top_y = self._MARGIN_TOP + 10
        cup_bot_y = h - self._MARGIN_BOT
        cup_cx = w // 2
        return cup_top_y, cup_bot_y, cup_cx

    def _x_at(self, y: float, cup_top_y: float, cup_bot_y: float,
               cup_cx: int, w: int):
        """y座標でのカップ左右x座標を返す（線形補間）"""
        t = (y - cup_top_y) / (cup_bot_y - cup_top_y)
        half_top = self._CUP_TOP_W / 2
        half_bot = self._CUP_BOT_W / 2
        lx = (cup_cx - half_top) + ((cup_cx - half_bot) - (cup_cx - half_top)) * t
        rx = (cup_cx + half_top) + ((cup_cx + half_bot) - (cup_cx + half_top)) * t
        return lx, rx

    def _get_cup_path(self, w: int, h: int) -> QPainterPath:
        """カップ輪郭パスをキャッシュして返す"""
        if self._cup_path is not None and self._cached_size == (w, h):
            return self._cup_path

        cup_top_y, cup_bot_y, cup_cx = self._cup_geometry(w, h)
        half_top = self._CUP_TOP_W / 2
        half_bot = self._CUP_BOT_W / 2

        tl = QPointF(cup_cx - half_top, cup_top_y)
        tr = QPointF(cup_cx + half_top, cup_top_y)
        br = QPointF(cup_cx + half_bot, cup_bot_y)
        bl = QPointF(cup_cx - half_bot, cup_bot_y)

        p = QPainterPath()
        p.moveTo(tl.x() + 8, tl.y())
        p.lineTo(tr.x() - 8, tr.y())
        p.quadTo(tr.x(), tr.y(), tr.x() - 2, tr.y() + 6)
        p.lineTo(br.x() + 2, br.y() - 8)
        p.quadTo(br.x(), br.y(), br.x() - 8, br.y())
        p.lineTo(bl.x() + 8, bl.y())
        p.quadTo(bl.x(), bl.y(), bl.x() + 2, bl.y() - 8)
        p.lineTo(tl.x() - 2, tl.y() + 6)
        p.quadTo(tl.x(), tl.y(), tl.x() + 8, tl.y())
        p.closeSubpath()

        self._cup_path = p
        self._cached_size = (w, h)
        return p

    # ────────────────────────────────────────────────────────────────────────
    # 描画
    # ────────────────────────────────────────────────────────────────────────
    def paintEvent(self, event):
        theme = self._theme
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cup_top_y, cup_bot_y, cup_cx = self._cup_geometry(w, h)
        cup_path = self._get_cup_path(w, h)

        # ── カップ背景 ──────────────────────────────────────────────────────
        painter.save()
        painter.setClipPath(cup_path)

        bg_grad = QLinearGradient(0, cup_top_y, 0, cup_bot_y)
        bg_grad.setColorAt(0.0, QColor(255, 255, 255, 200))
        bg_grad.setColorAt(1.0, QColor(240, 248, 255, 160))
        painter.fillPath(cup_path, QBrush(bg_grad))

        # ── 水の描画 ────────────────────────────────────────────────────────
        if self._water_level > 0.001:
            cup_inner_h = cup_bot_y - cup_top_y
            water_h = cup_inner_h * self._water_level
            water_top_y = cup_bot_y - water_h

            wl_top, wr_top = self._x_at(water_top_y, cup_top_y, cup_bot_y, cup_cx, w)
            wl_bot, wr_bot = self._x_at(cup_bot_y,   cup_top_y, cup_bot_y, cup_cx, w)

            # 波形水面パスを生成
            wave_path = self._build_wave_surface(
                wl_top, wr_top, water_top_y,
                wl_bot, wr_bot, cup_bot_y,
            )

            # 水グラデーション（透明感を強調）
            grad = QLinearGradient(0, water_top_y, 0, cup_bot_y)
            water_top_c = QColor(theme.get_color("water_top"))
            water_bot_c = QColor(theme.get_color("water_bot"))
            water_top_c.setAlpha(200)
            water_bot_c.setAlpha(230)
            grad.setColorAt(0.0, water_top_c)
            grad.setColorAt(0.4, water_bot_c)
            grad.setColorAt(1.0, water_bot_c)
            painter.fillPath(wave_path, QBrush(grad))

            # 水面の光反射（上部ハイライト帯）
            self._draw_water_highlight(painter, wl_top, wr_top, water_top_y)

            # リップルエフェクト
            for ripple in self._ripples:
                self._draw_ripple(painter, ripple)

        painter.restore()

        # ── カップ枠線 ──────────────────────────────────────────────────────
        outline_pen = QPen(QColor(theme.get_color("cup_outline")), 2.5)
        painter.setPen(outline_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(cup_path)

        # カップ上部の縁（太め）
        rim_pen = QPen(QColor(theme.get_color("cup_outline")), 4)
        rim_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(rim_pen)
        painter.drawLine(
            QPointF(cup_cx - self._CUP_TOP_W / 2 + 4, cup_top_y),
            QPointF(cup_cx + self._CUP_TOP_W / 2 - 4, cup_top_y),
        )

        # カップ内側の光沢ライン（左端）
        gloss_grad = QLinearGradient(
            cup_cx - self._CUP_TOP_W / 2, 0,
            cup_cx - self._CUP_TOP_W / 2 + 12, 0,
        )
        gloss_grad.setColorAt(0.0, QColor(255, 255, 255, 80))
        gloss_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        gloss_pen = QPen(QBrush(gloss_grad), 8)
        gloss_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(gloss_pen)
        painter.drawLine(
            QPointF(cup_cx - self._CUP_TOP_W / 2 + 6, cup_top_y + 10),
            QPointF(cup_cx - self._CUP_BOT_W / 2 + 6, cup_bot_y - 10),
        )

        # ── ストロー ────────────────────────────────────────────────────────
        straw_x = cup_cx + self._CUP_TOP_W / 2 - 22
        straw_pen = QPen(QColor(theme.get_color("primary_dark")), 5)
        straw_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(straw_pen)
        painter.drawLine(
            QPointF(straw_x, cup_top_y - 35),
            QPointF(straw_x + 4, cup_bot_y - 30),
        )
        # ストロー光沢
        straw_gloss_pen = QPen(QColor(255, 255, 255, 80), 2)
        straw_gloss_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(straw_gloss_pen)
        painter.drawLine(
            QPointF(straw_x - 1, cup_top_y - 35),
            QPointF(straw_x + 3, cup_bot_y - 30),
        )

        # ── ワッペン（スカラップ型） ─────────────────────────────────────────
        badge_y = cup_top_y + (cup_bot_y - cup_top_y) * 0.52
        self._draw_badge(painter, cup_cx, badge_y)

        # ── 満水テキスト ────────────────────────────────────────────────────
        if self._water_level >= 1.0:
            painter.setPen(QPen(QColor(theme.get_color("white"))))
            font = QFont("Yu Gothic UI", 11, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(
                QRectF(cup_cx - 40, cup_top_y + 10, 80, 30),
                Qt.AlignmentFlag.AlignCenter,
                "満水！",
            )

    # ────────────────────────────────────────────────────────────────────────
    # 描画ヘルパー
    # ────────────────────────────────────────────────────────────────────────
    def _build_wave_surface(
        self,
        wl_top: float, wr_top: float, water_top_y: float,
        wl_bot: float, wr_bot: float, cup_bot_y: float,
    ) -> QPainterPath:
        """波形水面を持つ水領域パスを生成する"""
        path = QPainterPath()
        steps = 24
        noise = self._wave_noise
        noise_len = len(noise)

        # 上辺（波形）
        for i in range(steps + 1):
            fx = wl_top + (wr_top - wl_top) * i / steps
            # 主波 + 副波 + ノイズ
            phase = self._wave_phase
            n_idx = int(i / steps * (noise_len - 1))
            fy = (
                water_top_y
                + math.sin(i / steps * math.pi * 4 + phase) * 2.2
                + math.sin(i / steps * math.pi * 2 + phase * 0.7) * 1.2
                + noise[n_idx] * 0.6
            )
            if i == 0:
                path.moveTo(fx, fy)
            else:
                path.lineTo(fx, fy)

        # 右辺 → 下辺 → 左辺
        path.lineTo(wr_bot, cup_bot_y)
        path.lineTo(wl_bot, cup_bot_y)
        path.closeSubpath()
        return path

    def _draw_water_highlight(
        self,
        painter: QPainter,
        wl_top: float, wr_top: float, water_top_y: float,
    ):
        """水面上部の光反射ハイライトを描画する"""
        # 白い半透明の帯（水面直下）
        hl_grad = QLinearGradient(0, water_top_y, 0, water_top_y + 12)
        hl_grad.setColorAt(0.0, QColor(255, 255, 255, 120))
        hl_grad.setColorAt(1.0, QColor(255, 255, 255, 0))

        hl_path = QPainterPath()
        hl_path.moveTo(wl_top, water_top_y - 2)
        hl_path.lineTo(wr_top, water_top_y - 2)
        hl_path.lineTo(wr_top, water_top_y + 12)
        hl_path.lineTo(wl_top, water_top_y + 12)
        hl_path.closeSubpath()
        painter.fillPath(hl_path, QBrush(hl_grad))

        # 細い白ライン（水面の輝き）
        hl_pen = QPen(QColor(255, 255, 255, 180), 1.5)
        hl_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(hl_pen)
        painter.drawLine(
            QPointF(wl_top + 6, water_top_y + 2),
            QPointF(wr_top - 6, water_top_y + 2),
        )

    def _draw_ripple(self, painter: QPainter, ripple: _Ripple):
        """リップル（水面の波紋）を描画する"""
        p = ripple.progress
        # ease-out
        radius = p * 18
        alpha = int(180 * (1.0 - p))
        if alpha <= 0:
            return

        painter.save()
        pen = QPen(QColor(255, 255, 255, alpha), 1.5)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        # 楕円形（水面なので横長）
        painter.drawEllipse(
            QPointF(ripple.x, ripple.y),
            radius, radius * 0.35,
        )
        # 内側の小さな波紋
        if p < 0.6:
            inner_r = p * 8
            inner_alpha = int(140 * (1.0 - p / 0.6))
            painter.setPen(QPen(QColor(255, 255, 255, inner_alpha), 1.0))
            painter.drawEllipse(
                QPointF(ripple.x, ripple.y),
                inner_r, inner_r * 0.35,
            )
        painter.restore()

    def _draw_badge(self, painter: QPainter, cx: float, cy: float):
        """スカラップ型（花型）ワッペンを描画する"""
        theme = self._theme
        painter.save()
        painter.translate(cx, cy)

        # ── スカラップ（花型）外形パス ──────────────────────────────────────
        petal_count = 8
        outer_r = 22.0
        inner_r = 16.0
        scallop_path = QPainterPath()

        for i in range(petal_count):
            angle = math.pi * 2 * i / petal_count - math.pi / 2
            next_angle = math.pi * 2 * (i + 1) / petal_count - math.pi / 2
            mid_angle = (angle + next_angle) / 2

            # 花びら中心（外側）
            px = math.cos(mid_angle) * outer_r
            py = math.sin(mid_angle) * outer_r

            # 花びら間のくびれ（内側）
            ix = math.cos(angle) * inner_r
            iy = math.sin(angle) * inner_r

            if i == 0:
                scallop_path.moveTo(ix, iy)

            # 円弧で花びらを描く（cubicTo で近似）
            ctrl_r = outer_r * 1.15
            c1x = math.cos(angle + (mid_angle - angle) * 0.5) * ctrl_r
            c1y = math.sin(angle + (mid_angle - angle) * 0.5) * ctrl_r
            c2x = math.cos(mid_angle + (next_angle - mid_angle) * 0.5) * ctrl_r
            c2y = math.sin(mid_angle + (next_angle - mid_angle) * 0.5) * ctrl_r

            nix = math.cos(next_angle) * inner_r
            niy = math.sin(next_angle) * inner_r

            scallop_path.cubicTo(c1x, c1y, px, py, px, py)
            scallop_path.cubicTo(px, py, c2x, c2y, nix, niy)

        scallop_path.closeSubpath()

        # 背景塗り（半透明白）
        bg_color = QColor(255, 255, 255, 200)
        painter.fillPath(scallop_path, QBrush(bg_color))

        # 枠線
        outline_c = QColor(theme.get_color("primary"))
        outline_c.setAlpha(180)
        painter.setPen(QPen(outline_c, 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(scallop_path)

        # 内側の小さな円（装飾）
        inner_circle_c = QColor(theme.get_color("primary"))
        inner_circle_c.setAlpha(40)
        painter.setBrush(QBrush(inner_circle_c))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(0, 0), inner_r * 0.75, inner_r * 0.75)

        # ── 中央テキスト "water_remind" ──────────────────────────────────────
        text_color = QColor(theme.get_color("primary_dark"))
        text_color.setAlpha(200)
        painter.setPen(QPen(text_color))

        # 2行に分けて描画（"water" / "remind"）
        font_top = QFont("Yu Gothic UI", 5, QFont.Weight.Bold)
        painter.setFont(font_top)
        painter.drawText(
            QRectF(-inner_r, -inner_r * 0.75, inner_r * 2, inner_r * 0.9),
            Qt.AlignmentFlag.AlignCenter,
            "water",
        )
        font_bot = QFont("Yu Gothic UI", 4, QFont.Weight.Bold)
        painter.setFont(font_bot)
        painter.drawText(
            QRectF(-inner_r, -inner_r * 0.05, inner_r * 2, inner_r * 0.9),
            Qt.AlignmentFlag.AlignCenter,
            "remind",
        )

        painter.restore()
