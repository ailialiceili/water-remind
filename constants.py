"""
constants.py
定数・カラーテーマ定義・設定I/O・メッセージ
"""

import json
import os

# ============================================================
# 定数
# ============================================================
DEFAULT_INTERVAL_MIN = 20          # デフォルト通知間隔（分）
REMIND_INTERVAL_SEC = DEFAULT_INTERVAL_MIN * 60
POPUP_AUTO_CLOSE_SEC = 25          # 通知自動消去（秒）
MAX_DRINK_COUNT = 8                # 満水とみなす回数
WINDOW_WIDTH = 300
WINDOW_HEIGHT = 440
ANIMATION_DURATION_MS = 500        # 水位アニメーション（ms）

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

# 無視回数に応じたメッセージ（優しい表現）
IGNORED_MESSAGES = [
    # ignore_count == 1
    [
        "お忙しいですか？少しだけ休憩しませんか 🌿",
        "ちょっとひと息、水を飲んでみてください",
        "気づいたときが飲みどきです 💧",
    ],
    # ignore_count == 2
    [
        "もしかして忘れていましたか？大丈夫ですよ 😊",
        "少しずつでいいので、水分補給を心がけましょう",
        "体が水を求めているかもしれません 🌊",
    ],
    # ignore_count >= 3
    [
        "水分補給は大切です",
        "お体のために、ほんの一口だけでも飲んでみてください",
        "長時間水を飲んでいないかもしれません。ご自愛ください 💙",
    ],
]


# ============================================================
# カラーテーマ定義
# ============================================================
THEMES = {
    "水色(ウォーター)": {
        "bg": "#EAF6FB", "bg2": "#D6EEF8",
        "primary": "#5BB8D4", "primary_dark": "#2A7FA8",
        "accent": "#3A9EC2", "water_top": "#A8DDEF", "water_bot": "#3A9EC2",
        "cup_outline": "#88CCEE", "text": "#1A4A6B", "text_light": "#4A8AAA",
        "btn_bg": "#5BB8D4", "btn_hover": "#3A9EC2", "shadow": "#B0D8EC",
    },
    "ピンク(ストロベリーフィズ)": {
        "bg": "#FFF0F5", "bg2": "#FFD6E7",
        "primary": "#E87DA0", "primary_dark": "#B5476A",
        "accent": "#D45C85", "water_top": "#F7B8CF", "water_bot": "#D45C85",
        "cup_outline": "#F0A0C0", "text": "#6B1A3A", "text_light": "#AA4A70",
        "btn_bg": "#E87DA0", "btn_hover": "#D45C85", "shadow": "#F0C0D5",
    },
    "黄色(バナナオレ)": {
        "bg": "#FFFDE7", "bg2": "#FFF9C4",
        "primary": "#F9C846", "primary_dark": "#C49A00",
        "accent": "#F0B800", "water_top": "#FFE57F", "water_bot": "#F0B800",
        "cup_outline": "#FFD740", "text": "#5C4A00", "text_light": "#9A7A00",
        "btn_bg": "#F9C846", "btn_hover": "#F0B800", "shadow": "#FFE082",
    },
    "緑(抹茶ラテ)": {
        "bg": "#F1F8E9", "bg2": "#DCEDC8",
        "primary": "#66BB6A", "primary_dark": "#2E7D32",
        "accent": "#43A047", "water_top": "#A5D6A7", "water_bot": "#43A047",
        "cup_outline": "#81C784", "text": "#1B5E20", "text_light": "#4A8A50",
        "btn_bg": "#66BB6A", "btn_hover": "#43A047", "shadow": "#C8E6C9",
    },
    "紫(グレープソーダ)": {
        "bg": "#F3E5F5", "bg2": "#E1BEE7",
        "primary": "#AB47BC", "primary_dark": "#6A1B9A",
        "accent": "#8E24AA", "water_top": "#CE93D8", "water_bot": "#8E24AA",
        "cup_outline": "#BA68C8", "text": "#4A1A6B", "text_light": "#7A4A9A",
        "btn_bg": "#AB47BC", "btn_hover": "#8E24AA", "shadow": "#D1B0DC",
    },
    "白(ミルク)": {
        "bg": "#FAFAFA", "bg2": "#F0F0F0",
        "primary": "#90A4AE", "primary_dark": "#455A64",
        "accent": "#607D8B", "water_top": "#CFD8DC", "water_bot": "#607D8B",
        "cup_outline": "#B0BEC5", "text": "#263238", "text_light": "#607D8B",
        "btn_bg": "#90A4AE", "btn_hover": "#607D8B", "shadow": "#CFD8DC",
    },
    "黒(ブラックコーヒー)": {
        "bg": "#1E1E2E", "bg2": "#181825",
        "primary": "#89B4FA", "primary_dark": "#74C7EC",
        "accent": "#89DCEB", "water_top": "#89B4FA", "water_bot": "#74C7EC",
        "cup_outline": "#6C7086", "text": "#CDD6F4", "text_light": "#A6ADC8",
        "btn_bg": "#89B4FA", "btn_hover": "#74C7EC", "shadow": "#313244",
    },
}

DEFAULT_THEME_NAME = "水色(ウォーター)"

# 設定ファイルパス
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")


# ============================================================
# 設定の保存・読み込み
# ============================================================
def load_settings() -> dict:
    """設定ファイルを読み込む。ファイルが無い場合はデフォルト値を返す。"""
    defaults = {
        "interval": DEFAULT_INTERVAL_MIN,
        "theme": DEFAULT_THEME_NAME,
    }
    if not os.path.exists(SETTINGS_FILE):
        return defaults
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # バリデーション
        interval = data.get("interval", defaults["interval"])
        if not isinstance(interval, int) or not (5 <= interval <= 45):
            interval = defaults["interval"]
        theme = data.get("theme", defaults["theme"])
        if theme not in THEMES:
            theme = defaults["theme"]
        return {"interval": interval, "theme": theme}
    except Exception:
        return defaults


def save_settings(interval: int, theme: str) -> None:
    """設定をJSONファイルに保存する。"""
    data = {"interval": interval, "theme": theme}
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
