from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from PIL import Image, ImageTk
from tkinter import ttk, Frame
from typing import Any, Dict, Mapping, Optional, Union
import base64, hashlib, io, json, pyperclip, random, requests, threading, tkinter

@dataclass
class SDConfigs:
    ipaddr: Optional[str] = "127.0.0.1"
    port: Optional[int] = 7860
    steps: Optional[int] = 20
    batch_size: Optional[int] = 4
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

def dump_json(data: dict, label: str) -> None:
    print(f"{label}:", json.dumps(data, ensure_ascii=False, indent=2))

# 基底クラス
class PicMaker(ABC):
    @property
    @abstractmethod
    # キャラクタプロンプトテーブル
    def chara_tbl(self) -> Mapping[str, str]:
        raise NotImplementedError

    # コンストラクタ
    def __init__(self, do_post: bool, is_verbose: bool):
        self.sd_configs = SDConfigs()
        self.flags = PMFlags()

        self.crnt_clipboard = ""
        self.crnt_stats = {}

        # 設定ウィンドウ
        self.tk_root = tkinter.Tk()
        self.construct_config_window()
        self.image_window = None

        self.pm_configs = PMConfigs()
        self.pm_configs.do_post = do_post
        self.pm_configs.is_verbose = is_verbose

    # 自身のクラス名を取得する
    def whoami(self) -> str:
        pass

    # テキストボックスの作成
    def put_textbox(self, frame :Frame, name: str, row: int, col: int, width: int, default: str) -> ttk.Entry:
        ttk.Label(frame, text=name).grid(row=row, column=col, padx=6, pady=6, sticky="w")
        entry = ttk.Entry(frame, width=width)
        entry.grid(row=row, column=(col + 1), padx=2, pady=6, sticky="w")
        entry.insert(0, default)
        return entry

    # GUI の構築
    def construct_config_window(self) -> None:
        # ウィンドウ定義
        self.tk_root.protocol("WM_DELETE_WINDOW", self.on_config_window_close)
        self.tk_root.title("設定")
        self.tk_root.columnconfigure(0, weight=1)
        self.tk_root.rowconfigure(0, weight=1)
        # フレーム定義
        self.main_frame = ttk.Frame(self.tk_root, padding=12)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.config_button_frame = ttk.Frame(self.main_frame)
        self.config_button_frame.grid(row=0, column=0, sticky="w")
        self.config_param1_frame = ttk.Frame(self.main_frame)
        self.config_param1_frame.grid(row=1, column=0, sticky="w")
        self.config_param2_frame = ttk.Frame(self.main_frame)
        self.config_param2_frame.grid(row=2, column=0, sticky="w")
        # フレーム 1
        # ボタン(今すぐ生成)
        button = ttk.Button(self.config_button_frame, text="今すぐ生成", command=self.doit_oneshot)
        button.grid(row=0, column=0, padx=6, pady=6, sticky="w")
        # テキストボックス(幅)
        self.entry_width = self.put_textbox(self.config_param1_frame, "幅", 1, 0, 5, str(self.sd_configs.width))
        # テキストボックス(高さ)
        self.entry_height = self.put_textbox(self.config_param1_frame, "高さ", 1, 2, 5, str(self.sd_configs.height))
        # テキストボックス(ステップ数)
        self.entry_steps = self.put_textbox(self.config_param1_frame, "Steps", 2, 0, 4, str(self.sd_configs.steps))
        # テキストボックス(生成数)
        self.entry_batch_size = self.put_textbox(self.config_param1_frame, "生成数", 2, 2, 4, str(self.sd_configs.batch_size))
        # フレーム 2
        # テキストボックス(IPアドレス)
        self.entry_ipaddr = self.put_textbox(self.config_param2_frame, "IPアドレス", 0, 0, 16, str(self.sd_configs.ipaddr))
        # テキストボックス(ポート)
        self.entry_port = self.put_textbox(self.config_param2_frame, "ポート", 0, 2, 6, str(self.sd_configs.port))

    # 設定ウィンドウが開かれているか
    def is_config_window_open(self):
        return (self.tk_root is not None) and (self.tk_root.winfo_exists())

    # 画像ウィンドウのクローズ時のハンドラ
    def on_config_window_close(self) -> None:
        self.on_image_window_close()
        if self.is_config_window_open():
            self.tk_root.destroy()

    # 画像ウィンドウが開かれているか
    def is_image_window_open(self):
        return (self.image_window is not None) and (self.image_window.winfo_exists())

    # 画像ウィンドウのクローズ時のハンドラ
    def on_image_window_close(self) -> None:
        if self.is_image_window_open():
            self.image_window.destroy()
        self.image_window = None

    # 画像ウィンドウを構成, ただしすでに開いている場合は最前面に表示するのみ
    def construct_image_window(self) -> None:
        if self.is_image_window_open():
            self.image_window.deiconify()
            self.image_window.lift()
            return

        self.image_window = tkinter.Toplevel(self.tk_root)
        self.image_window.title("画像")
        self.image_window.protocol("WM_DELETE_WINDOW", self.on_image_window_close)
        image_frame = ttk.Frame(self.image_window, padding=5)
        image_frame.grid(row=0, column=0, sticky="nsew")
        self.image_label = ttk.Label(image_frame)
        self.image_label.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")

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
        dump_json(self.crnt_stats, "crnt_stats")

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
        self.construct_image_window()
        self.image_label.configure(image=tk_img)
        self.image_label.image = tk_img

    # ステータス等をもとに画像のパスを生成する
    def gen_image_path(self) -> str:
        pass

    # GUI から SD コンフィグを更新する
    def refresh_sd_configs(self) -> None:
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

    # 現在の SD 設定から RestAPI で txt2img にポストする json を生成する
    def make_json_for_txt2img(self) -> dict:
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

    # 画像を保存する
    # 親ディレクトリが存在しない場合は作成する
    def save_image_safely(self, img: Image.Image, path: Union[str, Path]) -> None:
        dest = Path(path)
        if dest.parent and not dest.parent.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(dest))

    # 指定の画像群を保存する
    # 生成した画像のパス群を返す
    def save_images(self, images: Any, info_obj: Any) -> list[str]:
        image_paths = []
        prompts = info_obj.get("all_prompts", [])
        neg_prompts = info_obj.get("all_negative_prompts", [])
        seeds = info_obj.get("all_seeds", [])
        for idx, image_data in enumerate(images):
            try:
                dir_raw :str = prompts[idx] + neg_prompts[idx]
                dir = self.whoami() + "/" + hashlib.md5(dir_raw.encode()).hexdigest()
                filename_raw :str = prompts[idx] + neg_prompts[idx] + str(seeds[idx])
                filename = hashlib.md5(filename_raw.encode()).hexdigest()

                b64 = image_data.split(",", 1)[-1]
                image = Image.open(io.BytesIO(base64.b64decode(b64)))
                image_path = dir + "/" + filename + ".png"
                self.save_image_safely(image, image_path)
                image_paths.append(image_path)
            except Exception as e:
                print(f"[WARN] Failed to save image idx={idx}: {e}")

        return image_paths

    # json を生成し RestAPI でポストする
    # 生成した画像のパス群を返す
    # 生成中の場合は何もしない
    def gen_pic(self) -> list[str]:
        if self.flags.is_generating:
            print("In generating, Busy!")
            return []
        try:
            self.flags.is_generating = True
            self.refresh_sd_configs()
            payload = self.make_json_for_txt2img()
            if not payload:
                # プロンプトが空の場合はポストしない
                return []

            # txt2img
            response = requests.post(f"http://{self.sd_configs.ipaddr}:{self.sd_configs.port}/sdapi/v1/txt2img", json=payload, timeout=self.pm_configs.timeout_sec)
            response.raise_for_status()
            body = response.json()
            images = body.get("images", [])
            if not images:
                print("API response without images.")
                return []

            info_obj = json.loads(body.get("info", "{}"))
            return self.save_images(images, info_obj)
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

    # 生成スレッドエントリポイント
    def make_pic_async(self) -> None:
        def worker():
            image_paths = self.gen_pic()
            self.update_image(random.choice(image_paths))
        threading.Thread(target=worker, args=(), daemon=True).start()

    # SIGINT ハンドラ
    def sigint_handler(self, sig, frame) -> None:
        self.tk_root.destroy()

    # ワンショット処理 (ステータス表示 -> ステータス型式確認 -> 非同期で生成, tkinter 更新)
    def doit_oneshot(self) -> None:
        self.print_stats()
        if not self.is_stats_enough_for_prompt():
            return
        if self.pm_configs.do_post:
            self.make_pic_async()
        else:
            print("Will post!")

    # メイン処理 (ステータス更新 -> ワンショット処理)
    def doit(self) -> None:
        try:
            self.refresh_stats()
            if not self.flags.is_new_stats:
                return

            self.doit_oneshot()
        finally:
            self.tk_root.after(500, self.doit)