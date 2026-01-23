import random
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Protocol


class NodeBody(Protocol):
    class_type: str
    inputs: object


class NodeSkeleton:
    def __init__(self, nodeidx: int, body: NodeBody):
        self.nodeidx: str = str(nodeidx)
        self.body: NodeBody = body

    def __or__(self, other):
        if isinstance(other, NodeSkeleton):
            return self.todict() | other.todict()
        elif isinstance(other, dict):
            return self.todict() | other
        return NotImplemented

    def __ror__(self, other):
        if isinstance(other, dict):
            return other | self.todict()
        return NotImplemented

    def todict(self) -> dict[str, dict]:
        return {self.nodeidx: asdict(self.body)}


@dataclass
class CheckpointLoaderSimple(NodeBody):
    @dataclass
    class Inputs:
        ckpt_name: str = ""

        @classmethod
        def make(cls, ckpt_name: str):
            return cls(ckpt_name=ckpt_name)

    class_type: str = "CheckpointLoaderSimple"
    inputs: Inputs = None

    @classmethod
    def make(cls, ckpt_name: str):
        return cls(inputs=CheckpointLoaderSimple.Inputs.make(ckpt_name=ckpt_name))


@dataclass
class EmptyLatentImage(NodeBody):
    @dataclass
    class Inputs:
        width: int = 0
        height: int = 0
        batch_size: int = 0

        @classmethod
        def make(cls, width: int, height: int, batch_size: int):
            return cls(width=width, height=height, batch_size=batch_size)

    class_type: str = "EmptyLatentImage"
    inputs: Inputs = None

    @classmethod
    def make(cls, width: int, height: int, batch_size: int):
        return cls(
            inputs=EmptyLatentImage.Inputs.make(width=width, height=height, batch_size=batch_size)
        )


@dataclass
class CLIPTextEncode(NodeBody):
    @dataclass
    class Inputs:
        text: str = ""
        clip: list[int | str] = field(default_factory=list)

        @classmethod
        def make(cls, text: str, loader: NodeSkeleton):
            return cls(text=text, clip=[loader.nodeidx, 1])

    class_type: str = "CLIPTextEncode"
    inputs: Inputs = None

    @classmethod
    def make(cls, text: str, loader: NodeSkeleton):
        if not isinstance(loader.body, CheckpointLoaderSimple):
            raise TypeError

        return cls(inputs=CLIPTextEncode.Inputs.make(text=text, loader=loader))


class UpScaleMethod(Enum):
    nearest_exact = "nearest-exact"
    nearest = "nearest"
    bilinear = "bilinear"
    area = "area"
    bicubic = "bicubic"


@dataclass
class LatentUpscale(NodeBody):
    @dataclass
    class Inputs:
        upscale_method: str = 0
        width: int = 0
        height: int = 0
        crop: str = 0
        samples: list[int | str] = field(default_factory=list)

        @classmethod
        def make(
            cls,
            upscale_method: str,
            width: int,
            height: int,
            crop: str,
            sampler: NodeSkeleton,
        ):
            return cls(
                upscale_method=upscale_method,
                width=width,
                height=height,
                crop=crop,
                samples=[sampler.nodeidx, 0],
            )

    class_type: str = "LatentUpscale"
    inputs: Inputs = None

    @classmethod
    def make(
        cls,
        upscale_method: UpScaleMethod,
        width: int,
        height: int,
        crop: bool,
        sampler: NodeSkeleton,
    ):
        if not isinstance(sampler.body, KSampler | KSamplerAdvanced):
            raise TypeError

        return cls(
            inputs=LatentUpscale.Inputs.make(
                upscale_method=upscale_method.value,
                width=width,
                height=height,
                crop="disabled" if not crop else "enabled",
                sampler=sampler,
            )
        )


@dataclass
class LatentUpscaleBy(NodeBody):
    @dataclass
    class Inputs:
        upscale_method: str = 0
        scale_by: float = 0
        samples: list[int | str] = field(default_factory=list)

        @classmethod
        def make(
            cls,
            upscale_method: str,
            scale_by: float,
            sampler: NodeSkeleton,
        ):
            return cls(
                upscale_method=upscale_method,
                scale_by=scale_by,
                samples=[sampler.nodeidx, 0],
            )

    class_type: str = "LatentUpscaleBy"
    inputs: Inputs = None

    @classmethod
    def make(
        cls,
        upscale_method: str,
        scale_by: float,
        sampler: NodeSkeleton,
    ):
        if not isinstance(sampler.body, KSampler | KSamplerAdvanced):
            raise TypeError

        return cls(
            inputs=LatentUpscaleBy.Inputs.make(
                upscale_method=upscale_method.value,
                scale_by=scale_by,
                sampler=sampler,
            )
        )


class SamplerName(Enum):
    euler = "euler"
    euler_ancestral = "euler_ancestral"
    heun = "heun"
    lms = "lms"
    ddim = "ddim"
    dpm_2 = "dpm_2"
    dpm_2_ancestral = "dpm_2_ancestral"
    dpm_fast = "dpm_fast"
    dpm_adaptive = "dpm_adaptive"
    dpmpp_2s_ancestral = "dpmpp_2s_ancestral"
    dpmpp_2m = "dpmpp_2m"
    dpmpp_2m_sde = "dpmpp_2m_sde"
    dpmpp_3m_sde = "dpmpp_3m_sde"


class SchedulerName(Enum):
    normal = "normal"
    karras = "karras"
    simple = "simple"
    exponential = "exponential"


@dataclass
class KSampler(NodeBody):
    @dataclass
    class Inputs:
        seed: int = 0
        steps: int = 0
        cfg: float = 0
        denoise: float = 0
        sampler_name: str = ""
        scheduler: str = ""
        model: list[int | str] = field(default_factory=list)
        latent_image: list[int | str] = field(default_factory=list)
        positive: list[int | str] = field(default_factory=list)
        negative: list[int | str] = field(default_factory=list)

        @classmethod
        def make(
            cls,
            seed: int,
            steps: int,
            cfg: float,
            denoise: float,
            sampler_name: str,
            scheduler: str,
            loader: NodeSkeleton,
            latent_image: NodeSkeleton,
            positive: NodeSkeleton,
            negative: NodeSkeleton,
        ):
            return cls(
                seed=seed,
                steps=steps,
                cfg=cfg,
                denoise=denoise,
                sampler_name=sampler_name,
                scheduler=scheduler,
                model=[loader.nodeidx, 0],
                latent_image=[latent_image.nodeidx, 0],
                positive=[positive.nodeidx, 0],
                negative=[negative.nodeidx, 0],
            )

    class_type: str = "KSampler"
    inputs: Inputs = None

    @classmethod
    def make(
        cls,
        seed: int,
        steps: int,
        cfg: float,
        denoise: float,
        sampler_name: SamplerName,
        scheduler: SchedulerName,
        loader: NodeSkeleton,
        latent_image: NodeSkeleton,
        positive: NodeSkeleton,
        negative: NodeSkeleton,
    ):
        if (
            not isinstance(loader.body, CheckpointLoaderSimple)
            or not isinstance(latent_image.body, EmptyLatentImage | LatentUpscale | LatentUpscaleBy)
            or not isinstance(positive.body, CLIPTextEncode)
            or not isinstance(negative.body, CLIPTextEncode)
        ):
            raise TypeError

        return cls(
            inputs=KSampler.Inputs.make(
                seed=random.randint(0, 2**31 - 1) if seed == -1 else seed,
                steps=steps,
                cfg=cfg,
                denoise=denoise,
                sampler_name=sampler_name.value,
                scheduler=scheduler.value,
                loader=loader,
                latent_image=latent_image,
                positive=positive,
                negative=negative,
            )
        )


@dataclass
class KSamplerAdvanced(NodeBody):
    @dataclass
    class Inputs:
        seed: int = 0
        steps: int = 0
        cfg: float = 0
        sampler_name: str = ""
        scheduler: str = ""
        start_at_step: int = 0
        end_at_step: int = 0
        add_noise: bool = False
        return_with_leftover_noise: bool = False
        model: list[int | str] = field(default_factory=list)
        latent_image: list[int | str] = field(default_factory=list)
        positive: list[int | str] = field(default_factory=list)
        negative: list[int | str] = field(default_factory=list)

        @classmethod
        def make(
            cls,
            seed: int,
            steps: int,
            cfg: float,
            sampler_name: SamplerName,
            scheduler: SchedulerName,
            start_at_step: int,
            end_at_step: int,
            add_noise: bool,
            return_with_leftover_noise: bool,
            loader: NodeSkeleton,
            latent_image: NodeSkeleton,
            positive: NodeSkeleton,
            negative: NodeSkeleton,
        ):
            return cls(
                seed=seed,
                steps=steps,
                cfg=cfg,
                sampler_name=sampler_name.value,
                scheduler=scheduler.value,
                start_at_step=start_at_step,
                end_at_step=end_at_step,
                add_noise=add_noise,
                return_with_leftover_noise=return_with_leftover_noise,
                model=[loader.nodeidx, 0],
                latent_image=[latent_image.nodeidx, 0],
                positive=[positive.nodeidx, 0],
                negative=[negative.nodeidx, 0],
            )

    class_type: str = "KSamplerAdvanced"
    inputs: Inputs = None

    @classmethod
    def make(
        cls,
        seed: int,
        steps: int,
        cfg: float,
        sampler_name: str,
        scheduler: str,
        start_at_step: int,
        end_at_step: int,
        add_noise: bool,
        return_with_leftover_noise: bool,
        loader: NodeSkeleton,
        latent_image: NodeSkeleton,
        positive: NodeSkeleton,
        negative: NodeSkeleton,
    ):
        if (
            not isinstance(loader.body, CheckpointLoaderSimple)
            or not isinstance(latent_image.body, EmptyLatentImage | LatentUpscale | LatentUpscaleBy)
            or not isinstance(positive.body, CLIPTextEncode)
            or not isinstance(negative.body, CLIPTextEncode)
        ):
            raise TypeError

        return cls(
            inputs=KSamplerAdvanced.Inputs.make(
                seed=random.randint(0, 2**31 - 1) if seed == -1 else seed,
                steps=steps,
                cfg=cfg,
                sampler_name=sampler_name,
                scheduler=scheduler,
                start_at_step=start_at_step,
                end_at_step=end_at_step,
                add_noise=add_noise,
                return_with_leftover_noise=return_with_leftover_noise,
                loader=loader,
                latent_image=latent_image,
                positive=positive,
                negative=negative,
            )
        )


@dataclass
class VAELoader(NodeBody):
    @dataclass
    class Inputs:
        vae_name: str = ""

        @classmethod
        def make(cls, vae_name: str):
            return cls(vae_name=vae_name)

    class_type: str = "VAELoader"
    inputs: Inputs = None

    @classmethod
    def make(cls, vae_name: str):
        return cls(inputs=VAELoader.Inputs.make(vae_name=vae_name))


@dataclass
class VAEDecode(NodeBody):
    @dataclass
    class Inputs:
        samples: list[int | str] = field(default_factory=list)
        vae: list[int | str] = field(default_factory=list)

        @classmethod
        def make(cls, sampler: NodeSkeleton, vae: NodeSkeleton):
            return cls(samples=[sampler.nodeidx, 0], vae=[vae.nodeidx, 2])

    class_type: str = "VAEDecode"
    inputs: Inputs = None

    @classmethod
    def make(cls, sampler: NodeSkeleton, vae: NodeSkeleton):
        if not isinstance(vae.body, CheckpointLoaderSimple | VAELoader) or not isinstance(
            sampler.body, KSampler | KSamplerAdvanced
        ):
            raise TypeError

        return cls(inputs=VAEDecode.Inputs.make(sampler=sampler, vae=vae))


@dataclass
class VAEEncode(NodeBody):
    @dataclass
    class Inputs:
        pixels: list[int | str] = field(default_factory=list)
        vae: list[int | str] = field(default_factory=list)

        @classmethod
        def make(cls, image: NodeSkeleton, vae: NodeSkeleton):
            return cls(pixels=[image.nodeidx, 0], vae=[vae.nodeidx, 0])

    class_type: str = "VAEEncode"
    inputs: Inputs = None

    @classmethod
    def make(cls, image: NodeSkeleton, vae: NodeSkeleton):
        if not isinstance(image.body, LoadImage) or not isinstance(
            vae.body, CheckpointLoaderSimple | VAELoader
        ):
            raise TypeError

        return cls(inputs=VAEEncode.Inputs.make(image=image, vae=vae))


@dataclass
class LoadImage(NodeBody):
    @dataclass
    class Inputs:
        image: str = ""

        @classmethod
        def make(cls, image_name: str):
            return cls(image=image_name)

    class_type: str = "LoadImage"
    inputs: Inputs = None

    @classmethod
    def make(cls, image_name: str):
        return cls(inputs=LoadImage.Inputs.make(image_name=image_name))


@dataclass
class SaveImage(NodeBody):
    @dataclass
    class Inputs:
        images: list[int | str] = field(default_factory=list)

        @classmethod
        def make(cls, vaedec: NodeSkeleton):
            return cls(images=[vaedec.nodeidx, 0])

    class_type: str = "SaveImage"
    inputs: Inputs = None

    @classmethod
    def make(cls, vaedec: NodeSkeleton):
        if not isinstance(vaedec.body, VAEDecode):
            raise TypeError

        return cls(inputs=SaveImage.Inputs.make(vaedec=vaedec))


@dataclass
class PreviewImage(NodeBody):
    @dataclass
    class Inputs:
        images: list[int | str] = field(default_factory=list)

        @classmethod
        def make(cls, vaedec: NodeSkeleton):
            return cls(images=[vaedec.nodeidx, 0])

    class_type: str = "PreviewImage"
    inputs: Inputs = None

    @classmethod
    def make(cls, vaedec: NodeSkeleton):
        if not isinstance(vaedec.body, VAEDecode):
            raise TypeError

        return cls(inputs=PreviewImage.Inputs.make(vaedec=vaedec))


class WorkFlow:
    """
    ワークフロー
    """

    def __init__(self):
        """
        コンストラクタ
        """
        self.nodelist: list[tuple[int, NodeSkeleton]] = []

    def node_of(self, idx: int) -> NodeSkeleton:
        """
        指定のノード番号を持つノードを取得する

        Args:
            idx (int): ノード番号

        Returns:
            str: ノード
        """
        return next((s for i, s in self.nodelist if i == str(idx)), None)

    def add(self, node: NodeSkeleton) -> None:
        """
        ノードを追加する\n
        すでに同じノード番号のノードがある場合は何もしない

        Args:
            node (NodeSkeleton): ノード
        """
        if self.node_of(node.nodeidx) is not None:
            # 追加済ノードは追加しない
            return

        self.nodelist.append((node.nodeidx, node))

    def todict(self) -> dict[str, dict[str, Any]]:
        """
        dict を取得

        Returns:
            dict[str, dict[str, Any]]: dict
        """
        d = {}
        for _, node in self.nodelist:
            d.update(node.todict())
        return d


class Txt2ImgWorkFlow(WorkFlow):
    """
    txt2img に相当するワークフロー
    """

    def __init__(
        self,
        ckpt_name: str,
        width: int,
        height: int,
        batch_size: int,
        pos_prompt: str,
        neg_prompt: str,
        seed: int,
        steps: int,
    ):
        """
        コンストラクタ
        """
        super().__init__()
        self.add(NodeSkeleton(1, CheckpointLoaderSimple.make(ckpt_name=ckpt_name)))
        self.add(
            NodeSkeleton(
                2, EmptyLatentImage.make(width=width, height=height, batch_size=batch_size)
            )
        )
        self.add(NodeSkeleton(3, CLIPTextEncode.make(text=pos_prompt, loader=self.node_of(1))))
        self.add(NodeSkeleton(4, CLIPTextEncode.make(text=neg_prompt, loader=self.node_of(1))))
        self.add(
            NodeSkeleton(
                5,
                KSampler.make(
                    seed=seed,
                    steps=steps,
                    cfg=7.0,
                    denoise=1.0,
                    sampler_name=SamplerName.dpmpp_2s_ancestral,
                    scheduler=SchedulerName.karras,
                    loader=self.node_of(1),
                    latent_image=self.node_of(2),
                    positive=self.node_of(3),
                    negative=self.node_of(4),
                ),
            ),
        )
        self.add(NodeSkeleton(6, VAEDecode.make(sampler=self.node_of(5), vae=self.node_of(1))))
        self.add(NodeSkeleton(7, PreviewImage.make(vaedec=self.node_of(6))))
