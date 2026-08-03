"""
GUI 管理クラス
"""

from __future__ import annotations

import tkinter
from tkinter import Frame, TclError, ttk

import master.events
from archiver.dataclasses import NoImageStats, PicStats
from character.manager import CharacterMeta
from character.models import ENUM, SCALAR, WARDROBE, ActionSet, CharacterSheet
from character.state import CharacterState
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
    返り値は更新可能な文字列ベースのオブジェクト
    """
    ttk.Label(frame, text=name).grid(row=row, column=col, sticky=sticky)
    strvar = tkinter.StringVar(value=default)
    ttk.Label(frame, textvariable=strvar).grid(row=row, column=(col + 1), sticky=sticky)
    return strvar


class HorizontalSeparator:
    """
    ラベル付き区切り線
    """

    def __init__(self, frame: ttk.Frame, row: int, column: int, name: str):
        self.local_frame = ttk.Frame(frame)
        self.local_frame.grid(row=row, column=column, sticky="ew")
        self.local_frame.columnconfigure(0, weight=1)
        self.local_frame.columnconfigure(2, weight=16)

        ttk.Separator(self.local_frame, orient="horizontal").grid(
            row=1, column=0, sticky="ew", padx=(0, 10)
        )
        ttk.Label(self.local_frame, text=name).grid(row=1, column=1)
        ttk.Separator(self.local_frame, orient="horizontal").grid(
            row=1, column=2, sticky="ew", padx=(10, 0)
        )


class MainTab:
    """
    交流タブ (キャラ選択 / 状態 / アクション / セリフ / 表示操作)
    """

    def __init__(self, owner: MainWindow, init_configs: GUIConfigs):
        self.super_owner = owner
        self.displayer: Displayer = owner.super_owner

        self.main_frame = ttk.Frame(owner.main_tab)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.columnconfigure(0, weight=1)

        # 動的 UI が参照する状態
        self.char_metas: list[CharacterMeta] = []
        self.actions: ActionSet | None = None
        self.action_kinds: dict[str, str] = {}
        self.param_widgets: dict[str, tuple[str, object, tkinter.StringVar]] = {}
        self.wardrobe_keys: list[str] = []

        HorizontalSeparator(self.main_frame, 0, 0, "キャラクター")
        self._build_character_frame(1)
        HorizontalSeparator(self.main_frame, 2, 0, "状態")
        self.param_frame = ttk.Frame(self.main_frame)
        self.param_frame.grid(row=3, column=0, sticky="ew", padx=6, pady=2)
        HorizontalSeparator(self.main_frame, 4, 0, "アクション")
        self.action_frame = ttk.Frame(self.main_frame)
        self.action_frame.grid(row=5, column=0, sticky="ew", padx=6, pady=2)
        self._build_wardrobe_frame(6)
        HorizontalSeparator(self.main_frame, 7, 0, "セリフ")
        self._build_dialogue_frame(8)
        HorizontalSeparator(self.main_frame, 9, 0, "表示・タスク")
        self._build_op_frame(10)

    # -- 静的フレーム ------------------------------------------------------ #
    def _build_character_frame(self, row: int) -> None:
        frame = ttk.Frame(self.main_frame)
        frame.grid(row=row, column=0, sticky="w")

        ttk.Label(frame, text="キャラ").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.character_var = tkinter.StringVar()
        self.character_combo = ttk.Combobox(
            frame, textvariable=self.character_var, values=[], state="readonly", width=20
        )
        self.character_combo.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        self.character_combo.bind(
            "<<ComboboxSelected>>", lambda e: self.displayer.on_select_character()
        )
        ttk.Button(frame, text="再読み込み", command=self.displayer.on_reload_character).grid(
            row=0, column=2, padx=6, pady=6, sticky="w"
        )

    def _build_wardrobe_frame(self, row: int) -> None:
        frame = ttk.Frame(self.main_frame)
        frame.grid(row=row, column=0, sticky="w")

        ttk.Label(frame, text="衣装").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.wardrobe_var = tkinter.StringVar()
        self.wardrobe_combo = ttk.Combobox(
            frame, textvariable=self.wardrobe_var, values=[], state="disabled", width=18
        )
        self.wardrobe_combo.grid(row=0, column=1, padx=6, pady=6, sticky="w")

    def _build_dialogue_frame(self, row: int) -> None:
        frame = ttk.Frame(self.main_frame)
        frame.grid(row=row, column=0, sticky="ew", padx=6)
        frame.columnconfigure(0, weight=1)

        self.dialogue_name_var = tkinter.StringVar(value="")
        ttk.Label(frame, textvariable=self.dialogue_name_var, font=("", 9, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        self.dialogue_text = tkinter.Text(frame, height=3, wrap="word", state="disabled")
        self.dialogue_text.grid(row=1, column=0, sticky="ew", pady=(2, 4))

    def _build_op_frame(self, row: int) -> None:
        frame = ttk.Frame(self.main_frame)
        frame.grid(row=row, column=0, sticky="w")
        d = self.displayer

        ttk.Label(frame, text="表示").grid(row=0, column=0, padx=6, pady=4, sticky="w")
        self.output_button = ttk.Button(frame, text="画像", command=d.on_open_pic_window)
        self.output_button.grid(row=0, column=1, padx=4, pady=4, sticky="w")
        ttk.Button(frame, text="情報", command=d.on_open_info_window).grid(
            row=0, column=2, padx=4, pady=4, sticky="w"
        )
        ttk.Button(frame, text="再生成", command=d.on_repeat_task).grid(
            row=0, column=3, padx=4, pady=4, sticky="w"
        )
        ttk.Button(frame, text="中断", command=d.on_interrput_task).grid(
            row=0, column=4, padx=4, pady=4, sticky="w"
        )

        ttk.Label(frame, text="キュー").grid(row=1, column=0, padx=6, pady=4, sticky="w")
        ttk.Button(frame, text="全タスク", command=d.on_flush_tasks).grid(
            row=1, column=1, padx=4, pady=4, sticky="w"
        )
        ttk.Button(frame, text="生成", command=d.on_flush_txt2img_tasks).grid(
            row=1, column=2, padx=4, pady=4, sticky="w"
        )
        ttk.Button(frame, text="拡大", command=d.on_flush_img2img_tasks).grid(
            row=1, column=3, padx=4, pady=4, sticky="w"
        )

        ttk.Label(frame, text="状態").grid(row=2, column=0, padx=6, pady=4, sticky="w")
        ttk.Button(frame, text="保存", command=d.on_save_state).grid(
            row=2, column=1, padx=4, pady=4, sticky="w"
        )
        ttk.Button(frame, text="復元", command=d.on_load_state).grid(
            row=2, column=2, padx=4, pady=4, sticky="w"
        )
        ttk.Button(frame, text="リセット", command=d.on_reset_state).grid(
            row=2, column=3, padx=4, pady=4, sticky="w"
        )

    # -- 動的レンダリング -------------------------------------------------- #
    def set_character_list(self, metas: list[CharacterMeta], current: str | None) -> None:
        """キャラ選択コンボボックスを更新する"""
        self.char_metas = list(metas)
        self.character_combo["values"] = [m.display_name for m in self.char_metas]
        if current is not None:
            for i, m in enumerate(self.char_metas):
                if m.char_id == current:
                    self.character_combo.current(i)
                    break

    @property
    def selected_char_id(self) -> str | None:
        idx = self.character_combo.current()
        if idx is None or idx < 0 or idx >= len(self.char_metas):
            return None
        return self.char_metas[idx].char_id

    def render_character(
        self, sheet: CharacterSheet, actions: ActionSet, state: CharacterState
    ) -> None:
        """
        選択キャラに合わせてパラメータ表示・アクションボタン・衣装候補を再構築する
        """
        self.actions = actions
        self.action_kinds = {a.action_id: a.kind for a in actions.actions}

        self._render_params(sheet, state)
        self._render_actions(actions)
        self._render_wardrobe(sheet, state)

    def _render_params(self, sheet: CharacterSheet, state: CharacterState) -> None:
        for child in self.param_frame.winfo_children():
            child.destroy()
        self.param_widgets = {}

        for i, (name, pdef) in enumerate(sheet.parameters.items()):
            ttk.Label(self.param_frame, text=pdef.label).grid(
                row=i, column=0, padx=6, pady=3, sticky="w"
            )
            value_var = tkinter.StringVar()
            if pdef.kind == SCALAR:
                span = max(1.0, pdef.maxv - pdef.minv)
                bar = ttk.Progressbar(
                    self.param_frame, orient="horizontal", length=180, maximum=span
                )
                bar.grid(row=i, column=1, padx=6, pady=3, sticky="w")
                ttk.Label(self.param_frame, textvariable=value_var).grid(
                    row=i, column=2, padx=6, pady=3, sticky="w"
                )
                self.param_widgets[name] = (SCALAR, bar, value_var)
            else:
                ttk.Label(self.param_frame, textvariable=value_var).grid(
                    row=i, column=1, padx=6, pady=3, sticky="w"
                )
                self.param_widgets[name] = (ENUM, None, value_var)

        self.update_state_view(sheet, state)

    def _render_actions(self, actions: ActionSet) -> None:
        for child in self.action_frame.winfo_children():
            child.destroy()

        per_row = 4
        for i, action in enumerate(actions.actions):
            ttk.Button(
                self.action_frame,
                text=action.label,
                command=lambda a=action.action_id: self.displayer.on_action(a),
            ).grid(row=i // per_row, column=i % per_row, padx=4, pady=4, sticky="w")

    def _render_wardrobe(self, sheet: CharacterSheet, state: CharacterState) -> None:
        self.wardrobe_keys = list(sheet.wardrobe.keys())
        labels = [sheet.wardrobe[k].label for k in self.wardrobe_keys]
        if labels:
            self.wardrobe_combo["values"] = labels
            self.wardrobe_combo["state"] = "readonly"
            if state.outfit in self.wardrobe_keys:
                self.wardrobe_combo.current(self.wardrobe_keys.index(state.outfit))
        else:
            self.wardrobe_combo["values"] = []
            self.wardrobe_combo["state"] = "disabled"

    @property
    def selected_wardrobe_key(self) -> str | None:
        idx = self.wardrobe_combo.current()
        if idx is None or idx < 0 or idx >= len(self.wardrobe_keys):
            return None
        return self.wardrobe_keys[idx]

    def update_state_view(self, sheet: CharacterSheet, state: CharacterState) -> None:
        """パラメータ表示と衣装コンボの現在値を更新する"""
        for name, (kind, widget, value_var) in self.param_widgets.items():
            pdef = sheet.parameters.get(name)
            if pdef is None:
                continue
            current = state.params.get(name)
            if kind == SCALAR:
                try:
                    num = float(current)
                except (TypeError, ValueError):
                    num = pdef.minv
                widget["value"] = num - pdef.minv
                shown = int(num) if float(num).is_integer() else round(num, 1)
                value_var.set(f"{shown} / {int(pdef.maxv)}")
            else:
                value_var.set(str(current))

        if state.outfit in self.wardrobe_keys:
            self.wardrobe_combo.current(self.wardrobe_keys.index(state.outfit))

    def set_dialogue(self, name: str, line: str, locked: bool) -> None:
        """セリフ欄を更新する"""
        self.dialogue_name_var.set(name)
        self.dialogue_text.configure(state="normal")
        self.dialogue_text.delete("1.0", "end")
        self.dialogue_text.insert("1.0", line)
        self.dialogue_text.configure(state="disabled")


class ConfigTab:
    """
    設定タブ (生成設定 / バックエンド / 状態トグル)
    """

    def __init__(self, owner: MainWindow, init_configs: GUIConfigs):
        self.super_owner = owner
        d: Displayer = owner.super_owner

        self.main_frame = ttk.Frame(owner.config_tab)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        HorizontalSeparator(self.main_frame, 0, 0, "生成設定")
        interior = ttk.Frame(self.main_frame)
        interior.grid(row=1, column=0, sticky="w")
        self.width_entry = put_textbox(
            interior, "幅", 0, 0, 5, str(init_configs.sd_width), "w", d.update_configs
        )
        self.height_entry = put_textbox(
            interior, "高さ", 0, 2, 5, str(init_configs.sd_height), "w", d.update_configs
        )
        self.scaleby_entry = put_textbox(
            interior, "倍率", 0, 4, 4, str(init_configs.sd_scaleby), "w", d.update_configs
        )
        self.steps_entry = put_textbox(
            interior, "ステップ数", 1, 0, 4, str(init_configs.sd_steps), "w", d.update_configs
        )
        self.batch_size_entry = put_textbox(
            interior, "生成数", 1, 2, 4, str(init_configs.sd_batch_size), "w", d.update_configs
        )

        exterior = ttk.Frame(self.main_frame)
        exterior.grid(row=2, column=0, sticky="w")
        self.ipaddr_entry = put_textbox(
            exterior, "IPアドレス", 0, 0, 16, init_configs.srv_ipaddr, "w", d.update_configs
        )
        self.port_entry = put_textbox(
            exterior, "ポート", 0, 2, 6, init_configs.srv_port, "w", d.update_configs
        )

        genctrl = ttk.Frame(self.main_frame)
        genctrl.grid(row=3, column=0, sticky="w")
        self.each_max_pics_entry = put_textbox(
            genctrl,
            "プロンプトごとの生成上限",
            0,
            0,
            4,
            str(init_configs.each_max_pics),
            "w",
            d.update_configs,
        )
        self.rest_capacity = put_textlabel(
            genctrl, "現在のディレクトリの残り容量(枚):", 0, 2, "", "w"
        )

        HorizontalSeparator(self.main_frame, 4, 0, "バックエンド")
        backend_frame = ttk.Frame(self.main_frame)
        backend_frame.grid(row=5, column=0, sticky="w")
        self.back_options = [BackEnd.a1111.value, BackEnd.comfy_ui.value]
        self.backend_var = tkinter.StringVar(value=init_configs.backend or self.back_options[0])
        self.backend_combo = ttk.Combobox(
            backend_frame,
            textvariable=self.backend_var,
            values=self.back_options,
            state="readonly",
            width=10,
        )
        self.backend_combo.grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.backend_combo.bind("<<ComboboxSelected>>", lambda e: d.on_switch_backend())

        HorizontalSeparator(self.main_frame, 6, 0, "状態")
        toggle = ttk.Frame(self.main_frame)
        toggle.grid(row=7, column=0, sticky="w")
        self.save_state_end_check = tkinter.BooleanVar(value=init_configs.save_state_end)
        ttk.Checkbutton(
            toggle, text="終了時に保存", variable=self.save_state_end_check, command=d.update_configs
        ).grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.load_state_start_check = tkinter.BooleanVar(value=init_configs.load_state_start)
        ttk.Checkbutton(
            toggle,
            text="開始時/選択時に復元",
            variable=self.load_state_start_check,
            command=d.update_configs,
        ).grid(row=0, column=1, padx=6, pady=6, sticky="w")


class DebugTab:
    """
    デバッグタブ (ダンプ / 表示トグル)
    """

    def __init__(self, owner: MainWindow, init_configs: GUIConfigs):
        self.super_owner = owner
        d: Displayer = owner.super_owner

        self.main_frame = ttk.Frame(owner.debug_tab)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        HorizontalSeparator(self.main_frame, 0, 0, "出力")
        dump = ttk.Frame(self.main_frame)
        dump.grid(row=1, column=0, sticky="w")
        ttk.Button(dump, text="アーカイブ出力", command=d.on_dump_archiver).grid(
            row=0, column=0, padx=6, pady=6, sticky="w"
        )
        ttk.Button(dump, text="タスクリスト", command=d.on_dump_tasklist).grid(
            row=0, column=1, padx=6, pady=6, sticky="w"
        )

        HorizontalSeparator(self.main_frame, 2, 0, "表示トグル")
        verbose = ttk.Frame(self.main_frame)
        verbose.grid(row=3, column=0, sticky="w")
        self.print_prompt_check = tkinter.BooleanVar(value=init_configs.print_prompt)
        ttk.Checkbutton(
            verbose, text="プロンプトを表示", variable=self.print_prompt_check, command=d.update_configs
        ).grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.print_picinfo_check = tkinter.BooleanVar(value=init_configs.print_picinfo)
        ttk.Checkbutton(
            verbose,
            text="画像メタデータを表示",
            variable=self.print_picinfo_check,
            command=d.update_configs,
        ).grid(row=0, column=1, padx=6, pady=6, sticky="w")
        self.print_event_check = tkinter.BooleanVar(value=init_configs.print_event)
        ttk.Checkbutton(
            verbose, text="イベントを表示", variable=self.print_event_check, command=d.update_configs
        ).grid(row=1, column=0, padx=6, pady=6, sticky="w")


class MainWindow:
    """
    メインウィンドウ (交流 / 設定 / デバッグ)
    """

    def __init__(self, owner: Displayer, init_configs: GUIConfigs):
        self.super_owner = owner

        owner.master.root.title("picmaker")
        owner.master.root.columnconfigure(0, weight=1)
        owner.master.root.rowconfigure(0, weight=1)
        owner.master.root.protocol("WM_DELETE_WINDOW", owner.destroy)

        self.notebook = ttk.Notebook(owner.master.root)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        self.main_tab = ttk.Frame(self.notebook, padding=12)
        self.main_tab.columnconfigure(0, weight=1)
        self.notebook.add(self.main_tab, text="交流")
        self.main_tab_obj = MainTab(self, init_configs)

        self.config_tab = ttk.Frame(self.notebook, padding=12)
        self.config_tab.columnconfigure(0, weight=1)
        self.notebook.add(self.config_tab, text="設定")
        self.config_tab_obj = ConfigTab(self, init_configs)

        self.debug_tab = ttk.Frame(self.notebook, padding=12)
        self.debug_tab.columnconfigure(0, weight=1)
        self.notebook.add(self.debug_tab, text="デバッグ")
        self.debug_tab_obj = DebugTab(self, init_configs)

        def clear_selection(event):
            if isinstance(event.widget, ttk.Entry):
                return
            owner.master.root.focus_set()

        self.notebook.bind("<Button-1>", clear_selection, add="+")


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

    # -- 便宜アクセサ ------------------------------------------------------ #
    @property
    def main_tab_obj(self) -> MainTab:
        return self.main_window.main_tab_obj

    @property
    def config_tab_obj(self) -> ConfigTab:
        return self.main_window.config_tab_obj

    @property
    def debug_tab_obj(self) -> DebugTab:
        return self.main_window.debug_tab_obj

    # -- ウィンドウ管理 ---------------------------------------------------- #
    def exists(self) -> bool:
        if self.master.root is None:
            return False
        try:
            return bool(self.master.root.winfo_exists())
        except TclError:
            return False

    def destroy(self) -> None:
        self.pic_window.destroy()
        self.info_window.destroy()
        if self.exists():
            self.master.root.destroy()

    def update_main_window(self, rest_capacity: int | None) -> None:
        """設定タブの残り容量表示を更新する"""
        from displayer.info_window import Consts

        self.config_tab_obj.rest_capacity.set(
            rest_capacity if rest_capacity is not None else Consts.not_available_text
        )

    def update_pic_window(self, picstats: PicStats = None) -> None:
        self.last_picstats = picstats
        if picstats is not NoImageStats:
            self.pic_window.update(picstats.path)
            self.switch_output_button_state(True)
        else:
            self.pic_window.update()
            self.switch_output_button_state(False)

        self.info_window.update_picinfo_tab(picstats)

    def switch_output_button_state(self, toggle: bool) -> None:
        if not self.exists():
            return

        output_button = self.main_tab_obj.output_button
        if toggle:
            if str(output_button.cget("state")) == "disabled":
                output_button.configure(state="normal")
        else:
            if str(output_button.cget("state")) == "normal":
                output_button.configure(state="disabled")

    # -- キャラクター UI 反映 (Master から呼ぶ) ---------------------------- #
    def set_character_list(self, metas: list[CharacterMeta], current: str | None) -> None:
        self.main_tab_obj.set_character_list(metas, current)

    def render_character(
        self, sheet: CharacterSheet, actions: ActionSet, state: CharacterState
    ) -> None:
        self.main_tab_obj.render_character(sheet, actions, state)

    def update_state_view(self, sheet: CharacterSheet, state: CharacterState) -> None:
        self.main_tab_obj.update_state_view(sheet, state)

    def set_dialogue(self, name: str, line: str, locked: bool) -> None:
        self.main_tab_obj.set_dialogue(name, line, locked)

    # -- イベント発行 ------------------------------------------------------ #
    def on_select_character(self) -> None:
        char_id = self.main_tab_obj.selected_char_id
        if char_id is not None:
            self.to_master.enclose(master.events.OnSelectCharacter(char_id=char_id))

    def on_reload_character(self) -> None:
        self.to_master.enclose(master.events.OnReloadCharacter())

    def on_action(self, action_id: str) -> None:
        wardrobe_key = None
        if self.main_tab_obj.action_kinds.get(action_id) == WARDROBE:
            wardrobe_key = self.main_tab_obj.selected_wardrobe_key
        self.to_master.enclose(
            master.events.OnAction(action_id=action_id, wardrobe_key=wardrobe_key)
        )

    def on_save_state(self) -> None:
        self.to_master.enclose(master.events.OnSaveState())

    def on_load_state(self) -> None:
        self.to_master.enclose(master.events.OnLoadState())

    def on_reset_state(self) -> None:
        self.to_master.enclose(master.events.OnResetState())

    def on_repeat_task(self) -> None:
        self.to_master.enclose(master.events.OnRepeatTask())

    def on_interrput_task(self) -> None:
        self.to_master.enclose(master.events.OnInterruptTask())

    def on_flush_tasks(self) -> None:
        self.to_master.enclose(master.events.OnFlushTasks())

    def on_flush_txt2img_tasks(self) -> None:
        self.to_master.enclose(master.events.OnFlushTxt2ImgTasks())

    def on_flush_img2img_tasks(self) -> None:
        self.to_master.enclose(master.events.OnFlushImg2ImgTasks())

    def on_open_pic_window(self) -> None:
        if self.pic_window is not None and self.pic_window.existed():
            self.pic_window.pic_window.deiconify()
            self.pic_window.pic_window.lift()
        else:
            self.pic_window.construct(fix_position=True)

        self.update_pic_window(self.last_picstats)

    def on_open_info_window(self) -> None:
        if self.info_window is not None and self.info_window.existed():
            self.info_window.info_window.deiconify()
            self.info_window.info_window.lift()
        else:
            self.info_window.construct(fix_position=True)

        self.info_window.update_taskinfo_tab(task=self.last_task)
        self.info_window.update_picinfo_tab(self.last_picstats)

    def on_dump_archiver(self) -> None:
        self.to_master.enclose(master.events.OnDumpArchiver())

    def on_dump_tasklist(self) -> None:
        self.to_master.enclose(master.events.OnDumpTaskList())

    def on_backward(self) -> None:
        self.to_master.enclose(master.events.OnBackward())

    def on_forward(self) -> None:
        self.to_master.enclose(master.events.OnForward())

    def on_upscale(self) -> None:
        self.to_master.enclose(master.events.OnUpscale())

    def on_delete(self) -> None:
        self.to_master.enclose(master.events.OnDelete())

    def on_switch_backend(self) -> None:
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

    @property
    def crnt_configs(self) -> GUIConfigs:
        """GUI 上の設定値"""
        config = self.config_tab_obj
        debug = self.debug_tab_obj
        return GUIConfigs(
            srv_ipaddr=config.ipaddr_entry.get(),
            srv_port=config.port_entry.get(),
            sd_steps=int(config.steps_entry.get()),
            sd_batch_size=int(config.batch_size_entry.get()),
            sd_width=int(config.width_entry.get()),
            sd_height=int(config.height_entry.get()),
            sd_scaleby=float(config.scaleby_entry.get()),
            each_max_pics=int(config.each_max_pics_entry.get()),
            backend=config.backend_combo.get(),
            crnt_character=self.main_tab_obj.selected_char_id,
            save_state_end=bool(config.save_state_end_check.get()),
            load_state_start=bool(config.load_state_start_check.get()),
            print_prompt=bool(debug.print_prompt_check.get()),
            print_picinfo=bool(debug.print_picinfo_check.get()),
            print_event=bool(debug.print_event_check.get()),
        )

    # -- ウィンドウ座標 ---------------------------------------------------- #
    @property
    def config_window_x(self) -> int:
        self.master.root.update_idletasks()
        return self.master.root.winfo_x()

    @property
    def config_window_y(self) -> int:
        self.master.root.update_idletasks()
        return self.master.root.winfo_y()

    @property
    def config_window_width(self) -> int:
        self.master.root.update_idletasks()
        return self.master.root.winfo_width()

    @property
    def config_window_height(self) -> int:
        self.master.root.update_idletasks()
        return self.master.root.winfo_height()
