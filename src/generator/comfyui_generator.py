"""
ファイル生成クラス (ComfyUI 版)
"""

from __future__ import annotations

import io
import json
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto

import requests
import websocket
from PIL import Image, ImageFile

from common.classes import PicInfo
from common.interfaces import MasterIF
from generator.comfyui_workflow import Txt2ImgWorkFlow
from generator.generator import Generator


class WSMessageType(Enum):
    executing = auto()  # 個別ノードごとの進捗
    progress = auto()  # サンプラ進捗(ステップ毎)
    executed = auto()  # 実行完了
    none = auto()


@dataclass
class TaskProgress:
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
            obj.fileinfos = [TaskProgress.FileInfo.make(img) for img in images]

        return obj


class ComfyUIGenerator(Generator[None]):
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

        self.crnt_progress_ratio: float = 0.0

    def request_generate(self) -> list[tuple[ImageFile.ImageFile, PicInfo]]:
        if self.crnt_task is None:
            return []

        client_id = str(uuid.uuid4())
        ws = websocket.WebSocket()
        ws.connect(f"ws://{self.crnt_dst}/ws?clientId={client_id}")
        task = self.crnt_task
        workflow = Txt2ImgWorkFlow(
            ckpt_name="Illustrious\\waiNSFWIllustrious_v150.safetensors",
            width=task.width,
            height=task.height,
            batch_size=task.batch_size,
            pos_prompt=task.prompt,
            neg_prompt=task.negative_prompt,
            seed=task.seed,
            steps=task.steps,
        )
        res = requests.post(
            f"http://{self.crnt_dst}/prompt",
            json={"prompt": workflow.todict(), "client_id": client_id},
        )
        res.raise_for_status()

        while True:
            out = ws.recv()
            if not isinstance(out, str):
                continue

            message = json.loads(out)
            report = TaskProgress.make(message)
            if report.type == WSMessageType.executing:
                print(f"node:{report.executing_node}")
            elif report.type == WSMessageType.progress:
                print(f"sampling_progress:{report.sampling_progress}")
            elif report.type == WSMessageType.executed:
                print("executed")
                break
        ws.close()

        result: list[tuple[ImageFile.ImageFile, PicInfo]] = []
        for info in report.fileinfos:
            img_res = requests.get(
                f"http://{self.crnt_dst}/view?filename={info.filename}&\
                subfolder={info.subfolder}&type={info.type}"
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

    def request_upscale(self) -> None:
        return

    def request_interrupt(self) -> None:
        return

    def request_progress(self) -> None:
        return None
