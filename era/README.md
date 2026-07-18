# generatw ⇔ Emuera socket 連携 (Reverse / TW 共通)

クリップボード監視をやめ、改造 Emuera が画面確定時に画面テキストを TCP で
本アプリへ直接 push する方式。両者は「4byte 長さ(big-endian) + UTF-8 本文」で通信する。
Emuera が接続する側(client)、本アプリが待ち受ける側(server)。

- 対象実行体: `LazyLoadingV26.exe`（Reverse / TW 共通）
- 改造元ソース: https://gitlab.com/EvilMask/emuera.em （.NET 10, master）
- 送るテキストは従来クリップボードに来ていたものと同一なので、Python 側 Interpreter は無改造で流用。

---

## 1. アプリ側 (このリポジトリ, 実装済み)

- `src/parser/input_source.py`: `InputSource` 抽象 + `ClipboardInputSource`(従来) + `SocketInputSource`(新規)
- `src/parser/parser.py`: 入力ソースからのイベント駆動受信に変更
- `config.json`:
  ```json
  "input_source": "socket",   // socket 連携を使う (既定は "clipboard")
  "socket_port": 52340,
  ```
- デバッグ送信ツール: `python src/debug/pseudo_emuera.py`（改造 Emuera 無しで socket 経路を試せる）

---

## 2. エンジン側改造 (パッチ: `era/generatw-ipc.patch`)

> このディレクトリ `era/` に、改造した8ファイル(`era/emuera-em/`, リポジトリ相対パス保持)、
> パッチ(`era/generatw-ipc.patch`)、手順書(この `README.md`) を git 管理下で保存している。
> ビルド用の完全クローン(`stash/emuera.em`, 約147MB)と成果物 exe(`era/dist/Emuera.exe`, 119MB)は
> サイズのため git 管理外(gitignore)。exe はパッチから随時再生成できる。

追加 config (emuera が client として送信):
- `GTWSocketEmit`（bool, 既定 false）… 画面テキストを socket 送信する
- `GTWSocketHost`（string, 既定 127.0.0.1）
- `GTWSocketPort`（int, 既定 52340）

主な変更:
- 新規 `Emuera/Runtime/Utils/Generatw/GeneratwEmitter.cs`（TCP client, バックグラウンド送信, 例外は全握り潰し, 再接続あり）
- `ClipboardProcessor`(Clipboard.cs) の行バッファ/送出ロジックに相乗り。
  `CBBufferingActive = CBUseClipboard || GTWSocketEmit` を導入し、
  画面確定時(InputWait/AnyKeyWait)に構築される `newText` を、変化時のみ socket へ送出。
- 送出タイミング/内容はクリップボード機能とバイト同一。

### ビルド (WSL / Linux で可能。要 .NET 10 SDK)

```bash
# .NET 10 SDK (rootless)
curl -sSL https://dot.net/v1/dotnet-install.sh -o /tmp/dotnet-install.sh && chmod +x /tmp/dotnet-install.sh
/tmp/dotnet-install.sh --channel 10.0 --install-dir "$HOME/.dotnet"
export PATH="$HOME/.dotnet:$PATH"; export DOTNET_ROOT="$HOME/.dotnet"

cd stash/emuera.em                        # ビルド用クローン (未取得なら下記 clone)
# git clone https://gitlab.com/EvilMask/emuera.em.git stash/emuera.em
git apply ../../era/generatw-ipc.patch    # このブランチには適用済み

# 重要:
#  -c Release-NAudio  … WMPLib(COM参照)を避ける構成(Linuxビルド必須)
#  -p:EnableWindowsTargeting=true … Windows ターゲットを Linux でビルド
dotnet publish Emuera/Emuera.csproj -c Release-NAudio -r win-x64 -p:Platform=x64 \
  --self-contained true -p:EnableWindowsTargeting=true -o ../../era/dist
```

生成された `era/dist/Emuera.exe`(self-contained, Windows 実行用) を、
ゲームフォルダの `LazyLoadingV26.exe` と差し替え(または併置)して起動する。

> 注: master は `EMv18+EEv56`。出荷版 `LazyLoadingV26`(EEv47) より新しいエンジンになる。

---

## 3. emuera.config への追記 (ゲームフォルダ)

**移行手順(安全策)**: まず現行のクリップボード設定は**変えずに**、送信だけ足す。

```
画面テキストをsocketで送信する(generatw連携):YES
generatw送信先ホスト:127.0.0.1
generatw送信先ポート:52340
```

- `INPUTをトリガーにする:YES`（既定 YES。状態画面の確定時に送出）
- メッセージ画面(WAIT)でも追従したい場合: `WAITをトリガーにする:YES`
- 低遅延にしたい場合: `クリップボードの更新間隔(ミリ秒)` を下げる（既定 800）
- 動作確認後、クリップボード汚染を止めたければ
  `表示したテキストをクリップボードにコピーする:NO` にしてよい
  （`GTWSocketEmit:YES` があれば送信は継続する）

---

## 4. 動作確認

1. アプリを `input_source:"socket"` で起動（`SocketInputSource listening on 127.0.0.1:52340` が出る）
2. 改造 Emuera でゲームを進める → 画面が変わるたびアプリが生成ラインを起動

改造 Emuera 抜きでの経路単体テスト:
```bash
# アプリ(socketモード)起動後、別端末で
python src/debug/pseudo_emuera.py --port 52340
```

## 検証済み事項 (このリポジトリでの作業)

- socket ラウンドトリップ（Python 受信）: サンプル7画面すべて受信 OK
- 実 `GeneratwEmitter`(C#) → 実 `SocketInputSource`(Python) のワイヤ契約:
  マルチバイト日本語・絵文字含めバイト同一で PASS
- `ReverseInterpreter` が socket 配送テキストから `screen_id=main`・トークン生成・充足判定 True
- 改造エンジンの WSL ビルド: 0 Error
