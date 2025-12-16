from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional
from PIL import Image, ImageTk
import base64, io, json, pyperclip, requests, sys, tkinter, time

@dataclass
class SDConfigs:
    url: Optional[str] = "http://127.0.0.1:7860"
    steps: Optional[int] = 20
    sampler_name: Optional[str] = "DPM++ 2S a"
    scheduler: Optional[str] = "Karras"
    cfg_scale: Optional[float] = 7.0
    seed: Optional[int] = -1
    width: Optional[int] = 512
    height: Optional[int] = 512

@dataclass
class PMConfigs:
    do_post: bool = False
    is_verbose: bool = False
    timeout_sec: int = 60

@dataclass
class PMFlags:
    is_new_clipboard: bool = False
    is_new_stats: bool = False
    is_generating: bool = False

# 基底クラス
class PicMaker(ABC):
    @property
    @abstractmethod
    # キャラクタプロンプトテーブル
    def chara_tbl(self) -> Mapping[str, str]:
        raise NotImplementedError

    # コンストラクタ
    def __init__(self, title: str, do_post: bool, is_verbose: bool):
        self.crnt_clipboard = ""
        self.crnt_stats = {}

        self.tk_root = tkinter.Tk()
        self.tk_root.title(title)
        self.tk_label = tkinter.Label(self.tk_root)
        self.tk_label.pack()

        self.sd_configs = SDConfigs()
        self.flags = PMFlags()

        self.pm_configs = PMConfigs()
        self.pm_configs.do_post = do_post
        self.pm_configs.is_verbose = is_verbose

    # クリップボードから文字列を得る
    # 前回文字列と同様かどうかも記録する
    def reflesh_clipboard(self) -> None:
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

    # クリップボード文字列をもとに各ステータスを取得する
    def parse_clipboard(self) -> Dict[str, Any]:
        pass

    # ステータスを更新する
    # 前回のクリップボード文字列から変化がない場合は何もしない
    def refresh_stats(self) -> None:
        self.reflesh_clipboard()
        if not self.flags.is_new_clipboard:
            self.flags.is_new_stats = False
            return

        new_stats = self.parse_clipboard()

        if self.pm_configs.is_verbose:
            print("new_stats:", json.dumps(new_stats, ensure_ascii=False, indent=2))

        if self.crnt_stats == new_stats:
            self.flags.is_new_stats = False
            return

        self.flags.is_new_stats = True
        self.crnt_stats = new_stats

    # ステータスをダンプする
    def print_stats(self) -> None:
        print("crnt_stats:", json.dumps(self.crnt_stats, ensure_ascii=False, indent=2))

    # ステータスがプロンプト生成において十分な情報を有しているか
    def is_stats_enough_for_prompt(self) -> bool:
        pass

    # ステータスからポジティブプロンプトを生成する
    def make_pos_prompt(self) -> str:
        pass

    # ステータスからネガティブプロンプトを生成する
    def make_neg_prompt(self) -> str:
        pass

    # TKinter を指定の画像パスで更新する
    def update_image(self, path: str) -> None:
        if not path:
            return

        img = Image.open(path)
        tk_img = ImageTk.PhotoImage(img)
        self.tk_label.configure(image=tk_img)
        self.tk_label.image = tk_img

    # ステータス等をもとに画像のパスを生成する
    def gen_image_path(self) -> str:
        pass

    # json を生成し RestAPI でポストする
    # 生成した画像のパスを返す
    # 生成中の場合は何もしない
    def gen_pic(self) -> str:
        if self.flags.is_generating:
            print("In generating, Busy!")
            return ""

        try:
            self.flags.is_generating = True
            json = {}
            json["prompt"] = self.make_pos_prompt()
            json["negative_prompt"] = self.make_neg_prompt()
            json["steps"] = self.sd_configs.steps
            json["sampler_name"] = self.sd_configs.sampler_name
            json["scheduler"] = self.sd_configs.scheduler
            json["cfg_scale"] = self.sd_configs.cfg_scale
            json["seed"] = self.sd_configs.seed
            json["width"] = self.sd_configs.width
            json["height"] = self.sd_configs.height

            if (not json["prompt"]) or (not json["negative_prompt"]):
                # プロンプトが空の場合はポストしない
                return ""

            # txt2img
            response = requests.post(f"{self.sd_configs.url}/sdapi/v1/txt2img", json=json, timeout=self.pm_configs.timeout_sec)
            response.raise_for_status()
            body = response.json()
            images = body.get("images")
            if not images:
                print("API response without images.")
                return ""
            image_data = images[0]

            # 画像保存
            image = Image.open(io.BytesIO(base64.b64decode(image_data)))
            image_path = self.gen_image_path()
            image.save(image_path)
            return image_path
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
        return ""

    # SIGINT ハンドラ
    def sigint_handler(self, sig, frame) -> None:
        self.tk_root.destroy()
        sys.exit(0)

    # メイン処理
    def doit(self) -> None:
        try:
            self.refresh_stats()
            if not self.flags.is_new_stats:
                return

            self.print_stats()
            if not self.is_stats_enough_for_prompt():
                return

            if self.pm_configs.do_post:
                self.update_image(self.gen_pic())
            else:
                print("Will post!")
        finally:
            self.tk_root.after(500, self.doit)