# キャラクター / アクション YAML 仕様書

本アプリは「単一キャラクターとの交流」を通じて, 内部パラメータと状況に応じた
画像生成プロンプトを組み立てる. その素材は 2 種類の YAML で定義する.

- **キャラクター YAML** (`yamls/characters/<id>.yaml`): 1 ファイル = 1 キャラ
- **アクション YAML** (`yamls/actions.yaml`): 全キャラ共通のアクション定義

セリフ・アクション・パラメータはいずれも YAML の追記だけで拡張できる.

---

## 1. プロンプト文字列記法

positive / negative に書く文字列は, カンマ区切りのトークン列.
以下の記法が使える (詳細な確率選択の重み計算は `common/atoms.py` の `TokenExpr`).

- 重み: `(token:1.3)` — 省略時は `1.0`
- スペース可: `blue hair`
- 確率選択: `<a|b|c>` から 1 つを決定論的に抽選 (`<2::a|b>` で重み付け)
- 直積・インライン: `a,<b|c>` / `x<y|z>` など

プロンプト指定は次のいずれの形でもよい.

```yaml
positive: "smile, blush"        # positive のみの短縮形 (文字列)
# または
scene:
  positive: "hug, close-up"
  negative: "multiple boys"
```

---

## 2. キャラクター YAML

```yaml
character: sample            # キャラ ID (必須. 状態ファイル名/記録キー)
display_name: アオイ         # UI 表示名 (省略時は character)

base:                       # 基本容姿 (常時付与)
  positive: "1girl, solo, long blue hair, blue eyes"

common:                     # 末尾に常時付与する共通プロンプト (省略可)
  positive: "masterpiece, best quality, looking at viewer"
  negative: "worst quality, low quality"

wardrobe:                   # 着せ替え候補 (省略可)
  casual:  { label: 私服, positive: "casual clothes" }
  uniform: { label: 制服, positive: "school uniform, blazer" }
init_outfit: casual         # 初期衣装キー (省略時は wardrobe の先頭)

parameters:                 # 内部パラメータ (挿入順で表示)
  affection:
    label: 好感度            # 表示名 (省略時は ID)
    type: scalar            # scalar (数値) / enum (離散)
    range: [0, 100]         # scalar の下限・上限
    init: 20                # 初期値
    prompt:                 # 値 -> プロンプトの写像
      intervals:
        - { in: [0, 30],   positive: "expressionless" }
        - { in: [31, 70],  positive: "soft smile" }
        - { in: [71, 100], positive: "(loving smile:1.2), blush" }
  mood:
    label: 気分
    type: enum
    values: [normal, happy, shy]   # 取りうる値 (先頭が既定)
    init: normal
    prompt:
      maps:
        happy: "happy, smile"
        shy:   { positive: "shy, blush", negative: "angry" }
```

### 2.1 パラメータの写像 (`prompt`)

- `intervals`: 数値の**閉区間** `[lo, hi]` にヒットしたら付与 (scalar 向け, 複数ヒット可)
- `maps`: 値 (enum 値や数値の文字列) をキーに付与

`in`/`positive`/`negative` の値は「プロンプト文字列記法」に従う (`<>` や重みも可).

### 2.2 プロンプト構築順

生成時, 次の順でトークンが連結される.

```
base -> 現在の衣装 -> 各パラメータ(定義順) -> アクション scene -> common
```

各文字列は `TokenExpr` を通り, `<>` の抽選が確定する.
抽選シードはアクションごとに変わるため, ボタンを押すたびに `<>` の中身が変化しうる.

---

## 3. アクション YAML

```yaml
actions:
  - id: greet               # アクション ID (必須)
    label: 挨拶             # ボタン表示名
    kind: normal            # normal / wardrobe (省略時 normal)
    scene:                  # 実行時のみ付与するプロンプト (省略可)
      positive: "waving, upper body"
    effects:                # パラメータ変化 (省略可)
      affection: +2         # scalar: +n / -n / =n (絶対代入)
      mood: happy           # enum: 値名を設定
    precondition:           # 前提条件 (省略可). 未達なら locked
      affection: { min: 15 }   # scalar: min / max,  enum: is / in
    dialogue:               # 通常セリフ候補 (1 つ決定論的に選択)
      - "やっほー！"
      - "こんにちは。"
    dialogue_by:            # パラメータ条件別セリフ (成立時に優先, 省略可)
      affection:
        - { in: [80, 100], lines: ["会いたかった…！"] }   # scalar
      mood:
        - { is: sulky, lines: ["ふん。"] }                # enum
    dialogue_locked:        # precondition 未達時のセリフ (省略可)
      - "い、いきなりは困るってば！"
```

### 3.1 `kind: wardrobe` (着せ替え)

`kind: wardrobe` のアクションは, UI の「衣装」コンボで選ばれた衣装キーへ切り替える.
`effects`/`scene`/`dialogue` も通常どおり併用できる.

### 3.2 locked (拒否) の挙動

`precondition` を満たさない場合:

- `effects` と `scene` は適用されない (状態は変化しない)
- セリフは `dialogue_locked` から選ばれる
- 画像は「素立ち + 現在パラメータ」で再生成される

---

## 4. 内部状態と永続化

各パラメータの現在値と現在の衣装は `CharacterState` として保持され,
`memories/<character>.state.json` に保存される.

- 「状態: 保存 / 復元 / リセット」ボタン, および設定タブのトグルで制御
- YAML 側でパラメータや衣装を増減しても, 復元時に定義と自動整合される

---

## 5. 会話方式の拡張 (ハイブリッド設計)

セリフ供給は `character/dialogue.py` の `DialogueProvider` を境界に抽象化している.
既定は YAML 定型セリフを選ぶ `YamlDialogueProvider`.
将来的に LLM 応答へ差し替える場合は, `DialogueContext` (キャラ・状態・アクション・
locked・シード) を素材に `line()` を実装した Provider を `CharacterEngine` へ注入すればよい.
