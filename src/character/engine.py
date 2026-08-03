"""
キャラクターエンジン

キャラシート + アクション定義 + 実行時状態 + セリフプロバイダを束ね,
アクション適用 (状態更新 -> Prompt 構築 -> セリフ確定) を担う.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from character.dialogue import DialogueContext, DialogueProvider, YamlDialogueProvider
from character.models import WARDROBE, ActionDef, ActionSet, CharacterSheet
from character.state import CharacterState
from common.atoms import CategoryPath, Prompt, PromptParts, TokenExpr


@dataclass
class ActionResult:
    """
    アクション適用の結果

    Attributes:
        positive (str): 生成用ポジティブプロンプト文字列
        negative (str): 生成用ネガティブプロンプト文字列
        dialogue (str): 表示するセリフ
        locked (bool): precondition 未達で拒否されたか
        action_id (str): 実行アクション ID
    """

    positive: str = ""
    negative: str = ""
    dialogue: str = ""
    locked: bool = False
    action_id: str = ""


class CharacterEngine:
    """
    1 キャラクター分の状態遷移とプロンプト構築を司るエンジン
    """

    def __init__(
        self,
        sheet: CharacterSheet,
        actions: ActionSet,
        state: CharacterState,
        dialogue_provider: DialogueProvider | None = None,
    ):
        """
        コンストラクタ

        Args:
            sheet (CharacterSheet): キャラシート
            actions (ActionSet): アクション定義集合
            state (CharacterState): 実行時状態
            dialogue_provider (DialogueProvider): セリフプロバイダ (既定: YAML 定型)
        """
        self.sheet = sheet
        self.actions = actions
        self.state = state
        self.dialogue = dialogue_provider or YamlDialogueProvider()

        self._counter = 0  # アクションごとに増やし, <> 抽選のバリエーションを生む
        self._last_pos = ""
        self._last_neg = ""

    # ------------------------------------------------------------------ #
    # 状態遷移
    # ------------------------------------------------------------------ #
    def precondition_ok(self, action: ActionDef) -> bool:
        """
        アクションの前提条件を満たすか

        Args:
            action (ActionDef): アクション

        Returns:
            bool: 満たすなら True
        """
        for pname, cond in action.precondition.items():
            pdef = self.sheet.parameters.get(pname)
            if pdef is None:
                continue
            if not pdef.check(self.state.params.get(pname), cond):
                return False
        return True

    def _apply_effects(self, action: ActionDef) -> None:
        """
        アクションの effect を状態へ適用する

        Args:
            action (ActionDef): アクション
        """
        for pname, effect in action.effects.items():
            pdef = self.sheet.parameters.get(pname)
            if pdef is None:
                continue
            self.state.params[pname] = pdef.apply_effect(self.state.params.get(pname), effect)

    def apply_action(self, action_id: str, wardrobe_key: str | None = None) -> ActionResult | None:
        """
        アクションを適用し, 生成プロンプトとセリフを確定する

        precondition 未達の場合は状態を変えず (locked), scene も付与しない.
        kind=wardrobe のアクションは wardrobe_key で衣装を切り替える.

        Args:
            action_id (str): アクション ID
            wardrobe_key (str | None): 着せ替え先の衣装キー

        Returns:
            ActionResult | None: 結果 (未知アクションなら None)
        """
        action = self.actions.get(action_id)
        if action is None:
            return None

        locked = not self.precondition_ok(action)

        if not locked:
            self._apply_effects(action)
            if action.kind == WARDROBE and wardrobe_key and wardrobe_key in self.sheet.wardrobe:
                self.state.outfit = wardrobe_key

        self._counter += 1
        pos, neg = self._build_strs(action if not locked else None)
        self._last_pos, self._last_neg = pos, neg

        line = self.dialogue.line(
            DialogueContext(
                sheet=self.sheet,
                state=self.state,
                action=action,
                locked=locked,
                seed=f"{self.sheet.char_id}#{action_id}#{self._counter}",
            )
        )

        return ActionResult(
            positive=pos, negative=neg, dialogue=line, locked=locked, action_id=action_id
        )

    def reset_state(self) -> None:
        """状態を初期値へ戻す"""
        self.state = CharacterState.initial(self.sheet)
        self._counter = 0
        self.refresh_prompt()

    # ------------------------------------------------------------------ #
    # プロンプト構築
    # ------------------------------------------------------------------ #
    def refresh_prompt(self) -> tuple[str, str]:
        """
        現在状態のみ (アクション scene なし) からプロンプトを組み直してキャッシュする\n
        キャラ選択直後や着せ替え反映後の「素立ち」表示に使う

        Returns:
            tuple[str, str]: (positive, negative)
        """
        self._counter += 1
        self._last_pos, self._last_neg = self._build_strs(None)
        return self._last_pos, self._last_neg

    def build_prompt(self, action: ActionDef | None) -> Prompt:
        """
        現在状態 (+ 任意のアクション scene) から Prompt を構築する

        構築順: base -> 衣装 -> 各パラメータ -> action.scene -> common\n
        各プロンプト文字列は TokenExpr を通し, ``<a|b>`` の確率選択を確定させる.

        Args:
            action (ActionDef | None): アクション (scene 付与用, None なら素立ち)

        Returns:
            Prompt: 構築結果
        """
        prompt = Prompt(screen_id=self.sheet.char_id)
        seed = f"{self.sheet.char_id}#{self._counter}"

        def add(pos_text: str, neg_text: str, path: tuple[str, ...]) -> None:
            cpath = CategoryPath(path)
            if pos_text:
                toks = TokenExpr.make(pos_text, cpath).confirm(f"{seed}#pos#{path}")
                if toks:
                    prompt.positive.append(PromptParts(path=cpath, tokens=toks))
            if neg_text:
                toks = TokenExpr.make(neg_text, cpath).confirm(f"{seed}#neg#{path}")
                if toks:
                    prompt.negative.append(PromptParts(path=cpath, tokens=toks))

        add(self.sheet.base_pos, self.sheet.base_neg, ("base",))

        item = self.sheet.wardrobe.get(self.state.outfit)
        if item is not None:
            add(item.positive, item.negative, ("outfit",))

        for pname, pdef in self.sheet.parameters.items():
            pos_list, neg_list = pdef.prompt_map.resolve(self.state.params.get(pname))
            add(",".join(pos_list), ",".join(neg_list), ("param", pname))

        if action is not None:
            add(action.scene_pos, action.scene_neg, ("scene",))

        add(self.sheet.common_pos, self.sheet.common_neg, ("common",))
        return prompt

    def _build_strs(self, action: ActionDef | None) -> tuple[str, str]:
        """
        build_prompt の結果をカンマ連結の (positive, negative) 文字列へ変換する

        Args:
            action (ActionDef | None): アクション

        Returns:
            tuple[str, str]: (positive, negative)
        """
        prompt = self.build_prompt(action)
        pos = ",".join(t.to_str() for parts in prompt.positive for t in parts.tokens)
        neg = ",".join(t.to_str() for parts in prompt.negative for t in parts.tokens)
        return pos, neg

    # ------------------------------------------------------------------ #
    # 参照
    # ------------------------------------------------------------------ #
    @property
    def last_strs(self) -> tuple[str, str]:
        """直近に構築した (positive, negative)"""
        return self._last_pos, self._last_neg
