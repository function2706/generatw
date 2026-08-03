"""
共用クラス
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path


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
    sd_scaleby: float = 0.0
    each_max_pics: int = 0
    backend: str = ""
    # 選択中キャラクター ID (yamls/characters/<id>.yaml の character キー)
    crnt_character: str | None = None
    # 終了時に内部状態を保存する
    save_state_end: bool = True
    # 開始時 / キャラ選択時に保存状態を復元する
    load_state_start: bool = True
    # 画像メタデータをコンソールへ出力する
    print_picinfo: bool = False
    # 構築したプロンプト文字列をコンソールへ出力する
    print_prompt: bool = False
    # モジュール間イベントをコンソールへ出力する
    print_event: bool = False

    @classmethod
    def fromjson(cls, path: Path) -> GUIConfigs:
        """
        JSON から設定を読み込む\n
        未知キー (旧スキーマの残骸など) は無視し, 欠落キーは既定値で補う

        Args:
            path (Path): JSON パス

        Returns:
            GUIConfigs: 設定
        """
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in raw.items() if k in known})

    def tojson(self, path: Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)
