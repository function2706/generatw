from tw_pic_maker import TWPicMaker
from reverse_pic_maker import ReversePicMaker
import argparse, signal

# エントリポイント
def main() -> None:
    try:
        parser = argparse.ArgumentParser(
            prog="era_pic_maker.py",
            description="Era Picture Maker",
            epilog="ex: python era_pic_maker.py -m TW"
        )
        parser.add_argument("-m", "--mode", choices=["TW", "R", "hoge"], default="TW", help="Run as this mode")
        parser.add_argument("-p", "--post", action="store_true", help="Do posting via RestAPI")
        parser.add_argument("-v", "--verbose", action="store_true", help="Show all clipboard and stats")

        args = parser.parse_args()

        if args.mode == "TW":
            pm = TWPicMaker(args.post, args.verbose)
        elif args.mode == "R":
            pm = ReversePicMaker(args.post, args.verbose)
        else:
            print(f"[debug] mode={args.mode}, post={args.post}, verbose={args.verbose}")
            return

        signal.signal(signal.SIGINT, pm.sigint_handler)

        # Tkinterのイベントループ開始
        pm.tk_root.after(100, pm.doit)  # 監視を開始
        pm.tk_root.mainloop()
    except KeyboardInterrupt:
        print("\nExit...")
        pm.tk_root.destroy()

if __name__ == "__main__":
    main()