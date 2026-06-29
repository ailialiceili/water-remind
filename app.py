"""
水飲みリマインドデスクトップアプリ（PyQt6版）
- 30分ごとに通知ポップアップを表示
- 飲水回数をカウント
- テイクアウトカップ風水位ビジュアル（グラデーション・アニメーション付き）
- マリンテイストUI
- 設定機能（通知間隔・カラーテーマ）
"""

import sys
from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtCore import QTimer

from constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    MAX_DRINK_COUNT,
    load_settings, save_settings,
)
from theme import ThemeManager
from ui_main import MainWindowUI, SettingsDialog
from ui_popup import PopupWindow


# ============================================================
# メインウィンドウ（状態管理・タイマー・シグナル接続）
# ============================================================
class MainWindow(MainWindowUI):
    def __init__(self):
        self.drink_count: int = 0
        self.ignore_count: int = 0   # 連続無視回数
        self.snooze_count: int = 0   # 連続スヌーズ回数
        self.popup: "PopupWindow | None" = None

        # 設定をファイルから読み込む（起動時自動読み込み）
        saved = load_settings()
        self.remind_interval: int = saved["interval"]

        # ThemeManager を生成してテーマを適用
        self.theme = ThemeManager(saved["theme"])

        super().__init__(theme=self.theme)

        self.remaining_time: int = self.remind_interval * 60
        self.time_label.setText(self._format_time(self.remaining_time))

        self._connect_signals()
        self._start_timer()

    # ----------------------------------------------------------
    # シグナル接続
    # ----------------------------------------------------------
    def _connect_signals(self):
        self.gear_btn.clicked.connect(self._open_settings)
        self.close_btn.clicked.connect(self.close)
        self.drink_btn.clicked.connect(self._on_drink)

    # ----------------------------------------------------------
    # 設定ダイアログ
    # ----------------------------------------------------------
    def _open_settings(self):
        dlg = SettingsDialog(
            current_interval=self.remind_interval,
            current_theme=self.theme.current_name,
            parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            settings = dlg.get_settings()
            old_interval = self.remind_interval
            self.remind_interval = settings["interval"]
            new_theme = settings["theme"]

            # テーマが変わった場合は ThemeManager を更新してUI再描画
            if new_theme != self.theme.current_name:
                self.theme.set_theme(new_theme)
                self.apply_theme_to_ui()

            # 通知間隔が変わった場合のみ残り時間をリセット
            if settings["interval"] != old_interval:
                self.remaining_time = self.remind_interval * 60
                self.time_label.setText(self._format_time(self.remaining_time))
            # 設定をファイルに保存
            save_settings(self.remind_interval, self.theme.current_name)

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
            self.remaining_time = self.remind_interval * 60

    # ----------------------------------------------------------
    # 飲んだ処理
    # ----------------------------------------------------------
    def _on_drink(self):
        self.drink_count += 1
        self.ignore_count = 0   # 飲んだらカウントリセット
        self.snooze_count = 0   # スヌーズカウントもリセット
        self.remaining_time = self.remind_interval * 60
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
        self.popup = PopupWindow(
            self,
            ignore_count=self.ignore_count,
            snooze_count=self.snooze_count,
            theme=self.theme,
        )
        self.popup.drink_signal.connect(self._on_drink)
        self.popup.snooze_signal.connect(self._on_snooze)
        self.popup.close_signal.connect(self._on_close_popup)
        self.popup.ignored_signal.connect(self._on_ignored)
        self.popup.show_at_bottom_right()

    # ----------------------------------------------------------
    # あとで（スヌーズ）処理
    # ----------------------------------------------------------
    def _on_snooze(self):
        """「あとで」ボタン押下時：snooze_countを増やしてタイマーを5分にリセット"""
        self.snooze_count += 1
        self.remaining_time = 5 * 60
        self.time_label.setText(self._format_time(self.remaining_time))

    # ----------------------------------------------------------
    # 閉じるボタン処理（最終警告時）
    # ----------------------------------------------------------
    def _on_close_popup(self):
        """「閉じる」ボタン押下時：snooze_countを増やし、水位ペナルティを適用してタイマーをリセット"""
        self.snooze_count += 1

        # 水位ペナルティ：min(snooze_count * 0.05, 0.2) だけ水位を減少
        penalty = min(self.snooze_count * 0.05, 0.2)
        current_level = min(self.drink_count / MAX_DRINK_COUNT, 1.0)
        new_level = max(current_level - penalty, 0.0)
        self.cup_widget.set_level(new_level, animate=True)

        # タイマーを通常の設定時間に戻す
        self.remaining_time = self.remind_interval * 60
        self.time_label.setText(self._format_time(self.remaining_time))

    # ----------------------------------------------------------
    # 無視カウント処理
    # ----------------------------------------------------------
    def _on_ignored(self):
        """ポップアップが無操作で閉じられた時：無視カウントを増やす"""
        self.ignore_count += 1

    # ----------------------------------------------------------
    # ユーティリティ
    # ----------------------------------------------------------
    @staticmethod
    def _format_time(seconds: int) -> str:
        seconds = max(0, seconds)
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"


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
