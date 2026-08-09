"""
ログウィンドウ

標準出力 / 標準エラーを捕捉し, GUI に表示する (コンソールにもミラー)\n
デバッグ用の print / dump_json 出力を別ウィンドウで確認できる
"""

from __future__ import annotations

import queue
import sys
import threading
import tkinter
from collections import deque
from tkinter import TclError, ttk
from typing import TYPE_CHECKING

from displayer import widgets
from displayer.theme import STYLES

if TYPE_CHECKING:
    from displayer.displayer import Displayer


class _Stream:
    """
    LogCapture へ書き込みを委譲しつつ, 元のストリームへもミラーするテキストストリーム
    """

    def __init__(self, capture: LogCapture, mirror):
        self._capture = capture
        self._mirror = mirror

    def write(self, text: str) -> int:
        if self._mirror is not None:
            try:
                self._mirror.write(text)
            except (ValueError, OSError):
                pass
        self._capture.append(text)
        return len(text)

    def flush(self) -> None:
        if self._mirror is not None:
            try:
                self._mirror.flush()
            except (ValueError, OSError):
                pass

    def isatty(self) -> bool:
        return False


class LogCapture:
    """
    stdout / stderr を捕捉し, 履歴 (直近 N チャンク) と, 表示中ウィンドウ向けの
    ライブキューへ配る. スレッド安全
    """

    def __init__(self, maxlen: int = 4000):
        self._lock = threading.Lock()
        self._history: deque[str] = deque(maxlen=maxlen)
        self._live: queue.Queue[str] | None = None
        self._orig_out = sys.stdout
        self._orig_err = sys.stderr
        self._installed = False

    def install(self) -> None:
        """stdout / stderr を捕捉ストリームへ差し替える"""
        if self._installed:
            return
        sys.stdout = _Stream(self, self._orig_out)
        sys.stderr = _Stream(self, self._orig_err)
        self._installed = True

    def restore(self) -> None:
        """stdout / stderr を元へ戻す"""
        if not self._installed:
            return
        sys.stdout = self._orig_out
        sys.stderr = self._orig_err
        self._installed = False

    def append(self, text: str) -> None:
        """捕捉した文字列を履歴とライブキューへ積む"""
        with self._lock:
            self._history.append(text)
            if self._live is not None:
                self._live.put(text)

    def attach(self) -> tuple[str, queue.Queue[str]]:
        """
        表示開始: 現在の履歴スナップショットと, 以降の追記を受けるキューを返す\n
        スナップショット取得とキュー登録をロック下で行うため取りこぼし / 重複が起きない
        """
        with self._lock:
            self._live = queue.Queue()
            return "".join(self._history), self._live

    def detach(self) -> None:
        """表示終了: ライブ配信を止める (履歴は保持)"""
        with self._lock:
            self._live = None

    def clear(self) -> None:
        """履歴を消去する"""
        with self._lock:
            self._history.clear()


class LogWindow:
    """
    ログ表示ウィンドウ (Toplevel)
    """

    def __init__(self, owner: Displayer, capture: LogCapture):
        """
        コンストラクタ

        Args:
            owner (Displayer): Displayer インスタンス
            capture (LogCapture): 捕捉器 (Displayer が生成・install 済み)
        """
        self.super_owner = owner
        self.capture = capture
        self.window: tkinter.Toplevel = None
        self.text: tkinter.Text = None
        self.autoscroll_var: tkinter.BooleanVar = None
        self._queue: queue.Queue[str] | None = None
        self._after_id: str = ""

    def construct(self, fix_position=False) -> None:
        """
        ログウィンドウを構築する\n
        すでに開いている場合は何もしない

        Args:
            fix_position (bool): 表示位置を親ウィンドウ基準に固定するか
        """
        if self.existed() and self.window:
            return

        self.window = tkinter.Toplevel(self.super_owner.master.root)
        widgets.apply_toplevel_bg(self.window)
        win_w, win_h = 620, 420
        self.window.title("picmaker - ログ")
        self.window.protocol("WM_DELETE_WINDOW", self.destroy)
        self.window.geometry(f"{win_w}x{win_h}")
        self.window.rowconfigure(1, weight=1)
        self.window.columnconfigure(0, weight=1)
        if fix_position:
            x = self.super_owner.config_window_x + 60
            y = self.super_owner.config_window_y + self.super_owner.config_window_height + 50
            max_y = self.window.winfo_screenheight() - win_h - 60
            self.window.geometry(f"+{x}+{min(y, max(0, max_y))}")

        # --- ヘッダ (自動スクロール / クリア) --------------------------------
        head = ttk.Frame(self.window, padding=(10, 8, 10, 4))
        head.grid(row=0, column=0, sticky="ew")
        head.columnconfigure(0, weight=1)
        ttk.Label(head, text="標準出力 / 標準エラー", style=STYLES.section).grid(
            row=0, column=0, sticky="w"
        )
        self.autoscroll_var = tkinter.BooleanVar(value=True)
        ttk.Checkbutton(head, text="自動スクロール", variable=self.autoscroll_var).grid(
            row=0, column=1, padx=(0, 8)
        )
        ttk.Button(head, text="クリア", command=self.clear).grid(row=0, column=2)

        # --- ログ本文 --------------------------------------------------------
        body = ttk.Frame(self.window, padding=(10, 0, 10, 10))
        body.grid(row=1, column=0, sticky="nsew")
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=1)
        self.text = widgets.themed_text(body, wrap="char")
        self.text.grid(row=0, column=0, sticky="nsew")
        yscroll = ttk.Scrollbar(body, orient="vertical", command=self.text.yview)
        yscroll.grid(row=0, column=1, sticky="ns")
        self.text.configure(yscrollcommand=yscroll.set)

        # 履歴を流し込み, 以降はライブキューをポーリング
        snapshot, self._queue = self.capture.attach()
        self._append(snapshot)
        self._after_id = self.window.after(150, self._poll)

    def destroy(self) -> None:
        """ログウィンドウのクローズ時のハンドラ"""
        self.capture.detach()
        self._queue = None
        if self._after_id and self.window is not None:
            try:
                self.window.after_cancel(self._after_id)
            except TclError:
                pass
        self._after_id = ""
        if self.existed():
            self.window.destroy()
        self.window = None

    def existed(self) -> bool:
        """
        ログウィンドウが開かれているか

        Returns:
            bool: True: 開かれている, False: 開かれていない or TclError 例外発生
        """
        if self.window is None:
            return False
        try:
            return bool(self.window.winfo_exists())
        except TclError:
            return False

    def retheme(self) -> None:
        """テーマ切替時にテキスト配色を追従させる"""
        if self.text is not None:
            widgets.retheme_text(self.text)

    def clear(self) -> None:
        """表示と履歴を消去する"""
        self.capture.clear()
        if self.text is not None:
            self.text.configure(state="normal")
            self.text.delete("1.0", "end")
            self.text.configure(state="disabled")

    def _poll(self) -> None:
        """ライブキューを掃き出して表示へ反映する"""
        if not self.existed() or self._queue is None:
            return
        drained: list[str] = []
        try:
            while True:
                drained.append(self._queue.get_nowait())
        except queue.Empty:
            pass
        if drained:
            self._append("".join(drained))
        self._after_id = self.window.after(150, self._poll)

    def _append(self, text: str) -> None:
        if not text or self.text is None:
            return
        self.text.configure(state="normal")
        self.text.insert("end", text)
        # 肥大化防止: 一定行を超えたら先頭を削る
        if int(self.text.index("end-1c").split(".")[0]) > 5000:
            self.text.delete("1.0", "2000.0")
        if self.autoscroll_var.get():
            self.text.see("end")
        self.text.configure(state="disabled")
