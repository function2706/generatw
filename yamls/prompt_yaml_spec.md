# Prompt Rule YAML 仕様書

本ドキュメントは, テキスト入力から **ポジティブ / ネガティブプロンプト** を構成するための, 単数あるいは複数のトークンを自動生成するための YAML ルール仕様を定義する.

---

## 目次

1. [全体構造](#1-全体構造)
2. [`interpreter`: Interpreter との紐づけ](#2-interpreter-interpreter-との紐づけ)
3. [`ignition` (発火条件)](#3-ignition-発火条件)
4. [Category 定義](#4-category-定義)
5. [Rule 定義](#5-rule-定義)
6. [プロンプト文字列記法](#6-プロンプト文字列記法)
7. [Screen 共通プロンプト](#7-screen-共通プロンプト)
8. [処理フロー](#8-処理フロー)
9. [YAML の例](#9-yaml-の例)
10. [制約・注意事項](#10-制約注意事項)

---

## 1. 全体構造

```yaml
interpreter: <Interpreter ID> # Interpreter が提供する紐づけのための予約語
<screen name>:                # Screen 名, Interpreter による予約語
  ignition: <regex>
  <category name>:            # Category 名, Interpreter による予約語, 階層は任意
    pattern: <regex>
    capturegrp: <number>      # オプション
    maps:                     # または ranges, intervals
      rule:                   # Rule 名, Interpreter による予約語
        positive: <tokens>
        negative: <tokens>
    default: <prompt>         # オプション
  common:                     # オプション
    positive: <tokens>
    negative: <tokens>
```

このフォーマットは Screen > Category > Rule という三層構造によって記述される.  
これらは YAML 上の階層(インデント)によって書き分けることとする.

- Screen: 画面種別

ステータス画面や戦闘画面など, どの画面上のテキストをキャプチャするのかを指定する.

- Category: テキストのカテゴリーごとのパターン対応表

Screen 上のテキストのキャプチャ範囲とそれに対する Rule 対応表を指定する.

- Rule: トークン化ルール

Category のパターンにマッチした文字列ごとの変換規則を指定する.

---

## 2. `interpreter`: Interpreter との紐づけ

どの Interpreter の継承クラスのための対応表なのかを指定するための文字列を指定する.  
この文字列は Interpreter によって提供されるものを使用する(通常はクラス名そのものを想定).

### 2.1 記述例

```yaml
interpreter: SampleInterpreter
```

### 2.2 振る舞い

- 指定文字列と完全一致した場合, 各 Screen の `ignition` チェックが上から順に実施される
- Interpreter が認知しない文字列が指定されている場合, シンタックスエラーとする

### 2.3 以降の処理

以降各処理において, DSL 側では Interpreter が想定しているデータが完備されているかどうかは判断せず, YAML に書かれている分を愚直に処理する(判断は Interpreter の責務).

ただし以下の2つの制約を加える.

- Interpreter が認知しない文字列が指定されている場合, シンタックスエラーとする
- マッチ・ヒットしなかった等返すべきデータがない場合はデータを付帯しない

### 2.4 Interpreter に渡すデータ形式

Interpreter には以下の形式からなるデータの list を渡す (Prompt).
Category が多層的である場合は Screen 直下からの名前を list に格納する.

```python
{
  "screen_id": "screen1",
  "positive": [
    {
      "path": ["category1", "category1.1"], # 最右が pattern をもつ実際の Category
      "tokens": [{"token": "pos1", "weight": 1.0}, ...],
    },
    ...
  ],
  "negative": [
    {
      "path": ["category1", "category1.1"],
      "tokens": [{"token": "neg1", "weight": 1.2}, ...],
    },
    ...
  ],
}
```

**`tokens` が空の場合, この dict は append されない.**

Interpreter との共用クラスの定義は以下の通り.

```python
@dataclass
class Token:
    token: str = ""
    weight: float = 0.0

@dataclass
class PromptParts:
  path: list[str]
  tokens: list[Token]

@dataclass
class Prompt:
  screen_id: str
  positive: list[PromptParts]
  negative: list[PromptParts]
```

以降簡単のため, 本書では以下の形を `Token("pos1", 1.0)` と表すこととする.

```python
{"token": "pos1", "weight": 1.0}
```

#### 2.4.1 Screen が発火しなかった場合

いずれの Screen の `ignition` (後述)も未発火であった場合は, `screen_id` が `None` の Prompt が返される.

```python
{
  "screen_id": None,
  "positive": [],
  "negative": []
}
```

#### 2.4.2 発火したがマッチ・ヒットしなかった場合

いずれの Rule もマッチ・ヒットしなかった, かつ `default` (後述)も未定義の場合, 発火した `screen_id` のみが書かれた Prompt が返される.

```python
{
  "screen_id": "screen1",
  "positive": [],
  "negative": []
}
```

#### 2.4.3 備考

同じ token をもつ Token が tokens 内に混在していてもよいものとする(dedupe は Interpreter に委任).

---

## 3. `ignition` (発火条件)

ルールを適用するかどうかを判定する条件. Python `re.search` で評価される.

**制約:**

- バックスラッシュは必ずエスケープ (AML 仕様: `\\s`, `\\d` など), もしくは `'`で囲むこと
- 可変長後読み(`(?<=...)` で `*` や `+`)は禁止 (python re 制限)
- キャプチャグループ `()` の番号は左から自動採番

### 3.1 記述例

単項の正規表現で指定する. キャプチャ範囲は常に全体とする.

```yaml
ignition: "Test:"
```

### 3.2 振る舞い

- 各 Category のうち, 初めてマッチしたもののみのデータを付帯する (Screen は混在しない)
- マッチしない Screen についてはデータを付帯しない

---

## 4. Category 定義

### 4.1 記述例

`pattern` キーを持つオブジェクトが Category 定義として認識される.  

```yaml
category:
  pattern: "[0-9]{2},\\s(\\w*)"
  capturegrp: 1
  maps:
    #...
```

Screen 下に階層をいくら掘っても, 本 DS としては有効な記法とみなす.

```yaml
screen1:
  ignition: #...
  category1:
    category1.1:
      category1.1.1:
        pattern: # このキーを持つものが実 Category
```

上記の場合, 返すデータは以下のようになる.

```python
{
  "screen_id": "screen1",
  "positive": [
    {
      "path": ["category1", "category1.1", "category1.1.1"],
      "tokens": [...],
    }
    ...
  ],
  "negative": [
    # positive と同様
    ...
  ]
}
```

### 4.2 必須プロパティ

#### 4.2.1 `pattern`

Python `re.search` で評価される正規表現を指定する.

**制約:**

- バックスラッシュは必ずエスケープ (AML 仕様: `\\s`, `\\d` など), もしくは `'`で囲むこと
- 可変長後読み(`(?<=...)` で `*` や `+`)は禁止 (python re 制限)
- キャプチャグループ `()` の番号は左から自動採番

```yaml
pattern: "[0-9]{2},\\s(\\w*)"
pattern: 'test:\s(.+?)'
pattern: "(sunny|rainy|cloudy)"
pattern: "(1|2)[0-9]{3}/([0-9]{2})"  # 2つのキャプチャグループ
```

マッチした場合に, キャプチャした文字列をもとに以下の対応処理に続く.

#### 4.2.2 `maps` / `ranges` / `intervals`

マッチした文字列をプロンプトに変換する方法 (Rule) を定義. **どれか一つが必須.**
2つ以上記述されている場合はシンタックスエラーとする.

pattern が複数回マッチした場合, 各マッチを独立に処理し, 得られた各トークンは順にリストに追加される.

記法については後述.

### 4.3 オプションプロパティ

#### 4.3.1 `capturegrp`

使用するキャプチャグループのインデックス.  
指定された番号のキャプチャグループが存在しない場合, そのマッチは無視される(例外にはならない).
未定義の場合は `0` と同義.

- `0`: パターン全体のマッチ
- `1`, `2`, ...: 各キャプチャグループ

```yaml
pattern: "name:\\s(\\w+)"
capturegrp: 1  # \\w+ の部分を使用
```

```yaml
pattern: "(1|2)[0-9]{3}/([0-9]{2})"
capturegrp: 2  # 2番目のグループ(2桁部分)を使用
```

#### 4.3.2 `default`

`pattern` に **マッチはした**が, `maps` / `ranges` / `intervals` の**いずれの Rule にもヒットしなかった**場合に適用されるフォールバック.

```yaml
default: "unknown"
default: (cloudy:1.3)
default:
  positive: fallback,FallBack
  negative: FALLBACK
```

- `pattern` に1度もマッチしなかった場合は適用されない
- `pattern` にマッチし, かつ `maps` / `ranges` / `intervals` のいずれの Rule にもヒットしなかった場合に適用される
- よって **`capturegrp` が `0` (もしくは未定義)の場合, `default` が採用されることはない**

以上のように `default` は `maps` / `ranges` / `intervals` の各ルールと同じ評価パスを通る.

#### 4.3.3 `import`

YAML 内にすでに記述されている Rule を再度記述する場合に用いる.

`import` の引数にはリストによって, Screen ID 及び Category のパスを記述する(下記参照).
また, 指定できるパスは同一ファイル内のものに限られる.

```yaml
import_src:
  ignition: "src"
  character:
    name:
      pattern: name:(.+?)
      capturegrp: 1
      maps:
        Hogemaru: hogemaru
        Fugami: fugami
      default: smith # ここは対象外
import_dst:
  ignition: "dst"
  name:
    pattern: NAME-(.+?) # パターン再定義
    capturegrp: 1
    import: [import_src, character, name]
    default: bob
import_dst2:
  ignition: "dst2"
  name:
    import: [import_dst, name] # パターン引き継ぎ
    default: alice
```

- インポートする Rule は `import` の記述箇所よりも上部に定義されていなければならない(シンタックスエラー)
- `pattern` が記述されている場合は上書きされ, **未定義の場合はインポート元から引き継がれる**
- `capturegrp` もこれに従う(インポート元で未定義の場合は仕様に則り `0`)
- インポート対象は `maps` / `ranges` / `intervals` のみ, **`default` はインポート対象外**
- Screen ID 及び Category のパスはインポートした側の記述に従う(上記の場合は `import_dst,name`)
- 多段インポート(すでにインポートしている Rule をインポートすること)は合法である

### 4.3.4 `recurse`

Category を再帰的に定義する.

`[(foo1)(foo2)][(bar1)(bar2)(bar3)][(baz1)]` といった文字列から `foo1,foo2,bar1,bar2,bar3,baz1` を抜き出すなど, 複数回のグローバルマッチが必要な場合に用いる.

```yaml
brackets_parentheses:
  pattern: '\[([^\[\]]+)\]'
  capturegrp: 1
  recurse:
    parentheses:
      pattern: '\(([^\(\)]+)\)'
      capturegrp: 1
      maps:
        foo1: foo1
      default: foobar
```

処理は以下のように実施される.

1. 与えられた文字列に対して `\[([^\[\]]+)\]` を実施
2. こうして得た各部分文字列について `\(([^\(\)]+)\)` を実施

- Category のパスは最下層の `pattern` に紐づくものまでのすべてをとる(上記の場合は `brackets_parentheses,parentheses`)
- `default` は同階層の `pattern` に対するフォールバックとする
- `recurse` が存在する `pattern` の `default` は原理上通らない(マッチすれば例外なく下層へ移譲するため)
- 再帰構造のインポート, 及び再帰先のインポートはどちらも合法である

```yaml
angles_parentheses:
  pattern: '\<([^\<\>]+)\>'
  capturegrp: 1
  import: [recursive, brackets_parentheses] # 再起構造のインポート
curlyblackets:
  pattern: '\{([^\{\}])\}'
  capturegrp: 1
  import: [recursive, brackets_parentheses, parentheses] # 再記先のインポート
```

- 再帰構造のインポートを行う場合, その再帰先に `default` が定義されているなら引き継がれる
- 再帰先の定義を別の再帰先で行うことは合法である

```yaml
hifen&quotes:
  pattern: '\-([^\-]+)\-'
  capturegrp: 1
  quotes: { import: [recursive, brackets_parentheses, parentheses] } # 再帰先を別の再帰先 import で定義
```

- 2段以上の再帰構造は合法である

```yaml
big:
  pattern: '\[([^\[\]]+)\]'
  capturegrp: 1
  middle:
    pattern: '\{([^\{\}]+)\}'
    capturegrp: 1
    small:
      pattern: '\(([^\(\)]+)\)"'
      capturegrp: 1
      import: [recursive, brackets_parentheses, parentheses] 
```

---

## 5. Rule 定義

### 5.1 `maps` - 文字列マッピング

抽出した文字列を**直接キーとしてマッピング**する方式.

```yaml
maps:
  <matched_value>: <entry>
```

#### 5.1.1 シンプルなマッピング

```yaml
pattern: "(sunny|rainy)"
maps:
  Sunny: sunny
  Rainy: rainy,wet
```

- キャプチャした値が `"Sunny"` なら `sunny` が Prompt に追加される
- キャプチャした値が `"Rainy"` なら `rainy,wet` が Prompt に追加される

#### 5.1.2 positive/negative 分離

```yaml
pattern: "(foo|bar)"
maps:
  summer:
    positive: hot
    negative: cold
  spring:
    negative: hot,(snow:1.1)
```

- `positive` / `negative` は独立
- **片方のみ定義してもよい**(negative のみも定義可能)

### 5.2 `ranges` - 値範囲マッピング

**キーと値の役割が逆転する**ことに注意.

```yaml
ranges:
  <prompt_key>: <range_entry>
```

- プロンプト(キー)に対して, 該当する値のリストを定義
- 抽出した値がリストに含まれていれば, キーが `tokens` として使用される

複数ヒットした場合は**それらすべてを採用**する.

#### 5.2.1 シンプルな範囲

```yaml
pattern: "([0-9]{2})"
capturegrp: 1
ranges:
  spring: ["03", "04", "05", "06"]
  summer: ["07", "08"]
  winter: ["12", "01", "02"]
```

- ヒットした値が `"03"` なら `spring` が `positive` に追加
- ヒットした値が `"07"` なら `summer` が `positive` に追加

#### 5.2.2 `positive` + `negative`

```yaml
ranges:
  (hoge:1.3):
    positive: ["hoge"]
    negative: HOGE,nope
  fuga:
    positive: FUGA,(nope:1.3)
    negative: ["fuga", "Fuga"]
```

- `positive` (もしくは `negative`) に含まれていれば **キー自体が `positive` (もしくは negative) として使用**
- キー部分(`(hoge:1.3)`, `fuga`)がプロンプト
- 一方を **条件リスト(list)**, 他方を **補助トークン(string)** として指定
- `positive` と `negative` の一方は必ず list でなければならず, 他方は string でなければならない

**設計意図:**

- list側: プロンプトキー自体を `positive`/`negative` のどちらに入れるか判定する条件
- string側: 条件成立時に**反対側**に同時追加する補助トークン

条件によってキー自体の `positive`/`negative` を切り替えたい場合は, 別々のキーとして定義すること.

#### 5.2.3 `positive` (もしくは `negative`) のみ

```yaml
(hoge:1.2):
  positive: ["Hoge"]
```

- キー `(hoge:1.2)` が `positive` (もしくは `negative`) として使用される

### 5.3 `intervals` - 区間マッピング

**キーと値の役割が逆転する**ことに注意.

```yaml
intervals:
  <prompt_key>: <intervals>
```

- **プロンプト(キー)** に対して, 該当する値の範囲(閉区間, 両端を含む)を定義
- 抽出した値が範囲内であれば, キーが `tokens` として使用される
- リストの長さは 2, かつ昇順でないといけない
- リストは数値以外の要素を含んでいてはいけない

```yaml
OK1: [20, 40.3]
OK2: ["20", "40.3"]
NG1: [1, 2, 3]
NG2: [40, 20]
NG3: [a, 20]
```

複数ヒットした場合は**それらすべてを採用**する.

#### 5.3.1: シンプルな範囲

```yaml
pattern: "(\\d+)"
capturegrp: 1
ranges:
  good: [71, 100]
  normal: [30, 70]
  bad: [0, 30]
```

- ヒットした値が `"40"` なら `normal` が Prompt に追加される
- ヒットした値が `"30"` なら `normal,bad` が Prompt に追加される
- ヒットした値が `"70.5"` なら Prompt には追加されない

#### 5.3.2: positive + negative

```yaml
ranges:
  (hoge:1.3):
    positive: [20, 40]
    negative: HOGE,nope
  fuga:
    positive: FUGA,(nope:1.3)
    negative: [60, 80]
```

- `positive` (もしくは `negative`) に含まれていれば **キー自体が `tokens` として使用**
- キー部分(`(hoge:1.3)`, `fuga`)が `tokens` プロンプト
- `positive` と `negative` の一方は必ず list でなければならず, 他方は string でなければならない

#### 5.3.3 `positive` (もしくは `negative`) のみ

```yaml
(hoge:1.2):
  positive: [20, 40]
```

- キー `(hoge:1.2)` が `tokens` として使用される

---

## 6. プロンプト文字列記法

### 6.1 基本形式

カンマ区切りでトークンを列挙. `"` や `'` での囲みは任意.

```yaml
positive: "pos1,pos2,pos3"
negative: neg1,neg2
```

列挙したプロンプトがデータとして返される場合は Prompt に格納される.

```python
{
  "screen_id": "screen1",
  "positive": [
    {
      "path": ["category1"],
      "tokens": [Token("pos1", 1.0), Token("pos2", 1.0), Token("pos3", 1.0)],
    }
  ],
  "negative": [
    {
      "path": ["category1"],
      "tokens": [Token("neg1", 1.0), Token("neg2", 1.0)],
    }
  ],
}
```

### 6.2 重み付き記法

括弧内で `(token:weight)` の形式で重みを指定.

```yaml
positive: foo,(bar:1.5),baz
negative: BAD,(worse:2.0)
```

- 重みを指定しない場合は `1.0` がデフォルト
- 重みは小数点も可能

### 6.3 スペースを含むトークン

スペースはそのまま保持される.
`ranges` や `intervals` の場合は `"` や `'` で囲むことは YAML 文法に抵触するので不可能.

```yaml
positive: blue hair,red eyes,long dress

black hair,(blue eye:1.2): ["bob"]
```

---

## 7. Screen 共通プロンプト

### 7.1 `common`

各 Screen において, すべてのマッチ結果に必ず追加したいプロンプトを指定する.  
順番については Interpreter に一任するが, 基本的には末尾の Boilerplate プロンプトを想定する.

```yaml
common:
  positive: "common positive,high quality"
  negative: "common negative,bad quality"
```

`maps` と同じく, 以下の記法も有効.

```yaml
common: common negative,low quality,blurry

common:
  negative: bad quality
```

また `common` は省略可能である.

返すデータの `path` キーは 空リストとなる.

```python
[ # positive
  ...,
  {
    "path": [],
    "tokens": [Token("common positive", 1.0), Token("high quality", 1.0)],
  }
]
[ # negative
  ...,
  {
    "path": [],
    "tokens": [Token("common negative", 1.0), Token("bad quality", 1.0)],
  }
]
```

### 7.2 `common` のインポート

YAML 内にすでに記述されている `common` を再度記述する場合に用いる.

`import` の引数には**リストで** Screen ID を記述する(下記参照).
指定できるパスは同一ファイル内のものに限られる.

```yaml
import_src:
  ignition: "src"
  character:
    ...
  common:
    positive: common pos
    negative: common neg
import_dst:
  ignition: "dst"
  name:
    ...
  common: [import_src] # 必ずリスト
```

- インポートする `common` は記述箇所よりも上部に定義されていなければならない(シンタックスエラー)
- Screen ID はインポートした側の記述に従う(上記の場合は `import_dst`)
- 多段インポート(すでにインポートしている `common` をインポートすること)は合法である

---

## 8. 処理フロー

1. **Interpreter 適合チェック**: Interpreter との紐づけ
2. **Ignition チェック**: `ignition` でテキストが発火条件を満たすか判定
3. **パターンマッチ**: 各 Category の `pattern` でテキストを検索
4. **値抽出**: `capturegrp` で指定されたグループの値を取得
5. **マッピング**: `maps` / `ranges` / `intervals` で値をプロンプトに変換
6. **共通プロンプト追加**: `common` を追加
7. **出力**: リストとして返す

---

## 9. YAML の例

```yaml
interpreter: SampleInterpreter
main:
  ignition: "(m|M)ain"
  name:
    pattern: '^name:\s(.+?),'
    capturegrp: 1
    maps:
      Hogemaru: hogemaru
      Fugami: (fugami:1.2)
      Foota:
        positive: foota,(boy:1.1)
        negative: barta
    default:
      positive: smith
  season:
    pattern: 'season:\s([0-9]{2})'
    capturegrp: 1
    ranges:
      spring: ["03", "04", "05"]
      summer:
        positive: ["07", "08", "09"]
        negative: cold
      autumn: ["10", "11"]
      winter: ["02"]
      (winter:1.1),snow: ["12", "01"]
      scorching heat:
        positive: cool
        negative: ["01", "02", "03", "04", "05", "06", "09", "10", "11", "12"]
    default: ordinary
  vitality:
    pattern: 'vitality:\s(.+?),'
    capturegrp: 1
    intervals:
      low:
        positive: [0, 50]
        negative: good
      high:
        positive: bad
        negative: [0, 70]
      middle: [40, 60]
      perfect:
        positive: [95, 100]
      ok:
        negative: [0, 40]
    default: average
  fashion:
    upper:
      pattern: 'upper:\s(.+?),'
      capturegrp: 1
      maps:
        Shirt: shirt
        T Shirt: t-shirt
    lower:
      pattern: 'lower:\s(.+?),'
      capturegrp: 1
      maps:
        Pants: pants
        Skirt: skirt
  common:
    positive: common main positive
    negative: common main negative
meta:
  ignition: "(m|M)eta"
  name:
    pattern: '^name:\s(.+?),'
    capturegrp: 1
    import: [main, name]
    default:
      positive: smith
  weather:
    pattern: "(sunny|rainy)"
    capturegrp: 1
    maps:
      sunny: sunny
      rainy: rainy
    default: cloudy
  location:
    pattern: "(room|city)"
    maps:
      room: room
      city: city
  common: [main]
```

### 9.1 入力例と出力例

- 入力

```txt
Main
name: Fugami, season: 11, vitality: 50, upper: Shirt, lower: Pants,
```

- 出力

```python
{
  "screen_id": "main",
  "positive": [
    {
      "path": ["name"],
      "tokens": [Token("fugami", 1.2)],
    },
    {
      "path": ["season"],
      "tokens": [Token("autumn", 1.0), Token("cool", 1.0)],
    },
    {
      "path": ["vitality"],
      "tokens": [Token("low", 1.0), Token("bad", 1.0), Token("middle", 1.0)],
    },
    {
      "path": ["fashion", "upper"],
      "tokens": [Token("shirt", 1.0)],
    },
    {
      "path": ["fashion", "lower"],
      "tokens": [Token("pants", 1.0)],
    },
    {
      "path": [],
      "tokens": [Token("common main positive", 1.0)],
    }
  ],
  "negative": [
    {
      "path": ["season"],
      "tokens": [Token("scorching heat", 1.0)],
    },
    {
      "path": ["vitality"],
      "tokens": [Token("good", 1.0)], Token("high", 1.0),
    },
    {
      "path": [],
      "tokens": [Token("common main negative", 1.0)],
    },
  ],
}
```

---

## 10. 制約・注意事項

### 10.1 正規表現

- 可変長後読み `(?<=pattern*)` は使用不可 (python re 制限)
- バックスラッシュは必ずエスケープ (AML 仕様: `\\` で記述)
- キャプチャグループの番号は左から順に自動採番(`(a)(b)` なら 1, 2)

### 10.2 トークン

- カンマ `,` はトークン区切り文字(トークン内には使用不可)
- 括弧 `()` は重み記法の予約文字
- **スペースはトークン内で使用可能**(例: `blue hair`)
- `(((foo)))`や`[[[foo]]]`の記法は非対応

### 10.3 マッピング

- `maps`, `ranges`, `intervals` は混在していればシンタックスエラー
- いずれも指定されていない場合はシンタックスエラー
- `ranges` 及び `intervals` では **key がプロンプト, value が検索対象値リスト**
- `maps` では **key が検索対象値, value がプロンプト**

### 10.4 予約語一覧

本 DS では, 以下のキーは **特別な意味を持つ予約語** として定義されている.  
Interpreter はこれらを遵守して Screen 名, Category 名を定義しなくてはいけない.

| 予約語        | 禁止              |
| ------------- | ----------------- |
| `interpreter` | Screen 名として   |
| `ignition`    | Category 名として |

### 10.5 命名上の注意

大文字 / 小文字は **区別される**.
