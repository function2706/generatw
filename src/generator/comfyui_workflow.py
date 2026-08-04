"""
ComfyUI ワークフロー定義 (YAML) のロードと構築

仕様: yamls/workflow_yaml_spec.md
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, Protocol, get_type_hints

import yaml

from archiver.dataclasses import PicInfo
from common.functions import PathConsts

BACKEND_KEYWORD = "ComfyUIGenerator"

# セクション名として使えない予約語
RESERVED_KEYS: tuple[str, ...] = ("backend",)
# ノード定義のキー
NODE_KEYS: tuple[str, ...] = ("idx", "class_type", "inputs")


class WorkFlowSyntaxError(Exception):
    """
    ワークフロー YAML のシンタックスエラー\n
    ロード時に検出される
    """


class NodeBody(Protocol):
    class_type: str
    inputs: object


class NodeSkeleton:
    def __init__(self, nodeidx: int, body: NodeBody):
        self.nodeidx: str = str(nodeidx)
        self.body: NodeBody = body

    def __or__(self, other):
        if isinstance(other, NodeSkeleton):
            return self.todict() | other.todict()
        elif isinstance(other, dict):
            return self.todict() | other
        return NotImplemented

    def __ror__(self, other):
        if isinstance(other, dict):
            return other | self.todict()
        return NotImplemented

    def todict(self) -> dict[str, dict]:
        return {self.nodeidx: asdict(self.body)}


@dataclass
class GenericNode(NodeBody):
    """
    汎用ノード本体\n
    YAML のワークフロー定義から動的に構築されるノードを表す
    """

    class_type: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)


class WorkFlow:
    """
    ワークフロー
    """

    def __init__(self):
        """
        コンストラクタ
        """
        self.nodelist: list[tuple[int, NodeSkeleton]] = []

    def node_of(self, idx: int) -> NodeSkeleton:
        """
        指定のノード番号を持つノードを取得する

        Args:
            idx (int): ノード番号

        Returns:
            str: ノード
        """
        return next((s for i, s in self.nodelist if i == str(idx)), None)

    def add(self, node: NodeSkeleton) -> None:
        """
        ノードを追加する\n
        すでに同じノード番号のノードがある場合は何もしない

        Args:
            node (NodeSkeleton): ノード
        """
        if self.node_of(node.nodeidx) is not None:
            # 追加済ノードは追加しない
            return

        self.nodelist.append((node.nodeidx, node))

    def todict(self) -> dict[str, dict[str, Any]]:
        """
        dict を取得

        Returns:
            dict[str, dict[str, Any]]: dict
        """
        d = {}
        for _, node in self.nodelist:
            d.update(node.todict())
        return d


# =============================================================================
# ノードカタログ
# =============================================================================


class NodeCatalog:
    """
    ノード型定義 (node_catalog.yaml)\n
    リンクのスロット解決と, ロード時の入力検証に用いる
    """

    def __init__(self, nodes: dict[str, dict[str, Any]] = None):
        """
        コンストラクタ

        Args:
            nodes (dict[str, dict[str, Any]]): class_type -> 定義
        """
        self.nodes: dict[str, dict[str, Any]] = nodes or {}

    @classmethod
    def load(cls, yamlpath: Path = None) -> NodeCatalog:
        """
        カタログを読み込む\n
        ファイルが存在しない場合は空のカタログを返す (スロット推論と検証が無効になる)

        Args:
            yamlpath (Path): カタログパス

        Raises:
            WorkFlowSyntaxError: カタログが不正

        Returns:
            NodeCatalog: カタログ
        """
        yamlpath = Path(yamlpath) if yamlpath is not None else PathConsts.node_catalog
        if not yamlpath.exists():
            return cls()

        try:
            with open(yamlpath, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise WorkFlowSyntaxError(f"{yamlpath}: YAML のパースに失敗しました: {e}") from e

        nodes = data.get("nodes")
        if not isinstance(nodes, dict):
            raise WorkFlowSyntaxError(f"{yamlpath}: 'nodes' がありません")

        return cls(nodes=nodes)

    def known(self, class_type: str) -> bool:
        """
        カタログに存在する class_type か
        """
        return class_type in self.nodes

    def outputs(self, class_type: str) -> list[str]:
        """
        出力スロット名のリスト (インデックス順)
        """
        return list(self.nodes.get(class_type, {}).get("outputs") or [])

    def inputs(self, class_type: str) -> dict[str, dict[str, Any]]:
        """
        入力定義
        """
        return dict(self.nodes.get(class_type, {}).get("inputs") or {})

    def is_output(self, class_type: str) -> bool:
        """
        終端ノードか
        """
        return bool(self.nodes.get(class_type, {}).get("is_output", False))

    def is_link_input(self, class_type: str, name: str) -> bool:
        """
        指定の入力がリンクを取るものか\n
        カタログ未登録の class_type では常に False

        Args:
            class_type (str): ノードクラス名
            name (str): 入力名

        Returns:
            bool: True: リンク入力
        """
        return self.inputs(class_type).get(name, {}).get("type") == "link"

    def slot_of(self, class_type: str, slotname: str) -> int | None:
        """
        出力スロット名をインデックスへ変換する\n
        解決できない場合は None

        Args:
            class_type (str): ノードクラス名
            slotname (str): スロット名

        Returns:
            int | None: インデックス
        """
        outputs = self.outputs(class_type)
        return outputs.index(slotname) if slotname in outputs else None

    def infer_slot(self, src_class: str, dst_class: str, dst_input: str) -> int:
        """
        入力の受け入れ型から出力スロットを推論する

        Args:
            src_class (str): 接続元ノードの class_type
            dst_class (str): 接続先ノードの class_type
            dst_input (str): 接続先の入力名

        Raises:
            WorkFlowSyntaxError: 推論できない, または一意でない

        Returns:
            int: 出力スロットインデックス
        """
        accepts = self.inputs(dst_class).get(dst_input, {}).get("accepts") or []
        outputs = self.outputs(src_class)
        if not outputs:
            raise WorkFlowSyntaxError(
                f"接続元 '{src_class}' がカタログ未登録のためスロットを推論できません "
                f"([<ノード名>, <スロット番号>] 形式で明示してください)"
            )
        if not accepts:
            raise WorkFlowSyntaxError(
                f"'{dst_class}' の入力 '{dst_input}' に accepts が定義されていないため"
                f"スロットを推論できません ([<ノード名>, <スロット番号>] 形式で明示してください)"
            )

        matched = [i for i, name in enumerate(outputs) if name in accepts]
        if not matched:
            raise WorkFlowSyntaxError(
                f"型が一致しません ('{src_class}' の出力 {outputs} に "
                f"{accepts} がありません)"
            )
        if len(matched) > 1:
            names = [outputs[i] for i in matched]
            raise WorkFlowSyntaxError(
                f"スロットが一意に定まりません ('{src_class}' の出力 {names} が"
                f"いずれも {accepts} に該当します. スロット名で明示してください)"
            )
        return matched[0]


# =============================================================================
# ワークフロー定義
# =============================================================================


@dataclass(frozen=True)
class Link:
    """
    ノードリンク (解決済)
    """

    node: str
    slot: int


@dataclass(frozen=True)
class Param:
    """
    パラメータプレースホルダ ($xxx)
    """

    name: str


@dataclass(frozen=True)
class PicInfoRef:
    """
    PicInfo 逆引き 1 件
    """

    node: str
    input: str
    negate: bool = False


@dataclass
class WorkFlowDef:
    """
    ワークフロー定義 (YAML の1セクション分)\n
    パラメータを与えてのノードグラフ構築, および生成結果からの PicInfo 復元を担う
    """

    name: str = ""
    # ノード名 -> (idx, class_type, 解決済 inputs)
    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    picinfo: dict[str, PicInfoRef] = field(default_factory=dict)
    # 孤立ノード等の警告 (エラーではない)
    warnings: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, yamlpath: Path, catalog: NodeCatalog = None) -> dict[str, WorkFlowDef]:
        """
        YAML からワークフロー定義群を読み込む\n
        "backend" キーが "ComfyUIGenerator" でない場合はシンタックスエラーとする

        Args:
            yamlpath (Path): YAML パス
            catalog (NodeCatalog): ノードカタログ (省略時は既定パスから読む)

        Raises:
            WorkFlowSyntaxError: YAML が不正

        Returns:
            dict[str, WorkFlowDef]: セクション名 (txt2img, img2img 等) -> ワークフロー定義
        """
        yamlpath = Path(yamlpath)
        if not yamlpath.exists():
            raise WorkFlowSyntaxError(f"{yamlpath}: ファイルが存在しません")

        try:
            with open(yamlpath, encoding="utf-8") as f:
                yamldict = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise WorkFlowSyntaxError(f"{yamlpath}: YAML のパースに失敗しました: {e}") from e

        if not isinstance(yamldict, dict):
            raise WorkFlowSyntaxError(f"{yamlpath}: トップレベルがマッピングではありません")

        keyword = yamldict.get("backend")
        if keyword != BACKEND_KEYWORD:
            raise WorkFlowSyntaxError(
                f"{yamlpath}: 'backend' が '{BACKEND_KEYWORD}' ではありません: {keyword}"
            )

        catalog = catalog if catalog is not None else NodeCatalog.load()

        wfdefs: dict[str, WorkFlowDef] = {}
        for name, section in yamldict.items():
            if name in RESERVED_KEYS:
                continue
            wfdefs[name] = cls._load_section(yamlpath, str(name), section, catalog)

        if not wfdefs:
            raise WorkFlowSyntaxError(f"{yamlpath}: ワークフロー定義がありません")

        return wfdefs

    @classmethod
    def _load_section(
        cls, yamlpath: Path, name: str, section: Any, catalog: NodeCatalog
    ) -> WorkFlowDef:
        """
        1 セクション分を解析し, 検証済の定義を返す

        Args:
            yamlpath (Path): YAML パス (エラーメッセージ用)
            name (str): セクション名
            section (Any): セクション本体
            catalog (NodeCatalog): ノードカタログ

        Raises:
            WorkFlowSyntaxError: セクションが不正

        Returns:
            WorkFlowDef: ワークフロー定義
        """
        where = f"{yamlpath}: {name}"
        if not isinstance(section, dict):
            raise WorkFlowSyntaxError(f"{where}: セクションがマッピングではありません")

        raw_nodes = section.get("nodes")
        if not isinstance(raw_nodes, dict) or not raw_nodes:
            raise WorkFlowSyntaxError(f"{where}: 'nodes' がありません")

        obj = cls(name=name)
        obj._assign_idxs(where, raw_nodes)
        obj._resolve_inputs(where, raw_nodes, catalog)
        obj._validate_inputs(where, catalog)
        obj._detect_cycle(where)
        obj._parse_picinfo(where, section.get("picinfo") or {})
        obj._detect_orphans(catalog)
        return obj

    def _assign_idxs(self, where: str, raw_nodes: dict[str, Any]) -> None:
        """
        ノード番号を確定する\n
        明示された idx を優先し, 省略されたノードには記述順に空き番号を割り当てる

        Args:
            where (str): エラーメッセージ用の位置情報
            raw_nodes (dict[str, Any]): nodes セクション

        Raises:
            WorkFlowSyntaxError: idx が不正または重複
        """
        explicit: dict[str, int] = {}
        for nname, ndef in raw_nodes.items():
            if not isinstance(ndef, dict):
                raise WorkFlowSyntaxError(f"{where}: ノード '{nname}': 定義がマッピングではありません")
            if ndef.get("idx") is None:
                continue

            idx = ndef.get("idx")
            if not isinstance(idx, int) or idx < 1:
                raise WorkFlowSyntaxError(f"{where}: ノード '{nname}': 'idx' は 1 以上の整数です")
            if idx in explicit.values():
                raise WorkFlowSyntaxError(f"{where}: ノード '{nname}': 'idx' {idx} が重複しています")
            explicit[nname] = idx

        nextidx = 1
        for nname, ndef in raw_nodes.items():
            class_type = ndef.get("class_type")
            if not isinstance(class_type, str) or not class_type:
                raise WorkFlowSyntaxError(f"{where}: ノード '{nname}': 'class_type' がありません")

            for key in ndef:
                if key not in NODE_KEYS:
                    raise WorkFlowSyntaxError(
                        f"{where}: ノード '{nname}': 未知のキー '{key}' があります {NODE_KEYS}"
                    )

            if nname in explicit:
                idx = explicit[nname]
            else:
                while nextidx in explicit.values():
                    nextidx += 1
                idx = nextidx
                nextidx += 1

            self.nodes[nname] = {"idx": idx, "class_type": class_type, "inputs": {}}

    def _resolve_inputs(
        self, where: str, raw_nodes: dict[str, Any], catalog: NodeCatalog
    ) -> None:
        """
        inputs をリンク / プレースホルダ / 静的値へ分類し, リンクのスロットを解決する

        Args:
            where (str): エラーメッセージ用の位置情報
            raw_nodes (dict[str, Any]): nodes セクション
            catalog (NodeCatalog): ノードカタログ

        Raises:
            WorkFlowSyntaxError: 記法が不正, またはリンクを解決できない
        """
        for nname, ndef in raw_nodes.items():
            class_type = self.nodes[nname]["class_type"]
            raw_inputs = ndef.get("inputs") or {}
            if not isinstance(raw_inputs, dict):
                raise WorkFlowSyntaxError(f"{where}: ノード '{nname}': 'inputs' がマッピングではありません")

            for key, value in raw_inputs.items():
                pos = f"{where}: ノード '{nname}' の入力 '{key}'"
                self.nodes[nname]["inputs"][key] = self._resolve_value(
                    pos, class_type, key, value, catalog
                )

    def _resolve_value(
        self, pos: str, class_type: str, key: str, value: Any, catalog: NodeCatalog
    ) -> Any:
        """
        入力値 1 つを解決する

        Args:
            pos (str): エラーメッセージ用の位置情報
            class_type (str): ノードクラス名
            key (str): 入力名
            value (Any): YAML 上の値
            catalog (NodeCatalog): ノードカタログ

        Raises:
            WorkFlowSyntaxError: 記法が不正

        Returns:
            Any: Link, Param, または静的値
        """
        # [<ノード名>] / [<ノード名>, <スロット名 | スロット番号>]
        if isinstance(value, list):
            if not 1 <= len(value) <= 2 or not isinstance(value[0], str):
                raise WorkFlowSyntaxError(
                    f"{pos}: リンクは [<ノード名>] か [<ノード名>, <スロット>] で記述します"
                )
            return self._make_link(pos, class_type, key, value[0], value[1:], catalog)

        if isinstance(value, str):
            # $$ は $ のエスケープ
            if value.startswith("$$"):
                return value[1:]
            if value.startswith("$"):
                return Param(name=value[1:])
            # カタログが link 型と宣言している入力は, スカラをノード名として解釈する
            if catalog.is_link_input(class_type, key):
                return self._make_link(pos, class_type, key, value, [], catalog)

        return value

    def _make_link(
        self,
        pos: str,
        class_type: str,
        key: str,
        target: str,
        rest: list[Any],
        catalog: NodeCatalog,
    ) -> Link:
        """
        リンクを構築する (スロット未指定時は型から推論する)

        Args:
            pos (str): エラーメッセージ用の位置情報
            class_type (str): 接続先ノードの class_type
            key (str): 接続先の入力名
            target (str): 接続元ノード名
            rest (list[Any]): スロット指定 (0 or 1 要素)
            catalog (NodeCatalog): ノードカタログ

        Raises:
            WorkFlowSyntaxError: リンク先が存在しない, またはスロットを解決できない

        Returns:
            Link: リンク
        """
        if target not in self.nodes:
            raise WorkFlowSyntaxError(f"{pos}: リンク先ノード '{target}' が存在しません")

        src_class = self.nodes[target]["class_type"]
        if not rest:
            try:
                return Link(node=target, slot=catalog.infer_slot(src_class, class_type, key))
            except WorkFlowSyntaxError as e:
                raise WorkFlowSyntaxError(f"{pos}: {e}") from e

        slot = rest[0]
        if isinstance(slot, bool) or not isinstance(slot, int | str):
            raise WorkFlowSyntaxError(f"{pos}: スロットはスロット名か整数で指定します")
        if isinstance(slot, int):
            return Link(node=target, slot=slot)

        resolved = catalog.slot_of(src_class, slot)
        if resolved is None:
            raise WorkFlowSyntaxError(
                f"{pos}: '{src_class}' に出力スロット '{slot}' がありません "
                f"(カタログ未登録の場合はスロット番号で指定してください)"
            )
        return Link(node=target, slot=resolved)

    def _validate_inputs(self, where: str, catalog: NodeCatalog) -> None:
        """
        カタログと突き合わせて入力名 / 必須 / リンク型 / 選択肢を検証する\n
        カタログ未登録の class_type は検証をスキップし, 警告に記録する

        Args:
            where (str): エラーメッセージ用の位置情報
            catalog (NodeCatalog): ノードカタログ

        Raises:
            WorkFlowSyntaxError: 検証に失敗
        """
        for nname, ndef in self.nodes.items():
            class_type = ndef["class_type"]
            if not catalog.known(class_type):
                self.warnings.append(
                    f"ノード '{nname}': class_type '{class_type}' はカタログに未登録のため"
                    f"検証をスキップしました"
                )
                continue

            defs = catalog.inputs(class_type)
            for key, value in ndef["inputs"].items():
                pos = f"{where}: ノード '{nname}' の入力 '{key}'"
                idef = defs.get(key)
                if idef is None:
                    raise WorkFlowSyntaxError(f"{pos}: '{class_type}' に存在しない入力名です")

                if idef.get("type") == "link":
                    if not isinstance(value, Link):
                        raise WorkFlowSyntaxError(f"{pos}: リンクを指定する必要があります")
                    accepts = idef.get("accepts")
                    outputs = catalog.outputs(self.nodes[value.node]["class_type"])
                    if accepts and outputs and value.slot < len(outputs):
                        actual = outputs[value.slot]
                        if actual not in accepts:
                            raise WorkFlowSyntaxError(
                                f"{pos}: 型が一致しません (期待: {accepts}, 実際: '{actual}')"
                            )
                    continue

                if isinstance(value, Link):
                    raise WorkFlowSyntaxError(f"{pos}: この入力はリンクを受け付けません")

                # 静的値のみ検証する (プレースホルダの中身はビルド時にしか分からない)
                choices = idef.get("choices")
                if not isinstance(value, Param) and choices and value not in choices:
                    raise WorkFlowSyntaxError(f"{pos}: '{value}' は {choices} にありません")

            for key, idef in defs.items():
                if idef.get("required") and key not in ndef["inputs"]:
                    raise WorkFlowSyntaxError(
                        f"{where}: ノード '{nname}': 必須の入力 '{key}' がありません"
                    )

    def _detect_cycle(self, where: str) -> None:
        """
        循環参照を検出する

        Args:
            where (str): エラーメッセージ用の位置情報

        Raises:
            WorkFlowSyntaxError: 循環参照を検出
        """
        # 0: 未訪問, 1: 探索中, 2: 完了
        state: dict[str, int] = {name: 0 for name in self.nodes}

        def visit(name: str, stack: list[str]) -> None:
            if state[name] == 1:
                raise WorkFlowSyntaxError(
                    f"{where}: 循環参照を検出しました: {' -> '.join([*stack, name])}"
                )
            if state[name] == 2:
                return

            state[name] = 1
            for value in self.nodes[name]["inputs"].values():
                if isinstance(value, Link):
                    visit(value.node, [*stack, name])
            state[name] = 2

        for name in self.nodes:
            visit(name, [])

    def _parse_picinfo(self, where: str, raw: Any) -> None:
        """
        picinfo を解析する

        Args:
            where (str): エラーメッセージ用の位置情報
            raw (Any): picinfo セクション

        Raises:
            WorkFlowSyntaxError: picinfo が不正
        """
        if not isinstance(raw, dict):
            raise WorkFlowSyntaxError(f"{where}: 'picinfo' がマッピングではありません")

        valid_fields = {f.name for f in fields(PicInfo)}
        for key, spec in raw.items():
            pos = f"{where}: picinfo '{key}'"
            if key not in valid_fields:
                raise WorkFlowSyntaxError(f"{pos}: PicInfo に存在しないフィールドです")

            negate = False
            if isinstance(spec, dict):
                accessor = spec.get("from")
                negate = bool(spec.get("negate", False))
            else:
                accessor = spec

            if (
                not isinstance(accessor, list)
                or len(accessor) != 2
                or not all(isinstance(e, str) for e in accessor)
            ):
                raise WorkFlowSyntaxError(f"{pos}: [<ノード名>, <入力名>] 形式で記述します")

            node_name, input_name = accessor
            if node_name not in self.nodes:
                raise WorkFlowSyntaxError(f"{pos}: ノード '{node_name}' が存在しません")
            if input_name not in self.nodes[node_name]["inputs"]:
                raise WorkFlowSyntaxError(
                    f"{pos}: ノード '{node_name}' に入力 '{input_name}' がありません"
                )
            if isinstance(self.nodes[node_name]["inputs"][input_name], Link):
                raise WorkFlowSyntaxError(f"{pos}: リンクを指す入力は参照できません")

            self.picinfo[key] = PicInfoRef(node=node_name, input=input_name, negate=negate)

    def _detect_orphans(self, catalog: NodeCatalog) -> None:
        """
        孤立ノードを警告として記録する

        Args:
            catalog (NodeCatalog): ノードカタログ
        """
        referred = {
            value.node
            for ndef in self.nodes.values()
            for value in ndef["inputs"].values()
            if isinstance(value, Link)
        }
        for nname, ndef in self.nodes.items():
            if nname in referred or catalog.is_output(ndef["class_type"]):
                continue
            self.warnings.append(
                f"ノード '{nname}' (idx={ndef['idx']}) はどこからも参照されていません"
            )

    @property
    def placeholders(self) -> list[str]:
        """
        本定義が要求するパラメータ名 (重複なし, 出現順)

        Returns:
            list[str]: パラメータ名のリスト
        """
        found: list[str] = []
        for ndef in self.nodes.values():
            for value in ndef["inputs"].values():
                if isinstance(value, Param) and value.name not in found:
                    found.append(value.name)
        return found

    def build(self, params: dict[str, Any]) -> WorkFlow:
        """
        パラメータを与えてワークフロー (ノードグラフ) を構築する

        Args:
            params (dict[str, Any]): "$xxx" で参照されるパラメータ

        Raises:
            KeyError: 要求されたパラメータが渡されていない

        Returns:
            WorkFlow: 構築されたワークフロー
        """
        workflow = WorkFlow()
        for ndef in self.nodes.values():
            inputs: dict[str, Any] = {}
            for key, value in ndef["inputs"].items():
                if isinstance(value, Link):
                    inputs[key] = [str(self.nodes[value.node]["idx"]), value.slot]
                elif isinstance(value, Param):
                    if value.name not in params:
                        raise KeyError(f"Missing parameter for workflow build: {value.name}")
                    inputs[key] = params[value.name]
                else:
                    inputs[key] = value

            workflow.add(
                NodeSkeleton(
                    ndef["idx"], GenericNode(class_type=ndef["class_type"], inputs=inputs)
                )
            )
        return workflow

    def read_picinfo(self, data: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """
        生成結果のワークフロー dict (ComfyUI が PNG メタデータの "prompt" として返すものと
        同じ形) から, PicInfo 用の値を picinfo 定義に従って抽出する

        Args:
            data (dict[str, dict[str, Any]]): ワークフロー dict (キーはノード番号の文字列)

        Returns:
            dict[str, Any]: PicInfo フィールド名 -> 値 (PicInfo のフィールド型に変換済み)
        """
        type_hints = get_type_hints(PicInfo)
        result: dict[str, Any] = {}

        for key, ref in self.picinfo.items():
            node_data = data.get(str(self.nodes[ref.node]["idx"]), {})
            value = (node_data.get("inputs") or {}).get(ref.input)
            if value is None:
                continue

            if ref.negate:
                value = -value

            field_type = type_hints.get(key)
            if field_type is int:
                value = int(value)
            elif field_type is float:
                value = float(value)

            result[key] = value

        return result


@dataclass
class WorkFlowYamlSummary:
    """
    ワークフロー YAML の走査結果 1 件
    """

    path: Path
    sections: list[str] = field(default_factory=list)
    error: str = ""

    @property
    def label(self) -> str:
        """
        UI 表示用のラベル
        """
        return self.path.name if not self.error else f"{self.path.name} (エラー)"


def scan_workflow_yamls(
    dirpath: Path = None, catalog: NodeCatalog = None
) -> list[WorkFlowYamlSummary]:
    """
    ディレクトリ内のワークフロー YAML (backend キーを持つもの) を走査する\n
    不正なファイルは error 付きで返す

    Args:
        dirpath (Path): 走査先ディレクトリ
        catalog (NodeCatalog): ノードカタログ

    Returns:
        list[WorkFlowYamlSummary]: 走査結果
    """
    dirpath = Path(dirpath) if dirpath is not None else PathConsts.yaml_dir
    if not dirpath.exists():
        return []

    catalog = catalog if catalog is not None else NodeCatalog.load()

    results: list[WorkFlowYamlSummary] = []
    for path in sorted(dirpath.glob("*.yaml")):
        try:
            with open(path, encoding="utf-8") as f:
                head = yaml.safe_load(f) or {}
        except (yaml.YAMLError, OSError):
            continue

        if not isinstance(head, dict) or head.get("backend") != BACKEND_KEYWORD:
            # ワークフロー YAML ではない (プロンプトルール YAML 等)
            continue

        try:
            wfdefs = WorkFlowDef.load(path, catalog)
            results.append(WorkFlowYamlSummary(path=path, sections=list(wfdefs)))
        except WorkFlowSyntaxError as e:
            results.append(WorkFlowYamlSummary(path=path, error=str(e)))

    return results
