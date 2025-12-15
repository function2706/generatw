from pic_maker import TWPicMaker
import signal

# エントリポイント
def main():
    try:
        pm = TWPicMaker()
        signal.signal(signal.SIGINT, pm.sigint_handler)

        # Tkinterのイベントループ開始
        pm.tk_root.after(100, pm.doit)  # 監視を開始
        pm.tk_root.mainloop()
    except KeyboardInterrupt:
        print("\n終了します。")
        pm.tk_root.destroy()

if __name__ == "__main__":
    main()