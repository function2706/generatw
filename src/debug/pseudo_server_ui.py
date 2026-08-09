"""
擬似サーバ UI

A1111 / ComfyUI のダミーサーバを 1 つの GUI から起動・停止・設定する\n
ダミー生成時間や失敗率などのサーバオプションを操作できる\n
実行: python src/debug/pseudo_server_ui.py  (もしくは run_srv_ui.bat)
"""

from __future__ import annotations

import os
import queue
import socket
import sys
import threading
import tkinter
from tkinter import ttk

import uvicorn

# displayer のテーマ/部品を流用するため src をパスに追加
_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import pseudo_a1111  # noqa: E402  (same-dir module)
import pseudo_comfyui  # noqa: E402

from displayer import theme, widgets  # noqa: E402
from displayer.theme import STYLES  # noqa: E402

# バックエンド表示名 -> (FastAPI app, 既定ポート)
BACKENDS: dict[str, tuple] = {
    "A1111": (pseudo_a1111.app, "7860"),
    "ComfyUI": (pseudo_comfyui.app, "8188"),
}
THEME_LABELS = {"自動": "auto", "ライト": "light", "ダーク": "dark"}
THEME_PREFS = {v: k for k, v in THEME_LABELS.items()}


class ServerRunner:
    """
    uvicorn サーバを別スレッドで起動・停止するラッパ
    """

    def __init__(self):
        self._server: uvicorn.Server | None = None
        self._thread: threading.Thread | None = None

    def running(self) -> bool:
        """稼働中か"""
        return self._thread is not None and self._thread.is_alive()

    def start(self, app, host: str, port: int) -> None:
        """
        サーバを起動する (別スレッド)

        Args:
            app: FastAPI アプリ
            host (str): バインドするホスト
            port (int): バインドするポート
        """
        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        self._server = uvicorn.Server(config)
        # 非メインスレッドではシグナルハンドラを張らない
        self._server.install_signal_handlers = lambda: None
        self._thread = threading.Thread(target=self._server.run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """サーバを停止する"""
        if self._server is not None:
            self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=5)
        self._server = None
        self._thread = None


class QueueWriter:
    """
    書き込み内容をキューへ流しつつ, 元のストリームにも転送するテキストライタ
    """

    def __init__(self, q: queue.Queue, mirror):
        self._q = q
        self._mirror = mirror

    def write(self, text: str) -> int:
        if text:
            self._q.put(text)
        if self._mirror is not None:
            try:
                self._mirror.write(text)
            except (ValueError, OSError):
                pass
        return len(text)

    def flush(self) -> None:
        if self._mirror is not None:
            try:
                self._mirror.flush()
            except (ValueError, OSError):
                pass

    def isatty(self) -> bool:
        # uvicorn のカラーフォーマッタが参照する. 色コードは Text に不要なので False
        return False


def port_available(host: str, port: int) -> bool:
    """
    host:port が bind 可能か (空いているか) を判定する

    Args:
        host (str): ホスト
        port (int): ポート

    Returns:
        bool: 空いていれば True
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


class PseudoServerUI:
    """
    擬似サーバ管理 GUI
    """

    def __init__(self, root: tkinter.Tk):
        """
        コンストラクタ

        Args:
            root (tkinter.Tk): ルートウィンドウ
        """
        self.root = root
        self.runner = ServerRunner()
        self.log_queue: queue.Queue[str] = queue.Queue()

        # stdout/stderr をキューへ (uvicorn ログや print を UI に取り込む)
        self._orig_out, self._orig_err = sys.stdout, sys.stderr
        sys.stdout = QueueWriter(self.log_queue, self._orig_out)
        sys.stderr = QueueWriter(self.log_queue, self._orig_err)

        theme.apply(root, "auto")
        root.title("picmaker - 擬似サーバ")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)
        root.geometry("560x620")
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        self._build_toolbar()
        self._build_body()

        self._apply_settings()
        self._refresh_state()
        self.root.after(120, self._poll_log)

    # -------------------------------------------------------------------------
    # 構築
    # -------------------------------------------------------------------------

    def _build_toolbar(self) -> None:
        bar = ttk.Frame(self.root, padding=(12, 10, 12, 6))
        bar.grid(row=0, column=0, sticky="ew")
        bar.columnconfigure(1, weight=1)
        ttk.Label(bar, text="擬似サーバ", style=STYLES.title).grid(row=0, column=0, sticky="w")
        ttk.Label(bar, text="テーマ", style=STYLES.section).grid(row=0, column=2, padx=(0, 6))
        self.theme_var = tkinter.StringVar(value="自動")
        combo = ttk.Combobox(
            bar, textvariable=self.theme_var, values=list(THEME_LABELS.keys()),
            state="readonly", width=8,
        )
        combo.grid(row=0, column=3, sticky="e")
        combo.bind("<<ComboboxSelected>>", lambda e: self.on_change_theme())

    def _build_body(self) -> None:
        body = ttk.Frame(self.root, padding=(12, 0, 12, 12))
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(3, weight=1)

        # --- 設定カード ------------------------------------------------------
        ttk.Label(body, text="サーバ設定", style=STYLES.section).grid(
            row=0, column=0, sticky="w", pady=(6, 2)
        )
        card = ttk.Frame(body, style=STYLES.card, padding=12)
        card.grid(row=1, column=0, sticky="ew")

        ttk.Label(card, text="バックエンド", style=STYLES.muted).grid(
            row=0, column=0, padx=(0, 6), pady=5, sticky="e"
        )
        self.backend_var = tkinter.StringVar(value="ComfyUI")
        self.backend_combo = ttk.Combobox(
            card, textvariable=self.backend_var, values=list(BACKENDS.keys()),
            state="readonly", width=12,
        )
        self.backend_combo.grid(row=0, column=1, pady=5, sticky="w")
        self.backend_combo.bind("<<ComboboxSelected>>", lambda e: self.on_change_backend())

        self.host_entry = widgets.field_entry(card, "ホスト", 1, 0, 16, "127.0.0.1")
        self.port_entry = widgets.field_entry(card, "ポート", 1, 2, 8, "8188")
        self.cooldown_entry = widgets.field_entry(
            card, "生成時間(秒)", 2, 0, 8, "0.0", on_change=self._apply_settings
        )
        self.fail_entry = widgets.field_entry(
            card, "失敗率(%)", 2, 2, 8, "0", on_change=self._apply_settings
        )

        # --- 操作行 ----------------------------------------------------------
        ctrl = ttk.Frame(body)
        ctrl.grid(row=2, column=0, sticky="ew", pady=(10, 4))
        ctrl.columnconfigure(1, weight=1)
        self.toggle_button = ttk.Button(ctrl, text="起動", width=10, command=self.on_toggle)
        self.toggle_button.grid(row=0, column=0, sticky="w")
        self.status_var = tkinter.StringVar(value="停止中")
        self.status_label = ttk.Label(ctrl, textvariable=self.status_var)
        self.status_label.grid(row=0, column=1, padx=10, sticky="w")

        # --- ログ ------------------------------------------------------------
        head = ttk.Frame(body)
        head.grid(row=3, column=0, sticky="ew", pady=(6, 3))
        head.columnconfigure(0, weight=1)
        ttk.Label(head, text="ログ", style=STYLES.section).grid(row=0, column=0, sticky="w")
        ttk.Button(head, text="クリア", command=self.clear_log).grid(row=0, column=1, sticky="e")

        log_frame = ttk.Frame(body)
        log_frame.grid(row=4, column=0, sticky="nsew")
        body.rowconfigure(4, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = widgets.themed_text(log_frame, height=12, wrap="char")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scroll.set, state="disabled")

    # -------------------------------------------------------------------------
    # 設定
    # -------------------------------------------------------------------------

    @property
    def current_app(self):
        """現在選択中のバックエンドの FastAPI app"""
        return BACKENDS[self.backend_var.get()][0]

    def _apply_settings(self) -> None:
        """
        生成時間・失敗率を現在のバックエンドの app.state へ反映する (稼働中も即時)
        """
        app = self.current_app
        try:
            app.state.cooldown = max(0.0, float(self.cooldown_entry.get()))
        except ValueError:
            pass
        try:
            app.state.fail_rate = min(1.0, max(0.0, float(self.fail_entry.get()) / 100.0))
        except ValueError:
            pass

    # -------------------------------------------------------------------------
    # ハンドラ
    # -------------------------------------------------------------------------

    def on_change_backend(self) -> None:
        """バックエンド変更: 既定ポートを補完し, 設定を反映する"""
        self.port_entry.delete(0, "end")
        self.port_entry.insert(0, BACKENDS[self.backend_var.get()][1])
        self._apply_settings()

    def on_toggle(self) -> None:
        """起動/停止ボタンハンドラ"""
        if self.runner.running():
            self._log("[UI] サーバを停止します...\n")
            self.runner.stop()
        else:
            self._start()
        self._refresh_state()

    def _start(self) -> None:
        """入力値を検証してサーバを起動する"""
        host = self.host_entry.get().strip() or "127.0.0.1"
        try:
            port = int(self.port_entry.get())
        except ValueError:
            self._set_status("ポート番号が不正です", ok=False)
            return
        if not port_available(host, port):
            self._set_status(f"{host}:{port} は使用中です", ok=False)
            return

        self._apply_settings()
        self._log(f"[UI] {self.backend_var.get()} を {host}:{port} で起動します\n")
        self.runner.start(self.current_app, host, port)

    def on_change_theme(self) -> None:
        """テーマ切替"""
        theme.apply(self.root, THEME_LABELS.get(self.theme_var.get(), "auto"))
        widgets.apply_toplevel_bg(self.root)
        widgets.retheme_text(self.log_text)
        self._refresh_state()

    def on_close(self) -> None:
        """ウィンドウクローズ: サーバ停止と標準出力の復帰"""
        if self.runner.running():
            self.runner.stop()
        sys.stdout, sys.stderr = self._orig_out, self._orig_err
        self.root.destroy()

    # -------------------------------------------------------------------------
    # 表示更新
    # -------------------------------------------------------------------------

    def _refresh_state(self) -> None:
        """稼働状態に応じて表示とウィジェットの活性を更新する"""
        running = self.runner.running()
        self.toggle_button.configure(text="停止" if running else "起動")
        entry_state = "disabled" if running else "normal"
        self.backend_combo.configure(state="disabled" if running else "readonly")
        self.host_entry.configure(state=entry_state)
        self.port_entry.configure(state=entry_state)
        if running:
            host = self.host_entry.get().strip() or "127.0.0.1"
            addr = f"{host}:{self.port_entry.get()}"
            self._set_status(f"起動中: {self.backend_var.get()} @ {addr}", ok=True)
        elif "使用中" not in self.status_var.get() and "不正" not in self.status_var.get():
            self._set_status("停止中", ok=None)

    def _set_status(self, message: str, ok: bool | None) -> None:
        """状態ラベルを更新する (ok: True=正常, False=異常, None=中立)"""
        color = theme.current.muted if ok is None else (
            theme.current.ok if ok else theme.current.err
        )
        self.status_label.configure(foreground=color)
        self.status_var.set(message)

    # -------------------------------------------------------------------------
    # ログ
    # -------------------------------------------------------------------------

    def _poll_log(self) -> None:
        """ログキューを掃き出して表示に反映する"""
        drained = []
        try:
            while True:
                drained.append(self.log_queue.get_nowait())
        except queue.Empty:
            pass
        if drained:
            self._append_log("".join(drained))
        # 停止検知 (スレッド終了時に表示を戻す)
        if not self.runner.running() and self.toggle_button.cget("text") == "停止":
            self._refresh_state()
        self.root.after(150, self._poll_log)

    def _append_log(self, text: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text)
        self.log_text.see("end")
        # 行数が増えすぎたら先頭を削る
        if int(self.log_text.index("end-1c").split(".")[0]) > 2000:
            self.log_text.delete("1.0", "1000.0")
        self.log_text.configure(state="disabled")

    def _log(self, text: str) -> None:
        self.log_queue.put(text)

    def clear_log(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")


def main() -> None:
    root = tkinter.Tk()
    PseudoServerUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
