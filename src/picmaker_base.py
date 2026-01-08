"""
クリップボード監視, GUI 管理, 画像生成管理を実施するモジュールの基底クラス
"""

from __future__ import annotations

import base64
import copy
import hashlib
import io
import json
import random
import re
import threading
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Generic, List, Mapping, Optional, Protocol, Tuple, TypeVar

import pyperclip
import requests
from PIL import Image

from displayer import Displayer
from picmanager import PicManager, PicStats, SDPngInfo


def json_default(obj: Any) -> str:
    """
    Enum 型を Enum.name() に統一する

    Args:
        obj (Any): オブジェクト

    Raises:
        TypeError: 型違反

    Returns:
        str: Enum.name()
    """
    if isinstance(obj, Enum):
        return obj.name
    raise TypeError(f"{obj.__class__.__name__} is not JSON serializable")


def dump_json(data: Dict, label: str) -> None:
    """
    指定の Dict を json 形式でダンプする

    Args:
        data (Dict): ダンプ対象
        label (str): 表示するラベル("label": {...})
    """
    print(f'"{label}":')
    print(json.dumps(data, ensure_ascii=False, indent=2, default=json_default))


def search_regex(s: str, regex: str, gridx: int = 1) -> str:
    m = re.search(regex, s, flags=re.MULTILINE)
    if not m:
        # print(f'No match with "{regex}".')
        return None
    return m.group(gridx)


@dataclass(frozen=True)
class PMConsts:
    """
    このクラス関連の定数

    """

    # デバッグ用キャラクター名の部分文字列
    charaname_substr_debug: str = "DebuggingPM"


@dataclass
class PMFlags:
    """
    このクラスで用いるフラグ
    """

    # SIGINT が発生したか
    is_task_thread_alive: bool = True


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
    クリップボード監視, GUI 管理, 画像生成管理を実施するクラス
    """

    class TaskBlueprint:
        """
        タスクの設計図\n
        プロンプトの組, 生成キュー用に使用する\n
        インスタンス化した際, その時点のプロンプトを記録中ステータスから生成し, セットする
        """

        def __init__(
            self, picmaker_base: PicMakerBase = None, pos_prompt: str = "", neg_prompt: str = ""
        ):
            """
            コンストラクタ\n
            PicManagerBase が指定されている場合は, 必ず記録中ステータスをもとに生成する\n
            ただしプロンプト生成に十分なステータスでない場合は何もしない\n
            PicManagerBase が指定されておらず, 両プロンプトが指定されている場合は直接初期化する\n
            それ以外は空文字列で初期化する

            Args:
                picmaker_base (PicMakerBase, optional): PicMakerBase インスタンス, Defaults to None.
                pos_prompt (str, optional): ポジティブプロンプト, Defaults to "".
                neg_prompt (str, optional): ネガティブプロンプト, Defaults to "".
            """
            if picmaker_base is not None:
                if not picmaker_base.is_stats_enough_for_prompt():
                    return

                self.pos_prompt = picmaker_base.make_pos_prompt()
                self.neg_prompt = picmaker_base.make_neg_prompt()
            elif (pos_prompt is not None) and (neg_prompt is not None):
                self.pos_prompt = pos_prompt
                self.neg_prompt = neg_prompt
            else:
                self.pos_prompt = ""
                self.neg_prompt = ""

        def __eq__(self, other: PicMakerBase.TaskBlueprint):
            return (
                isinstance(other, PicMakerBase.TaskBlueprint)
                and self.pos_prompt == other.pos_prompt
                and self.neg_prompt == other.neg_prompt
            )

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
        self.flags = PMFlags()

        self.crnt_clipboard = ""
        self.crnt_stats = stats

        self.picmanager = PicManager(self.pics_dir_path())

        self.displayer = Displayer(
            self.picmanager,
            self.run_main,
            self.reserve_task,
            self.on_debug,
            self.on_dump_picmanager,
            self.on_good,
            self.on_bad,
            self.whoami(),
        )

        self.tasks: deque[PicMakerBase.TaskBlueprint] = deque()
        self.crnt_task: PicMakerBase.TaskBlueprint = None

        self.task_thread = threading.Thread(target=self.do_task, args=(), daemon=True)
        self.task_thread.start()

    def finalize(self) -> None:
        """
        終了処理
        """
        if not self.flags.is_task_thread_alive:
            return

        self.flags.is_task_thread_alive = False
        self.task_thread.join()
        self.picmanager.finalize()
        self.displayer.destroy_config_window()

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
        return Path("pics") / Path(self.whoami())

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

    def on_dump_picmanager(self) -> None:
        """
        PicManager ダンプボタンハンドラ
        """
        print(self.picmanager.to_json())

    def on_good(self) -> None:
        """
        GOOD ボタンハンドラ
        """
        return

    def on_bad(self) -> None:
        """
        BAD ボタンハンドラ
        """
        return

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

    def make_json_for_txt2img(self) -> Dict:
        """
        現在の Stable Diffusion 設定から txt2img エンドポイントにポストする json を生成する

        Returns:
            Dict: ポストする json
        """
        api_json = {}
        api_json["prompt"] = self.crnt_task.pos_prompt
        api_json["negative_prompt"] = self.crnt_task.neg_prompt
        api_json["steps"] = self.displayer.sd_steps
        api_json["batch_size"] = self.displayer.sd_batch_size
        api_json["sampler_name"] = "DPM++ 2S a"
        api_json["scheduler"] = "Karras"
        api_json["cfg_scale"] = 7.0
        api_json["seed"] = -1
        api_json["width"] = self.displayer.sd_width
        api_json["height"] = self.displayer.sd_height
        return api_json if api_json["prompt"] and api_json["negative_prompt"] else None

    def post_to_txt2img(self) -> Optional[Tuple[Any, Any]]:
        """
        json を生成し Stable Diffusion txt2img エンドポイントへポストする

        Returns:
            Tuple[Any, Any]: image フィールド, info フィールド, 失敗時は None
        """
        payload = self.make_json_for_txt2img()
        if not payload:
            return None

        # txt2img
        response = requests.post(
            f"http://{self.displayer.srv_ipaddr}:{self.displayer.srv_port}/sdapi/v1/txt2img",
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        body = response.json()
        images = body.get("images", [])
        if not images:
            print("API response without images.")
            return None

        return images, json.loads(body.get("info", "{}"))

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

    def make_dirname_from_info(self, infos: Any, idx: int) -> str:
        """
        info 領域上のデータからディレクトリ名を生成する\n
        info 領域上のデータは同時生成した画像群に関する配列構造のため, インデックスの指定も必要

        Args:
            infos (Any): info 領域上のデータ
            idx (int): 配列のインデックス

        Returns:
            str: ディレクトリ名
        """
        pos_prompts = infos.get("all_prompts", [])
        neg_prompts = infos.get("all_negative_prompts", [])
        return self.make_dirname_from_prompts(pos_prompts[idx], neg_prompts[idx])

    def make_filepath(self, infos: Any, idx: int) -> Path:
        """
        info 領域上のデータからファイルパスを生成する\n
        info 領域上のデータは同時生成した画像群に関する配列構造のため, インデックスの指定も必要\n
        ファイル名は"YYYYMMDDhhmmss-<seed>.png"

        Args:
            infos (Any): info 領域上のデータ
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
                b64 = image_data.split(",", 1)[-1]
                image = Image.open(io.BytesIO(base64.b64decode(b64)))

                pic_path = self.make_filepath(infos, idx)
                if pic_path.parent and not pic_path.parent.exists():
                    # 親ディレクトリが存在しない場合は作成する
                    pic_path.parent.mkdir(parents=True, exist_ok=True)

                image.save(str(pic_path), pnginfo=SDPngInfo(infos, idx))

                if self.displayer.print_images:
                    dump_json(PicStats(pic_path).info.to_dict(), "image")
            except Exception as e:
                print(f"[WARN] Failed to save image idx={idx}: {e}")

        self.picmanager.refresh_piclist()

    def get_crnt_picstats_list(self) -> List[PicStats]:
        """
        記録中ステータスに適合するディレクトリ下の画像群に関する PicStats のリストを取得する

        Returns:
            List[Path]: 画像パス群
        """
        pos_prompt = self.make_pos_prompt()
        neg_prompt = self.make_neg_prompt()
        return self.picmanager.get_picstats_list(
            self.make_dirname_from_prompts(pos_prompt, neg_prompt)
        )

    def refresh_pic(self) -> None:
        """
        表示可能な画像が複数個存在する場合にランダムで表示する\n
        存在しない場合は何もしない
        """
        if not self.get_crnt_picstats_list():
            return

        self.displayer.update_pic(random.choice(self.get_crnt_picstats_list()))

    def reserve_task(self) -> None:
        """
        新しいタスクを生成し, タスクリストに予約する\n
        ただしプロンプト生成に十分なステータスが記録されていない,\n
        すでにリストに存在する, あるいは作業中のタスクの場合は何もしない
        """
        if not self.is_stats_enough_for_prompt():
            return

        new_task = PicMakerBase.TaskBlueprint(self)
        if (new_task in self.tasks) or (new_task == self.crnt_task):
            return

        self.tasks.append(new_task)

    def do_task(self) -> None:
        """
        タスクを実行する, つまり生成 -> 保存をアトミックに繰り返し実行する\n
        タスクが空, すでに実行中タスクが存在する, あるいは生成が失敗した場合はスキップする\n
        例外発生時はループを抜ける
        """
        while self.flags.is_task_thread_alive:
            time.sleep(0.5)
            if (not self.tasks) or (self.crnt_task is not None):
                # ここでは実行中タスクを解除してはいけない
                continue

            try:
                self.crnt_task = self.tasks.popleft()
                result = self.post_to_txt2img()
                if result is None:
                    # 生成失敗
                    print("Failed to post.")
                    continue
                else:
                    images, infos = result
                    self.save_images(images, infos)
            except Exception as e:
                print("Any exception occurred: ", e)
            finally:
                self.crnt_task = None

    def run_oneshot(self) -> None:
        """
        タスク予約とすでに存在する画像の表示を1度だけ行う
        """
        self.reserve_task()
        self.refresh_pic()

    def run_main(self) -> None:
        """
        メイン処理 (ステータス更新 -> 更新がある場合にタスクを予約 -> すでに存在する画像を表示)\n
        Tkinter メインループにて周期的に呼び出される処理
        """
        try:
            is_new_stats = self.refresh_stats()
            if (not is_new_stats) or (not self.is_stats_enough_for_prompt()):
                return

            self.run_oneshot()
        finally:
            self.displayer.endpoint()
            self.displayer.switch_output_button_state(
                self.is_stats_enough_for_prompt() and self.picmanager.crnt_picstats
            )
