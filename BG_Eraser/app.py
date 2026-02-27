# app.py
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import threading
import os

from constants import *
from widgets import AnimatedButton, create_checkerboard
from processor import process_image


class BGRemoverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BG Eraser")
        self.root.geometry("480x700")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_DARK)

        self.output_image: Image.Image | None = None
        self.face_detected = False

        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg=BG_DARK)
        header.pack(fill="x", padx=30, pady=(28, 0))
        tk.Label(header, text="BG", font=("Georgia", 22, "bold"), fg=ACCENT, bg=BG_DARK).pack(side="left")
        tk.Label(header, text=" Eraser", font=("Georgia", 22, "bold"), fg=TEXT_PRIMARY, bg=BG_DARK).pack(side="left")
        tk.Label(header, text="Powered by rembg", font=("Helvetica", 9), fg=TEXT_MUTED, bg=BG_DARK).pack(side="right", pady=6)

        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x", padx=30, pady=(14, 0))

        # Preview Card
        self.card = tk.Frame(self.root, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
        self.card.pack(padx=30, pady=20, fill="x")

        self.preview_canvas = tk.Canvas(self.card, width=420, height=300, bg=BG_CARD, highlightthickness=0)
        self.preview_canvas.pack(padx=20, pady=20)
        self._draw_placeholder()

        # Status
        self.status_var = tk.StringVar(value="Upload an image to get started")
        status_frame = tk.Frame(self.root, bg=BG_SURFACE, highlightbackground=BORDER, highlightthickness=1)
        status_frame.pack(padx=30, fill="x")
        self.status_dot = tk.Label(status_frame, text="●", font=("Helvetica", 9), fg=TEXT_MUTED, bg=BG_SURFACE)
        self.status_dot.pack(side="left", padx=(14, 4), pady=10)
        tk.Label(status_frame, textvariable=self.status_var, font=("Helvetica", 10), fg=TEXT_MUTED, bg=BG_SURFACE, anchor="w").pack(side="left", pady=10)

        # Progress
        self.progress_frame = tk.Frame(self.root, bg=BG_DARK)
        self.progress_frame.pack(padx=30, fill="x", pady=(10, 0))
        self.progress_canvas = tk.Canvas(self.progress_frame, height=4, bg=BG_SURFACE, highlightthickness=0)
        self.progress_canvas.pack(fill="x")

        # Buttons
        btn_row = tk.Frame(self.root, bg=BG_DARK)
        btn_row.pack(pady=22)

        self.upload_btn = AnimatedButton(btn_row, text="Upload Image", command=self._upload, width=190, height=46)
        self.upload_btn.pack(side="left", padx=8)

        self.save_btn = AnimatedButton(btn_row, text="Save Image", command=self._save, width=190, height=46,
                                       bg_color="#1E2A1E", hover_color=SUCCESS, text_color=TEXT_MUTED)
        self.save_btn.pack(side="left", padx=8)
        self.save_btn.set_state(True)

        tk.Label(self.root, text="PNG (full) • Cropped Lossless JPG (faces only)",
                 font=("Helvetica", 8), fg=TEXT_MUTED, bg=BG_DARK).pack(pady=(0, 14))

    # ==================== UI Helpers ====================
    def _draw_placeholder(self):
        c = self.preview_canvas
        c.delete("all")
        W, H = 420, 300
        dash_step = 12
        for x in range(20, W-20, dash_step*2):
            c.create_line(x, 20, x+dash_step, 20, fill=BORDER, width=1)
            c.create_line(x, H-20, x+dash_step, H-20, fill=BORDER, width=1)
        for y in range(20, H-20, dash_step*2):
            c.create_line(20, y, 20, y+dash_step, fill=BORDER, width=1)
            c.create_line(W-20, y, W-20, y+dash_step, fill=BORDER, width=1)
        c.create_text(W//2, H//2 - 24, text="⬆", font=("Helvetica", 36), fill=BORDER)
        c.create_text(W//2, H//2 + 20, text="Drop or upload an image", font=("Helvetica", 12), fill=TEXT_MUTED)
        c.create_text(W//2, H//2 + 42, text="Background removed + face cropped automatically", font=("Helvetica", 9), fill=BORDER)

    def _show_preview(self, pil_image):
        c = self.preview_canvas
        c.delete("all")
        W, H = 420, 300
        checker = create_checkerboard((W, H))
        self._checker_photo = ImageTk.PhotoImage(checker)
        c.create_image(0, 0, anchor="nw", image=self._checker_photo)

        thumb = pil_image.copy()
        thumb.thumbnail((W - 40, H - 40), Image.LANCZOS)
        thumb = thumb.convert("RGBA")
        x = (W - thumb.width) // 2
        y = (H - thumb.height) // 2
        composite = checker.copy()
        composite.paste(thumb, (x, y), thumb)
        self._preview_photo = ImageTk.PhotoImage(composite)
        c.create_image(W//2, H//2, anchor="center", image=self._preview_photo)

    # ==================== Progress ====================
    def _start_progress(self):
        self._animating = True
        self._progress_val = 0
        self._tick_progress()

    def _tick_progress(self):
        if not getattr(self, '_animating', False):
            return
        self._progress_val = (self._progress_val + 2) % 100
        self._draw_progress(self._progress_val)
        self.root.after(20, self._tick_progress)

    def _draw_progress(self, val):
        c = self.progress_canvas
        c.delete("all")
        W = c.winfo_width() or 420
        fill_w = int(W * val / 100)
        c.create_rectangle(0, 0, fill_w, 4, fill=ACCENT, outline="")
        c.create_rectangle(fill_w, 0, W, 4, fill=BG_SURFACE, outline="")

    def _stop_progress(self, success=True):
        self._animating = False
        c = self.progress_canvas
        c.delete("all")
        W = c.winfo_width() or 420
        color = SUCCESS if success else ERROR_COLOR
        c.create_rectangle(0, 0, W, 4, fill=color, outline="")
        self.root.after(1200, lambda: c.delete("all"))

    # ==================== Core Logic ====================
    def _upload(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp")])
        if not path:
            return

        self.upload_btn.set_state(True, "Processing…")
        self.save_btn.set_state(True)
        self.status_dot.config(fg=ACCENT)
        self.status_var.set("Removing background & cropping face…")
        self._draw_placeholder()
        self._start_progress()

        threading.Thread(target=self._process, args=(path,), daemon=True).start()

    def _process(self, file_path):
        try:
            final_image, face_detected = process_image(file_path)
            self.root.after(0, self._on_success, final_image, face_detected)
        except Exception as e:
            self.root.after(0, self._on_error, str(e))

    def _on_success(self, image: Image.Image, face_detected: bool):
        self._stop_progress(True)

        self.output_image = image
        self.face_detected = face_detected

        self._show_preview(image)
        self.upload_btn.set_state(False, "Upload Image")
        self.save_btn.set_state(False)

        if face_detected:
            self.status_dot.config(fg=SUCCESS)
            self.status_var.set("Background removed & Face cropped ✓")
            self.save_btn._bg = SUCCESS
            self.save_btn._hover = "#1ED99F"
            self.save_btn._tc = "#0D1A0D"
            self.save_btn.set_text("Save Cropped Lossless JPG")
        else:
            self.status_dot.config(fg=SUCCESS)
            self.status_var.set("Background removed successfully ✓")
            self.save_btn._bg = "#1E2A1E"
            self.save_btn._hover = SUCCESS
            self.save_btn._tc = TEXT_MUTED
            self.save_btn.set_text("Save Image")

    def _on_error(self, msg):
        self.face_detected = False
        self.output_image = None
        self._stop_progress(False)
        self.upload_btn.set_state(False, "Upload Image")
        self.status_dot.config(fg=ERROR_COLOR)
        self.status_var.set(f"Error: {msg}")
        messagebox.showerror("Error", msg)

    # ==================== Save ====================
    def _save(self):
        if self.output_image is None:
            return

        if self.face_detected:
            defaultextension = ".jpg"
            filetypes = [("JPEG Image", "*.jpg *.jpeg"), ("All Files", "*.*")]
            title = "Save Cropped Lossless JPG (Quality 100%)"
        else:
            defaultextension = ".png"
            filetypes = [("PNG Image", "*.png"), ("All Files", "*.*")]
            title = "Save Transparent Image"

        save_path = filedialog.asksaveasfilename(
            defaultextension=defaultextension,
            filetypes=filetypes,
            title=title
        )
        if not save_path:
            return

        try:
            img = self.output_image
            lower = save_path.lower()

            if lower.endswith(('.jpg', '.jpeg')):
                if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                    white_bg = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "RGBA":
                        white_bg.paste(img, mask=img.split()[3])
                    else:
                        white_bg.paste(img, mask=img.split()[1])
                    img = white_bg
                else:
                    img = img.convert("RGB")

                img.save(save_path, "JPEG", quality=100, optimize=True, subsampling=0)
                msg = f"Saved cropped lossless JPG → {os.path.basename(save_path)}"
            else:
                img.save(save_path)
                msg = f"Saved → {os.path.basename(save_path)}"

            self.status_var.set(msg)
            messagebox.showinfo("Saved!", f"Image saved to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))