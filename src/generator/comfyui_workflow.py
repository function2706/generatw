import random
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Protocol, cast


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

    @classmethod
    def set(cls, data: dict[str, Any]):
        if data["class_type"] != "CheckpointLoaderSimple":
            raise ValueError
        data_inputs = data["inputs"]
        return cls(inputs=CheckpointLoaderSimple.Inputs.make(ckpt_name=data_inputs["ckpt_name"]))


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

    @classmethod
    def set(cls, data: dict[str, Any]):
        if data["class_type"] != "EmptyLatentImage":
            raise ValueError
        data_inputs = data["inputs"]
        return cls(
            inputs=EmptyLatentImage.Inputs.make(
                width=int(data_inputs["width"]),
                height=int(data_inputs["height"]),
                batch_size=int(data_inputs["batch_size"]),
            )
        )


@dataclass
class CLIPTextEncode(NodeBody):
    @dataclass
    class Inputs:
        text: str = ""
        clip: list[int | str] = field(default_factory=list)

        @classmethod
        def make(cls, text: str, loader: NodeSkeleton = None):
            return cls(text=text, clip=[loader.nodeidx, 1] if loader is not None else [])

    class_type: str = "CLIPTextEncode"
    inputs: Inputs = None

    @classmethod
    def make(cls, text: str, loader: NodeSkeleton):
        if not isinstance(loader.body, CheckpointLoaderSimple):
            raise TypeError

        return cls(inputs=CLIPTextEncode.Inputs.make(text=text, loader=loader))

    @classmethod
    def set(cls, data: dict[str, Any]):
        if data["class_type"] != "CLIPTextEncode":
            raise ValueError
        data_inputs = data["inputs"]
        return cls(
            inputs=CLIPTextEncode.Inputs.make(
                text=data_inputs["text"],
            )
        )


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
            sampler: NodeSkeleton = None,
        ):
            return cls(
                upscale_method=upscale_method,
                width=width,
                height=height,
                crop=crop,
                samples=[sampler.nodeidx, 0] if sampler is not None else [],
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

    @classmethod
    def set(cls, data: dict[str, Any]):
        if data["class_type"] != "LatentUpscale":
            raise ValueError
        data_inputs = data["inputs"]
        return cls(
            inputs=LatentUpscale.Inputs.make(
                upscale_method=data_inputs["upscale_method"],
                width=int(data_inputs["width"]),
                height=int(data_inputs["height"]),
                crop=data_inputs["crop"],
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
            sampler: NodeSkeleton = None,
        ):
            return cls(
                upscale_method=upscale_method,
                scale_by=scale_by,
                samples=[sampler.nodeidx, 0] if sampler is not None else [],
            )

    class_type: str = "LatentUpscaleBy"
    inputs: Inputs = None

    @classmethod
    def make(
        cls,
        upscale_method: UpScaleMethod,
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

    @classmethod
    def set(cls, data: dict[str, Any]):
        if data["class_type"] != "LatentUpscaleBy":
            raise ValueError
        data_inputs = data["inputs"]
        return cls(
            inputs=LatentUpscaleBy.Inputs.make(
                upscale_method=data_inputs["upscale_method"],
                scale_by=float(data_inputs["scale_by"]),
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
            loader: NodeSkeleton = None,
            latent_image: NodeSkeleton = None,
            positive: NodeSkeleton = None,
            negative: NodeSkeleton = None,
        ):
            return cls(
                seed=seed,
                steps=steps,
                cfg=cfg,
                denoise=denoise,
                sampler_name=sampler_name,
                scheduler=scheduler,
                model=[loader.nodeidx, 0] if loader is not None else [],
                latent_image=[latent_image.nodeidx, 0] if latent_image is not None else [],
                positive=[positive.nodeidx, 0] if positive is not None else [],
                negative=[negative.nodeidx, 0] if negative is not None else [],
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

    @classmethod
    def set(cls, data: dict[str, Any]):
        if data["class_type"] != "KSampler":
            raise ValueError
        data_inputs = data["inputs"]
        return cls(
            inputs=KSampler.Inputs.make(
                seed=int(data_inputs["seed"]),
                steps=int(data_inputs["steps"]),
                cfg=float(data_inputs["cfg"]),
                denoise=float(data_inputs["denoise"]),
                sampler_name=data_inputs["sampler_name"],
                scheduler=data_inputs["scheduler"],
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
            loader: NodeSkeleton = None,
            latent_image: NodeSkeleton = None,
            positive: NodeSkeleton = None,
            negative: NodeSkeleton = None,
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
                model=[loader.nodeidx, 0] if loader is not None else [],
                latent_image=[latent_image.nodeidx, 0] if latent_image is not None else [],
                positive=[positive.nodeidx, 0] if positive is not None else [],
                negative=[negative.nodeidx, 0] if negative is not None else [],
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

    @classmethod
    def set(cls, data: dict[str, Any]):
        if data["class_type"] != "KSamplerAdvanced":
            raise ValueError
        data_inputs = data["inputs"]
        return cls(
            inputs=KSamplerAdvanced.Inputs.make(
                seed=int(data_inputs["seed"]),
                steps=int(data_inputs["steps"]),
                cfg=float(data_inputs["cfg"]),
                sampler_name=data_inputs["sampler_name"],
                scheduler=data_inputs["scheduler"],
                start_at_step=int(data_inputs["start_at_step"]),
                end_at_step=int(data_inputs["end_at_step"]),
                add_noise=True if data_inputs["add_noise"] == "true" else False,
                return_with_leftover_noise=True
                if data_inputs["return_with_leftover_noise"] == "true"
                else False,
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

    @classmethod
    def set(cls, data: dict[str, Any]):
        if data["class_type"] != "VAELoader":
            raise ValueError
        data_inputs = data["inputs"]
        return cls(inputs=VAELoader.Inputs.make(vae_name=data_inputs["vae_name"]))


@dataclass
class VAEDecode(NodeBody):
    @dataclass
    class Inputs:
        samples: list[int | str] = field(default_factory=list)
        vae: list[int | str] = field(default_factory=list)

        @classmethod
        def make(cls, sampler: NodeSkeleton = None, vae: NodeSkeleton = None):
            return cls(
                samples=[sampler.nodeidx, 0] if sampler is not None else [],
                vae=[vae.nodeidx, 2] if vae is not None else [],
            )

    class_type: str = "VAEDecode"
    inputs: Inputs = None

    @classmethod
    def make(cls, sampler: NodeSkeleton, vae: NodeSkeleton):
        if not isinstance(vae.body, CheckpointLoaderSimple | VAELoader) or not isinstance(
            sampler.body, KSampler | KSamplerAdvanced
        ):
            raise TypeError

        return cls(inputs=VAEDecode.Inputs.make(sampler=sampler, vae=vae))

    @classmethod
    def set(cls, data: dict[str, Any]):
        if data["class_type"] != "VAEDecode":
            raise ValueError
        return cls(inputs=VAEDecode.Inputs.make())


@dataclass
class VAEEncode(NodeBody):
    @dataclass
    class Inputs:
        pixels: list[int | str] = field(default_factory=list)
        vae: list[int | str] = field(default_factory=list)

        @classmethod
        def make(cls, image: NodeSkeleton = None, vae: NodeSkeleton = None):
            return cls(
                pixels=[image.nodeidx, 0] if image is not None else [],
                vae=[vae.nodeidx, 0] if vae is not None else [],
            )

    class_type: str = "VAEEncode"
    inputs: Inputs = None

    @classmethod
    def make(cls, image: NodeSkeleton, vae: NodeSkeleton):
        if not isinstance(image.body, LoadImage) or not isinstance(
            vae.body, CheckpointLoaderSimple | VAELoader
        ):
            raise TypeError

        return cls(inputs=VAEEncode.Inputs.make(image=image, vae=vae))

    @classmethod
    def set(cls, data: dict[str, Any]):
        if data["class_type"] != "VAEEncode":
            raise ValueError
        return cls(inputs=VAEEncode.Inputs.make())


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

    @classmethod
    def set(cls, data: dict[str, Any]):
        if data["class_type"] != "LoadImage":
            raise ValueError
        data_inputs = data["inputs"]
        return cls(inputs=LoadImage.Inputs.make(image_name=data_inputs["image"]))


@dataclass
class SaveImage(NodeBody):
    @dataclass
    class Inputs:
        images: list[int | str] = field(default_factory=list)

        @classmethod
        def make(cls, vaedec: NodeSkeleton = None):
            return cls(images=[vaedec.nodeidx, 0] if vaedec is not None else [])

    class_type: str = "SaveImage"
    inputs: Inputs = None

    @classmethod
    def make(cls, vaedec: NodeSkeleton):
        if not isinstance(vaedec.body, VAEDecode):
            raise TypeError

        return cls(inputs=SaveImage.Inputs.make(vaedec=vaedec))

    @classmethod
    def set(cls, data: dict[str, Any]):
        if data["class_type"] != "SaveImage":
            raise ValueError
        return cls(inputs=SaveImage.Inputs.make())


@dataclass
class PreviewImage(NodeBody):
    @dataclass
    class Inputs:
        images: list[int | str] = field(default_factory=list)

        @classmethod
        def make(cls, vaedec: NodeSkeleton = None):
            return cls(images=[vaedec.nodeidx, 0] if vaedec is not None else [])

    class_type: str = "PreviewImage"
    inputs: Inputs = None

    @classmethod
    def make(cls, vaedec: NodeSkeleton):
        if not isinstance(vaedec.body, VAEDecode):
            raise TypeError

        return cls(inputs=PreviewImage.Inputs.make(vaedec=vaedec))

    @classmethod
    def set(cls, data: dict[str, Any]):
        if data["class_type"] != "PreviewImage":
            raise ValueError
        return cls(inputs=PreviewImage.Inputs.make())


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

    @classmethod
    def fromdict(cls, data: dict[str, dict[str, Any]]):
        """
        dict から生成

        Args:
            data (dict[str, dict[str, Any]]): dict
        """
        obj = cls()

        for idx, node_skeleton in data.items():
            class_type: str = node_skeleton.get("class_type")
            if class_type == "CheckpointLoaderSimple":
                obj.add(NodeSkeleton(int(idx), CheckpointLoaderSimple.set(node_skeleton)))
            elif class_type == "EmptyLatentImage":
                obj.add(NodeSkeleton(int(idx), EmptyLatentImage.set(node_skeleton)))
            elif class_type == "CLIPTextEncode":
                obj.add(NodeSkeleton(int(idx), CLIPTextEncode.set(node_skeleton)))
            elif class_type == "LatentUpscale":
                obj.add(NodeSkeleton(int(idx), LatentUpscale.set(node_skeleton)))
            elif class_type == "LatentUpscaleBy":
                obj.add(NodeSkeleton(int(idx), LatentUpscaleBy.set(node_skeleton)))
            elif class_type == "KSampler":
                obj.add(NodeSkeleton(int(idx), KSampler.set(node_skeleton)))
            elif class_type == "KSamplerAdvanced":
                obj.add(NodeSkeleton(int(idx), KSamplerAdvanced.set(node_skeleton)))
            elif class_type == "VAELoader":
                obj.add(NodeSkeleton(int(idx), VAELoader.set(node_skeleton)))
            elif class_type == "VAEDecode":
                obj.add(NodeSkeleton(int(idx), VAEDecode.set(node_skeleton)))
            elif class_type == "VAEEncode":
                obj.add(NodeSkeleton(int(idx), VAEEncode.set(node_skeleton)))
            elif class_type == "LoadImage":
                obj.add(NodeSkeleton(int(idx), LoadImage.set(node_skeleton)))
            elif class_type == "SaveImage":
                obj.add(NodeSkeleton(int(idx), SaveImage.set(node_skeleton)))
            elif class_type == "PreviewImage":
                obj.add(NodeSkeleton(int(idx), PreviewImage.set(node_skeleton)))
            else:
                print(f"Invalid class_type: {class_type}")
        return obj


class Txt2ImgWorkFlow(WorkFlow):
    """
    txt2img に相当するワークフロー
    """

    def __init__(
        self,
        ckpt_name: str = None,
        width: int = None,
        height: int = None,
        batch_size: int = None,
        pos_prompt: str = None,
        neg_prompt: str = None,
        seed: int = None,
        steps: int = None,
    ):
        """
        コンストラクタ
        """
        super().__init__()

        if (
            ckpt_name is None
            or width is None
            or height is None
            or batch_size is None
            or pos_prompt is None
            or neg_prompt is None
            or seed is None
            or steps is None
        ):
            return

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

    @property
    def positive_prompt(self) -> str:
        return cast(CLIPTextEncode.Inputs, self.node_of(3).body.inputs).text

    @property
    def negative_prompt(self) -> str:
        return cast(CLIPTextEncode.Inputs, self.node_of(4).body.inputs).text

    @property
    def steps(self) -> int:
        return cast(KSampler.Inputs, self.node_of(5).body.inputs).steps

    @property
    def sampler(self) -> str:
        return cast(KSampler.Inputs, self.node_of(5).body.inputs).sampler_name

    @property
    def scheduler(self) -> str:
        return cast(KSampler.Inputs, self.node_of(5).body.inputs).scheduler

    @property
    def cfg_scale(self) -> float:
        return cast(KSampler.Inputs, self.node_of(5).body.inputs).cfg

    @property
    def seed(self) -> int:
        return cast(KSampler.Inputs, self.node_of(5).body.inputs).seed

    @property
    def width(self) -> int:
        return cast(EmptyLatentImage.Inputs, self.node_of(2).body.inputs).width

    @property
    def height(self) -> int:
        return cast(EmptyLatentImage.Inputs, self.node_of(2).body.inputs).height

    @property
    def model_name(self) -> str:
        return cast(CheckpointLoaderSimple.Inputs, self.node_of(1).body.inputs).ckpt_name

    @property
    def clip_skip(self) -> int:
        return 0
