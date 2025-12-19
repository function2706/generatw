from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageTk, PngImagePlugin
from tkinter import ttk, Frame
from typing import Any, Dict, Mapping, Optional
import base64, csv, datetime, hashlib, io, json, os, pyperclip, random, requests, threading, tkinter

class _ReadOnly(type):
    def __setattr__(cls, name, value):
        raise AttributeError("read-only class")
    def __delattr__(cls, name):
        raise AttributeError("read-only class")

class Const(metaclass=_ReadOnly):
    INFO_CSV_NAME = "info.csv"

@dataclass
class SDConfigs:
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
    is_verbose: bool = False
    timeout_sec: int = 60

@dataclass
class PMFlags:
    is_new_clipboard: bool = False
    is_new_stats: bool = False
    is_generating: bool = False

def dump_json(data: dict, label: str) -> None:
    print(f"\"{label}\":")
    print(json.dumps(data, ensure_ascii=False, indent=2))

# 基底クラス
class PicMakerBase(ABC):
    @property
    @abstractmethod
    # キャラクタプロンプトテーブル
    def chara_tbl(self) -> Mapping[str, str]:
        raise NotImplementedError

    # コンストラクタ
    def __init__(self, is_verbose: bool):
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

        self.crnt_image_path: Path = None

    # 自身のクラス名を取得する
    def whoami(self) -> str:
        return self.__class__.__name__

    # モードに即したダミーデータをステータスにセットする
    def set_dummy_stats(self) -> None:
        pass

    # デバッグボタンハンドラ
    # ダミーデータをステータスにセットし, 即時ポストする
    def doit_debug(self) -> None:
        self.set_dummy_stats()
        self.doit_oneshot()

    # テキストボックスの作成
    def put_textbox(self, frame :Frame, name: str, row: int, col: int, width: int, default: str) -> ttk.Entry:
        ttk.Label(frame, text=name).grid(row=row, column=col, padx=6, pady=6, sticky="w")
        entry = ttk.Entry(frame, width=width)
        entry.grid(row=row, column=(col + 1), padx=2, pady=6, sticky="w")
        entry.insert(0, default)
        return entry

    # 設定ウィンドウが開かれているか
    def is_config_window_open(self) -> bool:
        return (self.tk_root is not None) and (self.tk_root.winfo_exists())

    # 設定ウィンドウのクローズ時のハンドラ
    def on_config_window_close(self) -> None:
        self.on_image_window_close()
        if self.is_config_window_open():
            self.tk_root.destroy()

    # 画像ウィンドウが開かれているか
    def is_image_window_open(self) -> bool:
        return (self.image_window is not None) and (self.image_window.winfo_exists())

    # 画像ウィンドウのクローズ時のハンドラ
    def on_image_window_close(self) -> None:
        if self.is_image_window_open():
            self.image_window.destroy()
        self.image_window = None

    # GUI の構築
    def construct_config_window(self) -> None:
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
        button = ttk.Button(self.config_button_frame, text="今すぐ生成", command=self.doit_oneshot)
        button.grid(row=0, column=0, padx=6, pady=6, sticky="w")
        # ボタン(デバッグ)
        button = ttk.Button(self.config_button_frame, text="デバッグ", command=self.doit_debug)
        button.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        # フレーム 1
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

    # 画像ウィンドウを構成, ただしすでに開いている場合は最前面に表示するのみ
    def construct_image_window(self) -> None:
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
        button = ttk.Button(self.image_label_frame, text="<", width=2, command=self.on_prev_button)
        button.grid(row=0, column=0, padx=6, pady=6, sticky="nsw")
        # ボタン(>)
        button = ttk.Button(self.image_label_frame, text=">", width=2, command=self.on_next_button)
        button.grid(row=0, column=2, padx=6, pady=6, sticky="nse")
        # 評価フレーム
        self.image_eval_frame.columnconfigure(0, weight=1)
        self.image_eval_frame.columnconfigure(1, weight=1)
        # ボタン(GOOD)
        button = ttk.Button(self.image_eval_frame, text="GOOD", command=self.on_good_button)
        button.grid(row=0, column=0, padx=6, pady=6, sticky="wes")
        # ボタン(BAD)
        button = ttk.Button(self.image_eval_frame, text="BAD", command=self.on_bad_button)
        button.grid(row=0, column=1, padx=6, pady=6, sticky="wes")

    # 画像フレームを指定の画像パスで更新する
    def update_image(self, path: Path) -> None:
        if not path:
            return

        img = Image.open(path)
        tk_img = ImageTk.PhotoImage(img)
        self.construct_image_window()
        self.image_label.configure(image=tk_img)
        self.image_label.image = tk_img

        self.crnt_image_path = path

    # > ボタンハンドラ
    def on_next_button(self) -> None:
        dirname = Path(self.whoami()) / self.get_dirname(self.make_pos_prompt(), self.make_neg_prompt())
        filepaths = self.get_filelist(dirname)
        idx = filepaths.index(Path(self.crnt_image_path.name))
        self.update_image(dirname / filepaths[min(idx + 1, len(filepaths) - 1)])

    # < ボタンハンドラ
    def on_prev_button(self) -> None:
        dirname = Path(self.whoami()) / self.get_dirname(self.make_pos_prompt(), self.make_neg_prompt())
        filepaths = self.get_filelist(dirname)
        idx = filepaths.index(Path(self.crnt_image_path.name))
        self.update_image(dirname / filepaths[max(idx - 1, 0)])

    # GOOD ボタンハンドラ
    def on_good_button(self) -> None:
        return

    # BAD ボタンハンドラ
    def on_bad_button(self) -> None:
        return

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

        if self.crnt_stats == new_stats:
            self.flags.is_new_stats = False
            return

        if self.pm_configs.is_verbose:
            dump_json(new_stats, "new_stats")

        self.flags.is_new_stats = True
        self.crnt_stats = new_stats

    # ステータスがプロンプト生成において十分な情報を有しているか
    def is_stats_enough_for_prompt(self) -> bool:
        pass

    # ステータスからポジティブプロンプトを生成する
    def make_pos_prompt(self) -> str:
        pass

    # ステータスからネガティブプロンプトを生成する
    def make_neg_prompt(self) -> str:
        pass

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

    # プロンプトからハッシュ値(MD5)からなるディレクトリ名を得る
    def get_dirname(self, prompt: str, neg_prompt: str) -> Path:
        dirpath_raw :str = prompt + neg_prompt
        return Path(hashlib.md5(dirpath_raw.encode()).hexdigest())

    # メタデータからディレクトリ名を生成する
    def make_dirname(self, info_obj: Any, idx: int) -> Path:
        prompts = info_obj.get("all_prompts", [])
        neg_prompts = info_obj.get("all_negative_prompts", [])
        return self.get_dirname(prompts[idx], neg_prompts[idx])

    # メタデータやモードからファイルパスを生成する
    def make_filepath(self, info_obj: Any, idx: int) -> Path:
        seeds = info_obj.get("all_seeds", [])

        dirpath = Path(self.whoami()) / self.make_dirname(info_obj, idx)
        now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = Path(f"{now}-{seeds[idx]}.png")
        return dirpath / filename

    # 指定のディレクトリ直下のファイルリストを取得する
    def get_filelist(self, dirname: Path) -> list[Path]:
        files = os.listdir(dirname)
        return [Path(s) for s in files]

    # PNG に付帯するメタデータを生成する
    # (API 応答で得たメタデータは "images" で削ぎ落とした時点でなくなるので, 再度の付与が必要)
    def make_metadata(self, info_obj: Any, idx: int) -> PngImagePlugin.PngInfo:
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text("parameters", info_obj.get("infotexts", [])[idx])
        metadata.add_text("prompt", info_obj.get("all_prompts", [])[idx])
        metadata.add_text("negative_prompt", info_obj.get("all_negative_prompts", [])[idx])
        metadata.add_text("steps", str(info_obj.get("steps", 0)))
        metadata.add_text("sampler", info_obj.get("sampler_name", ""))
        metadata.add_text("schedule_type", info_obj.get("extra_generation_params", {}).get("Schedule type", ""))
        metadata.add_text("cfg_scale", str(info_obj.get("cfg_scale", 0)))
        metadata.add_text("seed", str(info_obj.get("all_seeds", [])[idx]))
        metadata.add_text("width", str(info_obj.get("width", 0)))
        metadata.add_text("height", str(info_obj.get("height", 0)))
        metadata.add_text("sd_model_name", info_obj.get("sd_model_name", ""))
        metadata.add_text("sd_model_hash", info_obj.get("sd_model_hash", ""))
        metadata.add_text("clip_skip", str(info_obj.get("clip_skip", 0)))
        return metadata

    # Image からメタデータを取り出す
    def get_metadata(self, image: Image) -> dict[str, Any]:
        metadata = {}
        metadata["prompt"] = image.info.get("prompt")
        metadata["negative_prompt"] = image.info.get("negative_prompt")
        metadata["steps"] = int(image.info.get("steps"))
        metadata["sampler"] = image.info.get("sampler")
        metadata["schedule_type"] = image.info.get("schedule_type")
        metadata["cfg_scale"] = float(image.info.get("cfg_scale"))
        metadata["seed"] = int(image.info.get("seed"))
        metadata["width"] = int(image.info.get("width"))
        metadata["height"] = int(image.info.get("height"))
        metadata["sd_model_name"] = image.info.get("sd_model_name")
        metadata["sd_model_hash"] = image.info.get("sd_model_hash")
        metadata["clip_skip"] = int(image.info.get("clip_skip"))
        return metadata

    # 記録用 CSV にディレクトリ名とプロンプトを記録する
    # 初回はヘッダーも記述する
    def record_dir_csv(self, info_obj: Any, idx: int) -> None:
        csv_path = Path(self.whoami()) / Path(Const.INFO_CSV_NAME)
        need_header = (not csv_path.exists()) or (csv_path.stat().st_size == 0)
        with open(csv_path, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if need_header:
                writer.writerow(["dirname", "prompt", "negative_prompt"])
            writer.writerow([self.make_dirname(info_obj, idx), info_obj.get("all_prompts", [])[idx], info_obj.get("all_negative_prompts", [])[idx]])

    # 記録用 CSV を list として得る
    def get_dir_csv_list(self) -> list[Any]:
        csv_path = Path(self.whoami()) / Path(Const.INFO_CSV_NAME)
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)

    # 指定の画像群を保存する
    # この際メタデータ(プロンプト, シード)も同時に埋め込む
    # 生成した画像のパス群を返す
    def save_images(self, images: Any, info_obj: Any) -> list[Path]:
        if self.pm_configs.is_verbose:
            dump_json(info_obj, "info_obj")

        image_paths: list[Path] = []
        for idx, image_data in enumerate(images):
            try:
                b64 = image_data.split(",", 1)[-1]
                image = Image.open(io.BytesIO(base64.b64decode(b64)))

                image_path = self.make_filepath(info_obj, idx)
                if image_path.parent and not image_path.parent.exists():
                    # 親ディレクトリが存在しない場合は作成する
                    image_path.parent.mkdir(parents=True, exist_ok=True)
                    self.record_dir_csv(info_obj, idx)

                image.save(str(image_path), pnginfo=self.make_metadata(info_obj, idx))
                image_paths.append(image_path)

                if self.pm_configs.is_verbose:
                    image_v = Image.open(str(image_path))
                    dump_json(self.get_metadata(image_v), "image")
            except Exception as e:
                print(f"[WARN] Failed to save image idx={idx}: {e}")

        return image_paths

    # json を生成し RestAPI でポストする
    # 生成した画像のパス群を返す
    # 生成中の場合は何もしない
    def gen_pic(self) -> list[Path]:
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
            response = requests.post(f"http://{self.sd_configs.ipaddr}:{self.sd_configs.port}/sdapi/v1/txt2img",
                                     json=payload, timeout=self.pm_configs.timeout_sec)
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

    # 生成スレッドエントリポイント
    # 複数個生成した場合はランダムで 1 つ表示する
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
        if not self.is_stats_enough_for_prompt():
            return
        self.make_pic_async()

    # メイン処理 (ステータス更新 -> ワンショット処理)
    def doit(self) -> None:
        try:
            self.refresh_stats()
            if not self.flags.is_new_stats:
                return

            self.doit_oneshot()
        finally:
            self.tk_root.after(500, self.doit)