"""
メインスクリプト
"""

import argparse
import signal
import tkinter
from tkinter import ttk

from common.interfaces import BackEnd, FrontEnd
from master import Master


class ModeWindow:
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
        ttk.Label(self.tk_root, text="フロントエンド").grid(
            row=0, column=0, padx=6, pady=6, sticky="w"
        )
        front_options = ["Reverse", "The World"]
        self.combo_front = tkinter.StringVar(value=front_options[0])
        combo_front = ttk.Combobox(
            self.tk_root,
            textvariable=self.combo_front,
            values=front_options,
            state="readonly",
            width=10,
        )
        combo_front.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        ttk.Label(self.tk_root, text="バックエンド").grid(
            row=1, column=0, padx=6, pady=6, sticky="w"
        )
        back_options = ["A1111", "ComfyUI"]
        self.combo_back = tkinter.StringVar(value=back_options[0])
        combo_back = ttk.Combobox(
            self.tk_root,
            textvariable=self.combo_back,
            values=back_options,
            state="readonly",
            width=10,
        )
        combo_back.grid(row=1, column=1, padx=6, pady=6, sticky="w")
        button_ok = ttk.Button(self.tk_root, text="OK", command=self.on_ok_mode_window)
        button_ok.grid(row=2, column=0, padx=6, pady=6, sticky="w")

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
    def front(self) -> str:
        return self.combo_front.get()

    @property
    def back(self) -> str:
        return self.combo_back.get()


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
        "-f", "--front", choices=["W", "R", "None"], default="None", help="Frontend"
    )
    parser.add_argument("-b", "--back", choices=["A", "C", "None"], default="None", help="Backend")
    args = parser.parse_args()

    master: Master = None
    try:
        match (args.front, args.back):
            case ("R", "A"):
                master = Master(FrontEnd.reverse, BackEnd.a1111)
            case ("R", "C"):
                master = Master(FrontEnd.reverse, BackEnd.comfy_ui)
            case ("W", "A"):
                master = Master(FrontEnd.the_world, BackEnd.a1111)
            case ("W", "C"):
                master = Master(FrontEnd.the_world, BackEnd.comfy_ui)
            case _:
                window = ModeWindow()
                window.entrypoint()
                if not window.flag_exe_main:
                    return

                master = Master(
                    frontend=FrontEnd.reverse
                    if window.front == "Reverse"
                    else FrontEnd.the_world
                    if window.front == "The World"
                    else None,
                    backend=BackEnd.a1111
                    if window.back == "A1111"
                    else BackEnd.comfy_ui
                    if window.back == "ComfyUI"
                    else None,
                )
        if master is not None:
            signal.signal(signal.SIGINT, master.sigint_handler)
            master.start()
    finally:
        if master is not None:
            master.finalize()


if __name__ == "__main__":
    main()
    print("Exit...")
