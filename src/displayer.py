"""
GUI 管理クラス
"""

from __future__ import annotations

import tkinter
from dataclasses import dataclass
from pathlib import Path
from tkinter import Frame, TclError, ttk
from typing import Callable, Optional

from PIL import Image, ImageTk


@dataclass
class SDConfigs:
    """
    Stable Diffusion API 関連の設定一覧
    """

    ipaddr: Optional[str] = "127.0.0.1"
    port: Optional[int] = 7860
    steps: Optional[int] = 30
    batch_size: Optional[int] = 2
    sampler_name: Optional[str] = "DPM++ 2S a"
    scheduler: Optional[str] = "Karras"
    cfg_scale: Optional[float] = 7.0
    seed: Optional[int] = -1
    width: Optional[int] = 540
    height: Optional[int] = 960


class Displayer:
    """
    GUI 管理クラス
    """

    SD_CONFIGS_DEFAULT = SDConfigs()

    def __init__(
        self,
        on_entrypoint: Callable[[], None],
        on_endpoint: Callable[[], None],
        on_gen: Callable[[], None],
        on_output: Callable[[], None],
        on_debug: Callable[[], None],
        on_next: Callable[[], None],
        on_prev: Callable[[], None],
        on_good: Callable[[], None],
        on_bad: Callable[[], None],
    ):
        """
        コンストラクタ

        Args:
            on_entrypoint (Callable[[], None]): エントリポイントコールバック
            on_endpoint (Callable[[], None]): エンドポイントコールバック
            on_gen (Callable[[], None]): 生成処理コールバック
            on_output (Callable[[], None]): 表示処理コールバック
            on_debug (Callable[[], None]): デバッグ処理コールバック
            on_next (Callable[[], None]): Next 画像処理コールバック
            on_prev (Callable[[], None]): Prev 画像処理コールバック
            on_good (Callable[[], None]): Good 処理コールバック
            on_bad (Callable[[], None]): Bad 処理コールバック
        """
        self.on_entrypoint: Callable[[], None] = on_entrypoint
        self.on_endpoint: Callable[[], None] = on_endpoint
        self.on_gen: Callable[[], None] = on_gen
        self.on_output: Callable[[], None] = on_output
        self.on_debug: Callable[[], None] = on_debug
        self.on_next: Callable[[], None] = on_next
        self.on_prev: Callable[[], None] = on_prev
        self.on_good: Callable[[], None] = on_good
        self.on_bad: Callable[[], None] = on_bad

        # 設定ウィンドウ
        self.tk_root = tkinter.Tk()
        self.construct_config_window()

        # 画像ウィンドウ
        self.pic_window = None
        self.pic_main_frame = None
        self.pic_label_frame = None
        self.pic_eval_frame = None
        self.pic_label = None
        self.button_prev = None
        self.button_next = None
        self.pic_eval_frame = None
        self.button_good = None
        self.button_bad = None

    def put_textbox(
        self, frame: Frame, name: str, row: int, col: int, width: int, default: str
    ) -> ttk.Entry:
        """
        テキストボックスの作成\n
        本オブジェクトは column 2つ分を占めることに注意

        Args:
            frame (Frame): 挿入先フレーム
            name (str): ラベル
            row (int): フレーム内の row
            col (int): フレーム内の column
            width (int): 長さ
            default (str): デフォルト値

        Returns:
            ttk.Entry: オブジェクトインスタンス
        """
        ttk.Label(frame, text=name).grid(row=row, column=col, padx=6, pady=6, sticky="w")
        entry = ttk.Entry(frame, width=width)
        entry.grid(row=row, column=(col + 1), padx=2, pady=6, sticky="w")
        entry.insert(0, default)
        return entry

    def is_config_window_open(self) -> bool:
        """
        設定ウィンドウが開かれているか

        Returns:
            bool: True: 開かれている, False: 開かれていない or TclError 例外発生
        """
        if self.tk_root is None:
            return False
        try:
            return bool(self.tk_root.winfo_exists())
        except TclError:
            return False

    def destroy_config_window(self) -> None:
        """
        設定ウィンドウのクローズ時のハンドラ
        """
        self.destroy_pic_window()
        if self.is_config_window_open():
            self.tk_root.destroy()

    def is_pic_window_open(self) -> bool:
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

    def destroy_pic_window(self) -> None:
        """
        画像ウィンドウのクローズ時のハンドラ
        """
        if self.is_pic_window_open():
            self.pic_window.destroy()
        self.pic_window = None

    def construct_config_window(self) -> None:
        """
        GUI の構築
        """
        # ウィンドウ定義
        self.tk_root.protocol("WM_DELETE_WINDOW", self.destroy_config_window)
        self.tk_root.title("設定")
        self.tk_root.columnconfigure(0, weight=1)
        self.tk_root.rowconfigure(0, weight=1)
        # フレーム定義
        self.config_main_frame = ttk.Frame(self.tk_root, padding=12)
        self.config_main_frame.grid(row=0, column=0, sticky="nsew")
        self.config_button_frame = ttk.Frame(self.config_main_frame)
        self.config_button_frame.grid(row=0, column=0, sticky="w")
        self.config_param1_frame = ttk.Frame(self.config_main_frame)
        self.config_param1_frame.grid(row=1, column=0, sticky="w")
        self.config_param2_frame = ttk.Frame(self.config_main_frame)
        self.config_param2_frame.grid(row=2, column=0, sticky="w")
        # ボタン用フレーム
        # ボタン(今すぐ生成)
        self.button_gen = ttk.Button(
            self.config_button_frame, text="今すぐ生成", command=self.on_gen
        )
        self.button_gen.grid(row=0, column=0, padx=6, pady=6, sticky="w")
        # ボタン(画像を表示)
        self.button_output = ttk.Button(
            self.config_button_frame, text="画像を表示", command=self.on_output
        )
        self.button_output.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        # ボタン(デバッグ)
        self.button_debug = ttk.Button(
            self.config_button_frame, text="デバッグ", command=self.on_debug
        )
        self.button_debug.grid(row=0, column=2, padx=6, pady=6, sticky="w")
        # フレーム 1
        # テキストボックス(幅)
        self.entry_width = self.put_textbox(
            self.config_param1_frame, "幅", 1, 0, 5, str(self.SD_CONFIGS_DEFAULT.width)
        )
        # テキストボックス(高さ)
        self.entry_height = self.put_textbox(
            self.config_param1_frame, "高さ", 1, 2, 5, str(self.SD_CONFIGS_DEFAULT.height)
        )
        # テキストボックス(ステップ数)
        self.entry_steps = self.put_textbox(
            self.config_param1_frame, "Steps", 2, 0, 4, str(self.SD_CONFIGS_DEFAULT.steps)
        )
        # テキストボックス(生成数)
        self.entry_batch_size = self.put_textbox(
            self.config_param1_frame, "生成数", 2, 2, 4, str(self.SD_CONFIGS_DEFAULT.batch_size)
        )
        # フレーム 2
        # テキストボックス(IPアドレス)
        self.entry_ipaddr = self.put_textbox(
            self.config_param2_frame, "IPアドレス", 0, 0, 16, str(self.SD_CONFIGS_DEFAULT.ipaddr)
        )
        # テキストボックス(ポート)
        self.entry_port = self.put_textbox(
            self.config_param2_frame, "ポート", 0, 2, 6, str(self.SD_CONFIGS_DEFAULT.port)
        )

    def construct_pic_window(self) -> None:
        """
        画像ウィンドウを構成, ただしすでに開いている場合は最前面に表示するのみ
        """
        if self.is_pic_window_open():
            self.pic_window.deiconify()
            self.pic_window.lift()
            return

        self.pic_window = tkinter.Toplevel(self.tk_root)
        self.pic_window.title("画像")
        self.pic_window.protocol("WM_DELETE_WINDOW", self.destroy_pic_window)
        # フレーム定義
        self.pic_main_frame = ttk.Frame(self.pic_window, padding=5)
        self.pic_main_frame.grid(row=0, column=0, sticky="nsew")
        self.pic_label_frame = ttk.Frame(self.pic_main_frame)
        self.pic_label_frame.grid(row=0, column=0, sticky="nwe")
        self.pic_eval_frame = ttk.Frame(self.pic_main_frame)
        self.pic_eval_frame.grid(row=1, column=0, sticky="swe")
        # 画像フレーム
        # ラベル
        self.pic_label = ttk.Label(self.pic_label_frame)
        self.pic_label.grid(row=0, column=1, padx=6, pady=6, sticky="nswe")
        # ボタン(<)
        self.button_prev = ttk.Button(self.pic_label_frame, text="<", width=2, command=self.on_prev)
        self.button_prev.grid(row=0, column=0, padx=6, pady=6, sticky="nsw")
        # ボタン(>)
        self.button_next = ttk.Button(self.pic_label_frame, text=">", width=2, command=self.on_next)
        self.button_next.grid(row=0, column=2, padx=6, pady=6, sticky="nse")
        # 評価フレーム
        self.pic_eval_frame.columnconfigure(0, weight=1)
        self.pic_eval_frame.columnconfigure(1, weight=1)
        # ボタン(GOOD)
        self.button_good = ttk.Button(self.pic_eval_frame, text="GOOD", command=self.on_good)
        self.button_good.grid(row=0, column=0, padx=6, pady=6, sticky="wes")
        # ボタン(BAD)
        self.button_bad = ttk.Button(self.pic_eval_frame, text="BAD", command=self.on_bad)
        self.button_bad.grid(row=0, column=1, padx=6, pady=6, sticky="wes")

    def popup_with(self, path: Path) -> None:
        """
        指定の画像を画像ウィンドウに表示する

        Args:
            path (Path): 画像のパス
        """
        image = Image.open(path)
        tk_img = ImageTk.PhotoImage(image)
        self.construct_pic_window()
        self.pic_label.configure(image=tk_img)
        self.pic_label.image = tk_img

    def switch_output_button_state(self, toggle: bool) -> None:
        """
        表示ボタンの有効/無効(グレーアウト)を切り替える

        Args:
            toggle (bool): True で有効, False で無効
        """
        if not self.is_config_window_open():
            return

        if toggle:
            self.button_output.configure(state="normal")
        else:
            self.button_output.configure(state="disabled")

    def get_sd_configs(self) -> SDConfigs:
        """
        GUI から SD コンフィグを取得する
        """
        sd_configs = SDConfigs()
        sd_configs.ipaddr = self.entry_ipaddr.get()
        sd_configs.port = self.entry_port.get()
        sd_configs.steps = int(self.entry_steps.get())
        sd_configs.batch_size = int(self.entry_batch_size.get())
        sd_configs.sampler_name = "DPM++ 2S a"
        sd_configs.scheduler = "Karras"
        sd_configs.cfg_scale = 7.0
        sd_configs.seed = -1
        sd_configs.width = int(self.entry_width.get())
        sd_configs.height = int(self.entry_height.get())
        return sd_configs

    def entrypoint(self) -> None:
        """
        エントリポイントの処理
        """
        self.tk_root.after(100, self.on_entrypoint)
        self.tk_root.mainloop()

    def endpoint(self) -> None:
        """
        エンドポイントの処理
        """
        self.tk_root.after(500, self.on_endpoint)
