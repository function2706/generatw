"""
プロンプトの原子的データ構造

era 依存の解釈系から切り離した, プロンプト構築の共通部品.
- Token: 重み付きトークン
- TokenExpr: `<a|b>` 形式の確率的選択記法を含むプロンプト文字列の構文木
- Prompt / PromptParts / CategoryPath: 生成タスクへ渡すプロンプト表現
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256


@dataclass
class Token:
    """
    重み付きトークンを表すクラス\n
    例: '(foo:1.2)' -> Token(token='foo', weight=1.2)

    Attributes:
        token (str): トークン文字列
        weight (float): トークンの重み
    """

    token: str = ""
    weight: float = 1.0

    @classmethod
    def make(cls, original_token: str):
        """
        文字列から Token インスタンスを生成する

        Args:
            original_token (str): 元のトークン文字列('word' または '(word:1.2)' 形式)

        Returns:
            Token: 生成された Token インスタンス

        Raises:
            ValueError: トークンの形式が不正な場合
        """
        m = re.fullmatch(r"\(?([\w\s\-\(\)\\'.]+)(?::([0-9.]+))?\)?", original_token.strip())
        if not m:
            raise ValueError(
                f"Invalid token format: '{original_token}'. Expected 'word' or '(word:1.2)'."
            )

        token, weight_str = m.groups()
        try:
            weight = float(weight_str) if weight_str is not None else 1.0
        except ValueError:
            weight = 1.0

        return cls(token=token, weight=weight)

    def to_str(self) -> str:
        """
        プロンプト文字列に変換する

        Returns:
            str: プロンプト文字列('token' または '(token:weight)' 形式)
        """
        return f"({self.token}:{self.weight})" if self.weight != 1.0 else self.token


def split_top_level(s: str, sep: str = "|") -> list[str]:
    """
    `<>` および `()` のネストを考慮して, 最上位レベルのセパレータ `sep` で文字列を分割する\n
    ネスト内部の `sep` は分割対象外とする

    Args:
        s (str): 分割対象の文字列
        sep (str): セパレータ文字 (デフォルト: '|')

    Returns:
        list[str]: 分割後の文字列リスト
    """
    parts = []
    angle_depth = 0  # <> のネスト深度
    paren_depth = 0  # () のネスト深度
    current = []

    for ch in s:
        if ch == "<":
            angle_depth += 1
            current.append(ch)
        elif ch == ">":
            angle_depth -= 1
            current.append(ch)
        elif ch == "(":
            paren_depth += 1
            current.append(ch)
        elif ch == ")":
            paren_depth -= 1
            current.append(ch)
        elif ch == sep and angle_depth == 0 and paren_depth == 0:
            # ネスト外のセパレータ -> 分割ポイント
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)

    parts.append("".join(current))
    return parts


def split_prob_and_token(part: str) -> tuple[float, str]:
    """
    選択肢パート文字列を確率部分とトークン部分に分割する\n
    `<` で始まる場合はネストされた選択肢ブロックとみなし, prob=1.0 のままトークン部分として返す\n
    `::` が存在しない場合も prob=1.0 とする

    書式: `prob::token_part` (例: `2::hoge`, `3::(foo:1.2)`)

    Args:
        part (str): 選択肢パート文字列

    Returns:
        tuple[float, str]: (確率, トークン部分文字列)
    """
    # <...> で始まる場合はネストされた選択肢ブロック -> prob は外側から与えられる
    if part.startswith("<"):
        return 1.0, part

    idx = part.find("::")
    if idx == -1:
        # :: がない場合は prob=1.0
        return 1.0, part

    return float(part[:idx]), part[idx + 2 :]


class TokenExprType(StrEnum):
    leaf = "leaf"  # リテラルトークン1つ
    choice = "choice"  # `<a|b>` 形式の選択ノード
    seq = "seq"  # カンマ連結の順序ノード
    none = "none"  # 未初期化


@dataclass
class TokenExpr:
    """
    プロンプト文字列の構文木ノード\n
    `make()` によってテキストをパースし, `confirm()` によって確定したトークン列を返す

    Attributes:
        kind (TokenExprType): ノード種別
        children (list[TokenExpr]): 子ノードリスト (leaf の場合は空)
        pweight (float): 親 choice ノードから与えられる相対重み
        token (Token | None): leaf ノードが保持するトークン (leaf 以外は None)
        total (float): compute_total() で算出される重みの合計
        norm (list[tuple[TokenExpr, float]]): choice ノードの (子, 重み) リスト
        key (str | None): next_seed() で用いるノード固有キー (make() 時に text から生成)
    """

    kind: TokenExprType = TokenExprType.none
    children: list[TokenExpr] = field(default_factory=list)
    pweight: float = 1.0
    token: Token | None = None
    total: float = 0.0
    norm: list[tuple[TokenExpr, float]] = field(default_factory=list)
    key: str | None = None

    @classmethod
    def parse_sequence_node(cls, text: str) -> TokenExpr:
        """
        カンマ区切りの連結シーケンスをパースして seq または leaf ノードを返す\n
        カンマが1つもなければ単一ノードとして返す

        Args:
            text (str): カンマ区切りのシーケンス文字列

        Returns:
            TokenExpr: seq ノード (要素が2つ以上) または単一子ノード
        """
        parts = split_top_level(text, ",")

        children = []
        for part in parts:
            if not part:
                continue
            children.append(TokenExpr.parse_part(part))

        if not children:
            # 空文字列 -> 空の leaf
            return cls(kind=TokenExprType.leaf, token=Token())

        if len(children) == 1:
            return children[0]

        return cls(kind=TokenExprType.seq, children=children)

    @classmethod
    def parse_choice(cls, text: str) -> TokenExpr:
        """
        `<...>` 形式の選択ブロックをパースして choice ノードを返す\n
        各選択肢は `prob::token_part` 形式, prob 省略時は 1.0\n
        空文字列 -> pweight=1.0 の空 leaf として扱う(<|foo> の空パターンの抽選機会のため)

        Args:
            text (str): `<...>` 形式の文字列

        Returns:
            TokenExpr: choice ノード
        """
        inner = text[1:-1]
        parts = split_top_level(inner, "|")

        children = []
        for part in parts:
            if not part:
                node = cls(kind=TokenExprType.leaf, token=Token())
                node.pweight = 1.0
                children.append(node)
                continue

            prob, token_part = split_prob_and_token(part)
            node = TokenExpr.parse_sequence_node(token_part)
            node.pweight = prob
            children.append(node)

        return cls(kind=TokenExprType.choice, children=children)

    @classmethod
    def parse_inline(cls, text: str) -> TokenExpr:
        """
        トークン文字列に埋め込まれた `<...>` をパースし, choice ノードを返す\n
        `<...>` 前後の prefix/suffix は各選択肢の先頭・末尾トークンに文字列として結合される\n
        例: `x<y,A|z,B>w` -> choice( seq(xy, Aw), seq(xz, Bw) )

        Args:
            text (str): `<...>` を含むトークン文字列

        Returns:
            TokenExpr: prefix/suffix を結合済みの choice ノード
        """
        # 最初の < の位置を特定
        start = text.find("<")

        # 対応する > を探す (ネスト考慮)
        depth = 0
        end = -1
        for i, ch in enumerate(text[start:], start):
            if ch == "<":
                depth += 1
            elif ch == ">":
                depth -= 1
                if depth == 0:
                    end = i
                    break

        prefix = text[:start]  # <...> より前の文字列
        suffix = text[end + 1 :]  # <...> より後の文字列
        inner = text[start : end + 1]  # <...> 部分

        # choice ノードの各子に prefix/suffix を結合して新しい children を構築
        choice_node = TokenExpr.parse_choice(inner)

        new_children = []
        for child in choice_node.children:
            new_child = cls._attach_prefix_suffix(child, prefix, suffix)
            new_child.pweight = child.pweight
            new_children.append(new_child)

        choice_node.children = new_children
        return choice_node

    @classmethod
    def _attach_prefix_suffix(cls, node: TokenExpr, prefix: str, suffix: str) -> TokenExpr:
        """
        ノードの先頭トークンに prefix を, 末尾トークンに suffix を文字列結合する\n
        - leaf: トークン文字列に直接結合\n
        - seq: 先頭子に prefix, 末尾子に suffix を再帰適用\n
        - choice: 全子に再帰適用 (ネストした choice への伝播)

        Args:
            node (TokenExpr): 結合対象ノード
            prefix (str): 先頭に結合する文字列
            suffix (str): 末尾に結合する文字列

        Returns:
            TokenExpr: prefix/suffix を結合した新しいノード
        """
        if node.kind == TokenExprType.leaf:
            tok = node.token
            new_text = prefix + (tok.token if tok else "") + suffix
            if not new_text:
                # prefix/suffix ともに空かつトークンも空 -> 元のノードをそのまま返す
                return node
            return cls(kind=TokenExprType.leaf, token=Token.make(new_text))
        elif node.kind == TokenExprType.seq:
            # 先頭子に prefix, 末尾子に suffix を適用
            new_children = list(node.children)
            if new_children:
                new_children[0] = cls._attach_prefix_suffix(new_children[0], prefix, "")
                new_children[-1] = cls._attach_prefix_suffix(new_children[-1], "", suffix)
            return cls(kind=TokenExprType.seq, children=new_children)
        elif node.kind == TokenExprType.choice:
            # ネストした choice -> 全子に再帰
            new_children = []
            for child in node.children:
                new_child = cls._attach_prefix_suffix(child, prefix, suffix)
                new_child.pweight = child.pweight
                new_children.append(new_child)
            return cls(kind=TokenExprType.choice, children=new_children)

        return node

    @classmethod
    def parse_part(cls, part: str) -> TokenExpr:
        """
        単一パーツ文字列を適切なノードにパースする\n
        - `<...>` 形式 -> choice ノード\n
        - `<` を含む -> inline ノード (parse_inline)\n
        - その他 -> leaf ノード

        Args:
            part (str): パーツ文字列

        Returns:
            TokenExpr: パース結果のノード
        """
        part = part.strip()

        if part.startswith("<") and part.endswith(">"):
            return TokenExpr.parse_choice(part)

        if "<" in part:
            return TokenExpr.parse_inline(part)

        return cls(kind=TokenExprType.leaf, token=Token.make(part))

    def compute_total(self) -> None:
        """
        各ノードの重み合計 `total` と choice ノードの正規化済みリスト `norm` を再帰的に算出する\n
        `make()` 内で自動的に呼ばれる

        - leaf: total = 1.0\n
        - seq: total = 全子の total の積 (直積展開の組み合わせ数に対応)\n
        - choice: total = 全子の pweight の和, norm = [(子, pweight), ...]
        """
        if self.kind == TokenExprType.leaf:
            self.total = 1.0
        elif self.kind == TokenExprType.seq:
            t = 1.0
            for c in self.children:
                c.compute_total()
                t *= c.total
            self.total = t
        elif self.kind == TokenExprType.choice:
            for c in self.children:
                c.compute_total()
            self.norm = []
            self.total = 0.0
            for c in self.children:
                # pweight をそのまま区間幅として使用
                # sample() 内で子の [0, c.total) へのスケーリングにより正しい確率で選択される
                self.norm.append((c, c.pweight))
                self.total += c.pweight

    @classmethod
    def make(cls, text: str | None, path: CategoryPath, matches: set[str] = None) -> TokenExpr:
        """
        テキストから TokenExpr ノード木を構築する\n
        パース後に compute_total() を呼び出して重みを確定する

        Args:
            text (str | None): プロンプト文字列, None の場合は空ノードを返す
            path (CategoryPath): カテゴリーパス
                複数カテゴリーが定義されていて, それらのいくつかがヒットした場合に必要
            matches (set[str]): マッチ条件
                maps に複数ヒットが定義されていて, それらのいくつかがヒットした場合に必要

        Returns:
            TokenExpr: 構築されたノード木
        """
        if text is None:
            return cls()

        node = cls.parse_sequence_node(text)
        match_str = str(sorted(matches)) if matches is not None else "empty"
        node.key = f"{text}#{CategoryPath(path).stringfy()}#{match_str}"
        node.compute_total()
        return node

    def sample(self, seed: str) -> list[Token]:
        """
        シードを元に再帰的にトークン列を確定する\n
        - leaf: 保持するトークンを返す\n
        - seq: 各子に派生シードを渡して連結\n
        - choice: pweight に従って1つの子を選択し, その子に派生シードを渡す

        Args:
            seed (str): 選択を決定するシード文字列

        Returns:
            list[Token]: 確定したトークン列
        """
        if self.kind == TokenExprType.leaf:
            return [self.token] if self.token and self.token.token else []
        elif self.kind == TokenExprType.seq:
            out = []
            for i, c in enumerate(self.children):
                # 各子に独立した派生シードを渡して連結
                out.extend(c.sample(f"{seed}#{i}"))
            return out
        elif self.kind == TokenExprType.choice:
            h = sha256(seed.encode())
            h.update((self.key or "").encode())
            r = (int(h.hexdigest(), 16) / 2**256) * self.total
            acc = 0.0
            for i, (c, w) in enumerate(self.norm):
                if r < acc + w:
                    return c.sample(f"{seed}#{i}")
                acc += w

            # 浮動小数誤差対策: 最後の選択肢を返す
            last_idx = len(self.norm) - 1
            return self.norm[last_idx][0].sample(f"{seed}#{i}")

        return []

    def confirm(self, seed: str) -> list[Token]:
        """
        シード文字列を元に選択肢を1つ確定して返す\n
        seed の SHA-256 ハッシュ値を用いて決定論的に選択する\n
        同一 seed に対して常に同じ結果を返す

        Args:
            seed (str): 選択を決定するシード文字列

        Returns:
            list[Token]: 確定したトークン列 (選択肢がない場合は空リスト)
        """
        tokens = self.sample(seed)
        return [] if not tokens or (len(tokens) == 1 and not tokens[0].token) else tokens


class CategoryPath(tuple[str, ...]):
    def stringfy(self) -> str:
        return str(self)


@dataclass
class PromptParts:
    """
    Cartegory パスごとにまとめられたトークン

    Attributes:
        path (CategoryPath): Category パス
        tokens (list[Token]): トークンのリスト
    """

    path: CategoryPath = field(default_factory=tuple)
    tokens: list[Token] = field(default_factory=list)


@dataclass
class Prompt:
    """
    Screen ごとにまとめられた PromptParts

    Attributes:
        screen_id (str): Screen ID
        positive (list[PromptParts]): ポジティブプロンプト
        negative (list[PromptParts]): ネガティブプロンプト
    """

    screen_id: str | None = None
    positive: list[PromptParts] = field(default_factory=list)
    negative: list[PromptParts] = field(default_factory=list)
