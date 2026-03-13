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
from threading import Lock

import requests
import websocket
from PIL import Image, ImageFile

import master.events
from archiver.dataclasses import PicInfo
from common.functions import BottleMail
from generator.comfyui_workflow import Img2ImgWorkFlow, Txt2ImgWorkFlow
from generator.dataclasses import TaskBlueprint, TaskBlueprintImg2Img, TaskBlueprintTxt2Img
from generator.generator import Generator
from master.interfaces import MasterIF


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


class ComfyUIGenerator(Generator[ComfyUITaskProgress | None]):
    """
    ファイル生成クラス (ComfyUI 版)\n
    タスク設計図をもとにサーバへ非同期にポストし, ファイル保存をする
    """

    def __init__(self, master: MasterIF, to_master: BottleMail[master.events.GeneratorEvent]):
        """
        コンストラクタ

        Args:
            master (MasterIF): Master インターフェース
        """
        super().__init__(master, to_master)

        self.client_id = str(uuid.uuid4())

        self.progress: ComfyUITaskProgress = None
        self.progress_lock = Lock()

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
                self.progress = ComfyUITaskProgress(excuting_node_idx=report.executing_node)
            elif report.type == WSMessageType.progress:
                self.progress = ComfyUITaskProgress(progress=report.sampling_progress)
            elif report.type == WSMessageType.executed:
                self.progress = ComfyUITaskProgress()
                return report

        return None

    def make_pictuple(
        self, report: TaskReport, is_upscale: bool
    ) -> list[tuple[ImageFile.ImageFile, PicInfo]]:
        """
        ImageFile と PicInfo のタプルリストをタスクレポートから得る\n
        失敗時は空リストを返す

        Args:
            report (TaskReport): タスクレポート

        Returns:
            list[tuple[ImageFile.ImageFile, PicInfo]]: ImageFile と PicInfo のタプルリスト
        """
        result: list[tuple[ImageFile.ImageFile, PicInfo]] = []
        task: TaskBlueprint = self.crnt_task_copy
        for info in report.fileinfos:
            img_res = requests.get(
                f"http://{task.dst_addr}:{task.dst_port}/view?filename={info.filename}&subfolder={info.subfolder}&type={info.type}"
            )
            if img_res.status_code != 200:
                return []

            pic = Image.open(io.BytesIO(img_res.content))
            buf = io.BytesIO()
            pic.save(buf, format="PNG")

            if is_upscale:
                workflow_resp = Img2ImgWorkFlow.fromdict(json.loads(pic.info.get("prompt")))
                picinfo = PicInfo(
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
                    ancestor=workflow_resp.ancestor,
                )
            else:
                workflow_resp = Txt2ImgWorkFlow.fromdict(json.loads(pic.info.get("prompt")))
                picinfo = PicInfo(
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

        task: TaskBlueprintTxt2Img = self.crnt_task_copy
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

        try:
            requests.post(
                f"http://{task.dst_addr}:{task.dst_port}/prompt",
                json={"prompt": workflow.todict(), "client_id": self.client_id},
            )
        except requests.exceptions.RequestException:
            print(f"Failed request to {task.dst_addr}:{task.dst_port}.")
        except Exception as e:
            print("Any exception occurred on interrupting: ", e)

        report = None
        ws = websocket.WebSocket()
        ws.connect(f"ws://{task.dst_addr}:{task.dst_port}/ws?clientId={self.client_id}")
        try:
            while True:
                try:
                    if self.is_interrupting_listen.is_set():
                        self.progress = ComfyUITaskProgress(progress=0)
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

        return self.make_pictuple(report, False) if report is not None else []

    def request_upscale(self) -> None:
        self.is_interrupting_listen.clear()
        if self.is_crnt_task_none():
            return []

        task: TaskBlueprintImg2Img = self.crnt_task_copy
        workflow = Img2ImgWorkFlow(
            ckpt_name="Illustrious\\waiNSFWIllustrious_v150.safetensors",
            path=task.path,
            pos_prompt=task.prompt,
            neg_prompt=task.negative_prompt,
            seed=task.seed,
            steps=task.steps,
            batch_size=task.batch_size,
            sampler_name=task.sampler_name,
            scheduler=task.scheduler,
            upscaler=task.upscaler_name,
            cfg_scale=task.cfg_scale,
            denoise=task.denoising_strength,
            width=task.width,
            height=task.height,
        )

        try:
            requests.post(
                f"http://{task.dst_addr}:{task.dst_port}/prompt",
                json={"prompt": workflow.todict(), "client_id": self.client_id},
            )
        except requests.exceptions.RequestException:
            print(f"Failed request to {task.dst_addr}:{task.dst_port}.")
        except Exception as e:
            print("Any exception occurred on interrupting: ", e)

        report = None
        ws = websocket.WebSocket()
        ws.connect(f"ws://{task.dst_addr}:{task.dst_port}/ws?clientId={self.client_id}")
        try:
            while True:
                try:
                    if self.is_interrupting_listen.is_set():
                        self.progress = ComfyUITaskProgress(progress=0)
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

        return self.make_pictuple(report, True) if report is not None else []

    def request_interrupt(self) -> None:
        if self.is_crnt_task_none():
            return

        try:
            task: TaskBlueprint = self.crnt_task_copy
            requests.post(f"http://{task.dst_addr}:{task.dst_port}/interrupt", timeout=(5, 10))
        except requests.exceptions.RequestException:
            return
        except Exception as e:
            print("Any exception occurred on interrupt: ", e)

        self.is_interrupting_listen.set()

    def request_progress(self) -> ComfyUITaskProgress | None:
        if self.is_crnt_task_none():
            return None

        with self.progress_lock:
            return self.progress
