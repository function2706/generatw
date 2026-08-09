"""
GUI テーマ

ライト / ダーク両対応の配色パレットと, ttk スタイルの一元設定を提供する\n
clam テーマをベースに全ウィジェットの見た目を統一する
"""

from __future__ import annotations

from dataclasses import dataclass
from tkinter import font, ttk

# =============================================================================
# 配色パレット
# =============================================================================


@dataclass(frozen=True)
class Palette:
    """
    1 テーマ分の配色定義
    """

    # 背景 (ウィンドウ地色 / カード面 / 一段沈めた面)
    bg: str
    surface: str
    surface_alt: str
    # 枠線
    border: str
    # 文字色 (通常 / 弱め / 反転)
    text: str
    muted: str
    on_accent: str
    # アクセント (主ボタン / 選択 / 進捗バー)
    accent: str
    accent_active: str
    accent_soft: str
    # 状態色 (正常 / 警告 / 異常)
    ok: str
    warn: str
    err: str
    # ウィジェット微調整
    field: str  # 入力欄の地色
    hover: str  # ボタン等のホバー地色
    selection: str  # 一覧の選択行地色


LIGHT = Palette(
    bg="#f3f4f6",
    surface="#ffffff",
    surface_alt="#eef0f3",
    border="#d5d9e0",
    text="#1f2328",
    muted="#6b7280",
    on_accent="#ffffff",
    accent="#2f6feb",
    accent_active="#2158c9",
    accent_soft="#e5edfb",
    ok="#1a7f37",
    warn="#9a6700",
    err="#cf222e",
    field="#ffffff",
    hover="#e9ebef",
    selection="#dbe6fb",
)

DARK = Palette(
    bg="#1b1e24",
    surface="#242830",
    surface_alt="#2c313b",
    border="#3a414d",
    text="#e6e8eb",
    muted="#9aa4b2",
    on_accent="#0d1117",
    accent="#4f8cf0",
    accent_active="#5f99f4",
    accent_soft="#2b3550",
    ok="#3fb950",
    warn="#d29922",
    err="#f85149",
    field="#1f232a",
    hover="#313742",
    selection="#33405c",
)


# =============================================================================
# スタイル名 (typo 防止のため定数化)
# =============================================================================


@dataclass(frozen=True)
class Styles:
    """
    アプリ内で参照する ttk スタイル名
    """

    card: str = "Card.TFrame"
    surface: str = "Surface.TFrame"
    section: str = "Section.TLabel"
    title: str = "Title.TLabel"
    muted: str = "Muted.TLabel"
    value: str = "Value.TLabel"
    ok: str = "OK.TLabel"
    warn: str = "Warn.TLabel"
    err: str = "Err.TLabel"
    accent_button: str = "Accent.TButton"


STYLES = Styles()


# =============================================================================
# フォント
# =============================================================================

_FAMILY = "Yu Gothic UI"
_SIZE = 10


def _init_fonts() -> None:
    """
    名前付きフォントを日本語向けに調整する
    """
    for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont"):
        try:
            f = font.nametofont(name)
            f.configure(family=_FAMILY, size=_SIZE)
        except Exception:
            pass


# =============================================================================
# 現在のパレット (ウィジェットから色を引くための共有状態)
# =============================================================================

current: Palette = LIGHT


def detect_os_dark() -> bool:
    """
    Windows のアプリテーマ設定がダークかどうかを判定する

    Returns:
        bool: ダークなら True (判定不能時は False)
    """
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return value == 0
    except Exception:
        return False


def resolve_mode(pref: str) -> str:
    """
    テーマ設定値を実際のモードへ解決する

    Args:
        pref (str): "auto" / "light" / "dark"

    Returns:
        str: "light" or "dark"
    """
    if pref == "dark":
        return "dark"
    if pref == "light":
        return "light"
    return "dark" if detect_os_dark() else "light"


def palette_of(mode: str) -> Palette:
    """
    モード名からパレットを取得する

    Args:
        mode (str): "light" or "dark"

    Returns:
        Palette: パレット
    """
    return DARK if mode == "dark" else LIGHT


def apply(root, pref: str = "auto") -> Palette:
    """
    root 以下の ttk スタイルを設定し, 現在のパレットを更新する\n
    テーマ切替時に再度呼ぶことで動的に見た目を差し替えられる

    Args:
        root: Tk ルート (または Toplevel)
        pref (str): テーマ設定値 ("auto" / "light" / "dark")

    Returns:
        Palette: 適用されたパレット
    """
    global current
    mode = resolve_mode(pref)
    pal = palette_of(mode)
    current = pal

    _init_fonts()

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # コンボボックスのドロップダウン (tk Listbox) はオプションDBで着色
    root.option_add("*TCombobox*Listbox.background", pal.field)
    root.option_add("*TCombobox*Listbox.foreground", pal.text)
    root.option_add("*TCombobox*Listbox.selectBackground", pal.accent)
    root.option_add("*TCombobox*Listbox.selectForeground", pal.on_accent)
    try:
        root.configure(background=pal.bg)
    except Exception:
        pass

    _configure_styles(style, pal)
    return pal


def _configure_styles(style: ttk.Style, pal: Palette) -> None:
    """
    各 ttk スタイルを設定する

    Args:
        style (ttk.Style): スタイルオブジェクト
        pal (Palette): 適用するパレット
    """
    # --- 基底 -----------------------------------------------------------------
    style.configure(
        ".",
        background=pal.bg,
        foreground=pal.text,
        fieldbackground=pal.field,
        bordercolor=pal.border,
        lightcolor=pal.border,
        darkcolor=pal.border,
        focuscolor=pal.accent,
        troughcolor=pal.surface_alt,
    )

    # --- フレーム / カード ------------------------------------------------------
    style.configure("TFrame", background=pal.bg)
    style.configure(
        STYLES.card,
        background=pal.surface,
        relief="solid",
        borderwidth=1,
        bordercolor=pal.border,
        lightcolor=pal.border,
        darkcolor=pal.border,
    )
    # カード内でウィジェットをまとめるための枠なし surface フレーム
    style.configure(STYLES.surface, background=pal.surface)

    # --- ラベル ---------------------------------------------------------------
    style.configure("TLabel", background=pal.bg, foreground=pal.text)
    style.configure(STYLES.section, background=pal.bg, foreground=pal.muted)
    style.configure(
        STYLES.title, background=pal.surface, foreground=pal.text, font=(_FAMILY, _SIZE, "bold")
    )
    style.configure(STYLES.muted, background=pal.surface, foreground=pal.muted)
    style.configure(STYLES.value, background=pal.surface, foreground=pal.text)
    for name, color in ((STYLES.ok, pal.ok), (STYLES.warn, pal.warn), (STYLES.err, pal.err)):
        style.configure(name, background=pal.bg, foreground=color)

    # --- ボタン ---------------------------------------------------------------
    style.configure(
        "TButton",
        background=pal.surface,
        foreground=pal.text,
        bordercolor=pal.border,
        lightcolor=pal.surface,
        darkcolor=pal.surface,
        relief="solid",
        borderwidth=1,
        focusthickness=0,
        padding=(10, 5),
    )
    style.map(
        "TButton",
        background=[("pressed", pal.surface_alt), ("active", pal.hover), ("disabled", pal.bg)],
        foreground=[("disabled", pal.muted)],
        bordercolor=[("active", pal.accent)],
    )
    style.configure(
        STYLES.accent_button,
        background=pal.accent,
        foreground=pal.on_accent,
        bordercolor=pal.accent,
        lightcolor=pal.accent,
        darkcolor=pal.accent,
        relief="solid",
        borderwidth=1,
        padding=(12, 5),
    )
    style.map(
        STYLES.accent_button,
        background=[
            ("pressed", pal.accent_active),
            ("active", pal.accent_active),
            ("disabled", pal.surface_alt),
        ],
        foreground=[("disabled", pal.muted)],
        bordercolor=[("disabled", pal.border)],
    )

    # --- 入力欄 ---------------------------------------------------------------
    for name in ("TEntry", "TSpinbox"):
        style.configure(
            name,
            fieldbackground=pal.field,
            foreground=pal.text,
            bordercolor=pal.border,
            lightcolor=pal.border,
            darkcolor=pal.border,
            insertcolor=pal.text,
            padding=4,
        )
        style.map(name, bordercolor=[("focus", pal.accent)])

    style.configure(
        "TCombobox",
        fieldbackground=pal.field,
        background=pal.surface,
        foreground=pal.text,
        arrowcolor=pal.muted,
        bordercolor=pal.border,
        lightcolor=pal.border,
        darkcolor=pal.border,
        padding=4,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", pal.field), ("disabled", pal.bg)],
        bordercolor=[("focus", pal.accent)],
        arrowcolor=[("disabled", pal.border)],
    )

    # --- チェックボタン --------------------------------------------------------
    style.configure(
        "TCheckbutton", background=pal.surface, foreground=pal.text, focuscolor=pal.surface
    )
    style.map(
        "TCheckbutton",
        background=[("active", pal.surface)],
        indicatorcolor=[("selected", pal.accent), ("!selected", pal.field)],
        foreground=[("disabled", pal.muted)],
    )

    # --- ノートブック ----------------------------------------------------------
    # clam 既定の Tab レイアウトから Notebook.focus を除去し, 選択タブに出る
    # 青い点線フォーカス枠を消す
    style.layout(
        "TNotebook.Tab",
        [
            (
                "Notebook.tab",
                {
                    "sticky": "nswe",
                    "children": [
                        (
                            "Notebook.padding",
                            {
                                "side": "top",
                                "sticky": "nswe",
                                "children": [("Notebook.label", {"side": "top", "sticky": ""})],
                            },
                        )
                    ],
                },
            )
        ],
    )
    # tabmargins と選択タブの expand を上端で揃え, 選択/非選択を同じ高さにする
    # (clam は既定で非選択タブを高く描くため, 選択タブを同じだけ持ち上げる)
    style.configure("TNotebook", background=pal.bg, borderwidth=0, tabmargins=(2, 6, 2, 0))
    style.configure(
        "TNotebook.Tab",
        background=pal.surface_alt,
        foreground=pal.muted,
        bordercolor=pal.border,
        lightcolor=pal.surface_alt,
        darkcolor=pal.surface_alt,
        focuscolor=pal.surface_alt,
        borderwidth=1,
        padding=(16, 6),
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", pal.surface), ("active", pal.hover)],
        foreground=[("selected", pal.text)],
        lightcolor=[("selected", pal.surface)],
        darkcolor=[("selected", pal.surface)],
        expand=[("selected", (2, 6, 2, 0))],
    )

    # --- ツリービュー ----------------------------------------------------------
    style.configure(
        "Treeview",
        background=pal.surface,
        fieldbackground=pal.surface,
        foreground=pal.text,
        bordercolor=pal.border,
        lightcolor=pal.border,
        darkcolor=pal.border,
        borderwidth=1,
        rowheight=24,
    )
    style.map(
        "Treeview",
        background=[("selected", pal.selection)],
        foreground=[("selected", pal.text)],
    )
    style.configure(
        "Treeview.Heading",
        background=pal.surface_alt,
        foreground=pal.muted,
        bordercolor=pal.border,
        relief="flat",
        padding=(6, 4),
        font=(_FAMILY, _SIZE, "bold"),
    )
    style.map("Treeview.Heading", background=[("active", pal.hover)])

    # --- 進捗バー / 区切り / スクロールバー ------------------------------------
    style.configure(
        "TProgressbar",
        background=pal.accent,
        troughcolor=pal.surface_alt,
        bordercolor=pal.border,
        lightcolor=pal.accent,
        darkcolor=pal.accent,
        thickness=14,
    )
    style.configure("TSeparator", background=pal.border)
    style.configure(
        "TScrollbar",
        background=pal.surface_alt,
        troughcolor=pal.bg,
        bordercolor=pal.border,
        arrowcolor=pal.muted,
    )
    style.map("TScrollbar", background=[("active", pal.hover)])
