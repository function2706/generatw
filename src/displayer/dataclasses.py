"""
共用クラス
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GUIConfigs:
    """
    Displayer 外で参照する設定フォーマット
    """

    srv_ipaddr: str = ""
    srv_port: str = ""
    sd_steps: int = 0
    sd_batch_size: int = 0
    sd_width: int = 0
    sd_height: int = 0
    allow_edit_clipboard: bool = False
    print_new_clipboard: bool = False
    print_new_stats: bool = False
    print_picinfo: bool = False

    @classmethod
    def make(
        cls,
        srv_ipaddr: str,
        srv_port: str,
        sd_steps: int,
        sd_batch_size: int,
        sd_width: int,
        sd_height: int,
        allow_edit_clipboard: bool,
        print_new_clipboard: bool,
        print_new_stats: bool,
        print_picinfo: bool,
    ):
        """
        コンストラクタ

        Args:
            srv_ipaddr (str): ポスト先 IP アドレス
            srv_port (str): ポスト先ポート
            sd_steps (int): ステップ数
            sd_batch_size (int): バッチサイズ
            sd_width (int): 幅
            sd_height (int): 高さ
            allow_edit_clipboard (bool): デバッグ時にクリップボード更新を認めるか
            print_new_clipboard (bool): クリップボードの更新があった場合にログ出力するか
            print_new_stats (bool): ステータスの更新があった場合にログ出力するか
            print_picinfo (bool): 応答 image の PicInfo をログ出力するか
        """
        return cls(
            srv_ipaddr=srv_ipaddr,
            srv_port=srv_port,
            sd_steps=sd_steps,
            sd_batch_size=sd_batch_size,
            sd_width=sd_width,
            sd_height=sd_height,
            allow_edit_clipboard=allow_edit_clipboard,
            print_new_clipboard=print_new_clipboard,
            print_new_stats=print_new_stats,
            print_picinfo=print_picinfo,
        )
