"""
キャラクターシート / アクション / パラメータ定義のデータ構造と YAML ローダ

YAML スキーマの詳細は ``yamls/character_yaml_spec.md`` を参照.
拡張は基本的に YAML の追記のみで完結するよう設計している.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


def parse_pn(spec: object) -> tuple[str, str]:
    """
    プロンプト指定を (positive, negative) の文字列ペアに正規化する

    許容する記法:
        - 文字列: positive のみ (例: ``"smile, blush"``)
        - dict:   ``{positive: ..., negative: ...}`` (片方のみも可)

    Args:
        spec (object): プロンプト指定

    Returns:
        tuple[str, str]: (positive, negative)
    """
    if spec is None:
        return "", ""
    if isinstance(spec, str):
        return spec, ""
    if isinstance(spec, dict):
        return str(spec.get("positive", "") or ""), str(spec.get("negative", "") or "")
    return "", ""


@dataclass
class PromptMap:
    """
    パラメータの現在値をプロンプト文字列へ写像する規則

    - maps: 値 (enum 値や文字列) -> (positive, negative)
    - intervals: 数値の閉区間 [lo, hi] -> (positive, negative) (scalar 用, 複数ヒット可)
    """

    maps: dict[str, tuple[str, str]] = field(default_factory=dict)
    intervals: list[tuple[float, float, str, str]] = field(default_factory=list)

    def resolve(self, value: object) -> tuple[list[str], list[str]]:
        """
        現在値に対応する positive/negative プロンプト片のリストを返す

        Args:
            value (object): パラメータの現在値

        Returns:
            tuple[list[str], list[str]]: (positive 片リスト, negative 片リスト)
        """
        pos: list[str] = []
        neg: list[str] = []

        key = str(value)
        if key in self.maps:
            p, n = self.maps[key]
            if p:
                pos.append(p)
            if n:
                neg.append(n)

        try:
            num = float(value)
        except (TypeError, ValueError):
            num = None
        if num is not None:
            for lo, hi, p, n in self.intervals:
                if lo <= num <= hi:
                    if p:
                        pos.append(p)
                    if n:
                        neg.append(n)

        return pos, neg

    @classmethod
    def fromdict(cls, d: dict | None) -> PromptMap:
        """
        ``prompt`` キー配下の dict から PromptMap を構築する

        Args:
            d (dict | None): ``{maps: {...}}`` や ``{intervals: [...]}`` 形式の dict

        Returns:
            PromptMap: 構築結果 (未指定時は空マップ)
        """
        if not d:
            return cls()

        maps: dict[str, tuple[str, str]] = {}
        for k, v in (d.get("maps") or {}).items():
            maps[str(k)] = parse_pn(v)

        intervals: list[tuple[float, float, str, str]] = []
        for item in d.get("intervals") or []:
            rng = item.get("in") or item.get("range")
            if not rng or len(rng) != 2:
                continue
            p, n = parse_pn(item)
            intervals.append((float(rng[0]), float(rng[1]), p, n))

        return cls(maps=maps, intervals=intervals)


SCALAR = "scalar"
ENUM = "enum"


@dataclass
class ParameterDef:
    """
    内部パラメータの定義

    Attributes:
        name (str): パラメータ ID
        label (str): 表示名
        kind (str): "scalar" (数値) または "enum" (離散値)
        init (object): 初期値
        minv / maxv (float): scalar の下限・上限
        values (list[str]): enum の取りうる値 (順序は表示順)
        prompt_map (PromptMap): 値 -> プロンプトの写像
    """

    name: str
    label: str
    kind: str
    init: object
    minv: float = 0.0
    maxv: float = 100.0
    values: list[str] = field(default_factory=list)
    prompt_map: PromptMap = field(default_factory=PromptMap)

    def clamp(self, value: object) -> object:
        """
        値を定義域に収める

        Args:
            value (object): 値

        Returns:
            object: 収めた値 (enum で未知値なら init)
        """
        if self.kind == SCALAR:
            try:
                num = float(value)
            except (TypeError, ValueError):
                return self.init
            num = max(self.minv, min(self.maxv, num))
            # 整数レンジは整数に丸める
            if float(self.minv).is_integer() and float(self.maxv).is_integer():
                return int(round(num))
            return num
        if self.kind == ENUM:
            return value if value in self.values else self.init
        return value

    def apply_effect(self, current: object, effect: object) -> object:
        """
        アクションの effect を現在値へ適用した新しい値を返す

        scalar:
            - 数値 / "+n" / "-n" : 相対変化
            - "=n"               : 絶対代入
        enum:
            - 文字列             : その値へ設定

        Args:
            current (object): 現在値
            effect (object): 変化指定

        Returns:
            object: 適用後の値 (clamp 済み)
        """
        if self.kind == SCALAR:
            if isinstance(effect, str) and effect.strip().startswith("="):
                return self.clamp(float(effect.strip()[1:]))
            try:
                return self.clamp(float(current) + float(effect))
            except (TypeError, ValueError):
                return self.clamp(current)
        if self.kind == ENUM:
            return self.clamp(effect)
        return current

    def check(self, current: object, cond: dict) -> bool:
        """
        precondition (前提条件) を満たすか

        scalar: ``{min: x, max: y}``\n
        enum:   ``{is: v}`` または ``{in: [v1, v2, ...]}``

        Args:
            current (object): 現在値
            cond (dict): 条件

        Returns:
            bool: 満たすなら True
        """
        if self.kind == SCALAR:
            try:
                num = float(current)
            except (TypeError, ValueError):
                return False
            if "min" in cond and num < float(cond["min"]):
                return False
            if "max" in cond and num > float(cond["max"]):
                return False
            if "in" in cond:
                rng = cond["in"]
                if not (float(rng[0]) <= num <= float(rng[1])):
                    return False
            return True
        if self.kind == ENUM:
            if "is" in cond and current != cond["is"]:
                return False
            if "in" in cond and current not in cond["in"]:
                return False
            return True
        return True

    @classmethod
    def fromdict(cls, name: str, d: dict) -> ParameterDef:
        """
        パラメータ定義 dict から ParameterDef を構築する

        Args:
            name (str): パラメータ ID
            d (dict): 定義 dict

        Returns:
            ParameterDef: 構築結果
        """
        kind = d.get("type", SCALAR)
        prompt_map = PromptMap.fromdict(d.get("prompt"))
        label = d.get("label", name)

        if kind == ENUM:
            values = [str(v) for v in (d.get("values") or [])]
            init = d.get("init", values[0] if values else "")
            return cls(
                name=name, label=label, kind=ENUM, init=init, values=values, prompt_map=prompt_map
            )

        # scalar
        rng = d.get("range", [0, 100])
        minv, maxv = float(rng[0]), float(rng[1])
        init = d.get("init", minv)
        return cls(
            name=name,
            label=label,
            kind=SCALAR,
            init=init,
            minv=minv,
            maxv=maxv,
            prompt_map=prompt_map,
        )


@dataclass
class WardrobeItem:
    """着せ替え候補 (衣装)"""

    key: str
    label: str
    positive: str = ""
    negative: str = ""


@dataclass
class CharacterSheet:
    """
    キャラクター定義 (1 キャラ = 1 YAML)

    Attributes:
        char_id (str): キャラ ID (状態ファイル名や記録キーに使用)
        display_name (str): 表示名
        base_pos / base_neg (str): 基本容姿プロンプト
        common_pos / common_neg (str): 末尾に常時付与する共通プロンプト
        wardrobe (dict[str, WardrobeItem]): 着せ替え候補 (挿入順)
        init_outfit (str): 初期衣装キー
        parameters (dict[str, ParameterDef]): 内部パラメータ (挿入順=表示順)
        source_path (Path): 読み込み元 YAML
    """

    char_id: str
    display_name: str
    base_pos: str = ""
    base_neg: str = ""
    common_pos: str = ""
    common_neg: str = ""
    wardrobe: dict[str, WardrobeItem] = field(default_factory=dict)
    init_outfit: str = ""
    parameters: dict[str, ParameterDef] = field(default_factory=dict)
    persona: str = ""  # 参照する性格・口調 (personas.yaml の ID)
    source_path: Path | None = None

    @classmethod
    def load(cls, path: Path) -> CharacterSheet:
        """
        キャラクター YAML を読み込む

        Args:
            path (Path): YAML パス

        Returns:
            CharacterSheet: 構築結果
        """
        path = Path(path)
        with open(path, encoding="utf-8") as f:
            d: dict = yaml.safe_load(f) or {}

        char_id = str(d.get("character") or path.stem)
        base_pos, base_neg = parse_pn(d.get("base"))
        common_pos, common_neg = parse_pn(d.get("common"))

        wardrobe: dict[str, WardrobeItem] = {}
        for key, item in (d.get("wardrobe") or {}).items():
            pos, neg = parse_pn(item)
            label = item.get("label", key) if isinstance(item, dict) else key
            wardrobe[str(key)] = WardrobeItem(
                key=str(key), label=str(label), positive=pos, negative=neg
            )

        init_outfit = str(d.get("init_outfit") or (next(iter(wardrobe), "")))

        parameters: dict[str, ParameterDef] = {}
        for name, pdef in (d.get("parameters") or {}).items():
            parameters[str(name)] = ParameterDef.fromdict(str(name), pdef or {})

        return cls(
            char_id=char_id,
            display_name=str(d.get("display_name") or char_id),
            base_pos=base_pos,
            base_neg=base_neg,
            common_pos=common_pos,
            common_neg=common_neg,
            wardrobe=wardrobe,
            init_outfit=init_outfit,
            parameters=parameters,
            persona=str(d.get("persona") or ""),
            source_path=path,
        )


NORMAL = "normal"
WARDROBE = "wardrobe"


@dataclass
class ActionDef:
    """
    アクション定義 (挨拶 / 着せ替え / スキンシップ 等)

    Attributes:
        action_id (str): アクション ID
        label (str): ボタン表示名
        kind (str): "normal" または "wardrobe" (着せ替え選択 UI を伴う)
        scene_pos / scene_neg (str): このアクション実行時に一時付与するプロンプト
        effects (dict): パラメータ ID -> 変化指定
        precondition (dict): パラメータ ID -> 条件 dict
        dialogue (list[str]): セリフ候補
        dialogue_locked (list[str]): precondition 未達時のセリフ候補
        dialogue_by (dict): パラメータ ID -> 条件別セリフ候補リスト
    """

    action_id: str
    label: str
    kind: str = NORMAL
    scene_pos: str = ""
    scene_neg: str = ""
    effects: dict[str, object] = field(default_factory=dict)
    precondition: dict[str, dict] = field(default_factory=dict)
    dialogue: list[str] = field(default_factory=list)
    dialogue_locked: list[str] = field(default_factory=list)
    dialogue_by: dict[str, list[dict]] = field(default_factory=dict)

    @classmethod
    def fromdict(cls, d: dict) -> ActionDef:
        """
        アクション定義 dict から ActionDef を構築する

        Args:
            d (dict): 定義 dict

        Returns:
            ActionDef: 構築結果
        """
        scene_pos, scene_neg = parse_pn(d.get("scene"))
        return cls(
            action_id=str(d.get("id")),
            label=str(d.get("label") or d.get("id")),
            kind=str(d.get("kind") or NORMAL),
            scene_pos=scene_pos,
            scene_neg=scene_neg,
            effects=dict(d.get("effects") or {}),
            precondition=dict(d.get("precondition") or {}),
            dialogue=[str(x) for x in (d.get("dialogue") or [])],
            dialogue_locked=[str(x) for x in (d.get("dialogue_locked") or [])],
            dialogue_by=dict(d.get("dialogue_by") or {}),
        )


@dataclass
class ActionSet:
    """アクション定義の集合 (yamls/actions.yaml)"""

    actions: list[ActionDef] = field(default_factory=list)
    source_path: Path | None = None

    def get(self, action_id: str) -> ActionDef | None:
        return next((a for a in self.actions if a.action_id == action_id), None)

    @classmethod
    def load(cls, path: Path) -> ActionSet:
        """
        アクション YAML を読み込む

        Args:
            path (Path): YAML パス

        Returns:
            ActionSet: 構築結果
        """
        path = Path(path)
        with open(path, encoding="utf-8") as f:
            d: dict = yaml.safe_load(f) or {}
        actions = [ActionDef.fromdict(a) for a in (d.get("actions") or [])]
        return cls(actions=actions, source_path=path)


@dataclass
class PersonaLines:
    """
    1 アクション分の, ペルソナ固有のセリフ

    Attributes:
        lines (list[str]): 通常セリフ候補
        locked (list[str]): precondition 未達時のセリフ候補
        by (dict[str, list[dict]]): パラメータ条件別セリフ (ActionDef.dialogue_by と同形式)
    """

    lines: list[str] = field(default_factory=list)
    locked: list[str] = field(default_factory=list)
    by: dict[str, list[dict]] = field(default_factory=dict)

    @classmethod
    def fromobj(cls, obj: object) -> PersonaLines:
        """
        リスト (通常セリフのみ) または dict (lines/locked/by) から構築する

        Args:
            obj (object): セリフ定義

        Returns:
            PersonaLines: 構築結果
        """
        if isinstance(obj, list):
            return cls(lines=[str(x) for x in obj])
        if isinstance(obj, dict):
            return cls(
                lines=[str(x) for x in (obj.get("lines") or [])],
                locked=[str(x) for x in (obj.get("locked") or [])],
                by=dict(obj.get("by") or {}),
            )
        return cls()


@dataclass
class Persona:
    """
    性格・口調の属性 (幼馴染系 / お嬢様系 など)

    Attributes:
        persona_id (str): ペルソナ ID
        label (str): 表示名
        description (str): 説明
        dialogue (dict[str, PersonaLines]): アクション ID -> セリフ
    """

    persona_id: str
    label: str = ""
    description: str = ""
    dialogue: dict[str, PersonaLines] = field(default_factory=dict)

    def lines_for(self, action_id: str) -> PersonaLines | None:
        return self.dialogue.get(action_id)


@dataclass
class PersonaSet:
    """ペルソナ定義の集合 (yamls/personas.yaml)"""

    personas: dict[str, Persona] = field(default_factory=dict)
    source_path: Path | None = None

    def get(self, persona_id: str) -> Persona | None:
        return self.personas.get(persona_id)

    @property
    def metas(self) -> list[tuple[str, str]]:
        """(persona_id, label) の一覧 (UI 用)"""
        return [(p.persona_id, p.label or p.persona_id) for p in self.personas.values()]

    @classmethod
    def load(cls, path: Path) -> PersonaSet:
        """
        ペルソナ YAML を読み込む

        Args:
            path (Path): YAML パス

        Returns:
            PersonaSet: 構築結果
        """
        path = Path(path)
        with open(path, encoding="utf-8") as f:
            d: dict = yaml.safe_load(f) or {}

        personas: dict[str, Persona] = {}
        for pid, pdef in (d.get("personas") or {}).items():
            pdef = pdef or {}
            dialogue = {
                str(aid): PersonaLines.fromobj(entry)
                for aid, entry in (pdef.get("dialogue") or {}).items()
            }
            personas[str(pid)] = Persona(
                persona_id=str(pid),
                label=str(pdef.get("label") or pid),
                description=str(pdef.get("description") or ""),
                dialogue=dialogue,
            )
        return cls(personas=personas, source_path=path)
