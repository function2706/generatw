"""
GUI 管理クラス
"""

from __future__ import annotations

import tkinter
from tkinter import Frame, TclError, ttk
from typing import Callable

from PIL import Image, ImageTk

from picmanager import PicManager, PicStats


class Displayer:
    """
    GUI 管理クラス
    """

    def __init__(
        self,
        picmanager: PicManager,
        on_edgepoint: Callable[[], None],
        on_append: Callable[[], None],
        on_debug: Callable[[], None],
        on_good: Callable[[], None],
        on_bad: Callable[[], None],
        ownername: str,
    ):
        """
        コンストラクタ

        Args:
            picmanager (PicManager): PicManager インスタンス
            on_edgepoint (Callable[[], None]): 端点処理コールバック
            on_append (Callable[[], None]): タスク登録処理コールバック
            on_debug (Callable[[], None]): デバッグ処理コールバック
            on_good (Callable[[], None]): Good 処理コールバック
            on_bad (Callable[[], None]): Bad 処理コールバック
            ownername (str): 所有者の名前
        """
        self.ownername = ownername

        self.picmanager: PicManager = picmanager
        self.on_edgepoint: Callable[[], None] = on_edgepoint
        self.on_append: Callable[[], None] = on_append
        self.on_debug: Callable[[], None] = on_debug
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

    def on_output(self) -> None:
        """
        表示ボタンハンドラ\n
        表示すべき画像がないときは何もしない
        """
        self.update_pic(self.picmanager.crnt_picstats)

    def on_next(self) -> None:
        """
        > ボタンハンドラ
        """
        self.update_pic(self.picmanager.next_picstats())

    def on_prev(self) -> None:
        """
        < ボタンハンドラ
        """
        self.update_pic(self.picmanager.prev_picstats())

    def construct_config_window(self) -> None:
        """
        GUI の構築
        """
        # ウィンドウ定義
        self.tk_root.protocol("WM_DELETE_WINDOW", self.destroy_config_window)
        self.tk_root.title("picmaker - 設定")
        self.tk_root.columnconfigure(0, weight=1)
        self.tk_root.rowconfigure(0, weight=1)
        # Notebook（タブ）
        notebook = ttk.Notebook(self.tk_root)
        notebook.grid(row=0, column=0, sticky="nsew")
        # タブ定義
        tab_main = ttk.Frame(notebook, padding=12)
        tab_debug = ttk.Frame(notebook, padding=12)
        notebook.add(tab_main, text="メイン")
        notebook.add(tab_debug, text="デバッグ")

        # メインタブ
        self.config_main_frame = ttk.Frame(tab_main)
        self.config_main_frame.grid(row=0, column=0, sticky="nsew")
        self.config_button_frame = ttk.Frame(self.config_main_frame)
        self.config_button_frame.grid(row=0, column=0, sticky="w")
        self.config_param1_frame = ttk.Frame(self.config_main_frame)
        self.config_param1_frame.grid(row=1, column=0, sticky="w")
        self.config_param2_frame = ttk.Frame(self.config_main_frame)
        self.config_param2_frame.grid(row=2, column=0, sticky="w")
        self.config_param3_frame = ttk.Frame(self.config_main_frame)
        self.config_param3_frame.grid(row=3, column=0, sticky="ew")
        self.config_param3_frame.columnconfigure(0, weight=1)
        # ボタン用フレーム
        # ボタン(タスク登録)
        self.button_gen = ttk.Button(
            self.config_button_frame, text="タスク登録", command=self.on_append
        )
        self.button_gen.grid(row=0, column=0, padx=6, pady=6, sticky="w")
        # ボタン(画像を表示)
        self.button_output = ttk.Button(
            self.config_button_frame, text="画像を表示", command=self.on_output
        )
        self.button_output.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        # フレーム 1
        # テキストボックス(幅)
        self.entry_width = self.put_textbox(self.config_param1_frame, "幅", 1, 0, 5, str(540))
        # テキストボックス(高さ)
        self.entry_height = self.put_textbox(self.config_param1_frame, "高さ", 1, 2, 5, str(960))
        # テキストボックス(ステップ数)
        self.entry_steps = self.put_textbox(self.config_param1_frame, "Steps", 2, 0, 4, str(30))
        # テキストボックス(生成数)
        self.entry_batch_size = self.put_textbox(
            self.config_param1_frame, "生成数", 2, 2, 4, str(2)
        )
        # フレーム 2
        # テキストボックス(IPアドレス)
        self.entry_ipaddr = self.put_textbox(
            self.config_param2_frame, "IPアドレス", 0, 0, 16, "127.0.0.1"
        )
        # テキストボックス(ポート)
        self.entry_port = self.put_textbox(self.config_param2_frame, "ポート", 0, 2, 6, str(7860))
        # 動作モード
        ttk.Label(self.config_param3_frame, text=f"動作モード: {self.ownername}").grid(
            row=0, column=0, padx=6, pady=6, sticky="e"
        )

        # デバッグタブ
        self.config_main_frame_debug = ttk.Frame(tab_debug)
        self.config_main_frame_debug.grid(row=0, column=0, sticky="nsew")
        self.config_param1_frame_debug = ttk.Frame(self.config_main_frame_debug)
        self.config_param1_frame_debug.grid(row=1, column=0, sticky="w")
        self.config_param2_frame_debug = ttk.Frame(self.config_main_frame_debug)
        self.config_param2_frame_debug.grid(row=2, column=0, sticky="w")
        # デバッグメインフレーム
        # フレーム 1
        # ボタン(デバッグ)
        self.button_debug = ttk.Button(
            self.config_param1_frame_debug, text="デバッグ", command=self.on_debug
        )
        self.button_debug.grid(row=0, column=0, padx=6, pady=6, sticky="w")
        # チェックボックス
        self.check_allow_edit_clipboard = tkinter.BooleanVar()
        ttk.Checkbutton(
            self.config_param1_frame_debug,
            text="デバッグ時にクリップボードを書き換える",
            variable=self.check_allow_edit_clipboard,
        ).grid(row=0, column=1, padx=6, pady=6, sticky="w")
        # フレーム 2
        self.radio_modes = ["表示しない", "表示する"]
        ttk.Label(self.config_param2_frame_debug, text=" クリップボード").grid(
            row=1, column=0, padx=6, pady=6, sticky="w"
        )
        self.radio_verbose_clipboard = tkinter.StringVar(value=self.radio_modes[0])
        for i, m in enumerate(self.radio_modes):
            ttk.Radiobutton(
                self.config_param2_frame_debug,
                text=m,
                value=m,
                variable=self.radio_verbose_clipboard,
            ).grid(row=1, column=1 + i, padx=4, pady=6, sticky="w")
        ttk.Label(self.config_param2_frame_debug, text=" ステータス").grid(
            row=2, column=0, padx=6, pady=6, sticky="w"
        )
        self.radio_verbose_stats = tkinter.StringVar(value=self.radio_modes[0])
        for i, m in enumerate(self.radio_modes):
            ttk.Radiobutton(
                self.config_param2_frame_debug,
                text=m,
                value=m,
                variable=self.radio_verbose_stats,
            ).grid(row=2, column=1 + i, padx=4, pady=6, sticky="w")
        ttk.Label(self.config_param2_frame_debug, text=" 応答(image)").grid(
            row=3, column=0, padx=6, pady=6, sticky="w"
        )
        self.radio_verbose_image = tkinter.StringVar(value=self.radio_modes[0])
        for i, m in enumerate(self.radio_modes):
            ttk.Radiobutton(
                self.config_param2_frame_debug,
                text=m,
                value=m,
                variable=self.radio_verbose_image,
            ).grid(row=3, column=1 + i, padx=4, pady=6, sticky="w")
        ttk.Label(self.config_param2_frame_debug, text=" PicInfo").grid(
            row=4, column=0, padx=6, pady=6, sticky="w"
        )
        self.radio_verbose_picinfo = tkinter.StringVar(value=self.radio_modes[0])
        for i, m in enumerate(self.radio_modes):
            ttk.Radiobutton(
                self.config_param2_frame_debug,
                text=m,
                value=m,
                variable=self.radio_verbose_picinfo,
            ).grid(row=4, column=1 + i, padx=4, pady=6, sticky="w")

    def construct_pic_window(self) -> None:
        """
        画像ウィンドウを構成, ただしすでに開いている場合は最前面に表示するのみ
        """
        if self.is_pic_window_open():
            self.pic_window.deiconify()
            self.pic_window.lift()
            return

        self.pic_window = tkinter.Toplevel(self.tk_root)
        self.pic_window.title("pipmaker - 画像")
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

    def update_pic(self, picstats: PicStats) -> None:
        """
        画像フレームを指定の PicStats で更新する\n
        picstats が None の場合は何もしない

        Args:
            picstats (PicStats): 更新予定の PicStats
        """
        if not picstats:
            return

        image = Image.open(picstats.path)
        tk_img = ImageTk.PhotoImage(image)
        self.construct_pic_window()
        self.pic_label.configure(image=tk_img)
        self.pic_label.image = tk_img

        self.picmanager.crnt_picstats = picstats
        self.switch_output_button_state(True)

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

    def entrypoint(self) -> None:
        """
        エントリポイントの処理
        """
        self.tk_root.after(100, self.on_edgepoint)
        self.tk_root.mainloop()

    def endpoint(self) -> None:
        """
        エンドポイントの処理
        """
        self.tk_root.after(500, self.on_edgepoint)

    @property
    def srv_ipaddr(self) -> str:
        return self.entry_ipaddr.get()

    @property
    def srv_port(self) -> str:
        return self.entry_port.get()

    @property
    def sd_steps(self) -> int:
        return int(self.entry_steps.get())

    @property
    def sd_batch_size(self) -> int:
        return int(self.entry_batch_size.get())

    @property
    def sd_width(self) -> int:
        return int(self.entry_width.get())

    @property
    def sd_height(self) -> int:
        return int(self.entry_height.get())

    @property
    def allow_edit_clipboard(self) -> bool:
        return self.check_allow_edit_clipboard.get()

    @property
    def print_new_clipboard(self) -> bool:
        return self.radio_verbose_clipboard.get() == self.radio_modes[1]

    @property
    def print_new_stats(self) -> bool:
        return self.radio_verbose_stats.get() == self.radio_modes[1]

    @property
    def print_images(self) -> bool:
        return self.radio_verbose_image.get() == self.radio_modes[1]

    @property
    def print_picinfo(self) -> bool:
        return self.radio_verbose_picinfo.get() == self.radio_modes[1]
