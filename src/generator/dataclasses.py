"""
共用クラス
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum, auto
from typing import Any


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
    restart = auto()
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


class ResizeMode(Enum):
    just_resize = 0
    crop_n_resize = 1
    resize_n_fill = 2
    just_resize_latent = 3


class UpScalerName(Enum):
    nearest_exact = auto()
    bilinear = auto()
    area = auto()
    bicubic = auto()
    bislerp = auto()


@dataclass
class TaskBlueprint:
    """
    タスクの設計図
    """

    prompt: str = ""
    negative_prompt: str = ""
    seed: int = 0
    steps: int = 0
    batch_size: int = 0
    sampler_name: str = ""
    scheduler: str = ""
    cfg_scale: float = 0.0
    width: int = 0
    height: int = 0

    dst_addr: str = ""
    dst_port: str = ""

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
    txt2img タスクの設計図
    """

    pass


@dataclass
class TaskBlueprintImg2Img(TaskBlueprint):
    path: str = None
    denoising_strength: float = 0.0

    # for A1111
    init_images: list[str] = field(default_factory=list)
    resize_mode: int = 0

    # for ComfyUI
    upscaler_name: str = ""


@dataclass
class GeneratorEvent:
    pass


@dataclass
class TaskStart(GeneratorEvent):
    new_task: TaskBlueprint


@dataclass
class TaskComplete(GeneratorEvent):
    pass


@dataclass
class IsNewProgress(GeneratorEvent):
    progress: float = 0.0


@dataclass
class IncreasedTasks(GeneratorEvent):
    tasks: int = 0
