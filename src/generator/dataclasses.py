"""
共用クラス
"""

from __future__ import annotations

from abc import ABC
from dataclasses import asdict, dataclass
from enum import Enum, auto
from typing import Any, Generic, Iterable, Mapping, TypeVar

from archiver.dataclasses import PicStats
from common.functions import BackEnd


class SamplerName(Enum):
    euler = auto()
    euler_cfg_pp = auto()
    euler_ancestral = auto()
    euler_ancestral_cfg_pp = auto()
    heun = auto()
    heunpp2 = auto()
    exp_heun_2_x0 = auto()
    exp_heun_2_x0_sde = auto()
    dpm_2 = auto()
    dpm_2_ancestral = auto()
    lms = auto()
    dpm_fast = auto()
    dpm_adaptive = auto()
    dpmpp_2s_ancestral = auto()
    dpmpp_2s_ancestral_cfg_pp = auto()
    dpmpp_sde = auto()
    dpmpp_sde_gpu = auto()
    dpmpp_2m = auto()
    dpmpp_2m_cfg_pp = auto()
    dpmpp_2m_sde = auto()
    dpmpp_2m_sde_gpu = auto()
    dpmpp_2m_sde_heun = auto()
    dpmpp_2m_sde_heun_gpu = auto()
    dpmpp_3m_sde = auto()
    dpmpp_3m_sde_gpu = auto()
    ddpm = auto()
    lcm = auto()
    ipndm = auto()
    ipndm_v = auto()
    deis = auto()
    res_multistep = auto()
    res_multistep_cfg_pp = auto()
    res_multistep_ancestral = auto()
    res_multistep_ancestral_cfg_pp = auto()
    gradient_estimation = auto()
    gradient_estimation_cfg_pp = auto()
    er_sde = auto()
    seeds_2 = auto()
    seeds_3 = auto()
    sa_solver = auto()
    sa_solver_pece = auto()
    restart = (auto(),)
    ddim = auto()
    ddim_cfg_pp = auto()
    plms = auto()
    uni_pc = auto()
    uni_pc_bh2 = auto()


class SchedulerName(Enum):
    automatic = auto()
    uniform = auto()
    simple = auto()
    sgm_uniform = auto()
    karras = auto()
    exponential = auto()
    polyexponential = auto()
    ddim = auto()
    ddim_uniform = auto()
    beta = auto()
    normal = auto()
    linear_quadratic = auto()
    kl_optimal = auto()
    align_your_steps = auto()


NameEnum = TypeVar("NameEnum")


@dataclass(frozen=True)
class NamesOnBackend(Generic[NameEnum]):
    name: NameEnum
    a1111: str | None
    comfy_ui: str | None


class Parser(ABC, Generic[NameEnum]):
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


@dataclass
class TaskBlueprint:
    """
    タスクの設計図
    """

    seed: int = 0
    steps: int = 0
    batch_size: int = 0
    sampler_name: str = ""
    scheduler: str = ""
    cfg_scale: float = 0.0

    dst_addr: str = ""
    dst_port: str = ""

    @classmethod
    def make(
        cls,
        b_end: BackEnd,
        seed: int,
        stps: int,
        b_size: int,
        smplr: SamplerName,
        schdlr: SchedulerName,
        cfg: float,
        d_addr: str,
        d_port: str,
    ):
        """
        コンストラクタ

        Args:
            b_end (BackEnd): バックエンド型
            seed (int): シード値
            stps (int): ステップ数
            b_size (int): バッチサイズ
            smplr (SamplerName): サンプラー
            schdlr (SchedulerName): スケジューラ
            cfg (float): コンフィグスケール
            d_addr (str): 宛先アドレス
            d_port (str): 宛先ポート

        Returns:
            _type_: TaskBlueprint
        """
        obj = cls()
        obj.seed = seed
        obj.steps = stps
        obj.batch_size = b_size
        obj.sampler_name = SamplerParser().getname(type=smplr, backend=b_end)
        obj.scheduler = SchedulerParser().getname(type=schdlr, backend=b_end)
        obj.cfg_scale = cfg
        obj.dst_addr = d_addr
        obj.dst_port = d_port

        return obj

    def todict(self) -> dict[str, Any]:
        """
        dict への変換

        Returns:
            dict[str, Any]: dict インスタンス
        """
        return asdict(self)


@dataclass
class TaskBlueprintTxt2Img(TaskBlueprint):
    """
    タスクの設計図\n
    プロンプトの組, 生成キュー用に使用する\n
    インスタンス化した際, その時点のプロンプトを記録中ステータスから生成し, セットする
    """

    prompt: str = ""
    negative_prompt: str = ""

    width: int = 0
    height: int = 0

    @classmethod
    def make(
        cls,
        b_end: BackEnd,
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
    ) -> TaskBlueprintTxt2Img:
        """
        コンストラクタ

        Args:
            b_end (BackEnd): バックエンド型
            pos (str): ポジティブプロンプト
            neg (str): ネガティブプロンプト
            seed (int): シード値
            stps (int): ステップ数
            b_size (int): バッチサイズ
            smplr (SamplerName): サンプラー
            schdlr (SchedulerName): スケジューラ
            cfg (float): コンフィグスケール
            w (int): 幅
            h (int): 高さ
            d_addr (str): 宛先アドレス
            d_port (str): 宛先ポート
        """
        obj: TaskBlueprintTxt2Img = super().make(
            b_end=b_end,
            seed=seed,
            stps=stps,
            b_size=b_size,
            smplr=smplr,
            schdlr=schdlr,
            cfg=cfg,
            d_addr=d_addr,
            d_port=d_port,
        )
        obj.prompt = pos
        obj.negative_prompt = neg
        obj.width = w
        obj.height = h
        return obj


@dataclass
class TaskBlueprintImg2Img(TaskBlueprint):
    target: PicStats = None

    scaleby: int = 0
    denoising_strength: float = 0.0

    resize_mode: int = 0

    @classmethod
    def make(
        cls, pos: str, neg: str, stps: int, b_size: int, w: int, h: int, d_addr: str, d_port: str
    ) -> TaskBlueprintImg2Img:
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
