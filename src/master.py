"""
各モジュールの横断処理を統括するクラス
"""

from __future__ import annotations

import tkinter
from parser.reverse_parser import ReverseParser
from parser.theworld_parser import TheWorldParser
from pathlib import Path
from typing import Any

from archiver import Archiver
from common.classes import PicStats, TaskBlueprint
from common.interfaces import BackEnd, CrntGUIConfigs, FrontEnd, MasterIF
from displayer import Displayer
from generator.a1111_generator import A1111Generator
from generator.comfyui_generator import ComfyUIGenerator


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

        if frontend == FrontEnd.reverse:
            self.parser = ReverseParser(self)
        elif frontend == FrontEnd.the_world:
            self.parser = TheWorldParser(self)
        else:
            raise ValueError

        self.archiver = Archiver.make(self.parser.pics_dir_path())

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
        self.root.after(100, self.run_main)
        self.root.mainloop()

    def finalize(self) -> None:
        """
        終了処理
        """

        self.generator.finalize()

        def worker():
            self.generator.join()
            self.displayer.destroy_config_window()

        self.root.after(100, worker())

    def sigint_handler(self, sig, frame) -> None:
        """
        SIGINT ハンドラ

        Args:
            sig (_type_): シグナル
            frame (_type_): Tkinter フレーム
        """
        self.finalize()

    @property
    def frontend_name(self) -> str:
        """
        フロントエンド名

        Returns:
            str: フロントエンド名
        """
        return self.parser.whoami()

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
    def crnt_gui_configs(self) -> CrntGUIConfigs:
        """
        現在の GUI 上の設定値

        Returns:
            CrntGUIConfigs: 現在の GUI 上の設定値
        """
        return CrntGUIConfigs.make(
            srv_ipaddr=self.displayer.srv_ipaddr,
            srv_port=self.displayer.srv_port,
            sd_steps=self.displayer.sd_steps,
            sd_batch_size=self.displayer.sd_batch_size,
            sd_width=self.displayer.sd_width,
            sd_height=self.displayer.sd_height,
            allow_edit_clipboard=self.displayer.allow_edit_clipboard,
            print_new_clipboard=self.displayer.print_new_clipboard,
            print_new_stats=self.displayer.print_new_stats,
            print_images=self.displayer.print_images,
            print_picinfo=self.displayer.print_picinfo,
        )

    @property
    def crnt_picstats(self) -> PicStats:
        """
        現在の PicStats

        Returns:
            PicStats: 現在の PicStats
        """
        return self.archiver.crnt_picstats

    @property
    def crnt_archiver(self) -> dict[str, Any]:
        """
        現在の Archiver

        Returns:
            dict[str, Any]: 現在の Archiver
        """
        return self.archiver.todict()

    @property
    def crnt_task(self) -> TaskBlueprint:
        """
        現在のタスク

        Returns:
            TaskBlueprint: 現在のタスク
        """
        return self.generator.crnt_task

    @property
    def crnt_tasks(self) -> int:
        """
        現在のタスク数

        Returns:
            int: 現在のタスク数
        """
        return self.generator.len_tasks()

    @property
    def crnt_tasklist(self) -> list[TaskBlueprint]:
        """
        現在のタスクリスト

        Returns:
            list[TaskBlueprint]: 現在のタスクリスト
        """
        return list(self.generator.tasks)

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
        self.displayer.update_pic_window(self.archiver.crnt_picstats)

    def on_prev(self) -> None:
        """
        < ボタンハンドラ
        """
        self.archiver.prev_picstats()
        self.displayer.update_pic_window(self.archiver.crnt_picstats)

    def on_upscale(self) -> None:
        """
        GOOD ボタンハンドラ
        """
        return

    def on_remove(self) -> None:
        """
        BAD ボタンハンドラ\n
        表示中の画像を削除する\n
        削除後に同じディレクトリ内に画像が残っている場合はランダムで表示する\n
        残っていない場合はディレクトリを削除し, NO IMAGE を表示する
        """
        self.archiver.remove_crnt_picstats()
        if self.archiver.crnt_picstats is None:
            # 削除後に表示すべき画像がない
            self.displayer.put_no_image_placeholder()
        else:
            self.archiver.warp_picstats(self.archiver.crnt_picstats.dir)
            self.displayer.update_pic_window(self.archiver.crnt_picstats)

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

    def refresh_piclist(self) -> None:
        """
        監視対象ディレクトリ内の画像ファイルを PicStats の形で再帰的にリスト化する
        """
        self.archiver.refresh_piclist()

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

        self.generator.reserve(
            pos=self.parser.make_pos_prompt(),
            neg=self.parser.make_neg_prompt(),
            stps=self.displayer.sd_steps,
            b_size=self.displayer.sd_batch_size,
            w=self.displayer.sd_width,
            h=self.displayer.sd_height,
            d_addr=self.displayer.srv_ipaddr,
            d_port=self.displayer.srv_port,
        )

    def refresh_pic_randomly(self) -> None:
        """
        現在の PicStats 表示可能な画像が存在する場合にランダムで表示する\n
        存在しない場合は NO IMAGE を表示する
        """
        piclist = self.archiver.get_picstats_list(self.parser.get_crnt_picstats_dir())
        if not piclist:
            # 記録中ステータスに紐づくディレクトリ内に画像がない
            self.displayer.put_no_image_placeholder()
            return

        self.archiver.warp_picstats(self.parser.get_crnt_picstats_dir())
        self.displayer.update_pic_window(self.archiver.crnt_picstats)

    def run_oneshot(self) -> None:
        """
        タスク予約とすでに存在する画像の表示を1度だけ行う
        """
        self.reserve_task()
        self.refresh_pic_randomly()

    def run_main(self) -> None:
        """
        メイン処理 (ステータス更新 -> 更新がある場合にタスクを予約 -> すでに存在する画像を表示)\n
        Tkinter メインループにて周期的に呼び出される処理
        """
        try:
            if self.displayer.event.outputting_noimage.is_set():
                # NO IMAGE 表示中は記録中ステータスに沿った画像の表示を常に試みる
                self.refresh_pic_randomly()

            is_new_stats = self.parser.refresh_stats()
            if not is_new_stats:
                return
            elif not self.parser.is_stats_enough_for_prompt():
                # 記録中ステータスが生成に不十分 i.e. ステータスに紐づくディレクトリがない
                self.displayer.put_no_image_placeholder()
                return

            self.run_oneshot()
        finally:
            self.displayer.update_info_window()
            self.root.after(300, self.run_main)
