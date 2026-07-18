# Workflow YAML 仕様書

本ドキュメントは, ComfyUI へ POST するワークフローグラフ(ノード集合)を, Python コードではなく YAML で定義するための仕様を定義する.  
生成時のパラメータ注入と, 生成結果 PNG メタデータからの情報読み出し(PicInfo 逆引き)の両方を扱う.

---

## 目次

1. [全体構造](#1-全体構造)
2. [`backend`: Generator との紐づけ](#2-backend-generator-との紐づけ)
3. [nodes 定義](#3-nodes-定義)
4. [picinfo 定義](#4-picinfo-定義)
5. [処理フロー](#5-処理フロー)
6. [YAML の例](#6-yaml-の例)
7. [制約・注意事項](#7-制約注意事項)

---

## 1. 全体構造

```yaml
backend: <Generator ID>   # Generator が提供する紐づけのための予約語(現状 ComfyUIGenerator のみ)
<workflow name>:          # ワークフロー名. ComfyUIGenerator は txt2img / img2img を要求する
  nodes:
    <node name>:          # 任意の識別名. 同一ワークフロー内で一意
      idx: <int>          # ComfyUI ノード番号. 同一ワークフロー内で一意
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

  `idx` / `class_type` / `inputs` からなる, ComfyUI API 形式のノード1つ分に対応する.

各ワークフローは `nodes`(ビルド対象のグラフ定義)と `picinfo`(生成結果からの逆引き対応表)の2セクションから構成される.

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

---

## 3. nodes 定義

### 3.1 記述例

```yaml
sampler:
  idx: 6
  class_type: KSampler
  inputs:
    seed: $seed
    steps: $steps
    denoise: 1.0
    model: [ckpt_loader, 0]
    latent_image: [empty_latent, 0]
```

- `idx`: ComfyUI ノード番号. 同一ワークフロー内で一意でなければならない
- `class_type`: ComfyUI ノードの class_type をそのまま指定する
- `inputs`: 当該ノードへの入力値の対応表

### 3.2 `inputs` の値種別

`inputs` に列挙する各値は, 以下の3種類のいずれかとして解釈される.

| 種別                     | 記法                                          | 解決内容                                                                                          |
| ------------------------ | --------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| パラメータプレースホルダ | `$` で始まる文字列(例 `$seed`)               | ビルド時に Generator から渡される同名パラメータで置換される. 未定義パラメータはエラーとする         |
| ノードリンク             | 2要素リスト, 先頭が同一ワークフロー内のノード名(例 `[ckpt_loader, 1]`) | ビルド時に `["<そのノードの idx>", <port>]`(ComfyUI API リンク形式, idx は文字列化)へ解決される. 第2要素は接続元ノードの出力ポート番号を表す |
| 静的値                   | 上記以外                                      | そのまま出力される(例 `denoise: 1.0`, `crop: disabled`, `stop_at_clip_layer: -2`, モデル名など)   |

#### 3.2.1 パラメータプレースホルダ

```yaml
inputs:
  seed: $seed
  steps: $steps
```

ビルド時に Generator から渡される同名パラメータの値に置換される. YAML 側ではこれがどのような値になるかは判断せず, 渡された値をそのまま埋め込む.

#### 3.2.2 ノードリンク

```yaml
inputs:
  model: [ckpt_loader, 0]
```

先頭要素 `ckpt_loader` が同一ワークフロー内に定義されたノード名であるとき, これはノードリンクとして解決される. 第2要素 `0` は接続元ノード(`ckpt_loader`)の出力ポート番号である.

**リンク判定規則の注意**: 2要素リストであっても, 先頭要素がノード名として存在しない場合は静的値として扱う.

#### 3.2.3 静的値

```yaml
inputs:
  denoise: 1.0
  crop: disabled
  stop_at_clip_layer: -2
  ckpt_name: Illustrious\waiNSFWIllustrious_v150.safetensors
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

---

## 5. 処理フロー

1. **backend 適合チェック**: Generator との紐づけ
2. **ワークフロー走査**: ワークフロー名ごとに `nodes` を定義順に走査
3. **値解決**: パラメータプレースホルダの解決, ノードリンクの解決
4. **グラフ構築**: ComfyUI へ POST する dict を構築
5. **PicInfo 逆引き**(生成後): `picinfo` に従い, 生成結果 PNG のメタデータから値を読み出す

### 5.1 Generator 側の責務

以下は YAML の責務外であり, Generator が実行時に行う.

- `$seed` に渡る値が `-1` のときの乱数化(YAML は宣言的なままであり, 乱数化のロジックを持たない)
- img2img の `$path` の絶対パス解決

---

## 6. YAML の例

`ComfyUI.yaml` の `txt2img` セクションを例として示す.

```yaml
backend: ComfyUIGenerator
txt2img:
  nodes:
    ckpt_loader:
      idx: 1
      class_type: CheckpointLoaderSimple
      inputs:
        ckpt_name: Illustrious\waiNSFWIllustrious_v150.safetensors
    empty_latent:
      idx: 2
      class_type: EmptyLatentImage
      inputs:
        width: $width
        height: $height
        batch_size: $batch_size
    clip_layer_setter:
      idx: 3
      class_type: CLIPSetLastLayer
      inputs:
        stop_at_clip_layer: -2
        clip: [ckpt_loader, 1]
    positive_clip:
      idx: 4
      class_type: CLIPTextEncode
      inputs:
        text: $pos_prompt
        clip: [ckpt_loader, 1]
    negative_clip:
      idx: 5
      class_type: CLIPTextEncode
      inputs:
        text: $neg_prompt
        clip: [ckpt_loader, 1]
    sampler:
      idx: 6
      class_type: KSampler
      inputs:
        seed: $seed
        steps: $steps
        cfg: $cfg_scale
        denoise: 1.0
        sampler_name: $sampler_name
        scheduler: $scheduler
        model: [ckpt_loader, 0]
        latent_image: [empty_latent, 0]
        positive: [positive_clip, 0]
        negative: [negative_clip, 0]
    vae_decoder:
      idx: 7
      class_type: VAEDecode
      inputs:
        samples: [sampler, 0]
        vae: [ckpt_loader, 2]
    previewer:
      idx: 8
      class_type: PreviewImage
      inputs:
        images: [vae_decoder, 0]
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

### 6.1 読み解き

- `ckpt_loader.inputs.ckpt_name` はプレースホルダにもリンクにも該当しないため静的値として扱われる
- `empty_latent.inputs.width` / `height` / `batch_size` はいずれもパラメータプレースホルダであり, ビルド時に Generator から渡される値に置換される
- `clip_layer_setter.inputs.clip: [ckpt_loader, 1]` はノードリンクであり, `ckpt_loader`(idx 1)の出力ポート 1 番(CLIP 出力)への接続として `["1", 1]` に解決される
- `sampler`(KSampler)の `inputs` はリンク(`model`, `latent_image`, `positive`, `negative`), プレースホルダ(`seed`, `steps`, `cfg`, `sampler_name`, `scheduler`), 静的値(`denoise: 1.0`)が混在する典型例である
- `picinfo.clip_skip` は `clip_layer_setter.inputs.stop_at_clip_layer`(`-2`)を符号反転して読み出し, `clip_skip: 2` を得る

`img2img` セクションも同様の構造であり, `image_loader`(`UnlimitLoadImage`)の `path`(パラメータプレースホルダ `$path`)や `latent_upscaler`(`LatentUpscale`)を経由する点, および `picinfo.ancestor` で入力元画像パスを逆引きする点が txt2img との差分となる.

---

## 7. 制約・注意事項

### 7.1 ノード定義

- `idx` は同一ワークフロー内で重複してはならない
- ノード名は同一ワークフロー内で重複してはならない(YAML 仕様上, 重複した場合は後勝ちで上書きされる点に注意)
- 新しい `class_type` の追加は YAML 編集のみで可能であり, Python コードの変更は不要である

### 7.2 inputs 記法

- 静的値の先頭に `$` リテラルを用いたい場合, 現状は非対応(パラメータプレースホルダと区別できないため)
- 2要素リストであっても, 先頭要素が同一ワークフロー内のノード名として存在しなければ静的値として扱われる

### 7.3 検証

- 本 YAML 自体は構造的な検証(`idx` / ノード名の重複チェック等)のみを行い, ノード間の入出力の整合性(ポート番号や型の妥当性)についての最終的な検証は ComfyUI サーバ側で行われる
