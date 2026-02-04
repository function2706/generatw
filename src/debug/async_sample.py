import asyncio
import sys

from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget
from qasync import QEventLoop, asyncSlot


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PySide6 + asyncio Sample")

        self.layouta = QVBoxLayout()
        self.setLayout(self.layouta)

        self.label = QLabel("Counter: 0")
        self.layouta.addWidget(self.label)

        self.btn_start = QPushButton("Start Counting")
        self.layouta.addWidget(self.btn_start)

        self.btn_stop = QPushButton("Stop")
        self.layouta.addWidget(self.btn_stop)
        self.btn_stop.setEnabled(False)

        # 状態
        self._task = None
        self._counter = 0

        # ボタンハンドラ
        self.btn_start.clicked.connect(self.start_counting)
        self.btn_stop.clicked.connect(self.stop_counting)

    @asyncSlot()
    async def start_counting(self):
        """
        asyncio タスクでカウントを進める
        """
        # ボタンの状態変更
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

        self._counter = 0

        # 非同期カウント処理
        while self.btn_stop.isEnabled():
            self._counter += 1
            self.label.setText(f"Counter: {self._counter}")
            await asyncio.sleep(0.5)

        self.btn_start.setEnabled(True)

    def stop_counting(self):
        """
        counting を止める
        """
        self.btn_stop.setEnabled(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # asyncio イベントループを PySide のループに差し込む
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    with loop:
        loop.run_forever()
