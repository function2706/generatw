"""
GUI 管理クラス
"""

from __future__ import annotations

import tkinter
from pathlib import Path
from tkinter import TclError, filedialog, ttk

import master.events
from archiver.dataclasses import NoImageStats, PicStats
from common.functions import BottleMail
from displayer import theme, widgets
from displayer.dataclasses import GUIConfigs
from displayer.info_window import InfoWindow
from displayer.pic_window import PicWindow
from displayer.theme import STYLES
from displayer.widgets import action_button, carded_section, field_entry, field_value
from displayer.workflow_tab import WorkFlowTab
from generator.dataclasses import TaskBlueprint
from master.interfaces import BackEnd, MasterIF

# テーマ選択コンボの表示ラベル <-> 設定値
THEME_LABELS: dict[str, str] = {"自動": "auto", "ライト": "light", "ダーク": "dark"}
THEME_PREFS: dict[str, str] = {v: k for k, v in THEME_LABELS.items()}


class MainTab:
    """
    メインタブ (操作・生成設定・入力/バックエンド・記憶)
    """

    def __init__(self, owner: MainWindow, init_configs: GUIConfigs):
        """
        コンストラクタ

        Args:
            owner (MainWindow): MainWindow インスタンス
            init_configs (GUIConfigs): 初期設定値
        """
        self.super_owner = owner
        self.displayer = owner.super_owner

        self.main_frame = ttk.Frame(owner.main_tab)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.columnconfigure(0, weight=1)

        self._build_operation(0)
        self._build_sd_config(1, init_configs)
        self._build_source(2, init_configs)
        self._build_memory(3, init_configs)

    def _build_operation(self, row: int) -> None:
        """
        操作カード (タスク / 表示 / キュークリア / 記憶) を構築する
        """
        card = carded_section(self.main_frame, "操作", row, pady=(4, 2))
        d = self.displayer

        w = 8  # ボタン幅を揃える

        ttk.Label(card, text="タスク", style=STYLES.muted).grid(row=0, column=0, sticky="w", pady=3)
        action_button(card, "再実行", d.on_repeat_task, accent=True, width=w, row=0, column=1)
        action_button(card, "中断", d.on_interrput_task, width=w, row=0, column=2)

        ttk.Label(card, text="表示", style=STYLES.muted).grid(row=1, column=0, sticky="w", pady=3)
        self.output_button = action_button(
            card, "画像", d.on_open_pic_window, width=w, row=1, column=1
        )
        action_button(card, "情報", d.on_open_info_window, width=w, row=1, column=2)

        ttk.Label(card, text="キュークリア", style=STYLES.muted).grid(
            row=2, column=0, sticky="w", pady=3
        )
        action_button(card, "全タスク", d.on_flush_tasks, width=w, row=2, column=1)
        action_button(card, "生成タスク", d.on_flush_txt2img_tasks, width=w, row=2, column=2)
        action_button(card, "拡大タスク", d.on_flush_img2img_tasks, width=w, row=2, column=3)

        ttk.Label(card, text="記憶", style=STYLES.muted).grid(row=3, column=0, sticky="w", pady=3)
        action_button(card, "保存", d.on_save_memory, width=w, row=3, column=1)
        action_button(card, "復元", d.on_load_memory, width=w, row=3, column=2)
        action_button(card, "忘却", d.on_forget_memory, width=w, row=3, column=3)

    def _build_sd_config(self, row: int, cfg: GUIConfigs) -> None:
        """
        生成設定カード (寸法・ステップ・接続先・上限) を構築する
        """
        card = carded_section(self.main_frame, "生成設定", row)
        on_change = self.displayer.update_configs

        self.width_entry = field_entry(card, "幅", 0, 0, 6, str(cfg.sd_width), on_change)
        self.height_entry = field_entry(card, "高さ", 0, 2, 6, str(cfg.sd_height), on_change)
        self.scaleby_entry = field_entry(card, "倍率", 0, 4, 5, str(cfg.sd_scaleby), on_change)
        self.steps_entry = field_entry(card, "ステップ数", 1, 0, 6, str(cfg.sd_steps), on_change)
        self.batch_size_entry = field_entry(
            card, "生成数", 1, 2, 6, str(cfg.sd_batch_size), on_change
        )

        ttk.Separator(card, orient="horizontal").grid(
            row=2, column=0, columnspan=6, sticky="ew", pady=8
        )

        self.ipaddr_entry = field_entry(card, "IPアドレス", 3, 0, 16, cfg.srv_ipaddr, on_change)
        self.port_entry = field_entry(card, "ポート", 3, 2, 8, cfg.srv_port, on_change)

        self.each_max_pics_entry = field_entry(
            card, "生成上限/プロンプト", 4, 0, 6, str(cfg.each_max_pics), on_change
        )
        self.rest_capacity = field_value(card, "残り容量(枚)", 4, 2, "-")

    def _build_source(self, row: int, cfg: GUIConfigs) -> None:
        """
        入力 / バックエンドカードを構築する
        """
        card = carded_section(self.main_frame, "入力 / バックエンド", row)
        card.columnconfigure(1, weight=1)

        ttk.Label(card, text="選択中の YAML", style=STYLES.muted).grid(
            row=0, column=0, padx=(0, 6), pady=5, sticky="e"
        )
        self.yamlpath: Path | None = Path(cfg.yamlpath) if cfg.yamlpath is not None else None
        self.yamlpath_var = tkinter.StringVar(
            value=self.yamlpath.name
            if self.yamlpath is not None and self.yamlpath.exists()
            else "(未選択)"
        )
        ttk.Label(card, textvariable=self.yamlpath_var, style=STYLES.value).grid(
            row=0, column=1, pady=5, sticky="w"
        )
        btns = ttk.Frame(card, style=STYLES.surface)
        btns.grid(row=0, column=2, sticky="e")
        action_button(btns, "YAML選択", self.displayer.on_select_yaml, row=0, column=0)
        action_button(btns, "再読み込み", self.displayer.on_reload_yaml, row=0, column=1)

        ttk.Label(card, text="バックエンド", style=STYLES.muted).grid(
            row=1, column=0, padx=(0, 6), pady=5, sticky="e"
        )
        self.back_options = [BackEnd.a1111.value, BackEnd.comfy_ui.value]
        self.backend_var = tkinter.StringVar(value=cfg.backend or self.back_options[0])
        self.backend_combo = ttk.Combobox(
            card,
            textvariable=self.backend_var,
            values=self.back_options,
            state="readonly",
            width=12,
        )
        self.backend_combo.bind(
            "<<ComboboxSelected>>", lambda e: self.displayer.on_switch_backend()
        )
        self.backend_combo.grid(row=1, column=1, pady=5, sticky="w")

    def _build_memory(self, row: int, cfg: GUIConfigs) -> None:
        """
        記憶トグルカードを構築する
        """
        card = carded_section(self.main_frame, "起動時の記憶", row)
        on_change = self.displayer.update_configs

        self.save_memory_end_check = tkinter.BooleanVar(value=cfg.save_memory_end)
        ttk.Checkbutton(
            card, text="終了時に保存", variable=self.save_memory_end_check, command=on_change
        ).grid(row=0, column=0, padx=(0, 16), pady=3, sticky="w")

        self.load_memory_start_check = tkinter.BooleanVar(value=cfg.load_memory_start)
        ttk.Checkbutton(
            card, text="開始時に復元", variable=self.load_memory_start_check, command=on_change
        ).grid(row=0, column=1, pady=3, sticky="w")


class DebugTab:
    """
    デバッグタブ (操作と出力 / 動作トグル / 表示トグル)
    """

    def __init__(self, owner: MainWindow, init_configs: GUIConfigs):
        """
        コンストラクタ

        Args:
            owner (MainWindow): MainWindow インスタンス
            init_configs (GUIConfigs): 初期設定値
        """
        self.super_owner = owner
        self.displayer = owner.super_owner

        self.main_frame = ttk.Frame(owner.debug_tab)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.columnconfigure(0, weight=1)

        self._build_exec(0)
        self._build_toggles(1, init_configs)
        self._build_verbose(2, init_configs)

    def _build_exec(self, row: int) -> None:
        """
        操作と出力カードを構築する
        """
        card = carded_section(self.main_frame, "操作と出力", row, pady=(4, 2))
        d = self.displayer
        action_button(card, "デバッグ", d.on_debug, accent=True, row=0, column=0)
        action_button(card, "アーカイブ出力", d.on_dump_archiver, row=1, column=0, padx=(3, 12))
        action_button(card, "タスクリスト", d.on_dump_tasklist, row=1, column=1)
        action_button(card, "現在の記憶", d.on_dump_memory, row=1, column=2)

    def _build_toggles(self, row: int, cfg: GUIConfigs) -> None:
        """
        動作トグルカードを構築する
        """
        card = carded_section(self.main_frame, "動作トグル", row)
        on_change = self.displayer.update_configs

        self.allow_edit_clipboard_check = tkinter.BooleanVar(value=cfg.allow_edit_clipboard)
        ttk.Checkbutton(
            card, text="クリップボードの更新", variable=self.allow_edit_clipboard_check,
            command=on_change,
        ).grid(row=0, column=0, padx=(0, 16), pady=3, sticky="w")

        self.log_parser_reports_check = tkinter.BooleanVar(value=cfg.log_parser_reports)
        ttk.Checkbutton(
            card, text="Parser レポートのロギング", variable=self.log_parser_reports_check,
            command=on_change,
        ).grid(row=0, column=1, pady=3, sticky="w")

    def _build_verbose(self, row: int, cfg: GUIConfigs) -> None:
        """
        表示トグルカードを構築する
        """
        card = carded_section(self.main_frame, "表示トグル", row)
        on_change = self.displayer.update_configs

        # (属性名, ラベル, 初期値)
        specs = [
            ("verbose_clipboard_check", "クリップボードを表示", cfg.print_new_clipboard),
            ("verbose_prompt_set_check", "プロンプト(データ)を表示", cfg.print_new_prompt_set),
            ("verbose_prompt_check", "プロンプト(文字列)を表示", cfg.print_new_prompt),
            ("verbose_picinfo_check", "画像メタデータを表示", cfg.print_picinfo),
            ("verbose_event_check", "イベントを表示", cfg.print_event),
            ("verbose_parser_reports_check", "Parser レポートを表示", cfg.print_parser_reports),
        ]
        for idx, (attr, label, init) in enumerate(specs):
            var = tkinter.BooleanVar(value=init)
            setattr(self, attr, var)
            ttk.Checkbutton(card, text=label, variable=var, command=on_change).grid(
                row=idx // 2, column=idx % 2, padx=(0, 16), pady=3, sticky="w"
            )


class MainWindow:
    """
    メインウィンドウ (設定等)
    """

    def __init__(self, owner: Displayer, init_configs: GUIConfigs):
        """
        コンストラクタ

        Args:
            owner (Displayer): Displayer インスタンス
            init_configs (GUIConfigs): 初期設定値
        """
        self.super_owner = owner
        root = owner.master.root

        # テーマ適用 (ウィジェット構築前)
        theme.apply(root, init_configs.theme)

        root.title("picmaker")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)
        root.protocol("WM_DELETE_WINDOW", owner.destroy)

        self._build_toolbar(root, init_configs)

        # Notebook (タブ)
        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self.main_tab = ttk.Frame(self.notebook, padding=12)
        self.main_tab.columnconfigure(0, weight=1)
        self.notebook.add(self.main_tab, text="メイン")
        self.main_tab_obj = MainTab(self, init_configs)

        self.workflow_tab = ttk.Frame(self.notebook, padding=12)
        self.workflow_tab.columnconfigure(0, weight=1)
        self.workflow_tab.rowconfigure(0, weight=1)
        self.notebook.add(self.workflow_tab, text="ワークフロー")
        self.workflow_tab_obj = WorkFlowTab(self, init_configs)

        self.debug_tab = ttk.Frame(self.notebook, padding=12)
        self.debug_tab.columnconfigure(0, weight=1)
        self.notebook.add(self.debug_tab, text="デバッグ")
        self.debug_tab_obj = DebugTab(self, init_configs)

        # 入力欄以外クリックでフォーカスを外す
        widgets.bind_focus_clear(self.main_tab, root)
        widgets.bind_focus_clear(self.debug_tab, root)

    def _build_toolbar(self, root: tkinter.Misc, init_configs: GUIConfigs) -> None:
        """
        上部ツールバー (タイトル + テーマ選択) を構築する
        """
        bar = ttk.Frame(root, padding=(12, 10, 12, 6))
        bar.grid(row=0, column=0, sticky="ew")
        bar.columnconfigure(1, weight=1)

        ttk.Label(bar, text="picmaker", style=STYLES.title).grid(row=0, column=0, sticky="w")

        ttk.Label(bar, text="テーマ", style=STYLES.section).grid(row=0, column=2, padx=(0, 6))
        self.theme_var = tkinter.StringVar(value=THEME_PREFS.get(init_configs.theme, "自動"))
        combo = ttk.Combobox(
            bar,
            textvariable=self.theme_var,
            values=list(THEME_LABELS.keys()),
            state="readonly",
            width=8,
        )
        combo.grid(row=0, column=3, sticky="e")
        combo.bind("<<ComboboxSelected>>", lambda e: self.super_owner.on_change_theme())

    @property
    def theme_pref(self) -> str:
        """
        現在選択中のテーマ設定値 ("auto" / "light" / "dark")
        """
        return THEME_LABELS.get(self.theme_var.get(), "auto")


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
            to_master (BottleMail): Master へのイベント送出口
            init_configs (GUIConfigs): 初期設定値
        """
        self.master = master
        self.to_master = to_master

        # MainWindow 構築中に参照され得るため先に初期化しておく
        self.last_picstats: PicStats | NoImageStats = None
        self.last_task: TaskBlueprint = None

        self.main_window = MainWindow(self, init_configs)
        self.info_window = InfoWindow(self)
        self.info_window.construct(fix_position=True)
        self.pic_window = PicWindow(self)
        self.switch_output_button_state(False)

        self.update_configs()

    # -------------------------------------------------------------------------
    # ライフサイクル
    # -------------------------------------------------------------------------

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

    def destroy(self) -> None:
        """
        設定ウィンドウのクローズ時のハンドラ
        """
        self.pic_window.destroy()
        self.info_window.destroy()
        if self.exists():
            self.master.root.destroy()

    # -------------------------------------------------------------------------
    # 更新
    # -------------------------------------------------------------------------

    def update_main_window(self, rest_capacity: int | None) -> None:
        """
        メインウィンドウを更新する\n
        None が指定されている場合は N/A 相当の表示を行う

        Args:
            rest_capacity (int | None): 現在のディレクトリの残り容量
        """
        from displayer.info_window import Consts

        self.main_window.main_tab_obj.rest_capacity.set(
            rest_capacity if rest_capacity is not None else Consts.not_available_text
        )

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

        state = "normal" if toggle else "disabled"
        self.main_window.main_tab_obj.output_button.configure(state=state)

    # -------------------------------------------------------------------------
    # テーマ
    # -------------------------------------------------------------------------

    def on_change_theme(self) -> None:
        """
        テーマ選択変更ハンドラ\n
        ttk スタイルを再適用し, 非 ttk 領域も追従させる
        """
        theme.apply(self.master.root, self.main_window.theme_pref)
        widgets.apply_toplevel_bg(self.master.root)
        if self.info_window.existed():
            widgets.apply_toplevel_bg(self.info_window.info_window)
        if self.pic_window.existed():
            widgets.apply_toplevel_bg(self.pic_window.pic_window)
            self.pic_window.retheme()
        self.main_window.workflow_tab_obj.retheme()
        self.update_configs()

    # -------------------------------------------------------------------------
    # ボタンハンドラ (Master へイベント送出)
    # -------------------------------------------------------------------------

    def on_repeat_task(self) -> None:
        """再実行ボタンハンドラ"""
        self.to_master.enclose(master.events.OnRepeatTask())

    def on_interrput_task(self) -> None:
        """中断ボタンハンドラ"""
        self.to_master.enclose(master.events.OnInterruptTask())

    def on_flush_tasks(self) -> None:
        """全タスククリアボタンハンドラ"""
        self.to_master.enclose(master.events.OnFlushTasks())

    def on_flush_txt2img_tasks(self) -> None:
        """生成タスククリアボタンハンドラ"""
        self.to_master.enclose(master.events.OnFlushTxt2ImgTasks())

    def on_flush_img2img_tasks(self) -> None:
        """拡大タスククリアボタンハンドラ"""
        self.to_master.enclose(master.events.OnFlushImg2ImgTasks())

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

    def on_save_memory(self) -> None:
        """記憶保存ハンドラ"""
        self.to_master.enclose(master.events.OnSaveMemory())

    def on_load_memory(self) -> None:
        """記憶復元ハンドラ"""
        self.to_master.enclose(master.events.OnLoadMemory())

    def on_forget_memory(self) -> None:
        """記憶忘却ハンドラ"""
        self.to_master.enclose(master.events.OnForgetMemory())

    def on_select_yaml(self) -> None:
        """YAML選択ボタンハンドラ"""
        path = filedialog.askopenfilename(title="YAML選択", filetypes=[("YAML", "*.yaml")])
        if not path:
            return

        self.main_window.main_tab_obj.yamlpath = Path(path)
        self.main_window.main_tab_obj.yamlpath_var.set(Path(path).name)
        self.to_master.enclose(master.events.OnSelectYaml(path=path))
        self.update_configs()

    def on_reload_yaml(self) -> None:
        """YAML 再読み込みボタンハンドラ"""
        self.to_master.enclose(master.events.OnReloadYaml())

    def on_debug(self) -> None:
        """デバッグボタンハンドラ"""
        self.to_master.enclose(master.events.OnDebug())

    def on_dump_archiver(self) -> None:
        """Archiver ダンプボタンハンドラ"""
        self.to_master.enclose(master.events.OnDumpArchiver())

    def on_dump_tasklist(self) -> None:
        """タスクリストダンプボタンハンドラ"""
        self.to_master.enclose(master.events.OnDumpTaskList())

    def on_dump_memory(self) -> None:
        """現在の記憶ダンプボタンハンドラ"""
        self.to_master.enclose(master.events.OnDumpMemory())

    def on_backward(self) -> None:
        """< ボタンハンドラ"""
        self.to_master.enclose(master.events.OnBackward())

    def on_forward(self) -> None:
        """> ボタンハンドラ"""
        self.to_master.enclose(master.events.OnForward())

    def on_upscale(self) -> None:
        """アップスケール予約ボタンハンドラ"""
        self.to_master.enclose(master.events.OnUpscale())

    def on_delete(self) -> None:
        """削除ボタンハンドラ"""
        self.to_master.enclose(master.events.OnDelete())

    def on_switch_backend(self) -> None:
        """バックエンド変更を Master に通知する"""
        self.update_configs()
        self.to_master.enclose(
            master.events.OnSwitchBackend(
                new_backend=BackEnd.a1111
                if self.crnt_configs.backend == BackEnd.a1111.value
                else BackEnd.comfy_ui
            )
        )

    def update_configs(self) -> None:
        """GUI 上の設定値を Master に通知する"""
        self.to_master.enclose(master.events.OnChangeConfig(new_config=self.crnt_configs))

    # -------------------------------------------------------------------------
    # 設定値 / 座標
    # -------------------------------------------------------------------------

    @property
    def crnt_configs(self) -> GUIConfigs:
        """
        GUI 上の設定値

        Returns:
            GUIConfigs: GUI 上の設定値
        """
        main = self.main_window.main_tab_obj
        debug = self.main_window.debug_tab_obj
        return GUIConfigs(
            srv_ipaddr=main.ipaddr_entry.get(),
            srv_port=main.port_entry.get(),
            sd_steps=int(main.steps_entry.get()),
            sd_batch_size=int(main.batch_size_entry.get()),
            sd_width=int(main.width_entry.get()),
            sd_height=int(main.height_entry.get()),
            sd_scaleby=float(main.scaleby_entry.get()),
            each_max_pics=int(main.each_max_pics_entry.get()),
            yamlpath=str(main.yamlpath) if main.yamlpath is not None else None,
            wf_yamlpath=str(self.main_window.workflow_tab_obj.wf_yamlpath),
            backend=main.backend_combo.get(),
            theme=self.main_window.theme_pref,
            allow_edit_clipboard=bool(debug.allow_edit_clipboard_check.get()),
            log_parser_reports=bool(debug.log_parser_reports_check.get()),
            save_memory_end=bool(main.save_memory_end_check.get()),
            load_memory_start=bool(main.load_memory_start_check.get()),
            print_new_clipboard=bool(debug.verbose_clipboard_check.get()),
            print_new_prompt_set=bool(debug.verbose_prompt_set_check.get()),
            print_new_prompt=bool(debug.verbose_prompt_check.get()),
            print_picinfo=bool(debug.verbose_picinfo_check.get()),
            print_parser_reports=bool(debug.verbose_parser_reports_check.get()),
            print_event=bool(debug.verbose_event_check.get()),
        )

    @property
    def config_window_x(self) -> int:
        """設定ウィンドウの x 座標"""
        self.master.root.update_idletasks()
        return self.master.root.winfo_x()

    @property
    def config_window_y(self) -> int:
        """設定ウィンドウの y 座標"""
        self.master.root.update_idletasks()
        return self.master.root.winfo_y()

    @property
    def config_window_width(self) -> int:
        """設定ウィンドウの幅"""
        self.master.root.update_idletasks()
        return self.master.root.winfo_width()

    @property
    def config_window_height(self) -> int:
        """設定ウィンドウの高さ"""
        self.master.root.update_idletasks()
        return self.master.root.winfo_height()
