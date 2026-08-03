"""
各モジュールの横断処理を統括するクラス
"""

from __future__ import annotations

import tkinter
from dataclasses import dataclass
from pathlib import Path

import master.events
from archiver.archiver import Archiver
from archiver.dataclasses import NoImageStats, PicStats
from character.manager import CharacterManager
from common.functions import BackEnd, BottleMail, PathConsts, dump_json
from displayer.dataclasses import GUIConfigs
from displayer.displayer import Displayer
from generator.a1111_generator import A1111Generator
from generator.comfyui_generator import ComfyUIGenerator
from generator.dataclasses import TaskBlueprintImg2Img, TaskBlueprintTxt2Img
from master.interfaces import MasterIF


@dataclass(frozen=True)
class Consts:
    max_width: int = 1440
    max_height: int = 2560


class Master(MasterIF):
    """
    各モジュールの横断処理を統括するクラス
    """

    def __init__(self):
        """
        コンストラクタ
        """
        self.root = tkinter.Tk()
        self.after_id: str = ""

        self.from_archiver: BottleMail[master.events.ArchiverEvent] = BottleMail()
        self.from_displayer: BottleMail[master.events.DisplayerEvent] = BottleMail()
        self.from_generator: BottleMail[master.events.GeneratorEvent] = BottleMail()

        self.crnt_configs: GUIConfigs = (
            GUIConfigs.fromjson(PathConsts.config_json)
            if PathConsts.config_json.exists()
            else GUIConfigs(
                # コンフィグファイルがない場合は A1111 をバックエンドとして起動
                srv_ipaddr="127.0.0.1",
                srv_port=str(7860),
                sd_steps=30,
                sd_batch_size=2,
                sd_width=540,
                sd_height=960,
                sd_scaleby=2.0,
                each_max_pics=8,
                backend=BackEnd.a1111.value,
            )
        )

        # キャラクター管理 (旧 Parser の役割を置換)
        self.character = CharacterManager(load_state_start=self.crnt_configs.load_state_start)

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

        # キャラ一覧を UI へ反映し, 保存されている選択キャラを復元する
        self.displayer.set_character_list(self.character.metas, self.crnt_configs.crnt_character)
        if self.crnt_configs.crnt_character:
            self.select_character(self.crnt_configs.crnt_character, generate=False)

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
        if self.crnt_configs.save_state_end:
            self.character.save_state()

        self.crnt_configs.tojson(PathConsts.config_json)

        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = ""

        self.generator.finalize()

        def worker():
            self.generator.join()
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

    # ------------------------------------------------------------------ #
    # キャラクター操作
    # ------------------------------------------------------------------ #
    def select_character(self, char_id: str, generate: bool = True) -> None:
        """
        キャラクターを選択し, UI と表示画像を更新する

        Args:
            char_id (str): キャラ ID
            generate (bool): 選択直後に生成タスクを予約するか
        """
        if not self.character.select_character(char_id):
            return

        self.crnt_configs.crnt_character = char_id
        self.displayer.render_character(
            self.character.sheet, self.character.actions, self.character.state
        )
        self.displayer.set_dialogue(self.character.sheet.display_name, "", locked=False)

        if generate:
            strs = self.character.crnt_strs
            if strs is not None:
                self.run_oneshot(strs[0], strs[1])
        else:
            self.refresh_pic_randomly(construct_window=True)

    def reload_character(self) -> None:
        """
        選択中キャラのシート/アクションを再読み込みして UI を更新する
        """
        self.displayer.set_character_list(
            self.character.metas, self.character.char_id
        )
        if self.character.reload_current():
            self.displayer.render_character(
                self.character.sheet, self.character.actions, self.character.state
            )
            self.refresh_pic_randomly(construct_window=True)

    def do_action(self, action_id: str, wardrobe_key: str | None) -> None:
        """
        アクションを適用し, 状態表示・セリフ・画像生成を更新する

        Args:
            action_id (str): アクション ID
            wardrobe_key (str | None): 着せ替え先の衣装キー
        """
        result = self.character.apply_action(action_id, wardrobe_key=wardrobe_key)
        if result is None:
            return

        self.displayer.update_state_view(self.character.sheet, self.character.state)
        self.displayer.set_dialogue(
            self.character.sheet.display_name, result.dialogue, locked=result.locked
        )
        self.run_oneshot(result.positive, result.negative)

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
            if isinstance(event, master.events.NewPicStats):
                if self.crnt_gui_configs.print_event:
                    print("stats=", end="")
                    if event.next_picstats is NoImageStats:
                        print("NoImageStats")
                    elif isinstance(event.next_picstats, PicStats):
                        print(f"{event.next_picstats.name}")
                self.displayer.update_pic_window(event.next_picstats)
            if isinstance(event, master.events.DetectPicsChanges):
                if self.crnt_gui_configs.print_event:
                    print(f"type={event.type}")
                self.displayer.update_main_window(rest_capacity=self.rest_files_in_crnt_dir)

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
            if isinstance(event, master.events.OnSelectCharacter):
                self.select_character(event.char_id)
            if isinstance(event, master.events.OnReloadCharacter):
                self.reload_character()
            if isinstance(event, master.events.OnAction):
                self.do_action(event.action_id, event.wardrobe_key)
            if isinstance(event, master.events.OnSaveState):
                self.character.save_state()
            if isinstance(event, master.events.OnLoadState):
                if self.character.load_state():
                    self.displayer.update_state_view(self.character.sheet, self.character.state)
                    self.refresh_pic_randomly(construct_window=True)
            if isinstance(event, master.events.OnResetState):
                self.character.reset_state()
                if self.character.sheet is not None:
                    self.displayer.update_state_view(self.character.sheet, self.character.state)
                    self.refresh_pic_randomly(construct_window=True)
            if isinstance(event, master.events.OnRepeatTask):
                strs = self.character.crnt_strs
                if strs is not None:
                    self.reserve_txt2img_task(strs[0], strs[1])
            if isinstance(event, master.events.OnInterruptTask):
                self.generator.reserve_interrupt()
            if isinstance(event, master.events.OnFlushTasks):
                self.generator.clear()
            if isinstance(event, master.events.OnFlushTxt2ImgTasks):
                self.generator.clear_of(TaskBlueprintTxt2Img)
            if isinstance(event, master.events.OnFlushImg2ImgTasks):
                self.generator.clear_of(TaskBlueprintImg2Img)
            if isinstance(event, master.events.OnDumpArchiver):
                dump_json(self.archiver.archive.todict(), "archiver")
            if isinstance(event, master.events.OnDumpTaskList):
                dump_json(self.generator.crnt_tasklist(), "tasks")
            if isinstance(event, master.events.OnBackward):
                self.archiver.backward_picstats()
            if isinstance(event, master.events.OnForward):
                self.archiver.forward_picstats()
            if isinstance(event, master.events.OnUpscale):
                self.reserve_img2img_task()
            if isinstance(event, master.events.OnDelete):
                self.archiver.remove_crnt_picstats()
            if isinstance(event, master.events.OnChangeConfig):
                self.crnt_configs = event.new_config
                self.displayer.update_main_window(rest_capacity=self.rest_files_in_crnt_dir)
            if isinstance(event, master.events.OnSwitchBackend):
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
            if isinstance(event, master.events.TaskStart):
                if self.crnt_gui_configs.print_event:
                    prompt = event.new_task.prompt[:27] + "..."
                    if isinstance(event.new_task, TaskBlueprintTxt2Img):
                        print(f"txt2img, prompt={prompt}")
                    elif isinstance(event.new_task, TaskBlueprintImg2Img):
                        print(f"img2img, prompt={prompt}")
                self.displayer.info_window.update_taskinfo_tab(task=event.new_task)
            if isinstance(event, master.events.NewProgress):
                if self.crnt_gui_configs.print_event:
                    print(f"progress={event.progress}")
                self.displayer.info_window.update_taskinfo_tab(progress=event.progress)
            if isinstance(event, master.events.ChangeTasks):
                if self.crnt_gui_configs.print_event:
                    print(f"tasks={event.tasks}")
                self.displayer.info_window.update_taskinfo_tab(tasks=event.tasks)
            if isinstance(event, master.events.TaskComplete):
                if self.crnt_gui_configs.print_event:
                    print("OK")
                self.displayer.info_window.update_taskinfo_tab(done=True)
                if self.displayer.pic_window.event.outputting_noimage.is_set():
                    self.refresh_pic_randomly(construct_window=True)

    @property
    def backend_type(self) -> BackEnd:
        """
        バックエンドタイプ

        Returns:
            BackEnd: バックエンドタイプ
        """
        return self.backend

    @property
    def crnt_gui_configs(self) -> GUIConfigs:
        """
        現在の GUI 上の設定値

        Returns:
            GUIConfigs: 現在の GUI 上の設定値
        """
        return self.crnt_configs

    @property
    def files_in_crnt_dir(self) -> int:
        """
        記録中プロンプトに紐づくディレクトリ内の画像枚数を取得する

        Returns:
            int: 枚数
        """
        return (
            self.archiver.count_files_in(self.character.crnt_prompt_dir)
            if self.character.crnt_prompt_dir is not None
            else None
        )

    @property
    def rest_files_in_crnt_dir(self) -> int:
        """
        記録中プロンプトに紐づくディレクトリの枚数残り容量を取得する

        Returns:
            int: 残り枚数
        """
        if self.files_in_crnt_dir is None:
            return None
        rest = self.crnt_gui_configs.each_max_pics - self.files_in_crnt_dir
        return rest if rest >= 0 else 0

    def reserve_txt2img_task(self, positive: str, negative: str) -> None:
        """
        生成予約\n
        生成数上限到達時, あるいはバックエンド変更中の場合は何もしない\n
        バッチサイズが残り容量より大きい場合, その差だけ生成する(すり切りいっぱい)
        """
        if (
            self.rest_files_in_crnt_dir is not None and self.rest_files_in_crnt_dir <= 0
        ) or self.is_switching_backend:
            self.displayer.update_main_window(rest_capacity=self.rest_files_in_crnt_dir)
            return

        batch_size = (
            self.rest_files_in_crnt_dir
            if (self.rest_files_in_crnt_dir < self.crnt_configs.sd_batch_size)
            else self.crnt_configs.sd_batch_size
        )

        self.generator.reserve_txt2img(
            pos=positive,
            neg=negative,
            stps=self.crnt_configs.sd_steps,
            b_size=batch_size,
            w=self.crnt_configs.sd_width,
            h=self.crnt_configs.sd_height,
            d_addr=self.crnt_configs.srv_ipaddr,
            d_port=self.crnt_configs.srv_port,
        )

    def reserve_img2img_task(self) -> None:
        """
        アップスケール予約ボタンハンドラ\n
        NoImage 表示中, バックエンド変更中,\n
        あるいは拡大後の幅 or 高さが最大値を超過する場合は何もしない
        """
        if (
            self.archiver.crnt_picstats_copy is NoImageStats
            or self.is_switching_backend
            or self.archiver.crnt_picstats_copy.info.width * self.crnt_configs.sd_scaleby
            > Consts.max_width
            or self.archiver.crnt_picstats_copy.info.height * self.crnt_configs.sd_scaleby
            > Consts.max_height
        ):
            return

        self.generator.reserve_img2img(
            picstats=self.archiver.crnt_picstats_copy,
            stps=self.crnt_configs.sd_steps,
            scaleby=self.crnt_configs.sd_scaleby,
            d_addr=self.crnt_configs.srv_ipaddr,
            d_port=self.crnt_configs.srv_port,
        )

    def refresh_pic_randomly(self, construct_window=False) -> None:
        """
        現在の記録中ステータスにおいて, 表示可能な画像が存在する場合にランダムで表示する\n
        存在しない場合は NO IMAGE を表示する
        """
        if not self.character.is_ready:
            return

        if construct_window:
            self.displayer.pic_window.construct(fix_position=True)

        if self.files_in_crnt_dir == 0:
            # 記録中ステータスに紐づくディレクトリ内に画像がない
            self.archiver.drop_picstats()
            return

        self.archiver.warp_picstats(self.character.crnt_prompt_dir)

    def run_oneshot(self, positive: str, negative: str) -> None:
        """
        タスク予約とすでに存在する画像の表示を1度だけ行う
        """
        if not positive and not negative:
            return
        self.reserve_txt2img_task(positive, negative)
        self.refresh_pic_randomly(construct_window=True)

    def run_main(self) -> None:
        """
        メイン処理 (イベント処理 -> タスク予約 -> 画像表示)\n
        Tkinter メインループにて周期的に呼び出される処理
        """
        try:
            if not self.root.winfo_exists() or self.is_switching_backend:
                return

            self.operate_from_archiver()
            self.operate_from_displayer()
            self.operate_from_generator()
        except tkinter.TclError:
            return
        finally:
            self.after_id = self.root.after(10, self.run_main)
