# Prompt Rule YAML 仕様書

本ドキュメントは、テキスト入力から **ポジティブ / ネガティブプロンプト** を自動生成するための YAML ルール仕様を定義する。
本仕様は、正規表現・優先度・重み付きトークン・positive/negative 分離を統一的に扱う DS (ドメイン固有言語)である。

---

## 目次

1. [全体構造](#1-全体構造)
2. [Ignitio (発火条件)](#2-ignition発火条件)
3. [フィールド定義](#3-フィールド定義)
4. [マッピングタイプ](#4-マッピングタイプ)
5. [プロンプト文字列記法](#5-プロンプト文字列記法)
6. [共通プロンプト](#6-共通プロンプト)
7. [フラグシステム](#7-フラグシステム)
8. [処理フロー](#8-処理フロー)
9. [完全な例](#9-完全な例)
10. [制約・注意事項](#10-制約注意事項)
11. [予約語一覧](#11-予約語一覧)
12. [型定義(参考)](#12-型定義参考)

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
      maps: <mapping>                   # または ranges, intervals
      default: <prompt>                 # オプション
  POSITIVE: <common_prompt>             # オプション
  NEGATIVE: <common_prompt>             # オプション
```

### 構造のルール

- `rulename` ルール名称(任意の文字列)
- `ignition`: 必須の発火条件
- フィールドは **任意の深さでネスト可能**(`pattern` キーで識別)
- `POSITIVE` / `NEGATIVE` は任意(存在すれば必ず末尾に追加)

---

## 2. Ignitio (発火条件)

ルールを適用するかどうかを判定する条件。Python `re.search` で評価される。

### 2.1 `any` モード(論理和)

いずれか1つでもマッチすればルールが発火。

```yaml
ignition:
  any: ["today:", "date:"]
```

### 2.2 `all` モード(論理積)

すべてのパターンがマッチした場合のみルールが発火。

```yaml
ignition:
  all: ["user:", "status:active"]
```

### 2.3 振る舞い

- 1つもマッチしない場合、**ルール全体が無効**(空文字列を返す)
- マッチした場合、以降のフィールド処理が実行される

---

## 3. フィールド定義

### 3.1 フィールドの識別

`pattern` キーを持つオブジェクトがフィールド定義として認識される。

```yaml
mainstat:
  character:      # セクション名(任意)
    name:         # フィールド名(任意)
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

- バックスラッシュは必ずエスケープ (AML 仕様: `\\s`, `\\d` など)
- 可変長後読み(`(?<=...)` で `*` や `+`)は禁止 (ython re 制限)
- キャプチャグループ `()` の番号は左から自動採番

```yaml
pattern: "[0-9]{2},\\s(\\w*)"
pattern: "(sunny|rainy|cloudy)"
pattern: "(1|2)[0-9]{3}/([0-9]{2})"  # 2つのキャプチャグループ
```

#### `maps` または `ranges` または `intervals`

マッチした文字列をプロンプトに変換する方法を定義。**どれか一つが必須。**
2つ以上記述されている場合は`maps` > `ranges` > `intervals`の優先順位。

pattern が複数回マッチした場合、各マッチを独立に処理し、
得られたトークンは通常のマージ規則に従って統合される。

---

### 3.3 オプションプロパティ

#### `priority` (integer)

プロンプト出力順序の優先度。

- **小さい数字ほど先頭に配置**
- 同じ優先度の場合は YAML 記述順
- 未指定の場合は **自動で最大優先度+1** が割り当てられる(最低優先度)

```yaml
priority: 1   # 最優先
priority: 10  # 低優先度
# 未指定      # 最低優先度(自動割り当て)
```

---

#### `capturegrp` (integer, default: 0)

使用するキャプチャグループのインデックス。
指定された番号のキャプチャグループが存在しない場合、
そのマッチは無視される(例外にはならない)。

- `0`: パターン全体のマッチ
- `1`, `2`, ...: 各キャプチャグループ

```yaml
pattern: "name:\\s(\\w+)"
capturegrp: 1  # \\w+ の部分を使用
```

```yaml
pattern: "(1|2)[0-9]{3}/([0-9]{2})"
capturegrp: 2  # 2番目のグループ(月部分)を使用
```

---

#### `lifetime` (string, default: volatile)

トークンを次回以降の評価へ持ち越すかどうかを指定する。

```yaml
lifetime: stable   # 超越
lifetime: volatile # 超越しない
# 未指定           # 超越しない
```

`stable` なトークンは、次回評価時に通常のフィールド出力と同様に扱われ、
`priority` と weight ルールに従ってマージされる。

---

#### `default` (string | object)

パターンに **マッチはしたが、`maps` / `ranges` / `intervals` のいずれのルールにもヒットしなかった場合** に適用されるフォールバック。

```yaml
default: "unknown"
default: "cloudy"
```

```yaml
default:
  positive: fallback
  negative: FALLBACK
```

- `pattern` に一度もマッチしなかった場合は適用されない
- `pattern` がマッチし、かつ `maps` / `ranges` / `intervals` の結果が空だった場合(条件不成立も含む)に適用される
- フラグ条件がある場合はそれにも従う

すなわち `default` は `maps` / `ranges` / `intervals` の各ルールと同じ評価パスを通る。

---

## 4. マッピングタイプ

### 4.1 `maps` - 文字列マッピング

抽出した文字列を **直接キーとしてマッピング** する方式。

```yaml
maps:
  <matched_value>: <entry>
```

#### 例1: シンプルなマッピング (ositive のみ)

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
- **片方のみ定義してもよい**(例: negative のみ定義可能)

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

- **プロンプト(キー)** に対して、該当する値のリストを定義
- 抽出した値がリストに含まれていれば、キーが `positive` もしくは `negative` として使用される

#### 例4.2.1: シンプルな範囲

```yaml
pattern: "([0-9]{2})"
capturegrp: 1
ranges:
  spring: ["03", "04", "05", "06"]
  summer: ["07", "08"]
  winter: ["12", "01", "02"]
```

- マッチした値が `"03"` なら → `spring` が `positive` に追加
- マッチした値が `"07"` なら → `summer` が `positive` に追加

#### 例4.2.2: `positive` + `negative`

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
- キー部分(`(hoge:1.3)`, `fuga`)が `positive` (もしくは negative) プロンプト
- `positive` と `negative` の一方は必ず list でなければならず, 他方は string でなければならない

#### 例4.2.3: `positive` (もしくは `negative`) のみ

```yaml
(hoge:1.2):
  positive: ["Hoge"]
```

- キー `(hoge:1.2)` が `positive` (もしくは `negative`) として使用される

---

### 4.3 `intervals` - 区間マッピング

**キーと値の役割が逆転する**ことに注意。

```yaml
ranges:
  <prompt_key>: <intervals>
```

- **プロンプト(キー)** に対して、該当する値の範囲を定義
- 抽出した値が範囲内であれば、キーが `positive` もしくは `negative` として使用される
- リストの長さは 2, かつ昇順でないといけない
- リストは数値以外の要素を含んでいてはいけない

```yaml
OK1: [20, 40.3]
OK2: ["20", "40.3"]
NG1: [1, 2, 3]
NG2: [40, 20]
NG3: [a, 20]
```

#### 例4.3.1: シンプルな範囲

```yaml
pattern: "(\\d+)"
capturegrp: 1
ranges:
  good: [71, 100]
  normal: [30, 70]
  bad: [0, 30]
```

- マッチした値が `"40"` なら → `normal` が `positive` に追加
- マッチした値が `"30"` なら → `normal,bad` が `positive` に追加
- マッチした値が `"70.5"` なら → `positive` には追加されない

#### 例4.3.2: positive + negative

```yaml
ranges:
  (hoge:1.3):
    positive: [20, 40]
    negative: HOGE,nope
  fuga:
    positive: FUGA,(nope:1.3)
    negative: [60, 80]
```

- `positive` (もしくは `negative`) に含まれていれば **キー自体が `positive` (もしくは `negative`) として使用**
- キー部分(`(hoge:1.3)`, `fuga`)が `positive` (もしくは `negative`) プロンプト
- `positive` と `negative` の一方は必ず list でなければならず, 他方は string でなければならない

#### 例3: `positive` (もしくは `negative`) のみ

```yaml
(hoge:1.2):
  positive: [20, 40]
```

- キー `(hoge:1.2)` が `positive` (もしくは `negative`) として使用される

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

これは `positive` / `negative` 共通の振る舞い。
重みが同一の場合、`priority` が小さい(先に評価された)ものが採用される。

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

## 7. 不可欠なルール

フィールドには、プロンプト生成の成否を判定するための必須条件を定義することができる。
不可欠なフィールドがマッチしなかった場合、そのルールセット全体が「情報不足」と判定され、プロンプト生成は失敗として扱われることを想定する。

以下この状態を**不可欠ルールが未達成であると**定める。


### 7.1 `essential` (EssentialScope, optional)

この機能は各フィールドのマッピングに `essential` を宣言して用いる。
`essential` には2つのスコープが存在する。

#### 7.1.1 `local`

各評価試行機会内でのみ必須となるルール。

同じ Screen 内の他のフィールドと組み合わせて評価され、`local` な不可欠ルールに1つでもマッチしなかったものがある場合は未達成と判定される。

```yaml
age:
  pattern: "age:([1-9]?[0-9])"
  essential: local
  intervals:
    adult: [30, 60]
```

#### 7.1.2 `global`

各評価試行機会を超越して必須となるルール。

どの Screen が発火した場合でも、`global` な不可欠ルールに1つでもマッチしなかったものがある場合は未達成と判定される。

```yaml
name:
  pattern: "(name1|name2)"
  lifetime: stable
  essential: global  # stable と組み合わせることで Screen を超越して必須化
  maps:
    name1: name1
```

**制約**: `global` は `lifetime: stable` と組み合わせて使用することが推奨される。
`volatile` かつ `global` な不可欠ルールは実質的に `local` と同じ挙動となる。

### 7.2 評価ルール

1. `local`: その Screen 内で `essential` 指定されたすべてのフィールドがマッチした場合のみ達成
2. `global`: 過去のすべての評価を通じて、global essential が一度でも達成されている場合のみ達成

つまり `global` は `stable` によって継続されたトークンによって達成条件が満たされる。
後述の要因で未達成であった場合、再び達成するまでプロンプトの満足な生成は行われない(下記)。

- 達成: 通常通りプロンプトを生成し、`stable` トークンを継続
- 未達成: 空文字列 ("", "") を返し、すべての `stable` トークンを抹消

### 7.3 未発火と未達成の違い
| 状態   | `ignition` | `essential` | 結果                          | 画面の解釈           |
| ------ | ---------- | ----------- | ----------------------------- | -------------------- |
| 通常   | OK         | OK          | プロンプト生成、`stable` 継続 | 適切な情報を持つ画面 |
| 未達成 | OK         | NG          | 空文字列、`stable` 抹消       | 情報不足の画面       |
| 未発火 | NG         | -           | 何もしない、`stable` 継続     | パース対象外の画面   |

#### プロンプト生成の成否判定

各評価機会において、以下の条件により達成是非が判定される。

${\rm achieved\ essentials}\subset{\rm local\ essentials}\cup{\rm global\ essentials}$

### 7.4 実例

```yaml
main:
  ignition:
    any: ["main"]
  name:
    pattern: "(name1|name2)"
    capturegrp: 1
    lifetime: stable
    essential: global # global は stable がないと意味がない
    maps:
      name1: name1
      name2: name2
  age:
    pattern: "age:([1-9]?[0-9])"
    capturegrp: 1
    lifetime: stable
    essential: local
    intervals:
      child: [0, 10]
      teen: [10, 20]
      young: [20, 30]
      adult: [30, 60]
      old: [60, 99]
  vibe:
    pattern: "(good|bad)"
    capturegrp: 1
    essential: local # local は screen 範囲内で不可欠, global は screen を超越して不可欠
    maps:
      good: good
      bad: bad
  expression:
    pattern: "(smile|crying)"
    capturegrp: 1
    maps:
      smile: smile
      crying: crying
meta:
  ignition:
    any: ["meta"]
  where:
    pattern: "(room|city)"
    capturegrp: 1
    essential: local
    maps:
      room: room
      city: city
  when:
    pattern: "(morning|day|night)"
    capturegrp: 1
    essential: global # volatile でもエラーではなく local と同じ作用
    maps:
      morning: morning
      day: day
      night: night
  country:
    pattern: "(JPN|US|UK|CHN)"
    capturegrp: 1
    maps:
      JPN: JPN
      US: US
      UK: UK
      CHN: CHN
```

これに対し以下のテキストを順に読み込ませた場合の動作を記す。

```txt
1.
"meta room day"
meta の essential 未達成
プロンプト: "" (空文字列)

2.
"main good crying"
main の essential 未達成
プロンプト: "" (空文字列)

3.
"main name1 good"
同上
プロンプト: "" (空文字列)

4.
"main name1 good age:35"
main の essential 達成, name1 と age が次回も継続
プロンプト: "name1,adult,good"

5.
"meta city morning"
meta の essential 達成, 前回継続分も持ち越し
プロンプト: "name1,adult,city,morning"

6.
"main smile"
main 未達成, 継続分抹消
プロンプト: "" (空文字列)

7.
"meta JPN morning room"
global essential の name がないので未達成
プロンプト: "" (空文字列)

8.
"main name2 bad age:70"
main 達成
プロンプト: "name2,old,bad"

9.
"dummy"
未点火, stable は持ち越し
プロンプト: "name2,old" (空文字列)

10.
"meta room day"
name(global) と meta の local essential 達成, 未点火を挟んでも stable 継続分は表示される
プロンプト: "name2,old,room,day"

11.
"meta UK city"
meta 未達成
プロンプト: "" (空文字列)

12.
"meta city night US"
meta 達成も, もう name(global) がないので未達成扱い
プロンプト: "" (空文字列)

```

---

## 8. フラグシステム

フラグは、プロンプト生成時に使用される **評価コンテキスト** を提供する仕組みである。
トークンとは異なり、出力文字列には直接現れない。

各フィールドのマッピングは、以下を宣言できる：

- `add` : 成立した場合に有効化するフラグ
- `remove` : 成立した場合に無効化するフラグ
- `with` : 成立するために必要なフラグ条件

フラグは **一回の評価の中でのみ有効** であり、次回評価へは持ち越されない。

### 8.1 基本概念

フラグは単なる名前付きの状態値であり、
```txt
ある Rule が成立 → フラグを追加
次の Rule はそのフラグを参照して成立判定
```
という順序で評価される。
フラグは positive / negative のどちらにも属さない。
純粋に条件判定専用である。

### 8.2 `add` (str | list, optional)

ルールが成立した場合に **有効化されるフラグ** を定義する。
集合への要素追加(つまりその要素からなる単集合との和)に対応し、要素が重複する場合は新たに加えない。
`with` により不成立と判定された場合は有効化されない。

```yaml
maps:
  sunny:
    add: [hot]
    positive: sunny
  rainy:
    add: [cold, wet]
    positive: rainy
  snow:
    add: cold # add は atom 単項指定の場合に限りリスト形式を取らなくても OK
    positive: snow
```
- 単数指定の場合はリストで書いても書かなくてもよい
- 複数指定の場合はリストで書く

### 8.3 `remove` (str | list, optional)

ルールが成立した場合に **無効化されるフラグ** を定義する。
その要素からなる単集合との差に対応し、要素が存在しない場合は何も起こらない。
`with` により不成立と判定された場合は無効化されない。

```yaml
maps:
  room:
    remove: [outdoors]
    positive: room
  office:
    add: [outdoors, private]
    positive: office
  city:
    remove: indoors # remove も atom 単項指定の場合に限りリスト形式を取らなくても OK
    positive: city
```
- 単数指定の場合はリストで書いても書かなくてもよい
- 複数指定の場合はリストで書く

## 8.4 `add` と `remove` の順序
`add` と `remove` はyaml内の表記順の通りに実行される。

```yaml
A:
  add: foo # {} ∪ {foo} = {foo}
  remove: foo # {foo} - {foo} = {}

B:
  remove: bar # {} - {bar} = {}
  add: bar # {} ∪ {bar} = {bar}
```

### 8.5 `with` (Condition, optional)

そのルールが成立するために必要な フラグ条件 を定義する。

`with` はルール内で初め評価される。
条件が満たされない場合そのエントリは 無効 となり、positive / negative / add / remove のすべてが適用されない。

with は論理式として記述する。

#### 8.5.1 単項 (Atom)

```yaml
with: indoors
```
これは以下と等価：
```yaml
with:
  all: [indoors]
```
indoors が存在する場合のみ成立。

### 8.5.2 否定 (NotCond)

```yaml
with:
  not: indoors
```
indoors が存在しない場合のみ成立。

組み合わせる場合は以下のように記述する。
```yaml
{ not: p }
```

### 8.5.3 論理和 (AnyCond)

```yaml
with:
  any: [hot, cold]
```
いずれかが成立すればよい。

### 8.5.4 論理積 (AllCond)

```yaml
with:
  all: [private, indoors]
```
すべて成立する必要がある。

### 8.5.5 組み合わせ

これらを組み合わせた例は以下の通り。

- $\neg(p\land\neg q)$
```yaml
with:
  not: { all: [p, { not: q }] }
```

- $(p\land q)\lor(\neg r\land s)$
```yaml
with:
  any: [{ all: [p, q] }, { all: [{ not: r }, s] }]
```

- $p_1\land(\neg((p_2\lor\neg p_4)\land(p_4\lor(p_2\land p_3))))$
```yaml
with:
  all: [p1, { not: { all: all: [{ any: [p2, { not: p4 }] }, { any: [p4, { all: [p2, p3] }] }] } }]
```
※通常はより簡単かつ同値な式を指定することをおすすめする。
$p_1\land(\neg p_2\lor (\neg p_4\land\neg p_3))$
```yaml
with:
  all: [p1, { any: { not: p2 }, { all: [{ not: p3 }, { not: p4 }] } }]
```

#### Tips
$p\Rightarrow q$は数理論理の定義に則り$\neg p \lor q$とすればよい:
```yaml
with:
  any: [{ not: p }, q]
```

また、yamlのフォーマットに則り任意に入れ子に出来る。
```yaml
with:
  all:
    - private
    - any:
      - indoors
      - hot

with:
  all: [private, { any: [indoors, hot] }] # これと等価
```

### 8.6 評価タイミング

フラグは priority 順 に評価される。
先に評価されたルールが add したフラグが後続の with 判定に使用される。
後方のルールは前方の結果のみを参照できる。

### 8.7 循環参照と自己参照

循環依存が存在してもエラーにはならない。
```yaml
A:
  with: flag_b # 不成立
  add: flag_a # 実行されず

B:
  with: flag_a # 不成立
  add: flag_b
```
前方優先評価の結果どちらの条件も満たされず、両者とも不成立となる。

また自己参照が存在する場合、やはり前方優先評価の結果 add が実行されない。
```yaml
A:
  with: flag_a # 不成立
  add: flag_a

B:
  add: flag_b # with の後に判定, 実行されない
  with: flag_b # 優先評価, 不成立
```

これらはともに正常系として扱われる。

### 8.8 矛盾の扱い

同一評価中に以下のような表記がある場合、素直に数理論理的な解釈を行う。
```yaml
with:
  all: [hot, { not: hot }] # 恒偽

with:
  any: [hot, { not: hot }] # 恒真
```

### 8.9 フラグの寿命

フラグは次回のプロンプト生成に引き継がれる。
`volatile` なルールについては、マッチの瞬間にアクティブなフラグによってのみ成立可否が判定される。
`stable` なルールについては、マッチの瞬間に加え、次回引き継ぎのためのエンキューの際にも成立可否が判定される。

以下のyamlを例にする。
```yaml
stable:
  stable-rule:
    pattern: "(stable1|stable2)"
    capturegrp: 1
    lifetime: stable
    maps:
      stable1:
        with: volatile1
        add: stable1
        positive: stable1
      stable2:
        with: volatile2
        add: stable2
        positive: stable2
  volatile-rule:
    pattern: "(volatile1|volatile2|volatile3)"
    capturegrp: 1
    maps:
      volatile1:
        add: volatile1
        positive: volatile1
      volatile2:
        add: volatile2
        positive: volatile2
      volatile3:
        remove: [volatile1, volatile2]
        positive: volatile3
```

これに順にテキストを適用していった様子が下記の通り。
```txt
1.
"TEST volatile1"
アクティブフラグ: {volatile1}
ポジティブプロンプト: "volatile1"

2.
"TEST stable1"
ここは成立
アクティブフラグ: {volatile1, stable1}
ポジティブプロンプト: "stable1"

3.
"TEST volatile3"
しかしここで一旦 volatile1 が非アクティブに、トークン "stable1" は次回に引き継がれないことが決定
アクティブフラグ: {stable1}
ポジティブプロンプト: "stable1,volatile3"

4.
"TEST volatile2"
ポジティブプロンプト: "volatile2"
```

---

## 9. 処理フロー

1. **Ignition チェック**: テキストが発火条件を満たすか判定
2. **Priority ソート**: すべてのフィールドを priority 順に並べる
3. **パターンマッチ**: 各フィールドの pattern でテキストを検索
4. **値抽出**: capturegrp で指定されたグループの値を取得
5. **マッピング**: maps または ranges または intervals で値をプロンプトに変換
6. **マージ**: 同じトークンは最大重みで統合 (ositive/negative は完全に独立)
7. **共通プロンプト追加**: POSITIVE/NEGATIVE を末尾に追加
8. **出力**: カンマ区切りの文字列として出力

### 9.1 マージ規則の詳細

- すべてのフィールド結果を priority 順に評価
- positive / negative は **完全に独立して集約**
- token 衝突時は `max(weight)`
- 特例処理なし(すべて同一ロジック)
- stable 指定のトークンも priority の影響を受ける
- 最終的な並び順は period → priority の順で決定される

---

## 10. 完全な例

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
      essential: global
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
      essential: local
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
  s1:
    pattern: "(\\d+)"
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
  stable:
    stable-rule:
      pattern: "(stable1|stable2)"
      capturegrp: 1
      lifetime: stable
      maps:
        stable1:
          with: volatile1
          add: stable1
          positive: stable1
        stable2:
          with: volatile2
          add: stable2
          positive: stable2
    volatile-rule:
      pattern: "(volatile1|volatile2|volatile3)"
      capturegrp: 1
      maps:
        volatile1:
          add: volatile1
          positive: volatile1
        volatile2:
          add: volatile2
          positive: volatile2
        volatile3:
          remove: [volatile1, volatile2]
          positive: volatile3
  POSITIVE: "sub common positive"
  NEGATIVE: "sub common negative"
```

### 入力例

```txt
today: 2026/02/05, month: 02, 23, Alice (mood: happy) foobarHogefuga
```

### 出力例

```txt
POS: foo,(bar:1.3),fuga,winter,happy,smile,unknown character,masterpiece,best quality
NEG: FOO,BAR,nyome,(nope:1.3),(hoge:1.2),FUGA,sad,crying,worst quality,low quality,blurry
```

#### 処理の内訳

1. **foobar** (priority: 1):
   - `foo` → positive: `foo`, negative: `FOO,(nope:1.1)`
   - `bar` → positive: `(bar:1.3)`, negative: `BAR,(nope:1.2),nyome`
   - 重み: `(bar:1.3)` が採用(`(bar:1.1)` より大きい)

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

## 11. 制約・注意事項

### 11.1 正規表現

- 可変長後読み `(?<=pattern*)` は使用不可 (ython re 制限)
- バックスラッシュは必ずエスケープ (AML 仕様: `\\` で記述)
- キャプチャグループの番号は左から順に自動採番(`(a)(b)` なら 1, 2)

### 11.2 Priority

YAML に記述された priority 値は、読み込み後に以下のルールで再採番される。

1. priority が小さい順に並べる
2. 同値の場合は YAML 記述順
3. 1, 2, 3, ... の連番に振り直す
4. priority 未指定 (owest_priority)は最後に回される

したがって、ユーザーが指定した数値は
**相対順序を決めるための値**としてのみ使用される。

### 11.3 トークン

- カンマ `,` はトークン区切り文字(トークン内には使用不可)
- 括弧 `()` は重み記法の予約文字
- **スペースはトークン内で使用可能**(例: `blue hair`)
- `(((foo)))`や`[[[foo]]]`の記法は非対応

同一 token が複数回出現した場合、以下の順で採用が決定される。

1. **より大きい weight** を持つもの
2. weight が同一なら **priority が小さい(先に評価された)** もの

これは positive / negative で独立に行われる。

### 11.4 マッピング

- `maps` と `ranges` と `intervals` はこの順で優先的に適用される
- `ranges` 及び `intervals` では **key がプロンプト、value が検索対象値リスト**
- `maps` では **key が検索対象値、value がプロンプト**
- negative-only 定義が可能 (ositive を省略可能)

---

## 12. 予約語一覧

本 DS (Prompt Rule YAML)では、以下のキーは **特別な意味を持つ予約語** として定義されている。
これらのキーは、ユーザー定義のセクション名・フィールド名・値として使用してはならない。

### 12.1 ルート / 構造予約語

| 予約語     | 意味                     |
| ---------- | ------------------------ |
| `ignition` | 発火条件定義             |
| `POSITIVE` | 共通ポジティブプロンプト |
| `NEGATIVE` | 共通ネガティブプロンプト |

### 12.2 Ignition 関連

| 予約語 | 意味                     |
| ------ | ------------------------ |
| `any`  | 論理和(いずれかがマッチ) |
| `all`  | 論理積(すべてがマッチ)   |

### 12.3 フィールド定義予約語

| 予約語       | 意味                           |
| ------------ | ------------------------------ |
| `pattern`    | 正規表現パターン               |
| `priority`   | 出力順序の優先度               |
| `capturegrp` | 使用するキャプチャグループ番号 |
| `lifetime`   | 超越するかどうか               |
| `stable`     | 超越する                       |
| `volatile`   | 超越しない                     |
| `essential`  | 不可欠ルールのスコープ         |
| `global`     | 評価機会を超越して不可欠       |
| `local`      | 評価機会内で不可欠             |
| `default`    | マッチ失敗時のフォールバック   |

### 12.4 マッピング方式予約語

#### 12.4.1 Maps 型

| 予約語     | 意味                            |
| :--------- | :------------------------------ |
| `maps`     | 値 → プロンプトの直接マッピング |
| `positive` | ポジティブプロンプト            |
| `negative` | ネガティブプロンプト            |

#### 12.4.2 Ranges 型

| 予約語     | 意味                                           |
| ---------- | ---------------------------------------------- |
| `ranges`   | プロンプト → 値集合の逆引きマッピング          |
| `positive` | マッチ対象となる値リスト(ポジティブプロンプト) |
| `negative` | マッチ対象となる値リスト(ネガティブプロンプト) |

※ `ranges` では **キー自体が positive プロンプト** として使用される。

#### 12.4.3 intervals 型

| 予約語      | 意味                                         |
| ----------- | -------------------------------------------- |
| `intervals` | プロンプト → 値区間の逆引きマッピング        |
| `positive`  | マッチ対象となる値区間(ポジティブプロンプト) |
| `negative`  | マッチ対象となる値区間(ネガティブプロンプト) |

※ `intervals` では **キー自体が positive プロンプト** として使用される。

### 12.5 フラグシステム

| 予約語   | 意味                               |
| -------- | ---------------------------------- |
| `with`   | アクティブフラグと照合する条件定義 |
| `add`    | フラグの有効化                     |
| `remove` | フラグの無効化                     |
| `not`    | 条件式における否定                 |
| `any`    | 条件式における論理和               |
| `all`    | 条件式における論理積               |

### 12.6 プロンプト文字列予約記号(構文レベル)

| 記号             | 意味                     |
| ---------------- | ------------------------ |
| `,`              | トークン区切り           |
| `(token:weight)` | 重み付きトークン表記     |
| `()`             | 重み指定のための予約構文 |

### 12.7 命名上の注意

- 上記予約語は **セクション名・フィールド名・値として使用不可**
- 大文字 / 小文字は **区別される**
  - `POSITIVE` / `NEGATIVE` は大文字のみ有効
- 将来の拡張のため、以下の語も **使用非推奨**：
  - `enable`, `disable`, `when`, `unless`, `else`

### 12.8 実装上の扱い(参考)

- 予約語は **パーサ段階で除外 / 特別処理**
- 未知のキーはすべてユーザー定義セクションとして扱う
- 特例ルールは存在しない(予約語のみが制御構造)

---

## 13. 型定義(参考)

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
  essential?: EssentialScope
  default?: string | PromptEntry;
  with?: Condition
  add?: string[] | string
  remove?: string[] | string
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

type IntervalsField = {
  intervals: {
    [prompt: string]: string[] | IntervalEntry;
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

type IntervalEntry = {
  positive?: float[] | string;
  negative?: string | float[];
};
```

---

## 14. 設計思想(参考)

### 14.1 "書く側が迷わない" DSL

- 一貫したルール(特例処理なし)
- YAML がそのまま DSL になる
- positive / negative は対称設計

### 14.2 Weight 競合は常に決定的

- 同一 token の重複は必ず `max(weight)` で解決
- 処理順序に依存しない

### 14.3 正規表現は抽出にのみ集中

- パターンマッチは **抽出** のみ
- 意味解釈(プロンプト化)は YAML 側に寄せる
- 責務の分離により保守性を向上

---

以上が本 YAML 仕様の完全定義である。
