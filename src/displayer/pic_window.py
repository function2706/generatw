"""
画像ウィンドウ
"""

from __future__ import annotations

import threading
import tkinter
from dataclasses import dataclass
from pathlib import Path
from tkinter import TclError, ttk
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw, ImageFont, ImageTk

from displayer import theme, widgets
from displayer.theme import STYLES

if TYPE_CHECKING:
    from displayer.displayer import Displayer


@dataclass
class Event:
    """
    イベントフラグ
    """

    outputting_noimage = threading.Event()  # NO IMAGE 表示中


class CursorFrame:
    """
    画像表示フレーム (< 画像 >)
    """

    def __init__(self, owner: PicWindow):
        """
        コンストラクタ

        Args:
            owner (PicWindow): PicWindow インスタンス
        """
        self.super_owner = owner
        self.cursor_frame = ttk.Frame(owner.main_frame)
        self.cursor_frame.grid(row=0, column=0, sticky="nwe")

        self.backward_button = ttk.Button(
            self.cursor_frame, text="<", width=2, command=owner.super_owner.on_backward
        )
        self.backward_button.grid(row=0, column=0, padx=6, pady=6, sticky="nsw")

        self.pic_label = ttk.Label(self.cursor_frame, anchor="center")
        self.pic_label.grid(row=0, column=1, padx=6, pady=6, sticky="nswe")
        self.pic_label_image = None

        self.forward_button = ttk.Button(
            self.cursor_frame, text=">", width=2, command=owner.super_owner.on_forward
        )
        self.forward_button.grid(row=0, column=2, padx=6, pady=6, sticky="nse")


class EvalFrame:
    """
    評価フレーム (アップスケール予約 / 削除)
    """

    def __init__(self, owner: PicWindow):
        """
        コンストラクタ

        Args:
            owner (PicWindow): PicWindow インスタンス
        """
        self.super_owner = owner
        self.eval_frame = ttk.Frame(owner.main_frame)
        self.eval_frame.grid(row=1, column=0, sticky="swe")
        self.eval_frame.columnconfigure(0, weight=1)
        self.eval_frame.columnconfigure(1, weight=1)

        self.upscale_button = ttk.Button(
            self.eval_frame,
            text="アップスケール予約",
            style=STYLES.accent_button,
            command=owner.super_owner.on_upscale,
        )
        self.upscale_button.grid(row=0, column=0, padx=6, pady=6, sticky="wes")

        self.delete_button = ttk.Button(
            self.eval_frame,
            text="削除",
            command=owner.super_owner.on_delete,
        )
        self.delete_button.grid(row=0, column=1, padx=6, pady=6, sticky="wes")


class PicWindow:
    """
    画像ウィンドウ
    """

    def __init__(self, owner: Displayer):
        """
        コンストラクタ

        Args:
            owner (Displayer): Displayer インスタンス
        """
        self.super_owner = owner
        self.pic_window: tkinter.Toplevel = None
        self.main_frame: ttk.Frame = None
        self.cursor_frame: CursorFrame = None
        self.eval_frame: EvalFrame = None
        self.event = Event()
        self.noimage_img: ImageTk.PhotoImage = None
        self._noimage_size: tuple[int, int] = None

    def construct(self, fix_position=False) -> None:
        """
        画像ウィンドウを構築する\n
        すでに開いている場合は何もしない

        Args:
            fix_position (bool): 表示位置を親ウィンドウ基準に固定するか
        """
        if self.existed() and self.pic_window:
            return

        self.pic_window = tkinter.Toplevel(self.super_owner.master.root)
        widgets.apply_toplevel_bg(self.pic_window)
        if fix_position:
            self.pic_window.geometry(
                f"-{self.super_owner.config_window_x + self.super_owner.config_window_width + 50}"
                f"+{self.super_owner.config_window_y}"
            )
        self.pic_window.title("picmaker - 画像")
        self.pic_window.protocol("WM_DELETE_WINDOW", self.destroy)
        self.main_frame = ttk.Frame(self.pic_window, padding=8)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.cursor_frame = CursorFrame(self)
        self.eval_frame = EvalFrame(self)

    def destroy(self) -> None:
        """
        画像ウィンドウのクローズ時のハンドラ
        """
        if self.existed():
            self.pic_window.destroy()
        self.pic_window = None

    def existed(self) -> bool:
        """
        画像ウィンドウが開かれているか

        Returns:
            bool: True: 開かれている, False: 開かれていない or TclError 例外発生
        """
        if self.pic_window is None:
            return False
        try:
            return bool(self.pic_window.winfo_exists())
        except TclError:
            return False

    def update(self, path: Path = None) -> None:
        """
        画像ウィンドウを指定のパスの画像で更新する\n
        path が None の場合は NO IMAGE で更新する

        Args:
            path (Path): 表示する画像のパス
        """
        if not self.existed():
            return

        if path is not None and path.exists():
            tk_img = ImageTk.PhotoImage(Image.open(path))
            self.cursor_frame.pic_label.configure(image=tk_img)
            self.cursor_frame.pic_label_image = tk_img
            self.event.outputting_noimage.clear()
            self.switch_button_state(True)
        else:
            self.set_no_image()
            self.cursor_frame.pic_label.configure(image=self.noimage_img)
            self.cursor_frame.pic_label_image = self.noimage_img
            self.event.outputting_noimage.set()
            self.switch_button_state(False)

    def retheme(self) -> None:
        """
        テーマ切替時に NO IMAGE 画像を現在のパレットで再生成する
        """
        self.noimage_img = None
        self._noimage_size = None
        if self.existed() and self.event.outputting_noimage.is_set():
            self.update()

    def set_no_image(self) -> None:
        """
        表示すべき画像がない場合の画像を生成し, インスタンス変数へ格納する\n
        グレーのチェックパターンに "NO IMAGE"\n
        幅と高さは 8 の倍数へ切り下げる (Stable Diffusion の仕様に準拠)\n
        同サイズの生成済みイメージがある場合は再生成しない
        """
        width = self.super_owner.crnt_configs.sd_width & -8
        height = self.super_owner.crnt_configs.sd_height & -8
        if self.noimage_img is not None and self._noimage_size == (width, height):
            return

        pal = theme.current
        light, dark, text_color = pal.surface_alt, pal.border, pal.muted
        img = Image.new("RGB", (width, height), light)
        draw = ImageDraw.Draw(img)
        cell = max(8, min(width, height) // 20)
        for y in range(0, height, cell):
            for x in range(0, width, cell):
                if (x // cell + y // cell) % 2:
                    draw.rectangle((x, y, x + cell, y + cell), fill=dark)

        text = "NO IMAGE"
        font_size = int(height * 0.15)
        chosen = ImageFont.load_default()
        while font_size > 5:
            try:
                chosen = ImageFont.truetype("arial.ttf", font_size)
            except Exception:
                chosen = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), text, font=chosen)
            if bbox[2] - bbox[0] <= width * 0.8:
                break
            font_size -= 2

        bbox = draw.textbbox((0, 0), text, font=chosen)
        text_x = (width - (bbox[2] - bbox[0])) // 2
        text_y = (height - (bbox[3] - bbox[1])) // 2
        draw.text((text_x, text_y), text, fill=text_color, font=chosen)

        self.noimage_img = ImageTk.PhotoImage(img)
        self._noimage_size = (width, height)

    def switch_button_state(self, toggle: bool) -> None:
        """
        画像ウィンドウ上のボタンの有効/無効(グレーアウト)を切り替える

        Args:
            toggle (bool): True で有効, False で無効
        """
        if not self.existed():
            return

        state = "normal" if toggle else "disabled"
        for button in (
            self.cursor_frame.forward_button,
            self.cursor_frame.backward_button,
            self.eval_frame.upscale_button,
            self.eval_frame.delete_button,
        ):
            button.configure(state=state)
