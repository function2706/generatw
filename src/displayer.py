"""
GUI 管理クラス
"""

from __future__ import annotations

import threading
import tkinter
from dataclasses import dataclass
from tkinter import Frame, TclError, font, ttk
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageTk

from common.classes import PicStats, TaskBlueprint
from common.functions import dump_json
from common.interfaces import BackEnd, MasterIF


@dataclass(frozen=True)
class Consts:
    """
    このクラス関連の定数
    """

    # 表示する文字列の最大長
    max_output_strlen: int = 75
    # N/A テキスト
    not_available_text: str = "-"


class TipLabel:
    """
    Label とそれに付随する Tip を構築するクラス\n
    表示する文字列が最大長を超過する場合は, ラベル上の文字列を省略し,\n
    ツールチップをマウスオーバーで表示する
    """

    def __init__(self, frame: ttk.Frame, row: int, column: int, default: str, maxlen: int):
        """
        コンストラクタ

        Args:
            frame (ttk.Frame): 挿入先フレーム
            row (int): フレーム内の row
            column (int): フレーム内の column
            default (str): デフォルト値
            maxlen (int): 表示の最大長
        """
        self.tip_text = default
        self.maxlen = maxlen

        self.strvar = tkinter.StringVar(value=default)
        self.label = ttk.Label(frame, textvariable=self.strvar)
        self.label.grid(row=row, column=column, padx=6, pady=6, sticky="w")
        self.tip: tkinter.Toplevel = None

        self.label.bind("<Enter>", self.show)
        self.label.bind("<Leave>", self.hide)
        self.label.bind("<Motion>", self.move)

    def set_text(self, text: str) -> None:
        """
        Label 及び Tip に表示する文字列をセットする

        Args:
            text (str): 文字列
        """
        self.tip_text = text
        if len(text) <= self.maxlen:
            self.strvar.set(text)
        elif self.maxlen <= 3:
            self.strvar.set("." * self.maxlen)
        else:
            self.strvar.set(text[: self.maxlen - 3] + "...")

    def show(self, event: tkinter.Event = None):
        """
        マウスオーバーハンドラ

        Args:
            event (tkinter.Event, optional): イベントオブジェクト. Defaults to None.
        """
        if self.tip is not None:
            return
        elif len(self.tip_text) <= self.maxlen:
            return

        self.tip = tkinter.Toplevel(self.label)
        self.tip.wm_overrideredirect(True)
        self.tip.attributes("-topmost", True)

        x = self.label.winfo_rootx() + self.label.winfo_width()
        y = self.label.winfo_rooty() + self.label.winfo_height()
        self.tip.geometry(f"+{x}+{y}")

        label = tkinter.Label(
            self.tip,
            text=self.tip_text,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            padx=4,
            pady=2,
        )
        label.pack()

    def hide(self, event: tkinter.Event = None):
        """
        マウスアウトハンドラ

        Args:
            event (tkinter.Event, optional): イベントオブジェクト. Defaults to None.
        """
        if self.tip:
            self.tip.destroy()
            self.tip = None

    def move(self, event: tkinter.Event):
        """
        マウスムーブハンドラ

        Args:
            event (tkinter.Event): イベントオブジェクト
        """
        if not self.tip:
            return

        x = event.x_root + 12
        y = event.y_root + 12

        self.tip.geometry(f"+{x}+{y}")


class InfoTree:
    """
    ツリービューを構築するクラス
    """

    def __init__(self, meta_frame: ttk.Frame, infotbl: list[tuple[str, ...]]):
        """
        コンストラクタ\n
        infotbl の先頭行がカラムの見出しになる\n

        ex.)\n
        data = [\n
            ("キー", "値", "備考"),\n
            ("key1", "val11", "val12"),\n
            ("key2", "val21", "val22"),\n
            ("key3", "val31", "val32"),\n
        ]

        Args:
            meta_frame (ttk.Frame): 配置先フレーム
            infotbl (list[tuple[str, ...]]): 初期値テーブル
        """
        self.frame = ttk.Frame(meta_frame)
        self.frame.pack(fill="both", expand=True)
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)

        self.columns = infotbl[0]

        self.tree = ttk.Treeview(self.frame, columns=self.columns, show="headings")
        xscroll = ttk.Scrollbar(self.frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=xscroll.set)

        self._font = font.nametofont("TkDefaultFont")

        for col in self.columns:
            self.tree.column(col, width=50, stretch=False, anchor="w")
            self.tree.heading(col, text=col, anchor="w")

        self.tree.grid(row=0, column=0, sticky="nsew")
        xscroll.grid(row=1, column=0, sticky="ew")

        self._key_to_iid = {}
        for row in infotbl[1:]:
            key = row[0]
            iid = self.tree.insert("", "end", values=row)
            self._key_to_iid[key] = iid

        for col_idx, _ in enumerate(self.columns):
            self.adjust(col_idx)

    def adjust(self, col_idx: int):
        """
        特定列の幅を内容に合わせて調整する

        Args:
            col_idx (int): 調整する列のインデックス
        """
        if not self.tree.winfo_exists():
            return

        col = self.columns[col_idx]
        max_width = self._font.measure(col)
        for iid in self.tree.get_children():
            text = str(self.tree.item(iid, "values")[col_idx])
            w = self._font.measure(text)
            if w > max_width:
                max_width = w

        max_width += 20
        self.tree.column(col, width=max_width)

    def set(self, key: str, val: Any, idx: int = 1) -> None:
        """
        指定行・列の値を書き換える

        Args:
            key (str): 書き換える行のキー
            idx (int): 書き換える列のインデックス
            val (str): 値(未指定で 1)
        """
        if not self.tree.winfo_exists() or key not in self._key_to_iid:
            return

        iid = self._key_to_iid[key]
        values = list(self.tree.item(iid, "values"))

        if not (0 <= idx < len(values)):
            return

        values[idx] = str(val)
        self.tree.item(iid, values=values)

        self.adjust(idx)


class Displayer:
    """
    GUI 管理クラス
    """

    class ConfigWindow:
        class MainTab:
            """
            メインタブ
            """

            class ButtonFrame:
                """
                ボタンフレーム
                """

                def __init__(self, owner: Displayer.ConfigWindow.MainTab):
                    """
                    ボタンフレームコンストラクタ

                    Args:
                        owner (Displayer.ConfigWindow.MainTab): MainTab インスタンス
                    """
                    self.super_owner = owner

                    self.button_frame = ttk.Frame(owner.main_frame)
                    self.button_frame.grid(row=0, column=0, sticky="w")

                    # ボタン(タスク登録)
                    self.gen_button = ttk.Button(
                        self.button_frame,
                        text="タスク登録",
                        command=owner.super_owner.super_owner.master.reserve_task,
                    )
                    self.gen_button.grid(row=0, column=0, padx=6, pady=6, sticky="w")
                    # ボタン(中断)
                    self.interrupt_button = ttk.Button(
                        self.button_frame,
                        text="中断",
                        command=owner.super_owner.super_owner.master.on_interrupt,
                    )
                    self.interrupt_button.grid(row=0, column=1, padx=6, pady=6, sticky="w")
                    # タスククリア
                    self.clear_button = ttk.Button(
                        self.button_frame,
                        text="タスククリア",
                        command=owner.super_owner.super_owner.master.clear_tasks,
                    )
                    self.clear_button.grid(row=0, column=2, padx=6, pady=6, sticky="w")
                    # ボタン(画像を表示)
                    self.output_button = ttk.Button(
                        self.button_frame,
                        text="画像を表示",
                        command=owner.super_owner.super_owner.on_open_pic_window,
                    )
                    self.output_button.grid(row=1, column=0, padx=6, pady=6, sticky="w")
                    # ボタン(情報を表示)
                    self.open_info_button = ttk.Button(
                        self.button_frame,
                        text="情報を表示",
                        command=owner.super_owner.super_owner.on_open_info_window,
                    )
                    self.open_info_button.grid(row=1, column=1, padx=6, pady=6, sticky="w")

            class SDInteriorConfigFrame:
                """
                SD 内部設定フレーム
                """

                def __init__(self, owner: Displayer.ConfigWindow.MainTab):
                    """
                    SD 内部設定フレームコンストラクタ

                    Args:
                        owner (Displayer.ConfigWindow.MainTab): MainTab インスタンス
                    """
                    self.super_owner = owner

                    self.sd_interior_config_frame = ttk.Frame(owner.main_frame)
                    self.sd_interior_config_frame.grid(row=1, column=0, sticky="w")

                    # テキストボックス(幅)
                    self.width_entry = owner.super_owner.super_owner.put_textbox(
                        self.sd_interior_config_frame, "幅", 1, 0, 5, str(540), "w"
                    )
                    # テキストボックス(高さ)
                    self.height_entry = owner.super_owner.super_owner.put_textbox(
                        self.sd_interior_config_frame, "高さ", 1, 2, 5, str(960), "w"
                    )
                    # テキストボックス(ステップ数)
                    self.steps_entry = owner.super_owner.super_owner.put_textbox(
                        self.sd_interior_config_frame, "Steps", 2, 0, 4, str(30), "w"
                    )
                    # テキストボックス(生成数)
                    self.batch_size_entry = owner.super_owner.super_owner.put_textbox(
                        self.sd_interior_config_frame, "生成数", 2, 2, 4, str(2), "w"
                    )

            class SDExteriorConfigFrame:
                """
                SD 外部設定フレーム
                """

                def __init__(self, owner: Displayer.ConfigWindow.MainTab):
                    """
                    SD 外部設定フレームコンストラクタ

                    Args:
                        owner (Displayer.ConfigWindow.MainTab): MainTab インスタンス
                    """
                    self.super_owner = owner

                    self.sd_exterior_config_frame = ttk.Frame(owner.main_frame)
                    self.sd_exterior_config_frame.grid(row=2, column=0, sticky="w")

                    # テキストボックス(IPアドレス)
                    self.ipaddr_entry = owner.super_owner.super_owner.put_textbox(
                        self.sd_exterior_config_frame, "IPアドレス", 0, 0, 16, "127.0.0.1", "w"
                    )
                    # テキストボックス(ポート)
                    type = owner.super_owner.super_owner.master.backend_type
                    self.port_entry = owner.super_owner.super_owner.put_textbox(
                        self.sd_exterior_config_frame,
                        "ポート",
                        0,
                        2,
                        6,
                        str(
                            7860
                            if type == BackEnd.a1111
                            else 8188
                            if type == BackEnd.comfy_ui
                            else 0
                        ),
                        "w",
                    )

            def __init__(self, owner: Displayer.ConfigWindow):
                """
                メインタブコンストラクタ

                Args:
                    owner (Displayer.ConfigWindow): ConfigWindow インスタンス
                """
                self.super_owner = owner

                self.main_frame = ttk.Frame(owner.main_tab)
                self.main_frame.grid(row=0, column=0, sticky="nsew")

                self.button_frame = self.ButtonFrame(self)
                self.sd_interior_config_frame = self.SDInteriorConfigFrame(self)
                self.sd_exterior_config_frame = self.SDExteriorConfigFrame(self)

        class DebugTab:
            """
            デバッグタブ
            """

            class ExeDebugFrame:
                """
                デバッグ実行フレーム
                """

                def __init__(self, owner: Displayer.ConfigWindow.DebugTab):
                    """
                    デバッグ実行フレームコンストラクタ

                    Args:
                        owner (Displayer.ConfigWindow.DebugTab): DebugTab インスタンス
                    """
                    self.super_owner = owner

                    self.exe_debug_frame = ttk.Frame(owner.main_frame)
                    self.exe_debug_frame.grid(row=0, column=0, sticky="w")
                    # ボタン(デバッグ)
                    self.debug_button = ttk.Button(
                        self.exe_debug_frame,
                        text="デバッグ",
                        command=owner.super_owner.super_owner.master.on_debug,
                    )
                    self.debug_button.grid(row=0, column=0, padx=6, pady=6, sticky="w")
                    # チェックボックス
                    self.allow_edit_clipboard_check = tkinter.BooleanVar()
                    ttk.Checkbutton(
                        self.exe_debug_frame,
                        text="クリップボードの更新",
                        variable=self.allow_edit_clipboard_check,
                    ).grid(row=0, column=1, padx=6, pady=6, sticky="w")
                    # ボタン(アーカイブ出力 ダンプ)
                    self.debug_button = ttk.Button(
                        self.exe_debug_frame,
                        text="アーカイブ出力",
                        command=owner.super_owner.super_owner.on_dump_archiver,
                    )
                    self.debug_button.grid(row=1, column=0, padx=6, pady=6, sticky="w")
                    # ボタン(タスクリストダンプ)
                    self.debug_button = ttk.Button(
                        self.exe_debug_frame,
                        text="タスクリスト",
                        command=owner.super_owner.super_owner.on_dump_tasks,
                    )
                    self.debug_button.grid(row=1, column=1, padx=6, pady=6, sticky="w")

            class VerboseFrame:
                """
                表示設定フレーム
                """

                def __init__(self, owner: Displayer.ConfigWindow.DebugTab):
                    """
                    表示設定フレームコンストラクタ

                    Args:
                        owner (Displayer.ConfigWindow.DebugTab): DebugTab インスタンス
                    """
                    self.super_owner = owner

                    self.verbose_frame = ttk.Frame(owner.main_frame)
                    self.verbose_frame.grid(row=1, column=0, sticky="w")
                    # クリップボードの表示
                    self.verbose_clipboard_check = tkinter.BooleanVar()
                    ttk.Checkbutton(
                        self.verbose_frame,
                        text="クリップボード",
                        variable=self.verbose_clipboard_check,
                    ).grid(row=0, column=0, padx=6, pady=6, sticky="w")
                    # ステータスの表示
                    self.verbose_stats_check = tkinter.BooleanVar()
                    ttk.Checkbutton(
                        self.verbose_frame,
                        text="ステータス",
                        variable=self.verbose_stats_check,
                    ).grid(row=0, column=1, padx=6, pady=6, sticky="w")
                    # PicInfoの表示
                    self.verbose_picinfo_check = tkinter.BooleanVar()
                    ttk.Checkbutton(
                        self.verbose_frame,
                        text="PicInfo",
                        variable=self.verbose_picinfo_check,
                    ).grid(row=1, column=0, padx=6, pady=6, sticky="w")

            def __init__(self, owner: Displayer.ConfigWindow):
                """
                デバッグタブコンストラクタ

                Args:
                    owner (Displayer.ConfigWindow): ConfigWindow インスタンス
                """
                self.super_owner = owner

                self.main_frame = ttk.Frame(owner.debug_tab)
                self.main_frame.grid(row=0, column=0, sticky="nsew")

                self.exe_debug_frame = self.ExeDebugFrame(self)
                self.verbose_frame = self.VerboseFrame(self)

        def __init__(self, owner: Displayer):
            """
            設定ウィンドウコンストラクタ

            Args:
                owner (Displayer): Display インスタンス
            """
            self.super_owner = owner

            # 設定ウィンドウ
            owner.master.root.title("picmaker - 設定")
            owner.master.root.columnconfigure(0, weight=1)
            owner.master.root.rowconfigure(0, weight=1)
            owner.master.root.protocol("WM_DELETE_WINDOW", owner.destroy_config_window)
            # Notebook（タブ）
            self.notebook = ttk.Notebook(owner.master.root)
            self.notebook.grid(row=0, column=0, sticky="nsew")
            # メインタブ
            self.main_tab = ttk.Frame(self.notebook, padding=12)
            self.notebook.add(self.main_tab, text="メイン")
            self.main_tab_obj = self.MainTab(self)
            # デバッグタブ
            self.debug_tab = ttk.Frame(self.notebook, padding=12)
            self.notebook.add(self.debug_tab, text="デバッグ")
            self.debug_tab_obj = self.DebugTab(self)

    class InfoWindow:
        """
        情報ウィンドウ
        """

        class CommonFrame:
            """
            タブ共通フレーム
            """

            def __init__(self, owner: Displayer.InfoWindow, parent_frame: ttk.Frame):
                """
                タブ共通フレームコンストラクタ
                Args:
                    owner (Displayer.InfoWindow): InfoWindow インスタンス
                """
                self.super_owner = owner
                self.common_frame = ttk.Frame(parent_frame)
                self.common_frame.grid(row=0, column=0, padx=6, pady=6, sticky="ew")
                self.common_frame.columnconfigure(0, weight=1)
                # 残りタスク数
                ttk.Label(self.common_frame, text="残りタスク数").grid(row=0, column=0, sticky="w")
                ttk.Label(self.common_frame, textvariable=owner.len_tasks_strvar).grid(
                    row=0, column=1, sticky="w"
                )
                # プログレスバー
                self.task_progress = ttk.Progressbar(
                    self.common_frame,
                    orient="horizontal",
                    length=300,
                    mode="determinate",
                    variable=owner.progress_val,
                    maximum=1,
                )
                self.task_progress.grid(row=0, column=2, padx=6, pady=6, sticky="w")
                ttk.Label(self.common_frame, textvariable=owner.progress_strvar, width=4).grid(
                    row=0, column=3, padx=6, pady=6, sticky="w"
                )

        class TaskInfoTab:
            """
            タスク情報タブ
            """

            class InfoBoxFrame:
                """
                情報ボックスフレーム
                """

                def __init__(self, owner: Displayer.InfoWindow.TaskInfoTab):
                    """
                    情報ボックスフレームコンストラクタ

                    Args:
                        owner (Displayer.InfoWindow): InfoWindow インスタンス
                    """
                    self.super_owner = owner

                    self.infobox_frame = ttk.Frame(owner.main_frame)
                    self.infobox_frame.grid(row=1, column=0, sticky="nsew")
                    self.infobox_frame.rowconfigure(0, weight=1)
                    self.infobox_frame.columnconfigure(0, weight=1)

                    data = [
                        ("キー", "値"),
                        ("ポジティブプロンプト", Consts.not_available_text),
                        ("ネガティブプロンプト", Consts.not_available_text),
                        ("ステップ数", Consts.not_available_text),
                        ("バッチサイズ", Consts.not_available_text),
                        ("サンプラ", Consts.not_available_text),
                        ("スケジューラ", Consts.not_available_text),
                        ("スケール", Consts.not_available_text),
                        ("シード値", Consts.not_available_text),
                        ("幅", Consts.not_available_text),
                        ("高さ", Consts.not_available_text),
                        ("宛先アドレス", Consts.not_available_text),
                        ("宛先ポート", Consts.not_available_text),
                    ]
                    self.infobox_tree = InfoTree(self.infobox_frame, data)

            def __init__(self, owner: Displayer.InfoWindow):
                """
                タスク情報タブコンストラクタ

                Args:
                    owner (Displayer.InfoWindow): InfoWindow インスタンス
                """
                self.super_owner = owner

                self.main_frame = ttk.Frame(owner.taskinfo_tab)
                self.main_frame.grid(row=0, column=0, sticky="nsew")
                self.main_frame.rowconfigure(0, weight=0)
                self.main_frame.rowconfigure(1, weight=1)
                self.main_frame.columnconfigure(0, weight=1)

                self.common_frame = owner.CommonFrame(owner, self.main_frame)
                self.infobox_frame = self.InfoBoxFrame(self)

        class PicInfoTab:
            """
            画像情報タブ
            """

            class InfoBoxFrame:
                """
                情報ボックスフレーム
                """

                def __init__(self, owner: Displayer.InfoWindow.PicInfoTab):
                    """
                    情報ボックスフレームコンストラクタ

                    Args:
                        owner (Displayer.InfoWindow): InfoWindow インスタンス
                    """
                    self.super_owner = owner

                    self.infobox_frame = ttk.Frame(owner.main_frame)
                    self.infobox_frame.grid(row=1, column=0, sticky="nsew")
                    data = [
                        ("キー", "値"),
                        ("場所", Consts.not_available_text),
                        ("ポジティブプロンプト", Consts.not_available_text),
                        ("ネガティブプロンプト", Consts.not_available_text),
                        ("ステップ数", Consts.not_available_text),
                        ("サンプラ", Consts.not_available_text),
                        ("スケジューラ", Consts.not_available_text),
                        ("スケール", Consts.not_available_text),
                        ("シード値", Consts.not_available_text),
                        ("幅", Consts.not_available_text),
                        ("高さ", Consts.not_available_text),
                    ]
                    self.infobox_tree = InfoTree(self.infobox_frame, data)

            def __init__(self, owner: Displayer.InfoWindow):
                """
                画像情報タブコンストラクタ

                Args:
                    owner (Displayer.InfoWindow): InfoWindow インスタンス
                """
                self.super_owner = owner

                self.main_frame = ttk.Frame(owner.picinfo_tab)
                self.main_frame.grid(row=0, column=0, sticky="nsew")
                self.main_frame.rowconfigure(0, weight=0)
                self.main_frame.rowconfigure(1, weight=1)
                self.main_frame.columnconfigure(0, weight=1)

                self.common_frame = owner.CommonFrame(owner, self.main_frame)
                self.infobox_frame = self.InfoBoxFrame(self)

        def __init__(self, owner: Displayer, fix_position: bool = False):
            """
            情報ウィンドウコンストラクタ

            Args:
                owner (Displayer): Display インスタンス
                fix_position (bool, optional): 表示位置を固定するか
            """
            self.super_owner = owner

            self.info_window = tkinter.Toplevel(self.super_owner.master.root)
            if fix_position:
                self.info_window.geometry(
                    (
                        f"+{owner.config_window_x}"
                        f"+{owner.config_window_y + owner.config_window_height + 50}"
                    )
                )
            self.info_window.title(
                f"picmaker - 情報 [{owner.master.frontend_name} - {owner.master.backend_name}]"
            )
            self.info_window.protocol("WM_DELETE_WINDOW", self.super_owner.destroy_info_window)
            self.info_window.geometry("500x380")
            self.info_window.rowconfigure(0, weight=1)
            self.info_window.columnconfigure(0, weight=1)

            # タブを跨いで表示する情報
            self.len_tasks_strvar = tkinter.StringVar(value="0")
            self.progress_val = tkinter.DoubleVar(value=0)
            self.progress_strvar = tkinter.StringVar(value="0%")

            # Notebook（タブ）
            self.notebook = ttk.Notebook(self.info_window)
            self.notebook.grid(row=0, column=0, sticky="nsew")
            # タスク情報タブ
            self.taskinfo_tab = ttk.Frame(self.notebook, padding=12)
            self.taskinfo_tab.rowconfigure(0, weight=1)
            self.taskinfo_tab.columnconfigure(0, weight=1)
            self.notebook.add(self.taskinfo_tab, text="タスク")
            self.taskinfo_tab_obj = self.TaskInfoTab(self)
            # 画像情報タブ
            self.picinfo_tab = ttk.Frame(self.notebook, padding=12)
            self.picinfo_tab.rowconfigure(0, weight=1)
            self.picinfo_tab.columnconfigure(0, weight=1)
            self.notebook.add(self.picinfo_tab, text="画像")
            self.picinfo_tab_obj = self.PicInfoTab(self)

    class PicWindow:
        """
        画像ウィンドウ
        """

        @dataclass
        class Event:
            """
            イベントフラグ
            """

            outputting_noimage = threading.Event()  # NO IMAGE 表示中

        class CursorFrame:
            """
            画像表示フレーム
            """

            def __init__(self, owner: Displayer.PicWindow):
                """
                画像表示フレームコンストラクタ

                Args:
                    owner (Displayer.PicWindow): PicWindow インスタンス
                """
                self.super_owner = owner

                self.cursor_frame = ttk.Frame(owner.main_frame)
                self.cursor_frame.grid(row=0, column=0, sticky="nwe")

                # ラベル
                self.pic_label = ttk.Label(self.cursor_frame)
                self.pic_label.grid(row=0, column=1, padx=6, pady=6, sticky="nswe")
                self.pic_label_image = None
                # ボタン(<)
                self.prev_button = ttk.Button(
                    self.cursor_frame, text="<", width=2, command=owner.super_owner.master.on_prev
                )
                self.prev_button.grid(row=0, column=0, padx=6, pady=6, sticky="nsw")
                # ボタン(>)
                self.next_button = ttk.Button(
                    self.cursor_frame, text=">", width=2, command=owner.super_owner.master.on_next
                )
                self.next_button.grid(row=0, column=2, padx=6, pady=6, sticky="nse")

        class EvalFrame:
            """
            評価フレーム
            """

            def __init__(self, owner: Displayer.PicWindow):
                """
                評価フレームコンストラクタ

                Args:
                    owner (Displayer.PicWindow): PicWindow インスタンス
                """
                self.super_owner = owner

                self.eval_frame = ttk.Frame(owner.main_frame)
                self.eval_frame.grid(row=1, column=0, sticky="swe")
                self.eval_frame.columnconfigure(0, weight=1)
                self.eval_frame.columnconfigure(1, weight=1)

                # ボタン(アップスケール予約)
                self.upscale_button = ttk.Button(
                    self.eval_frame,
                    text="アップスケール予約",
                    command=self.super_owner.super_owner.master.on_upscale,
                )
                self.upscale_button.grid(row=0, column=0, padx=6, pady=6, sticky="wes")
                # ボタン(削除)
                self.remove_button = ttk.Button(
                    self.eval_frame,
                    text="削除",
                    command=self.super_owner.super_owner.master.on_remove,
                )
                self.remove_button.grid(row=0, column=1, padx=6, pady=6, sticky="wes")

        def __init__(self, owner: Displayer):
            """
            画像ウィンドウコンストラクタ

            Args:
                owner (Displayer): Display インスタンス
                fix_position (bool, optional): 表示位置を固定するか
            """
            self.super_owner = owner

            self.pic_window = None
            self.cursor_frame = None
            self.eval_frame = None
            self.event = Displayer.PicWindow.Event()
            self.noimage_img: ImageTk.PhotoImage = None

        def construct(self, fix_position=False) -> None:
            """
            画像ウィンドウを構築する\n
            すでに開いている場合は何もしない
            """
            if self.existed() and self.pic_window:
                return

            self.pic_window = tkinter.Toplevel(self.super_owner.master.root)
            if fix_position:
                self.pic_window.geometry(
                    (
                        f"-{
                            self.super_owner.config_window_x
                            + self.super_owner.config_window_width
                            + 50
                        }"
                        f"+{self.super_owner.config_window_y}"
                    )
                )
            self.pic_window.title("picmaker - 画像")
            self.pic_window.protocol("WM_DELETE_WINDOW", self.destroy)

            self.main_frame = ttk.Frame(self.pic_window, padding=5)
            self.main_frame.grid(row=0, column=0, sticky="nsew")

            self.cursor_frame = self.CursorFrame(self)
            self.eval_frame = self.EvalFrame(self)

        def destroy(self) -> None:
            """
            画像ウィンドウのクローズ時のハンドラ
            """
            if self.existed():
                self.pic_window.destroy()
            self.pic_window = None

        def existed(self) -> bool:
            """
            画像ウィンドウが開かれているか

            Returns:
                bool: True: 開かれている, False: 開かれていない or TclError 例外発生
            """
            if self.pic_window is None:
                return False
            try:
                return bool(self.pic_window.winfo_exists())
            except TclError:
                return False

        def update(self, picstats: PicStats = None) -> None:
            """
            画像ウィンドウを指定の PicStats で更新する\n
            picstats が None の場合は NO IMAGE で更新する

            Args:
                picstats (PicStats): 更新予定の PicStats
            """
            if not self.existed():
                return

            if picstats is not None:
                image = Image.open(picstats.path)
                tk_img = ImageTk.PhotoImage(image)
                self.cursor_frame.pic_label.configure(image=tk_img)
                self.cursor_frame.pic_label_image = tk_img
                self.event.outputting_noimage.clear()
                self.switch_button_state(True)
            else:
                self.set_no_image()
                self.cursor_frame.pic_label.configure(image=self.noimage_img)
                self.cursor_frame.pic_label_image = self.noimage_img
                self.event.outputting_noimage.set()
                self.switch_button_state(False)

        def set_no_image(self) -> None:
            """
            表示すべき画像がない場合の画像を作成し, インスタンス変数にセットする\n
            すでに同サイズの作成済みのイメージが存在する場合は新たに生成しない\n
            グレースケールのチェックパターンに"NO IMAGE"\n
            幅と高さは自動的に 8 の倍数に切り下げられる(Stable Diffusion の仕様に準拠)
            """
            width = self.super_owner.sd_width & -8
            height = self.super_owner.sd_height & -8
            if self.noimage_img is not None and (
                self.noimage_img.width() == width or self.noimage_img.height() == height
            ):
                return

            light = "#e0e0e0"
            dark = "#c0c0c0"
            text_color = "#444444"
            img = Image.new("RGB", (width, height), light)
            draw = ImageDraw.Draw(img)

            cell = max(8, min(width, height) // 20)
            for y in range(0, height, cell):
                for x in range(0, width, cell):
                    if (x // cell + y // cell) % 2 == 0:
                        draw.rectangle((x, y, x + cell, y + cell), fill=light)
                    else:
                        draw.rectangle((x, y, x + cell, y + cell), fill=dark)

            text = "NO IMAGE"
            fallback_font = ImageFont.load_default()
            font = fallback_font
            max_font_size = int(height * 0.15)
            font_size = max_font_size
            while font_size > 5:
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except Exception:
                    font = fallback_font
                bbox = draw.textbbox((0, 0), text, font=font)
                text_w = bbox[2] - bbox[0]
                if text_w <= width * 0.8:
                    break
                font_size -= 2

            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            text_x = (width - text_w) // 2
            text_y = (height - text_h) // 2
            draw.text((text_x, text_y), text, fill=text_color, font=font)

            self.noimage_img = ImageTk.PhotoImage(img)

        def switch_button_state(self, toggle: bool) -> None:
            """
            画像ウィンドウ上のボタンの有効/無効(グレーアウト)を切り替える

            Args:
                toggle (bool): True で有効, False で無効
            """
            if not self.existed():
                return

            if toggle:
                self.cursor_frame.next_button.configure(state="normal")
                self.cursor_frame.prev_button.configure(state="normal")
                self.eval_frame.upscale_button.configure(state="normal")
                self.eval_frame.remove_button.configure(state="normal")
            else:
                self.cursor_frame.next_button.configure(state="disabled")
                self.cursor_frame.prev_button.configure(state="disabled")
                self.eval_frame.upscale_button.configure(state="disabled")
                self.eval_frame.remove_button.configure(state="disabled")

    def __init__(self, master: MasterIF):
        """
        コンストラクタ

        Args:
            master (MasterIF): Master インターフェース
        """
        self.master = master

        self.config_window = self.ConfigWindow(self)
        self.info_window: Displayer.InfoWindow = None
        self.construct_info_window()
        self.pic_window = self.PicWindow(self)
        self.switch_output_button_state(False)

    def put_textbox(
        self, frame: Frame, name: str, row: int, col: int, width: int, default: str, sticky: str
    ) -> ttk.Entry:
        """
        テキストボックスの作成([name] [entry])\n
        本オブジェクトは column 2つ分を占めることに注意

        Args:
            frame (Frame): 挿入先フレーム
            name (str): ラベル
            row (int): フレーム内の row
            col (int): フレーム内の column
            width (int): 長さ
            default (str): デフォルト値
            sticky (str): 張り付き方

        Returns:
            ttk.Entry: オブジェクトインスタンス
        """
        ttk.Label(frame, text=name).grid(row=row, column=col, padx=6, pady=6, sticky=sticky)
        entry = ttk.Entry(frame, width=width)
        entry.grid(row=row, column=(col + 1), padx=2, pady=6, sticky=sticky)
        entry.insert(0, default)
        return entry

    def put_textlabel(
        self, frame: Frame, name: str, row: int, col: int, default: str, sticky: str
    ) -> tkinter.StringVar:
        """
        テキストラベルの作成([name] [label])\n
        本オブジェクトは column 2つ分を占めることに注意\n
        返り値は更新可能な文字列ベースのオブジェクト

        Args:
            frame (Frame): 挿入先フレーム
            name (str): ラベル
            row (int): フレーム内の row
            col (int): フレーム内の column
            default (str): デフォルト値
            sticky (str): 張り付き方

        Returns:
            tkinter.StringVar: オブジェクトインスタンス
        """
        ttk.Label(frame, text=name).grid(row=row, column=col, sticky=sticky)
        strvar = tkinter.StringVar(value=default)
        ttk.Label(frame, textvariable=strvar).grid(row=row, column=(col + 1), sticky=sticky)
        return strvar

    def is_config_window_open(self) -> bool:
        """
        設定ウィンドウが開かれているか

        Returns:
            bool: True: 開かれている, False: 開かれていない or TclError 例外発生
        """
        if self.master.root is None:
            return False
        try:
            return bool(self.master.root.winfo_exists())
        except TclError:
            return False

    def destroy_config_window(self) -> None:
        """
        設定ウィンドウのクローズ時のハンドラ
        """
        self.pic_window.destroy()
        self.destroy_info_window()
        if self.is_config_window_open():
            self.master.root.destroy()

    def construct_info_window(self) -> None:
        """
        情報ウィンドウを構築する\n
        すでに開いている場合は最前面に表示のみ行う
        """
        if self.is_info_window_open() and self.info_window:
            self.info_window.info_window.deiconify()
            self.info_window.info_window.lift()
            return

        self.info_window = self.InfoWindow(self, fix_position=True)

    def is_info_window_open(self) -> bool:
        """
        情報ウィンドウが開かれているか

        Returns:
            bool: True: 開かれている, False: 開かれていない or TclError 例外発生
        """
        if self.info_window is None or self.info_window.info_window is None:
            return False
        try:
            return bool(self.info_window.info_window.winfo_exists())
        except TclError:
            return False

    def destroy_info_window(self) -> None:
        """
        情報ウィンドウのクローズ時のハンドラ
        """
        if self.is_info_window_open():
            self.info_window.info_window.destroy()
        self.info_window.info_window = None

    def update_appinfo_frame(self) -> None:
        """
        アプリケーション情報フレームの更新を行う\n
        更新は呼び出した瞬間の TaskManager をもとに行う
        """
        self.info_window.len_tasks_strvar.set(f"{self.master.crnt_tasks}")
        crnt_task: TaskBlueprint = self.master.crnt_task
        if crnt_task is None:
            self.info_window.progress_val.set(0)
            self.info_window.progress_strvar.set("0%")
        else:
            self.info_window.progress_val.set(self.master.crnt_progress)
            task_progress_val = self.master.crnt_progress * 100
            self.info_window.progress_strvar.set(f"{task_progress_val:.0f}%")
            return

    def update_taskinfo_frame(self) -> None:
        """
        プロンプト, タスクメタ情報フレームの更新を行う\n
        更新は呼び出した瞬間の TaskManager をもとに行う
        """
        crnt_task: TaskBlueprint = self.master.crnt_task
        if crnt_task is None:
            self.info_window.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "ポジティブプロンプト", Consts.not_available_text
            )
            self.info_window.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "ネガティブプロンプト", Consts.not_available_text
            )
            self.info_window.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "ステップ数", Consts.not_available_text
            )
            self.info_window.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "バッチサイズ", Consts.not_available_text
            )
            self.info_window.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "サンプラ", Consts.not_available_text
            )
            self.info_window.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "スケジューラ", Consts.not_available_text
            )
            self.info_window.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "スケール", Consts.not_available_text
            )
            self.info_window.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "シード値", Consts.not_available_text
            )
            self.info_window.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "幅", Consts.not_available_text
            )
            self.info_window.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "高さ", Consts.not_available_text
            )
            self.info_window.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "宛先アドレス", Consts.not_available_text
            )
            self.info_window.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "宛先ポート", Consts.not_available_text
            )
        else:
            self.info_window.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "ポジティブプロンプト", crnt_task.prompt
            )
            self.info_window.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "ネガティブプロンプト", crnt_task.negative_prompt
            )
            self.info_window.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "ステップ数", crnt_task.steps
            )
            self.info_window.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "バッチサイズ", crnt_task.batch_size
            )
            self.info_window.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "サンプラ", crnt_task.sampler_name
            )
            self.info_window.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "スケジューラ", crnt_task.scheduler
            )
            self.info_window.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "スケール", crnt_task.cfg_scale
            )
            self.info_window.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "シード値", crnt_task.seed
            )
            self.info_window.taskinfo_tab_obj.infobox_frame.infobox_tree.set("幅", crnt_task.width)
            self.info_window.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "高さ", crnt_task.height
            )
            self.info_window.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "宛先アドレス", crnt_task.dst_addr
            )
            self.info_window.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "宛先ポート", crnt_task.dst_port
            )

    def update_picinfo_tab(self, reset: bool = False) -> None:
        crnt_picstats: PicStats = self.master.crnt_picstats
        if not crnt_picstats or reset:
            self.info_window.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "場所", Consts.not_available_text
            )
            self.info_window.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "ポジティブプロンプト", Consts.not_available_text
            )
            self.info_window.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "ネガティブプロンプト", Consts.not_available_text
            )
            self.info_window.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "ステップ数", Consts.not_available_text
            )
            self.info_window.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "サンプラ", Consts.not_available_text
            )
            self.info_window.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "スケジューラ", Consts.not_available_text
            )
            self.info_window.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "スケール", Consts.not_available_text
            )
            self.info_window.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "シード値", Consts.not_available_text
            )
            self.info_window.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "幅", Consts.not_available_text
            )
            self.info_window.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "高さ", Consts.not_available_text
            )
        else:
            self.info_window.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "場所", crnt_picstats.path
            )
            self.info_window.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "ポジティブプロンプト", crnt_picstats.info.positive_prompt
            )
            self.info_window.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "ネガティブプロンプト", crnt_picstats.info.negative_prompt
            )
            self.info_window.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "ステップ数", crnt_picstats.info.steps
            )
            self.info_window.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "サンプラ", crnt_picstats.info.sampler
            )
            self.info_window.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "スケジューラ", crnt_picstats.info.scheduler
            )
            self.info_window.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "スケール", crnt_picstats.info.cfg_scale
            )
            self.info_window.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "シード値", crnt_picstats.info.seed
            )
            self.info_window.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "幅", crnt_picstats.info.width
            )
            self.info_window.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "高さ", crnt_picstats.info.height
            )

    def update_info_window(self) -> None:
        """
        情報ウィンドウの更新を行う\n
        ウィンドウが開いていない場合は何もしない\n
        更新は呼び出した瞬間の TaskManager をもとに行う
        """
        if not self.info_window:
            return

        self.update_appinfo_frame()
        self.update_taskinfo_frame()

    def update_pic_window(self, picstats: PicStats = None) -> None:
        """
        画像ウィンドウを指定の PicStats で更新する\n
        picstats が None の場合は NO IMAGE で更新する\n
        設定ウィンドウと情報ウィンドウの更新も行う

        Args:
            picstats (PicStats): 更新予定の PicStats
        """
        self.pic_window.update(picstats)
        if picstats is not None:
            self.switch_output_button_state(True)
            self.update_picinfo_tab()
        else:
            self.switch_output_button_state(False)
            self.update_picinfo_tab(reset=True)

    def switch_output_button_state(self, toggle: bool) -> None:
        """
        表示ボタンの有効/無効(グレーアウト)を切り替える

        Args:
            toggle (bool): True で有効, False で無効
        """
        if not self.is_config_window_open():
            return

        if toggle:
            self.config_window.main_tab_obj.button_frame.output_button.configure(state="normal")
        else:
            self.config_window.main_tab_obj.button_frame.output_button.configure(state="disabled")

    def on_open_pic_window(self) -> None:
        """
        表示ボタンハンドラ\n
        表示すべき画像がないときは何もしない
        """
        self.update_pic_window(self.master.crnt_picstats)

    def on_open_info_window(self) -> None:
        """
        情報ウィンドウの表示ハンドラ\n
        すでに開いている場合は最前面に表示のみ行う\n
        情報の更新も直後に行う
        """
        if self.is_info_window_open() and self.info_window:
            self.info_window.info_window.deiconify()
            self.info_window.info_window.lift()
        else:
            self.construct_info_window()

        self.update_info_window()

    def on_dump_archiver(self) -> None:
        """
        Archiver ダンプボタンハンドラ
        """
        dump_json(self.master.crnt_archiver, "archiver")

    def on_dump_tasks(self) -> None:
        """
        タスクリストダンプボタンハンドラ
        """
        dump_json(list(self.master.crnt_tasklist), "tasks")

    @property
    def config_window_x(self) -> int:
        """
        設定ウィンドウ(メインウィンドウ)の x 座標

        Returns:
            int: 設定ウィンドウ(メインウィンドウ)の x 座標
        """
        self.master.root.update_idletasks()
        return self.master.root.winfo_x()

    @property
    def config_window_y(self) -> int:
        """
        設定ウィンドウ(メインウィンドウ)の y 座標

        Returns:
            int: 設定ウィンドウ(メインウィンドウ)の y 座標
        """
        self.master.root.update_idletasks()
        return self.master.root.winfo_y()

    @property
    def config_window_width(self) -> int:
        """
        設定ウィンドウ(メインウィンドウ)の幅

        Returns:
            int: 設定ウィンドウ(メインウィンドウ)の幅
        """
        self.master.root.update_idletasks()
        return self.master.root.winfo_width()

    @property
    def config_window_height(self) -> int:
        """
        設定ウィンドウ(メインウィンドウ)の高さ

        Returns:
            int: 設定ウィンドウ(メインウィンドウ)の高さ
        """
        self.master.root.update_idletasks()
        return self.master.root.winfo_height()

    @property
    def srv_ipaddr(self) -> str:
        """
        ポスト先 IP アドレス

        Returns:
            str: ポスト先 IP アドレス
        """
        return self.config_window.main_tab_obj.sd_exterior_config_frame.ipaddr_entry.get()

    @property
    def srv_port(self) -> str:
        """
        ポスト先ポート

        Returns:
            str: ポスト先ポート
        """
        return self.config_window.main_tab_obj.sd_exterior_config_frame.port_entry.get()

    @property
    def sd_steps(self) -> int:
        """
        ステップ数

        Returns:
            int: ステップ数
        """
        return int(self.config_window.main_tab_obj.sd_interior_config_frame.steps_entry.get())

    @property
    def sd_batch_size(self) -> int:
        """
        バッチサイズ

        Returns:
            int: バッチサイズ
        """
        return int(self.config_window.main_tab_obj.sd_interior_config_frame.batch_size_entry.get())

    @property
    def sd_width(self) -> int:
        """
        幅

        Returns:
            int: 幅
        """
        return int(self.config_window.main_tab_obj.sd_interior_config_frame.width_entry.get())

    @property
    def sd_height(self) -> int:
        """
        高さ

        Returns:
            int: 高さ
        """
        return int(self.config_window.main_tab_obj.sd_interior_config_frame.height_entry.get())

    @property
    def allow_edit_clipboard(self) -> bool:
        """
        デバッグ時にクリップボード更新を認めるか

        Returns:
            bool: True: 認める, False: 認めない
        """
        return self.config_window.debug_tab_obj.exe_debug_frame.allow_edit_clipboard_check.get()

    @property
    def print_new_clipboard(self) -> bool:
        """
        クリップボードの更新があった場合にログ出力するか

        Returns:
            bool: True: 表示する, False: 表示しない
        """
        return self.config_window.debug_tab_obj.verbose_frame.verbose_clipboard_check.get()

    @property
    def print_new_stats(self) -> bool:
        """
        ステータスの更新があった場合にログ出力するか

        Returns:
            bool: True: 表示する, False: 表示しない
        """
        return self.config_window.debug_tab_obj.verbose_frame.verbose_stats_check.get()

    @property
    def print_picinfo(self) -> bool:
        """
        応答 image の PicInfo をログ出力するか

        Returns:
            bool: True: 表示する, False: 表示しない
        """
        return self.config_window.debug_tab_obj.verbose_frame.verbose_picinfo_check.get()
