"""
画面テキストの入力ソース抽象

Parser はクリップボード監視に固定されず, 本モジュールの InputSource を介して
画面テキストを取得する. これにより「Emuera からの push (socket)」と
「クリップボード監視 (従来方式)」を差し替え可能にする.

read() は 1 件の画面テキスト, または待機タイムアウト時に None を返す.
None を挟むことで Parser 側は定期的にシャットダウン判定を行える.
"""

from __future__ import annotations

import socket
import struct
import time
from abc import ABC, abstractmethod


class InputSource(ABC):
    """
    画面テキスト入力ソースの抽象基底
    """

    @abstractmethod
    def open(self) -> None:
        """
        ソースを開く (listen 開始, 初期化など)
        """

    @abstractmethod
    def read(self) -> str | None:
        """
        次の画面テキストを取得する\n
        取得できない (タイムアウト) 場合は None を返す

        Returns:
            str | None: 画面テキスト, なければ None
        """

    @abstractmethod
    def close(self) -> None:
        """
        ソースを閉じる
        """


class ClipboardInputSource(InputSource):
    """
    従来方式のクリップボード監視ソース\n
    Emuera の「表示テキストをクリップボードにコピー」機能を前提に,
    一定間隔でクリップボードを読み取る (取得値の重複排除は Parser 側が行う)
    """

    def __init__(self, poll_interval_sec: float = 0.01, retry: int = 5, retry_delay: float = 0.1):
        self._poll_interval = poll_interval_sec
        self._retry = retry
        self._retry_delay = retry_delay
        self._pyperclip = None

    def open(self) -> None:
        # pyperclip はクリップボードモード時のみ必要なので遅延 import
        import pyperclip

        self._pyperclip = pyperclip

    def read(self) -> str | None:
        time.sleep(self._poll_interval)
        for _ in range(self._retry):
            try:
                return self._pyperclip.paste()
            except self._pyperclip.PyperclipWindowsException:
                time.sleep(self._retry_delay)
        # すべて失敗
        print("Clipboard unavailable, retrying...")
        return None

    def close(self) -> None:
        pass


class SocketInputSource(InputSource):
    """
    Emuera (改造版) からの push を受け取る TCP ソース\n
    本アプリが 127.0.0.1:<port> で listen し, Emuera が client として接続する\n
    メッセージは「4byte 長さ (big-endian, 符号なし) + UTF-8 本文」でフレーミングされる\n
    単一クライアント想定. 切断時は再 accept する (Emuera 再起動に追従)
    """

    _LEN_PREFIX = struct.Struct(">I")  # 4byte big-endian unsigned

    def __init__(self, host: str = "127.0.0.1", port: int = 52340, sock_timeout_sec: float = 0.5):
        self._host = host
        self._port = port
        self._timeout = sock_timeout_sec

        self._server: socket.socket | None = None
        self._conn: socket.socket | None = None
        self._buf = bytearray()

    def open(self) -> None:
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind((self._host, self._port))
        self._server.listen(1)
        self._server.settimeout(self._timeout)
        print(f"SocketInputSource listening on {self._host}:{self._port}")

    def _accept(self) -> None:
        """
        クライアント (Emuera) の接続を 1 件受け付ける\n
        タイムアウト時は何もしない (self._conn は None のまま)
        """
        try:
            conn, addr = self._server.accept()
        except (TimeoutError, socket.timeout):
            return
        except OSError:
            return
        conn.settimeout(self._timeout)
        self._conn = conn
        self._buf.clear()
        print(f"Emuera connected from {addr}")

    def _recv_into_buf(self) -> bool:
        """
        ソケットから可能な限り受信してバッファへ積む\n
        タイムアウト時は False (新規データなし), 切断検知時も後始末して False

        Returns:
            bool: 新規データを受信したか
        """
        try:
            chunk = self._conn.recv(65536)
        except (TimeoutError, socket.timeout):
            return False
        except OSError:
            self._drop_conn()
            return False

        if not chunk:
            # 対向が正常切断
            self._drop_conn()
            return False

        self._buf.extend(chunk)
        return True

    def _drop_conn(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except OSError:
                pass
        self._conn = None
        self._buf.clear()
        print("Emuera disconnected")

    def _pop_frame(self) -> str | None:
        """
        バッファから 1 フレーム分の本文を取り出す\n
        フレームが未完成の場合は None

        Returns:
            str | None: 本文, 未完成なら None
        """
        if len(self._buf) < self._LEN_PREFIX.size:
            return None
        (length,) = self._LEN_PREFIX.unpack_from(self._buf, 0)
        end = self._LEN_PREFIX.size + length
        if len(self._buf) < end:
            return None
        body = bytes(self._buf[self._LEN_PREFIX.size : end])
        del self._buf[:end]
        return body.decode("utf-8", errors="replace")

    def read(self) -> str | None:
        if self._conn is None:
            self._accept()
            return None

        # まずバッファに残っている完成フレームを優先的に返す
        frame = self._pop_frame()
        if frame is not None:
            return frame

        if not self._recv_into_buf():
            return None

        return self._pop_frame()

    def close(self) -> None:
        self._drop_conn()
        if self._server is not None:
            try:
                self._server.close()
            except OSError:
                pass
            self._server = None
