"""
PySide6 + asyncio ファイル監視アプリケーション (シンプル版)

こちらはQtのシグナル/スロットを主体とした、よりシンプルな実装です。
asyncioの使用を最小限に抑え、Qtネイティブな設計にしています。

必要なパッケージ:
pip install PySide6 watchdog
"""

import os
import random
import string
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal, Slot
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

# ==================== Observer (Watchdog) ====================


class FileEventHandler(FileSystemEventHandler):
    """ファイルシステムイベントハンドラ"""

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def on_created(self, event: FileSystemEvent):
        if not event.is_directory:
            self.callback()

    def on_deleted(self, event: FileSystemEvent):
        if not event.is_directory:
            self.callback()


class DirectoryObserver(QObject):
    """ディレクトリ監視モジュール"""

    # イベントシグナル
    dir_changed = Signal(int)  # ファイル数を通知

    def __init__(self, watch_path: Path):
        super().__init__()
        self.watch_path = watch_path
        self.observer: Optional[Observer] = None

    def start(self):
        """監視開始"""
        if not self.watch_path.exists():
            self.watch_path.mkdir(parents=True)

        event_handler = FileEventHandler(
            callback=lambda: self.dir_changed.emit(self._count_files())
        )

        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.watch_path), recursive=False)
        self.observer.start()

        # 初期カウント通知
        self.dir_changed.emit(self._count_files())

    def stop(self):
        """監視停止"""
        if self.observer:
            self.observer.stop()
            self.observer.join()

    def _count_files(self) -> int:
        """ディレクトリ内のファイル数をカウント"""
        return len([f for f in self.watch_path.iterdir() if f.is_file()])


# ==================== Worker ====================


class FileWorker(QObject):
    """ファイル操作モジュール"""

    # イベントシグナル
    job_started = Signal()
    job_completed = Signal()

    def __init__(self, work_path: Path):
        super().__init__()
        self.work_path = work_path

    @Slot()
    def generate_file(self):
        """ランダムなファイルを生成"""
        self.job_started.emit()

        # タイマーで非同期風に処理（UIブロック回避）
        QTimer.singleShot(500, self._do_generate)

    def _do_generate(self):
        """実際のファイル生成処理"""
        try:
            filename = "".join(random.choices(string.ascii_lowercase, k=8)) + ".txt"
            content = "".join(random.choices(string.ascii_letters + string.digits, k=100))

            filepath = self.work_path / filename
            filepath.write_text(content)
        finally:
            self.job_completed.emit()

    @Slot()
    def delete_random_file(self):
        """ランダムにファイルを削除"""
        self.job_started.emit()

        # タイマーで非同期風に処理
        QTimer.singleShot(500, self._do_delete)

    def _do_delete(self):
        """実際のファイル削除処理"""
        try:
            files = [f for f in self.work_path.iterdir() if f.is_file()]

            if files:
                target = random.choice(files)
                target.unlink()
        finally:
            self.job_completed.emit()


# ==================== Displayer (GUI) ====================


class DisplayerWidget(QWidget):
    """GUI表示モジュール"""

    # リクエストシグナル
    generate_requested = Signal()
    delete_requested = Signal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """UI初期化"""
        layout = QVBoxLayout()

        # ファイル数表示
        self.file_count_label = QLabel("ファイル数: 0")
        self.file_count_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.file_count_label)

        # ジョブ状態表示
        self.job_status_label = QLabel("状態: 待機中")
        self.job_status_label.setStyleSheet("font-size: 14px; color: green;")
        layout.addWidget(self.job_status_label)

        # 作成ボタン
        self.generate_btn = QPushButton("作成")
        self.generate_btn.clicked.connect(self.generate_requested.emit)
        layout.addWidget(self.generate_btn)

        # ランダム削除ボタン
        self.delete_btn = QPushButton("ランダム削除")
        self.delete_btn.clicked.connect(self.delete_requested.emit)
        layout.addWidget(self.delete_btn)

        self.setLayout(layout)

    @Slot(int)
    def update_file_count(self, count: int):
        """ファイル数表示を更新"""
        self.file_count_label.setText(f"ファイル数: {count}")

    @Slot()
    def set_job_active(self):
        """ジョブ開始状態に設定"""
        self.job_status_label.setText("状態: ファイル操作中...")
        self.job_status_label.setStyleSheet("font-size: 14px; color: orange;")
        self.generate_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

    @Slot()
    def set_job_idle(self):
        """ジョブ待機状態に設定"""
        self.job_status_label.setText("状態: 待機中")
        self.job_status_label.setStyleSheet("font-size: 14px; color: green;")
        self.generate_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)


# ==================== Master ====================


class Master(QObject):
    """統括モジュール - シグナル/スロット接続管理"""

    def __init__(self, work_path: Path):
        super().__init__()
        self.work_path = work_path

        # 各モジュールの初期化
        self.displayer = DisplayerWidget()
        self.observer = DirectoryObserver(work_path)
        self.worker = FileWorker(work_path)

        # シグナル/スロット接続
        self._connect_signals()

    def _connect_signals(self):
        """シグナル/スロット接続の設定"""

        # Observer → Displayer: ファイル数更新
        self.observer.dir_changed.connect(self.displayer.update_file_count)

        # Displayer → Worker: ファイル操作リクエスト
        self.displayer.generate_requested.connect(self.worker.generate_file)
        self.displayer.delete_requested.connect(self.worker.delete_random_file)

        # Worker → Displayer: ジョブ状態更新
        self.worker.job_started.connect(self.displayer.set_job_active)
        self.worker.job_completed.connect(self.displayer.set_job_idle)

    def start(self):
        """アプリケーション開始"""
        self.observer.start()

    def stop(self):
        """アプリケーション停止"""
        self.observer.stop()


# ==================== Main Window ====================


class MainWindow(QMainWindow):
    """メインウィンドウ"""

    def __init__(self, master: Master):
        super().__init__()
        self.master = master

        self.setWindowTitle("ファイル監視アプリケーション (シンプル版)")
        self.setGeometry(100, 100, 400, 250)

        self.setCentralWidget(master.displayer)

    def closeEvent(self, event):
        """ウィンドウクローズ時の処理"""
        self.master.stop()
        event.accept()


# ==================== アプリケーション起動 ====================


def main():
    """メインエントリポイント"""

    # 監視対象ディレクトリ
    work_path = Path.home() / "file_monitor_test_simple"

    app = QApplication([])

    # Masterとウィンドウの作成
    master = Master(work_path)
    window = MainWindow(master)

    # アプリケーション開始
    master.start()
    window.show()

    print(f"監視ディレクトリ: {work_path}")
    print("アプリケーションを起動しました (シンプル版)")

    app.exec()


if __name__ == "__main__":
    main()
