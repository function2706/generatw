"""
クリップボード監視, GUI 管理, 画像生成管理を実施するモジュールの基底クラス
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import random
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

import pyperclip
import requests
from PIL import Image

from displayer import Displayer, SDConfigs
from picmanager import PicManager, PicStats, SDPngInfo


@dataclass
class PMConfigs:
    """
    このクラス関連の設定一覧
    """

    is_verbose: bool = False
    timeout_sec: int = 60


@dataclass
class PMFlags:
    """
    このクラスで用いるフラグ
    """

    # クリップボードの更新があったか
    is_new_clipboard: bool = False
    # ステータスデータの更新があったか
    is_new_stats: bool = False
    # 画像生成中か
    is_generating: bool = False


def dump_json(data: Dict, label: str) -> None:
    """
    指定の Dict を json 形式でダンプする

    Args:
        data (Dict): ダンプ対象
        label (str): 表示するラベル("label": {...})
    """
    print(f'"{label}":')
    print(json.dumps(data, ensure_ascii=False, indent=2))


class PicMakerBase(ABC):
    """
    クリップボード監視, GUI 管理, 画像生成管理を実施するクラス
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

    def __init__(self, is_verbose: bool):
        """
        コンストラクタ\n

        Args:
            is_verbose (bool): 冗長的表示を行うか
        """
        self.flags = PMFlags()

        self.crnt_clipboard = ""
        self.crnt_stats = {}

        self.displayer = Displayer(
            self.doit,
            self.doit,
            self.doit_oneshot,
            self.on_output,
            self.on_debug,
            self.on_next,
            self.on_prev,
            self.on_good,
            self.on_bad,
        )

        self.pm_configs = PMConfigs()
        self.pm_configs.is_verbose = is_verbose

        self.picmanager = PicManager(self.pics_dir_path())

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
    def set_dummy_stats(self) -> None:
        """
        ダミーデータをステータスにセットする(デバッグ用)\n
        データはモードに即して定義される
        """
        pass

    def on_output(self) -> None:
        """
        表示ボタンハンドラ\n
        表示すべき画像がないときは何もしない
        """
        self.update_pic(self.picmanager.crnt_picstats)

    def on_debug(self) -> None:
        """
        デバッグボタンハンドラ\n
        ダミーデータをステータスにセットし, 即時ポストする
        """
        self.set_dummy_stats()
        self.doit_oneshot()

    def update_pic(self, picstats: PicStats) -> None:
        """
        画像フレームを指定の PicStats で更新する\n
        picstats が None の場合は何もしない

        Args:
            picstats (PicStats): 更新予定の PicStats
        """
        if not picstats:
            return

        self.displayer.popup_with(picstats.path)

        self.picmanager.crnt_picstats = picstats
        self.displayer.switch_output_button_state(True)

    def on_next(self) -> None:
        """
        > ボタンハンドラ
        """
        self.update_pic(self.picmanager.next_picstats())

    def on_prev(self) -> None:
        """
        < ボタンハンドラ
        """
        self.update_pic(self.picmanager.prev_picstats())

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

    def reflesh_clipboard(self) -> None:
        """
        クリップボードを監視し, 記録中文字列と異なる場合に記録する\n
        同時にフラグの更新も行う
        """
        try:
            new_clipboard = pyperclip.paste()
        except Exception as e:
            self.flags.is_new_clipboard = False
            print("An exception occur for watching clipboard.", e)
            return

        if self.crnt_clipboard == new_clipboard:
            self.flags.is_new_clipboard = False
            return

        if self.pm_configs.is_verbose:
            print("new_clipboard:")
            print(new_clipboard)

        self.flags.is_new_clipboard = True
        self.crnt_clipboard = new_clipboard

    @abstractmethod
    def parse_clipboard(self) -> Dict[str, Any]:
        """
        クリップボード文字列をもとに各ステータスを取得する

        Returns:
            Dict[str, Any]: ステータス
        """
        pass

    def refresh_stats(self) -> None:
        """
        記録中クリップボード文字列をもとにステータスを更新する\n
        同時に記録中ステータスと一致するかを示すフラグの管理も行う
        """
        self.reflesh_clipboard()
        if not self.flags.is_new_clipboard:
            self.flags.is_new_stats = False
            return

        new_stats = self.parse_clipboard()

        if self.crnt_stats == new_stats:
            self.flags.is_new_stats = False
            return

        if self.pm_configs.is_verbose:
            dump_json(new_stats, "new_stats")

        self.flags.is_new_stats = True
        self.crnt_stats = new_stats

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

    def make_json_for_txt2img(self, sd_configs: SDConfigs) -> Dict:
        """
        現在の Stable Diffusion 設定から txt2img エンドポイントにポストする json を生成する

        Returns:
            Dict: ポストする json
        """
        api_json = {}
        api_json["prompt"] = self.make_pos_prompt()
        api_json["negative_prompt"] = self.make_neg_prompt()
        api_json["steps"] = sd_configs.steps
        api_json["batch_size"] = sd_configs.batch_size
        api_json["sampler_name"] = sd_configs.sampler_name
        api_json["scheduler"] = sd_configs.scheduler
        api_json["cfg_scale"] = sd_configs.cfg_scale
        api_json["seed"] = sd_configs.seed
        api_json["width"] = sd_configs.width
        api_json["height"] = sd_configs.height
        return api_json if api_json["prompt"] and api_json["negative_prompt"] else None

    def post_to_txt2img(self) -> Optional[Tuple[Any, Any]]:
        """
        json を生成し Stable Diffusion txt2img エンドポイントへポストする

        Returns:
            Tuple[Any, Any]: image フィールド, info フィールド, 失敗時は None
        """
        try:
            self.flags.is_generating = True
            sd_configs = self.displayer.get_sd_configs()
            payload = self.make_json_for_txt2img(sd_configs)
            if not payload:
                return None

            # txt2img
            response = requests.post(
                f"http://{sd_configs.ipaddr}:{sd_configs.port}/sdapi/v1/txt2img",
                json=payload,
                timeout=self.pm_configs.timeout_sec,
            )
            response.raise_for_status()
            body = response.json()
            images = body.get("images", [])
            if not images:
                print("API response without images.")
                return None

            return images, json.loads(body.get("info", "{}"))
        except requests.exceptions.Timeout:
            print("API timeout.")
        except requests.exceptions.RequestException as e:
            print("API Failed to request:", e)
        except (ValueError, KeyError, IndexError) as e:
            print("Failed to generate image:", e)
        except Exception as e:
            print("Another error occurs about image:", e)
        finally:
            self.flags.is_generating = False
        return None

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

        if self.pm_configs.is_verbose:
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

                if self.pm_configs.is_verbose:
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

    @abstractmethod
    def should_gen_pic(self) -> bool:
        """
        画像生成を実施すべきか

        Returns:
            bool: True: 生成すべき, False: 生成すべきでない
        """
        pass

    def refresh_pic_main(self) -> None:
        """
        画像の更新, 生成から表示までを実施する\n
        生成すべきでないと判断した場合は, すでに生成した画像が存在するならそれを表示する\n
        存在しない場合は生成を実施する\n
        表示可能な画像が複数個存在する場合はランダムで決定する\n
        生成に失敗した場合は何もしない
        """
        if self.should_gen_pic() or not self.get_crnt_picstats_list():
            # 生成すべき or 画像が無いなら生成する
            result = self.post_to_txt2img()
            if result is None:
                # 生成失敗
                return
            else:
                images, infos = result
            self.save_images(images, infos)
        output_picstats = random.choice(self.get_crnt_picstats_list())
        self.update_pic(output_picstats)

    def sigint_handler(self, sig, frame) -> None:
        """
        SIGINT ハンドラ

        Args:
            sig (_type_): シグナル
            frame (_type_): Tkinter フレーム
        """
        self.displayer.destroy_config_window()

    def doit_oneshot(self) -> None:
        """
        ワンショット処理 (ステータス確認 -> 非同期で生成 -> 表示更新)\n
        記録中ステータスをもとに即座に生成する
        """
        if not self.is_stats_enough_for_prompt():
            return
        threading.Thread(target=self.refresh_pic_main, args=(), daemon=True).start()

    def doit(self) -> None:
        """
        メイン処理 (ステータス更新 -> ワンショット処理)\n
        Tkinter メインループにて周期的に呼び出される処理
        """
        try:
            if not self.is_stats_enough_for_prompt():
                self.displayer.switch_output_button_state(False)

            self.refresh_stats()
            if not self.flags.is_new_stats:
                return

            self.doit_oneshot()
        finally:
            self.displayer.endpoint()
