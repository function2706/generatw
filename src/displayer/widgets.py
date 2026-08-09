"""
GUI 部品

テーマ済みの再利用ウィジェット (見出し付きカード, ラベル付き入力欄など) を提供する
"""

from __future__ import annotations

import tkinter
from collections.abc import Callable
from tkinter import ttk

from displayer import theme
from displayer.theme import STYLES


def carded_section(parent: ttk.Frame, text: str, row: int, pady: tuple[int, int] = (12, 2)):
    """
    「見出しラベル + カード枠」を縦に 2 行占有して配置し, カード枠を返す\n
    parent は columnconfigure(0, weight=1) 済みであること\n
    row は論理行 (内部で見出し=row*2, カード=row*2+1 を使用)

    Args:
        parent (ttk.Frame): 配置先
        text (str): 見出し文言
        row (int): 論理行番号 (0 起算)
        pady (tuple[int, int]): 見出し上下の余白

    Returns:
        ttk.Frame: カード枠 (padding 済み)
    """
    ttk.Label(parent, text=text, style=STYLES.section).grid(
        row=row * 2, column=0, sticky="w", padx=4, pady=pady
    )
    card = ttk.Frame(parent, style=STYLES.card, padding=12)
    card.grid(row=row * 2 + 1, column=0, sticky="ew", padx=2)
    return card


def field_entry(
    parent: ttk.Frame,
    label: str,
    row: int,
    col: int,
    width: int,
    default: str,
    on_change: Callable[[], None] | None = None,
) -> ttk.Entry:
    """
    「ラベル + 入力欄」を横並びで配置する (2 カラム占有)

    Args:
        parent (ttk.Frame): 配置先
        label (str): ラベル文言
        row (int): 行
        col (int): 開始カラム (label=col, entry=col+1)
        width (int): 入力欄の文字幅
        default (str): 初期値
        on_change (Callable | None): FocusOut / Return 時の処理

    Returns:
        ttk.Entry: 入力欄
    """
    ttk.Label(parent, text=label, style=STYLES.muted).grid(
        row=row, column=col, padx=(0, 6), pady=5, sticky="e"
    )
    entry = ttk.Entry(parent, width=width)
    entry.grid(row=row, column=col + 1, padx=(0, 14), pady=5, sticky="w")
    entry.insert(0, default)
    entry.bind("<Return>", lambda e: e.widget.master.focus_set())
    if on_change is not None:
        entry.bind("<FocusOut>", lambda e: on_change())
    return entry


def field_value(
    parent: ttk.Frame, label: str, row: int, col: int, default: str = ""
) -> tkinter.StringVar:
    """
    「ラベル + 値ラベル」を横並びで配置し, 値側の StringVar を返す (2 カラム占有)

    Args:
        parent (ttk.Frame): 配置先
        label (str): ラベル文言
        row (int): 行
        col (int): 開始カラム
        default (str): 初期値

    Returns:
        tkinter.StringVar: 値側の可変文字列
    """
    ttk.Label(parent, text=label, style=STYLES.muted).grid(
        row=row, column=col, padx=(0, 6), pady=5, sticky="e"
    )
    var = tkinter.StringVar(value=default)
    ttk.Label(parent, textvariable=var, style=STYLES.value).grid(
        row=row, column=col + 1, padx=(0, 14), pady=5, sticky="w"
    )
    return var


def action_button(
    parent: ttk.Frame,
    text: str,
    command: Callable[[], None],
    accent: bool = False,
    width: int | None = None,
    **grid,
) -> ttk.Button:
    """
    アクションボタンを配置する

    Args:
        parent (ttk.Frame): 配置先
        text (str): 文言
        command (Callable): ハンドラ
        accent (bool): 主ボタンとして強調するか
        width (int | None): 文字幅を固定する場合に指定 (None で内容に合わせる)
        **grid: grid オプション (row, column, ...)

    Returns:
        ttk.Button: ボタン
    """
    style = STYLES.accent_button if accent else "TButton"
    kwargs = {"width": width} if width is not None else {}
    btn = ttk.Button(parent, text=text, command=command, style=style, **kwargs)
    grid.setdefault("padx", 3)
    grid.setdefault("pady", 3)
    grid.setdefault("sticky", "w")
    btn.grid(**grid)
    return btn


def bind_focus_clear(widget: tkinter.Misc, root: tkinter.Misc) -> None:
    """
    入力欄以外をクリックしたときにフォーカスを外す挙動を, 配下へ再帰的に付与する\n
    (入力欄の FocusOut を確実に発火させるため)

    Args:
        widget (tkinter.Misc): 起点ウィジェット
        root (tkinter.Misc): フォーカスを移す先
    """

    def handler(event: tkinter.Event) -> None:
        if not isinstance(event.widget, (ttk.Entry, ttk.Combobox, tkinter.Text)):
            root.focus_set()

    def walk(w: tkinter.Misc) -> None:
        if isinstance(w, (ttk.Frame, ttk.Label, ttk.Notebook)):
            w.bind("<Button-1>", handler, add="+")
        for child in w.winfo_children():
            walk(child)

    walk(widget)


def themed_text(parent: tkinter.Misc, **kwargs) -> tkinter.Text:
    """
    現在のパレットで着色した tkinter.Text を生成する\n
    (Text は ttk ではないため個別に配色が必要)

    Args:
        parent (tkinter.Misc): 配置先
        **kwargs: tkinter.Text へのオプション

    Returns:
        tkinter.Text: テキストウィジェット
    """
    pal = theme.current
    kwargs.setdefault("wrap", "none")
    kwargs.setdefault("relief", "flat")
    kwargs.setdefault("borderwidth", 8)
    text = tkinter.Text(
        parent,
        background=pal.field,
        foreground=pal.text,
        insertbackground=pal.text,
        selectbackground=pal.selection,
        selectforeground=pal.text,
        highlightthickness=1,
        highlightbackground=pal.border,
        highlightcolor=pal.accent,
        **kwargs,
    )
    return text


def retheme_text(text: tkinter.Text) -> None:
    """
    既存の tkinter.Text を現在のパレットへ追従させる

    Args:
        text (tkinter.Text): 対象
    """
    pal = theme.current
    try:
        text.configure(
            background=pal.field,
            foreground=pal.text,
            insertbackground=pal.text,
            selectbackground=pal.selection,
            selectforeground=pal.text,
            highlightbackground=pal.border,
            highlightcolor=pal.accent,
        )
    except tkinter.TclError:
        pass


def apply_toplevel_bg(win: tkinter.Toplevel | tkinter.Tk) -> None:
    """
    Toplevel / Tk の地色を現在のパレットに合わせる

    Args:
        win: 対象ウィンドウ
    """
    try:
        win.configure(background=theme.current.bg)
    except tkinter.TclError:
        pass
