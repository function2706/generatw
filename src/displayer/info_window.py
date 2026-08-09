"""
情報ウィンドウ
"""

from __future__ import annotations

import tkinter
from dataclasses import dataclass
from tkinter import TclError, font, ttk
from typing import TYPE_CHECKING, Any

from archiver.dataclasses import NoImageStats, PicStats
from displayer import widgets
from displayer.theme import STYLES
from generator.dataclasses import TaskBlueprint, TaskBlueprintImg2Img, TaskBlueprintTxt2Img

if TYPE_CHECKING:
    from displayer.displayer import Displayer


@dataclass(frozen=True)
class Consts:
    """
    このクラス関連の定数
    """

    # N/A テキスト
    not_available_text: str = "-"


# タスク情報タブの行キー (表示順)
TASK_ROWS: tuple[str, ...] = (
    "タスク種別",
    "ポジティブプロンプト",
    "ネガティブプロンプト",
    "ステップ数",
    "バッチサイズ",
    "サンプラ",
    "スケジューラ",
    "リサイズモード",
    "アップスケーラ",
    "デノイズ強度",
    "スケール",
    "シード値",
    "幅",
    "高さ",
    "宛先アドレス",
    "宛先ポート",
)

# 画像情報タブの行キー (表示順)
PIC_ROWS: tuple[str, ...] = (
    "場所",
    "ポジティブプロンプト",
    "ネガティブプロンプト",
    "ステップ数",
    "サンプラ",
    "スケジューラ",
    "スケール",
    "シード値",
    "幅",
    "高さ",
)


class InfoTree:
    """
    キー/値の 2 カラムツリービュー
    """

    def __init__(self, parent: ttk.Frame, rows: tuple[str, ...]):
        """
        コンストラクタ

        Args:
            parent (ttk.Frame): 配置先フレーム
            rows (tuple[str, ...]): 行キー (表示順)
        """
        self.frame = ttk.Frame(parent, style=STYLES.card, padding=1)
        self.frame.pack(fill="both", expand=True)
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)

        self.columns = ("キー", "値")
        self.tree = ttk.Treeview(self.frame, columns=self.columns, show="headings")
        self._font = font.nametofont("TkDefaultFont")

        for col in self.columns:
            self.tree.column(col, width=60, stretch=False, anchor="w")
            self.tree.heading(col, text=col, anchor="w")

        scroll = ttk.Scrollbar(self.frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        self._key_to_iid: dict[str, str] = {}
        for key in rows:
            self._key_to_iid[key] = self.tree.insert(
                "", "end", values=(key, Consts.not_available_text)
            )

        for col_idx in range(len(self.columns)):
            self.adjust(col_idx)

    def adjust(self, col_idx: int) -> None:
        """
        特定列の幅を内容に合わせて調整する

        Args:
            col_idx (int): 調整する列のインデックス
        """
        if not self.tree.winfo_exists():
            return
        try:
            col = self.columns[col_idx]
            max_width = self._font.measure(col)
            for iid in self.tree.get_children():
                w = self._font.measure(str(self.tree.item(iid, "values")[col_idx]))
                max_width = max(max_width, w)
            self.tree.column(col, width=max_width + 20)
        except tkinter.TclError:
            return

    def set(self, key: str, val: Any) -> None:
        """
        指定行の値を書き換える

        Args:
            key (str): 行キー
            val (Any): 値
        """
        if not self.tree.winfo_exists() or key not in self._key_to_iid:
            return
        iid = self._key_to_iid[key]
        self.tree.item(iid, values=(key, str(val)))
        self.adjust(1)

    def set_all(self, values: dict[str, Any]) -> None:
        """
        複数行を一括で書き換える

        Args:
            values (dict[str, Any]): {行キー: 値}
        """
        for key, val in values.items():
            self.set(key, val)


class InfoTab:
    """
    共通ヘッダ (残りタスク数 + 進捗) と情報ツリーを持つタブ
    """

    def __init__(self, owner: InfoWindow, parent: ttk.Frame, rows: tuple[str, ...]):
        """
        コンストラクタ

        Args:
            owner (InfoWindow): InfoWindow インスタンス
            parent (ttk.Frame): 配置先タブフレーム
            rows (tuple[str, ...]): 情報ツリーの行キー
        """
        self.super_owner = owner

        self.main_frame = ttk.Frame(parent)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.rowconfigure(2, weight=1)
        self.main_frame.columnconfigure(0, weight=1)

        # --- 共通ヘッダ (残りタスク数 + 進捗) --------------------------------
        head = ttk.Frame(self.main_frame, style=STYLES.card, padding=10)
        head.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        head.columnconfigure(2, weight=1)

        ttk.Label(head, text="残りタスク数", style=STYLES.muted).grid(row=0, column=0, sticky="w")
        ttk.Label(head, textvariable=owner.len_tasks_strvar, style=STYLES.value).grid(
            row=0, column=1, padx=(8, 16), sticky="w"
        )
        ttk.Progressbar(
            head,
            orient="horizontal",
            mode="determinate",
            variable=owner.progress_val,
            maximum=1,
        ).grid(row=0, column=2, padx=(0, 8), sticky="ew")
        ttk.Label(head, textvariable=owner.progress_strvar, style=STYLES.value, width=4).grid(
            row=0, column=3, sticky="e"
        )

        # --- 情報ツリー ------------------------------------------------------
        ttk.Label(self.main_frame, text="詳細", style=STYLES.section).grid(
            row=1, column=0, sticky="w", pady=(0, 2)
        )
        tree_holder = ttk.Frame(self.main_frame)
        tree_holder.grid(row=2, column=0, sticky="nsew")
        self.tree = InfoTree(tree_holder, rows)


class InfoWindow:
    """
    情報ウィンドウ
    """

    def __init__(self, owner: Displayer):
        """
        コンストラクタ

        Args:
            owner (Displayer): Displayer インスタンス
        """
        self.super_owner = owner
        self.info_window: tkinter.Toplevel = None
        self.len_tasks_strvar: tkinter.StringVar = None
        self.progress_val: tkinter.DoubleVar = None
        self.progress_strvar: tkinter.StringVar = None
        self.notebook: ttk.Notebook = None
        self.taskinfo_tab: ttk.Frame = None
        self.taskinfo_tab_obj: InfoTab = None
        self.picinfo_tab: ttk.Frame = None
        self.picinfo_tab_obj: InfoTab = None

    def construct(self, fix_position=False) -> None:
        """
        情報ウィンドウを構築する\n
        すでに開いている場合は何もしない

        Args:
            fix_position (bool): 表示位置を親ウィンドウ基準に固定するか
        """
        if self.existed() and self.info_window:
            return

        self.info_window = tkinter.Toplevel(self.super_owner.master.root)
        widgets.apply_toplevel_bg(self.info_window)
        win_w, win_h = 500, 460
        self.info_window.title("picmaker - 情報")
        self.info_window.protocol("WM_DELETE_WINDOW", self.destroy)
        self.info_window.geometry(f"{win_w}x{win_h}")
        if fix_position:
            # メインウィンドウの下に配置しつつ, 画面外へはみ出さないよう調整する
            x = self.super_owner.config_window_x
            y = self.super_owner.config_window_y + self.super_owner.config_window_height + 50
            max_y = self.info_window.winfo_screenheight() - win_h - 60
            self.info_window.geometry(f"+{x}+{min(y, max(0, max_y))}")
        self.info_window.rowconfigure(0, weight=1)
        self.info_window.columnconfigure(0, weight=1)

        # タブを跨いで共有する状態
        if self.len_tasks_strvar is None:
            self.len_tasks_strvar = tkinter.StringVar(value="0")
        if self.progress_val is None:
            self.progress_val = tkinter.DoubleVar(value=0)
        if self.progress_strvar is None:
            self.progress_strvar = tkinter.StringVar(value="0%")

        self.notebook = ttk.Notebook(self.info_window)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.taskinfo_tab = ttk.Frame(self.notebook, padding=12)
        self.taskinfo_tab.rowconfigure(0, weight=1)
        self.taskinfo_tab.columnconfigure(0, weight=1)
        self.notebook.add(self.taskinfo_tab, text="タスク")
        self.taskinfo_tab_obj = InfoTab(self, self.taskinfo_tab, TASK_ROWS)

        self.picinfo_tab = ttk.Frame(self.notebook, padding=12)
        self.picinfo_tab.rowconfigure(0, weight=1)
        self.picinfo_tab.columnconfigure(0, weight=1)
        self.notebook.add(self.picinfo_tab, text="画像")
        self.picinfo_tab_obj = InfoTab(self, self.picinfo_tab, PIC_ROWS)

    def destroy(self, fix_position=False) -> None:
        """
        情報ウィンドウのクローズ時のハンドラ
        """
        if self.existed():
            self.info_window.destroy()
        self.info_window = None

    def existed(self, fix_position=False) -> bool:
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

    # -------------------------------------------------------------------------
    # 更新
    # -------------------------------------------------------------------------

    def update_taskinfo_tab(
        self,
        task: TaskBlueprint = None,
        progress: float = None,
        tasks: int = None,
        done: bool = False,
    ) -> None:
        """
        進捗・残りタスク数・タスク詳細を更新する

        Args:
            task (TaskBlueprint): 新規タスク (None で詳細は据え置き)
            progress (float): 進捗 (0.0-1.0)
            tasks (int): 残りタスク数
            done (bool): タスク完了時 True (詳細と進捗をリセット)
        """
        self._update_progress(progress, tasks, done)

        if done:
            self.super_owner.last_task = None
            values = {k: Consts.not_available_text for k in TASK_ROWS}
        elif isinstance(task, TaskBlueprintTxt2Img):
            self.super_owner.last_task = task
            values = self._txt2img_values(task)
        elif isinstance(task, TaskBlueprintImg2Img):
            self.super_owner.last_task = task
            values = self._img2img_values(task)
        else:
            return  # progress / tasks のみの更新

        self.taskinfo_tab_obj.tree.set_all(values)

    def _update_progress(self, progress: float | None, tasks: int | None, done: bool) -> None:
        """
        残りタスク数と進捗バーを更新する
        """
        if done:
            self.len_tasks_strvar.set(f"{int(self.len_tasks_strvar.get()) - 1}")
            self.progress_val.set(0.0)
            self.progress_strvar.set("0%")
            return
        if tasks is not None:
            self.len_tasks_strvar.set(f"{tasks}")
        if progress is not None:
            self.progress_val.set(progress)
            self.progress_strvar.set("0%" if progress == 0 else f"{progress * 100:.0f}%")

    @staticmethod
    def _txt2img_values(task: TaskBlueprintTxt2Img) -> dict[str, Any]:
        """
        txt2img タスクの詳細値を組み立てる
        """
        na = Consts.not_available_text
        return {
            "タスク種別": "txt2img",
            "ポジティブプロンプト": task.prompt,
            "ネガティブプロンプト": task.negative_prompt,
            "ステップ数": task.steps,
            "バッチサイズ": task.batch_size,
            "サンプラ": task.sampler_name,
            "スケジューラ": task.scheduler,
            "リサイズモード": na,
            "アップスケーラ": na,
            "デノイズ強度": "1.0",
            "スケール": task.cfg_scale,
            "シード値": task.seed,
            "幅": task.width,
            "高さ": task.height,
            "宛先アドレス": task.dst_addr,
            "宛先ポート": task.dst_port,
        }

    @staticmethod
    def _img2img_values(task: TaskBlueprintImg2Img) -> dict[str, Any]:
        """
        img2img タスクの詳細値を組み立てる
        """
        na = Consts.not_available_text
        return {
            "タスク種別": "img2img",
            "ポジティブプロンプト": task.prompt,
            "ネガティブプロンプト": task.negative_prompt,
            "ステップ数": task.steps,
            "バッチサイズ": task.batch_size,
            "サンプラ": task.sampler_name,
            "スケジューラ": task.scheduler,
            "リサイズモード": task.resize_mode if not task.upscaler_name else na,
            "アップスケーラ": task.upscaler_name if task.upscaler_name else na,
            "デノイズ強度": task.denoising_strength,
            "スケール": task.cfg_scale,
            "シード値": task.seed,
            "幅": task.width,
            "高さ": task.height,
            "宛先アドレス": task.dst_addr,
            "宛先ポート": task.dst_port,
        }

    def update_picinfo_tab(self, picstats: PicStats | NoImageStats) -> None:
        """
        画像情報を更新する

        Args:
            picstats (PicStats | NoImageStats): 画像ステータス (None / NoImage で N/A)
        """
        na = Consts.not_available_text
        if picstats is None or picstats is NoImageStats:
            values = {k: na for k in PIC_ROWS}
        else:
            info = picstats.info
            values = {
                "場所": picstats.path,
                "ポジティブプロンプト": info.positive_prompt,
                "ネガティブプロンプト": info.negative_prompt,
                "ステップ数": info.steps,
                "サンプラ": info.sampler,
                "スケジューラ": info.scheduler,
                "スケール": info.cfg_scale,
                "シード値": info.seed,
                "幅": info.width,
                "高さ": info.height,
            }
        self.picinfo_tab_obj.tree.set_all(values)
