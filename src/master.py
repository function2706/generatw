"""
各モジュールの横断処理を統括するクラス
"""

from __future__ import annotations

import tkinter
from pathlib import Path
from typing import Any

from archiver.archiver import Archiver
from archiver.dataclasses import PicStats
from common.functions import BackEnd, FrontEnd
from common.interfaces import MasterIF
from displayer.displayer import Displayer, GUIConfigs
from generator.a1111_generator import A1111Generator
from generator.comfyui_generator import ComfyUIGenerator
from generator.dataclasses import SamplerName, SchedulerName, TaskBlueprint, UpScalerName
from parser.reverse_parser import ReverseParser
from parser.theworld_parser import TheWorldParser


class Master(MasterIF):
    """
    各モジュールの横断処理を統括するクラス
    """

    def __init__(self, frontend: FrontEnd, backend: BackEnd):
        """
        コンストラクタ

        Args:
            stats (Stats): ステータスインスタンス
        """
        self.root = tkinter.Tk()
        self.after_id: str = ""

        self.frontend: FrontEnd = frontend
        if frontend == FrontEnd.reverse:
            self.parser = ReverseParser(self)
        elif frontend == FrontEnd.the_world:
            self.parser = TheWorldParser(self)
        else:
            raise ValueError

        self.archiver = Archiver(self.parser.pics_dir_path())

        self.backend: BackEnd = backend
        if backend == BackEnd.a1111:
            self.generator = A1111Generator(self)
        elif backend == BackEnd.comfy_ui:
            self.generator = ComfyUIGenerator(self)
        else:
            raise ValueError

        self.displayer = Displayer(self)
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

    @property
    def frontend_type(self) -> FrontEnd:
        """
        フロントエンドタイプ

        Returns:
            FrontEnd: フロントエンドタイプ
        """
        return self.frontend

    @property
    def frontend_name(self) -> str:
        """
        フロントエンド名

        Returns:
            str: フロントエンド名
        """
        return self.parser.whoami()

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
        return self.generator.whoami()

    @property
    def pics_dir_path(self) -> Path:
        """
        画像ディレクトリパスを取得する\n
        (pics/<フロントエンド名>)

        Returns:
            Path: ディレクトリパス
        """
        return self.parser.pics_dir_path()

    @property
    def crnt_gui_configs(self) -> GUIConfigs:
        """
        現在の GUI 上の設定値

        Returns:
            CrntGUIConfigs: 現在の GUI 上の設定値
        """
        return self.displayer.crnt_config

    @property
    def crnt_picstats(self) -> PicStats:
        """
        現在の PicStats

        Returns:
            PicStats: 現在の PicStats
        """
        return self.archiver.crnt_picstats

    @property
    def crnt_archive(self) -> dict[str, Any]:
        """
        現在の Archiver

        Returns:
            dict[str, Any]: 現在の Archiver
        """
        return self.archiver.archive.todict()

    @property
    def crnt_task(self) -> TaskBlueprint:
        """
        現在のタスク(Generator スレッドについて安全)

        Returns:
            TaskBlueprint: 現在のタスク
        """
        return self.generator.crnt_task_copy

    @property
    def crnt_tasks(self) -> int:
        """
        現在のタスク数

        Returns:
            int: 現在のタスク数
        """
        return self.generator.len_tasks()

    @property
    def crnt_tasklist(self) -> list[dict[str, Any]]:
        """
        現在のタスクリスト

        Returns:
            list[dict[str, Any]]: 現在のタスクリスト
        """
        return self.generator.crnt_tasklist()

    @property
    def crnt_progress(self) -> float:
        """
        現在のタスクの進捗度

        Returns:
            float: 現在のタスクの進捗度
        """
        return self.generator.crnt_progress

    def on_next(self) -> None:
        """
        > ボタンハンドラ
        """
        self.archiver.next_picstats()

    def on_prev(self) -> None:
        """
        < ボタンハンドラ
        """
        self.archiver.prev_picstats()

    def on_upscale(self) -> None:
        """
        アップスケール予約ボタンハンドラ
        """
        self.generator.reserve_img2img(
            picstats=self.crnt_picstats,
            stps=self.displayer.crnt_config.sd_steps,
            smplr=SamplerName.dpmpp_2m_sde_gpu
            if self.backend == BackEnd.comfy_ui
            else SamplerName.dpmpp_2m_sde,
            schdlr=SchedulerName.karras,
            cfg=7.0,
            scaleby=1.2,
            denoise=0.65,
            d_addr=self.displayer.crnt_config.srv_ipaddr,
            d_port=self.displayer.crnt_config.srv_port,
            resize_mode=3 if self.backend_type == BackEnd.a1111 else None,
            upsclr=UpScalerName.nearest_exact if self.backend_type == BackEnd.comfy_ui else None,
        )

    def on_remove(self) -> None:
        """
        削除ボタンハンドラ
        """
        self.archiver.remove_crnt_picstats()

    def on_debug(self) -> None:
        """
        デバッグ処理\n
        ダミーステータスをセットし, 必要に応じてメイン処理を実施
        """
        run_oneshot = self.parser.ready_for_debug()
        if run_oneshot:
            self.run_oneshot()

    def on_interrupt(self) -> None:
        """
        中断処理要求時
        """
        self.generator.reserve_interrupt()

    def clear_tasks(self) -> None:
        """
        タスクリストを空にする
        """
        self.generator.clear()

    def reserve_task(self) -> None:
        """
        新しいタスクを生成し, タスクリストに予約する\n
        ただしプロンプト生成に十分なステータスが記録されていない,\n
        すでにリストに存在する, あるいは作業中のタスクの場合は何もしない
        """
        if not self.parser.is_stats_enough_for_prompt():
            return

        self.generator.reserve_txt2img(
            pos=self.parser.make_pos_prompt(),
            neg=self.parser.make_neg_prompt(),
            seed=-1,
            stps=self.displayer.crnt_config.sd_steps,
            b_size=self.displayer.crnt_config.sd_batch_size,
            smplr=SamplerName.dpmpp_2m,
            schdlr=SchedulerName.karras,
            cfg=7.0,
            w=self.displayer.crnt_config.sd_width,
            h=self.displayer.crnt_config.sd_height,
            d_addr=self.displayer.crnt_config.srv_ipaddr,
            d_port=self.displayer.crnt_config.srv_port,
        )

    def refresh_pic_randomly(self, construct_window=False) -> None:
        """
        現在の PicStats 表示可能な画像が存在する場合にランダムで表示する\n
        存在しない場合は NO IMAGE を表示する
        """
        if construct_window:
            self.displayer.pic_window.construct(fix_position=True)

        if self.archiver.count_files_in(self.parser.get_crnt_picstats_dir()) == 0:
            # 記録中ステータスに紐づくディレクトリ内に画像がない
            self.archiver.drop_picstats()
            return

        self.archiver.warp_picstats(self.parser.get_crnt_picstats_dir())

    def run_oneshot(self) -> None:
        """
        タスク予約とすでに存在する画像の表示を1度だけ行う
        """
        self.reserve_task()
        self.refresh_pic_randomly(construct_window=True)

    def run_main(self) -> None:
        """
        メイン処理 (ステータス更新 -> 更新がある場合にタスクを予約 -> すでに存在する画像を表示)\n
        Tkinter メインループにて周期的に呼び出される処理
        """
        try:
            if not self.root.winfo_exists():
                return

            if self.displayer.pic_window.event.outputting_noimage.is_set():
                # NO IMAGE 表示中は記録中ステータスに沿った画像の表示を常に試みる
                self.refresh_pic_randomly()

            is_new_stats = self.parser.refresh_stats()
            if not is_new_stats:
                return
            elif not self.parser.is_stats_enough_for_prompt():
                # 記録中ステータスが生成に不十分 i.e. ステータスに紐づくディレクトリがない
                self.archiver.drop_picstats()
                return

            self.run_oneshot()
        except tkinter.TclError:
            return
        finally:
            self.archiver.process_reports()
            self.displayer.update_pic_window(self.archiver.crnt_picstats)
            self.displayer.info_window.update()
            self.after_id = self.root.after(100, self.run_main)
