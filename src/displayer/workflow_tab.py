"""
ワークフロータブ

ComfyUI ワークフロー定義 YAML の選択, 検証, プレビューを行う\n
仕様: yamls/workflow_yaml_spec.md
"""

from __future__ import annotations

import json
import tkinter
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, ttk
from typing import TYPE_CHECKING

import master.events
from common.functions import YAML_KIND_WORKFLOW, PathConsts, read_yaml_kind
from displayer import theme, widgets
from displayer.dataclasses import GUIConfigs
from displayer.theme import STYLES
from generator.comfyui_generator import ComfyUIGenerator
from generator.comfyui_workflow import (
    Link,
    Param,
    WorkFlowDef,
    WorkFlowSyntaxError,
    scan_workflow_yamls,
)
from generator.dataclasses import TaskBlueprintImg2Img, TaskBlueprintTxt2Img

if TYPE_CHECKING:
    from displayer.displayer import MainWindow


@dataclass(frozen=True)
class Consts:
    """
    このクラス関連の定数\n
    (状態表示の色は displayer.theme のパレットを参照する)
    """

    # ComfyUIGenerator が要求するセクション名
    kind_txt2img: str = "txt2img"
    kind_img2img: str = "img2img"
    # プレビュー時のダミー値
    preview_prompt: str = "(preview) 1girl, masterpiece"
    preview_negative: str = "(preview) worst quality"
    preview_path: str = "pics/preview.png"


class WorkFlowPane:
    """
    1 セクション (txt2img / img2img) 分の内容表示ペイン
    """

    def __init__(self, owner: WorkFlowTab, parent: ttk.Notebook, kind: str):
        """
        コンストラクタ

        Args:
            owner (WorkFlowTab): WorkFlowTab インスタンス
            parent (ttk.Notebook): 挿入先ノートブック
            kind (str): セクション名 (txt2img / img2img)
        """
        self.super_owner = owner
        self.kind = kind
        self.wfdef: WorkFlowDef | None = None

        self.frame = ttk.Frame(parent, padding=10)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)
        self.frame.rowconfigure(5, weight=1)

        # --- ノード一覧 ------------------------------------------------------
        ttk.Label(self.frame, text="ノード", style=STYLES.section).grid(
            row=0, column=0, sticky="w", pady=(0, 3)
        )

        tree_frame = ttk.Frame(self.frame, style=STYLES.card, padding=1)
        tree_frame.grid(row=1, column=0, pady=(0, 4), sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            tree_frame, columns=("idx", "name", "class_type", "inputs"), show="headings", height=9
        )
        for col, text, width in (
            ("idx", "idx", 40),
            ("name", "ノード名", 140),
            ("class_type", "class_type", 170),
            ("inputs", "inputs", 320),
        ):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")

        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        tree_scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=tree_scroll.set)

        # --- プレースホルダ --------------------------------------------------
        self.placeholder_var = tkinter.StringVar(value="")
        ttk.Label(self.frame, textvariable=self.placeholder_var, wraplength=620).grid(
            row=2, column=0, pady=(2, 0), sticky="w"
        )

        # --- プレビュー ------------------------------------------------------
        head = ttk.Frame(self.frame)
        head.grid(row=3, column=0, pady=(10, 3), sticky="ew")
        ttk.Label(head, text="ビルド結果 (POST される JSON)", style=STYLES.section).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(head, text="プレビュー", command=self.on_preview).grid(
            row=0, column=1, padx=10
        )

        text_frame = ttk.Frame(self.frame)
        text_frame.grid(row=5, column=0, sticky="nsew")
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        self.preview_text = widgets.themed_text(text_frame, height=9)
        self.preview_text.grid(row=0, column=0, sticky="nsew")
        text_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.preview_text.yview)
        text_scroll.grid(row=0, column=1, sticky="ns")
        self.preview_text.configure(yscrollcommand=text_scroll.set, state="disabled")

    def retheme(self) -> None:
        """
        プレビューテキストを現在のパレットへ追従させる
        """
        widgets.retheme_text(self.preview_text)

    def update(self, wfdef: WorkFlowDef | None) -> None:
        """
        表示内容を差し替える

        Args:
            wfdef (WorkFlowDef | None): ワークフロー定義
        """
        self.wfdef = wfdef
        self.tree.delete(*self.tree.get_children())
        self.write_preview("")

        if wfdef is None:
            self.placeholder_var.set("")
            return

        for nname, ndef in wfdef.nodes.items():
            self.tree.insert(
                "",
                "end",
                values=(ndef["idx"], nname, ndef["class_type"], self.inputs_digest(ndef["inputs"])),
            )

        supplied = set(self.super_owner.supplied_params(self.kind))
        required = wfdef.placeholders
        missing = [p for p in required if p not in supplied]
        text = "パラメータ: " + (", ".join(f"${p}" for p in required) if required else "(なし)")
        if missing:
            text += "  /  Generator が渡さないもの: " + ", ".join(f"${p}" for p in missing)
        self.placeholder_var.set(text)

    def inputs_digest(self, inputs: dict[str, object]) -> str:
        """
        inputs を 1 行で表す文字列へ変換する

        Args:
            inputs (dict[str, object]): 解決済 inputs

        Returns:
            str: 表示用文字列
        """
        parts: list[str] = []
        for key, value in inputs.items():
            if isinstance(value, Link):
                parts.append(f"{key}=<{value.node}:{value.slot}>")
            elif isinstance(value, Param):
                parts.append(f"{key}=${value.name}")
            else:
                shown = str(value)
                parts.append(f"{key}={shown[:20] + '...' if len(shown) > 20 else shown}")
        return ", ".join(parts)

    def write_preview(self, text: str) -> None:
        """
        プレビュー領域を更新する

        Args:
            text (str): 表示する文字列
        """
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", text)
        self.preview_text.configure(state="disabled")

    def on_preview(self) -> None:
        """
        プレビューボタンハンドラ\n
        現在の GUI 設定値からダミータスクを作り, POST される JSON を表示する
        """
        if self.wfdef is None:
            self.write_preview(f"'{self.kind}' セクションが読み込まれていません.")
            return

        try:
            params = self.super_owner.preview_params(self.kind)
            built = self.wfdef.build(params).todict()
        except KeyError as e:
            self.write_preview(f"ビルドに失敗しました: {e}")
            return

        self.write_preview(json.dumps(built, ensure_ascii=False, indent=2))


class WorkFlowTab:
    """
    ワークフロータブ
    """

    def __init__(self, owner: MainWindow, init_configs: GUIConfigs):
        """
        コンストラクタ

        Args:
            owner (MainWindow): MainWindow インスタンス
            init_configs (GUIConfigs): 初期設定値
        """
        self.super_owner = owner
        self.wf_yamlpath: Path = (
            Path(init_configs.wf_yamlpath)
            if init_configs.wf_yamlpath is not None
            else PathConsts.workflow_yaml
        )
        self.wfdefs: dict[str, WorkFlowDef] = {}
        # 表示ラベル -> パス
        self.entries: dict[str, Path] = {}
        # 直近の検証結果 (retheme で状態色を再現するため)
        self._status_ok: bool = True

        self.main_frame = ttk.Frame(owner.workflow_tab)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(2, weight=1)

        # --- 定義カード (選択行 + 状態 + 警告) --------------------------------
        ttk.Label(self.main_frame, text="ワークフロー定義", style=STYLES.section).grid(
            row=0, column=0, sticky="w", pady=(0, 2)
        )
        card = ttk.Frame(self.main_frame, style=STYLES.card, padding=12)
        card.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        card.columnconfigure(1, weight=1)

        ttk.Label(card, text="WF YAML", style=STYLES.muted).grid(
            row=0, column=0, padx=(0, 6), pady=4, sticky="w"
        )
        self.selected_var = tkinter.StringVar(value=self.wf_yamlpath.name)
        self.combo = ttk.Combobox(card, textvariable=self.selected_var, state="readonly")
        self.combo.grid(row=0, column=1, pady=4, sticky="ew")
        self.combo.bind("<<ComboboxSelected>>", lambda e: self.on_select())

        button_frame = ttk.Frame(card, style=STYLES.surface)
        button_frame.grid(row=0, column=2, padx=(6, 0), sticky="e")
        ttk.Button(button_frame, text="参照", command=self.on_browse).grid(row=0, column=0, padx=2)
        ttk.Button(button_frame, text="再読み込み", command=self.on_reload).grid(
            row=0, column=1, padx=2
        )

        # --- 状態表示 --------------------------------------------------------
        self.status_var = tkinter.StringVar(value="")
        self.status_label = ttk.Label(
            card, textvariable=self.status_var, wraplength=620, style=STYLES.value
        )
        self.status_label.grid(row=1, column=0, columnspan=3, pady=(6, 0), sticky="w")

        self.warning_var = tkinter.StringVar(value="")
        self.warning_label = ttk.Label(
            card, textvariable=self.warning_var, wraplength=620, style=STYLES.value
        )
        self.warning_label.configure(foreground=theme.current.warn)
        self.warning_label.grid(row=2, column=0, columnspan=3, pady=(2, 0), sticky="w")

        # --- セクションごとのサブタブ -------------------------------------------
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.grid(row=2, column=0, sticky="nsew")

        self.panes: dict[str, WorkFlowPane] = {}
        for kind, label in (
            (Consts.kind_txt2img, "生成 (txt2img)"),
            (Consts.kind_img2img, "拡大 (img2img)"),
        ):
            pane = WorkFlowPane(self, self.notebook, kind)
            self.notebook.add(pane.frame, text=label)
            self.panes[kind] = pane

        self.refresh_entries()

    # -------------------------------------------------------------------------
    # 更新
    # -------------------------------------------------------------------------

    def refresh_entries(self) -> None:
        """
        YAML ディレクトリを走査してコンボボックスを作り直し, 検証を行う
        """
        self.entries = {s.label: s.path for s in scan_workflow_yamls(PathConsts.yaml_dir)}

        # ディレクトリ外のファイルが選択されている場合も選択肢に含める
        if self.wf_yamlpath not in self.entries.values():
            self.entries[str(self.wf_yamlpath)] = self.wf_yamlpath

        self.combo.configure(values=list(self.entries.keys()))
        label = next((k for k, v in self.entries.items() if v == self.wf_yamlpath), None)
        self.selected_var.set(label if label is not None else str(self.wf_yamlpath))

        self.validate()

    def validate(self) -> None:
        """
        選択中の YAML を読み込み, 状態表示と各ペインを更新する
        """
        self.wfdefs = {}
        self.warning_var.set("")

        try:
            self.wfdefs = WorkFlowDef.load(self.wf_yamlpath)
        except WorkFlowSyntaxError as e:
            self._status_ok = False
            self.status_label.configure(foreground=theme.current.err)
            self.status_var.set(f"エラー: {e}")
            for pane in self.panes.values():
                pane.update(None)
            return

        self._status_ok = True
        self.status_label.configure(foreground=theme.current.ok)
        sections = ", ".join(f"{k} ({len(v.nodes)} ノード)" for k, v in self.wfdefs.items())
        self.status_var.set(f"OK: {sections}")

        warnings = [w for wfdef in self.wfdefs.values() for w in wfdef.warnings]
        missing = [k for k in self.panes if k not in self.wfdefs]
        if missing:
            warnings.insert(0, f"セクションがありません: {', '.join(missing)}")
        if warnings:
            self.warning_var.set("警告: " + " / ".join(warnings))

        for kind, pane in self.panes.items():
            pane.update(self.wfdefs.get(kind))

    def retheme(self) -> None:
        """
        テーマ切替時に非 ttk 領域と状態色を追従させる
        """
        self.status_label.configure(
            foreground=theme.current.ok if self._status_ok else theme.current.err
        )
        self.warning_label.configure(foreground=theme.current.warn)
        for pane in self.panes.values():
            pane.retheme()

    # -------------------------------------------------------------------------
    # パラメータ
    # -------------------------------------------------------------------------

    def supplied_params(self, kind: str) -> list[str]:
        """
        ComfyUIGenerator が当該セクションへ渡すパラメータ名

        Args:
            kind (str): セクション名

        Returns:
            list[str]: パラメータ名のリスト
        """
        return list(self.preview_params(kind).keys())

    def preview_params(self, kind: str) -> dict[str, object]:
        """
        プレビュー用のパラメータを現在の GUI 設定値から組み立てる\n
        ComfyUIGenerator.make_params と同じ形を返す

        Args:
            kind (str): セクション名

        Returns:
            dict[str, object]: パラメータ
        """
        try:
            configs = self.displayer.crnt_configs
        except (ValueError, tkinter.TclError, AttributeError):
            configs = GUIConfigs()

        is_upscale = kind == Consts.kind_img2img
        picstats = self.displayer.last_picstats
        path = (
            str(picstats.path)
            if picstats is not None and getattr(picstats, "path", None) is not None
            else Consts.preview_path
        )

        common = {
            "prompt": Consts.preview_prompt,
            "negative_prompt": Consts.preview_negative,
            "seed": -1,
            "steps": configs.sd_steps,
            "batch_size": configs.sd_batch_size,
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "cfg_scale": 7.0,
            "dst_addr": configs.srv_ipaddr,
            "dst_port": configs.srv_port,
        }
        task = (
            TaskBlueprintImg2Img(
                path=path,
                upscaler_name="nearest-exact",
                denoising_strength=0.65,
                width=int(configs.sd_width * configs.sd_scaleby),
                height=int(configs.sd_height * configs.sd_scaleby),
                **common,
            )
            if is_upscale
            else TaskBlueprintTxt2Img(
                width=configs.sd_width, height=configs.sd_height, **common
            )
        )
        return ComfyUIGenerator.make_params(task, is_upscale)

    # -------------------------------------------------------------------------
    # ハンドラ
    # -------------------------------------------------------------------------

    def on_select(self) -> None:
        """
        コンボボックス選択ハンドラ
        """
        picked = self.entries.get(self.selected_var.get())
        if picked is None or picked == self.wf_yamlpath:
            return

        self.wf_yamlpath = picked
        self.validate()
        self.notify_select()

    def on_browse(self) -> None:
        """
        参照ボタンハンドラ
        """
        picked = filedialog.askopenfilename(
            title="WF YAML選択",
            initialdir=str(PathConsts.yaml_dir),
            filetypes=[("YAML", "*.yaml")],
        )
        if not picked:
            return

        path = Path(picked)
        if read_yaml_kind(path) != YAML_KIND_WORKFLOW:
            self._status_ok = False
            self.status_label.configure(foreground=theme.current.err)
            self.status_var.set(
                f"ワークフロー定義YAMLではありません (kind: workflow が必要): {path.name}"
            )
            return

        self.wf_yamlpath = path
        self.refresh_entries()
        self.notify_select()

    def on_reload(self) -> None:
        """
        再読み込みボタンハンドラ
        """
        self.refresh_entries()
        self.displayer.to_master.enclose(master.events.OnReloadWfYaml())

    def notify_select(self) -> None:
        """
        選択変更を Master へ通知し, メインタブの表示も同期する
        """
        self.displayer.to_master.enclose(
            master.events.OnSelectWfYaml(path=str(self.wf_yamlpath))
        )
        self.displayer.update_configs()
        self.displayer.sync_yaml_display()

    @property
    def displayer(self):
        """
        Displayer インスタンス

        Returns:
            Displayer: Displayer インスタンス
        """
        return self.super_owner.super_owner
