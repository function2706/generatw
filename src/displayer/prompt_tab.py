"""
プロンプト定義タブ

parser (プロンプトルール) YAML の編集, 検証, 構造/動作プレビューを行う\n
仕様: yamls/prompt_yaml_spec.md
"""

from __future__ import annotations

import tkinter
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, ttk
from typing import TYPE_CHECKING

import yaml

import master.events
from common.functions import PathConsts
from displayer import theme, widgets
from displayer.theme import STYLES
from parser.prompter.prompter import Prompter

if TYPE_CHECKING:
    from displayer.displayer import MainWindow


@dataclass(frozen=True)
class Consts:
    """
    このクラス関連の定数
    """

    # Category の構造解析で読み飛ばす予約キー
    reserved_keys: tuple[str, ...] = (
        "interpreter",
        "ignition",
        "common",
        "pattern",
        "capturegrp",
        "maps",
        "ranges",
        "intervals",
        "default",
        "import",
        "recurse",
    )
    # 構造ツリーで Rule ブロックとみなすキー
    rule_keys: tuple[str, ...] = ("maps", "ranges", "intervals", "recurse")


def known_interpreter_keywords() -> set[str]:
    """
    実行時に受理される interpreter キーワード集合を取得する (取得不能時は空集合)

    Returns:
        set[str]: interpreter キーワード
    """
    try:
        from parser.parser import INTERPRETER_LIST

        return {i.keyword() for i in INTERPRETER_LIST}
    except Exception:
        return set()


class PromptTab:
    """
    プロンプト定義タブ
    """

    def __init__(self, owner: MainWindow, init_configs):
        """
        コンストラクタ

        Args:
            owner (MainWindow): MainWindow インスタンス
            init_configs (GUIConfigs): 初期設定値
        """
        self.super_owner = owner
        # 既定は現在選択中のフロントエンド YAML
        self.path: Path | None = (
            Path(init_configs.yamlpath) if init_configs.yamlpath is not None else None
        )
        self.entries: dict[str, Path] = {}
        self._prompter: Prompter | None = None
        self._status_ok: bool = False

        self.main_frame = ttk.Frame(owner.prompt_tab)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(2, weight=1)

        self._build_definition_card()
        self._build_workspace()
        self.refresh_entries()

    # -------------------------------------------------------------------------
    # 構築
    # -------------------------------------------------------------------------

    def _build_definition_card(self) -> None:
        """
        定義カード (ファイル選択 + 状態 + 警告) を構築する
        """
        ttk.Label(self.main_frame, text="プロンプト定義", style=STYLES.section).grid(
            row=0, column=0, sticky="w", pady=(0, 2)
        )
        card = ttk.Frame(self.main_frame, style=STYLES.card, padding=12)
        card.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        card.columnconfigure(1, weight=1)

        ttk.Label(card, text="YAML", style=STYLES.muted).grid(
            row=0, column=0, padx=(0, 6), pady=4, sticky="w"
        )
        self.selected_var = tkinter.StringVar(value=self.path.name if self.path else "(未選択)")
        self.combo = ttk.Combobox(card, textvariable=self.selected_var, state="readonly")
        self.combo.grid(row=0, column=1, pady=4, sticky="ew")
        self.combo.bind("<<ComboboxSelected>>", lambda e: self.on_select())

        btns = ttk.Frame(card, style=STYLES.surface)
        btns.grid(row=0, column=2, padx=(6, 0), sticky="e")
        widgets.action_button(btns, "参照", self.on_browse, row=0, column=0)
        widgets.action_button(btns, "検証", self.validate, row=0, column=1)
        widgets.action_button(btns, "保存", self.on_save, row=0, column=2)

        self.status_var = tkinter.StringVar(value="")
        self.status_label = ttk.Label(
            card, textvariable=self.status_var, wraplength=680, style=STYLES.value
        )
        self.status_label.grid(row=1, column=0, columnspan=3, pady=(6, 0), sticky="w")

        self.warning_var = tkinter.StringVar(value="")
        self.warning_label = ttk.Label(
            card, textvariable=self.warning_var, wraplength=680, style=STYLES.value
        )
        self.warning_label.configure(foreground=theme.current.warn)
        self.warning_label.grid(row=2, column=0, columnspan=3, pady=(2, 0), sticky="w")

    def _build_workspace(self) -> None:
        """
        エディタ (左) と 構造/動作プレビュー (右) の 2 ペインを構築する
        """
        paned = ttk.Panedwindow(self.main_frame, orient="horizontal")
        paned.grid(row=2, column=0, sticky="nsew")

        # --- 左: エディタ ----------------------------------------------------
        editor_wrap = ttk.Frame(paned)
        editor_wrap.columnconfigure(0, weight=1)
        editor_wrap.rowconfigure(1, weight=1)
        ttk.Label(editor_wrap, text="エディタ", style=STYLES.section).grid(
            row=0, column=0, sticky="w", pady=(0, 3)
        )
        edit_frame = ttk.Frame(editor_wrap)
        edit_frame.grid(row=1, column=0, sticky="nsew")
        edit_frame.columnconfigure(0, weight=1)
        edit_frame.rowconfigure(0, weight=1)
        self.editor = widgets.themed_text(edit_frame, width=52, undo=True)
        self.editor.grid(row=0, column=0, sticky="nsew")
        yscroll = ttk.Scrollbar(edit_frame, orient="vertical", command=self.editor.yview)
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll = ttk.Scrollbar(edit_frame, orient="horizontal", command=self.editor.xview)
        xscroll.grid(row=1, column=0, sticky="ew")
        self.editor.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        paned.add(editor_wrap, weight=3)

        # --- 右: 構造 / 動作プレビュー ---------------------------------------
        self.right_notebook = rnb = ttk.Notebook(paned)
        rnb.add(self._build_structure_pane(rnb), text="構造")
        rnb.add(self._build_preview_pane(rnb), text="動作プレビュー")
        paned.add(rnb, weight=2)

    def _build_structure_pane(self, parent: ttk.Notebook) -> ttk.Frame:
        """
        構造プレビュー (Screen > Category ツリー) ペインを構築する
        """
        frame = ttk.Frame(parent, padding=8)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        holder = ttk.Frame(frame, style=STYLES.card, padding=1)
        holder.grid(row=0, column=0, sticky="nsew")
        holder.columnconfigure(0, weight=1)
        holder.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(holder, columns=("kind", "detail"), show="tree headings")
        self.tree.heading("#0", text="要素")
        self.tree.heading("kind", text="種別")
        self.tree.heading("detail", text="pattern / ignition")
        self.tree.column("#0", width=170, anchor="w")
        self.tree.column("kind", width=90, anchor="w")
        self.tree.column("detail", width=200, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(holder, orient="vertical", command=self.tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scroll.set)
        return frame

    def _build_preview_pane(self, parent: ttk.Notebook) -> ttk.Frame:
        """
        動作プレビュー (入力テキスト -> 生成プロンプト) ペインを構築する\n
        入力は複数行 (実際に画面から渡される改行込みテキストを想定) を受け付ける
        """
        frame = ttk.Frame(parent, padding=8)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        frame.rowconfigure(3, weight=2)

        # --- 入力テキスト (複数行) ------------------------------------------
        header = ttk.Frame(frame)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 3))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="入力テキスト (複数行可)", style=STYLES.section).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(header, text="プレビュー", command=self.on_preview).grid(
            row=0, column=1, sticky="e"
        )

        input_frame = ttk.Frame(frame)
        input_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 6))
        input_frame.columnconfigure(0, weight=1)
        input_frame.rowconfigure(0, weight=1)
        self.input_text = widgets.themed_text(input_frame, height=5, wrap="word")
        self.input_text.grid(row=0, column=0, sticky="nsew")
        iscroll = ttk.Scrollbar(input_frame, orient="vertical", command=self.input_text.yview)
        iscroll.grid(row=0, column=1, sticky="ns")
        self.input_text.configure(yscrollcommand=iscroll.set)

        # --- 結果 ------------------------------------------------------------
        ttk.Label(frame, text="結果", style=STYLES.section).grid(
            row=2, column=0, sticky="w", pady=(2, 3)
        )
        result_frame = ttk.Frame(frame)
        result_frame.grid(row=3, column=0, sticky="nsew")
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        self.result_text = widgets.themed_text(result_frame, height=8)
        self.result_text.grid(row=0, column=0, sticky="nsew")
        rscroll = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_text.yview)
        rscroll.grid(row=0, column=1, sticky="ns")
        self.result_text.configure(yscrollcommand=rscroll.set, state="disabled")
        return frame

    # -------------------------------------------------------------------------
    # ファイル操作
    # -------------------------------------------------------------------------

    def refresh_entries(self) -> None:
        """
        yamls ディレクトリを走査してコンボボックスを作り直し, 現ファイルを読み込む
        """
        found = sorted(PathConsts.yaml_dir.glob("*.yaml"))
        self.entries = {p.name: p for p in found}
        if self.path is not None and self.path not in self.entries.values():
            self.entries[str(self.path)] = self.path

        self.combo.configure(values=list(self.entries.keys()))
        if self.path is not None:
            label = next((k for k, v in self.entries.items() if v == self.path), self.path.name)
            self.selected_var.set(label)
            self.load_file()
        else:
            self.selected_var.set("(未選択)")

    def load_file(self) -> None:
        """
        現在のパスの内容をエディタへ読み込み, 検証する
        """
        if self.path is None or not self.path.exists():
            self.set_editor_text("")
            return
        try:
            text = self.path.read_text(encoding="utf-8")
        except OSError as e:
            self.set_status(f"読み込みに失敗しました: {e}", ok=False)
            return
        self.set_editor_text(text)
        self.validate()

    def on_select(self) -> None:
        """
        コンボボックス選択ハンドラ
        """
        picked = self.entries.get(self.selected_var.get())
        if picked is None or picked == self.path:
            return
        self.path = picked
        self.load_file()

    def on_browse(self) -> None:
        """
        参照ボタンハンドラ
        """
        picked = filedialog.askopenfilename(
            title="プロンプト定義 YAML 選択",
            initialdir=str(PathConsts.yaml_dir),
            filetypes=[("YAML", "*.yaml")],
        )
        if not picked:
            return
        self.path = Path(picked)
        self.refresh_entries()

    def on_save(self) -> None:
        """
        保存ボタンハンドラ\n
        エディタ内容を検証し, 問題がなければファイルへ書き出す\n
        保存先が現在のフロントエンド YAML なら Master へ再読み込みを通知する
        """
        if self.path is None:
            self.set_status("保存先が選択されていません.", ok=False)
            return
        if not self.validate():
            self.set_status("検証エラーのため保存を中止しました.", ok=False)
            return
        try:
            self.path.write_text(self.editor_text(), encoding="utf-8")
        except OSError as e:
            self.set_status(f"保存に失敗しました: {e}", ok=False)
            return

        msg = f"保存しました: {self.path.name}"
        active = self.displayer.crnt_configs.yamlpath
        if active is not None and Path(active) == self.path:
            self.displayer.to_master.enclose(master.events.OnReloadYaml())
            msg += " / 選択中のためリロードを通知しました"
        self.set_status(msg, ok=True)

    # -------------------------------------------------------------------------
    # 検証 / プレビュー
    # -------------------------------------------------------------------------

    def validate(self) -> bool:
        """
        エディタ内容を解析し, 状態表示と構造ツリーを更新する

        Returns:
            bool: 検証に成功したか
        """
        self.warning_var.set("")
        text = self.editor_text()

        try:
            yamldict = yaml.safe_load(text)
        except yaml.YAMLError as e:
            self._fail(f"YAML 構文エラー: {self._yaml_error(e)}")
            return False

        if not isinstance(yamldict, dict):
            self._fail("トップレベルはマッピング (キー: 値) である必要があります.")
            return False

        try:
            prompter = Prompter.from_yamldict(yamldict)
        except (ValueError, TypeError) as e:
            self._fail(f"定義エラー: {e}")
            return False
        except Exception as e:  # re.error など想定外も握って GUI を守る
            self._fail(f"解析エラー: {type(e).__name__}: {e}")
            return False

        self._prompter = prompter
        self._status_ok = True
        n_cat = sum(self._count_categories(v) for k, v in yamldict.items() if isinstance(v, dict))
        self.status_label.configure(foreground=theme.current.ok)
        self.status_var.set(
            f"OK: interpreter={prompter.interpreter_keyword or '(未指定)'}, "
            f"{len(prompter.screens)} screen / {n_cat} category"
        )

        self._check_warnings(prompter, yamldict)
        self.populate_tree(yamldict)
        return True

    def _check_warnings(self, prompter: Prompter, yamldict: dict) -> None:
        """
        非致命的な警告 (未知 interpreter 等) を集約して表示する
        """
        warnings: list[str] = []
        known = known_interpreter_keywords()
        kw = prompter.interpreter_keyword
        if known and kw not in known:
            cands = ", ".join(sorted(known))
            warnings.append(f"interpreter '{kw}' は実行時候補に見当たりません (候補: {cands})")
        if not prompter.screens:
            warnings.append("Screen が 1 つも定義されていません")
        self.warning_var.set(("警告: " + " / ".join(warnings)) if warnings else "")

    def _fail(self, message: str) -> None:
        """
        検証失敗時の共通処理
        """
        self._prompter = None
        self._status_ok = False
        self.status_label.configure(foreground=theme.current.err)
        self.status_var.set(message)
        self.tree.delete(*self.tree.get_children())

    def on_preview(self) -> None:
        """
        プレビューボタンハンドラ\n
        現在の入力テキストから生成されるプロンプトを表示する
        """
        if self._prompter is None and not self.validate():
            self.write_result("検証エラーのためプレビューできません.")
            return

        text = self.input_text.get("1.0", "end-1c")
        prompt, reports = self._prompter.to_prompt(text)
        lines = [
            f"発火Screen: {prompt.screen_id if prompt.screen_id is not None else '(未発火)'}",
            "",
            "[ positive ]",
            *self._format_parts(prompt.positive),
            "",
            "[ negative ]",
            *self._format_parts(prompt.negative),
        ]
        if reports:
            lines += ["", f"[ no-hit reports ] ({len(reports)} 件)"]
            for r in reports:
                lines.append(f"  screen={r.screen_id} matched={r.matched!r} pattern={r.pattern!r}")
        lines += ["", "※ <a|b> 等の確率記法は 1 通りにサンプルされた結果です"]
        self.write_result("\n".join(lines))

    @staticmethod
    def _format_parts(parts) -> list[str]:
        """
        PromptParts のリストを表示用の行へ整形する
        """
        if not parts:
            return ["  (なし)"]
        lines = []
        for pp in parts:
            path = "/".join(pp.path) if pp.path else "(common)"
            tokens = ", ".join(t.to_str() for t in pp.tokens)
            lines.append(f"  {path}: {tokens}")
        return lines

    # -------------------------------------------------------------------------
    # 構造ツリー
    # -------------------------------------------------------------------------

    def populate_tree(self, yamldict: dict) -> None:
        """
        yamldict から Screen > Category の構造ツリーを再構築する

        Args:
            yamldict (dict): 解析済み YAML 辞書
        """
        self.tree.delete(*self.tree.get_children())
        for key, val in yamldict.items():
            if key == "interpreter" or not isinstance(val, dict):
                continue
            ignition = val.get("ignition", "")
            sid = self.tree.insert(
                "", "end", text=key, values=("screen", f"ignition: {ignition}"), open=True
            )
            self._add_categories(sid, val)

    def _add_categories(self, parent: str, node: dict) -> None:
        """
        node 直下の Category / グループを再帰的にツリーへ追加する
        """
        for key, val in node.items():
            if key in Consts.reserved_keys or not isinstance(val, dict):
                continue
            iid = self.tree.insert(
                parent,
                "end",
                text=key,
                values=(self._kind_of(val), self._detail_of(val)),
                open=True,
            )
            # 通常のサブ Category
            self._add_categories(iid, val)
            # recurse ブロック配下の Category
            recurse = val.get("recurse")
            if isinstance(recurse, dict):
                self._add_categories(iid, recurse)

    @staticmethod
    def _kind_of(cat: dict) -> str:
        """
        Category 辞書から種別ラベルを求める
        """
        if "import" in cat:
            return "import"
        for rk in Consts.rule_keys:
            if rk in cat and isinstance(cat[rk], dict):
                return f"{rk}({len(cat[rk])})"
        if "pattern" in cat:
            return "category"
        return "group"

    @staticmethod
    def _detail_of(cat: dict) -> str:
        """
        Category 辞書から詳細 (pattern) 文字列を求める
        """
        if "pattern" in cat:
            grp = f" [grp {cat['capturegrp']}]" if "capturegrp" in cat else ""
            return f"{cat['pattern']}{grp}"
        if "import" in cat:
            return f"import {cat['import']}"
        return ""

    def _count_categories(self, node: dict) -> int:
        """
        node 配下の Category 数 (pattern または import を持つノード) を数える
        """
        count = 0
        for key, val in node.items():
            if key in ("ignition", "common") or not isinstance(val, dict):
                continue
            if "pattern" in val or "import" in val:
                count += 1
            count += self._count_categories(val)
            recurse = val.get("recurse")
            if isinstance(recurse, dict):
                count += self._count_categories(recurse)
        return count

    # -------------------------------------------------------------------------
    # 小物 / テーマ
    # -------------------------------------------------------------------------

    def editor_text(self) -> str:
        """エディタの現在の内容"""
        return self.editor.get("1.0", "end-1c")

    def set_editor_text(self, text: str) -> None:
        """エディタの内容を差し替える"""
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", text)
        self.editor.edit_reset()

    def write_result(self, text: str) -> None:
        """動作プレビュー結果欄を更新する"""
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", text)
        self.result_text.configure(state="disabled")

    def set_status(self, message: str, ok: bool) -> None:
        """状態ラベルを更新する (検証系以外の通知用)"""
        self._status_ok = ok
        self.status_label.configure(foreground=theme.current.ok if ok else theme.current.err)
        self.status_var.set(message)

    @staticmethod
    def _yaml_error(e: yaml.YAMLError) -> str:
        """yaml 例外から行番号付きの簡潔なメッセージを作る"""
        mark = getattr(e, "problem_mark", None)
        if mark is not None:
            return f"{getattr(e, 'problem', '')} ({mark.line + 1} 行目)"
        return str(e)

    def retheme(self) -> None:
        """テーマ切替時に非 ttk 領域と状態色を追従させる"""
        self.status_label.configure(
            foreground=theme.current.ok if self._status_ok else theme.current.err
        )
        self.warning_label.configure(foreground=theme.current.warn)
        widgets.retheme_text(self.editor)
        widgets.retheme_text(self.input_text)
        widgets.retheme_text(self.result_text)

    @property
    def displayer(self):
        """Displayer インスタンス"""
        return self.super_owner.super_owner
