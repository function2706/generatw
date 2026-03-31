from __future__ import annotations

import re
from dataclasses import dataclass, field
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
            # ネスト外のセパレータ → 分割ポイント
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
    # <...> で始まる場合はネストされた選択肢ブロック → prob は外側から与えられる
    if part.startswith("<"):
        return 1.0, part

    idx = part.find("::")
    if idx == -1:
        # :: がない場合は prob=1.0
        return 1.0, part

    return float(part[:idx]), part[idx + 2 :]


def parse_inline_options(text: str) -> list[tuple[list[str], float]]:
    """
    トークン文字列に埋め込まれた `<...>` 選択肢を展開する\n
    `<...>` の前後にある prefix/suffix 文字列を, 展開後の先頭・末尾トークンに結合する

    例:\n
    `x<y,A|z,B>` → `[(['xy', 'A'], 1.0), (['xz', 'B'], 1.0)]`\n
    `<a|b>_sfx`  → `[(['a_sfx'], 1.0), (['b_sfx'], 1.0)]`

    **制限事項**\n
    prefix/suffix への重み付けには対応しない\n
    重み付けが必要な場合は `<(prefix_x:1.2)|(prefix_y:1.5)>` 等のリテラル形式で記述すること

    Args:
        text (str): `<...>` を含むトークン文字列

    Returns:
        list[tuple[list[str], float]]: [(トークン文字列リスト, 重み), ...]
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
    inner_block = text[start : end + 1]  # <...> 部分

    # 内側の選択肢を展開
    inner_sequences = parse_options(inner_block)

    result = []
    for tok_list, w in inner_sequences:
        if not tok_list:
            # トークンが空の場合は prefix+suffix を単一トークンとして扱う
            new_list = [prefix + suffix] if (prefix or suffix) else []
        elif len(tok_list) == 1:
            # 単一トークン → prefix と suffix を両端に結合
            new_list = [prefix + tok_list[0] + suffix]
        else:
            # 複数トークン → 先頭に prefix, 末尾に suffix を結合
            new_list = [prefix + tok_list[0]] + tok_list[1:-1] + [tok_list[-1] + suffix]
        result.append((new_list, w))

    return result


def parse_sequence(text: str) -> list[tuple[list[str], float]]:
    """
    カンマ区切りのトークン連結シーケンスを直積展開し, 全組み合わせを返す\n
    各パーツは以下のいずれかとして処理される:\n
    - `<...>` 形式: `_parse_options` で再帰展開\n
    - `word<...>` 等の埋め込み形式: `_parse_inline_options` で展開\n
    - リテラル文字列: そのまま単一トークンとして扱う

    例: `t2,<3::t3|4::t4>` → `[([t2,t3], 3.0), ([t2,t4], 4.0)]`

    Args:
        text (str): カンマ区切りのシーケンス文字列

    Returns:
        list[tuple[list[str], float]]: [(トークン文字列リスト, 重み), ...]
    """
    # 最上位の , でパーツに分割
    parts = split_top_level(text, sep=",")

    all_candidates: list[list[tuple[list[str], float]]] = []

    for part in parts:
        if not part:
            continue

        if part.startswith("<") and part.endswith(">"):
            # 純粋な選択肢ブロック
            all_candidates.append(parse_options(part))
        elif "<" in part:
            # prefix/suffix を持つ埋め込み選択肢 (例: "word<a|b>suffix")
            all_candidates.append(parse_inline_options(part))
        else:
            # リテラルトークン
            all_candidates.append([([part], 1.0)])

    if not all_candidates:
        return [([], 1.0)]

    # 直積: 全パーツの組み合わせを列挙し, 重みは積を取る
    result: list[tuple[list[str], float]] = [([], 1.0)]
    for candidates in all_candidates:
        new_result = []
        for existing_list, existing_w in result:
            for tok_list, w in candidates:
                new_result.append((existing_list + tok_list, existing_w * w))
        result = new_result

    return result


def parse_options(text: str) -> list[tuple[list[str], float]]:
    """
    `<...>` 形式の選択肢ブロックをパースし, 展開済みの選択肢リストを返す\n
    `|` 区切りで選択肢を分割し, 各選択肢を `_parse_sequence` で再帰的に展開する

    **重みの正規化について**\n
    選択肢間の重み比率を正しく保つため, 各選択肢の有効重み (prob * 内側合計) を揃える必要がある\n
    具体的には全選択肢の内側合計の積を共通分母として利用する\n
    例: `<2::hoge|<3::fuga|4::hogefuga>>` の場合\n
    - `hoge` の内側合計=1, `<3::fuga|4::hogefuga>` の内側合計=7\n
    - all_nt = 1 * 7 = 7\n
    - hoge: prob=2, w=1, nt=1 → 2 * 1 * (7/1) = 14\n
    - fuga: prob=1, w=3, nt=7 → 1 * 3 * (7/7) = 3\n
    - hogefuga: prob=1, w=4, nt=7 → 1 * 4 * (7/7) = 4\n
    - 結果: [(hoge,14), (fuga,3), (hogefuga,4)]

    **制限事項**\n
    `<x|y>z` のような後置文字列への重み付けには対応しない\n
    この場合は `<(xz:1.2)|(yz:1.5)>` 等のリテラル形式で記述すること

    Args:
        text (str): `<...>` 形式の文字列

    Returns:
        list[tuple[list[str], float]]: [(トークン文字列リスト, 重み), ...]
    """
    assert text.startswith("<") and text.endswith(">")
    inner = text[1:-1]

    # 最上位の | で選択肢を分割
    parts = split_top_level(inner, sep="|")

    raw: list[tuple[float, list[tuple[list[str], float]]]] = []
    for part in parts:
        if not part:
            continue

        prob, token_part = split_prob_and_token(part)

        if prob <= 0:
            raise ValueError(f"Weight must be positive: {part}")

        # token_part はカンマ連結を含む可能性があるため _parse_sequence で展開
        sequences = parse_sequence(token_part)
        raw.append((prob, sequences))

    if not raw:
        raise ValueError("Empty options.")

    # 各選択肢の内側合計重みを計算
    effective = [(prob, seqs, sum(w for _, w in seqs)) for prob, seqs in raw]

    # 全選択肢の内側合計の積 → 共通分母として使用
    all_nt = 1.0
    for _, _, nt in effective:
        all_nt *= nt

    # 各トークンの最終重み = prob * inner_w * (all_nt / 自分の nt)
    opts: list[tuple[list[str], float]] = []
    for prob, seqs, nt in effective:
        for tok_list, w in seqs:
            opts.append((tok_list, prob * w * (all_nt / nt)))

    return opts


@dataclass
class TokenExpr:
    """
    未確定状態を含めたトークン定義クラス\n
    カンマ区切り・`<>` ネスト・インライン埋め込みを含む複合表現を保持し,
    `confirm()` によって確定したトークン列を返す

    **書式**\n
    - リテラル: `word` または `(word:1.2)`\n
    - 選択: `<2::a|3::b>` (重み付き選択, 省略時は重み=1.0)\n
    - 連結: `a,b,<c|d>` (カンマ区切りで複数トークンを連結)\n
    - ネスト: `<2::a|3::<4::b|5::c>>` (選択肢内に選択肢)\n
    - インライン: `pre<a|b>suf` (トークン内に選択肢を埋め込み)

    **重みの意味**\n
    `token_opts` 内の float は相対的な採用確率を表す\n
    `confirm()` では合計重みで正規化した上で確率的に1つの選択肢を返す

    **制限事項**\n
    `<x|y>z` のような後置文字列への重み付けには対応しない\n
    重み付けが必要な場合は `<(xz:1.2)|(yz:1.5)>` 等と記述すること

    Attributes:
        token_opts (list[tuple[list[Token], float]]): (確定トークン列, 相対重み) のリスト
        prob_total (float): confirm 時に用いる prob の合計値
        key (str): confirm 時に用いるオブジェクト固有の文字列
    """

    token_opts: list[tuple[list[Token], float]] = field(default_factory=list)
    prob_total: float = 0
    key: str = ""

    @classmethod
    def make(cls, text: str):
        """
        文字列から UnconfirmedToken インスタンスを生成する\n
        `_parse_sequence` を通じてカンマ連結・選択・ネストを再帰的に展開する

        Args:
            text (str): トークン定義文字列

        Returns:
            UnconfirmedToken: 生成された UnconfirmedToken インスタンス

        Raises:
            ValueError: 空の選択肢, または不正なトークン形式の場合
        """
        if text is None:
            return cls()

        sequences = parse_sequence(text)
        if not sequences:
            raise ValueError("Empty options.")

        opts = [([Token.make(t) for t in tok_list], w) for tok_list, w in sequences]
        total = sum(w for _, w in opts)
        key = "|".join(",".join(tok.token for tok in toks) for toks, _ in opts)
        return cls(token_opts=opts, prob_total=total, key=key)

    def confirm(self, seed: str) -> list[Token]:
        """
        シード文字列を元に選択肢を1つ確定して返す\n
        seed の SHA-256 ハッシュ値を用いて決定論的に選択する\n
        同一 seed に対して常に同じ結果を返す

        Args:
            seed (str): 選択を決定するシード文字列

        Returns:
            list[Token]: 確定したトークン列

        Raises:
            ValueError: 合計重みが 0 以下の場合
        """
        if not self.token_opts:
            return []

        def return_(toks: list[Token]) -> list[Token]:
            if not toks or (len(toks) == 1 and not toks[0].token):
                return []
            else:
                return toks

        # SHA-256 ハッシュを [0, prob_total) の範囲の乱数として使用
        # key はオブジェクトごとに異なる値を算出するために使用
        h = int(sha256(f"{seed}|{self.key}".encode()).hexdigest(), 16)
        r = (h / 2**256) * self.prob_total

        acc_prob = 0.0
        for tok_list, prob in self.token_opts:
            acc_prob += prob
            if r < acc_prob:
                return return_(tok_list)

        # 浮動小数誤差対策: 最後の選択肢を返す
        return return_(self.token_opts[-1][0])


class CategoryPath(tuple[str, ...]):
    def stringfy(self) -> str:
        return str(self)


@dataclass
class PromptParts:
    """
    Cartegory パスごとにまとめられたトークン

    Attributes:
        path (CategoryPath): Category パス
        tokens (list[Token | UnconfirmedToken]): トークンのリスト
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


@dataclass
class Report:
    """
    1回のパターンマッチング結果を記録するクラス\n
    末端 Category でのみ生成される(再帰 Category 階層では生成されない)

    同一性は (matched, pattern, capturegrp) の3つで判断される\n
    screen_id や paths は同一性に含まれない

    Attributes:
        matched (str): キャプチャグループで取得したマッチ文字列
        pattern (str): マッチに使用した正規表現パターン文字列
        capturegrp (int): 使用したキャプチャグループ番号
        screen_id (str): このマッチが発生した Screen の ID
        paths (set[CategoryPath]): このマッチに関連する CategoryPath の集合\n
            同一マッチが複数の CategoryPath に属する場合（import/recurse で
            同パターンを複数箇所で使う場合など）に複数要素を持つ
    """

    matched: str = ""
    pattern: str = ""
    capturegrp: int = 0
    screen_id: str = ""
    paths: set[CategoryPath] = field(default_factory=set)

    def __eq__(self, other: Report) -> bool:
        """
        screen_id, paths は同一性判定に含めない\n
        (同じパターンで同じ文字列にマッチした Report は paths のマージ対象として扱うため)

        Args:
            other (Report): 比較対象 Report

        Returns:
            bool: (matched, pattern, capturegrp) が一致するなら True
        """
        return (self.matched, self.pattern, self.capturegrp) == (
            other.matched,
            other.pattern,
            other.capturegrp,
        )


@dataclass
class Reports:
    """
    ヒット/未ヒットの Report をまとめて管理するクラス

    hit_reports:
        いずれかの Rule にヒットした (Token が生成された)マッチの記録

    nothit_reports:
        パターンにはマッチしたが, どの Rule にもヒットしなかったマッチの記録
        * パターン自体がマッチしなかった場合は記録されない
        * default が適用された場合も記録されない

    Attributes:
        hit_reports (list[Report]): Rule にヒットした記録
        nothit_reports (list[Report]): ヒットしなかった記録
    """

    hit_reports: list[Report] = field(default_factory=list)
    nothit_reports: list[Report] = field(default_factory=list)

    def append(self, report: Report, is_hit_report: bool) -> None:
        """
        Report を追加する\n
        同一 Reportが既に存在する場合は新規追加せず paths を union でマージする\n
        これにより, 同じパターンで同じ文字列にマッチした記録が重複して増えることを防ぐ

        Args:
            report (Report): 追加する Report
            is_hit_report (bool): True なら hit_reports, False なら nothit_reports に追加
        """
        target_list = self.hit_reports if is_hit_report else self.nothit_reports
        for appended_report in target_list:
            if report == appended_report:
                # 同一 Report が既存 -> paths だけ広げて終了
                appended_report.paths = appended_report.paths | report.paths
                break
        else:
            target_list.append(report)

    def extend(self, other: Reports) -> None:
        """
        別の Reports を取り込む\n
        再帰的な Category 処理で子の結果を親に集約する際に使用する\n
        hit/nothit それぞれを append で追加するため, paths のマージも適用される

        Args:
            other (Reports): 取り込む Reports
        """
        for hit_report in other.hit_reports:
            self.append(hit_report, True)
        for nothit_report in other.nothit_reports:
            self.append(nothit_report, False)

    @property
    def stripped_nothit_reports(self) -> list[Report]:
        """
        nothit_reports から\n
        「同一パターン, 同一 matched で hit_reports にも存在するもの」を除去して返す

        同一 matched が hit_reports と nothit_reports の両方に存在するケース:\n
            ある Rule ではヒット, 別の Rule ではヒットしない状況で両方に記録される\n
            この場合, ヒット済みの nothit_report はノイズになるため除去する

        例:
            pattern: (aaa|bbb), maps: {aaa: pos1}  で text="aaa bbb" の場合
                hit_reports:    [Report(matched="aaa")]
                nothit_reports: [Report(matched="bbb")]  # aaa は除去済み

        Returns:
            list[Report]: フィルタ後の nothit_reports
        """
        # hit_reports から {pattern: set(matched)} の辞書を構築
        hit_patterns_dict: dict[str, set[str]] = {}
        for report in self.hit_reports:
            if report.pattern in hit_patterns_dict:
                hit_patterns_dict[report.pattern].add(report.matched)
            else:
                hit_patterns_dict[report.pattern] = {report.matched}

        # hit_reports に存在しない (pattern, matched) の組み合わせのみ残す
        new_reports = []
        for report in self.nothit_reports:
            if (
                report.pattern not in hit_patterns_dict
                or report.matched not in hit_patterns_dict[report.pattern]
            ):
                new_reports.append(report)
        return new_reports
