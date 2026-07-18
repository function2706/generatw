"""
疑似 Emuera (socket push 送信側) デバッグツール

改造版 Emuera が本アプリの SocketInputSource へ画面テキストを push する挙動を模倣する.
本アプリを input_source="socket" で起動した状態で本スクリプトを実行すると,
サンプル画面テキストをフレーミングして送り込み, socket 経路を E2E で検証できる.

メッセージフレーム: 4byte 長さ (big-endian, 符号なし) + UTF-8 本文
(SocketInputSource と一致させること)

使い方:
    python src/debug/pseudo_emuera.py                       # 既定サンプルを順送り
    python src/debug/pseudo_emuera.py --file path/to.txt    # 任意ファイルを送る
    python src/debug/pseudo_emuera.py --whole               # 分割せず全文を 1 フレームで送る
    python src/debug/pseudo_emuera.py --interval 2.0        # フレーム間隔 (秒)
"""

from __future__ import annotations

import argparse
import re
import socket
import struct
import time
from pathlib import Path

LEN_PREFIX = struct.Struct(">I")

# clip_sample_R.txt のセクション番号 ("1.", "2." ...) を画面区切りとみなす
SECTION_MARKER = re.compile(r"^\s*\d+\.\s*$", re.MULTILINE)

DEFAULT_SAMPLE = Path("src/debug/clip_sample_R.txt")


def split_screens(text: str) -> list[str]:
    """
    サンプルテキストを画面 (セクション) 単位に分割する\n
    番号マーカー行で区切り, 空セクションは除外する

    Args:
        text (str): サンプル全文

    Returns:
        list[str]: 画面テキストのリスト
    """
    parts = SECTION_MARKER.split(text)
    screens = [p.strip("\n") for p in parts if p.strip()]
    return screens if screens else [text]


def send_frame(sock: socket.socket, body: str) -> None:
    """
    1 フレーム (長さ prefix + 本文) を送信する

    Args:
        sock (socket.socket): 接続済みソケット
        body (str): 本文
    """
    payload = body.encode("utf-8")
    sock.sendall(LEN_PREFIX.pack(len(payload)) + payload)


def main() -> None:
    ap = argparse.ArgumentParser(description="Pseudo Emuera socket sender")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=52340)
    ap.add_argument("--file", type=Path, default=DEFAULT_SAMPLE)
    ap.add_argument("--interval", type=float, default=1.5, help="フレーム間隔 (秒)")
    ap.add_argument("--whole", action="store_true", help="分割せず全文を 1 フレームで送る")
    ap.add_argument("--loop", action="store_true", help="送り終えたら繰り返す")
    args = ap.parse_args()

    text = args.file.read_text(encoding="utf-8")
    screens = [text] if args.whole else split_screens(text)

    with socket.create_connection((args.host, args.port)) as sock:
        print(f"connected to {args.host}:{args.port}, {len(screens)} screen(s)")
        while True:
            for i, screen in enumerate(screens):
                send_frame(sock, screen)
                head = screen.splitlines()[0] if screen.splitlines() else ""
                print(f"  sent screen {i + 1}/{len(screens)}: {head[:60]}")
                time.sleep(args.interval)
            if not args.loop:
                break
    print("done.")


if __name__ == "__main__":
    main()
