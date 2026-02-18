"""
Prompt 解釈クラス
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from parser.prompter import (
    CategoryPath,
    Prompt,
    Prompter,
    PromptParts,
    Token,
)


@dataclass
class PromptSet:
    positive: Prompt = field(default_factory=Prompt)
    negative: Prompt = field(default_factory=Prompt)


class Interpreter(ABC):
    """
    クリップボード監視, ステータス記録クラス
    """

    def __init__(
        self,
        yamlpath: Path,
    ):
        """
        コンストラクタ

        Args:
            yamlpath (Path): YAML パス
        """
        self.prompter: Prompter = None
        self.switch_prompter(yamlpath)

    @classmethod
    def keyword(cls) -> str:
        """
        キーワード (YAML の "interpreter" キーの値との照合値)を取得する

        Returns:
            str: キーワード_
        """
        return cls.__name__

    @property
    @abstractmethod
    def category_list(self) -> list[CategoryPath]:
        """
        カテゴリーリストを取得する\n
        リストの順序はプロンプト化における優先順位を表す

        Returns:
            list[CategoryPath]: カテゴリーリスト
        """
        pass

    def switch_prompter(self, yamlpath: Path) -> None:
        """
        指定の YAML を Prompter として設定する\n
        "interpreter" キーワードと一致しない場合は何もしない(そのまま)

        Args:
            yamlpath (Path): YAML パス
        """
        yamlpath = Path(yamlpath)
        if yamlpath.exists():
            with open(yamlpath, "r", encoding="utf-8") as f:
                yamldict: dict = yaml.safe_load(f)
                keyword = yamldict.get("interpreter")
            if keyword == self.keyword():
                self.prompter = Prompter.make(yamlpath)

    def strip(self, prompt: Prompt) -> Prompt:
        """
        カテゴリーリストに存在しない PromptParts を削ぎ落とす\n
        ただし common は除外する(必ず結果に含める)\n
        本関数は非破壊的である

        Args:
            prompt (Prompt): Prompt

        Returns:
            Prompt: Prompt
        """
        result: Prompt = []
        for prompt_parts in prompt:
            if len(prompt_parts.path) >= 2 and prompt_parts.path not in self.category_list:
                continue
            result.append(prompt_parts)
        return result

    def dedupe(self, prompt: Prompt) -> Prompt:
        """
        Prompt において同じ token を持つ Token のうち, |weight - 1| が最大のものを残す\n
        順序は同じ token を持つ CategoryPath において,\n
        カテゴリーリストで指定されている内の最も早いものに統一する\n
        本関数は非破壊的である

        Args:
            prompt (Prompt): Prompt

        Returns:
            Prompt: Prompt
        """

        def update_best(
            best: dict[str, tuple[Token, set[CategoryPath]]], token: Token, path: CategoryPath
        ) -> None:
            """最も weight が 1 に近いトークンと, 収集元の CategoryPath をすべて記録する"""
            score = abs(token.weight - 1.0)
            current = best.get(token.token)
            if current is None:
                best[token.token] = (token, {path})
            else:
                crnt_token = token if score > abs(current[0].weight - 1.0) else current[0]
                crnt_paths = current[1] | {path}
                best[token.token] = (crnt_token, crnt_paths)

        best: dict[str, tuple[Token, set[CategoryPath]]] = {}
        for prompt_parts in prompt:
            for token in prompt_parts.tokens:
                update_best(best, token, prompt_parts.path)

        def filter(
            prompt_parts: PromptParts, best: dict[str, tuple[Token, set[CategoryPath]]]
        ) -> PromptParts:
            result = PromptParts()
            for token in prompt_parts.tokens:
                if best.get(token.token) is not None and best.get(token.token)[0] is token:
                    result.tokens.append(token)
                    if not result.path:
                        result.path = next(
                            (p for p in self.category_list if p in best[token.token][1]),
                            prompt_parts.path,
                        )
                    best.pop(token.token)
            return result

        new_prompt: Prompt = []
        for prompt_parts in prompt:
            new_prompt.append(filter(prompt_parts, best))

        return new_prompt

    def sort(self, prompt: Prompt) -> Prompt:
        """
        PromptBase を適切にソートする\n
        ソートルールはカテゴリーリスト内の CategoryPath の順序に従う\n
        リスト内にない CategoryPath は順に最後尾に置き換えられ,\n
        リスト内の存在しない CategoryPath は無視される\n
        また(通常は誤って)同じ CategoryPath がリスト内に存在する場合, 比べて後ろの位置となる\n
        本関数は非破壊的である
        """
        order_index: dict[CategoryPath, int] = {
            path: i for i, path in enumerate(self.category_list)
        }

        return sorted(prompt, key=lambda c: order_index.get(c.path, float("inf")))

    def edit(self, prompt: Prompt) -> Prompt:
        """
        非破壊的に prompt を編集, 記録する\n
        各派生クラスはこの関数をオーバーライドすべきである(この関数自体を実行するのは構わない)

        Args:
            prompt (Prompt): Prompt

        Returns:
            Prompt: Prompt
        """
        return self.sort(self.dedupe(self.strip(prompt)))

    def make_prompt_set(self, text: str) -> PromptSet | None:
        """
        テキストをもとに Prompter によって PromptSet を得る\n
        PromptSet は dedupe かつ sort 済み, 加えて edit も実施済みである\n
        Prompter 未指定の場合は None を返す

        Args:
            text (str): テキスト

        Returns:
            PromptSet | None: PromptSet, Prompter 未指定の場合に None
        """
        if self.prompter is None:
            return None

        positive, negative = self.prompter.to_prompt(text)
        return PromptSet(positive=self.edit(positive), negative=self.edit(negative))

    @staticmethod
    def is_enough_prompt(prompt_set: PromptSet) -> bool:
        """
        指定の PromptSet が生成に十分な情報を持っているか\n
        各派生クラスはこの関数をオーバーライドすべきである(この関数自体を実行するのは構わない)\n
        基底クラスにおいては空かどうかだけを判定する

        Args:
            prompt_set (PromptSet): PromptSet

        Returns:
            bool: True: 十分, False: 不十分(空文字列)
        """
        return prompt_set is not None and (prompt_set.positive or prompt_set.negative)
