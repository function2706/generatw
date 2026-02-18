"""
各モジュールの横断処理を統括するクラス
"""

from __future__ import annotations

import tkinter
from dataclasses import dataclass
from pathlib import Path

import yaml

from archiver.archiver import Archiver
from archiver.dataclasses import NoImageStats, PicStats
from common.functions import BackEnd, BottleMail, dump_json
from displayer.dataclasses import GUIConfigs
from displayer.displayer import Displayer
from generator.a1111_generator import A1111Generator
from generator.comfyui_generator import ComfyUIGenerator
from generator.dataclasses import (
    SamplerName,
    SchedulerName,
    TaskBlueprintImg2Img,
    TaskBlueprintTxt2Img,
    UpScalerName,
)
from master.events import (
    ArchiverEvent,
    ChangeTasks,
    DisplayerEvent,
    GeneratorEvent,
    NewPicStats,
    NewProgress,
    NewPrompts,
    OnBackward,
    OnChangeConfig,
    OnDebug,
    OnDelete,
    OnDumpArchiver,
    OnDumpTaskList,
    OnFlushTasks,
    OnForward,
    OnInterruptTask,
    OnRepeatTask,
    OnSelectYaml,
    OnSwitchBackend,
    OnUpscale,
    ParserEvent,
    TaskComplete,
    TaskStart,
)
from master.interfaces import MasterIF
from parser.parser import Parser
from parser.test_parser import KEYWORD_TEST_PARSER, TestParser
from parser.theworld_parser import KEYWORD_THE_WORLD_PARSER, TheWorldParser

PARSER_KEYWORD_TBL = {
    KEYWORD_TEST_PARSER: TestParser,
    KEYWORD_THE_WORLD_PARSER: TheWorldParser,
}


@dataclass(frozen=True)
class Consts:
    config_path: Path = Path("config.json")


class Master(MasterIF):
    """
    各モジュールの横断処理を統括するクラス
    """

    def __init__(self):
        """
        コンストラクタ

        Args:
            stats (Stats): ステータスインスタンス
        """
        self.root = tkinter.Tk()
        self.after_id: str = ""

        self.from_archiver: BottleMail[ArchiverEvent] = BottleMail()
        self.from_displayer: BottleMail[DisplayerEvent] = BottleMail()
        self.from_generator: BottleMail[GeneratorEvent] = BottleMail()
        self.from_parser: BottleMail[ParserEvent] = BottleMail()

        self.crnt_configs: GUIConfigs = (
            GUIConfigs.fromjson(Consts.config_path)
            if Consts.config_path.exists()
            else GUIConfigs(
                # コンフィグファイルがない場合は A1111 をバックエンドとして起動
                srv_ipaddr="127.0.0.1",
                srv_port=str(7860),
                sd_steps=30,
                sd_batch_size=2,
                sd_width=540,
                sd_height=960,
                yamlpath=None,
                backend=BackEnd.a1111.value,
                allow_edit_clipboard=False,
                print_new_clipboard=False,
                print_new_prompt=False,
                print_picinfo=False,
                print_event=False,
            )
        )

        self.parser: Parser | None = None
        self.is_switching_frontend = False
        if self.crnt_configs.yamlpath is not None:
            self.switch_frontend(Path(self.crnt_configs.yamlpath))

        self.archiver = Archiver(self.from_archiver)

        self.backend: BackEnd = (
            BackEnd.a1111 if self.crnt_configs.backend == BackEnd.a1111.value else BackEnd.comfy_ui
        )
        if self.backend == BackEnd.a1111:
            self.generator = A1111Generator(self, self.from_generator)
        elif self.backend == BackEnd.comfy_ui:
            self.generator = ComfyUIGenerator(self, self.from_generator)
        else:
            raise ValueError
        self.is_switching_backend = False

        self.displayer = Displayer(self, self.from_displayer, self.crnt_configs)

        self.generator.start()

    def start(self) -> None:
        """
        メインループの開始
        """
        self.after_id = self.root.after(100, self.run_main)
        self.root.mainloop()

    def finalize(self) -> None:
        """
        終了処理
        """

        self.crnt_configs.tojson(Consts.config_path)

        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = ""

        self.generator.finalize()
        if self.parser is not None:
            self.parser.finalize()

        def worker():
            self.generator.join()
            if self.parser is not None:
                self.parser.join()
            self.displayer.destroy()
            self.archiver.finalize()

        self.root.after(100, worker)

    def sigint_handler(self, sig, frame) -> None:
        """
        SIGINT ハンドラ

        Args:
            sig (_type_): シグナル
            frame (_type_): Tkinter フレーム
        """
        self.finalize()

    def operate_from_archiver(self) -> None:
        """
        Archiver から発行されたイベントに即して作業を実施する\n
        本関数は一度の呼び出しで, その時点までに登録されている全イベントをこなす\n
        本関数は tkinter のメインループで呼び出すこと
        """
        self.archiver.process_reports()
        while True:
            try:
                event = self.from_archiver.pickup()
            except IndexError:
                break

            if self.crnt_gui_configs.print_event:
                print(
                    f"{self.archiver.__class__.__name__:20} > {event.__class__.__name__:20} > ",
                    end="",
                )
            if isinstance(event, NewPicStats):
                if self.crnt_gui_configs.print_event:
                    print("stats=", end="")
                    if event.next_picstats is NoImageStats:
                        print("NoImageStats")
                    elif isinstance(event.next_picstats, PicStats):
                        print(f"{event.next_picstats.name}")
                self.displayer.update_pic_window(event.next_picstats)

    def search_parser_with_keyword(self, keyword: str) -> type[Parser] | None:
        if keyword is None:
            return None

        for kwd, parser in PARSER_KEYWORD_TBL.items():
            if kwd == keyword:
                return parser

        return None

    def switch_frontend(self, new_yamlpath: Path) -> None:
        """
        フロントエンドの切り替えを行う

        Args:
            new_yamlpath (Path): 新しい YAML パス
        """
        if self.is_switching_frontend:
            return

        self.is_switching_frontend = True

        keyword = None
        with open(new_yamlpath, "r", encoding="utf-8") as f:
            yamldict: dict = yaml.safe_load(f)
            keyword = yamldict.get("parser")

        old = None
        if self.parser is not None:
            old = self.parser
            old.finalize()

        def worker():
            if old is not None:
                old.join()

            parser_cls = self.search_parser_with_keyword(keyword)
            if parser_cls is not None:
                self.parser = parser_cls(self, self.from_parser)
                self.parser.reset_prompter(new_yamlpath)
                self.parser.start()

            self.is_switching_frontend = False

        self.root.after(0, worker)

    def switch_backend(self, new_backend: BackEnd) -> None:
        """
        バックエンドの切り替えを行う

        Args:
            new_backend (BackEnd): 新しいバックエンド
        """
        if self.is_switching_backend:
            return

        self.is_switching_backend = True

        old = self.generator
        old.finalize()

        def worker():
            old.join()

            self.backend = new_backend
            self.generator = (
                A1111Generator(self, self.from_generator)
                if new_backend == BackEnd.a1111
                else ComfyUIGenerator(self, self.from_generator)
            )

            self.generator.start()
            self.is_switching_backend = False

        self.root.after(0, worker)

    def operate_from_displayer(self) -> None:
        """
        Displayer から発行されたイベントに即して作業を実施する\n
        本関数は一度の呼び出しで, その時点までに登録されている全イベントをこなす\n
        本関数は tkinter のメインループで呼び出すこと
        """
        while True:
            try:
                event = self.from_displayer.pickup()
            except IndexError:
                break

            if self.crnt_gui_configs.print_event:
                print(f"{self.displayer.__class__.__name__:20} > {event.__class__.__name__:20}")
            if isinstance(event, OnRepeatTask):
                self.reserve_txt2img_task()
            if isinstance(event, OnInterruptTask):
                self.generator.reserve_interrupt()
            if isinstance(event, OnFlushTasks):
                self.generator.clear()
            if isinstance(event, OnSelectYaml):
                self.switch_frontend(Path(event.path))
            if isinstance(event, OnDebug):
                if self.parser is not None:
                    self.parser.ready_for_debug()
            if isinstance(event, OnDumpArchiver):
                dump_json(self.archiver.archive.todict(), "archiver")
            if isinstance(event, OnDumpTaskList):
                dump_json(self.generator.crnt_tasklist(), "tasks")
            if isinstance(event, OnBackward):
                self.archiver.backward_picstats()
            if isinstance(event, OnForward):
                self.archiver.forward_picstats()
            if isinstance(event, OnUpscale):
                self.reserve_img2img_task()
            if isinstance(event, OnDelete):
                self.archiver.remove_crnt_picstats()
            if isinstance(event, OnChangeConfig):
                self.crnt_configs = event.new_config
            if isinstance(event, OnSwitchBackend):
                self.switch_backend(event.new_backend)

    def operate_from_generator(self) -> None:
        """
        Generator から発行されたイベントに即して作業を実施する\n
        本関数は一度の呼び出しで, その時点までに登録されている全イベントをこなす\n
        本関数は tkinter のメインループで呼び出すこと
        """
        while True:
            try:
                event = self.from_generator.pickup()
            except IndexError:
                break

            if self.crnt_gui_configs.print_event:
                print(
                    f"{self.generator.__class__.__name__:20} > {event.__class__.__name__:20} > ",
                    end="",
                )
            if isinstance(event, TaskStart):
                if self.crnt_gui_configs.print_event:
                    prompt = event.new_task.prompt[:27] + "..."
                    if isinstance(event.new_task, TaskBlueprintTxt2Img):
                        print(f"txt2img, prompt={prompt}")
                    elif isinstance(event.new_task, TaskBlueprintImg2Img):
                        print(f"img2img, prompt={prompt}")
                self.displayer.info_window.update_taskinfo_tab(task=event.new_task)
            if isinstance(event, NewProgress):
                if self.crnt_gui_configs.print_event:
                    print(f"progress={event.progress}")
                self.displayer.info_window.update_taskinfo_tab(progress=event.progress)
            if isinstance(event, ChangeTasks):
                if self.crnt_gui_configs.print_event:
                    print(f"tasks={event.tasks}")
                self.displayer.info_window.update_taskinfo_tab(tasks=event.tasks)
            if isinstance(event, TaskComplete):
                if self.crnt_gui_configs.print_event:
                    print("OK")
                self.displayer.info_window.update_taskinfo_tab(done=True)
                if self.displayer.pic_window.event.outputting_noimage.is_set():
                    self.refresh_pic_randomly(construct_window=True)

    def operate_from_parser(self) -> None:
        """
        Parser から発行されたイベントに即して作業を実施する\n
        本関数は一度の呼び出しで, その時点までに登録されている全イベントをこなす\n
        本関数は tkinter のメインループで呼び出すこと
        """
        while True:
            try:
                event = self.from_parser.pickup()
            except IndexError:
                break

            if self.crnt_gui_configs.print_event and self.parser is not None:
                print(
                    f"{self.parser.__class__.__name__:20} > {event.__class__.__name__:20} > ",
                    end="",
                )
            if isinstance(event, NewPrompts):
                if self.crnt_gui_configs.print_event:
                    print(f"enough={event.is_enough}")
                if event.is_enough:
                    self.run_oneshot()
                else:
                    self.archiver.drop_picstats()

    @property
    def backend_type(self) -> BackEnd:
        """
        バックエンドタイプ

        Returns:
            BackEnd: バックエンドタイプ
        """
        return self.backend

    @property
    def backend_name(self) -> str:
        """
        バックエンド名

        Returns:
            str: バックエンド名
        """
        return self.backend.value

    @property
    def crnt_gui_configs(self) -> GUIConfigs:
        """
        現在の GUI 上の設定値

        Returns:
            CrntGUIConfigs: 現在の GUI 上の設定値
        """
        return self.crnt_configs

    def reserve_img2img_task(self) -> None:
        """
        アップスケール予約ボタンハンドラ
        """
        if self.archiver.crnt_picstats_copy is NoImageStats or self.is_switching_backend:
            return

        self.generator.reserve_img2img(
            picstats=self.archiver.crnt_picstats_copy,
            stps=self.crnt_configs.sd_steps,
            smplr=SamplerName.dpmpp_2m_sde_gpu
            if self.backend == BackEnd.comfy_ui
            else SamplerName.dpmpp_2m_sde,
            schdlr=SchedulerName.karras,
            cfg=7.0,
            scaleby=1.2,
            denoise=0.65,
            d_addr=self.crnt_configs.srv_ipaddr,
            d_port=self.crnt_configs.srv_port,
            resize_mode=3 if self.backend_type == BackEnd.a1111 else None,
            upsclr=UpScalerName.nearest_exact if self.backend_type == BackEnd.comfy_ui else None,
        )

    def reserve_txt2img_task(self) -> None:
        """
        新しいタスクを生成し, タスクリストに予約する\n
        ただしプロンプト生成に十分なステータスが記録されていない,\n
        すでにリストに存在する, あるいは作業中のタスクの場合は何もしない
        """
        if self.parser is None or not self.parser.is_enough_prompt() or self.is_switching_backend:
            return

        pos, neg = self.parser.make_prompt_strs()
        self.generator.reserve_txt2img(
            pos=pos,
            neg=neg,
            seed=-1,
            stps=self.crnt_configs.sd_steps,
            b_size=self.crnt_configs.sd_batch_size,
            smplr=SamplerName.dpmpp_2m,
            schdlr=SchedulerName.karras,
            cfg=7.0,
            w=self.crnt_configs.sd_width,
            h=self.crnt_configs.sd_height,
            d_addr=self.crnt_configs.srv_ipaddr,
            d_port=self.crnt_configs.srv_port,
        )

    def refresh_pic_randomly(self, construct_window=False) -> None:
        """
        現在の記録中ステータスにおいて, 表示可能な画像が存在する場合にランダムで表示する\n
        存在しない場合は NO IMAGE を表示する
        """
        if self.parser is None:
            return

        if construct_window:
            self.displayer.pic_window.construct(fix_position=True)

        if self.archiver.count_files_in(self.parser.crnt_prompt_dir) == 0:
            # 記録中ステータスに紐づくディレクトリ内に画像がない
            self.archiver.drop_picstats()
            return

        self.archiver.warp_picstats(self.parser.crnt_prompt_dir)

    def run_oneshot(self) -> None:
        """
        タスク予約とすでに存在する画像の表示を1度だけ行う
        """
        self.reserve_txt2img_task()
        self.refresh_pic_randomly(construct_window=True)

    def run_main(self) -> None:
        """
        メイン処理 (ステータス更新 -> 更新がある場合にタスクを予約 -> すでに存在する画像を表示)\n
        Tkinter メインループにて周期的に呼び出される処理
        """
        try:
            if not self.root.winfo_exists() or self.is_switching_backend:
                return

            self.operate_from_parser()
            self.operate_from_archiver()
            self.operate_from_displayer()
            self.operate_from_generator()
        except tkinter.TclError:
            return
        finally:
            self.after_id = self.root.after(10, self.run_main)
