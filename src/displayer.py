"""
GUI 管理クラス
"""

from __future__ import annotations

import tkinter
from dataclasses import dataclass
from tkinter import Frame, TclError, ttk
from typing import Callable

from PIL import Image, ImageDraw, ImageFont, ImageTk

from functions import dump_json
from picmanager import PicManager, PicStats
from taskmanager import TaskBlueprint, TaskManager


@dataclass(frozen=True)
class Consts:
    """
    このクラス関連の定数
    """

    # 表示する文字列の最大長
    max_output_strlen: int = 75
    # N/A テキスト
    not_available_text: str = "N/A"


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
                        command=owner.super_owner.super_owner.on_append,
                    )
                    self.gen_button.grid(row=0, column=0, padx=6, pady=6, sticky="w")
                    # ボタン(中断)
                    self.interrupt_button = ttk.Button(
                        self.button_frame,
                        text="中断",
                        command=owner.super_owner.super_owner.taskmanager.post_interrupt,
                    )
                    self.interrupt_button.grid(row=0, column=1, padx=6, pady=6, sticky="w")
                    # タスククリア
                    self.clear_button = ttk.Button(
                        self.button_frame,
                        text="タスククリア",
                        command=owner.super_owner.super_owner.taskmanager.clear,
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
                        self.sd_interior_config_frame, "幅", 1, 0, 5, str(256), "w"
                    )
                    # テキストボックス(高さ)
                    self.height_entry = owner.super_owner.super_owner.put_textbox(
                        self.sd_interior_config_frame, "高さ", 1, 2, 5, str(256), "w"
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
                    self.port_entry = owner.super_owner.super_owner.put_textbox(
                        self.sd_exterior_config_frame, "ポート", 0, 2, 6, str(7860), "w"
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
                        command=owner.super_owner.super_owner.on_debug,
                    )
                    self.debug_button.grid(row=0, column=0, padx=6, pady=6, sticky="w")
                    # チェックボックス
                    self.allow_edit_clipboard_check = tkinter.BooleanVar()
                    ttk.Checkbutton(
                        self.exe_debug_frame,
                        text="クリップボードの更新",
                        variable=self.allow_edit_clipboard_check,
                    ).grid(row=0, column=1, padx=6, pady=6, sticky="w")
                    # ボタン(PicManager ダンプ)
                    self.debug_button = ttk.Button(
                        self.exe_debug_frame,
                        text="PicManager",
                        command=owner.super_owner.super_owner.on_dump_picmanager,
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
                    # 応答(image)の表示
                    self.verbose_image_check = tkinter.BooleanVar()
                    ttk.Checkbutton(
                        self.verbose_frame,
                        text="応答(image)",
                        variable=self.verbose_image_check,
                    ).grid(row=1, column=0, padx=6, pady=6, sticky="w")
                    # PicInfoの表示
                    self.verbose_picinfo_check = tkinter.BooleanVar()
                    ttk.Checkbutton(
                        self.verbose_frame,
                        text="PicInfo",
                        variable=self.verbose_picinfo_check,
                    ).grid(row=1, column=1, padx=6, pady=6, sticky="w")

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
            owner.root.title("picmaker - 設定")
            owner.root.columnconfigure(0, weight=1)
            owner.root.rowconfigure(0, weight=1)
            owner.root.protocol("WM_DELETE_WINDOW", owner.destroy_config_window)
            # Notebook（タブ）
            self.notebook = ttk.Notebook(owner.root)
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

        class TaskInfoTab:
            """
            タスク情報タブ
            """

            class AppInfoFrame:
                """
                アプリケーション情報フレーム
                """

                def __init__(self, owner: Displayer.InfoWindow.TaskInfoTab):
                    """
                    アプリケーション情報フレームコンストラクタ

                    Args:
                        owner (Displayer.InfoWindow): InfoWindow インスタンス
                    """
                    self.super_owner = owner

                    self.appinfo_frame = ttk.Frame(owner.main_frame)
                    self.appinfo_frame.grid(row=0, column=0, sticky="new")

                    # 残りタスク数
                    self.len_tasks_frame = ttk.Frame(self.appinfo_frame)
                    self.len_tasks_frame.grid(row=0, column=0, sticky="w")
                    self.len_tasks_strvar = owner.super_owner.super_owner.put_textlabel(
                        self.len_tasks_frame, "残りタスク数", 0, 0, "0", "w"
                    )
                    # プログレスバー
                    self.progress_frame = ttk.Frame(self.appinfo_frame)
                    self.progress_frame.grid(row=1, column=0, sticky="ew")
                    self.task_progress = ttk.Progressbar(
                        self.progress_frame, orient="horizontal", length=300, mode="determinate"
                    )
                    self.task_progress.grid(row=0, column=0, padx=6, pady=6, sticky="w")
                    self.task_progress["maximum"] = 1
                    self.task_progress["value"] = 0
                    self.progress_strvar = tkinter.StringVar(value="0%")
                    ttk.Label(self.progress_frame, textvariable=self.progress_strvar).grid(
                        row=0, column=1, padx=6, pady=6, sticky="w"
                    )

            class CrntTaskPromptsFrame:
                """
                現在のタスク情報(プロンプト)フレーム
                """

                def __init__(self, owner: Displayer.InfoWindow.TaskInfoTab):
                    """
                    現在のタスク情報(プロンプト)フレームコンストラクタ

                    Args:
                        owner (Displayer.InfoWindow): InfoWindow インスタンス
                    """
                    self.super_owner = owner

                    self.crnt_task_prompts_frame = ttk.Frame(owner.main_frame)
                    self.crnt_task_prompts_frame.grid(row=1, column=0, sticky="w")
                    self.crnt_task_prompts_frame.columnconfigure(0, weight=1)
                    self.crnt_task_prompts_frame.columnconfigure(1, weight=1)

                    ttk.Label(self.crnt_task_prompts_frame, text="- 現在のタスク -").grid(
                        row=0, column=0, padx=6, pady=6, sticky="w"
                    )
                    # ポジティブプロンプト
                    ttk.Label(self.crnt_task_prompts_frame, text="ポジティブプロンプト").grid(
                        row=1, column=0, padx=6, pady=6, sticky="w"
                    )
                    self.pos_prompt_tiplabel = TipLabel(
                        self.crnt_task_prompts_frame,
                        1,
                        1,
                        Consts.not_available_text,
                        Consts.max_output_strlen,
                    )
                    # ネガティブプロンプト
                    ttk.Label(self.crnt_task_prompts_frame, text="ネガティブプロンプト").grid(
                        row=2, column=0, padx=6, pady=6, sticky="w"
                    )
                    self.neg_prompt_tiplabel = TipLabel(
                        self.crnt_task_prompts_frame,
                        2,
                        1,
                        Consts.not_available_text,
                        Consts.max_output_strlen,
                    )

            class CrntTaskMetaInfoFrame:
                """
                現在のタスクメタ情報フレーム
                """

                def __init__(self, owner: Displayer.InfoWindow.TaskInfoTab):
                    """
                    現在のタスクメタ情報フレームコンストラクタ

                    Args:
                        owner (Displayer.InfoWindow): InfoWindow インスタンス
                    """
                    self.super_owner = owner

                    self.crnt_task_metainfo_frame = ttk.Frame(owner.main_frame)
                    self.crnt_task_metainfo_frame.grid(row=2, column=0, sticky="swe")
                    self.crnt_task_metainfo_frame.columnconfigure(0, weight=1)
                    self.crnt_task_metainfo_frame.columnconfigure(1, weight=1)

                    # ステップ数
                    self.steps_strvar = owner.super_owner.super_owner.put_textlabel(
                        self.crnt_task_metainfo_frame,
                        "ステップ数",
                        0,
                        0,
                        Consts.not_available_text,
                        "w",
                    )
                    # バッチサイズ
                    self.batch_size_strvar = owner.super_owner.super_owner.put_textlabel(
                        self.crnt_task_metainfo_frame,
                        "バッチサイズ",
                        0,
                        2,
                        Consts.not_available_text,
                        "w",
                    )
                    # サンプラ
                    self.sampler_strvar = owner.super_owner.super_owner.put_textlabel(
                        self.crnt_task_metainfo_frame,
                        "サンプラ",
                        1,
                        0,
                        Consts.not_available_text,
                        "w",
                    )
                    # スケジューラ
                    self.scheduler_strvar = owner.super_owner.super_owner.put_textlabel(
                        self.crnt_task_metainfo_frame,
                        "スケジューラ",
                        1,
                        2,
                        Consts.not_available_text,
                        "w",
                    )
                    # スケール
                    self.scale_strvar = owner.super_owner.super_owner.put_textlabel(
                        self.crnt_task_metainfo_frame,
                        "スケール",
                        1,
                        4,
                        Consts.not_available_text,
                        "w",
                    )
                    # シード値
                    self.seed_strvar = owner.super_owner.super_owner.put_textlabel(
                        self.crnt_task_metainfo_frame,
                        "シード値",
                        2,
                        0,
                        Consts.not_available_text,
                        "w",
                    )
                    # 幅
                    self.width_strvar = owner.super_owner.super_owner.put_textlabel(
                        self.crnt_task_metainfo_frame, "幅", 3, 0, Consts.not_available_text, "w"
                    )
                    # 高さ
                    self.height_strvar = owner.super_owner.super_owner.put_textlabel(
                        self.crnt_task_metainfo_frame, "高さ", 3, 2, Consts.not_available_text, "w"
                    )
                    # 宛先アドレス
                    self.addr_strvar = owner.super_owner.super_owner.put_textlabel(
                        self.crnt_task_metainfo_frame,
                        "宛先アドレス",
                        4,
                        0,
                        Consts.not_available_text,
                        "w",
                    )
                    # 宛先ポート
                    self.port_strvar = owner.super_owner.super_owner.put_textlabel(
                        self.crnt_task_metainfo_frame,
                        "宛先ポート",
                        4,
                        2,
                        Consts.not_available_text,
                        "w",
                    )

            def __init__(self, owner: Displayer.InfoWindow):
                """
                タスク情報タブコンストラクタ

                Args:
                    owner (Displayer.InfoWindow): InfoWindow インスタンス
                """
                self.super_owner = owner

                self.main_frame = ttk.Frame(owner.taskinfo_tab)
                self.main_frame.grid(row=0, column=0, sticky="nsew")

                self.appinfo_frame = self.AppInfoFrame(self)
                self.crnt_task_prompts_frame = self.CrntTaskPromptsFrame(self)
                self.crnt_task_metainfo_frame = self.CrntTaskMetaInfoFrame(self)

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
                    self.infobox_frame.grid(row=0, column=0, sticky="nsew")
                    self.infobox_frame.grid_rowconfigure(0, weight=1)
                    self.infobox_frame.grid_columnconfigure(0, weight=1)

                    self.fullpath_strvar = owner.super_owner.super_owner.put_textlabel(
                        self.infobox_frame, "TBD", 0, 0, Consts.not_available_text, "w"
                    )

            def __init__(self, owner: Displayer.InfoWindow):
                """
                画像情報タブコンストラクタ

                Args:
                    owner (Displayer.InfoWindow): InfoWindow インスタンス
                """
                self.super_owner = owner

                self.main_frame = ttk.Frame(owner.picinfo_tab)
                self.main_frame.grid(row=0, column=0, sticky="nsew")

                self.infobox_frame = self.InfoBoxFrame(self)

        def __init__(self, owner: Displayer, fix_position: bool = False):
            """
            情報ウィンドウコンストラクタ

            Args:
                owner (Displayer): Display インスタンス
                fix_position (bool, optional): 表示位置を固定するか
            """
            self.super_owner = owner

            self.info_window = tkinter.Toplevel(self.super_owner.root)
            if fix_position:
                self.info_window.geometry(
                    (
                        f"+{owner.config_window_x}"
                        f"+{owner.config_window_y + owner.config_window_height + 50}"
                    )
                )
            self.info_window.title(f"pipmaker - 情報 [{owner.ownername}]")
            self.info_window.protocol("WM_DELETE_WINDOW", self.super_owner.destroy_info_window)

            self.main_frame = ttk.Frame(self.info_window)
            self.main_frame.grid(row=0, column=0, sticky="nsew")

            # Notebook（タブ）
            self.notebook = ttk.Notebook(self.main_frame)
            self.notebook.grid(row=0, column=0, sticky="nsew")
            # タスク情報タブ
            self.taskinfo_tab = ttk.Frame(self.notebook, padding=12)
            self.notebook.add(self.taskinfo_tab, text="タスク")
            self.taskinfo_tab_obj = self.TaskInfoTab(self)
            # 画像情報タブ
            self.picinfo_tab = ttk.Frame(self.notebook, padding=12)
            self.notebook.add(self.picinfo_tab, text="画像")
            self.picinfo_tab_obj = self.PicInfoTab(self)

    class PicWindow:
        """
        画像ウィンドウ
        """

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
                    self.cursor_frame, text="<", width=2, command=owner.super_owner.on_prev
                )
                self.prev_button.grid(row=0, column=0, padx=6, pady=6, sticky="nsw")
                # ボタン(>)
                self.next_button = ttk.Button(
                    self.cursor_frame, text=">", width=2, command=owner.super_owner.on_next
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

                # ボタン(GOOD)
                self.good_button = ttk.Button(
                    self.eval_frame, text="GOOD", command=self.super_owner.super_owner.on_good
                )
                self.good_button.grid(row=0, column=0, padx=6, pady=6, sticky="wes")
                # ボタン(BAD)
                self.bad_button = ttk.Button(
                    self.eval_frame, text="BAD", command=self.super_owner.super_owner.on_bad
                )
                self.bad_button.grid(row=0, column=1, padx=6, pady=6, sticky="wes")

        def __init__(self, owner: Displayer, fix_position: bool = False):
            """
            画像ウィンドウコンストラクタ

            Args:
                owner (Displayer): Display インスタンス
                fix_position (bool, optional): 表示位置を固定するか
            """
            self.super_owner = owner

            self.pic_window = tkinter.Toplevel(self.super_owner.root)
            if fix_position:
                self.pic_window.geometry(
                    (
                        f"-{owner.config_window_x + owner.config_window_width + 50}"
                        f"+{owner.config_window_y}"
                    )
                )
            self.pic_window.title("pipmaker - 画像")
            self.pic_window.protocol("WM_DELETE_WINDOW", self.super_owner.destroy_pic_window)

            self.main_frame = ttk.Frame(self.pic_window, padding=5)
            self.main_frame.grid(row=0, column=0, sticky="nsew")

            self.cursor_frame = self.CursorFrame(self)
            self.eval_frame = self.EvalFrame(self)

    def __init__(
        self,
        picmanager: PicManager,
        taskmanager: TaskManager,
        on_edgepoint: Callable[[], None],
        on_append: Callable[[], None],
        on_debug: Callable[[], None],
        ownername: str,
    ):
        """
        コンストラクタ

        Args:
            picmanager (PicManager): PicManager インスタンス
            taskmanager (PicManager): TaskManager インスタンス
            on_edgepoint (Callable[[], None]): 端点処理コールバック
            on_append (Callable[[], None]): タスク登録処理コールバック
            on_debug (Callable[[], None]): デバッグ処理コールバック
            ownername (str): 所有者の名前
        """
        self.ownername = ownername

        self.picmanager: PicManager = picmanager
        self.taskmanager: TaskManager = taskmanager
        self.on_edgepoint: Callable[[], None] = on_edgepoint
        self.on_append: Callable[[], None] = on_append
        self.on_debug: Callable[[], None] = on_debug

        self.root = tkinter.Tk()
        self.config_window = self.ConfigWindow(self)
        self.info_window: Displayer.InfoWindow = None
        self.construct_info_window()
        self.pic_window: Displayer.PicWindow = None
        self.switch_output_button_state(False)

        self.noimage_img = ImageTk.PhotoImage(self.create_no_image_placeholder())

    def finalize(self) -> None:
        """
        終了処理\n
        Tkinter メインループ内でタスクスレッドの join とウィンドウの destroy を実施する
        """

        def worker():
            self.taskmanager.join()
            self.destroy_config_window()

        self.root.after(0, worker())

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
        ttk.Label(frame, text=name).grid(row=row, column=col, padx=6, pady=6, sticky=sticky)
        strvar = tkinter.StringVar(value=default)
        ttk.Label(frame, textvariable=strvar).grid(
            row=row, column=(col + 1), padx=6, pady=6, sticky=sticky
        )
        return strvar

    def is_config_window_open(self) -> bool:
        """
        設定ウィンドウが開かれているか

        Returns:
            bool: True: 開かれている, False: 開かれていない or TclError 例外発生
        """
        if self.root is None:
            return False
        try:
            return bool(self.root.winfo_exists())
        except TclError:
            return False

    def destroy_config_window(self) -> None:
        """
        設定ウィンドウのクローズ時のハンドラ
        """
        self.destroy_pic_window()
        self.destroy_info_window()
        if self.is_config_window_open():
            self.root.destroy()

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
        if self.info_window is None:
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
        self.info_window = None

    def update_appinfo_frame(self) -> None:
        """
        アプリケーション情報フレームの更新を行う\n
        更新は呼び出した瞬間の TaskManager をもとに行う
        """
        self.info_window.taskinfo_tab_obj.appinfo_frame.len_tasks_strvar.set(
            f"{self.taskmanager.len_tasks()}"
        )
        crnt_task: TaskBlueprint = self.taskmanager.crnt_task
        if crnt_task is None:
            self.info_window.taskinfo_tab_obj.appinfo_frame.task_progress["value"] = 0
            self.info_window.taskinfo_tab_obj.appinfo_frame.progress_strvar.set("0%")
        else:
            task_progress = self.taskmanager.post_progress()
            self.info_window.taskinfo_tab_obj.appinfo_frame.task_progress["value"] = (
                task_progress.progress if task_progress is not None else 0
            )
            task_progress_val = task_progress.progress * 100 if task_progress is not None else 0
            self.info_window.taskinfo_tab_obj.appinfo_frame.progress_strvar.set(
                f"{task_progress_val:.0f}%"
            )

    def update_taskinfo_frame(self) -> None:
        """
        プロンプト, タスクメタ情報フレームの更新を行う\n
        更新は呼び出した瞬間の TaskManager をもとに行う
        """
        crnt_task: TaskBlueprint = self.taskmanager.crnt_task
        if crnt_task is None:
            self.info_window.taskinfo_tab_obj.crnt_task_prompts_frame.pos_prompt_tiplabel.set_text(
                Consts.not_available_text
            )
            self.info_window.taskinfo_tab_obj.crnt_task_prompts_frame.neg_prompt_tiplabel.set_text(
                Consts.not_available_text
            )
            self.info_window.taskinfo_tab_obj.crnt_task_metainfo_frame.steps_strvar.set(
                Consts.not_available_text
            )
            self.info_window.taskinfo_tab_obj.crnt_task_metainfo_frame.batch_size_strvar.set(
                Consts.not_available_text
            )
            self.info_window.taskinfo_tab_obj.crnt_task_metainfo_frame.sampler_strvar.set(
                Consts.not_available_text
            )
            self.info_window.taskinfo_tab_obj.crnt_task_metainfo_frame.scheduler_strvar.set(
                Consts.not_available_text
            )
            self.info_window.taskinfo_tab_obj.crnt_task_metainfo_frame.scale_strvar.set(
                Consts.not_available_text
            )
            self.info_window.taskinfo_tab_obj.crnt_task_metainfo_frame.seed_strvar.set(
                Consts.not_available_text
            )
            self.info_window.taskinfo_tab_obj.crnt_task_metainfo_frame.width_strvar.set(
                Consts.not_available_text
            )
            self.info_window.taskinfo_tab_obj.crnt_task_metainfo_frame.height_strvar.set(
                Consts.not_available_text
            )
            self.info_window.taskinfo_tab_obj.crnt_task_metainfo_frame.addr_strvar.set(
                Consts.not_available_text
            )
            self.info_window.taskinfo_tab_obj.crnt_task_metainfo_frame.port_strvar.set(
                Consts.not_available_text
            )
        else:
            self.info_window.taskinfo_tab_obj.crnt_task_prompts_frame.pos_prompt_tiplabel.set_text(
                crnt_task.prompt
            )
            self.info_window.taskinfo_tab_obj.crnt_task_prompts_frame.neg_prompt_tiplabel.set_text(
                crnt_task.negative_prompt
            )
            self.info_window.taskinfo_tab_obj.crnt_task_metainfo_frame.steps_strvar.set(
                f"{crnt_task.steps}"
            )
            self.info_window.taskinfo_tab_obj.crnt_task_metainfo_frame.batch_size_strvar.set(
                f"{crnt_task.batch_size}"
            )
            self.info_window.taskinfo_tab_obj.crnt_task_metainfo_frame.sampler_strvar.set(
                crnt_task.sampler_name
            )
            self.info_window.taskinfo_tab_obj.crnt_task_metainfo_frame.scheduler_strvar.set(
                crnt_task.scheduler
            )
            self.info_window.taskinfo_tab_obj.crnt_task_metainfo_frame.scale_strvar.set(
                f"{crnt_task.cfg_scale}"
            )
            self.info_window.taskinfo_tab_obj.crnt_task_metainfo_frame.seed_strvar.set(
                f"{crnt_task.seed}"
            )
            self.info_window.taskinfo_tab_obj.crnt_task_metainfo_frame.width_strvar.set(
                f"{crnt_task.width}"
            )
            self.info_window.taskinfo_tab_obj.crnt_task_metainfo_frame.height_strvar.set(
                f"{crnt_task.height}"
            )
            self.info_window.taskinfo_tab_obj.crnt_task_metainfo_frame.addr_strvar.set(
                crnt_task.dst_addr
            )
            self.info_window.taskinfo_tab_obj.crnt_task_metainfo_frame.port_strvar.set(
                crnt_task.dst_port
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

    def construct_pic_window(self) -> None:
        """
        画像ウィンドウを構築する\n
        すでに開いている場合は最前面に表示のみ行う
        """
        if self.is_pic_window_open() and self.pic_window:
            self.pic_window.pic_window.deiconify()
            self.pic_window.pic_window.lift()
            return

        self.pic_window = self.PicWindow(self, fix_position=True)

    def is_pic_window_open(self) -> bool:
        """
        画像ウィンドウが開かれているか

        Returns:
            bool: True: 開かれている, False: 開かれていない or TclError 例外発生
        """
        if self.pic_window is None:
            return False
        try:
            return bool(self.pic_window.pic_window.winfo_exists())
        except TclError:
            return False

    def destroy_pic_window(self) -> None:
        """
        画像ウィンドウのクローズ時のハンドラ
        """
        if self.is_pic_window_open():
            self.pic_window.pic_window.destroy()
        self.pic_window = None

    def update_pic_window(self, picstats: PicStats) -> None:
        """
        画像ウィンドウを指定の PicStats で更新する\n
        picstats が None の場合は何もしない

        Args:
            picstats (PicStats): 更新予定の PicStats
        """
        if not picstats:
            return

        image = Image.open(picstats.path)
        tk_img = ImageTk.PhotoImage(image)
        self.construct_pic_window()
        self.pic_window.cursor_frame.pic_label.configure(image=tk_img)
        self.pic_window.cursor_frame.pic_label_image = tk_img

        self.switch_output_button_state(True)
        self.switch_picwindow_button_state(True)

    def create_no_image_placeholder(self) -> Image:
        """
        表示すべき画像がない場合の画像を作成する\n
        グレースケールのチェックパターンに"NO IMAGE"\n
        幅と高さは自動的に 8 の倍数に切り下げられる(Stable Diffusion の仕様に準拠)

        Returns:
            Image: 画像オブジェクト
        """
        light = "#e0e0e0"
        dark = "#c0c0c0"
        text_color = "#444444"
        width = self.sd_width & -8
        height = self.sd_height & -8
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

        return img

    def put_no_image_placeholder(self) -> None:
        """
        表示すべき画像がない場合の画像を画像ラベルに表示する\n
        幅と高さは設定に依存, 生成済みの画像と設定値のサイズが異なる場合は再生成
        """
        width = self.sd_width & -8
        height = self.sd_height & -8
        if self.noimage_img.width() != width or self.noimage_img.height() != height:
            self.noimage_img = ImageTk.PhotoImage(self.create_no_image_placeholder())

        self.construct_pic_window()
        self.pic_window.cursor_frame.pic_label.configure(image=self.noimage_img)
        self.pic_window.cursor_frame.pic_label_image = self.noimage_img
        self.switch_output_button_state(False)
        self.switch_picwindow_button_state(False)

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

    def switch_picwindow_button_state(self, toggle: bool) -> None:
        """
        画像ウィンドウ上のボタンの有効/無効(グレーアウト)を切り替える

        Args:
            toggle (bool): True で有効, False で無効
        """
        if not self.is_pic_window_open():
            return

        if toggle:
            self.pic_window.cursor_frame.next_button.configure(state="normal")
            self.pic_window.cursor_frame.prev_button.configure(state="normal")
            self.pic_window.eval_frame.good_button.configure(state="normal")
            self.pic_window.eval_frame.bad_button.configure(state="normal")
        else:
            self.pic_window.cursor_frame.next_button.configure(state="disabled")
            self.pic_window.cursor_frame.prev_button.configure(state="disabled")
            self.pic_window.eval_frame.good_button.configure(state="disabled")
            self.pic_window.eval_frame.bad_button.configure(state="disabled")

    def entrypoint(self) -> None:
        """
        エントリポイントの処理
        """
        self.root.after(100, self.on_edgepoint)
        self.root.mainloop()

    def endpoint(self) -> None:
        """
        エンドポイントの処理
        """
        self.update_info_window()
        self.root.after(300, self.on_edgepoint)

    def on_open_pic_window(self) -> None:
        """
        表示ボタンハンドラ\n
        表示すべき画像がないときは何もしない
        """
        self.update_pic_window(self.picmanager.crnt_picstats)

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

    def on_dump_picmanager(self) -> None:
        """
        PicManager ダンプボタンハンドラ
        """
        dump_json(self.picmanager.todict(), "picstats")

    def on_dump_tasks(self) -> None:
        """
        タスクリストダンプボタンハンドラ
        """

        dump_json(list(self.taskmanager.tasks), "tasks")

    def on_next(self) -> None:
        """
        > ボタンハンドラ
        """
        self.picmanager.next_picstats()
        self.update_pic_window(self.picmanager.crnt_picstats)

    def on_prev(self) -> None:
        """
        < ボタンハンドラ
        """
        self.picmanager.prev_picstats()
        self.update_pic_window(self.picmanager.crnt_picstats)

    def on_good(self) -> None:
        """
        GOOD ボタンハンドラ
        """
        return

    def on_bad(self) -> None:
        """
        BAD ボタンハンドラ\n
        表示中の画像を削除する\n
        削除後に同じディレクトリ内に画像が残っている場合はランダムで表示する\n
        残っていない場合はディレクトリを削除し, NO IMAGE を表示する
        """
        self.picmanager.remove_crnt_picstats()
        if self.picmanager.crnt_picstats is None:
            # 削除後に表示すべき画像がない
            self.put_no_image_placeholder()
        else:
            self.picmanager.warp_picstats(self.picmanager.crnt_picstats.dir)
            self.update_pic_window(self.picmanager.crnt_picstats)

    @property
    def config_window_x(self) -> int:
        """
        設定ウィンドウ(メインウィンドウ)の x 座標

        Returns:
            int: 設定ウィンドウ(メインウィンドウ)の x 座標
        """
        self.root.update_idletasks()
        return self.root.winfo_x()

    @property
    def config_window_y(self) -> int:
        """
        設定ウィンドウ(メインウィンドウ)の y 座標

        Returns:
            int: 設定ウィンドウ(メインウィンドウ)の y 座標
        """
        self.root.update_idletasks()
        return self.root.winfo_y()

    @property
    def config_window_width(self) -> int:
        """
        設定ウィンドウ(メインウィンドウ)の幅

        Returns:
            int: 設定ウィンドウ(メインウィンドウ)の幅
        """
        self.root.update_idletasks()
        return self.root.winfo_width()

    @property
    def config_window_height(self) -> int:
        """
        設定ウィンドウ(メインウィンドウ)の高さ

        Returns:
            int: 設定ウィンドウ(メインウィンドウ)の高さ
        """
        self.root.update_idletasks()
        return self.root.winfo_height()

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
    def print_images(self) -> bool:
        """
        応答 image があった場合にログ出力するか

        Returns:
            bool: True: 表示する, False: 表示しない
        """
        return self.config_window.debug_tab_obj.verbose_frame.verbose_image_check.get()

    @property
    def print_picinfo(self) -> bool:
        """
        応答 image の PicInfo をログ出力するか

        Returns:
            bool: True: 表示する, False: 表示しない
        """
        return self.config_window.debug_tab_obj.verbose_frame.verbose_picinfo_check.get()
