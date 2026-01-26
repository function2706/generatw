"""
GUI 管理クラス
"""

from __future__ import annotations

import tkinter
from tkinter import Frame, TclError, ttk

from common.classes import PicStats
from common.functions import dump_json
from common.interfaces import BackEnd, MasterIF
from displayer.info_window import InfoWindow
from displayer.pic_window import PicWindow


def put_textbox(
    frame: Frame, name: str, row: int, col: int, width: int, default: str, sticky: str
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
    frame: Frame, name: str, row: int, col: int, default: str, sticky: str
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


class MainTab:
    """
    メインタブ
    """

    class ButtonFrame:
        """
        ボタンフレーム
        """

        def __init__(self, owner: MainTab):
            """
            ボタンフレームコンストラクタ

            Args:
                owner (ConfigWindow.MainTab): MainTab インスタンス
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

        def __init__(self, owner: MainTab):
            """
            SD 内部設定フレームコンストラクタ

            Args:
                owner (ConfigWindow.MainTab): MainTab インスタンス
            """
            self.super_owner = owner

            self.sd_interior_config_frame = ttk.Frame(owner.main_frame)
            self.sd_interior_config_frame.grid(row=1, column=0, sticky="w")

            # テキストボックス(幅)
            self.width_entry = put_textbox(
                self.sd_interior_config_frame, "幅", 1, 0, 5, str(540), "w"
            )
            # テキストボックス(高さ)
            self.height_entry = put_textbox(
                self.sd_interior_config_frame, "高さ", 1, 2, 5, str(960), "w"
            )
            # テキストボックス(ステップ数)
            self.steps_entry = put_textbox(
                self.sd_interior_config_frame, "Steps", 2, 0, 4, str(30), "w"
            )
            # テキストボックス(生成数)
            self.batch_size_entry = put_textbox(
                self.sd_interior_config_frame, "生成数", 2, 2, 4, str(2), "w"
            )

    class SDExteriorConfigFrame:
        """
        SD 外部設定フレーム
        """

        def __init__(self, owner: MainTab):
            """
            SD 外部設定フレームコンストラクタ

            Args:
                owner (ConfigWindow.MainTab): MainTab インスタンス
            """
            self.super_owner = owner

            self.sd_exterior_config_frame = ttk.Frame(owner.main_frame)
            self.sd_exterior_config_frame.grid(row=2, column=0, sticky="w")

            # テキストボックス(IPアドレス)
            self.ipaddr_entry = put_textbox(
                self.sd_exterior_config_frame, "IPアドレス", 0, 0, 16, "127.0.0.1", "w"
            )
            # テキストボックス(ポート)
            type = owner.super_owner.super_owner.master.backend_type
            self.port_entry = put_textbox(
                self.sd_exterior_config_frame,
                "ポート",
                0,
                2,
                6,
                str(7860 if type == BackEnd.a1111 else 8188 if type == BackEnd.comfy_ui else 0),
                "w",
            )

    def __init__(self, owner: MainWindow):
        """
        メインタブコンストラクタ

        Args:
            owner (ConfigWindow): ConfigWindow インスタンス
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

        def __init__(self, owner: DebugTab):
            """
            デバッグ実行フレームコンストラクタ

            Args:
                owner (ConfigWindow.DebugTab): DebugTab インスタンス
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

        def __init__(self, owner: DebugTab):
            """
            表示設定フレームコンストラクタ

            Args:
                owner (ConfigWindow.DebugTab): DebugTab インスタンス
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

    def __init__(self, owner: MainWindow):
        """
        デバッグタブコンストラクタ

        Args:
            owner (ConfigWindow): ConfigWindow インスタンス
        """
        self.super_owner = owner

        self.main_frame = ttk.Frame(owner.debug_tab)
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        self.exe_debug_frame = self.ExeDebugFrame(self)
        self.verbose_frame = self.VerboseFrame(self)


class MainWindow:
    """
    メインウィンドウ(設定等)
    """

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
        owner.master.root.protocol("WM_DELETE_WINDOW", owner.destroy)
        # Notebook（タブ）
        self.notebook = ttk.Notebook(owner.master.root)
        self.notebook.grid(row=0, column=0, sticky="nsew")
        # メインタブ
        self.main_tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.main_tab, text="メイン")
        self.main_tab_obj = MainTab(self)
        # デバッグタブ
        self.debug_tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.debug_tab, text="デバッグ")
        self.debug_tab_obj = DebugTab(self)


class Displayer:
    """
    GUI 管理クラス
    """

    def __init__(self, master: MasterIF):
        """
        コンストラクタ

        Args:
            master (MasterIF): Master インターフェース
        """
        self.master = master

        self.main_window = MainWindow(self)
        self.info_window = InfoWindow(self)
        self.info_window.construct()
        self.pic_window = PicWindow(self)
        self.switch_output_button_state(False)

    def exists(self) -> bool:
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

    def destroy(self, fix_position=False) -> None:
        """
        設定ウィンドウのクローズ時のハンドラ
        """
        self.pic_window.destroy()
        self.info_window.destroy()
        if self.exists():
            self.master.root.destroy()

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
            self.info_window.update_picinfo_tab()
        else:
            self.switch_output_button_state(False)
            self.info_window.update_picinfo_tab(reset=True)

    def switch_output_button_state(self, toggle: bool) -> None:
        """
        表示ボタンの有効/無効(グレーアウト)を切り替える

        Args:
            toggle (bool): True で有効, False で無効
        """
        if not self.exists():
            return

        if toggle:
            self.main_window.main_tab_obj.button_frame.output_button.configure(state="normal")
        else:
            self.main_window.main_tab_obj.button_frame.output_button.configure(state="disabled")

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
        if self.info_window is not None and self.pic_window.existed():
            self.info_window.info_window.deiconify()
            self.info_window.info_window.lift()
        else:
            self.info_window.construct()

        self.info_window.update()

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
        return self.main_window.main_tab_obj.sd_exterior_config_frame.ipaddr_entry.get()

    @property
    def srv_port(self) -> str:
        """
        ポスト先ポート

        Returns:
            str: ポスト先ポート
        """
        return self.main_window.main_tab_obj.sd_exterior_config_frame.port_entry.get()

    @property
    def sd_steps(self) -> int:
        """
        ステップ数

        Returns:
            int: ステップ数
        """
        return int(self.main_window.main_tab_obj.sd_interior_config_frame.steps_entry.get())

    @property
    def sd_batch_size(self) -> int:
        """
        バッチサイズ

        Returns:
            int: バッチサイズ
        """
        return int(self.main_window.main_tab_obj.sd_interior_config_frame.batch_size_entry.get())

    @property
    def sd_width(self) -> int:
        """
        幅

        Returns:
            int: 幅
        """
        return int(self.main_window.main_tab_obj.sd_interior_config_frame.width_entry.get())

    @property
    def sd_height(self) -> int:
        """
        高さ

        Returns:
            int: 高さ
        """
        return int(self.main_window.main_tab_obj.sd_interior_config_frame.height_entry.get())

    @property
    def allow_edit_clipboard(self) -> bool:
        """
        デバッグ時にクリップボード更新を認めるか

        Returns:
            bool: True: 認める, False: 認めない
        """
        return self.main_window.debug_tab_obj.exe_debug_frame.allow_edit_clipboard_check.get()

    @property
    def print_new_clipboard(self) -> bool:
        """
        クリップボードの更新があった場合にログ出力するか

        Returns:
            bool: True: 表示する, False: 表示しない
        """
        return self.main_window.debug_tab_obj.verbose_frame.verbose_clipboard_check.get()

    @property
    def print_new_stats(self) -> bool:
        """
        ステータスの更新があった場合にログ出力するか

        Returns:
            bool: True: 表示する, False: 表示しない
        """
        return self.main_window.debug_tab_obj.verbose_frame.verbose_stats_check.get()

    @property
    def print_picinfo(self) -> bool:
        """
        応答 image の PicInfo をログ出力するか

        Returns:
            bool: True: 表示する, False: 表示しない
        """
        return self.main_window.debug_tab_obj.verbose_frame.verbose_picinfo_check.get()
