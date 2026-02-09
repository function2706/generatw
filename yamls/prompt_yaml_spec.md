# Prompt Rule YAML 仕様書

本ドキュメントは、テキスト入力から **ポジティブ / ネガティブプロンプト** を自動生成するための YAML ルール仕様を定義する。
本仕様は、正規表現・優先度・重み付きトークン・positive/negative 分離を統一的に扱う DSL（ドメイン固有言語）である。

---

## 目次

1. [全体構造](#1-全体構造)
2. [Ignition（発火条件）](#2-ignition発火条件)
3. [フィールド定義](#3-フィールド定義)
4. [マッピングタイプ](#4-マッピングタイプ)
5. [プロンプト文字列記法](#5-プロンプト文字列記法)
6. [共通プロンプト](#6-共通プロンプト)
7. [処理フロー](#7-処理フロー)
8. [完全な例](#8-完全な例)
9. [制約・注意事項](#9-制約注意事項)
10. [予約語一覧](#10-予約語一覧)
11. [型定義（参考）](#11-型定義参考)

---

## 1. 全体構造

```yaml
<rulename>:                             # ルール名称 (任意)
  ignition:
    any: [<pattern1>, <pattern2>, ...]  # または all
  <section_name>:                       # 任意の階層構造
    <field_name>:
      pattern: <regex>
      priority: <number>
      capturegrp: <number>
      maps: <mapping>                   # または ranges
      default: <prompt>                 # オプション
  POSITIVE: <common_prompt>             # オプション
  NEGATIVE: <common_prompt>             # オプション
```

### 構造のルール

- `rulename` ルール名称（任意の文字列）
- `ignition`: 必須の発火条件
- フィールドは **任意の深さでネスト可能**（`pattern` キーで識別）
- `POSITIVE` / `NEGATIVE` は任意（存在すれば必ず末尾に追加）

---

## 2. Ignition（発火条件）

ルールを適用するかどうかを判定する条件。Python `re.search` で評価される。

### 2.1 `any` モード（論理和）

いずれか1つでもマッチすればルールが発火。

```yaml
ignition:
  any: ["today:", "date:"]
```

### 2.2 `all` モード（論理積）

すべてのパターンがマッチした場合のみルールが発火。

```yaml
ignition:
  all: ["user:", "status:active"]
```

### 2.3 振る舞い

- 1つもマッチしない場合、**ルール全体が無効**（空文字列を返す）
- マッチした場合、以降のフィールド処理が実行される

---

## 3. フィールド定義

### 3.1 フィールドの識別

`pattern` キーを持つオブジェクトがフィールド定義として認識される。

```yaml
mainstat:
  character:      # セクション名（任意）
    name:         # フィールド名（任意）
      pattern: "[0-9]{2},\\s(\\w*)"
      # ...
  meta:
    date:
      pattern: "(1|2)[0-9]{3}/([0-9]{2})"
      # ...
```

### 3.2 必須プロパティ

#### `pattern` (string)

Python 正規表現パターン。

**制約:**

- バックスラッシュは必ずエスケープ（YAML 仕様: `\\s`, `\\d` など）
- 可変長後読み（`(?<=...)` で `*` や `+`）は禁止（Python re 制限）
- キャプチャグループ `()` の番号は左から自動採番

```yaml
pattern: "[0-9]{2},\\s(\\w*)"
pattern: "(sunny|rainy|cloudy)"
pattern: "(1|2)[0-9]{3}/([0-9]{2})"  # 2つのキャプチャグループ
```

#### `maps` または `ranges`

マッチした文字列をプロンプトに変換する方法を定義。**どちらか一方が必須。**
どちらも記述されている場合は`maps`が優先。

pattern が複数回マッチした場合、各マッチを独立に処理し、
得られたトークンは通常のマージ規則に従って統合される。

---

### 3.3 オプションプロパティ

#### `priority` (integer)

プロンプト出力順序の優先度。

- **小さい数字ほど先頭に配置**
- 同じ優先度の場合は YAML 記述順
- 未指定の場合は **自動で最大優先度+1** が割り当てられる（最低優先度）

```yaml
priority: 1   # 最優先
priority: 10  # 低優先度
# 未指定      # 最低優先度（自動割り当て）
```

---

#### `capturegrp` (integer, default: 0)

使用するキャプチャグループのインデックス。
指定された番号のキャプチャグループが存在しない場合、
そのマッチは無視される（例外にはならない）。

- `0`: パターン全体のマッチ
- `1`, `2`, ...: 各キャプチャグループ

```yaml
pattern: "name:\\s(\\w+)"
capturegrp: 1  # \\w+ の部分を使用
```

```yaml
pattern: "(1|2)[0-9]{3}/([0-9]{2})"
capturegrp: 2  # 2番目のグループ（月部分）を使用
```

---

#### `lifetime` (string, default: volatile)

トークンを次回以降の評価へ持ち越すかどうかを指定する。

```yaml
lifetime: stable   # 超越
lifetime: volatile # 超越しない
# 未指定           # 超越しない
```

stable なトークンは、次回評価時に通常のフィールド出力と同様に扱われ、
priority と weight ルールに従ってマージされる。

---

#### `default` (string | object)

パターンに **マッチはしたが、maps / ranges のいずれの rule にもヒットしなかった場合** に適用されるフォールバック。

```yaml
default: "unknown"
default: "cloudy"
```

```yaml
default:
  positive: fallback
  negative: FALLBACK
```

- pattern に一度もマッチしなかった場合は適用されない
- pattern がマッチし、かつ maps / ranges の結果が空だった場合に適用される

---

## 4. マッピングタイプ

### 4.1 `maps` - 文字列マッピング

抽出した文字列を **直接キーとしてマッピング** する方式。

```yaml
maps:
  <matched_value>: <entry>
```

#### 例1: シンプルなマッピング（positive のみ）

```yaml
pattern: "(sunny|rainy)"
maps:
  sunny: sunny
  rainy: rainy,wet
```

- キャプチャした値が `"sunny"` なら → `sunny` が positive に追加
- キャプチャした値が `"rainy"` なら → `rainy,wet` が positive に追加

#### 例2: Positive/Negative 分離

```yaml
pattern: "(foo|bar)"
maps:
  foo:
    positive: foo,good
    negative: FOO,bad
  bar:
    positive: bar
    negative: BAR
```

- `positive` / `negative` は独立
- **片方のみ定義してもよい**（例: negative のみ定義可能）

#### 例3: Negative のみ

```yaml
pattern: "(Baz)"
maps:
  Baz:
    negative: BAZ,(nope:1.4)
```

---

### 4.2 `ranges` - 値範囲マッピング

**キーと値の役割が逆転する**ことに注意。

```yaml
ranges:
  <prompt_key>: <range_entry>
```

- **プロンプト（キー）** に対して、該当する値のリストを定義
- 抽出した値がリストに含まれていれば、キーが positive として使用される

#### 例1: シンプルな範囲

```yaml
pattern: "([0-9]{2})"
capturegrp: 1
ranges:
  spring: ["03", "04", "05", "06"]
  summer: ["07", "08"]
  winter: ["12", "01", "02"]
```

- マッチした値が `"03"` なら → `spring` が positive に追加
- マッチした値が `"07"` なら → `summer` が positive に追加

#### 例2: positive + negative

```yaml
ranges:
  (hoge:1.3):
    positive: ["hoge"]
    negative: HOGE,nope
  fuga:
    positive: FUGA,(nope:1.3)
    negative: ["fuga", "Fuga"]
```

- `positive` (もしくは `negative`) に含まれていれば **キー自体が positive (もしくは negative) として使用**
- キー部分（`(hoge:1.3)`, `fuga`）が positive (もしくは negative) プロンプト
- `positive` と `negative` の一方は必ず list でなければならず, 他方は string でなければならない

#### 例3: positive (もしくは negative) のみ

```yaml
(hoge:1.2):
  positive: ["Hoge"]
```

- negative の定義は不要
- キー `(hoge:1.2)` が positive として使用される

---

## 5. プロンプト文字列記法

### 5.1 基本形式

カンマ区切りでトークンを列挙。

```yaml
positive: "token1,token2,token3"
```

### 5.2 重み付き記法

括弧内で `(token:weight)` の形式で重みを指定。

```yaml
positive: "foo,(bar:1.5),baz"
negative: "BAD,(worse:2.0)"
```

- 重みを指定しない場合は `1.0` がデフォルト
- 重みは小数点も可能

### 5.3 スペースを含むトークン

スペースはそのまま保持される。

```yaml
positive: "blue hair,red eyes,long dress"
```

### 5.4 重み衝突時の挙動

同じトークンが複数回出現した場合、**最大の重みが採用される**。

```yaml
# 以下が同時にマッチした場合
positive: "(foo:1.2)"
positive: "(foo:1.5)"
# 結果: (foo:1.5)
```

これは positive / negative 共通の振る舞い。
重みが同一の場合、priority が小さい（先に評価された）ものが採用される。

---

## 6. 共通プロンプト

### 6.1 `POSITIVE` (string, optional)

すべてのマッチ結果の**末尾**に必ず追加されるポジティブプロンプト。

```yaml
POSITIVE: "common positive,high quality"
```

### 6.2 `NEGATIVE` (string, optional)

すべてのマッチ結果の**末尾**に必ず追加されるネガティブプロンプト。

```yaml
NEGATIVE: "common negative,low quality,blurry"
```

### 6.3 振る舞い

- 他の token と同様に weight 解釈・マージされる
- 必ず最後に追加されるため、視覚的に末尾に配置される

---

## 7. 処理フロー

1. **Ignition チェック**: テキストが発火条件を満たすか判定
2. **Priority ソート**: すべてのフィールドを priority 順に並べる
3. **パターンマッチ**: 各フィールドの pattern でテキストを検索
4. **値抽出**: capturegrp で指定されたグループの値を取得
5. **マッピング**: maps または ranges で値をプロンプトに変換
6. **マージ**: 同じトークンは最大重みで統合（positive/negative は完全に独立）
7. **共通プロンプト追加**: POSITIVE/NEGATIVE を末尾に追加
8. **出力**: カンマ区切りの文字列として出力

### 7.1 マージ規則の詳細

- すべてのフィールド結果を priority 順に評価
- positive / negative は **完全に独立して集約**
- token 衝突時は `max(weight)`
- 特例処理なし（すべて同一ロジック）
- stable 指定のトークンも priority の影響を受ける
- 最終的な並び順は period → priority の順で決定される

---

## 8. 完全な例

```yaml
mainstat:
  ignition:
    any: ["today:"]
  
  character:
    name:
      pattern: "[0-9]{2},\\s(\\w*)"
      priority: 6
      capturegrp: 1
      lifetime: stable
      maps:
        Alice: alice,blonde hair,blue eyes
        Bob: bob,brown hair
      default: unknown character
    
    mood:
      pattern: "mood:\\s(\\w+)"
      priority: 5
      capturegrp: 1
      maps:
        happy:
          positive: happy,smile
          negative: sad,crying
        angry:
          positive: angry,fierce
          negative: happy
  
  meta:
    season:
      pattern: "month:\\s([0-9]{2})"
      priority: 3
      capturegrp: 1
      lifetime: volatile
      ranges:
        spring: ["03", "04", "05"]
        summer: ["06", "07", "08"]
        autumn: ["09", "10", "11"]
        winter: ["12", "01", "02"]
    
    weather:
      pattern: "(sunny|rainy)"
      priority: 4
      maps:
        sunny: sunny
        rainy: rainy
      default: cloudy
  
  test:
    foobar:
      pattern: "(foo|bar|Bar|Baz)"
      priority: 1
      maps:
        foo:
          positive: foo
          negative: FOO,(nope:1.1)
        bar:
          positive: (bar:1.3)
          negative: BAR,(nope:1.2),nyome
        Bar:
          positive: (bar:1.1)
          negative: BAR,(nope:1.2)
        Baz:
          negative: BAZ,(nope:1.4)
    
    hogefuga:
      pattern: "([hH]oge|[fF]uga)"
      priority: 2
      ranges:
        (hoge:1.3):
          positive: ["hoge"]
          negative: HOGE,nope
        (hoge:1.2):
          negative: ["Hoge"]
        fuga:
          positive: ["fuga", "Fuga"]
          negative: FUGA,(nope:1.3)
  
  POSITIVE: "masterpiece,best quality"
  NEGATIVE: "worst quality,low quality,blurry"
sub:
  ignition:
    all: ["sub:", "WOW"]
  mood:
    pattern: "mood:\\s([^\\)]*)\\s"
    priority: 2
    capturegrp: 1
    maps:
      Mood1: mood1
      Mood2:
        positive: mood2
        negative: MOOD2
    default: mood3
  POSITIVE: "sub common positive"
  NEGATIVE: "sub common negative"
```

### 入力例

```txt
today: 2026/02/05, month: 02, 23, Alice (mood: happy) foobarHogefuga
```

### 出力例

```txt
POS: foo,(bar:1.3),(hoge:1.3),fuga,winter,cloudy,happy,smile,alice,blonde hair,blue eyes,masterpiece,best quality
NEG: FOO,BAR,HOGE,FUGA,BAZ,(nope:1.4),nyome,sad,crying,worst quality,low quality,blurry
```

#### 処理の内訳

1. **foobar** (priority: 1):
   - `foo` → positive: `foo`, negative: `FOO,(nope:1.1)`
   - `bar` → positive: `(bar:1.3)`, negative: `BAR,(nope:1.2),nyome`
   - 重み: `(bar:1.3)` が採用（`(bar:1.1)` より大きい）

2. **hogefuga** (priority: 2):
   - `Hoge` → positive: `(hoge:1.2)`
   - `fuga` → positive: `fuga`, negative: `FUGA,(nope:1.3)`
   - 重み: `(hoge:1.3)` vs `(hoge:1.2)` → `(hoge:1.3)` が採用

3. **season** (priority: 3):
   - `02` → `winter`

4. **weather** (priority: 4):
   - マッチなし → default: `cloudy`

5. **mood** (priority: 5):
   - `happy` → positive: `happy,smile`, negative: `sad,crying`

6. **name** (priority: 6):
   - `Alice` → `alice,blonde hair,blue eyes`

7. **POSITIVE/NEGATIVE** (末尾):
   - positive に `masterpiece,best quality` 追加
   - negative に `worst quality,low quality,blurry` 追加

---

## 9. 制約・注意事項

### 9.1 正規表現

- 可変長後読み `(?<=pattern*)` は使用不可（Python re 制限）
- バックスラッシュは必ずエスケープ（YAML 仕様: `\\` で記述）
- キャプチャグループの番号は左から順に自動採番（`(a)(b)` なら 1, 2）

### 9.2 Priority

YAML に記述された priority 値は、読み込み後に以下のルールで再採番される。

1. priority が小さい順に並べる  
2. 同値の場合は YAML 記述順  
3. 1, 2, 3, ... の連番に振り直す  
4. priority 未指定（lowest_priority）は最後に回される

したがって、ユーザーが指定した数値は
**相対順序を決めるための値**としてのみ使用される。

### 9.3 トークン

- カンマ `,` はトークン区切り文字（トークン内には使用不可）
- 括弧 `()` は重み記法の予約文字
- **スペースはトークン内で使用可能**（例: `blue hair`）
- `(((foo)))`や`[[[foo]]]`の記法は非対応

同一 token が複数回出現した場合、以下の順で採用が決定される。

1. **より大きい weight** を持つもの
2. weight が同一なら **priority が小さい（先に評価された）** もの

これは positive / negative で独立に行われる。

### 9.4 マッピング

- `maps` と `ranges` が同時に指定された場合、maps が優先され、ranges は無視される
- `ranges` では **key がプロンプト、value が検索対象値リスト**
- `maps` では **key が検索対象値、value がプロンプト**
- negative-only 定義が可能（positive を省略可能）

---

## 10. 予約語一覧

本 DSL（Prompt Rule YAML）では、以下のキーは **特別な意味を持つ予約語** として定義されている。
これらのキーは、ユーザー定義のセクション名・フィールド名・値として使用してはならない。

### 10.1 ルート / 構造予約語

|予約語|意味|
|------|------|
|`ignition`|発火条件定義|
|`POSITIVE`|共通ポジティブプロンプト|
|`NEGATIVE`|共通ネガティブプロンプト|

### 10.2 Ignition 関連

|予約語|意味|
|------|------|
|`any`|論理和（いずれかがマッチ）|
|`all`|論理積（すべてがマッチ）|

### 10.3 フィールド定義予約語

|予約語|意味|
|------|------|
|`pattern`|正規表現パターン|
|`priority`|出力順序の優先度|
|`capturegrp`|使用するキャプチャグループ番号|
|`lifetime`|超越するかどうか|
|`default`|マッチ失敗時のフォールバック|

### 10.4 マッピング方式予約語

#### 10.4.1 Maps 型

|予約語|意味|
|------|------|
|`maps`|値 → プロンプトの直接マッピング|
|`positive`|ポジティブプロンプト|
|`negative`|ネガティブプロンプト|

#### 10.4.2 Ranges 型

|予約語|意味|
|------|------|
|`ranges`|プロンプト → 値集合の逆引きマッピング|
|`positive`|マッチ対象となる値リスト|
|`negative`|ネガティブプロンプト|

※ `ranges` では **キー自体が positive プロンプト** として使用される。

### 10.5 プロンプト文字列予約記号（構文レベル）

|記号|意味|
|----|----|
|`,`|トークン区切り|
|`(token:weight)`|重み付きトークン表記|
|`()`|重み指定のための予約構文|

### 10.6 命名上の注意

- 上記予約語は **セクション名・フィールド名・値として使用不可**
- 大文字 / 小文字は **区別される**
  - `POSITIVE` / `NEGATIVE` は大文字のみ有効
- 将来の拡張のため、以下の語も **使用非推奨**：
  - `enable`, `disable`, `when`, `unless`, `else`

### 10.7 実装上の扱い（参考）

- 予約語は **パーサ段階で除外 / 特別処理**
- 未知のキーはすべてユーザー定義セクションとして扱う
- 特例ルールは存在しない（予約語のみが制御構造）

---

## 11. 型定義（参考）

```typescript
type Rule = {
  ignition: Ignition;
  POSITIVE?: string;
  NEGATIVE?: string;
  [sectionName: string]: Section | Ignition | string;
};

type Ignition = {
  any?: string[];
  all?: string[];
};

type Section = {
  [fieldName: string]: Field | Section;
};

type Field = {
  pattern: string;
  priority?: number;
  capturegrp?: number;
  lifetime?: string;
  default?: string | PromptEntry;
} & (MapsField | RangesField);

type MapsField = {
  maps: {
    [value: string]: string | PromptEntry;
  };
};

type RangesField = {
  ranges: {
    [prompt: string]: string[] | RangeEntry;
  };
};

type PromptEntry = {
  positive?: string;
  negative?: string;
};

type RangeEntry = {
  positive?: string[] | string;
  negative?: string | string[];
};
```

---

## 12. 設計思想（参考）

### 12.1 "書く側が迷わない" DSL

- 一貫したルール（特例処理なし）
- YAML がそのまま DSL になる
- positive / negative は対称設計

### 12.2 Weight 競合は常に決定的

- 同一 token の重複は必ず `max(weight)` で解決
- 処理順序に依存しない

### 12.3 正規表現は抽出にのみ集中

- パターンマッチは **抽出** のみ
- 意味解釈（プロンプト化）は YAML 側に寄せる
- 責務の分離により保守性を向上

---

以上が本 YAML 仕様の完全定義である。
