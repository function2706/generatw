"""
メインスクリプト
"""

import argparse
import signal
import tkinter
from tkinter import ttk

from picmaker_reverse import PicMakerReverse
from picmaker_tw import PicMakerTW


class mode_window:
    """
    初期ウィンドウ管理クラス
    """

    def __init__(self):
        """
        コンストラクタ
        """
        self.flag_exe_main = True

        self.tk_root = tkinter.Tk()
        self.tk_root.protocol("WM_DELETE_WINDOW", self.on_close_mode_window)
        self.tk_root.title("picmaker - モード選択")
        ttk.Label(self.tk_root, text="モード").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        mode_options = ["Reverse", "The World"]
        self.combo_modes = tkinter.StringVar(value=mode_options[0])
        combo = ttk.Combobox(
            self.tk_root,
            textvariable=self.combo_modes,
            values=mode_options,
            state="readonly",
            width=10,
        )
        combo.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        button_ok = ttk.Button(self.tk_root, text="OK", command=self.on_ok_mode_window)
        button_ok.grid(row=0, column=2, padx=6, pady=6, sticky="w")

    def on_ok_mode_window(self) -> None:
        """
        モード選択ウィンドウ OK 時のハンドラ
        """
        self.tk_root.destroy()

    def on_close_mode_window(self) -> None:
        """
        モード選択ウィンドウクローズ時のハンドラ
        """
        self.on_ok_mode_window()
        self.flag_exe_main = False

    def entrypoint(self) -> None:
        """
        エントリポイント
        """
        self.tk_root.mainloop()

    @property
    def mode(self) -> str:
        return self.combo_modes.get()


def main() -> None:
    """
    エントリポイント
    """

    parser = argparse.ArgumentParser(
        prog="picmaker.py",
        description="Era Picture Maker",
        epilog="ex: python picmaker.py -m TW",
    )
    parser.add_argument(
        "-m", "--mode", choices=["TW", "R", "None"], default="None", help="Run as this mode"
    )
    args = parser.parse_args()

    pm = None
    try:
        if args.mode == "TW":
            pm = PicMakerTW()
        elif args.mode == "R":
            pm = PicMakerReverse()
        else:
            window = mode_window()
            window.entrypoint()
            if not window.flag_exe_main:
                return
            elif window.mode == "The World":
                pm = PicMakerTW()
            elif window.mode == "Reverse":
                pm = PicMakerReverse()
        if pm is not None:
            signal.signal(signal.SIGINT, pm.sigint_handler)
            pm.displayer.entrypoint()
    finally:
        if pm is not None:
            pm.finalize()


if __name__ == "__main__":
    main()
    print("Exit...")
