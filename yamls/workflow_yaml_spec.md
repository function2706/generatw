# Workflow YAML 仕様書

本ドキュメントは, ComfyUI へ POST するワークフローグラフ(ノード集合)を, Python コードではなく YAML で定義するための仕様を定義する.  
生成時のパラメータ注入と, 生成結果 PNG メタデータからの情報読み出し(PicInfo 逆引き)の両方を扱う.

---

## 目次

1. [全体構造](#1-全体構造)
2. [`backend`: Generator との紐づけ](#2-backend-generator-との紐づけ)
3. [nodes 定義](#3-nodes-定義)
4. [picinfo 定義](#4-picinfo-定義)
5. [ノードカタログ](#5-ノードカタログ)
6. [処理フロー](#6-処理フロー)
7. [UI (ワークフロータブ)](#7-ui-ワークフロータブ)
8. [YAML の例](#8-yaml-の例)
9. [制約・注意事項](#9-制約注意事項)

---

## 1. 全体構造

```yaml
backend: <Generator ID>   # Generator が提供する紐づけのための予約語(現状 ComfyUIGenerator のみ)
<workflow name>:          # ワークフロー名. ComfyUIGenerator は txt2img / img2img を要求する
  nodes:
    <node name>:          # 任意の識別名. 同一ワークフロー内で一意
      idx: <int>          # オプション. ComfyUI ノード番号(省略時は記述順に自動採番)
      class_type: <str>   # ComfyUI ノードの class_type
      inputs:
        <input name>: <value>
  picinfo:
    <picinfo key>: <accessor>
```

このフォーマットは Workflow > Node という二層構造によって記述される.

- Workflow: ワークフロー種別

  txt2img や img2img など, ComfyUI へ POST するグラフ全体を指定する.

- Node: ComfyUI ノード定義

  `class_type` / `inputs` (と任意の `idx`)からなる, ComfyUI API 形式のノード1つ分に対応する.

各ワークフローは `nodes`(ビルド対象のグラフ定義)と `picinfo`(生成結果からの逆引き対応表)の2セクションから構成される.

ファイルは `yamls/` 配下に配置し, UTF-8 で保存する. 既定のパスは `yamls/ComfyUI.yaml`.

---

## 2. `backend`: Generator との紐づけ

どの Generator の継承クラスのための YAML なのかを指定するための文字列を指定する.  
この文字列は Generator によって提供されるものを使用する(通常はクラス名そのものを想定).

### 2.1 記述例

```yaml
backend: ComfyUIGenerator
```

### 2.2 振る舞い

- 指定文字列と完全一致した場合, 以降の各ワークフロー定義が有効となる
- Generator が認知しない文字列が指定されている場合, シンタックスエラーとする
- ComfyUIGenerator は `txt2img` と `img2img` の両ワークフロー名を認知し要求する(Prompt Rule YAML における Screen 予約語に相当する)
- `backend` 以外のトップレベルキーはすべてワークフロー名として扱われる

---

## 3. nodes 定義

### 3.1 記述例

```yaml
sampler:
  class_type: KSampler
  inputs:
    seed: $seed
    steps: $steps
    denoise: 1.0
    model: ckpt_loader
    latent_image: empty_latent
```

- `idx`: ComfyUI ノード番号. 省略可 ([3.2](#32-idx-ノード番号と自動採番))
- `class_type`: ComfyUI ノードの class_type をそのまま指定する
- `inputs`: 当該ノードへの入力値の対応表

`idx` / `class_type` / `inputs` 以外のキーが書かれている場合はシンタックスエラーとする(タイポ検出のため).

### 3.2 `idx`: ノード番号と自動採番

`idx` は省略できる. 省略されたノードには **記述順に 1 から空き番号が割り当てられる**.

```yaml
nodes:
  ckpt_loader:      # -> idx 1
    class_type: CheckpointLoaderSimple
    ...
  empty_latent:     # -> idx 2
    class_type: EmptyLatentImage
    ...
```

- 明示された `idx` は先に確保され, 自動採番はそれを避けて割り当てられる(混在可)
- `idx` は 1 以上の整数であり, 同一ワークフロー内で重複してはならない
- 進捗表示 (`ComfyUITaskProgress.excuting_node_idx`) が参照するため, 番号を固定したい場合のみ明示する

### 3.3 `inputs` の値種別

`inputs` に列挙する各値は, 以下の3種類のいずれかとして解釈される.

| 種別                     | 記法                                                   | 解決内容                                                                              |
| ------------------------ | ------------------------------------------------------ | ------------------------------------------------------------------------------------- |
| パラメータプレースホルダ | `$` で始まる文字列(例 `$seed`)                        | ビルド時に Generator から渡される同名パラメータで置換される. 未定義パラメータはエラー   |
| ノードリンク             | カタログが `link` 型と宣言する入力に書かれたノード名, または `[<ノード名>]` / `[<ノード名>, <スロット>]` | ビルド時に `["<そのノードの idx>", <ポート>]`(ComfyUI API リンク形式)へ解決される      |
| 静的値                   | 上記以外                                               | そのまま出力される(例 `denoise: 1.0`, `crop: disabled`, `stop_at_clip_layer: -2`)     |

#### 3.3.1 パラメータプレースホルダ

```yaml
inputs:
  seed: $seed
  steps: $steps
```

ビルド時に Generator から渡される同名パラメータの値に置換される. YAML 側ではこれがどのような値になるかは判断せず, 渡された値をそのまま埋め込む.

`$` そのものを静的値として書きたい場合は `$$` とエスケープする (`$$foo` → `$foo`).

#### 3.3.2 ノードリンク

**接続元ノード名だけを書けばよい.** 接続先の入力が受け入れる型([ノードカタログ](#5-ノードカタログ)の `accepts`)から, 接続元のどの出力スロットへ繋ぐかが一意に決まるためである.

```yaml
vae_decoder:
  class_type: VAEDecode
  inputs:
    samples: sampler        # KSampler の LATENT 出力 -> ["<sampler の idx>", 0]
    vae: ckpt_loader        # CheckpointLoaderSimple の VAE 出力 -> ["<ckpt_loader の idx>", 2]
```

スロットを明示したい場合, あるいは推論できない場合はリスト形式で書く.

```yaml
inputs:
  clip: [ckpt_loader, CLIP]   # スロット名で指定
  clip: [ckpt_loader, 1]      # スロット番号で指定
  samples: [sampler]          # スロット省略 (推論に任せる)
```

**解決規則:**

1. 値がリストの場合, 先頭要素をノード名とみなす(1〜2要素以外はシンタックスエラー)
2. 値がスカラで, かつカタログが当該入力を `link` 型と宣言している場合, 値をノード名とみなす
3. 第2要素が整数ならスロット番号, 文字列ならスロット名としてカタログから解決する
4. 第2要素が省略された場合, 接続先入力の `accepts` に該当する接続元の出力スロットを探す
   - 該当が 0 個 → 型不一致としてシンタックスエラー
   - 該当が 2 個以上 → 一意に定まらないためシンタックスエラー(スロット名で明示すること)
5. リンク先ノードが同一ワークフロー内に存在しない場合はシンタックスエラー

カタログに未登録の `class_type` では規則 2 と 4 が働かないため, リンクは `[<ノード名>, <スロット番号>]` 形式で明示する必要がある.

#### 3.3.3 静的値

```yaml
inputs:
  denoise: 1.0
  crop: disabled
  stop_at_clip_layer: -2
  ckpt_name: Illustrious\waiIllustriousSDXL_v170.safetensors
```

パラメータプレースホルダにもノードリンクにも該当しない値は, そのまま静的値として出力される.

---

## 4. picinfo 定義

生成結果 PNG のメタデータ(ComfyUI が埋め込む workflow dict)から, PicInfo の各フィールドを読み出すための対応表を定義する.

### 4.1 記述例

```yaml
picinfo:
  steps: [sampler, steps]
  clip_skip:
    from: [clip_layer_setter, stop_at_clip_layer]
    negate: true
```

### 4.2 値の形式

値は以下の2形式のいずれかで記述する.

- `[<node name>, <input name>]`

  そのノードの `inputs` から値を読み出す.

- `{from: [<node name>, <input name>], negate: true}`

  読み出した数値の符号を反転する. たとえば `stop_at_clip_layer: -2` を `clip_skip: 2` として読み出す場合に用いる.

### 4.3 型変換

読み出した値は, PicInfo dataclass の当該フィールドの型(int / float / str)に自動変換される.

### 4.4 検証

以下はロード時にシンタックスエラーとして検出される.

- PicInfo に存在しないフィールド名
- 存在しないノード名 / 入力名
- ノードリンクを指す入力の参照(逆引きできる値ではないため)

応答側のノードとの突合は `idx` を介して行う. 対応する `idx` が応答に無い場合, 当該フィールドは PicInfo の既定値のままとなる.

---

## 5. ノードカタログ

`yamls/node_catalog.yaml` に, ノードクラスごとの入出力定義を持つ. リンクのスロット解決([3.3.2](#332-ノードリンク))とロード時の入力検証に用いる.

```yaml
version: 1
nodes:
  CLIPTextEncode:
    outputs: [CONDITIONING]     # 出力スロット名をインデックス順に並べたもの
    inputs:
      text: { type: str, required: true }
      clip: { type: link, accepts: [CLIP], required: true }
  PreviewImage:
    outputs: []
    is_output: true             # 終端ノード
    inputs:
      images: { type: link, accepts: [IMAGE], required: true }
```

| キー                     | 説明                                              |
| ------------------------ | ------------------------------------------------- |
| `outputs`                | 出力スロット名を **インデックス順** に並べたもの   |
| `is_output`              | 終端ノードであれば `true`                          |
| `inputs.<名>.type`       | `str`/`int`/`float`/`bool`/`link`                 |
| `inputs.<名>.accepts`    | `type: link` のとき, 受け入れる出力スロット型      |
| `inputs.<名>.required`   | 未指定の場合ロード時エラーとするか                 |
| `inputs.<名>.choices`    | 静的値の許容値リスト                               |

### 5.1 カタログによる検証

カタログに登録された `class_type` については, ロード時に以下を検証する.

- 存在しない入力名(タイポ検出)
- 必須入力の欠落
- リンク入力へのリンク以外の指定, および非リンク入力へのリンク指定
- リンクの型不一致
- 静的値の `choices` 逸脱

### 5.2 カタログに無いノード

カタログに無い `class_type` も使用できる. ただし以下の制限がかかり, 警告が記録される.

- リンクは `[<ノード名>, <スロット番号>]` 形式で明示する必要がある
- 入力の検証は行われない(妥当性は ComfyUI サーバ側で判定される)

カタログファイル自体が存在しない場合も同様に動作する(全ノードが未登録扱いとなる).

---

## 6. 処理フロー

```
[ロード時] (起動時 / WF YAML 選択時 / 再読み込み時)
  1. backend 適合チェック
  2. ワークフロー走査: ワークフロー名ごとに nodes を定義順に走査
  3. idx の確定 (明示分の確保 -> 自動採番)
  4. 入力の分類 (プレースホルダ / リンク / 静的値) とリンクのスロット解決
  5. カタログ照合, 循環参照検出, picinfo 検証
  6. 孤立ノード等を警告として記録

[実行時] (1 タスクごと)
  7. Generator がパラメータを組み立てる
  8. build(): グラフを dict 化して POST /prompt
  9. PicInfo 逆引き: picinfo に従い, 生成結果 PNG のメタデータから値を読み出す
```

ロード時エラーは **シンタックスエラー** として `WorkFlowSyntaxError` で送出される. ビルド時に要求されたパラメータが渡されていない場合は `KeyError` となる.

### 6.1 Generator 側の責務

以下は YAML の責務外であり, Generator が実行時に行う.

- `$seed` に渡る値が `-1` のときの乱数化(YAML は宣言的なままであり, 乱数化のロジックを持たない)
- img2img の `$path` の絶対パス解決

### 6.2 Generator が渡すパラメータ

`ComfyUIGenerator.make_params()` が組み立てる. YAML はこの範囲の `$xxx` を参照できる.

| パラメータ       | 供給元                          | txt2img | img2img |
| ---------------- | ------------------------------- | :-----: | :-----: |
| `$pos_prompt`    | `task.prompt`                   | ○       | ○       |
| `$neg_prompt`    | `task.negative_prompt`          | ○       | ○       |
| `$seed`          | `task.seed` (-1 なら乱数化)     | ○       | ○       |
| `$steps`         | `task.steps`                    | ○       | ○       |
| `$batch_size`    | `task.batch_size`               | ○       | ○       |
| `$sampler_name`  | `task.sampler_name`             | ○       | ○       |
| `$scheduler`     | `task.scheduler`                | ○       | ○       |
| `$cfg_scale`     | `task.cfg_scale`                | ○       | ○       |
| `$width`         | `task.width`                    | ○       | ○       |
| `$height`        | `task.height`                   | ○       | ○       |
| `$path`          | `task.path` (絶対パス化)        | -       | ○       |
| `$upscaler`      | `task.upscaler_name`            | -       | ○       |
| `$denoise`       | `task.denoising_strength`       | -       | ○       |

パラメータを追加したい場合は `make_params()` に足す. YAML 側だけでは増やせない.

### 6.3 使用する YAML の指定

`config.json` (= `GUIConfigs`) の `wf_yamlpath` で指定する. 未指定時は `yamls/ComfyUI.yaml`.

読み込みに失敗した場合はエラーを表示し, 現在の定義を維持する(起動時に失敗した場合は既定パスで再試行する).

---

## 7. UI (ワークフロータブ)

設定ウィンドウの「ワークフロー」タブ (`src/displayer/workflow_tab.py`) から操作する.

- **選択**: `yamls/` を走査し, `backend: ComfyUIGenerator` を持つ YAML を一覧表示する. `参照` で任意のパスも指定できる. 選択は `OnSelectWfYaml` として Master へ通知され, Generator の定義が差し替わる
- **検証**: 選択と同時にロードを試み, 成功時は緑でセクション名とノード数を, 失敗時は赤でシンタックスエラーの内容を表示する. 孤立ノードやカタログ未登録は橙の警告として表示する
- **ノード一覧**: セクションごとのサブタブに `idx` / ノード名 / `class_type` / 解決済 `inputs` を表示する. リンクは `<接続元:スロット>`, プレースホルダは `$名前` として表示されるため, **スロット推論の結果をここで確認できる**
- **パラメータ**: 当該セクションが要求する `$xxx` を列挙し, Generator が渡さないものがあれば併記する
- **プレビュー**: 現在の GUI 設定値からダミータスクを作り, `make_params()` を通して実際に POST される JSON を表示する
- **再読み込み**: 再走査 + 再検証を行い, `OnReloadWfYaml` を Master へ通知する

選択結果は `GUIConfigs` 経由で保持され, 終了時に `config.json` へ保存される.

---

## 8. YAML の例

`ComfyUI.yaml` の `txt2img` セクションを例として示す.

```yaml
backend: ComfyUIGenerator
txt2img:
  nodes:
    ckpt_loader:
      class_type: CheckpointLoaderSimple
      inputs:
        ckpt_name: Illustrious\waiIllustriousSDXL_v170.safetensors
    empty_latent:
      class_type: EmptyLatentImage
      inputs:
        width: $width
        height: $height
        batch_size: $batch_size
    clip_layer_setter:
      class_type: CLIPSetLastLayer
      inputs:
        stop_at_clip_layer: -2
        clip: ckpt_loader
    positive_clip:
      class_type: CLIPTextEncode
      inputs:
        text: $pos_prompt
        clip: ckpt_loader
    negative_clip:
      class_type: CLIPTextEncode
      inputs:
        text: $neg_prompt
        clip: ckpt_loader
    sampler:
      class_type: KSampler
      inputs:
        seed: $seed
        steps: $steps
        cfg: $cfg_scale
        denoise: 1.0
        sampler_name: $sampler_name
        scheduler: $scheduler
        model: ckpt_loader
        latent_image: empty_latent
        positive: positive_clip
        negative: negative_clip
    vae_decoder:
      class_type: VAEDecode
      inputs:
        samples: sampler
        vae: ckpt_loader
    previewer:
      class_type: PreviewImage
      inputs:
        images: vae_decoder
  picinfo:
    positive_prompt: [positive_clip, text]
    negative_prompt: [negative_clip, text]
    steps: [sampler, steps]
    sampler: [sampler, sampler_name]
    scheduler: [sampler, scheduler]
    cfg_scale: [sampler, cfg]
    seed: [sampler, seed]
    width: [empty_latent, width]
    height: [empty_latent, height]
    model_name: [ckpt_loader, ckpt_name]
    clip_skip:
      from: [clip_layer_setter, stop_at_clip_layer]
      negate: true
```

### 8.1 読み解き

- `idx` はすべて省略されているため, 記述順に `ckpt_loader` = 1 から `previewer` = 8 が割り当てられる
- `ckpt_loader.inputs.ckpt_name` はプレースホルダにもリンクにも該当しないため静的値として扱われる
- `empty_latent.inputs.width` / `height` / `batch_size` はいずれもパラメータプレースホルダであり, ビルド時に Generator から渡される値に置換される
- `positive_clip.inputs.clip: ckpt_loader` は, `CLIPTextEncode.clip` が CLIP を受け入れ, `CheckpointLoaderSimple` の CLIP 出力が 1 番であることから `["1", 1]` に解決される
- 同様に `sampler.inputs.model` は MODEL 出力の `["1", 0]`, `vae_decoder.inputs.vae` は VAE 出力の `["1", 2]` に解決される
- `sampler`(KSampler)の `inputs` はリンク(`model`, `latent_image`, `positive`, `negative`), プレースホルダ(`seed`, `steps`, `cfg`, `sampler_name`, `scheduler`), 静的値(`denoise: 1.0`)が混在する典型例である
- `picinfo.clip_skip` は `clip_layer_setter.inputs.stop_at_clip_layer`(`-2`)を符号反転して読み出し, `clip_skip: 2` を得る

`img2img` セクションも同様の構造であり, `image_loader`(`UnlimitLoadImage`)の `path`(パラメータプレースホルダ `$path`)や `latent_upscaler`(`LatentUpscale`)を経由する点, および `picinfo.ancestor` で入力元画像パスを逆引きする点が txt2img との差分となる.

### 8.2 同梱サンプルの既知の挙動

同梱の `ComfyUI.yaml` は, 従来ハードコードされていた `Txt2ImgWorkFlow` / `Img2ImgWorkFlow` と **同一の dict を生成する**. 以下の挙動もそのまま再現している.

- **`CLIPSetLastLayer` が孤立ノードになっている**: `CLIPTextEncode.clip` が `clip_layer_setter` ではなく `ckpt_loader` へ直結しているため, `clip_skip` は実際には生成に影響していない. `clip: clip_layer_setter` に書き換えるだけで有効化できる(ロード時に孤立ノードの警告が出るのはこのため)
- **img2img が `$batch_size` を使っていない**: 従来の `Img2ImgWorkFlow` も `batch_size` を引数に取りながらどのノードにも渡していなかった

---

## 9. 制約・注意事項

### 9.1 ノード定義

- `idx` は同一ワークフロー内で重複してはならない
- ノード名は同一ワークフロー内で重複してはならない(YAML 仕様上, 重複した場合は後勝ちで上書きされる点に注意)
- 新しい `class_type` の追加は YAML 編集のみで可能である. スロット名で繋ぎたい場合や入力検証を効かせたい場合はカタログにも追記する
- 循環参照はシンタックスエラーとする
- 孤立ノード(どこからも参照されず, かつ終端ノードでもないノード)は **警告** に留める(現行 WF の `CLIPSetLastLayer` が該当するため)

### 9.2 inputs 記法

- 静的値の先頭に `$` を用いたい場合は `$$` とエスケープする
- リンクをスカラで書けるのはカタログが `link` 型と宣言している入力のみである. それ以外はリスト形式を用いること
- スロット省略時の推論が一意に定まらない場合はシンタックスエラーとなる. スロット名で明示すること

### 9.3 パラメータ

- `$xxx` の名前は [6.2](#62-generator-が渡すパラメータ) の範囲に限られる. 未知の名前はビルド時に `KeyError` となる
- パラメータの型変換や既定値の適用は行わない. 渡された値をそのまま埋め込む

### 9.4 命名上の注意

- 大文字 / 小文字は **区別される**(ノード名, `class_type`, スロット名, パラメータ名すべて)

### 9.5 予約語一覧

| 予約語       | 禁止                       |
| ------------ | -------------------------- |
| `backend`    | ワークフロー名として       |
| `nodes`      | ワークフロー直下の他用途で |
| `picinfo`    | ワークフロー直下の他用途で |
| `idx`        | ノードの入力名として       |
| `class_type` | ノードの入力名として       |
| `inputs`     | ノードの入力名として       |
