"""
情報ウィンドウ
"""

from __future__ import annotations

import tkinter
from dataclasses import dataclass
from tkinter import TclError, font, ttk
from typing import Any

from archiver.dataclasses import PicStats
from common.interfaces import DisplayerIF
from generator.dataclasses import TaskBlueprint


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


class CommonFrame:
    """
    タブ共通フレーム
    """

    def __init__(self, owner: InfoWindow, parent_frame: ttk.Frame):
        """
        タブ共通フレームコンストラクタ
        Args:
            owner (InfoWindow): InfoWindow インスタンス
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

        def __init__(self, owner: TaskInfoTab):
            """
            情報ボックスフレームコンストラクタ

            Args:
                owner (InfoWindow): InfoWindow インスタンス
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

    def __init__(self, owner: InfoWindow):
        """
        タスク情報タブコンストラクタ

        Args:
            owner (InfoWindow): InfoWindow インスタンス
        """
        self.super_owner = owner

        self.main_frame = ttk.Frame(owner.taskinfo_tab)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.rowconfigure(0, weight=0)
        self.main_frame.rowconfigure(1, weight=1)
        self.main_frame.columnconfigure(0, weight=1)

        self.common_frame = CommonFrame(owner, self.main_frame)
        self.infobox_frame = self.InfoBoxFrame(self)


class PicInfoTab:
    """
    画像情報タブ
    """

    class InfoBoxFrame:
        """
        情報ボックスフレーム
        """

        def __init__(self, owner: PicInfoTab):
            """
            情報ボックスフレームコンストラクタ

            Args:
                owner (PicInfoTab): PicInfoTab インスタンス
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

    def __init__(self, owner: InfoWindow):
        """
        画像情報タブコンストラクタ

        Args:
            owner (InfoWindow): InfoWindow インスタンス
        """
        self.super_owner = owner

        self.main_frame = ttk.Frame(owner.picinfo_tab)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.rowconfigure(0, weight=0)
        self.main_frame.rowconfigure(1, weight=1)
        self.main_frame.columnconfigure(0, weight=1)

        self.common_frame = CommonFrame(owner, self.main_frame)
        self.infobox_frame = self.InfoBoxFrame(self)


class InfoWindow:
    """
    情報ウィンドウ
    """

    def __init__(self, owner: DisplayerIF):
        """
        情報ウィンドウコンストラクタ

        Args:
            owner (DisplayerIF): Display インスタンス
            fix_position (bool, optional): 表示位置を固定するか
        """
        self.super_owner = owner
        self.info_window: tkinter.Toplevel = None
        self.len_tasks_strvar: tkinter.StringVar = None
        self.progress_val: tkinter.DoubleVar = None
        self.progress_strvar: tkinter.StringVar = None
        self.notebook: ttk.Notebook = None
        self.taskinfo_tab: ttk.Frame = None
        self.taskinfo_tab_obj: TaskInfoTab = None
        self.picinfo_tab: ttk.Frame = None
        self.picinfo_tab_obj: PicInfoTab = None

    def construct(self, fix_position=False) -> None:
        """
        情報ウィンドウを構築する\n
        すでに開いている場合は最前面に表示のみ行う
        """
        if self.existed() and self.info_window:
            return

        self.info_window = tkinter.Toplevel(self.super_owner.master.root)
        if fix_position:
            self.info_window.geometry(
                (
                    f"+{self.super_owner.config_window_x}"
                    f"+{
                        self.super_owner.config_window_y
                        + self.super_owner.config_window_height
                        + 50
                    }"
                )
            )
        self.info_window.title(
            f"picmaker - 情報 [{self.super_owner.master.frontend_name} "
            f"- {self.super_owner.master.backend_name}]"
        )
        self.info_window.protocol("WM_DELETE_WINDOW", self.destroy)
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
        self.taskinfo_tab_obj = TaskInfoTab(self)
        # 画像情報タブ
        self.picinfo_tab = ttk.Frame(self.notebook, padding=12)
        self.picinfo_tab.rowconfigure(0, weight=1)
        self.picinfo_tab.columnconfigure(0, weight=1)
        self.notebook.add(self.picinfo_tab, text="画像")
        self.picinfo_tab_obj = PicInfoTab(self)

    def destroy(self, fix_position=False) -> None:
        """
        情報ウィンドウのクローズ時のハンドラ
        """
        if self.existed():
            self.info_window.destroy()
        self.info_window = None

    def existed(self, fix_position=False) -> None:
        """
        情報ウィンドウが開かれているか

        Returns:
            bool: True: 開かれている, False: 開かれていない or TclError 例外発生
        """
        if self.info_window is None:
            return False
        try:
            return bool(self.info_window.winfo_exists())
        except TclError:
            return False

    def update_appinfo_frame(self) -> None:
        """
        アプリケーション情報フレームの更新を行う\n
        更新は呼び出した瞬間の TaskManager をもとに行う
        """
        self.len_tasks_strvar.set(f"{self.super_owner.master.crnt_tasks}")
        crnt_task: TaskBlueprint = self.super_owner.master.crnt_task
        if crnt_task is None:
            self.progress_val.set(0)
            self.progress_strvar.set("0%")
        else:
            self.progress_val.set(self.super_owner.master.crnt_progress)
            task_progress_val = self.super_owner.master.crnt_progress * 100
            self.progress_strvar.set(f"{task_progress_val:.0f}%")
            return

    def update_taskinfo_frame(self) -> None:
        """
        プロンプト, タスクメタ情報フレームの更新を行う\n
        更新は呼び出した瞬間の TaskManager をもとに行う
        """
        crnt_task: TaskBlueprint = self.super_owner.master.crnt_task
        if crnt_task is None:
            self.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "ポジティブプロンプト", Consts.not_available_text
            )
            self.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "ネガティブプロンプト", Consts.not_available_text
            )
            self.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "ステップ数", Consts.not_available_text
            )
            self.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "バッチサイズ", Consts.not_available_text
            )
            self.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "サンプラ", Consts.not_available_text
            )
            self.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "スケジューラ", Consts.not_available_text
            )
            self.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "スケール", Consts.not_available_text
            )
            self.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "シード値", Consts.not_available_text
            )
            self.taskinfo_tab_obj.infobox_frame.infobox_tree.set("幅", Consts.not_available_text)
            self.taskinfo_tab_obj.infobox_frame.infobox_tree.set("高さ", Consts.not_available_text)
            self.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "宛先アドレス", Consts.not_available_text
            )
            self.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "宛先ポート", Consts.not_available_text
            )
        else:
            self.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "ポジティブプロンプト", crnt_task.prompt
            )
            self.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "ネガティブプロンプト", crnt_task.negative_prompt
            )
            self.taskinfo_tab_obj.infobox_frame.infobox_tree.set("ステップ数", crnt_task.steps)
            self.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "バッチサイズ", crnt_task.batch_size
            )
            self.taskinfo_tab_obj.infobox_frame.infobox_tree.set("サンプラ", crnt_task.sampler_name)
            self.taskinfo_tab_obj.infobox_frame.infobox_tree.set(
                "スケジューラ", crnt_task.scheduler
            )
            self.taskinfo_tab_obj.infobox_frame.infobox_tree.set("スケール", crnt_task.cfg_scale)
            self.taskinfo_tab_obj.infobox_frame.infobox_tree.set("シード値", crnt_task.seed)
            self.taskinfo_tab_obj.infobox_frame.infobox_tree.set("幅", crnt_task.width)
            self.taskinfo_tab_obj.infobox_frame.infobox_tree.set("高さ", crnt_task.height)
            self.taskinfo_tab_obj.infobox_frame.infobox_tree.set("宛先アドレス", crnt_task.dst_addr)
            self.taskinfo_tab_obj.infobox_frame.infobox_tree.set("宛先ポート", crnt_task.dst_port)

    def update_picinfo_tab(self, reset: bool = False) -> None:
        crnt_picstats: PicStats = self.super_owner.master.crnt_picstats
        if not crnt_picstats or reset:
            self.picinfo_tab_obj.infobox_frame.infobox_tree.set("場所", Consts.not_available_text)
            self.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "ポジティブプロンプト", Consts.not_available_text
            )
            self.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "ネガティブプロンプト", Consts.not_available_text
            )
            self.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "ステップ数", Consts.not_available_text
            )
            self.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "サンプラ", Consts.not_available_text
            )
            self.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "スケジューラ", Consts.not_available_text
            )
            self.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "スケール", Consts.not_available_text
            )
            self.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "シード値", Consts.not_available_text
            )
            self.picinfo_tab_obj.infobox_frame.infobox_tree.set("幅", Consts.not_available_text)
            self.picinfo_tab_obj.infobox_frame.infobox_tree.set("高さ", Consts.not_available_text)
        else:
            self.picinfo_tab_obj.infobox_frame.infobox_tree.set("場所", crnt_picstats.path)
            self.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "ポジティブプロンプト", crnt_picstats.info.positive_prompt
            )
            self.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "ネガティブプロンプト", crnt_picstats.info.negative_prompt
            )
            self.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "ステップ数", crnt_picstats.info.steps
            )
            self.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "サンプラ", crnt_picstats.info.sampler
            )
            self.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "スケジューラ", crnt_picstats.info.scheduler
            )
            self.picinfo_tab_obj.infobox_frame.infobox_tree.set(
                "スケール", crnt_picstats.info.cfg_scale
            )
            self.picinfo_tab_obj.infobox_frame.infobox_tree.set("シード値", crnt_picstats.info.seed)
            self.picinfo_tab_obj.infobox_frame.infobox_tree.set("幅", crnt_picstats.info.width)
            self.picinfo_tab_obj.infobox_frame.infobox_tree.set("高さ", crnt_picstats.info.height)

    def update(self, fix_position=False) -> None:
        """
        情報ウィンドウの更新を行う\n
        ウィンドウが開いていない場合は何もしない\n
        更新は呼び出した瞬間の TaskManager をもとに行う
        """
        if not self.info_window:
            return

        self.update_appinfo_frame()
        self.update_taskinfo_frame()
