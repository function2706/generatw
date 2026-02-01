import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
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

    class_type: str = "CheckpointLoaderSimple"
    inputs: Inputs = None

    @classmethod
    def make(cls, ckpt_name: str):
        return cls(inputs=CheckpointLoaderSimple.Inputs(ckpt_name=ckpt_name))

    @classmethod
    def set(cls, data: dict[str, dict[str, Any]]):
        if data.get("class_type") != cls.class_type:
            raise ValueError
        data_inputs = data.get("inputs")
        return cls(inputs=CheckpointLoaderSimple.Inputs(ckpt_name=data_inputs.get("ckpt_name")))


@dataclass
class EmptyLatentImage(NodeBody):
    @dataclass
    class Inputs:
        width: int = 0
        height: int = 0
        batch_size: int = 0

    class_type: str = "EmptyLatentImage"
    inputs: Inputs = None

    @classmethod
    def make(cls, width: int, height: int, batch_size: int):
        return cls(
            inputs=EmptyLatentImage.Inputs(width=width, height=height, batch_size=batch_size)
        )

    @classmethod
    def set(cls, data: dict[str, dict[str, Any]]):
        if data.get("class_type") != cls.class_type:
            raise ValueError
        data_inputs = data.get("inputs")
        return cls(
            inputs=EmptyLatentImage.Inputs(
                width=int(data_inputs.get("width")),
                height=int(data_inputs.get("height")),
                batch_size=int(data_inputs.get("batch_size")),
            )
        )


@dataclass
class CLIPSetLastLayer(NodeBody):
    @dataclass
    class Inputs:
        stop_at_clip_layer: int = ""
        clip: list[int | str] = field(default_factory=list)

        @classmethod
        def make(cls, stop_at_clip_layer: str, loader: NodeSkeleton = None):
            return cls(
                stop_at_clip_layer=stop_at_clip_layer,
                clip=[loader.nodeidx, 1] if loader is not None else [],
            )

    class_type: str = "CLIPSetLastLayer"
    inputs: Inputs = None

    @classmethod
    def make(cls, stop_at_clip_layer: int, loader: NodeSkeleton):
        if not isinstance(loader.body, CheckpointLoaderSimple):
            raise TypeError

        return cls(
            inputs=CLIPSetLastLayer.Inputs.make(
                stop_at_clip_layer=stop_at_clip_layer, loader=loader
            )
        )

    @classmethod
    def set(cls, data: dict[str, dict[str, Any]]):
        if data.get("class_type") != cls.class_type:
            raise ValueError
        data_inputs = data.get("inputs")
        return cls(
            inputs=CLIPSetLastLayer.Inputs.make(
                stop_at_clip_layer=int(data_inputs.get("stop_at_clip_layer"))
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
    def set(cls, data: dict[str, dict[str, Any]]):
        if data.get("class_type") != cls.class_type:
            raise ValueError
        data_inputs = data.get("inputs")
        return cls(inputs=CLIPTextEncode.Inputs.make(text=data_inputs.get("text")))


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
            samples: NodeSkeleton = None,
        ):
            return cls(
                upscale_method=upscale_method,
                width=width,
                height=height,
                crop=crop,
                samples=[samples.nodeidx, 0] if samples is not None else [],
            )

    class_type: str = "LatentUpscale"
    inputs: Inputs = None

    @classmethod
    def make(
        cls,
        upscale_method: str,
        width: int,
        height: int,
        crop: bool,
        samples: NodeSkeleton,
    ):
        if not isinstance(samples.body, KSampler | KSamplerAdvanced | VAEEncode):
            raise TypeError

        return cls(
            inputs=LatentUpscale.Inputs.make(
                upscale_method=upscale_method,
                width=width,
                height=height,
                crop="disabled" if not crop else "enabled",
                samples=samples,
            )
        )

    @classmethod
    def set(cls, data: dict[str, dict[str, Any]]):
        if data.get("class_type") != cls.class_type:
            raise ValueError
        data_inputs = data.get("inputs")
        return cls(
            inputs=LatentUpscale.Inputs.make(
                upscale_method=data_inputs.get("upscale_method"),
                width=int(data_inputs.get("width")),
                height=int(data_inputs.get("height")),
                crop=data_inputs.get("crop"),
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
            samples: NodeSkeleton = None,
        ):
            return cls(
                upscale_method=upscale_method,
                scale_by=scale_by,
                samples=[samples.nodeidx, 0] if samples is not None else [],
            )

    class_type: str = "LatentUpscaleBy"
    inputs: Inputs = None

    @classmethod
    def make(
        cls,
        upscale_method: str,
        scale_by: float,
        samples: NodeSkeleton,
    ):
        if not isinstance(samples.body, KSampler | KSamplerAdvanced | VAEEncode):
            raise TypeError

        return cls(
            inputs=LatentUpscaleBy.Inputs.make(
                upscale_method=upscale_method,
                scale_by=scale_by,
                samples=samples,
            )
        )

    @classmethod
    def set(cls, data: dict[str, dict[str, Any]]):
        if data.get("class_type") != cls.class_type:
            raise ValueError
        data_inputs = data.get("inputs")
        return cls(
            inputs=LatentUpscaleBy.Inputs.make(
                upscale_method=data_inputs.get("upscale_method"),
                scale_by=float(data_inputs.get("scale_by")),
            )
        )


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
        sampler_name: str,
        scheduler: str,
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
                sampler_name=sampler_name,
                scheduler=scheduler,
                loader=loader,
                latent_image=latent_image,
                positive=positive,
                negative=negative,
            )
        )

    @classmethod
    def set(cls, data: dict[str, dict[str, Any]]):
        if data.get("class_type") != cls.class_type:
            raise ValueError
        data_inputs = data.get("inputs")
        return cls(
            inputs=KSampler.Inputs.make(
                seed=int(data_inputs.get("seed")),
                steps=int(data_inputs.get("steps")),
                cfg=float(data_inputs.get("cfg")),
                denoise=float(data_inputs.get("denoise")),
                sampler_name=data_inputs.get("sampler_name"),
                scheduler=data_inputs.get("scheduler"),
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
            sampler_name: str,
            scheduler: str,
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
    def set(cls, data: dict[str, dict[str, Any]]):
        if data.get("class_type") != cls.class_type:
            raise ValueError
        data_inputs = data.get("inputs")
        return cls(
            inputs=KSamplerAdvanced.Inputs.make(
                seed=int(data_inputs.get("seed")),
                steps=int(data_inputs.get("steps")),
                cfg=float(data_inputs.get("cfg")),
                sampler_name=data_inputs.get("sampler_name"),
                scheduler=data_inputs.get("scheduler"),
                start_at_step=int(data_inputs.get("start_at_step")),
                end_at_step=int(data_inputs.get("end_at_step")),
                add_noise=True if data_inputs.get("add_noise") == "true" else False,
                return_with_leftover_noise=True
                if data_inputs.get("return_with_leftover_noise") == "true"
                else False,
            )
        )


@dataclass
class VAELoader(NodeBody):
    @dataclass
    class Inputs:
        vae_name: str = ""

    class_type: str = "VAELoader"
    inputs: Inputs = None

    @classmethod
    def make(cls, vae_name: str):
        return cls(inputs=VAELoader.Inputs(vae_name=vae_name))

    @classmethod
    def set(cls, data: dict[str, dict[str, Any]]):
        if data.get("class_type") != cls.class_type:
            raise ValueError
        data_inputs = data.get("inputs")
        return cls(inputs=VAELoader.Inputs(vae_name=data_inputs.get("vae_name")))


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
    def set(cls, data: dict[str, dict[str, Any]]):
        if data.get("class_type") != cls.class_type:
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
                vae=[vae.nodeidx, 2] if vae is not None else [],
            )

    class_type: str = "VAEEncode"
    inputs: Inputs = None

    @classmethod
    def make(cls, image: NodeSkeleton, vae: NodeSkeleton):
        if not isinstance(image.body, LoadImage | UnlimitLoadImage) or not isinstance(
            vae.body, CheckpointLoaderSimple | VAELoader
        ):
            raise TypeError

        return cls(inputs=VAEEncode.Inputs.make(image=image, vae=vae))

    @classmethod
    def set(cls, data: dict[str, dict[str, Any]]):
        if data.get("class_type") != cls.class_type:
            raise ValueError
        return cls(inputs=VAEEncode.Inputs.make())


@dataclass
class LoadImage(NodeBody):
    @dataclass
    class Inputs:
        image: str = ""

    class_type: str = "LoadImage"
    inputs: Inputs = None

    @classmethod
    def make(cls, image: str):
        return cls(inputs=LoadImage.Inputs(image=image))

    @classmethod
    def set(cls, data: dict[str, dict[str, Any]]):
        if data.get("class_type") != cls.class_type:
            raise ValueError
        data_inputs = data.get("inputs")
        return cls(inputs=LoadImage.Inputs(image=data_inputs.get("image")))


@dataclass
class UnlimitLoadImage(NodeBody):
    @dataclass
    class Inputs:
        path: str = ""

    class_type: str = "UnlimitLoadImage"
    inputs: Inputs = None

    @classmethod
    def make(cls, path: str):
        return cls(inputs=UnlimitLoadImage.Inputs(path=path))

    @classmethod
    def set(cls, data: dict[str, dict[str, Any]]):
        if data.get("class_type") != cls.class_type:
            raise ValueError
        data_inputs = data.get("inputs")
        return cls(inputs=UnlimitLoadImage.Inputs(path=data_inputs.get("path")))


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
    def set(cls, data: dict[str, dict[str, Any]]):
        if data.get("class_type") != cls.class_type:
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
    def set(cls, data: dict[str, dict[str, Any]]):
        if data.get("class_type") != cls.class_type:
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
            elif class_type == "CLIPSetLastLayer":
                obj.add(NodeSkeleton(int(idx), CLIPSetLastLayer.set(node_skeleton)))
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
            elif class_type == "UnlimitLoadImage":
                obj.add(NodeSkeleton(int(idx), UnlimitLoadImage.set(node_skeleton)))
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
        pos_prompt: str = None,
        neg_prompt: str = None,
        seed: int = None,
        steps: int = None,
        batch_size: int = None,
        sampler_name: str = None,
        scheduler: str = None,
        cfg_scale: float = None,
        width: int = None,
        height: int = None,
    ):
        """
        コンストラクタ
        """
        super().__init__()

        self.ckpt_loader_idx = 1
        self.empty_latent_idx = 2
        self.clip_layer_setter_idx = 3
        self.positive_clip_idx = 4
        self.negatice_clip_idx = 5
        self.sampler_idx = 6
        self.vae_decoder_idx = 7
        self.previewer_idx = 8

        if (
            ckpt_name is None
            or pos_prompt is None
            or neg_prompt is None
            or seed is None
            or steps is None
            or batch_size is None
            or sampler_name is None
            or scheduler is None
            or cfg_scale is None
            or width is None
            or height is None
        ):
            return

        self.add(
            NodeSkeleton(self.ckpt_loader_idx, CheckpointLoaderSimple.make(ckpt_name=ckpt_name))
        )
        self.add(
            NodeSkeleton(
                self.empty_latent_idx,
                EmptyLatentImage.make(width=width, height=height, batch_size=batch_size),
            )
        )
        self.add(
            NodeSkeleton(
                self.clip_layer_setter_idx,
                CLIPSetLastLayer.make(
                    stop_at_clip_layer=-2, loader=self.node_of(self.ckpt_loader_idx)
                ),
            )
        )
        self.add(
            NodeSkeleton(
                self.positive_clip_idx,
                CLIPTextEncode.make(text=pos_prompt, loader=self.node_of(self.ckpt_loader_idx)),
            )
        )
        self.add(
            NodeSkeleton(
                self.negatice_clip_idx,
                CLIPTextEncode.make(text=neg_prompt, loader=self.node_of(self.ckpt_loader_idx)),
            )
        )
        self.add(
            NodeSkeleton(
                self.sampler_idx,
                KSampler.make(
                    seed=seed,
                    steps=steps,
                    cfg=cfg_scale,
                    denoise=1.0,
                    sampler_name=sampler_name,
                    scheduler=scheduler,
                    loader=self.node_of(self.ckpt_loader_idx),
                    latent_image=self.node_of(self.empty_latent_idx),
                    positive=self.node_of(self.positive_clip_idx),
                    negative=self.node_of(self.negatice_clip_idx),
                ),
            ),
        )
        self.add(
            NodeSkeleton(
                self.vae_decoder_idx,
                VAEDecode.make(
                    sampler=self.node_of(self.sampler_idx), vae=self.node_of(self.ckpt_loader_idx)
                ),
            )
        )
        self.add(
            NodeSkeleton(
                self.previewer_idx, PreviewImage.make(vaedec=self.node_of(self.vae_decoder_idx))
            )
        )

    @property
    def positive_prompt(self) -> str:
        return cast(CLIPTextEncode.Inputs, self.node_of(self.positive_clip_idx).body.inputs).text

    @property
    def negative_prompt(self) -> str:
        return cast(CLIPTextEncode.Inputs, self.node_of(self.negatice_clip_idx).body.inputs).text

    @property
    def steps(self) -> int:
        return cast(KSampler.Inputs, self.node_of(self.sampler_idx).body.inputs).steps

    @property
    def sampler(self) -> str:
        return cast(KSampler.Inputs, self.node_of(self.sampler_idx).body.inputs).sampler_name

    @property
    def scheduler(self) -> str:
        return cast(KSampler.Inputs, self.node_of(self.sampler_idx).body.inputs).scheduler

    @property
    def cfg_scale(self) -> float:
        return cast(KSampler.Inputs, self.node_of(self.sampler_idx).body.inputs).cfg

    @property
    def seed(self) -> int:
        return cast(KSampler.Inputs, self.node_of(self.sampler_idx).body.inputs).seed

    @property
    def width(self) -> int:
        return cast(EmptyLatentImage.Inputs, self.node_of(self.empty_latent_idx).body.inputs).width

    @property
    def height(self) -> int:
        return cast(EmptyLatentImage.Inputs, self.node_of(self.empty_latent_idx).body.inputs).height

    @property
    def model_name(self) -> str:
        return cast(
            CheckpointLoaderSimple.Inputs, self.node_of(self.ckpt_loader_idx).body.inputs
        ).ckpt_name

    @property
    def clip_skip(self) -> int:
        return -cast(
            CLIPSetLastLayer.Inputs, self.node_of(self.clip_layer_setter_idx).body.inputs
        ).stop_at_clip_layer


class Img2ImgWorkFlow(WorkFlow):
    """
    img2img に相当するワークフロー
    """

    def __init__(
        self,
        ckpt_name: str = None,
        path: str = None,
        pos_prompt: str = None,
        neg_prompt: str = None,
        seed: int = None,
        steps: int = None,
        batch_size: int = None,
        sampler_name: str = None,
        scheduler: str = None,
        upscaler: str = None,
        cfg_scale: float = None,
        denoise: float = None,
        width: int = None,
        height: int = None,
    ):
        """
        コンストラクタ
        """
        super().__init__()

        self.ckpt_loader_idx = 1
        self.image_loader_idx = 2
        self.vae_encoder_idx = 3
        self.clip_layer_setter_idx = 4
        self.positive_clip_idx = 5
        self.negative_clip_idx = 6
        self.latent_upscaler_idx = 7
        self.sampler_idx = 8
        self.vae_decoder_idx = 9
        self.previewer_idx = 10

        if (
            ckpt_name is None
            or path is None
            or pos_prompt is None
            or neg_prompt is None
            or seed is None
            or steps is None
            or batch_size is None
            or sampler_name is None
            or scheduler is None
            or upscaler is None
            or cfg_scale is None
            or denoise is None
            or width is None
            or height is None
        ):
            return

        self.add(
            NodeSkeleton(self.ckpt_loader_idx, CheckpointLoaderSimple.make(ckpt_name=ckpt_name))
        )
        self.add(
            NodeSkeleton(
                self.image_loader_idx, UnlimitLoadImage.make(path=str(Path(path).resolve()))
            )
        )
        self.add(
            NodeSkeleton(
                self.vae_encoder_idx,
                VAEEncode.make(
                    image=self.node_of(self.image_loader_idx),
                    vae=self.node_of(self.ckpt_loader_idx),
                ),
            )
        )
        self.add(
            NodeSkeleton(
                self.clip_layer_setter_idx,
                CLIPSetLastLayer.make(
                    stop_at_clip_layer=-2, loader=self.node_of(self.ckpt_loader_idx)
                ),
            )
        )
        self.add(
            NodeSkeleton(
                self.positive_clip_idx,
                CLIPTextEncode.make(text=pos_prompt, loader=self.node_of(self.ckpt_loader_idx)),
            )
        )
        self.add(
            NodeSkeleton(
                self.negative_clip_idx,
                CLIPTextEncode.make(text=neg_prompt, loader=self.node_of(self.ckpt_loader_idx)),
            )
        )
        self.add(
            NodeSkeleton(
                self.latent_upscaler_idx,
                LatentUpscale.make(
                    upscale_method=upscaler,
                    width=width,
                    height=height,
                    crop=False,
                    samples=self.node_of(self.vae_encoder_idx),
                ),
            )
        )
        self.add(
            NodeSkeleton(
                self.sampler_idx,
                KSampler.make(
                    seed=seed,
                    steps=steps,
                    cfg=cfg_scale,
                    denoise=denoise,
                    sampler_name=sampler_name,
                    scheduler=scheduler,
                    loader=self.node_of(self.ckpt_loader_idx),
                    latent_image=self.node_of(self.latent_upscaler_idx),
                    positive=self.node_of(self.positive_clip_idx),
                    negative=self.node_of(self.negative_clip_idx),
                ),
            ),
        )
        self.add(
            NodeSkeleton(
                self.vae_decoder_idx,
                VAEDecode.make(
                    sampler=self.node_of(self.sampler_idx), vae=self.node_of(self.ckpt_loader_idx)
                ),
            )
        )
        self.add(
            NodeSkeleton(
                self.previewer_idx, PreviewImage.make(vaedec=self.node_of(self.vae_decoder_idx))
            )
        )

    @property
    def ancestor(self) -> str:
        return cast(UnlimitLoadImage.Inputs, self.node_of(self.image_loader_idx).body.inputs).path

    @property
    def positive_prompt(self) -> str:
        return cast(CLIPTextEncode.Inputs, self.node_of(self.positive_clip_idx).body.inputs).text

    @property
    def negative_prompt(self) -> str:
        return cast(CLIPTextEncode.Inputs, self.node_of(self.negative_clip_idx).body.inputs).text

    @property
    def steps(self) -> int:
        return cast(KSampler.Inputs, self.node_of(self.sampler_idx).body.inputs).steps

    @property
    def sampler(self) -> str:
        return cast(KSampler.Inputs, self.node_of(self.sampler_idx).body.inputs).sampler_name

    @property
    def scheduler(self) -> str:
        return cast(KSampler.Inputs, self.node_of(self.sampler_idx).body.inputs).scheduler

    @property
    def cfg_scale(self) -> float:
        return cast(KSampler.Inputs, self.node_of(self.sampler_idx).body.inputs).cfg

    @property
    def seed(self) -> int:
        return cast(KSampler.Inputs, self.node_of(self.sampler_idx).body.inputs).seed

    @property
    def upscaler(self) -> str:
        return cast(
            LatentUpscale.Inputs, self.node_of(self.latent_upscaler_idx).body.inputs
        ).upscale_method

    @property
    def width(self) -> int:
        return cast(LatentUpscale.Inputs, self.node_of(self.latent_upscaler_idx).body.inputs).width

    @property
    def height(self) -> int:
        return cast(LatentUpscale.Inputs, self.node_of(self.latent_upscaler_idx).body.inputs).height

    @property
    def model_name(self) -> str:
        return cast(
            CheckpointLoaderSimple.Inputs, self.node_of(self.ckpt_loader_idx).body.inputs
        ).ckpt_name

    @property
    def clip_skip(self) -> int:
        return -cast(
            CLIPSetLastLayer.Inputs, self.node_of(self.clip_layer_setter_idx).body.inputs
        ).stop_at_clip_layer
