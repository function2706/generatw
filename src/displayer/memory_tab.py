"""
記憶タブ

記憶の保存 / 復元 / 忘却, 起動時の動作設定, および現在の記憶の表示を集約する
"""

from __future__ import annotations

import json
import tkinter
from tkinter import ttk
from typing import TYPE_CHECKING

from displayer import widgets
from displayer.theme import STYLES
from displayer.widgets import action_button, carded_section

if TYPE_CHECKING:
    from displayer.dataclasses import GUIConfigs
    from displayer.displayer import MainWindow


class MemoryTab:
    """
    記憶タブ
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

        self.main_frame = ttk.Frame(owner.memory_tab)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(5, weight=1)

        self._build_operation()
        self._build_startup(init_configs)
        self._build_view()

    def _build_operation(self) -> None:
        """記憶操作カード (保存 / 復元 / 忘却) を構築する"""
        card = carded_section(self.main_frame, "記憶操作", 0, pady=(4, 2))
        d = self.displayer
        w = 8
        action_button(card, "保存", d.on_save_memory, width=w, row=0, column=0)
        action_button(card, "復元", d.on_load_memory, width=w, row=0, column=1)
        action_button(card, "忘却", d.on_forget_memory, width=w, row=0, column=2)

    def _build_startup(self, cfg: GUIConfigs) -> None:
        """起動時の記憶カード (終了時保存 / 開始時復元) を構築する"""
        card = carded_section(self.main_frame, "起動時の記憶", 1)
        on_change = self.displayer.update_configs

        self.save_memory_end_check = tkinter.BooleanVar(value=cfg.save_memory_end)
        ttk.Checkbutton(
            card, text="終了時に保存", variable=self.save_memory_end_check, command=on_change
        ).grid(row=0, column=0, padx=(0, 16), pady=3, sticky="w")

        self.load_memory_start_check = tkinter.BooleanVar(value=cfg.load_memory_start)
        ttk.Checkbutton(
            card, text="開始時に復元", variable=self.load_memory_start_check, command=on_change
        ).grid(row=0, column=1, pady=3, sticky="w")

    def _build_view(self) -> None:
        """現在の記憶の表示領域 (更新ボタン + JSON テキスト) を構築する"""
        head = ttk.Frame(self.main_frame)
        head.grid(row=4, column=0, sticky="ew", pady=(12, 3))
        head.columnconfigure(0, weight=1)
        ttk.Label(head, text="現在の記憶", style=STYLES.section).grid(row=0, column=0, sticky="w")
        action_button(head, "更新", self.displayer.on_request_memory, row=0, column=1)

        body = ttk.Frame(self.main_frame)
        body.grid(row=5, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)
        self.view = widgets.themed_text(body, wrap="none")
        self.view.grid(row=0, column=0, sticky="nsew")
        yscroll = ttk.Scrollbar(body, orient="vertical", command=self.view.yview)
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll = ttk.Scrollbar(body, orient="horizontal", command=self.view.xview)
        xscroll.grid(row=1, column=0, sticky="ew")
        self.view.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self._write("(未取得 — 「更新」を押してください)")

    # -------------------------------------------------------------------------

    def update_view(self, data: dict) -> None:
        """
        記憶スナップショットを JSON テキストで表示する

        Args:
            data (dict): parser.memory_snapshot() の戻り値
        """
        if not data:
            self._write("(記憶なし — YAML が未選択か, まだ記録がありません)")
            return
        self._write(json.dumps(data, ensure_ascii=False, indent=2))

    def _write(self, text: str) -> None:
        self.view.configure(state="normal")
        self.view.delete("1.0", "end")
        self.view.insert("1.0", text)
        self.view.configure(state="disabled")

    def retheme(self) -> None:
        """テーマ切替時にテキスト配色を追従させる"""
        widgets.retheme_text(self.view)
