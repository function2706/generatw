# Interpreter ScreenTable 仕様書

本ドキュメントは, `interpreter.py` における `ScreenTable` / `ScreenConfig` / `CategoryConfig` の設計仕様を定義する.
YAML 仕様書で定義された `Prompter` の出力 (`Prompt`) をさらに加工・管理するための, Interpreter 側のレイヤーに相当する.

---

## 目次

1. [全体構造](#1-全体構造)
2. [ScreenTable](#2-screentable)
3. [ScreenConfig](#3-screenconfig)
4. [CategoryConfig](#4-categoryconfig)
5. [編集パイプライン (`edit`)](#5-編集パイプライン-edit)
6. [Memory / Record](#6-memory--record)
7. [記述例](#7-記述例)
8. [制約・注意事項](#8-制約注意事項)

---

## 1. 全体構造

`Interpreter` は YAML から生成した `Prompter` に加え, Python コード側に `ScreenTable` を持つ.
`ScreenTable` は Screen ID をキーとして `ScreenConfig` を保持し, `Prompter` が返す生の `Prompt` に対してふるいがけ・重複排除・ソート・メモリ同期を施す.

```python
type ScreenTable = dict[
    str,          # Screen ID (YAML の Screen 名と一致)
    ScreenConfig,
]
```

`Interpreter.__init__` において `screen_table` を定義する. Screen ID の登録順序が優先順位を表す (dict の挿入順を利用).

### 1.1 記述例

実装では `StrEnum` を用いて Screen 名 / Category 名を定数として定義しておくことを推奨する.

```python
class Scr(StrEnum):
    screen1 = "screen1"
    screen2 = "screen2"


class Cat(StrEnum):
    key = "key"
    cat1 = "cat1"
    cat2 = "cat2"
    cat2_sub = "cat2_sub"
    # ...


class MyInterpreter(Interpreter):
    def __init__(self, yamlpath: Path):
        super().__init__(yamlpath, Cat.key)  # keyname = "key"

        self.screen_table = {
            Scr.screen1: ScreenConfig.set(
                cat_configs={
                    (Cat.key,):       (None, True),
                    (Cat.cat1,):      (None, True),
                    (Cat.cat2, Cat.cat2_sub): (None, False),
                    # ...
                },
                sufficiency=Has((Cat.key,)),
            ),
            Scr.screen2: ScreenConfig.set(
                # ...
            ),
        }
```

---

## 2. ScreenTable

### 2.1 役割

| 役割                     | 説明                                         |
| ------------------------ | -------------------------------------------- |
| Screen の列挙            | Interpreter が認識する Screen の完全なリスト |
| 優先順位の表現           | `dict` の挿入順が処理優先度を表す            |
| Screen ↔ Config の紐づけ | 各 Screen に対する加工ルールを保持           |

### 2.2 制約

- `screen_table` に存在しない `screen_id` の `Prompt` が到来した場合, `make_prompt()` が `ValueError` を送出する
- YAML の Screen 名と `screen_table` のキーは完全一致でなければならない (大文字・小文字区別あり)
- `check_sufficiency_of()` も同様に `screen_table` を参照するため, 全 Screen を登録する必要がある

---

## 3. ScreenConfig

各 Screen に対する加工ルールを定義するクラス. `ScreenConfig.set()` クラスメソッドで生成する.

```python
@classmethod
def set(
    cls,
    cat_configs: dict[CategoryPath, tuple[Expr | None, bool]],
    sufficiency: Expr | None = None,
    request_cats: dict[str, list[CategoryPath]] | None = None,
    takeover_cats: list[CategoryPath] | None = None,
) -> ScreenConfig
```

### 3.1 `cat_configs`

**必須.** Interpreter がこの Screen で扱う `CategoryPath` の完全なリストと, 各 CategoryPath に対する設定のマッピング.
値は `tuple[Expr | None, bool]` であり, それぞれ以下を表す.

| インデックス | 型             | 意味                    |
| ------------ | -------------- | ----------------------- |
| `[0]`        | `Expr \| None` | `sift_condition` (後述) |
| `[1]`        | `bool`         | `log_report` (後述)     |

`cat_configs` の登録順序は `sort()` のソート基準となる.

> `CategoryPath` は `tuple[str, ...]` の型エイリアス. YAML 階層に対応する.
> `StrEnum` を使っている場合も通常のタプルとして記述できる.
>
> ```txt
> category > category.sub  ->  (Cat.category, Cat.sub)
> category                 ->  (Cat.category,)  # 単項タプルの ',' を忘れないこと
> ```

#### 3.1.1 記述例

```python
# cat_b が存在しない場合のみ cat_c を残す条件式
expr_no_b = ~Has((Cat.cat_b,))

cat_configs={
    (Cat.key,):              (None, True),        # 常に残す, Report あり
    (Cat.cat_a,):            (None, False),       # 常に残す, Report なし
    (Cat.cat_b,):            (None, True),
    (Cat.cat_c,):            (expr_no_b, True),   # cat_b がない場合のみ残す
    (Cat.meta, Cat.sub):     (None, False),
},
```

### 3.2 `sufficiency`

**省略可 (デフォルト: 恒真).** この Screen の `Prompt` が「生成に十分」とみなす条件式.

`check_sufficiency_of()` によって評価され, 全 CategoryPath の集合 (`existing_paths`) を引数に `eval()` を呼ぶ.
`None` を渡した場合は `TrueExpr()` が適用され, 常に `True` を返す.

#### 3.2.1 記述例

```python
# key のみ必須
sufficiency=Has((Cat.key,))

# key と cat1 の両方が必須
sufficiency=Has((Cat.key,)) & Has((Cat.cat1,))
```

### 3.3 `request_cats`

**省略可 (デフォルト: `{}`).** 他の Screen の記憶から, キーカテゴリーに基づいて引き継ぎたい CategoryPath を指定する.

- キーは取得元の Screen ID (`screen_table` に登録されていなくともよい)
- 値は取得したい CategoryPath のリスト
- キーカテゴリー (`keyname`) が合致する `Memory` が存在する場合のみ適用される
- 存在しない場合は無視される (例外にはならない)

#### 3.3.1 記述例

```python
# screen1 の記憶から cat1 / cat2 を key をキーに引き継ぐ
request_cats={
    Scr.screen1: [
        (Cat.cat1,),
        (Cat.cat2, Cat.cat2_sub),
    ]
},
```

### 3.4 `takeover_cats`

**省略可 (デフォルト: `[]`).** 直前の Screen から無条件で引き継ぎたい CategoryPath のリスト.

- `request_cats` より先に適用される (TakeOver -> Request の順)
- キーカテゴリーの有無に関係なく引き継ぐ

#### 3.4.1 記述例

```python
# 直前 Screen の key を無条件で引き継ぐ
takeover_cats=[
    (Cat.key,),
],
```

---

## 4. CategoryConfig

`cat_configs` の値部分 `tuple[Expr | None, bool]` を格納する内部クラス.
`ScreenConfig.set()` が自動的に `CategoryConfig.set()` を呼んで生成するため, 直接構築することはない.

```python
@dataclass(frozen=True)
class CategoryConfig:
    sift_condition: Expr  # ふるいがけ条件
    log_report: bool      # Report を残すか
```

### 4.1 `sift_condition`

`sift()` 処理において, この CategoryPath の `PromptParts` を残すかどうかの条件式.
`existing_paths` (その時点で存在する全 CategoryPath の集合) を引数として `eval()` が呼ばれる.
`None` を渡した場合は `TrueExpr()` が適用され, 常に残される.

#### 4.1.1 記述例

```python
# cat_a が存在する場合のみ cat_b を残す
(Cat.cat_b,): (Has((Cat.cat_a,)), True)

# cat_x / cat_y のいずれかが存在する場合のみ cat_z を残す
expr = Has((Cat.cat_x,)) | Has((Cat.cat_y,))
(Cat.cat_z,): (expr, False)

# 無条件で残す
(Cat.key,): (None, True)
```

### 4.2 `log_report`

`strip_reports()` において, この CategoryPath に紐づく `Report` を保持するかどうかのフラグ.

#### 4.2.1 記述例

```python
(Cat.key,):   (None, True),   # Report を残す
(Cat.cat_a,): (None, False),  # Report を捨てる
```

---

## 5. 編集パイプライン (`edit`)

`make_prompt()` は `Prompter` から得た `Prompt` を `ScreenConfig.edit()` に渡す.
`edit()` は以下の順序で処理を行う.

```txt
strip -> dedupe -> sift -> sync -> sort
```

### 5.1 `strip` — 不要 CategoryPath の除去

`cat_configs` に登録されていない CategoryPath を持つ `PromptParts` を削除する.
`common` (`path` が空リスト) は常に保持される.

### 5.2 `dedupe` — 重複トークンの統合

同一 `token` 文字列を持つ `Token` が複数の `PromptParts` にまたがって存在する場合, 以下のルールで一つに絞り込む.

| 観点                | ルール                                                         |
| ------------------- | -------------------------------------------------------------- |
| 採用するトークン    | `abs(weight - 1.0)` が最大のもの (同点は先着優先)              |
| 配置先 CategoryPath | `cat_configs` の登録順で最も早いもの (`common` は候補から除外) |
| 出現順序            | 元の `PromptParts` 内での出現インデックスを基準に昇順          |

### 5.3 `sift` — ふるいがけ

各 `PromptParts` の CategoryPath に紐づく `sift_condition` を評価し, 条件を満たさないものを除去する.
`common` は常に保持される.

### 5.4 `sync` — メモリ同期

TakeOver -> Request -> Offer の順で `Memory` / `Record` と同期する.

| フェーズ | 処理                                                                                                              |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| TakeOver | `takeover_cats` の各 CategoryPath を直前 Screen の `Memory` から引き継ぐ                                          |
| Request  | `request_cats` で指定した Screen の `Record` から, キーカテゴリー一致の `Memory` を参照し CategoryPath を補完する |
| Offer    | 現在の `Memory` のすべてのエントリをキーカテゴリーと紐づけて `Record` に登録する                                  |

### 5.5 `sort` — ソート

`cat_configs` の登録順に従って `PromptParts` を並べ替える.
登録されていない CategoryPath は末尾に置かれる.

---

## 6. Memory / Record

`Interpreter` は Screen をまたいだ状態保持のために `Memory` と `Record` を使用する.

```python
type Record = dict[
    KeyEntry,  # キーカテゴリーの Token 情報 (immutable)
    Memory,    # そのキーに紐づく Screen 全体の記憶
]
```

`keyname` は `Interpreter.__init__` で指定するキーカテゴリーの名前 (CategoryPath の末尾要素).
`sync()` において `Memory.get_key_entry(keyname)` によって参照される.

```python
# keyname = Cat.key ("key") として初期化する例
super().__init__(yamlpath, Cat.key)
```

| クラス        | 役割                                                     |
| ------------- | -------------------------------------------------------- |
| `Memory`      | ある Screen の `PromptParts` を CategoryPath ごとに保持  |
| `MemoryEntry` | pos/neg トークンリストを持つ単位                         |
| `KeyEntry`    | `MemoryEntry` の immutable 版. `Record` のキーとして機能 |
| `Record`      | `KeyEntry -> Memory` のマッピング. Screen ごとに保持     |

`export_memory()` / `import_memory()` / `clear_memory()` によって外部からの保存・復元・初期化が可能.

---

## 7. 記述例

以下に 2 Screen 構成の Interpreter 定義例を示す.
`screen1` の記憶を `screen2` で引き継ぐ構成, および直前 Screen からの TakeOver を例示する.

```python
class Scr(StrEnum):
    screen1 = "screen1"
    screen2 = "screen2"


class Cat(StrEnum):
    key = "key"
    cat_a = "cat_a"
    cat_b = "cat_b"
    cat_c = "cat_c"
    meta = "meta"
    sub = "sub"


class MyInterpreter(Interpreter):
    def __init__(self, yamlpath: Path):
        super().__init__(yamlpath, Cat.key)

        # cat_b が存在しない場合のみ cat_c を残す
        expr_no_b = ~Has((Cat.cat_b,))

        # 単項タプルの ',' を忘れないように!!
        self.screen_table = {
            Scr.screen1: ScreenConfig.set(
                cat_configs={
                    (Cat.key,):          (None, True),
                    (Cat.cat_a,):        (None, True),
                    (Cat.cat_b,):        (None, True),
                    (Cat.cat_c,):        (expr_no_b, True),  # cat_b がない場合のみ残す
                    (Cat.meta, Cat.sub): (None, False),
                },
                sufficiency=Has((Cat.key,)),
            ),
            Scr.screen2: ScreenConfig.set(
                cat_configs={
                    (Cat.key,):          (None, True),
                    (Cat.cat_a,):        (None, True),
                    (Cat.cat_b,):        (None, True),
                    (Cat.cat_c,):        (expr_no_b, True),
                    (Cat.meta, Cat.sub): (None, False),
                },
                sufficiency=Has((Cat.key,)) & Has((Cat.cat_a,)),
                # screen1 の記憶から cat_a / cat_b / cat_c を key をキーに引き継ぐ
                request_cats={
                    Scr.screen1: [
                        (Cat.cat_a,),
                        (Cat.cat_b,),
                        (Cat.cat_c,),
                        (Cat.meta, Cat.sub),
                    ]
                },
                # 直前 Screen の key を無条件で引き継ぐ
                takeover_cats=[
                    (Cat.key,),
                ],
            ),
        }
```

---

## 8. 制約・注意事項

### 8.1 Screen ID の一致

`screen_table` のキーは YAML の Screen 名と完全一致しなければならない.
不一致の場合は `make_prompt()` で `ValueError` が送出される.

### 8.2 CategoryPath の網羅

`cat_configs` には Interpreter が扱う全 CategoryPath を登録すること.
未登録の CategoryPath は `strip()` によって除去される.

### 8.3 登録順序の意味

`cat_configs` の登録順は `dedupe()` の配置先決定と `sort()` のソート基準を兼ねる.
論理的に優先されるべき CategoryPath を先に登録すること.

### 8.4 `keyname`

`keyname` は `MemoryEntry` を識別するためのキーカテゴリー名 (CategoryPath の末尾要素).
指定した名前に対応する CategoryPath が `cat_configs` に存在しない場合, `sync()` の Request / Offer フェーズは無効化される.

### 8.5 `common` の扱い

`common` (`path` が空タプル `()`) は `strip()` / `sift()` / `dedupe()` においてすべて保持・後処理の対象外とされる.
`sort()` では `cat_configs` に含まれないため末尾に配置される.

### 8.6 単項タプルの記法

CategoryPath を単項タプルで記述する場合, 末尾のカンマを必ず付けること.

```python
(Cat.cat_a,)   # OK
(Cat.cat_a)    # NG: str として評価される
```
