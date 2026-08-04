"""
セリフ供給の抽象化

会話方式は「メニュー選択 + 定型セリフ」を既定としつつ, 将来的に LLM 応答へ
差し替えられるよう ``DialogueProvider`` を境界として切り出している (ハイブリッド設計).

セリフはキャラの **ペルソナ (性格・口調)** に紐づく. アクション YAML の ``dialogue`` は
ペルソナが該当セリフを持たない場合のフォールバックとして機能する.

- YamlDialogueProvider: ペルソナ (なければアクション) の定型セリフから決定論的に 1 つ選ぶ
- (将来) LLMDialogueProvider: DialogueContext を素材にプロンプトを組み立てて応答

セリフは自然文なので, プロンプトトークン用の ``<>`` 記法や重み記法は適用しない.
複数候補からの抽選のみ行う.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from hashlib import sha256

from character.models import ActionDef, CharacterSheet, Persona
from character.state import CharacterState


@dataclass
class DialogueContext:
    """
    セリフ選択/生成に必要な文脈

    Attributes:
        sheet (CharacterSheet): キャラシート
        state (CharacterState): 直近適用後の状態
        action (ActionDef): 実行アクション
        persona (Persona | None): 参照ペルソナ (未設定なら None)
        locked (bool): precondition 未達 (拒否) だったか
        seed (str): 決定論的抽選のためのシード
    """

    sheet: CharacterSheet
    state: CharacterState
    action: ActionDef
    persona: Persona | None
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
    ペルソナ (なければアクション) の定型セリフから選ぶ既定プロバイダ

    優先順位:
        1. locked (拒否) 時は locked 候補
        2. パラメータ条件別セリフ (条件成立時)
        3. 通常候補

    各段でまずペルソナのセリフを見て, 無ければアクション YAML のセリフにフォールバックする.
    """

    def line(self, ctx: DialogueContext) -> str:
        action = ctx.action
        pl = ctx.persona.lines_for(action.action_id) if ctx.persona is not None else None

        if ctx.locked:
            locked = (pl.locked if pl and pl.locked else action.dialogue_locked)
            return pick(locked, ctx.seed)

        by = pl.by if pl and pl.by else action.dialogue_by
        conditional = self._conditional_lines(ctx, by)
        if conditional:
            return pick(conditional, ctx.seed)

        normal = (pl.lines if pl and pl.lines else action.dialogue)
        return pick(normal, ctx.seed)

    def _conditional_lines(self, ctx: DialogueContext, by: dict[str, list[dict]]) -> list[str]:
        """
        条件別セリフ定義を評価し, 成立した条件のセリフ候補をまとめて返す

        書式:
            <param>:
              - { in: [71, 100], lines: ["..."] }   # scalar
              - { is: happy,     lines: ["..."] }    # enum

        Args:
            ctx (DialogueContext): 文脈
            by (dict): パラメータ ID -> 条件別セリフ定義

        Returns:
            list[str]: 成立した候補 (なければ空)
        """
        lines: list[str] = []
        for pname, entries in by.items():
            pdef = ctx.sheet.parameters.get(pname)
            if pdef is None:
                continue
            current = ctx.state.params.get(pname)
            for entry in entries:
                cond = {k: v for k, v in entry.items() if k != "lines"}
                if pdef.check(current, cond):
                    lines.extend(str(x) for x in (entry.get("lines") or []))
        return lines
