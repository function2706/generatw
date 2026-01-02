"""
メインスクリプト
"""

import argparse
import signal
import tkinter
from tkinter import ttk

from picmaker_reverse import PicMakerReverse
from picmaker_tw import PicMakerTW


def main() -> None:
    """
    エントリポイント
    """

    flag_exe = True

    def on_ok_mode_window() -> None:
        """
        モード選択ウィンドウ OK 時のハンドラ
        """
        tk_root.destroy()

    def on_close_mode_window() -> None:
        """
        モード選択ウィンドウクローズ時のハンドラ
        """
        nonlocal flag_exe
        on_ok_mode_window()
        flag_exe = False

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
            tk_root = tkinter.Tk()
            tk_root.protocol("WM_DELETE_WINDOW", on_close_mode_window)
            tk_root.title("picmaker - モード選択")
            ttk.Label(tk_root, text="モード").grid(row=0, column=0, padx=6, pady=6, sticky="w")
            mode_options = ["Reverse", "The World"]
            combo_modes = tkinter.StringVar(value=mode_options[0])
            combo = ttk.Combobox(
                tk_root,
                textvariable=combo_modes,
                values=mode_options,
                state="readonly",
                width=10,
            )
            combo.grid(row=0, column=1, padx=6, pady=6, sticky="w")
            button_ok = ttk.Button(tk_root, text="OK", command=on_ok_mode_window)
            button_ok.grid(row=0, column=2, padx=6, pady=6, sticky="w")
            tk_root.mainloop()
            if not flag_exe:
                return

            if combo_modes.get() == "The World":
                pm = PicMakerTW()
            elif combo_modes.get() == "Reverse":
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
