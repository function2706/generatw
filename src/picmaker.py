"""
メインスクリプト
"""

import signal

from master.master import Master

if __name__ == "__main__":
    master = Master()
    signal.signal(signal.SIGINT, master.sigint_handler)
    master.start()
    master.finalize()
    print("Exit...")
