"""
ファイル生成クラス
"""

from __future__ import annotations

import os
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Protocol

from PIL import ImageFile

import master.events
from archiver.dataclasses import PicInfo, PicStats
from common.functions import BackEnd, BottleMail, PathConsts, dirname_by_prompts, dump_json
from common.multideque import MultiDeque
from generator.dataclasses import (
    ResizeMode,
    SamplerName,
    SchedulerName,
    TaskBlueprintImg2Img,
    TaskBlueprintTxt2Img,
    UpScalerName,
)
from master.interfaces import MasterIF


@dataclass(frozen=True)
class Consts:
    thread_interval_sec = 0.1


@dataclass(frozen=True)
class NamesOnBackend[NameEnum]:
    name: NameEnum
    a1111: str | None
    comfy_ui: str | None


class Parser[NameEnum](ABC):
    table: Iterable[NamesOnBackend[NameEnum]]
    by_type: Mapping[NameEnum, NamesOnBackend[NameEnum]]

    def __init__(self, table: Iterable[NamesOnBackend[NameEnum]]):
        self.table = list(table)
        self.by_type = {e.name: e for e in self.table}

    def getname(self, type: NameEnum, backend: BackEnd) -> str:
        entry = self.by_type.get(type)
        if entry is None:
            raise KeyError(type)

        if backend == BackEnd.a1111:
            if entry.a1111 is None:
                raise ValueError(f"{type} not supported on a1111")
            return entry.a1111

        if backend == BackEnd.comfy_ui:
            if entry.comfy_ui is None:
                raise ValueError(f"{type} not supported on ComfyUI")
            return entry.comfy_ui

        raise ValueError(backend)


class SamplerParser(Parser[SamplerName]):
    """
    サンプラの名前定義とパーサ
    """

    def __init__(self):
        super().__init__(
            [
                NamesOnBackend(SamplerName.euler, "Euler", "euler"),
                NamesOnBackend(SamplerName.euler_cfg_pp, None, "euler_cfg_pp"),
                NamesOnBackend(SamplerName.euler_ancestral, "Euler a", "euler_ancestral"),
                NamesOnBackend(SamplerName.euler_ancestral_cfg_pp, None, "euler_ancestral_cfg_pp"),
                NamesOnBackend(SamplerName.heun, "Heun", "heun"),
                NamesOnBackend(SamplerName.heunpp2, None, "heunpp2"),
                NamesOnBackend(SamplerName.exp_heun_2_x0, None, "exp_heun_2_x0"),
                NamesOnBackend(SamplerName.exp_heun_2_x0_sde, None, "exp_heun_2_x0_sde"),
                NamesOnBackend(SamplerName.dpm_2, "DPM2", "dpm_2"),
                NamesOnBackend(SamplerName.dpm_2_ancestral, "DPM2 a", "dpm_2_ancestral"),
                NamesOnBackend(SamplerName.lms, "LMS", "lms"),
                NamesOnBackend(SamplerName.dpm_fast, "DPM fast", "dpm_fast"),
                NamesOnBackend(SamplerName.dpm_adaptive, "DPM adaptive", "dpm_adaptive"),
                NamesOnBackend(SamplerName.dpmpp_2s_ancestral, "DPM++ 2S a", "dpmpp_2s_ancestral"),
                NamesOnBackend(
                    SamplerName.dpmpp_2s_ancestral_cfg_pp, None, "dpmpp_2s_ancestral_cfg_pp"
                ),
                NamesOnBackend(SamplerName.dpmpp_sde, "DPM++ SDE", "dpmpp_sde"),
                NamesOnBackend(SamplerName.dpmpp_sde_gpu, None, "dpmpp_sde_gpu"),
                NamesOnBackend(SamplerName.dpmpp_2m, "DPM++ 2M", "dpmpp_2m"),
                NamesOnBackend(SamplerName.dpmpp_2m_cfg_pp, None, "dpmpp_2m_cfg_pp"),
                NamesOnBackend(SamplerName.dpmpp_2m_sde, "DPM++ 2M SDE", "dpmpp_2m_sde"),
                NamesOnBackend(SamplerName.dpmpp_2m_sde_gpu, None, "dpmpp_2m_sde_gpu"),
                NamesOnBackend(
                    SamplerName.dpmpp_2m_sde_heun, "DPM++ 2M SDE Heun", "dpmpp_2m_sde_heun"
                ),
                NamesOnBackend(SamplerName.dpmpp_2m_sde_heun_gpu, None, "dpmpp_2m_sde_heun_gpu"),
                NamesOnBackend(SamplerName.dpmpp_3m_sde, "DPM++ 3M SDE", "dpmpp_3m_sde"),
                NamesOnBackend(SamplerName.dpmpp_3m_sde_gpu, None, "dpmpp_3m_sde_gpu"),
                NamesOnBackend(SamplerName.ddpm, None, "ddpm"),
                NamesOnBackend(SamplerName.lcm, "LCM", "lcm"),
                NamesOnBackend(SamplerName.ipndm, None, "ipndm"),
                NamesOnBackend(SamplerName.ipndm_v, None, "ipndm_v"),
                NamesOnBackend(SamplerName.deis, None, "deis"),
                NamesOnBackend(SamplerName.res_multistep, None, "res_multistep"),
                NamesOnBackend(SamplerName.res_multistep_cfg_pp, None, "res_multistep_cfg_pp"),
                NamesOnBackend(
                    SamplerName.res_multistep_ancestral, None, "res_multistep_ancestral"
                ),
                NamesOnBackend(
                    SamplerName.res_multistep_ancestral_cfg_pp,
                    None,
                    "res_multistep_ancestral_cfg_pp",
                ),
                NamesOnBackend(SamplerName.gradient_estimation, None, "gradient_estimation"),
                NamesOnBackend(
                    SamplerName.gradient_estimation_cfg_pp, None, "gradient_estimation_cfg_pp"
                ),
                NamesOnBackend(SamplerName.er_sde, None, "er_sde"),
                NamesOnBackend(SamplerName.seeds_2, None, "seeds_2"),
                NamesOnBackend(SamplerName.seeds_3, None, "seeds_3"),
                NamesOnBackend(SamplerName.sa_solver, None, "sa_solver"),
                NamesOnBackend(SamplerName.sa_solver_pece, None, "sa_solver_pece"),
                NamesOnBackend(SamplerName.restart, "Restart", None),
                NamesOnBackend(SamplerName.ddim, "DDIM", "ddim"),
                NamesOnBackend(SamplerName.ddim_cfg_pp, "DDIM CFG++", "ddim_cfg_pp"),
                NamesOnBackend(SamplerName.plms, "PLMS", None),
                NamesOnBackend(SamplerName.uni_pc, "UniPC", "uni_pc"),
                NamesOnBackend(SamplerName.uni_pc_bh2, None, "uni_pc_bh2"),
            ]
        )


class SchedulerParser(Parser[SchedulerName]):
    """
    スケジューラの名前定義とパーサ
    """

    def __init__(self):
        super().__init__(
            [
                NamesOnBackend(SchedulerName.automatic, "Automatic", None),
                NamesOnBackend(SchedulerName.uniform, "Uniform", None),
                NamesOnBackend(SchedulerName.simple, "Simple", "simple"),
                NamesOnBackend(SchedulerName.sgm_uniform, "SGM Uniform", "sgm_uniform"),
                NamesOnBackend(SchedulerName.karras, "Karras", "karras"),
                NamesOnBackend(SchedulerName.exponential, "Exponential", "exponential"),
                NamesOnBackend(SchedulerName.polyexponential, "Polyexponential", None),
                NamesOnBackend(SchedulerName.ddim, "DDIM", None),
                NamesOnBackend(SchedulerName.ddim_uniform, None, "ddim_uniform"),
                NamesOnBackend(SchedulerName.beta, "Beta", "beta"),
                NamesOnBackend(SchedulerName.normal, "Normal", "normal"),
                NamesOnBackend(SchedulerName.linear_quadratic, None, "linear_quadratic"),
                NamesOnBackend(SchedulerName.kl_optimal, "KL Optimal", "kl_optimal"),
                NamesOnBackend(SchedulerName.align_your_steps, "Align Your Steps", None),
            ]
        )


class UpscalerParser(Parser[UpScalerName]):
    def __init__(self):
        super().__init__(
            [
                NamesOnBackend(UpScalerName.nearest_exact, None, "nearest-exact"),
                NamesOnBackend(UpScalerName.bilinear, None, "bilinear"),
                NamesOnBackend(UpScalerName.area, None, "area"),
                NamesOnBackend(UpScalerName.bicubic, None, "bicubic"),
                NamesOnBackend(UpScalerName.bislerp, None, "bislerp"),
            ]
        )


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


class Generator[TaskProgress](ABC):
    """
    ファイル生成クラス\n
    タスク設計図をもとにサーバへ非同期にポストし, ファイル保存をする
    """

    def __init__(self, master: MasterIF, to_master: BottleMail[master.events.GeneratorEvent]):
        """
        コンストラクタ

        Args:
            master (MasterIF): Master インターフェース
        """
        self.master = master

        self.event = Event()

        self.tasks: MultiDeque[TaskBlueprintTxt2Img, TaskBlueprintImg2Img] = MultiDeque(
            TaskBlueprintTxt2Img, TaskBlueprintImg2Img
        )
        self.tasks_lock = Lock()
        self.crnt_task: TaskBlueprintTxt2Img | TaskBlueprintImg2Img = None
        self.crnt_task_lock = Lock()

        self.to_master = to_master

        self.worker_thread = threading.Thread(
            target=self.worker, args=(), daemon=True, name="worker"
        )
        self.instructor_thread = threading.Thread(
            target=self.instructor, args=(), daemon=True, name="instructor"
        )
        self.observer_thread = threading.Thread(
            target=self.observer, args=(), daemon=True, name="observer"
        )

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
        if self.worker_thread.is_alive():
            self.worker_thread.join()
        if self.observer_thread.is_alive():
            self.observer_thread.join()
        if self.instructor_thread.is_alive():
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
        stps: int,
        b_size: int,
        w: int,
        h: int,
        d_addr: str,
        d_port: str,
        seed: int = -1,
        smplr: SamplerName = SamplerName.dpmpp_2m,
        schdlr: SchedulerName = SchedulerName.karras,
        cfg: float = 7.0,
    ):
        """
        新しい txt2img タスクを生成し, タスクリストに予約する\n
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
            seed (int): シード値, Defaults to -1.
            smplr (SamplerName): サンプラ, Defaults to SamplerName.dpmpp_2m.
            schdlr (SchedulerName): スケジューラ, Defaults to SchedulerName.karras.
            cfg (float): コンフィグスケール, Defaults to 7.0.
        """
        new_task: TaskBlueprintTxt2Img = TaskBlueprintTxt2Img(
            prompt=pos,
            negative_prompt=neg,
            seed=seed,
            steps=stps,
            batch_size=b_size,
            sampler_name=SamplerParser().getname(smplr, self.master.backend_type),
            scheduler=SchedulerParser().getname(schdlr, self.master.backend_type),
            cfg_scale=cfg,
            width=w,
            height=h,
            dst_addr=d_addr,
            dst_port=d_port,
        )
        with self.tasks_lock:
            with self.crnt_task_lock:
                if (new_task in self.tasks) or (new_task == self.crnt_task):
                    return
                self.tasks.push(new_task)
                nexts = len(self.tasks)
                self.to_master.enclose(
                    master.events.ChangeTasks(nexts if self.crnt_task is None else nexts + 1)
                )

    def reserve_img2img(
        self,
        picstats: PicStats,
        stps: int,
        scaleby: float,
        d_addr: str,
        d_port: str,
        smplr: SamplerName = None,
        schdlr: SchedulerName = SchedulerName.karras,
        resize_mode: ResizeMode = None,
        upsclr: UpScalerName = None,
        cfg: float = 7.0,
        denoise: float = 0.65,
    ):
        """
        新しい img2img タスクを生成し, タスクリストに予約する\n
        すでにリストに存在する, あるいは作業中のタスクの場合は何もしない

        Args:
            picstats (PicStats): 拡大する PicStats
            stps (int): ステップ数
            scaleby (float): 拡大率
            d_addr (str): 宛先アドレス
            d_port (str): 宛先ポート
            smplr (SamplerName): サンプラ, Defaults to None.
            schdlr (SchedulerName): スケジューラ, Defaults to SchedulerName.karras.
            resize_mode (ResizeMode, optional): 拡大モード(for A1111), Defaults to None.
            upsclr (UpScalerName, optional): アップスケーラ(for ComfyUI), Defaults to None.
            cfg (float): コンフィグスケール, Defaults to 7.0.
            denoise (float): ノイズ付加タイミング, Defaults to 0.65.
        """

        backend = self.master.backend_type
        if backend == BackEnd.comfy_ui:
            if smplr is None:
                smplr = SamplerName.dpmpp_2m_sde_gpu
            if upsclr is None:
                upsclr = UpScalerName.nearest_exact
        elif backend == BackEnd.a1111:
            if smplr is None:
                smplr = SamplerName.dpmpp_2m_sde
            if resize_mode is None:
                resize_mode = 3
        else:
            raise ValueError("Invalid backend for generator, img2img.")

        new_task: TaskBlueprintImg2Img = TaskBlueprintImg2Img(
            path=str(picstats.path),
            prompt=picstats.info.positive_prompt,
            negative_prompt=picstats.info.negative_prompt,
            seed=picstats.info.seed,
            steps=stps,
            batch_size=1,
            sampler_name=SamplerParser().getname(type=smplr, backend=backend),
            scheduler=SchedulerParser().getname(type=schdlr, backend=backend),
            upscaler_name=UpscalerParser().getname(type=upsclr, backend=backend)
            if upsclr is not None
            else "",
            cfg_scale=cfg,
            denoising_strength=denoise,
            resize_mode=resize_mode if resize_mode is not None else 0,
            width=int(picstats.info.width * scaleby),
            height=int(picstats.info.height * scaleby),
            dst_addr=d_addr,
            dst_port=d_port,
        )
        with self.tasks_lock:
            with self.crnt_task_lock:
                if (new_task in self.tasks) or (new_task == self.crnt_task):
                    return
                self.tasks.push(new_task)
                nexts = len(self.tasks)
                self.to_master.enclose(
                    master.events.ChangeTasks(nexts if self.crnt_task is None else nexts + 1)
                )

    def clear(self) -> None:
        """
        タスクリストを空にする
        """
        with self.tasks_lock:
            self.tasks.clear()
            self.to_master.enclose(master.events.ChangeTasks(0 if self.crnt_task is None else 1))

    def clear_of(self, task_type: type) -> None:
        """
        タスクリストを空にする
        """
        with self.tasks_lock:
            self.tasks.clear_type(task_type)
            self.to_master.enclose(
                master.events.ChangeTasks(
                    len(self.tasks) if self.crnt_task is None else len(self.tasks) + 1
                )
            )

    def is_crnt_task_none(self) -> bool:
        """
        現在のタスクが存在するか

        Returns:
            bool: True: 存在する(実行中), False: 存在しない
        """
        with self.crnt_task_lock:
            return self.crnt_task is None

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

        dirpath = PathConsts.pic_dir / Path(dirname_by_prompts(pos_prompt, neg_prompt))
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
            image, picinfo = imgtuple
            if self.master.crnt_gui_configs.print_picinfo:
                dump_json(picinfo.todict(), "picinfo")

            picpath = self.make_filepath(picinfo, idx)
            if picpath.parent and not picpath.parent.exists():
                # 親ディレクトリが存在しない場合は作成する
                picpath.parent.mkdir(parents=True, exist_ok=True)

            image.save(str(picpath), pnginfo=picinfo.topnginfo())

            if picinfo.ancestor:
                # 拡大元画像がある場合は削除する
                os.remove(picinfo.ancestor)

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
                    self.to_master.enclose(master.events.TaskStart(self.crnt_task))

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
                print(f"Any exception occurred in {threading.current_thread().name}: ", e)
            finally:
                with self.crnt_task_lock:
                    if self.crnt_task is not None:
                        self.to_master.enclose(master.events.TaskComplete())
                        self.to_master.enclose(master.events.NewProgress(0))
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
                response = self.request_progress()
                if response is not None:
                    self.to_master.enclose(master.events.NewProgress(response.progress))
            except Exception as e:
                print(f"Any exception occurred in {threading.current_thread().name}: ", e)
