"""
タスク管理クラス
"""

from __future__ import annotations

import json
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass
from typing import Any, Callable, Dict, Optional, Tuple

import requests


@dataclass
class Event:
    """
    イベントフラグ
    """

    shutdown = threading.Event()
    interrupt = threading.Event()


@dataclass
class TaskBlueprint:
    """
    タスクの設計図\n
    プロンプトの組, 生成キュー用に使用する\n
    インスタンス化した際, その時点のプロンプトを記録中ステータスから生成し, セットする
    """

    prompt: str = ""
    negative_prompt: str = ""
    steps: int = 0
    batch_size: int = 0
    sampler_name: str = "DPM++ 2S a"
    scheduler: str = "Karras"
    cfg_scale: float = 7.0
    seed: int = -1
    width: int = 0
    height: int = 0

    dst_addr: str = ""
    dst_port: str = ""

    @classmethod
    def make(
        cls, pos: str, neg: str, stps: int, b_size: int, w: int, h: int, d_addr: str, d_port: str
    ):
        """
        コンストラクタ

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
        return cls(
            prompt=pos,
            negative_prompt=neg,
            steps=stps,
            batch_size=b_size,
            width=w,
            height=h,
            dst_addr=d_addr,
            dst_port=d_port,
        )

    def todict(self) -> Dict[str, Any]:
        """
        Dict への変換

        Returns:
            Dict[str, Any]: Dict インスタンス
        """
        return asdict(self)


class TaskManager:
    """
    タスク管理クラス
    """

    def __init__(self, on_saving: Callable[[Any, Any], None]):
        """
        コンストラクタ

        Args:
            on_saving (Callable[[Any, Any]): 画像保存処理コールバック
        """
        self.event = Event()

        self.on_saving: Callable[[Any, Any], None] = on_saving

        self.tasks: deque[TaskBlueprint] = deque()
        self.crnt_task: TaskBlueprint = None

        self.task_thread = threading.Thread(target=self.task_thread, args=(), daemon=True)

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
        self.post_interrupt()

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

    def post_interrupt(self) -> None:
        """
        Stable Diffusion interrupt エンドポイントへポストする\n
        現在のタスクが空の場合は何もしない
        """
        if self.crnt_task is None:
            return

        self.event.interrupt.set()
        try:
            requests.post(
                f"http://{self.crnt_task.dst_addr}:{self.crnt_task.dst_port}/sdapi/v1/interrupt",
                timeout=(5, 10),
            )
        except Exception as e:
            print("Any exception occurred on interrupt: ", e)

    def post_txt2img(self) -> Optional[Tuple[Any, Any]]:
        """
        現在のタスクをもとに Stable Diffusion txt2img エンドポイントへポストする\n
        現在のタスクが空の場合は何もしない

        Returns:
            Tuple[Any, Any]: image フィールドと info フィールドのタプル, 失敗時は None
        """
        if self.crnt_task is None:
            return

        try:
            response = requests.post(
                f"http://{self.crnt_task.dst_addr}:{self.crnt_task.dst_port}/sdapi/v1/txt2img",
                json=self.crnt_task.todict(),
                timeout=(5, 60),
            )
        except Exception as e:
            print("Any exception occurred on interrupt: ", e)
            return None

        response.raise_for_status()
        body = response.json()
        images = body.get("images", [])
        if not images:
            return None

        return images, json.loads(body.get("info", "{}"))

    def task_thread(self) -> None:
        """
        タスクを実行する, つまり生成 -> 保存をアトミックに繰り返し実行する\n
        タスクが空, すでに実行中タスクが存在する, あるいは生成が失敗した場合はスキップする
        """
        while not self.event.shutdown.is_set():
            time.sleep(0.5)
            if not self.tasks or self.crnt_task is not None:
                # ここでは実行中タスクを解除してはいけない
                continue

            try:
                self.crnt_task = self.tasks.popleft()

                result = self.post_txt2img()
                if self.event.interrupt.is_set():
                    continue
                if result is None:
                    # 生成失敗
                    print("Failed to post, API response without images.")
                    continue
                else:
                    images, infos = result
                    self.on_saving(images, infos)
            except Exception as e:
                print("Any exception occurred: ", e)
            finally:
                self.crnt_task = None
                self.event.interrupt.clear()
