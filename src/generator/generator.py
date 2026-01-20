"""
ファイル生成クラス
"""

from __future__ import annotations

import base64
import io
import threading
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Generic, Protocol, TypeVar

from PIL import Image

from common.classes import PicStats, SDPngInfo, TaskBlueprint
from common.functions import dirname_by_prompts, dump_json
from common.interfaces import MasterIF


class HasCommonMembers(Protocol):
    """
    Generic な Stats が 共通メンバを持つことを伝えるためのクラス
    """

    # var: int <- ここで共通メンバ変数の存在を通告することもできる

    def refresh(self) -> None: ...
    def todict(self) -> dict[str, Any]: ...


@dataclass
class Event:
    """
    イベントフラグ
    """

    shutdown = threading.Event()  # 終了予定
    interrupt = threading.Event()  # 中断処理実行予定


ProgressResp = TypeVar("ProgressResp", bound=HasCommonMembers)


class Generator(ABC, Generic[ProgressResp]):
    """
    ファイル生成クラス\n
    タスク設計図をもとにサーバへ非同期にポストし, ファイル保存をする
    """

    def __init__(self, master: MasterIF):
        """
        コンストラクタ

        Args:
            master (MasterIF): Master インターフェース
        """
        self.master = master

        self.event = Event()

        self.tasks: deque[TaskBlueprint] = deque()
        self.crnt_task: TaskBlueprint = None

        self.progress: ProgressResp = None

        self.task_thread = threading.Thread(target=self.task_thread_main, args=(), daemon=True)

    def whoami(self) -> str:
        """
        自身のバックエンド名を取得する

        Returns:
            str: バックエンド名
        """
        return self.__class__.__name__.replace("Generator", "")

    def start(self) -> None:
        """
        スレッドを開始する
        """
        self.task_thread.start()

    def join(self) -> None:
        """
        スレッドの join を行う\n
        すでに死んでいる場合は何もしない
        """
        if not self.task_thread.is_alive():
            return

        self.task_thread.join()

    def finalize(self) -> None:
        """
        終了処理\n
        タスクの破棄, 及び txt2img へリクエスト中の場合は interrupt ポストを行う\n
        リクエスト中かどうかは(post_interrupt() が)現在タスクの有無で判断
        """
        self.event.shutdown.set()
        self.tasks.clear()
        self.request_interrupt()

    def reserve(
        self, pos: str, neg: str, stps: int, b_size: int, w: int, h: int, d_addr: str, d_port: str
    ):
        """
        新しいタスクを生成し, タスクリストに予約する\n
        すでにリストに存在する, あるいは作業中のタスクの場合は何もしない

        Args:
            pos (str): ポジティブプロンプト
            neg (str): ネガティブプロンプト
            stps (int): ステップ数
            b_size (int): バッチサイズ
            w (int): 幅
            h (int): 高さ
            d_addr (str): 宛先アドレス
            d_port (str): 宛先ポート
        """
        new_task = TaskBlueprint.make(pos, neg, stps, b_size, w, h, d_addr, d_port)
        if (new_task in self.tasks) or (new_task == self.crnt_task):
            return

        self.tasks.append(new_task)

    def clear(self) -> None:
        """
        タスクリストを空にする
        """
        self.tasks.clear()

    def len_tasks(self) -> int:
        """
        現在のタスクと残りタスクの合計数を算出する

        Returns:
            int: 合計数
        """
        nexts = len(self.tasks)
        return nexts if self.crnt_task is None else nexts + 1

    def reserve_interrupt(self) -> None:
        """
        中断処理を予約する
        """
        self.event.interrupt.set()

    def reserve_progress(self) -> None:
        """
        進捗要求を予約する
        """
        self.event.interrupt.set()

    @abstractmethod
    def request_generate(self) -> tuple[Any, Any] | None:
        """
        現在のタスクをもとに生成要求を行う\n
        現在のタスクが空の場合は何もしない

        Returns:
            tuple[Any, Any]: image フィールドと info フィールドのタプル, 失敗時は None
        """
        pass

    @abstractmethod
    def request_upscale(self) -> None:
        """
        現在のタスクをもとにアップスケール要求を行う\n
        現在のタスクが空の場合は何もしない

        Returns:
            tuple[Any, Any]: image フィールドと info フィールドのタプル, 失敗時は None
        """
        pass

    @abstractmethod
    def request_interrupt(self) -> None:
        """
        中断要求を行う\n
        現在のタスクが空の場合は何もしない
        """
        pass

    @abstractmethod
    def request_progress(self) -> ProgressResp:
        """
        現在のタスクの進捗報告要求を行う\n
        現在のタスクが空の場合は何もしない
        """
        pass

    @property
    @abstractmethod
    def crnt_progress(self) -> float:
        """
        現在のタスクの進捗度

        Returns:
            float: 現在のタスクの進捗度
        """
        pass

    def make_filepath(self, infos: dict, idx: int) -> Path:
        """
        info 領域上のデータからファイルパスを生成する\n
        info 領域上のデータは同時生成した画像群に関する配列構造のため, インデックスの指定も必要\n
        ファイル名は"YYYYMMDDhhmmss-<seed>.png"

        Args:
            infos (dict): info 領域上のデータ
            idx (int): 配列のインデックス

        Returns:
            Path: ファイルパス
        """
        pos_prompts = infos.get("all_prompts", [])
        neg_prompts = infos.get("all_negative_prompts", [])
        seeds = infos.get("all_seeds", [])

        dirpath = self.master.pics_dir_path / Path(
            dirname_by_prompts(pos_prompts[idx], neg_prompts[idx])
        )
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

        if self.master.crnt_gui_configs.print_picinfo:
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

                if self.master.crnt_gui_configs.print_images:
                    dump_json(PicStats.make(pic_path).info.todict(), "image")
            except Exception as e:
                print(f"[WARN] Failed to save image idx={idx}: {e}")

        self.master.refresh_piclist()

    def task_thread_main(self) -> None:
        """
        タスクを実行する, つまり生成 -> 保存をアトミックに繰り返し実行する\n
        タスクが空, すでに実行中タスクが存在する, あるいは生成が失敗した場合はスキップする
        """
        while not self.event.shutdown.is_set():
            time.sleep(0.2)
            if self.event.interrupt.is_set():
                # 中断要求はキュー上のタスクよりも優先度が高い処理
                # 同期処理なので中断処理中にここを複数回通ることはない
                self.request_interrupt()

            # 進捗は必ず確認
            self.progress = self.request_progress()

            if not self.tasks or self.crnt_task is not None:
                # 残りタスクが空か実行中タスクがない
                # ここでは実行中タスクを解除してはいけない
                continue

            try:
                self.crnt_task = self.tasks.popleft()

                result = self.request_generate()
                if result is None:
                    # 生成失敗
                    print("Failed to post, API response without images.")
                    continue
                else:
                    images, infos = result
                    self.save_images(images, infos)
            except Exception as e:
                print("Any exception occurred: ", e)
            finally:
                self.crnt_task = None
                self.event.interrupt.clear()
