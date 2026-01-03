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
                    self.owner = owner

                    self.button_frame = ttk.Frame(owner.main_frame)
                    self.button_frame.grid(row=0, column=0, sticky="w")

                    # ボタン(タスク登録)
                    self.gen_button = ttk.Button(
                        self.button_frame,
                        text="タスク登録",
                        command=owner.super_owner.super_owner.on_append,
                    )
                    self.gen_button.grid(row=0, column=0, padx=6, pady=6, sticky="w")
                    # ボタン(画像を表示)
                    self.output_button = ttk.Button(
                        self.button_frame,
                        text="画像を表示",
                        command=owner.super_owner.super_owner.on_output,
                    )
                    self.output_button.grid(row=0, column=1, padx=6, pady=6, sticky="w")

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
                    self.owner = owner

                    self.sd_interior_config_frame = ttk.Frame(owner.main_frame)
                    self.sd_interior_config_frame.grid(row=1, column=0, sticky="w")

                    # テキストボックス(幅)
                    self.width_entry = owner.super_owner.super_owner.put_textbox(
                        self.sd_interior_config_frame, "幅", 1, 0, 5, str(540)
                    )
                    # テキストボックス(高さ)
                    self.height_entry = owner.super_owner.super_owner.put_textbox(
                        self.sd_interior_config_frame, "高さ", 1, 2, 5, str(960)
                    )
                    # テキストボックス(ステップ数)
                    self.steps_entry = owner.super_owner.super_owner.put_textbox(
                        self.sd_interior_config_frame, "Steps", 2, 0, 4, str(30)
                    )
                    # テキストボックス(生成数)
                    self.batch_size_entry = owner.super_owner.super_owner.put_textbox(
                        self.sd_interior_config_frame, "生成数", 2, 2, 4, str(2)
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
                    self.owner = owner

                    self.sd_exterior_config_frame = ttk.Frame(owner.main_frame)
                    self.sd_exterior_config_frame.grid(row=2, column=0, sticky="w")

                    # テキストボックス(IPアドレス)
                    self.ipaddr_entry = owner.super_owner.super_owner.put_textbox(
                        self.sd_exterior_config_frame, "IPアドレス", 0, 0, 16, "127.0.0.1"
                    )
                    # テキストボックス(ポート)
                    self.port_entry = owner.super_owner.super_owner.put_textbox(
                        self.sd_exterior_config_frame, "ポート", 0, 2, 6, str(7860)
                    )

            class RunningModeFrame:
                """
                実行中モード表示フレーム
                """

                def __init__(self, owner: Displayer.ConfigWindow.MainTab):
                    """
                    実行中モード表示フレームコンストラクタ

                    Args:
                        owner (Displayer.ConfigWindow.MainTab): MainTab インスタンス
                    """
                    self.owner = owner

                    self.running_mode_frame = ttk.Frame(owner.main_frame)
                    self.running_mode_frame.grid(row=3, column=0, sticky="ew")
                    self.running_mode_frame.columnconfigure(0, weight=1)

                    # 動作モード
                    ttk.Label(
                        self.running_mode_frame,
                        text=f"動作モード: {owner.super_owner.super_owner.ownername}",
                    ).grid(row=0, column=0, padx=6, pady=6, sticky="e")

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
                self.running_mode_frame = self.RunningModeFrame(self)

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
                        text="デバッグ時にクリップボードを書き換える",
                        variable=self.allow_edit_clipboard_check,
                    ).grid(row=0, column=1, padx=6, pady=6, sticky="w")

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
            self.main_tab = self.MainTab(self)
            # デバッグタブ
            self.debug_tab = ttk.Frame(self.notebook, padding=12)
            self.notebook.add(self.debug_tab, text="デバッグ")
            self.debug_tab = self.DebugTab(self)

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

        def __init__(self, owner: Displayer):
            """
            画像ウィンドウコンストラクタ

            Args:
                owner (Displayer): Display インスタンス
            """
            self.super_owner = owner

            self.pic_window = tkinter.Toplevel(self.super_owner.root)
            self.pic_window.title("pipmaker - 画像")
            self.pic_window.protocol("WM_DELETE_WINDOW", self.super_owner.destroy_pic_window)

            self.main_frame = ttk.Frame(self.pic_window, padding=5)
            self.main_frame.grid(row=0, column=0, sticky="nsew")

            self.cursor_frame = self.CursorFrame(self)
            self.eval_frame = self.EvalFrame(self)

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

        self.root = tkinter.Tk()
        self.config_window = self.ConfigWindow(self)
        self.pic_window: Displayer.PicWindow = None

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
        if self.is_config_window_open():
            self.root.destroy()

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

    def construct_pic_window(self) -> None:
        """
        画像ウィンドウを構築する\n
        すでに開いている場合は最前面に表示のみ行う
        """
        if self.is_pic_window_open() and self.pic_window:
            self.pic_window.pic_window.deiconify()
            self.pic_window.pic_window.lift()
            return

        self.pic_window = self.PicWindow(self)

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
        self.pic_window.cursor_frame.pic_label.configure(image=tk_img)
        self.pic_window.cursor_frame.pic_label.image = tk_img

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
            self.config_window.main_tab.button_frame.output_button.configure(state="normal")
        else:
            self.config_window.main_tab.button_frame.output_button.configure(state="disabled")

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
        self.root.after(500, self.on_edgepoint)

    @property
    def srv_ipaddr(self) -> str:
        """
        ポスト先 IP アドレス

        Returns:
            str: ポスト先 IP アドレス
        """
        return self.config_window.main_tab.sd_exterior_config_frame.ipaddr_entry.get()

    @property
    def srv_port(self) -> str:
        """
        ポスト先ポート

        Returns:
            str: ポスト先ポート
        """
        return self.config_window.main_tab.sd_exterior_config_frame.port_entry.get()

    @property
    def sd_steps(self) -> int:
        """
        ステップ数

        Returns:
            int: ステップ数
        """
        return int(self.config_window.main_tab.sd_interior_config_frame.steps_entry.get())

    @property
    def sd_batch_size(self) -> int:
        """
        バッチサイズ

        Returns:
            int: バッチサイズ
        """
        return int(self.config_window.main_tab.sd_interior_config_frame.batch_size_entry.get())

    @property
    def sd_width(self) -> int:
        """
        幅

        Returns:
            int: 幅
        """
        return int(self.config_window.main_tab.sd_interior_config_frame.width_entry.get())

    @property
    def sd_height(self) -> int:
        """
        高さ

        Returns:
            int: 高さ
        """
        return int(self.config_window.main_tab.sd_interior_config_frame.height_entry.get())

    @property
    def allow_edit_clipboard(self) -> bool:
        """
        デバッグ時にクリップボード更新を認めるか

        Returns:
            bool: True: 認める, False: 認めない
        """
        return self.config_window.debug_tab.exe_debug_frame.allow_edit_clipboard_check.get()

    @property
    def print_new_clipboard(self) -> bool:
        """
        クリップボードの更新があった場合にログ出力するか

        Returns:
            bool: True: 表示する, False: 表示しない
        """
        return self.config_window.debug_tab.verbose_frame.verbose_clipboard_check.get()

    @property
    def print_new_stats(self) -> bool:
        """
        ステータスの更新があった場合にログ出力するか

        Returns:
            bool: True: 表示する, False: 表示しない
        """
        return self.config_window.debug_tab.verbose_frame.verbose_stats_check.get()

    @property
    def print_images(self) -> bool:
        """
        応答 image があった場合にログ出力するか

        Returns:
            bool: True: 表示する, False: 表示しない
        """
        return self.config_window.debug_tab.verbose_frame.verbose_image_check.get()

    @property
    def print_picinfo(self) -> bool:
        """
        応答 image の PicInfo をログ出力するか

        Returns:
            bool: True: 表示する, False: 表示しない
        """
        return self.config_window.debug_tab.verbose_frame.verbose_picinfo_check.get()
