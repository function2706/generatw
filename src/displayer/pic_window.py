"""
画像ウィンドウ
"""

from __future__ import annotations

import threading
import tkinter
from dataclasses import dataclass
from pathlib import Path
from tkinter import TclError, ttk

from PIL import Image, ImageDraw, ImageFont, ImageTk

from common.interfaces import DisplayerIF


@dataclass
class Event:
    """
    イベントフラグ
    """

    outputting_noimage = threading.Event()  # NO IMAGE 表示中


class CursorFrame:
    """
    画像表示フレーム
    """

    def __init__(self, owner: PicWindow):
        """
        画像表示フレームコンストラクタ
        Args:
            owner (PicWindow): PicWindow インスタンス
        """
        self.super_owner = owner
        self.cursor_frame = ttk.Frame(owner.main_frame)
        self.cursor_frame.grid(row=0, column=0, sticky="nwe")
        # ラベル
        self.pic_label = ttk.Label(self.cursor_frame)
        self.pic_label.grid(row=0, column=1, padx=6, pady=6, sticky="nswe")
        self.pic_label_image = None
        # ボタン(<)
        self.backward_button = ttk.Button(
            self.cursor_frame, text="<", width=2, command=owner.super_owner.on_backward
        )
        self.backward_button.grid(row=0, column=0, padx=6, pady=6, sticky="nsw")
        # ボタン(>)
        self.forward_button = ttk.Button(
            self.cursor_frame, text=">", width=2, command=owner.super_owner.on_forward
        )
        self.forward_button.grid(row=0, column=2, padx=6, pady=6, sticky="nse")


class EvalFrame:
    """
    評価フレーム
    """

    def __init__(self, owner: PicWindow):
        """
        評価フレームコンストラクタ
        Args:
            owner (PicWindow): PicWindow インスタンス
        """
        self.super_owner = owner
        self.eval_frame = ttk.Frame(owner.main_frame)
        self.eval_frame.grid(row=1, column=0, sticky="swe")
        self.eval_frame.columnconfigure(0, weight=1)
        self.eval_frame.columnconfigure(1, weight=1)
        # ボタン(アップスケール予約)
        self.upscale_button = ttk.Button(
            self.eval_frame,
            text="アップスケール予約",
            command=self.super_owner.super_owner.on_upscale,
        )
        self.upscale_button.grid(row=0, column=0, padx=6, pady=6, sticky="wes")
        # ボタン(削除)
        self.delete_button = ttk.Button(
            self.eval_frame,
            text="削除",
            command=self.super_owner.super_owner.on_delete,
        )
        self.delete_button.grid(row=0, column=1, padx=6, pady=6, sticky="wes")


class PicWindow:
    """
    画像ウィンドウ
    """

    def __init__(self, owner: DisplayerIF):
        """
        画像ウィンドウコンストラクタ
        Args:
            owner (Displayer): Display インスタンス
            fix_position (bool, optional): 表示位置を固定するか
        """
        self.super_owner = owner
        self.pic_window: tkinter.Toplevel = None
        self.cursor_frame: CursorFrame = None
        self.eval_frame: EvalFrame = None
        self.event = Event()
        self.noimage_img: ImageTk.PhotoImage = None

    def construct(self, fix_position=False) -> None:
        """
        画像ウィンドウを構築する\n
        すでに開いている場合は何もしない
        """
        if self.existed() and self.pic_window:
            return

        self.pic_window = tkinter.Toplevel(self.super_owner.master.root)
        if fix_position:
            self.pic_window.geometry(
                (
                    f"-{
                        self.super_owner.config_window_x + self.super_owner.config_window_width + 50
                    }"
                    f"+{self.super_owner.config_window_y}"
                )
            )
        self.pic_window.title("picmaker - 画像")
        self.pic_window.protocol("WM_DELETE_WINDOW", self.destroy)
        self.main_frame = ttk.Frame(self.pic_window, padding=5)
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
            path (PicStats): 更新予定の PicStats
        """
        if not self.existed():
            return
        if path is not None and path.exists():
            image = Image.open(path)
            tk_img = ImageTk.PhotoImage(image)
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

    def set_no_image(self) -> None:
        """
        表示すべき画像がない場合の画像を作成し, インスタンス変数にセットする\n
        すでに同サイズの作成済みのイメージが存在する場合は新たに生成しない\n
        グレースケールのチェックパターンに"NO IMAGE"\n
        幅と高さは自動的に 8 の倍数に切り下げられる(Stable Diffusion の仕様に準拠)
        """
        width = self.super_owner.crnt_configs.sd_width & -8
        height = self.super_owner.crnt_configs.sd_height & -8
        if self.noimage_img is not None and (
            self.noimage_img.width() == width or self.noimage_img.height() == height
        ):
            return
        light = "#e0e0e0"
        dark = "#c0c0c0"
        text_color = "#444444"
        img = Image.new("RGB", (width, height), light)
        draw = ImageDraw.Draw(img)
        cell = max(8, min(width, height) // 20)
        for y in range(0, height, cell):
            for x in range(0, width, cell):
                if (x // cell + y // cell) % 2 == 0:
                    draw.rectangle((x, y, x + cell, y + cell), fill=light)
                else:
                    draw.rectangle((x, y, x + cell, y + cell), fill=dark)
        text = "NO IMAGE"
        fallback_font = ImageFont.load_default()
        max_font_size = int(height * 0.15)
        font_size = max_font_size
        while font_size > 5:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except Exception:
                font = fallback_font
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            if text_w <= width * 0.8:
                break
            font_size -= 2
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        text_x = (width - text_w) // 2
        text_y = (height - text_h) // 2
        draw.text((text_x, text_y), text, fill=text_color, font=font)
        self.noimage_img = ImageTk.PhotoImage(img)

    def switch_button_state(self, toggle: bool) -> None:
        """
        画像ウィンドウ上のボタンの有効/無効(グレーアウト)を切り替える
        Args:
            toggle (bool): True で有効, False で無効
        """
        if not self.existed():
            return

        forward_button = self.cursor_frame.forward_button
        backward_button = self.cursor_frame.backward_button
        upscale_button = self.eval_frame.upscale_button
        remove_button = self.eval_frame.delete_button
        if toggle:
            if str(forward_button.cget("state")) == "disabled":
                forward_button.configure(state="normal")
            if str(backward_button.cget("state")) == "disabled":
                backward_button.configure(state="normal")
            if str(upscale_button.cget("state")) == "disabled":
                upscale_button.configure(state="normal")
            if str(remove_button.cget("state")) == "disabled":
                remove_button.configure(state="normal")
        else:
            if str(forward_button.cget("state")) == "normal":
                forward_button.configure(state="disabled")
            if str(backward_button.cget("state")) == "normal":
                backward_button.configure(state="disabled")
            if str(upscale_button.cget("state")) == "normal":
                upscale_button.configure(state="disabled")
            if str(remove_button.cget("state")) == "normal":
                remove_button.configure(state="disabled")
