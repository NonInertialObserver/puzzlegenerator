import json
import os
import random
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageChops, ImageOps, ImageTk

from i18n import SUPPORTED_LANGUAGES, Translator, get_language_display_name, language_from_display_name
from main import build_piece_mask, compute_piece_boxes, export_pieces, generate_edge_map


class PuzzleGeneratorGUI(tk.Tk):
    """Tkinter front-end for the puzzle piece generator."""

    def __init__(self) -> None:
        super().__init__()
        self.translator = Translator()
        self._ = self.translator.gettext
        self.title(self._("app.title"))
        self.geometry("760x560")
        self.resizable(False, False)
        self.iconbitmap("./icon.ico") 
        self.input_path = tk.StringVar()
        self.output_dir = tk.StringVar(value="pieces")
        self.rows = tk.IntVar(value=4)
        self.cols = tk.IntVar(value=4)
        self.output_format = tk.StringVar(value="png")
        self.write_metadata = tk.BooleanVar(value=True)
        self.tab_size = tk.DoubleVar(value=0.35)
        self.seed = tk.IntVar(value=0)
        self.language_display = tk.StringVar(
            value=get_language_display_name(self.translator.language)
        )
        self.status = tk.StringVar(value=self._("status.ready"))
        self.preview_status = tk.StringVar(value=self._("preview.no_image"))
        self.preview_image: ImageTk.PhotoImage | None = None
        self.translatable_widgets: list[tuple[tk.Widget, str, str]] = []

        self._build_widgets()
        self._bind_preview_updates()

    def _register_text(self, widget: tk.Widget, key: str, option: str = "text") -> tk.Widget:
        self.translatable_widgets.append((widget, key, option))
        widget.configure(**{option: self._(key)})
        return widget

    def _build_widgets(self) -> None:
        main_frame = ttk.Frame(self, padding=16)
        main_frame.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(
            main_frame,
            font=("Segoe UI", 16, "bold"),
        )
        self._register_text(title, "app.heading")
        title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 16))

        self._register_text(ttk.Label(main_frame), "field.input_image").grid(row=1, column=0, sticky="w")
        ttk.Entry(main_frame, textvariable=self.input_path, width=56).grid(
            row=1, column=1, sticky="ew", padx=8
        )
        self._register_text(ttk.Button(main_frame, command=self.browse_input), "button.browse").grid(
            row=1, column=2, sticky="ew"
        )

        self._register_text(ttk.Label(main_frame), "field.output_folder").grid(
            row=2, column=0, sticky="w", pady=(10, 0)
        )
        ttk.Entry(main_frame, textvariable=self.output_dir, width=56).grid(
            row=2, column=1, sticky="ew", padx=8, pady=(10, 0)
        )
        self._register_text(ttk.Button(main_frame, command=self.browse_output), "button.browse").grid(
            row=2, column=2, sticky="ew", pady=(10, 0)
        )

        center_frame = ttk.Frame(main_frame)
        center_frame.grid(row=3, column=0, columnspan=3, sticky="nsew", pady=18)
        center_frame.columnconfigure(0, weight=1, uniform="center")
        center_frame.columnconfigure(1, weight=1, uniform="center")

        options = ttk.LabelFrame(center_frame, padding=12)
        self._register_text(options, "frame.options")
        options.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self._register_text(ttk.Label(options), "field.rows").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(options, from_=1, to=100, textvariable=self.rows, width=8).grid(
            row=0, column=1, sticky="ew", padx=(6, 0)
        )

        self._register_text(ttk.Label(options), "field.columns").grid(row=1, column=0, sticky="w", pady=(12, 0))
        ttk.Spinbox(options, from_=1, to=100, textvariable=self.cols, width=8).grid(
            row=1, column=1, sticky="ew", padx=(6, 0), pady=(12, 0)
        )

        self._register_text(ttk.Label(options), "field.format").grid(row=2, column=0, sticky="w", pady=(12, 0))
        ttk.Combobox(
            options,
            textvariable=self.output_format,
            values=("png", "jpg", "jpeg", "webp"),
            width=8,
            state="readonly",
        ).grid(row=2, column=1, sticky="ew", padx=(6, 0), pady=(12, 0))

        self._register_text(ttk.Label(options), "field.tab_size").grid(row=3, column=0, sticky="w", pady=(12, 0))
        ttk.Spinbox(
            options,
            from_=0.10,
            to=0.45,
            increment=0.05,
            textvariable=self.tab_size,
            width=8,
        ).grid(row=3, column=1, sticky="ew", padx=(6, 0), pady=(12, 0))

        self._register_text(ttk.Label(options), "field.seed").grid(row=4, column=0, sticky="w", pady=(12, 0))
        ttk.Spinbox(options, from_=0, to=999999, textvariable=self.seed, width=8).grid(
            row=4, column=1, sticky="ew", padx=(6, 0), pady=(12, 0)
        )

        self._register_text(ttk.Checkbutton(
            options,
            variable=self.write_metadata,
        ), "checkbox.write_metadata").grid(row=5, column=0, columnspan=2, sticky="w", pady=(12, 0))
        options.columnconfigure(1, weight=1)

        preview_frame = ttk.LabelFrame(center_frame, padding=12)
        self._register_text(preview_frame, "frame.preview")
        preview_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self.preview_label = ttk.Label(preview_frame, anchor="center")
        self.preview_label.grid(row=0, column=0, sticky="nsew")
        ttk.Label(preview_frame, textvariable=self.preview_status, foreground="#666", wraplength=300).grid(
            row=1, column=0, sticky="w", pady=(8, 0)
        )
        preview_frame.rowconfigure(0, weight=1)
        preview_frame.columnconfigure(0, weight=1)

        self.generate_button = ttk.Button(
            main_frame, command=self.generate_clicked
        )
        self._register_text(self.generate_button, "button.generate")
        self.generate_button.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(0, 12))

        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        self._register_text(ttk.Label(bottom_frame), "field.language").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Combobox(
            bottom_frame,
            textvariable=self.language_display,
            values=tuple(SUPPORTED_LANGUAGES.values()),
            width=10,
            state="readonly",
        ).grid(row=0, column=1, sticky="w", padx=(6, 0))
        self.language_display.trace_add("write", self.language_changed)

        ttk.Label(main_frame, textvariable=self.status, foreground="#444").grid(
            row=6, column=0, columnspan=3, sticky="w"
        )

        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)

    def _bind_preview_updates(self) -> None:
        for variable in (self.input_path, self.rows, self.cols, self.tab_size, self.seed):
            variable.trace_add("write", self.preview_inputs_changed)

    def preview_inputs_changed(self, *_args: object) -> None:
        self.after_idle(self.update_preview)

    def browse_input(self) -> None:
        path = filedialog.askopenfilename(
            title=self._("dialog.select_source_image"),
            filetypes=(
                (self._("dialog.image_files"), "*.png *.jpg *.jpeg *.webp *.bmp *.gif"),
                (self._("dialog.all_files"), "*.*"),
            ),
        )
        if path:
            self.input_path.set(path)

    def browse_output(self) -> None:
        path = filedialog.askdirectory(title=self._("dialog.select_output_folder"))
        if path:
            self.output_dir.set(path)

    def language_changed(self, *_args: object) -> None:
        self.translator.set_language(language_from_display_name(self.language_display.get()))
        self.title(self._("app.title"))
        for widget, key, option in self.translatable_widgets:
            widget.configure(**{option: self._(key)})
        if self.generate_button.cget("state") != tk.DISABLED:
            self.status.set(self._("status.ready"))
        self.update_preview()

    def update_preview(self) -> None:
        input_path = self.input_path.get().strip()
        if not input_path:
            self.preview_label.configure(image="")
            self.preview_image = None
            self.preview_status.set(self._("preview.no_image"))
            return

        if not os.path.exists(input_path):
            self.preview_label.configure(image="")
            self.preview_image = None
            self.preview_status.set(self._("preview.input_missing"))
            return

        try:
            rows = self.rows.get()
            cols = self.cols.get()
            tab_size = self.tab_size.get()
            seed = self.seed.get()
            if rows <= 0 or cols <= 0:
                raise ValueError(self._("error.rows_cols_positive"))

            with Image.open(input_path) as image:
                image = image.convert("RGBA")
                piece_w = image.width // cols
                piece_h = image.height // rows
                if piece_w == 0 or piece_h == 0:
                    raise ValueError(self._("error.image_too_small"))

                crop_w = piece_w * cols
                crop_h = piece_h * rows
                image = image.crop((0, 0, crop_w, crop_h))
                tab_radius = max(2, int(min(piece_w, piece_h) * tab_size / 2))
                pad = tab_radius
                rng = random.Random(seed)
                edge_map = generate_edge_map(rows, cols, rng, border_tabs=False)
                padded_image = ImageOps.expand(image, border=pad, fill=(0, 0, 0, 0))
                piece = padded_image.crop((0, 0, piece_w + 2 * pad, piece_h + 2 * pad)).convert("RGBA")
                mask = build_piece_mask(piece_w, piece_h, pad, edge_map[0][0], tab_radius)
                piece.putalpha(ImageChops.multiply(piece.getchannel("A"), mask))
                piece.thumbnail((220, 220), Image.Resampling.LANCZOS)

            self.preview_image = ImageTk.PhotoImage(piece)
            self.preview_label.configure(image=self.preview_image)
            self.preview_status.set(
                self._("preview.showing", width=piece_w, height=piece_h, rows=rows, cols=cols)
            )
        except Exception as exc:
            self.preview_label.configure(image="")
            self.preview_image = None
            self.preview_status.set(self._("preview.failed", error=exc))

    def generate_clicked(self) -> None:
        try:
            self._validate_inputs()
        except ValueError as exc:
            messagebox.showerror(self._("dialog.invalid_input"), str(exc))
            return

        self.generate_button.config(state=tk.DISABLED)
        self.status.set(self._("status.generating"))
        threading.Thread(target=self._generate_worker, daemon=True).start()

    def _validate_inputs(self) -> None:
        if not self.input_path.get().strip():
            raise ValueError(self._("error.select_input"))
        if not os.path.exists(self.input_path.get()):
            raise ValueError(self._("error.input_missing"))
        if not self.output_dir.get().strip():
            raise ValueError(self._("error.select_output"))
        if self.rows.get() <= 0 or self.cols.get() <= 0:
            raise ValueError(self._("error.rows_cols_positive"))
        if not 0.1 <= self.tab_size.get() <= 0.45:
            raise ValueError(self._("error.tab_size_range"))

    def _generate_worker(self) -> None:
        try:
            count = self.generate_pieces()
        except Exception as exc:  # Show unexpected generation errors in the GUI.
            self.after(0, self._generation_failed, str(exc))
            return

        self.after(0, self._generation_succeeded, count)

    def generate_pieces(self) -> int:
        input_path = self.input_path.get()
        output_dir = self.output_dir.get()
        rows = self.rows.get()
        cols = self.cols.get()
        fmt = self.output_format.get()
        tab_size = self.tab_size.get()
        seed = self.seed.get()

        with Image.open(input_path) as image:
            image = image.convert("RGBA")
            piece_w = image.width // cols
            piece_h = image.height // rows
            if piece_w == 0 or piece_h == 0:
                raise ValueError(self._("error.image_too_small"))

            crop_w = piece_w * cols
            crop_h = piece_h * rows
            image = image.crop((0, 0, crop_w, crop_h))

            boxes = compute_piece_boxes(crop_w, crop_h, rows, cols)
            tab_radius = max(2, int(min(piece_w, piece_h) * tab_size / 2))
            pad = tab_radius

            rng = random.Random(seed)
            edge_map = generate_edge_map(rows, cols, rng, border_tabs=False)
            padded_image = ImageOps.expand(image, border=pad, fill=(0, 0, 0, 0))

            pieces = export_pieces(
                padded_image,
                boxes,
                edge_map,
                piece_w,
                piece_h,
                pad,
                tab_radius,
                rows,
                cols,
                output_dir,
                fmt,
            )

        if self.write_metadata.get():
            metadata_path = os.path.join(output_dir, "pieces.json")
            with open(metadata_path, "w", encoding="utf-8") as handle:
                json.dump([piece.__dict__ for piece in pieces], handle, indent=2)

        return len(pieces)

    def _generation_succeeded(self, count: int) -> None:
        self.generate_button.config(state=tk.NORMAL)
        self.status.set(self._("status.done", count=count, output_dir=self.output_dir.get()))
        messagebox.showinfo(self._("dialog.success"), self._("dialog.success_message", count=count))

    def _generation_failed(self, error: str) -> None:
        self.generate_button.config(state=tk.NORMAL)
        self.status.set(self._("status.failed"))
        messagebox.showerror(self._("dialog.generation_failed"), error)


def main() -> None:
    app = PuzzleGeneratorGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
