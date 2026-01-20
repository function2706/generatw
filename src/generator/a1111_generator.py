"""
ファイル生成クラス (A1111 版)
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

import requests

from common.interfaces import MasterIF
from generator.generator import Generator


@dataclass
class TaskProgress:
    """
    Progress エンドポイントの応答
    """

    progress: float = 0
    eta_relative: float = 0
    skipped: bool = False
    interrupted: bool = False
    job: str = ""
    job_count: int = 0
    job_timestamp: int = 0
    job_no: int = 0
    sampling_step: int = 0
    sampling_steps: int = 0

    @staticmethod
    def to_int(v):
        return int(v) if v is not None else None

    @staticmethod
    def to_float(v):
        return float(v) if v is not None else None

    @classmethod
    def make(cls, info: dict):
        """
        コンストラクタ

        Args:
            info (dict): info 領域上のデータ
        """
        raw_skipped = info.get("skipped", False)
        skipped = (
            raw_skipped if isinstance(raw_skipped, bool) else str(raw_skipped).lower() == "true"
        )
        raw_interrupt = info.get("interrupted", False)
        interrupted = (
            raw_interrupt
            if isinstance(raw_interrupt, bool)
            else str(raw_interrupt).lower() == "true"
        )

        return cls(
            progress=cls.to_float(info.get("progress", 0)),
            eta_relative=cls.to_float(info.get("eta_relative", 0)),
            skipped=skipped,
            interrupted=interrupted,
            job=info.get("job", ""),
            job_count=cls.to_int(info.get("job_count", 0)),
            job_timestamp=cls.to_int(info.get("job_timestamp", 0)),
            job_no=cls.to_int(info.get("job_no", 0)),
            sampling_step=cls.to_int(info.get("sampling_step", 0)),
            sampling_steps=cls.to_int(info.get("sampling_steps", 0)),
        )

    def todict(self) -> dict[str, Any]:
        """
        dict への変換

        Returns:
            dict[str, Any]: dict インスタンス
        """
        return asdict(self)


class A1111Generator(Generator[TaskProgress | None]):
    """
    ファイル生成クラス (A1111 版)\n
    タスク設計図をもとにサーバへ非同期にポストし, ファイル保存をする
    """

    def __init__(self, master: MasterIF):
        """
        コンストラクタ

        Args:
            master (MasterIF): Master インターフェース
        """
        super().__init__(master)

    @property
    def crnt_progress(self) -> float:
        return self.progress.progress if self.progress is not None else 0

    def request_generate(self) -> tuple[Any, Any] | None:
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
        body: dict = response.json()
        images = body.get("images", [])
        if not images:
            return None

        return images, json.loads(body.get("info", "{}"))

    def request_upscale(self) -> None:
        return

    def request_interrupt(self) -> None:
        if self.crnt_task is None:
            return

        try:
            requests.post(
                f"http://{self.crnt_task.dst_addr}:{self.crnt_task.dst_port}/sdapi/v1/interrupt",
                timeout=(5, 10),
            )
        except Exception as e:
            print("Any exception occurred on interrupt: ", e)

    def request_progress(self) -> TaskProgress | None:
        if self.crnt_task is None:
            return

        try:
            response = requests.get(
                f"http://{self.crnt_task.dst_addr}:{self.crnt_task.dst_port}/sdapi/v1/progress?skip_current_image=true",
                timeout=(5, 10),
            )
        except Exception as e:
            print("Any exception occurred on interrupt: ", e)
            return None

        response.raise_for_status()
        return TaskProgress.make(response.json())
