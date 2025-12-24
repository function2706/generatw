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
import tkinter
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import Frame, TclError, ttk
from typing import Any, Dict, List, Mapping, Optional

import pyperclip
import requests
from PIL import Image, ImageTk, PngImagePlugin

from picmanager import PicManager, PicStats


@dataclass
class SDConfigs:
    """
    Stable Diffusion API 関連の設定一覧
    """

    ipaddr: Optional[str] = "127.0.0.1"
    port: Optional[int] = 7860
    steps: Optional[int] = 30
    batch_size: Optional[int] = 4
    sampler_name: Optional[str] = "DPM++ 2S a"
    scheduler: Optional[str] = "Karras"
    cfg_scale: Optional[float] = 7.0
    seed: Optional[int] = -1
    width: Optional[int] = 540
    height: Optional[int] = 960


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
        self.sd_configs = SDConfigs()
        self.flags = PMFlags()

        self.crnt_clipboard = ""
        self.crnt_stats = {}

        # 設定ウィンドウ
        self.tk_root = tkinter.Tk()
        self.construct_config_window()
        self.image_window = None

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
        self.update_image(self.picmanager.crnt_picstats)

    def doit_debug(self) -> None:
        """
        デバッグボタンハンドラ\n
        ダミーデータをステータスにセットし, 即時ポストする
        """
        self.set_dummy_stats()
        self.doit_oneshot()

    def put_textbox(
        self, frame: Frame, name: str, row: int, col: int, width: int, default: str
    ) -> ttk.Entry:
        """
        テキストボックスの作成\n
        本オブジェクトは column 2つ分を占めることに注意

        Args:
            frame (Frame): 挿入先フレーム
            name (str): ラベル
            row (int): フレーム内の row
            col (int): フレーム内の column
            width (int): 長さ
            default (str): デフォルト値

        Returns:
            ttk.Entry: オブジェクトインスタンス
        """
        ttk.Label(frame, text=name).grid(row=row, column=col, padx=6, pady=6, sticky="w")
        entry = ttk.Entry(frame, width=width)
        entry.grid(row=row, column=(col + 1), padx=2, pady=6, sticky="w")
        entry.insert(0, default)
        return entry

    def is_config_window_open(self) -> bool:
        """
        設定ウィンドウが開かれているか

        Returns:
            bool: True: 開かれている, False: 開かれていない or TclError 例外発生
        """
        if self.tk_root is None:
            return False
        try:
            return bool(self.tk_root.winfo_exists())
        except TclError:
            return False

    def on_config_window_close(self) -> None:
        """
        設定ウィンドウのクローズ時のハンドラ
        """
        self.on_image_window_close()
        if self.is_config_window_open():
            self.tk_root.destroy()

    def is_image_window_open(self) -> bool:
        """
        画像ウィンドウが開かれているか

        Returns:
            bool: True: 開かれている, False: 開かれていない or TclError 例外発生
        """
        if self.image_window is None:
            return False
        try:
            return bool(self.image_window.winfo_exists())
        except TclError:
            return False

    def on_image_window_close(self) -> None:
        """
        画像ウィンドウのクローズ時のハンドラ
        """
        if self.is_image_window_open():
            self.image_window.destroy()
        self.image_window = None

    def construct_config_window(self) -> None:
        """
        GUI の構築
        """
        # ウィンドウ定義
        self.tk_root.protocol("WM_DELETE_WINDOW", self.on_config_window_close)
        self.tk_root.title("設定")
        self.tk_root.columnconfigure(0, weight=1)
        self.tk_root.rowconfigure(0, weight=1)
        # フレーム定義
        self.config_main_frame = ttk.Frame(self.tk_root, padding=12)
        self.config_main_frame.grid(row=0, column=0, sticky="nsew")
        self.config_button_frame = ttk.Frame(self.config_main_frame)
        self.config_button_frame.grid(row=0, column=0, sticky="w")
        self.config_param1_frame = ttk.Frame(self.config_main_frame)
        self.config_param1_frame.grid(row=1, column=0, sticky="w")
        self.config_param2_frame = ttk.Frame(self.config_main_frame)
        self.config_param2_frame.grid(row=2, column=0, sticky="w")
        # ボタン用フレーム
        # ボタン(今すぐ生成)
        self.button_gen = ttk.Button(
            self.config_button_frame, text="今すぐ生成", command=self.doit_oneshot
        )
        self.button_gen.grid(row=0, column=0, padx=6, pady=6, sticky="w")
        # ボタン(画像を表示)
        self.button_output = ttk.Button(
            self.config_button_frame, text="画像を表示", command=self.on_output
        )
        self.button_output.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        # ボタン(デバッグ)
        self.button_debug = ttk.Button(
            self.config_button_frame, text="デバッグ", command=self.doit_debug
        )
        self.button_debug.grid(row=0, column=2, padx=6, pady=6, sticky="w")
        # フレーム 1
        # テキストボックス(幅)
        self.entry_width = self.put_textbox(
            self.config_param1_frame, "幅", 1, 0, 5, str(self.sd_configs.width)
        )
        # テキストボックス(高さ)
        self.entry_height = self.put_textbox(
            self.config_param1_frame, "高さ", 1, 2, 5, str(self.sd_configs.height)
        )
        # テキストボックス(ステップ数)
        self.entry_steps = self.put_textbox(
            self.config_param1_frame, "Steps", 2, 0, 4, str(self.sd_configs.steps)
        )
        # テキストボックス(生成数)
        self.entry_batch_size = self.put_textbox(
            self.config_param1_frame, "生成数", 2, 2, 4, str(self.sd_configs.batch_size)
        )
        # フレーム 2
        # テキストボックス(IPアドレス)
        self.entry_ipaddr = self.put_textbox(
            self.config_param2_frame, "IPアドレス", 0, 0, 16, str(self.sd_configs.ipaddr)
        )
        # テキストボックス(ポート)
        self.entry_port = self.put_textbox(
            self.config_param2_frame, "ポート", 0, 2, 6, str(self.sd_configs.port)
        )

    def construct_image_window(self) -> None:
        """
        画像ウィンドウを構成, ただしすでに開いている場合は最前面に表示するのみ
        """
        if self.is_image_window_open():
            self.image_window.deiconify()
            self.image_window.lift()
            return

        self.image_window = tkinter.Toplevel(self.tk_root)
        self.image_window.title("画像")
        self.image_window.protocol("WM_DELETE_WINDOW", self.on_image_window_close)
        # フレーム定義
        self.image_main_frame = ttk.Frame(self.image_window, padding=5)
        self.image_main_frame.grid(row=0, column=0, sticky="nsew")
        self.image_label_frame = ttk.Frame(self.image_main_frame)
        self.image_label_frame.grid(row=0, column=0, sticky="nwe")
        self.image_eval_frame = ttk.Frame(self.image_main_frame)
        self.image_eval_frame.grid(row=1, column=0, sticky="swe")
        # 画像フレーム
        # ラベル
        self.image_label = ttk.Label(self.image_label_frame)
        self.image_label.grid(row=0, column=1, padx=6, pady=6, sticky="nswe")
        # ボタン(<)
        self.button_prev = ttk.Button(
            self.image_label_frame, text="<", width=2, command=self.on_prev_button
        )
        self.button_prev.grid(row=0, column=0, padx=6, pady=6, sticky="nsw")
        # ボタン(>)
        self.button_next = ttk.Button(
            self.image_label_frame, text=">", width=2, command=self.on_next_button
        )
        self.button_next.grid(row=0, column=2, padx=6, pady=6, sticky="nse")
        # 評価フレーム
        self.image_eval_frame.columnconfigure(0, weight=1)
        self.image_eval_frame.columnconfigure(1, weight=1)
        # ボタン(GOOD)
        self.button_good = ttk.Button(
            self.image_eval_frame, text="GOOD", command=self.on_good_button
        )
        self.button_good.grid(row=0, column=0, padx=6, pady=6, sticky="wes")
        # ボタン(BAD)
        self.button_bad = ttk.Button(self.image_eval_frame, text="BAD", command=self.on_bad_button)
        self.button_bad.grid(row=0, column=1, padx=6, pady=6, sticky="wes")

    def update_image(self, picstats: PicStats) -> None:
        """
        画像フレームを指定の PicStats で更新する\n
        picstats が None の場合は何もしない

        Args:
            picstats (PicStats): 更新予定の PicStats
        """
        if not picstats:
            return

        image = Image.open(picstats.path)
        tk_img = ImageTk.PhotoImage(image)
        self.construct_image_window()
        self.image_label.configure(image=tk_img)
        self.image_label.image = tk_img

        self.picmanager.crnt_picstats = picstats
        if self.is_config_window_open():
            self.button_output.configure(state="normal")

    def on_next_button(self) -> None:
        """
        > ボタンハンドラ
        """
        self.update_image(self.picmanager.next_picstats())

    def on_prev_button(self) -> None:
        """
        < ボタンハンドラ
        """
        self.update_image(self.picmanager.prev_picstats())

    def on_good_button(self) -> None:
        """
        GOOD ボタンハンドラ
        """
        return

    def on_bad_button(self) -> None:
        """
        BAD ボタンハンドラ
        """
        return

    def refresh_sd_configs(self) -> None:
        """
        GUI から SD コンフィグを更新する
        """
        self.sd_configs.ipaddr = self.entry_ipaddr.get()
        self.sd_configs.port = self.entry_port.get()
        self.sd_configs.steps = int(self.entry_steps.get())
        self.sd_configs.batch_size = int(self.entry_batch_size.get())
        self.sd_configs.sampler_name = "DPM++ 2S a"
        self.sd_configs.scheduler = "Karras"
        self.sd_configs.cfg_scale = 7.0
        self.sd_configs.seed = -1
        self.sd_configs.width = int(self.entry_width.get())
        self.sd_configs.height = int(self.entry_height.get())

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

    def make_dirname_from_info(self, info_obj: Any, idx: int) -> str:
        """
        info 領域上のデータからディレクトリ名を生成する\n
        info 領域上のデータは同時生成した画像群に関する配列構造のため, インデックスの指定も必要

        Args:
            info_obj (Any): info 領域上のデータ
            idx (int): 配列のインデックス

        Returns:
            str: ディレクトリ名
        """
        pos_prompts = info_obj.get("all_prompts", [])
        neg_prompts = info_obj.get("all_negative_prompts", [])
        return self.make_dirname_from_prompts(pos_prompts[idx], neg_prompts[idx])

    def make_filepath(self, info_obj: Any, idx: int) -> Path:
        """
        info 領域上のデータからファイルパスを生成する\n
        info 領域上のデータは同時生成した画像群に関する配列構造のため, インデックスの指定も必要\n
        ファイル名は"YYYYMMDDhhmmss-<seed>.png"

        Args:
            info_obj (Any): info 領域上のデータ
            idx (int): 配列のインデックス

        Returns:
            Path: ファイルパス
        """
        seeds = info_obj.get("all_seeds", [])

        dirpath = self.pics_dir_path() / Path(self.make_dirname_from_info(info_obj, idx))
        now = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = Path(f"{now}-{seeds[idx]}.png")
        return dirpath / filename

    def make_metadata(self, info_obj: Any, idx: int) -> PngImagePlugin.PngInfo:
        """
        PNG に付与する PNG Info を生成する\n
        info 領域上のデータは "images" で削ぎ落とした時点でなくなるので, 再度の付与を行う\n
        info 領域上のデータは同時生成した画像群に関する配列構造のため, インデックスの指定も必要

        Args:
            info_obj (Any): info 領域上のデータ
            idx (int): 配列のインデックス

        Returns:
            PngImagePlugin.PngInfo: PNG Info
        """
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text("prompt", info_obj.get("all_prompts", [])[idx])
        metadata.add_text("negative_prompt", info_obj.get("all_negative_prompts", [])[idx])
        metadata.add_text("steps", str(info_obj.get("steps", 0)))
        metadata.add_text("sampler", info_obj.get("sampler_name", ""))
        metadata.add_text(
            "schedule_type",
            info_obj.get("extra_generation_params", {}).get("Schedule type", ""),
        )
        metadata.add_text("cfg_scale", str(info_obj.get("cfg_scale", 0)))
        metadata.add_text("seed", str(info_obj.get("all_seeds", [])[idx]))
        metadata.add_text("width", str(info_obj.get("width", 0)))
        metadata.add_text("height", str(info_obj.get("height", 0)))
        metadata.add_text("sd_model_name", info_obj.get("sd_model_name", ""))
        metadata.add_text("sd_model_hash", info_obj.get("sd_model_hash", ""))
        metadata.add_text("clip_skip", str(info_obj.get("clip_skip", 0)))
        metadata.add_text("parameters", info_obj.get("infotexts", [])[idx])
        return metadata

    def save_images(self, images: Any, info_obj: Any) -> List[Path]:
        """
        指定の画像群を保存する\n
        各画像には次回起動時にメタデータの再取得ができるよう, info 領域上のデータが埋め込まれる

        Args:
            images (Any): 画像群データ
            info_obj (Any): info 領域上のデータ

        Returns:
            List[Path]: 生成した画像のパス群
        """
        if self.pm_configs.is_verbose:
            dump_json(info_obj, "info_obj")

        pic_paths: List[Path] = []
        for idx, image_data in enumerate(images):
            try:
                b64 = image_data.split(",", 1)[-1]
                image = Image.open(io.BytesIO(base64.b64decode(b64)))

                pic_path = self.make_filepath(info_obj, idx)
                if pic_path.parent and not pic_path.parent.exists():
                    # 親ディレクトリが存在しない場合は作成する
                    pic_path.parent.mkdir(parents=True, exist_ok=True)

                image.save(str(pic_path), pnginfo=self.make_metadata(info_obj, idx))
                pic_paths.append(pic_path)

                if self.pm_configs.is_verbose:
                    dump_json(PicStats(pic_path).info.to_dict(), "image")
            except Exception as e:
                print(f"[WARN] Failed to save image idx={idx}: {e}")

        self.picmanager.refresh_piclist()
        return pic_paths

    def make_json_for_txt2img(self) -> Dict:
        """
        現在の Stable Diffusion 設定から txt2img エンドポイントにポストする json を生成する

        Returns:
            Dict: ポストする json
        """
        api_json = {}
        api_json["prompt"] = self.make_pos_prompt()
        api_json["negative_prompt"] = self.make_neg_prompt()
        api_json["steps"] = self.sd_configs.steps
        api_json["batch_size"] = self.sd_configs.batch_size
        api_json["sampler_name"] = self.sd_configs.sampler_name
        api_json["scheduler"] = self.sd_configs.scheduler
        api_json["cfg_scale"] = self.sd_configs.cfg_scale
        api_json["seed"] = self.sd_configs.seed
        api_json["width"] = self.sd_configs.width
        api_json["height"] = self.sd_configs.height
        return api_json if api_json["prompt"] and api_json["negative_prompt"] else None

    def gen_pic(self) -> List[Path]:
        """
        json を生成し Stable Diffusion txt2img エンドポイントへポストする\n

        Returns:
            List[Path]: 生成した画像のパス群
        """
        try:
            self.flags.is_generating = True
            self.refresh_sd_configs()
            payload = self.make_json_for_txt2img()
            if not payload:
                return []

            # txt2img
            response = requests.post(
                f"http://{self.sd_configs.ipaddr}:{self.sd_configs.port}/sdapi/v1/txt2img",
                json=payload,
                timeout=self.pm_configs.timeout_sec,
            )
            response.raise_for_status()
            body = response.json()
            images = body.get("images", [])
            if not images:
                print("API response without images.")
                return []

            return self.save_images(images, json.loads(body.get("info", "{}")))
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
        return []

    def get_pic_list(self) -> List[Path]:
        """
        記録中ステータスに適合するディレクトリ下の画像パス群を取得する

        Returns:
            List[Path]: 画像パス群
        """
        pos_prompt = self.make_pos_prompt()
        neg_prompt = self.make_neg_prompt()
        picstat_list = self.picmanager.get_picstats_list(
            Path(self.make_dirname_from_prompts(pos_prompt, neg_prompt))
        )
        return [ps.path for ps in picstat_list]

    @abstractmethod
    def should_gen_pic(self) -> bool:
        """
        画像生成を実施すべきか

        Returns:
            bool: True: 生成すべき, False: 生成すべきでない
        """
        pass

    def make_pic_async(self) -> None:
        """
        画像生成スレッドエントリポイント\n
        生成から表示までを実施する(複数個生成した場合はランダムで 1 つ表示)\n
        生成すべきでないと判断した場合はすでに生成した画像を表示する\n
        生成に失敗した場合は何もしない
        """

        def worker():
            crnt_pic_paths = self.get_pic_list()
            # 生成すべき or 画像が無いなら生成する
            need_generate = self.should_gen_pic() or not crnt_pic_paths
            new_pic_paths = self.gen_pic() if need_generate else []
            # 生成が必要だったのに失敗した場合は中断
            if need_generate and not new_pic_paths:
                return
            # ここまで来たら new_pic_paths は [] か Path のリスト
            self.update_image(PicStats(random.choice(crnt_pic_paths + new_pic_paths)))

        threading.Thread(target=worker, args=(), daemon=True).start()

    def sigint_handler(self, sig, frame) -> None:
        """
        SIGINT ハンドラ

        Args:
            sig (_type_): シグナル
            frame (_type_): Tkinter フレーム
        """
        self.tk_root.destroy()

    def doit_oneshot(self) -> None:
        """
        ワンショット処理 (ステータス確認 -> 非同期で生成 -> tkinter 更新)\n
        記録中ステータスをもとに即座に生成する
        """
        if not self.is_stats_enough_for_prompt():
            return
        self.make_pic_async()

    def doit(self) -> None:
        """
        メイン処理 (ステータス更新 -> ワンショット処理)\n
        Tkinter メインループにて周期的に呼び出される処理
        """
        try:
            if not self.is_stats_enough_for_prompt() and self.is_config_window_open():
                self.button_output.configure(state="disabled")

            self.refresh_stats()
            if not self.flags.is_new_stats:
                return

            self.doit_oneshot()
        finally:
            self.tk_root.after(500, self.doit)
