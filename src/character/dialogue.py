"""
セリフ供給の抽象化

会話方式は「メニュー選択 + 定型セリフ」を既定としつつ, 将来的に LLM 応答へ
差し替えられるよう ``DialogueProvider`` を境界として切り出している (ハイブリッド設計).

- YamlDialogueProvider: アクション YAML の定型セリフから決定論的に 1 つ選ぶ
- (将来) LLMDialogueProvider: DialogueContext を素材にプロンプトを組み立てて応答

セリフは自然文なので, プロンプトトークン用の ``<>`` 記法や重み記法は適用しない.
複数候補からの抽選のみ行う.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from hashlib import sha256

from character.models import ActionDef, CharacterSheet
from character.state import CharacterState


@dataclass
class DialogueContext:
    """
    セリフ選択/生成に必要な文脈

    Attributes:
        sheet (CharacterSheet): キャラシート
        state (CharacterState): 直近適用後の状態
        action (ActionDef): 実行アクション
        locked (bool): precondition 未達 (拒否) だったか
        seed (str): 決定論的抽選のためのシード
    """

    sheet: CharacterSheet
    state: CharacterState
    action: ActionDef
    locked: bool
    seed: str


def pick(candidates: list[str], seed: str) -> str:
    """
    候補リストからシードに基づき決定論的に 1 つ選ぶ

    Args:
        candidates (list[str]): 候補
        seed (str): シード

    Returns:
        str: 選ばれた候補 (空なら "")
    """
    if not candidates:
        return ""
    h = sha256(seed.encode()).hexdigest()
    return candidates[int(h, 16) % len(candidates)]


class DialogueProvider(ABC):
    """セリフ供給の抽象基底"""

    @abstractmethod
    def line(self, ctx: DialogueContext) -> str:
        """
        文脈に応じたセリフを 1 つ返す

        Args:
            ctx (DialogueContext): 文脈

        Returns:
            str: セリフ (該当なしなら "")
        """


class YamlDialogueProvider(DialogueProvider):
    """
    アクション YAML の定型セリフから選ぶ既定プロバイダ

    優先順位:
        1. locked (拒否) 時は ``dialogue_locked``
        2. ``dialogue_by`` のパラメータ条件別セリフ (条件成立時)
        3. ``dialogue`` の通常候補
    """

    def line(self, ctx: DialogueContext) -> str:
        action = ctx.action

        if ctx.locked and action.dialogue_locked:
            return pick(action.dialogue_locked, ctx.seed)

        conditional = self._conditional_lines(ctx)
        if conditional:
            return pick(conditional, ctx.seed)

        return pick(action.dialogue, ctx.seed)

    def _conditional_lines(self, ctx: DialogueContext) -> list[str]:
        """
        ``dialogue_by`` を評価し, 成立した条件のセリフ候補をまとめて返す

        書式:
            dialogue_by:
              affection:
                - { in: [71, 100], lines: ["..."] }   # scalar
                - { is: happy,     lines: ["..."] }    # enum

        Args:
            ctx (DialogueContext): 文脈

        Returns:
            list[str]: 成立した候補 (なければ空)
        """
        lines: list[str] = []
        for pname, entries in ctx.action.dialogue_by.items():
            pdef = ctx.sheet.parameters.get(pname)
            if pdef is None:
                continue
            current = ctx.state.params.get(pname)
            for entry in entries:
                cond = {k: v for k, v in entry.items() if k != "lines"}
                if pdef.check(current, cond):
                    lines.extend(str(x) for x in (entry.get("lines") or []))
        return lines
