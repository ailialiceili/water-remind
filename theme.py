"""
theme.py
ThemeManager - テーマ管理クラス
"""

from constants import THEMES, DEFAULT_THEME_NAME


class ThemeManager:
    """
    カラーテーマを管理するクラス。
    テーマ定義を内部に保持し、get_color() で色を取得する。
    """

    def __init__(self, theme_name: str = DEFAULT_THEME_NAME):
        self._current_name: str = ""
        self._current_theme: dict = {}
        self.set_theme(theme_name)

    def set_theme(self, name: str) -> None:
        """テーマを切り替える。存在しない名前の場合はデフォルトを適用する。"""
        if name in THEMES:
            self._current_name = name
            self._current_theme = THEMES[name]
        else:
            self._current_name = DEFAULT_THEME_NAME
            self._current_theme = THEMES[DEFAULT_THEME_NAME]

    def get_color(self, key: str) -> str:
        """
        指定キーの色コードを返す。
        特殊キー "white" と "btn_fg" は常に "#FFFFFF" を返す。
        """
        if key in ("white", "btn_fg"):
            return "#FFFFFF"
        return self._current_theme.get(key, "#000000")

    @property
    def current_name(self) -> str:
        """現在のテーマ名を返す"""
        return self._current_name
