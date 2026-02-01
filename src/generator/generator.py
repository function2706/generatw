"""
ファイル生成クラス
"""

from __future__ import annotations

import threading
import time
from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Generic, Protocol, TypeVar

from PIL import ImageFile

from archiver.dataclasses import PicInfo
from common.functions import dirname_by_prompts, dump_json
from common.interfaces import MasterIF
from common.multideque import multideque
from generator.dataclasses import (
    SamplerName,
    SchedulerName,
    TaskBlueprintImg2Img,
    TaskBlueprintTxt2Img,
)


@dataclass(frozen=True)
class Consts:
    thread_interval_sec = 0.2


class HasCommonMembers(Protocol):
    """
    Generic な Stats が 共通メンバを持つことを伝えるためのクラス
    """

    progress: float

    def todict(self) -> dict[str, Any]: ...


@dataclass
class Event:
    """
    イベントフラグ
    """

    shutdown: threading.Event = field(default_factory=threading.Event)  # 終了予定
    interrupt: threading.Event = field(default_factory=threading.Event)  # 中断処理実行予定


TaskProgress = TypeVar("TaskProgress", bound=HasCommonMembers)


class Generator(ABC, Generic[TaskProgress]):
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

        self.tasks: multideque[TaskBlueprintTxt2Img, TaskBlueprintImg2Img] = multideque(
            TaskBlueprintTxt2Img, TaskBlueprintImg2Img
        )
        self.tasks_lock = Lock()
        self.crnt_task: TaskBlueprintTxt2Img | TaskBlueprintImg2Img = None
        self.crnt_task_lock = Lock()

        self.progress: TaskProgress = None
        self.progress_lock = Lock()

        self.worker_thread = threading.Thread(
            target=self.worker, args=(), daemon=True, name="worker"
        )
        self.instructor_thread = threading.Thread(
            target=self.instructor, args=(), daemon=True, name="instructor"
        )
        self.observer_thread = threading.Thread(
            target=self.observer, args=(), daemon=True, name="observer"
        )

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
        self.instructor_thread.start()
        self.observer_thread.start()
        self.worker_thread.start()

    def join(self) -> None:
        """
        スレッドの join を行う\n
        すでに死んでいる場合は何もしない
        """
        if not self.worker_thread.is_alive():
            return

        self.worker_thread.join()
        self.observer_thread.join()
        self.instructor_thread.join()

    def finalize(self) -> None:
        """
        終了処理\n
        タスクの破棄, 及び txt2img へリクエスト中の場合は interrupt ポストを行う\n
        リクエスト中かどうかは(post_interrupt() が)現在タスクの有無で判断
        """
        self.event.shutdown.set()
        self.clear()
        self.request_interrupt()

    def reserve_txt2img(
        self,
        pos: str,
        neg: str,
        seed: int,
        stps: int,
        b_size: int,
        smplr: SamplerName,
        schdlr: SchedulerName,
        cfg: float,
        w: int,
        h: int,
        d_addr: str,
        d_port: str,
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
        new_task: TaskBlueprintTxt2Img = TaskBlueprintTxt2Img.make(
            b_end=self.master.backend_type,
            pos=pos,
            neg=neg,
            seed=seed,
            stps=stps,
            b_size=b_size,
            smplr=smplr,
            schdlr=schdlr,
            cfg=cfg,
            w=w,
            h=h,
            d_addr=d_addr,
            d_port=d_port,
        )
        with self.tasks_lock:
            with self.crnt_task_lock:
                if (new_task in self.tasks) or (new_task == self.crnt_task):
                    return
                self.tasks.push(new_task)

    def clear(self) -> None:
        """
        タスクリストを空にする
        """
        with self.tasks_lock:
            self.tasks.clear()

    def len_tasks(self) -> int:
        """
        現在のタスクと残りタスクの合計数を算出する

        Returns:
            int: 合計数
        """
        with self.tasks_lock:
            with self.crnt_task_lock:
                nexts = len(self.tasks)
                return nexts if self.crnt_task is None else nexts + 1

    def is_crnt_task_none(self) -> bool:
        """
        現在のタスクが存在するか

        Returns:
            bool: True: 存在する(実行中), False: 存在しない
        """
        with self.crnt_task_lock:
            return self.crnt_task is None

    def crnt_taskdict(self) -> dict[str, Any]:
        """
        現在のタスクの dict を取得する

        Returns:
            dict[str, Any]: 現在のタスクの dict
        """
        with self.crnt_task_lock:
            return self.crnt_task.todict() if self.crnt_task is not None else {}

    def crnt_tasklist(self) -> list[dict[str, Any]]:
        """
        現在のタスクリストを取得する

        Returns:
            list[dict[str, Any]]: 現在のタスクリスト
        """
        with self.tasks_lock:
            return [task.todict() for task in self.tasks]

    def reserve_interrupt(self) -> None:
        """
        中断処理を予約する
        """
        self.event.interrupt.set()

    @abstractmethod
    def request_generate(self) -> list[tuple[ImageFile.ImageFile, PicInfo]]:
        """
        現在のタスクをもとに生成要求を行う\n
        現在のタスクが空の場合は何もしない\n
        失敗時に空リストを返す

        Returns:
            list[tuple[ImageFile.ImageFile, PicInfo]]: ImageFile, PicInfo のタプルリスト
        """
        pass

    @abstractmethod
    def request_upscale(self) -> list[tuple[ImageFile.ImageFile, PicInfo]]:
        """
        現在のタスクをもとにアップスケール要求を行う\n
        現在のタスクが空の場合は何もしない

        Returns:
            list[tuple[ImageFile.ImageFile, PicInfo]]: ImageFile, PicInfo のタプルリスト
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
    def request_progress(self) -> TaskProgress:
        """
        現在のタスクの進捗報告要求を行う\n
        現在のタスクが空の場合は何もしない
        """
        pass

    @property
    def crnt_progress(self) -> float:
        """
        現在のタスクの進捗度

        Returns:
            float: 現在のタスクの進捗度
        """
        with self.progress_lock:
            return self.progress.progress if self.progress is not None else 0

    @property
    def crnt_dst(self) -> str:
        """
        現在のタスクの宛先

        Returns:
            str: 現在のタスクの宛先
        """
        with self.crnt_task_lock:
            return (
                self.crnt_task.dst_addr + ":" + self.crnt_task.dst_port
                if self.crnt_task is not None
                else ""
            )

    @property
    def crnt_task_copy(self) -> TaskBlueprintTxt2Img | TaskBlueprintImg2Img | None:
        """
        現在のタスクのコピーを渡す\n
        現在のタスクは外部からの書き換えを認めない

        Returns:
            TaskBlueprint: タスクのコピー
        """
        with self.crnt_task_lock:
            return deepcopy(self.crnt_task)

    def make_filepath(self, picinfo: PicInfo, idx: int) -> Path:
        """
        PicInfoからファイルパスを生成する\n
        ファイル名は"YYYYMMDDhhmmss-<seed>.png"

        Args:
            picinfo (PicInfo): PicInfo
            idx (int): 同バッチ内インデックス(同ファイル名による上書き防止のため)

        Returns:
            Path: ファイルパス
        """
        pos_prompt = picinfo.positive_prompt
        neg_prompt = picinfo.negative_prompt
        seed = picinfo.seed

        dirpath = self.master.pics_dir_path / Path(dirname_by_prompts(pos_prompt, neg_prompt))
        now = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = Path(f"{now}-{seed}-{idx}.png")
        return dirpath / filename

    def save_images(self, imglist: list[tuple[ImageFile.ImageFile, PicInfo]]) -> None:
        """
        指定の画像群を保存する\n
        各画像には次回起動時にメタデータの再取得ができるよう, info 領域上のデータが埋め込まれる\n
        保存が正常に完了した場合は画像リストの更新が行われる\n
        imglist が None の場合は何もしない

        Args:
            imglist (list[tuple[ImageFile.ImageFile, PicInfo]]): ImageFile, PicInfo のタプルリスト
        """
        if not imglist:
            return

        for idx, imgtuple in enumerate(imglist):
            image = imgtuple[0]
            picinfo = imgtuple[1]
            if self.master.crnt_gui_configs.print_picinfo:
                dump_json(picinfo.todict(), "picinfo")

            picpath = self.make_filepath(picinfo, idx)
            if picpath.parent and not picpath.parent.exists():
                # 親ディレクトリが存在しない場合は作成する
                picpath.parent.mkdir(parents=True, exist_ok=True)

            image.save(str(picpath), pnginfo=picinfo.topnginfo())

    def worker(self) -> None:
        """
        タスクを実行する, つまり生成 -> 保存をアトミックに繰り返し実行する\n
        タスクが空, すでに実行中タスクが存在する, あるいは生成が失敗した場合はスキップする
        """
        while not self.event.shutdown.is_set():
            time.sleep(Consts.thread_interval_sec)
            with self.tasks_lock:
                with self.crnt_task_lock:
                    if not self.tasks or self.crnt_task is not None:
                        # 残りタスクが空か実行中タスクがない
                        # ここでは実行中タスクを解除してはいけない
                        continue

                    self.crnt_task = self.tasks.pop()

            try:
                if isinstance(self.crnt_task, TaskBlueprintTxt2Img):
                    imglist = self.request_generate()
                elif isinstance(self.crnt_task, TaskBlueprintImg2Img):
                    imglist = self.request_upscale()
                if not imglist:
                    continue
                else:
                    self.save_images(imglist)
            except Exception as e:
                raise
                print(f"Any exception occurred in {threading.current_thread().name}: ", e)
            finally:
                with self.crnt_task_lock:
                    self.crnt_task = None

    def instructor(self) -> None:
        """
        割り込み確認を行う\n
        ※サーバとの通信を行うので, 副スレッドにしないと timeout 時のフリーズが生じる
        """
        while not self.event.shutdown.is_set():
            time.sleep(Consts.thread_interval_sec)
            try:
                if self.event.interrupt.is_set():
                    # 中断要求
                    self.request_interrupt()
                    self.event.interrupt.clear()
            except Exception as e:
                print(f"Any exception occurred in {threading.current_thread().name}: ", e)

    def observer(self) -> None:
        """
        サーバ監視, タスクステータス更新処理を行う\n
        ※サーバとの通信を行うので, 副スレッドにしないと timeout 時のフリーズが生じる
        """
        while not self.event.shutdown.is_set():
            time.sleep(Consts.thread_interval_sec)
            try:
                with self.crnt_task_lock:
                    if self.crnt_task is None:
                        with self.progress_lock:
                            self.progress = None
                            continue

                response = self.request_progress()
                with self.progress_lock:
                    self.progress = response
            except Exception as e:
                print(f"Any exception occurred in {threading.current_thread().name}: ", e)
