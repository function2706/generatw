"""
メインスクリプト
"""

import argparse
import signal

from picmaker_reverse import PicMakerReverse
from picmaker_tw import PicMakerTW


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
        "-m", "--mode", choices=["TW", "R", "dummy"], default="dummy", help="Run as this mode"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Show all clipboard and stats")
    parser.add_argument("-c", "--check", action="store_true", help="Check option values")
    args = parser.parse_args()
    if args.check:
        print(f"[debug] mode={args.mode}, verbose={args.verbose}")
        return
    if args.mode == "TW":
        pm = PicMakerTW(args.verbose)
    elif args.mode == "R":
        pm = PicMakerReverse(args.verbose)
    else:
        print(f"[debug] mode={args.mode}, verbose={args.verbose}")
        return
    signal.signal(signal.SIGINT, pm.sigint_handler)
    # Tkinterのイベントループ開始
    pm.tk_root.after(100, pm.doit)
    pm.tk_root.mainloop()


if __name__ == "__main__":
    main()
    print("Exit...")
