"""
ファイル生成クラス (ComfyUI 版)
"""

from __future__ import annotations

import io
import json
import threading
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto

import requests
import websocket
from PIL import Image, ImageFile

from archiver.dataclasses import PicInfo
from common.interfaces import MasterIF
from generator.comfyui_workflow import Txt2ImgWorkFlow
from generator.generator import Generator


class WSMessageType(Enum):
    executing = auto()  # 個別ノードごとの進捗
    progress = auto()  # サンプラ進捗(ステップ毎)
    executed = auto()  # 実行完了
    none = auto()


@dataclass
class TaskReport:
    """
    タスクレポート
    """

    @dataclass
    class FileInfo:
        filename: str = ""
        subfolder: str = ""
        type: str = ""

        @classmethod
        def make(cls, images: dict):
            return cls(
                filename=images["filename"],
                subfolder=images["subfolder"],
                type=images["type"],
            )

    type: WSMessageType = WSMessageType.none
    executing_node: int = 0
    sampling_progress: float = 0.0
    fileinfos: list[FileInfo] = field(default_factory=list)

    @classmethod
    def make(cls, message: dict):
        obj = cls()
        msg_type = message.get("type")
        if msg_type == "executing":
            obj.type = WSMessageType.executing
            obj.executing_node = int(message["data"]["node"])
        elif msg_type == "progress":
            obj.type = WSMessageType.progress
            obj.sampling_progress = float(message["data"]["value"]) / float(message["data"]["max"])
        elif msg_type == "executed":
            obj.type = WSMessageType.executed
            images = message["data"]["output"].get("images", [])
            obj.fileinfos = [TaskReport.FileInfo.make(img) for img in images]

        return obj


@dataclass
class ComfyUITaskProgress:
    """
    ワークフロー進捗
    """

    progress: float = 0.0
    excuting_node_idx: int = 0

    @classmethod
    def make(cls, progress: float = -1, excuting_node_idx: int = -1):
        """
        コンストラクタ

        Args:
            progress (float): 進捗率
            excuting_node_idx (int): 実行中のノードインデックス
        """
        return cls(
            progress=progress if progress >= 0 else 0.0,
            excuting_node_idx=excuting_node_idx if excuting_node_idx >= 0 else 0,
        )


class ComfyUIGenerator(Generator[ComfyUITaskProgress | None]):
    """
    ファイル生成クラス (ComfyUI 版)\n
    タスク設計図をもとにサーバへ非同期にポストし, ファイル保存をする
    """

    def __init__(self, master: MasterIF):
        """
        コンストラクタ

        Args:
            master (MasterIF): Master インターフェース
        """
        super().__init__(master)

        self.client_id = str(uuid.uuid4())

        self.is_interrupting_listen = threading.Event()  # WS listen 中断要求があった

    def finalize(self) -> None:
        self.is_interrupting_listen.clear()
        super().finalize()

    def listen_websocket(self, ws: websocket.WebSocket) -> TaskReport | None:
        """
        WebSocket でリッスンし, タスクレポートを取得する

        Args:
            ws (websocket.WebSocket): WebSocket

        Returns:
            TaskReport | None: タスクレポート
        """
        ws.settimeout(0.5)
        out = ws.recv()
        if not isinstance(out, str) or len(out) == 0:
            return None

        message = json.loads(out)
        report = TaskReport.make(message)
        with self.progress_lock:
            if report.type == WSMessageType.executing:
                self.progress = ComfyUITaskProgress.make(excuting_node_idx=report.executing_node)
            elif report.type == WSMessageType.progress:
                self.progress = ComfyUITaskProgress.make(progress=report.sampling_progress)
            elif report.type == WSMessageType.executed:
                self.progress = ComfyUITaskProgress.make()
                return report

        return None

    def make_pictuple(self, report: TaskReport) -> list[tuple[ImageFile.ImageFile, PicInfo]]:
        """
        ImageFile と PicInfo のタプルリストをタスクレポートから得る\n
        失敗時は空リストを返す

        Args:
            report (TaskReport): タスクレポート

        Returns:
            list[tuple[ImageFile.ImageFile, PicInfo]]: ImageFile と PicInfo のタプルリスト
        """
        result: list[tuple[ImageFile.ImageFile, PicInfo]] = []
        for info in report.fileinfos:
            img_res = requests.get(
                f"http://{self.crnt_dst}/view?filename={info.filename}&subfolder={info.subfolder}&type={info.type}"
            )
            if img_res.status_code != 200:
                return []

            pic = Image.open(io.BytesIO(img_res.content))
            buf = io.BytesIO()
            pic.save(buf, format="PNG")

            workflow_resp = Txt2ImgWorkFlow.fromdict(json.loads(pic.info.get("prompt")))
            picinfo = PicInfo.make(
                positive_prompt=workflow_resp.positive_prompt,
                negative_prompt=workflow_resp.negative_prompt,
                steps=workflow_resp.steps,
                sampler=workflow_resp.sampler,
                scheduler=workflow_resp.scheduler,
                cfg_scale=workflow_resp.cfg_scale,
                seed=workflow_resp.seed,
                width=workflow_resp.width,
                height=workflow_resp.height,
                model_name=workflow_resp.model_name,
                model_hash="",
                clip_skip=workflow_resp.clip_skip,
            )

            result.append((Image.open(buf), picinfo))

        return result

    def request_generate(self) -> list[tuple[ImageFile.ImageFile, PicInfo]]:
        self.is_interrupting_listen.clear()
        if self.is_crnt_task_none():
            return []

        with self.crnt_task_lock:
            task = self.crnt_task
        workflow = Txt2ImgWorkFlow(
            ckpt_name="Illustrious\\waiNSFWIllustrious_v150.safetensors",
            pos_prompt=task.prompt,
            neg_prompt=task.negative_prompt,
            seed=task.seed,
            steps=task.steps,
            batch_size=task.batch_size,
            sampler_name=task.sampler_name,
            scheduler=task.scheduler,
            cfg_scale=task.cfg_scale,
            width=task.width,
            height=task.height,
        )

        dst = self.crnt_dst
        try:
            requests.post(
                f"http://{dst}/prompt",
                json={"prompt": workflow.todict(), "client_id": self.client_id},
            )
        except requests.exceptions.RequestException:
            print(f"Failed request to {dst}.")
        except Exception as e:
            print("Any exception occurred on interrupting: ", e)

        report = None
        ws = websocket.WebSocket()
        ws.connect(f"ws://{dst}/ws?clientId={self.client_id}")
        try:
            while True:
                try:
                    if self.is_interrupting_listen.is_set():
                        return []

                    report = self.listen_websocket(ws)
                    if report is not None:
                        break
                except websocket.WebSocketTimeoutException:
                    continue
        except Exception as e:
            print("Any exception occurred in connecting with WS: ", e)
        finally:
            ws.close()

        return self.make_pictuple(report) if report is not None else []

    def request_upscale(self) -> None:
        return

    def request_interrupt(self) -> None:
        if self.is_crnt_task_none():
            return

        try:
            dst = self.crnt_dst
            requests.post(f"http://{dst}/interrupt", timeout=(5, 10))
        except requests.exceptions.RequestException:
            return
        except Exception as e:
            print("Any exception occurred on interrupt: ", e)

        self.is_interrupting_listen.set()

    def request_progress(self) -> ComfyUITaskProgress | None:
        with self.progress_lock:
            return self.progress
