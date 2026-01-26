"""
クリップボード監視, ステータス記録クラス
"""

from __future__ import annotations

import copy
import random
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, Mapping, Protocol, TypeVar

import pyperclip

from common.classes import PMConsts
from common.functions import dirname_by_prompts, dump_json
from common.interfaces import MasterIF


class HasCommonMembers(Protocol):
    """
    Generic な Stats が 共通メンバを持つことを伝えるためのクラス
    """

    # var: int <- ここで共通メンバ変数の存在を通告することもできる

    def refresh(self) -> None: ...
    def todict(self) -> dict[str, Any]: ...


Stats = TypeVar("Stats", bound=HasCommonMembers)


class Parser(ABC, Generic[Stats]):
    """
    クリップボード監視, ステータス記録クラス
    """

    @property
    @abstractmethod
    def chara_tbl(self) -> Mapping[str, str]:
        """
        キャラクタプロンプトテーブル\n
        キャラクタ名と対応するプロンプトの定義

        Returns:
            Mapping[str, str]: テーブル
        """
        raise NotImplementedError

    def __init__(self, master: MasterIF, stats: Stats):
        """
        コンストラクタ

        Args:
            master (MasterIF): Master インターフェース
        """
        self.master = master

        self.crnt_clipboard = ""
        self.crnt_stats = stats

    def whoami(self) -> str:
        """
        自身のフロントエンド名を取得する

        Returns:
            str: フロントエンド名
        """
        return self.__class__.__name__.replace("Parser", "")

    def pics_dir_path(self) -> Path:
        """
        画像ディレクトリパスを取得する\n
        (pics/<クラス名>)

        Returns:
            Path: ディレクトリパス
        """
        return Path(PMConsts.pichome_dir) / Path(self.whoami())

    @abstractmethod
    def make_dummy_stats(self, name: str = None) -> Stats:
        """
        ダミーステータスを生成する(デバッグ用)\n
        データはモードに即して定義される

        Args:
            name (str, optional): name フィールドに代入する文字列, None でない場合はこの値で初期化

        Returns:
            Stats: ダミーステータス
        """
        pass

    def ready_for_debug(self) -> bool:
        """
        クリップボードの編集が許可されている場合はダミークリップボードを設定する\n
        そうでない場合はダミーステータスのみを編集し, メイン処理に委ねる

        Returns:
            bool: メイン処理の反映が必要なら True, そうでない場合は False
        """
        if self.master.crnt_gui_configs.allow_edit_clipboard:
            pyperclip.copy(PMConsts.charaname_substr_debug + str(random.randint(1, 8)))
            return False

        new_stats = self.make_dummy_stats()
        if new_stats is None or new_stats == self.crnt_stats:
            return False

        self.crnt_stats = new_stats
        if self.master.crnt_gui_configs.print_new_stats:
            dump_json(self.crnt_stats.todict(), "new_stats(debug)")

        return True

    def refresh_clipboard(self) -> bool:
        """
        クリップボードを監視し, 記録中文字列と異なる場合に記録する

        Returns:
            bool: 更新があった場合は True, なかった場合は False
        """
        try:
            new_clipboard = pyperclip.paste()
        except Exception as e:
            print("An exception occur for watching clipboard.", e)
            return False

        if self.crnt_clipboard == new_clipboard:
            return False

        if self.master.crnt_gui_configs.print_new_clipboard:
            print("new_clipboard:")
            print(new_clipboard)

        self.crnt_clipboard = new_clipboard
        return True

    def parse_clipboard(self) -> Stats:
        """
        クリップボード文字列をもとに各ステータスを取得する

        Returns:
            Stats: 新たなステータス
        """
        if PMConsts.charaname_substr_debug in self.crnt_clipboard:
            return self.make_dummy_stats(name=self.crnt_clipboard)

        new_stats = copy.deepcopy(self.crnt_stats)
        new_stats.refresh(self.crnt_clipboard)
        return new_stats

    def refresh_stats(self) -> bool:
        """
        記録中クリップボード文字列をもとにステータスを更新する\n
        前回のステータスと同じかどうかの判断も行う

        Returns:
            bool: True: ステータス更新あり, False: 更新なし
        """
        has_refreshed = self.refresh_clipboard()
        if not has_refreshed:
            return False

        new_stats = self.parse_clipboard()
        if new_stats is None or new_stats == self.crnt_stats:
            return False

        self.crnt_stats = new_stats
        if self.master.crnt_gui_configs.print_new_stats:
            dump_json(self.crnt_stats.todict(), "new_stats")
        return True

    @abstractmethod
    def is_stats_enough_for_prompt(self) -> bool:
        """
        記録中ステータスがプロンプト生成に際し十分な情報を有しているか

        Returns:
            bool: True: 有している, False: 有していない
        """
        pass

    @abstractmethod
    def make_pos_prompt(self) -> str:
        """
        記録中ステータスからポジティブプロンプトを生成する

        Returns:
            str: プロンプト
        """
        pass

    @abstractmethod
    def make_neg_prompt(self) -> str:
        """
        記録中ステータスからネガティブプロンプトを生成する

        Returns:
            str: プロンプト
        """
        pass

    def get_crnt_picstats_dir(self) -> str:
        """
        記録中ステータスに適合するディレクトリ名を返す

        Returns:
            str: ディレクトリ名
        """
        return dirname_by_prompts(self.make_pos_prompt(), self.make_neg_prompt())
