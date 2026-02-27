# widgets.py
import tkinter as tk
from PIL import Image, ImageDraw, ImageTk
import math
from constants import BG_DARK, ACCENT, ACCENT_GLOW, TEXT_PRIMARY, TEXT_MUTED


def create_checkerboard(size=(260, 260), tile=12):
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    cols = math.ceil(size[0] / tile)
    rows = math.ceil(size[1] / tile)
    light, dark = (200, 200, 200), (155, 155, 155)
    for r in range(rows):
        for c in range(cols):
            color = light if (r + c) % 2 == 0 else dark
            draw.rectangle([c*tile, r*tile, (c+1)*tile, (r+1)*tile], fill=color)
    return img


class AnimatedButton(tk.Canvas):
    def __init__(self, parent, text, command, width=220, height=46,
                 bg_color=ACCENT, hover_color=ACCENT_GLOW,
                 text_color=TEXT_PRIMARY, font=None, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=BG_DARK, highlightthickness=0, **kwargs)
        self._text = text
        self._cmd = command
        self._width, self._height = width, height
        self._bg = bg_color
        self._hover = hover_color
        self._tc = text_color
        self._font = font or ("Helvetica", 11, "bold")
        self._disabled = False
        self._draw(bg_color)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _draw(self, color):
        self.delete("all")
        r = self._height // 2
        self.create_oval(4, 4, self._width-4, self._height+4, fill="#000000", outline="")
        self.create_oval(0, 0, self._height, self._height, fill=color, outline="")
        self.create_oval(self._width-self._height, 0, self._width, self._height, fill=color, outline="")
        self.create_rectangle(r, 0, self._width-r, self._height, fill=color, outline="")
        self.create_text(self._width//2, self._height//2, text=self._text,
                         fill=self._tc if not self._disabled else TEXT_MUTED,
                         font=self._font)

    def _on_enter(self, _):
        if not self._disabled:
            self._draw(self._hover)

    def _on_leave(self, _):
        if not self._disabled:
            self._draw(self._bg)

    def _on_click(self, _):
        if not self._disabled and self._cmd:
            self._cmd()

    def set_state(self, disabled: bool, text: str = None):
        self._disabled = disabled
        if text:
            self._text = text
        self._draw(TEXT_MUTED if disabled else self._bg)

    def set_text(self, text):
        self._text = text
        self._draw(TEXT_MUTED if self._disabled else self._bg)