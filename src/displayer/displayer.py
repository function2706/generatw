"""
GUI 管理クラス
"""

from __future__ import annotations

import tkinter
from pathlib import Path
from tkinter import Frame, TclError, filedialog, ttk

import master.events
from archiver.dataclasses import NoImageStats, PicStats
from common.functions import BottleMail
from displayer.dataclasses import GUIConfigs
from displayer.info_window import InfoWindow
from displayer.pic_window import PicWindow
from generator.dataclasses import TaskBlueprint
from master.interfaces import BackEnd, MasterIF


def put_textbox(
    frame: Frame,
    name: str,
    row: int,
    col: int,
    width: int,
    default: str,
    sticky: str,
    on_change=None,
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
        on_change: FocusOut 発火時の処理

    Returns:
        ttk.Entry: オブジェクトインスタンス
    """
    ttk.Label(frame, text=name).grid(row=row, column=col, padx=6, pady=6, sticky=sticky)
    entry = ttk.Entry(frame, width=width)
    entry.grid(row=row, column=(col + 1), padx=2, pady=6, sticky=sticky)
    entry.insert(0, default)
    entry.bind("<Return>", lambda e: e.widget.master.focus_set())
    entry.bind("<FocusOut>", lambda e: on_change() if on_change else None)
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

            # ボタン(再実行)
            self.repeat_button = ttk.Button(
                self.button_frame,
                text="再実行",
                command=owner.super_owner.super_owner.on_repeat_task,
            )
            self.repeat_button.grid(row=0, column=0, padx=6, pady=6, sticky="w")
            # ボタン(中断)
            self.interrupt_button = ttk.Button(
                self.button_frame,
                text="中断",
                command=owner.super_owner.super_owner.on_interrput_task,
            )
            self.interrupt_button.grid(row=0, column=1, padx=6, pady=6, sticky="w")
            # タスククリア
            self.clear_button = ttk.Button(
                self.button_frame,
                text="タスククリア",
                command=owner.super_owner.super_owner.on_flush_tasks,
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
            # ボタン(YAML選択)
            self.select_yaml_button = ttk.Button(
                self.button_frame,
                text="YAML選択",
                command=owner.super_owner.super_owner.on_select_yaml,
            )
            self.select_yaml_button.grid(row=1, column=2, padx=6, pady=6, sticky="w")

    class SDInteriorConfigFrame:
        """
        SD 内部設定フレーム
        """

        def __init__(self, owner: MainTab, init_configs: GUIConfigs):
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
                frame=self.sd_interior_config_frame,
                name="幅",
                row=1,
                col=0,
                width=5,
                default=str(init_configs.sd_width),
                sticky="w",
                on_change=owner.super_owner.super_owner.update_configs,
            )
            # テキストボックス(高さ)
            self.height_entry = put_textbox(
                frame=self.sd_interior_config_frame,
                name="高さ",
                row=1,
                col=2,
                width=5,
                default=str(init_configs.sd_height),
                sticky="w",
                on_change=owner.super_owner.super_owner.update_configs,
            )
            # テキストボックス(ステップ数)
            self.steps_entry = put_textbox(
                frame=self.sd_interior_config_frame,
                name="Steps",
                row=2,
                col=0,
                width=4,
                default=str(init_configs.sd_steps),
                sticky="w",
                on_change=owner.super_owner.super_owner.update_configs,
            )
            # テキストボックス(生成数)
            self.batch_size_entry = put_textbox(
                frame=self.sd_interior_config_frame,
                name="生成数",
                row=2,
                col=2,
                width=4,
                default=str(init_configs.sd_batch_size),
                sticky="w",
                on_change=owner.super_owner.super_owner.update_configs,
            )

    class SDExteriorConfigFrame:
        """
        SD 外部設定フレーム
        """

        def __init__(self, owner: MainTab, init_configs: GUIConfigs):
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
                frame=self.sd_exterior_config_frame,
                name="IPアドレス",
                row=0,
                col=0,
                width=16,
                default=init_configs.srv_ipaddr,
                sticky="w",
                on_change=owner.super_owner.super_owner.update_configs,
            )
            # テキストボックス(ポート)
            self.port_entry = put_textbox(
                frame=self.sd_exterior_config_frame,
                name="ポート",
                row=0,
                col=2,
                width=6,
                default=init_configs.srv_port,
                sticky="w",
                on_change=owner.super_owner.super_owner.update_configs,
            )

    class SellectFrame:
        """
        エンドポイント選択フレーム
        """

        def __init__(self, owner: MainTab, init_configs: GUIConfigs):
            self.super_owner = owner
            self.thread_sellect_frame = ttk.Frame(owner.main_frame)
            self.thread_sellect_frame.grid(row=3, column=0, sticky="w")

            # YAML 選択
            ttk.Label(self.thread_sellect_frame, text="選択中のYAML").grid(
                row=0, column=0, padx=6, pady=6, sticky="w"
            )
            self.yamlpath: Path | None = (
                Path(init_configs.yamlpath) if init_configs.yamlpath is not None else None
            )
            self.yamlpath_var = tkinter.StringVar(
                value=self.yamlpath.name
                if self.yamlpath is not None and self.yamlpath.exists()
                else "(未選択)"
            )
            ttk.Label(self.thread_sellect_frame, textvariable=self.yamlpath_var).grid(
                row=0, column=1, padx=6, pady=6, sticky="w"
            )

            # バックエンド
            ttk.Label(self.thread_sellect_frame, text="バックエンド").grid(
                row=1, column=0, padx=6, pady=6, sticky="w"
            )
            self.back_options = [BackEnd.a1111.value, BackEnd.comfy_ui.value]
            self.backend_var = tkinter.StringVar(value=self.back_options[0])
            self.backend_var.set(init_configs.backend)
            self.backend_combo = ttk.Combobox(
                self.thread_sellect_frame,
                textvariable=self.backend_var,
                values=self.back_options,
                state="readonly",
                width=10,
            )
            self.backend_combo.bind(
                "<<ComboboxSelected>>",
                lambda e: self.super_owner.super_owner.super_owner.on_switch_backend(),
            )
            self.backend_combo.grid(row=1, column=1, padx=6, pady=6, sticky="w")

    def __init__(self, owner: MainWindow, init_configs: GUIConfigs):
        """
        メインタブコンストラクタ

        Args:
            owner (ConfigWindow): ConfigWindow インスタンス
        """
        self.super_owner = owner

        self.main_frame = ttk.Frame(owner.main_tab)
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        self.button_frame = self.ButtonFrame(self)
        self.sd_interior_config_frame = self.SDInteriorConfigFrame(self, init_configs)
        self.sd_exterior_config_frame = self.SDExteriorConfigFrame(self, init_configs)
        self.sellect_frame = self.SellectFrame(self, init_configs)


class DebugTab:
    """
    デバッグタブ
    """

    class ExeDebugFrame:
        """
        デバッグ実行フレーム
        """

        def __init__(self, owner: DebugTab, init_configs: GUIConfigs):
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
                command=owner.super_owner.super_owner.on_debug,
            )
            self.debug_button.grid(row=0, column=0, padx=6, pady=6, sticky="w")
            # チェックボックス
            self.allow_edit_clipboard_check = tkinter.BooleanVar()
            ttk.Checkbutton(
                self.exe_debug_frame,
                text="クリップボードの更新",
                variable=self.allow_edit_clipboard_check,
                command=self.super_owner.super_owner.super_owner.update_configs,
            ).grid(row=0, column=1, padx=6, pady=6, sticky="w")
            self.allow_edit_clipboard_check.set(init_configs.allow_edit_clipboard)
            # ボタン(アーカイブ出力ダンプ)
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
                command=owner.super_owner.super_owner.on_dump_tasklist,
            )
            self.debug_button.grid(row=1, column=1, padx=6, pady=6, sticky="w")

    class VerboseFrame:
        """
        表示設定フレーム
        """

        def __init__(self, owner: DebugTab, init_configs: GUIConfigs):
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
                command=self.super_owner.super_owner.super_owner.update_configs,
            ).grid(row=0, column=0, padx=6, pady=6, sticky="w")
            self.verbose_clipboard_check.set(init_configs.print_new_clipboard)
            # プロンプト(データ)の表示
            self.verbose_prompt_set_check = tkinter.BooleanVar()
            ttk.Checkbutton(
                self.verbose_frame,
                text="プロンプト(データ)",
                variable=self.verbose_prompt_set_check,
                command=self.super_owner.super_owner.super_owner.update_configs,
            ).grid(row=0, column=1, padx=6, pady=6, sticky="w")
            self.verbose_prompt_set_check.set(init_configs.print_new_prompt_set)
            # プロンプト(文字列)の表示
            self.verbose_prompt_check = tkinter.BooleanVar()
            ttk.Checkbutton(
                self.verbose_frame,
                text="プロンプト(文字列)",
                variable=self.verbose_prompt_check,
                command=self.super_owner.super_owner.super_owner.update_configs,
            ).grid(row=1, column=0, padx=6, pady=6, sticky="w")
            self.verbose_prompt_check.set(init_configs.print_new_prompt)
            # 画像メタデータの表示
            self.verbose_picinfo_check = tkinter.BooleanVar()
            ttk.Checkbutton(
                self.verbose_frame,
                text="画像メタデータ",
                variable=self.verbose_picinfo_check,
                command=self.super_owner.super_owner.super_owner.update_configs,
            ).grid(row=1, column=1, padx=6, pady=6, sticky="w")
            self.verbose_picinfo_check.set(init_configs.print_picinfo)
            # イベントの表示
            self.verbose_event_check = tkinter.BooleanVar()
            ttk.Checkbutton(
                self.verbose_frame,
                text="イベント",
                variable=self.verbose_event_check,
                command=self.super_owner.super_owner.super_owner.update_configs,
            ).grid(row=2, column=0, padx=6, pady=6, sticky="w")
            self.verbose_event_check.set(init_configs.print_event)

    def __init__(self, owner: MainWindow, init_configs: GUIConfigs):
        """
        デバッグタブコンストラクタ

        Args:
            owner (ConfigWindow): ConfigWindow インスタンス
        """
        self.super_owner = owner

        self.main_frame = ttk.Frame(owner.debug_tab)
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        self.exe_debug_frame = self.ExeDebugFrame(self, init_configs)
        self.verbose_frame = self.VerboseFrame(self, init_configs)


class MainWindow:
    """
    メインウィンドウ(設定等)
    """

    def __init__(self, owner: Displayer, init_configs: GUIConfigs):
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
        self.main_tab_obj = MainTab(self, init_configs)
        # デバッグタブ
        self.debug_tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.debug_tab, text="デバッグ")
        self.debug_tab_obj = DebugTab(self, init_configs)

        # ウィジェット外のクリック時に常に FocusOut するよう変更
        def clear_selection(event):
            widget = event.widget
            if isinstance(widget, ttk.Entry):
                return
            owner.master.root.focus_set()

        self.main_tab.bind("<Button-1>", clear_selection, add="+")
        self.main_tab_obj.main_frame.bind("<Button-1>", clear_selection, add="+")
        self.main_tab_obj.button_frame.button_frame.bind("<Button-1>", clear_selection, add="+")
        self.main_tab_obj.sd_interior_config_frame.sd_interior_config_frame.bind(
            "<Button-1>", clear_selection, add="+"
        )
        self.main_tab_obj.sd_exterior_config_frame.sd_exterior_config_frame.bind(
            "<Button-1>", clear_selection, add="+"
        )
        self.main_tab_obj.sellect_frame.thread_sellect_frame.bind(
            "<Button-1>", clear_selection, add="+"
        )


class Displayer:
    """
    GUI 管理クラス
    """

    def __init__(
        self,
        master: MasterIF,
        to_master: BottleMail[master.events.DisplayerEvent],
        init_configs: GUIConfigs,
    ):
        """
        コンストラクタ

        Args:
            master (MasterIF): Master インターフェース
        """
        self.master = master
        self.to_master = to_master

        self.main_window = MainWindow(self, init_configs)
        self.info_window = InfoWindow(self)
        self.info_window.construct(fix_position=True)
        self.pic_window = PicWindow(self)
        self.switch_output_button_state(False)

        self.update_configs()

        self.last_picstats: PicStats | NoImageStats = None
        self.last_task: TaskBlueprint = None

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
        self.last_picstats = picstats
        if picstats is not NoImageStats:
            self.pic_window.update(picstats.path)
            self.switch_output_button_state(True)
        else:
            self.pic_window.update()
            self.switch_output_button_state(False)

        self.info_window.update_picinfo_tab(picstats)

    def switch_output_button_state(self, toggle: bool) -> None:
        """
        表示ボタンの有効/無効(グレーアウト)を切り替える

        Args:
            toggle (bool): True で有効, False で無効
        """
        if not self.exists():
            return

        output_button = self.main_window.main_tab_obj.button_frame.output_button
        if toggle:
            if str(output_button.cget("state")) == "disabled":
                output_button.configure(state="normal")
        else:
            if str(output_button.cget("state")) == "normal":
                output_button.configure(state="disabled")

    def on_repeat_task(self) -> None:
        """
        再実行ボタンハンドラ
        """
        self.to_master.enclose(master.events.OnRepeatTask())

    def on_interrput_task(self) -> None:
        """
        中断ボタンハンドラ
        """
        self.to_master.enclose(master.events.OnInterruptTask())

    def on_flush_tasks(self) -> None:
        """
        タスククリアボタンハンドラ
        """
        self.to_master.enclose(master.events.OnFlushTasks())

    def on_open_pic_window(self) -> None:
        """
        表示ボタンハンドラ\n
        表示すべき画像がないときは何もしない
        """
        if self.pic_window is not None and self.pic_window.existed():
            self.pic_window.pic_window.deiconify()
            self.pic_window.pic_window.lift()
        else:
            self.pic_window.construct(fix_position=True)

        self.update_pic_window(self.last_picstats)

    def on_open_info_window(self) -> None:
        """
        情報ウィンドウの表示ハンドラ\n
        すでに開いている場合は最前面に表示のみ行う\n
        情報の更新も直後に行う
        """
        if self.info_window is not None and self.info_window.existed():
            self.info_window.info_window.deiconify()
            self.info_window.info_window.lift()
        else:
            self.info_window.construct(fix_position=True)

        self.info_window.update_taskinfo_tab(task=self.last_task)
        self.info_window.update_picinfo_tab(self.last_picstats)

    def on_select_yaml(self) -> None:
        """
        YAML選択ボタンハンドラ
        """
        path = filedialog.askopenfilename(title="YAML選択", filetypes=[("YAML", "*.yaml")])
        if not path:
            return

        self.main_window.main_tab_obj.sellect_frame.yamlpath = Path(path)
        self.main_window.main_tab_obj.sellect_frame.yamlpath_var.set(Path(path).name)
        self.to_master.enclose(master.events.OnSelectYaml(path=path))
        self.update_configs()

    def on_debug(self) -> None:
        """
        デバッグボタンハンドラ
        """
        self.to_master.enclose(master.events.OnDebug())

    def on_dump_archiver(self) -> None:
        """
        Archiver ダンプボタンハンドラ
        """
        self.to_master.enclose(master.events.OnDumpArchiver())

    def on_dump_tasklist(self) -> None:
        """
        タスクリストダンプボタンハンドラ
        """
        self.to_master.enclose(master.events.OnDumpTaskList())

    def on_backward(self) -> None:
        """
        < ボタンハンドラ
        """
        self.to_master.enclose(master.events.OnBackward())

    def on_forward(self) -> None:
        """
        > ボタンハンドラ
        """
        self.to_master.enclose(master.events.OnForward())

    def on_upscale(self) -> None:
        """
        アップスケール予約ボタンハンドラ
        """
        self.to_master.enclose(master.events.OnUpscale())

    def on_delete(self) -> None:
        """
        削除ボタンハンドラ
        """
        self.to_master.enclose(master.events.OnDelete())

    def on_switch_backend(self) -> None:
        """
        バックエンド変更を Master に通知する
        """
        self.update_configs()
        self.to_master.enclose(
            master.events.OnSwitchBackend(
                new_backend=BackEnd.a1111
                if self.crnt_configs.backend == BackEnd.a1111.value
                else BackEnd.comfy_ui
            )
        )

    def update_configs(self) -> None:
        """
        GUI 上の設定値を Master に通知する
        """
        self.to_master.enclose(master.events.OnChangeConfig(new_config=self.crnt_configs))

    @property
    def crnt_configs(self) -> GUIConfigs:
        """
        GUI 上の設定値

        Returns:
            GUIConfigs: GUI 上の設定値
        """
        return GUIConfigs(
            srv_ipaddr=self.main_window.main_tab_obj.sd_exterior_config_frame.ipaddr_entry.get(),
            srv_port=self.main_window.main_tab_obj.sd_exterior_config_frame.port_entry.get(),
            sd_steps=int(self.main_window.main_tab_obj.sd_interior_config_frame.steps_entry.get()),
            sd_batch_size=int(
                self.main_window.main_tab_obj.sd_interior_config_frame.batch_size_entry.get()
            ),
            sd_width=int(self.main_window.main_tab_obj.sd_interior_config_frame.width_entry.get()),
            sd_height=int(
                self.main_window.main_tab_obj.sd_interior_config_frame.height_entry.get()
            ),
            yamlpath=str(self.main_window.main_tab_obj.sellect_frame.yamlpath)
            if self.main_window.main_tab_obj.sellect_frame.yamlpath is not None
            else None,
            backend=self.main_window.main_tab_obj.sellect_frame.backend_combo.get(),
            allow_edit_clipboard=bool(
                self.main_window.debug_tab_obj.exe_debug_frame.allow_edit_clipboard_check.get()
            ),
            print_new_clipboard=bool(
                self.main_window.debug_tab_obj.verbose_frame.verbose_clipboard_check.get()
            ),
            print_new_prompt_set=bool(
                self.main_window.debug_tab_obj.verbose_frame.verbose_prompt_set_check.get()
            ),
            print_new_prompt=bool(
                self.main_window.debug_tab_obj.verbose_frame.verbose_prompt_check.get()
            ),
            print_picinfo=bool(
                self.main_window.debug_tab_obj.verbose_frame.verbose_picinfo_check.get()
            ),
            print_event=bool(
                self.main_window.debug_tab_obj.verbose_frame.verbose_event_check.get()
            ),
        )

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
