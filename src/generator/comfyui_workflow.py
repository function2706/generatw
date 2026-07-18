from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, Protocol, get_type_hints

import yaml

from archiver.dataclasses import PicInfo

BACKEND_KEYWORD = "ComfyUIGenerator"


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


@dataclass
class WorkFlowDef:
    """
    ワークフロー定義 (YAML の1セクション分)\n
    パラメータを与えてのノードグラフ構築, および生成結果からの PicInfo 復元を担う
    """

    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    picinfo: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, yamlpath: Path) -> dict[str, "WorkFlowDef"]:
        """
        YAML からワークフロー定義群を読み込む\n
        "backend" キーが "ComfyUIGenerator" でない場合は例外を送出する

        Args:
            yamlpath (Path): YAML パス

        Returns:
            dict[str, WorkFlowDef]: セクション名 (txt2img, img2img 等) -> ワークフロー定義
        """
        with open(yamlpath, encoding="utf-8") as f:
            yamldict: dict = yaml.safe_load(f)

        keyword = yamldict.get("backend")
        if keyword != BACKEND_KEYWORD:
            raise ValueError(f"Invalid backend for workflow YAML {yamlpath}: {keyword}")

        wfdefs: dict[str, WorkFlowDef] = {}
        for name, section in yamldict.items():
            if name == "backend":
                continue
            nodes: dict[str, dict[str, Any]] = section.get("nodes", {})
            idxs = [node_def["idx"] for node_def in nodes.values()]
            if len(idxs) != len(set(idxs)):
                raise ValueError(f"Duplicated node idx in workflow YAML {yamlpath}: {name}")
            wfdefs[name] = cls(nodes=nodes, picinfo=section.get("picinfo", {}))
        return wfdefs

    def _resolve_input(self, value: Any, params: dict[str, Any]) -> Any:
        """
        ノード入力値を解決する\n
        "$xxx" 形式はパラメータ参照, [node_name, port] 形式は同一セクション内の他ノードへの
        リンク, それ以外は静的な値としてそのまま扱う

        Args:
            value (Any): YAML 上の入力値
            params (dict[str, Any]): ビルド時パラメータ

        Returns:
            Any: 解決済みの入力値
        """
        if isinstance(value, str) and value.startswith("$"):
            pname = value[1:]
            if pname not in params:
                raise KeyError(f"Missing parameter for workflow build: {pname}")
            return params[pname]

        if (
            isinstance(value, list)
            and len(value) == 2
            and isinstance(value[0], str)
            and value[0] in self.nodes
        ):
            node_name, port = value
            return [str(self.nodes[node_name]["idx"]), port]

        return value

    def build(self, params: dict[str, Any]) -> WorkFlow:
        """
        パラメータを与えてワークフロー (ノードグラフ) を構築する

        Args:
            params (dict[str, Any]): "$xxx" で参照されるパラメータ

        Returns:
            WorkFlow: 構築されたワークフロー
        """
        workflow = WorkFlow()
        for node_def in self.nodes.values():
            idx = node_def["idx"]
            class_type = node_def["class_type"]
            raw_inputs: dict[str, Any] = node_def.get("inputs", {})
            inputs = {key: self._resolve_input(v, params) for key, v in raw_inputs.items()}
            workflow.add(NodeSkeleton(idx, GenericNode(class_type=class_type, inputs=inputs)))
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
        valid_fields = {f.name for f in fields(PicInfo)}
        type_hints = get_type_hints(PicInfo)
        result: dict[str, Any] = {}

        for key, spec in self.picinfo.items():
            if key not in valid_fields:
                raise KeyError(f"Unknown PicInfo field in picinfo YAML: {key}")

            negate = False
            if isinstance(spec, dict):
                node_name, input_field = spec["from"]
                negate = bool(spec.get("negate", False))
            else:
                node_name, input_field = spec

            node_idx = self.nodes[node_name]["idx"]
            node_data = data.get(str(node_idx), {})
            value = node_data.get("inputs", {}).get(input_field)

            if negate and value is not None:
                value = -value

            field_type = type_hints.get(key)
            if field_type is int:
                value = int(value)
            elif field_type is float:
                value = float(value)

            result[key] = value

        return result
