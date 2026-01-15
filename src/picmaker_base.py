"""
クリップボード監視, GUI 管理, 画像生成管理を実施するモジュールの基底クラス
"""

from __future__ import annotations

import base64
import copy
import hashlib
import io
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generic, Mapping, Protocol, TypeVar

import pyperclip
from PIL import Image

from displayer import Displayer
from functions import dump_json
from picmanager import PicManager, PicStats, SDPngInfo
from taskmanager import TaskManager


@dataclass(frozen=True)
class PMConsts:
    """
    このクラス関連の定数
    """

    # 画像保存先ディレクトリ
    pichome_dir: str = "pics"
    # デバッグ用キャラクター名の部分文字列
    charaname_substr_debug: str = "DebuggingPM"


class HasCommonMembers(Protocol):
    """
    Generic な Stats が 共通メンバを持つことを伝えるためのクラス
    """

    # var: int <- ここで共通メンバ変数の存在を通告することもできる

    def refresh(self) -> None: ...
    def todict(self) -> Dict[str, Any]: ...


Stats = TypeVar("Stats", bound=HasCommonMembers)


class PicMakerBase(ABC, Generic[Stats]):
    """
    クリップボード監視, GUI 管理, 画像生成管理を実施するクラス\n
    このクラス自体はクリップボード監視とファイル操作, ロギングを直接行う(対 OS 処理に限定)
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

    def __init__(self, stats: Stats):
        """
        コンストラクタ

        Args:
            stats (Stats): ステータスインスタンス
        """

        self.crnt_clipboard = ""
        self.crnt_stats = stats

        self.picmanager = PicManager.make(self.pics_dir_path())
        self.taskmanager = TaskManager(self.save_images)
        self.displayer = Displayer(
            picmanager=self.picmanager,
            taskmanager=self.taskmanager,
            on_edgepoint=self.run_main,
            on_append=self.reserve_task,
            on_debug=self.on_debug,
            ownername=self.whoami(),
        )
        self.taskmanager.start()

    def finalize(self) -> None:
        """
        終了処理
        """

        self.taskmanager.finalize()
        self.displayer.finalize()

    def sigint_handler(self, sig, frame) -> None:
        """
        SIGINT ハンドラ

        Args:
            sig (_type_): シグナル
            frame (_type_): Tkinter フレーム
        """
        self.finalize()

    def whoami(self) -> str:
        """
        自身のクラス名を取得する

        Returns:
            str: クラス名
        """
        return self.__class__.__name__

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

    def on_debug(self) -> None:
        """
        デバッグボタンハンドラ\n
        ダミークリップボードを設定する
        """
        if self.displayer.allow_edit_clipboard:
            pyperclip.copy(PMConsts.charaname_substr_debug + str(random.randint(1, 8)))
        else:
            new_stats = self.make_dummy_stats()
            if new_stats is None or new_stats == self.crnt_stats:
                return False

            self.crnt_stats = new_stats
            if self.displayer.print_new_stats:
                dump_json(self.crnt_stats.todict(), "new_stats(debug)")
            self.run_oneshot()

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

        if self.displayer.print_new_clipboard:
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
            return self.make_dummy_stats()

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
        if self.displayer.print_new_stats:
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

    def make_dirname_from_prompts(self, pos_prompt: str, neg_prompt: str) -> str:
        """
        プロンプトからディレクトリ名を生成する\n
        ディレクトリ名は MD5 (32byte Ascii) として得られる

        Args:
            pos_prompt (str): ポジティブプロンプト
            neg_prompt (str): ネガティブプロンプト

        Returns:
            str: ディレクトリ名
        """
        dirpath_raw: str = pos_prompt + neg_prompt
        return hashlib.md5(dirpath_raw.encode()).hexdigest()

    def make_dirname_from_info(self, infos: Dict, idx: int) -> str:
        """
        info 領域上のデータからディレクトリ名を生成する\n
        info 領域上のデータは同時生成した画像群に関する配列構造のため, インデックスの指定も必要

        Args:
            infos (Dict): info 領域上のデータ
            idx (int): 配列のインデックス

        Returns:
            str: ディレクトリ名
        """
        pos_prompts = infos.get("all_prompts", [])
        neg_prompts = infos.get("all_negative_prompts", [])
        return self.make_dirname_from_prompts(pos_prompts[idx], neg_prompts[idx])

    def make_filepath(self, infos: Dict, idx: int) -> Path:
        """
        info 領域上のデータからファイルパスを生成する\n
        info 領域上のデータは同時生成した画像群に関する配列構造のため, インデックスの指定も必要\n
        ファイル名は"YYYYMMDDhhmmss-<seed>.png"

        Args:
            infos (Dict): info 領域上のデータ
            idx (int): 配列のインデックス

        Returns:
            Path: ファイルパス
        """
        seeds = infos.get("all_seeds", [])

        dirpath = self.pics_dir_path() / Path(self.make_dirname_from_info(infos, idx))
        now = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = Path(f"{now}-{seeds[idx]}.png")
        return dirpath / filename

    def save_images(self, images: Any, infos: Any) -> None:
        """
        指定の画像群を保存する\n
        各画像には次回起動時にメタデータの再取得ができるよう, info 領域上のデータが埋め込まれる\n
        保存が正常に完了した場合は画像リストの更新が行われる\n
        images か infos が None の場合は何もしない

        Args:
            images (Any): 画像群データ
            infos (Any): info 領域上のデータ
        """
        if not images or not infos:
            return

        if self.displayer.print_picinfo:
            dump_json(infos, "infos")

        for idx, image_data in enumerate(images):
            try:
                image_data = str(image_data)
                b64 = image_data.split(",", 1)[-1]
                image = Image.open(io.BytesIO(base64.b64decode(b64)))

                pic_path = self.make_filepath(infos, idx)
                if pic_path.parent and not pic_path.parent.exists():
                    # 親ディレクトリが存在しない場合は作成する
                    pic_path.parent.mkdir(parents=True, exist_ok=True)

                image.save(str(pic_path), pnginfo=SDPngInfo(infos, idx))

                if self.displayer.print_images:
                    dump_json(PicStats.make(pic_path).info.todict(), "image")
            except Exception as e:
                print(f"[WARN] Failed to save image idx={idx}: {e}")

        self.picmanager.refresh_piclist()

    def get_crnt_picstats_dir(self) -> str:
        """
        記録中ステータスに適合するディレクトリ名を返す

        Returns:
            str: ディレクトリ名
        """
        pos_prompt = self.make_pos_prompt()
        neg_prompt = self.make_neg_prompt()
        return self.make_dirname_from_prompts(pos_prompt, neg_prompt)

    def reserve_task(self) -> None:
        """
        新しいタスクを生成し, タスクリストに予約する\n
        ただしプロンプト生成に十分なステータスが記録されていない,\n
        すでにリストに存在する, あるいは作業中のタスクの場合は何もしない
        """
        if not self.is_stats_enough_for_prompt():
            return

        self.taskmanager.reserve(
            pos=self.make_pos_prompt(),
            neg=self.make_neg_prompt(),
            stps=self.displayer.sd_steps,
            b_size=self.displayer.sd_batch_size,
            w=self.displayer.sd_width,
            h=self.displayer.sd_height,
            d_addr=self.displayer.srv_ipaddr,
            d_port=self.displayer.srv_port,
        )

    def refresh_pic_randomly(self) -> None:
        """
        現在の PicStats 表示可能な画像が存在する場合にランダムで表示する\n
        存在しない場合は NO IMAGE を表示する
        """
        piclist = self.picmanager.get_picstats_list(self.get_crnt_picstats_dir())
        if not piclist:
            # 記録中ステータスに紐づくディレクトリ内に画像がない
            self.displayer.put_no_image_placeholder()
            return

        self.picmanager.warp_picstats(self.get_crnt_picstats_dir())
        self.displayer.update_pic_window(self.picmanager.crnt_picstats)

    def run_oneshot(self) -> None:
        """
        タスク予約とすでに存在する画像の表示を1度だけ行う
        """
        self.reserve_task()
        self.refresh_pic_randomly()

    def run_main(self) -> None:
        """
        メイン処理 (ステータス更新 -> 更新がある場合にタスクを予約 -> すでに存在する画像を表示)\n
        Tkinter メインループにて周期的に呼び出される処理
        """
        try:
            is_new_stats = self.refresh_stats()
            if not is_new_stats:
                return
            elif not self.is_stats_enough_for_prompt():
                # 記録中ステータスが生成に不十分 i.e. ステータスに紐づくディレクトリがない
                self.displayer.put_no_image_placeholder()
                return

            self.run_oneshot()
        finally:
            self.displayer.endpoint()
