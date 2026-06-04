import argparse
import json
import os
import random
from dataclasses import dataclass
from typing import List, Tuple

from PIL import Image, ImageChops, ImageDraw, ImageOps


@dataclass
class PieceInfo:
    row: int
    col: int
    x: int
    y: int
    width: int
    height: int
    file: str
    offset_x: int
    offset_y: int
    image_width: int
    image_height: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export jigsaw-style grid pieces from an image."
    )
    parser.add_argument("input", help="Path to the source image.")
    parser.add_argument("--rows", type=int, default=4, help="Number of rows.")
    parser.add_argument("--cols", type=int, default=4, help="Number of columns.")
    parser.add_argument(
        "--output",
        default="pieces",
        help="Output directory for pieces (will be created if missing).",
    )
    parser.add_argument(
        "--format",
        default="png",
        choices=["png", "jpg", "jpeg", "webp"],
        help="Output image format.",
    )
    parser.add_argument(
        "--metadata",
        action="store_true",
        help="Also write pieces.json with piece metadata.",
    )
    parser.add_argument(
        "--tab-size",
        type=float,
        default=0.35,
        help="Tab diameter ratio relative to piece size (0.1 to 0.45).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for reproducible edge directions.",
    )
    return parser.parse_args()


def generate_edge_map(
    rows: int, cols: int, rng: random.Random, border_tabs: bool
) -> List[List[dict]]:
    edges = [
        [
            {"top": 0, "right": 0, "bottom": 0, "left": 0}
            for _ in range(cols)
        ]
        for _ in range(rows)
    ]

    for r in range(rows):
        for c in range(cols - 1):
            direction = rng.choice([1, -1])
            edges[r][c]["right"] = direction
            edges[r][c + 1]["left"] = -direction

    for r in range(rows - 1):
        for c in range(cols):
            direction = rng.choice([1, -1])
            edges[r][c]["bottom"] = direction
            edges[r + 1][c]["top"] = -direction

    if border_tabs:
        for c in range(cols):
            edges[0][c]["top"] = rng.choice([1, -1])
            edges[rows - 1][c]["bottom"] = rng.choice([1, -1])
        for r in range(rows):
            edges[r][0]["left"] = rng.choice([1, -1])
            edges[r][cols - 1]["right"] = rng.choice([1, -1])

    return edges


def draw_irregular_tab(
    draw: ImageDraw.ImageDraw,
    center: Tuple[int, int],
    radius: int,
    orientation: str,
    fill: int,
) -> None:
    x, y = center
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill)

    small_radius = max(2, int(radius * 0.55))
    offset = max(1, int(radius * 0.35))
    if orientation in {"top", "bottom"}:
        small_center = (x + offset, y)
    else:
        small_center = (x, y + offset)

    sx, sy = small_center
    draw.ellipse(
        (sx - small_radius, sy - small_radius, sx + small_radius, sy + small_radius),
        fill=fill,
    )


def build_piece_mask(
    piece_w: int,
    piece_h: int,
    pad: int,
    edges: dict,
    tab_radius: int,
) -> Image.Image:
    mask = Image.new("L", (piece_w + 2 * pad, piece_h + 2 * pad), 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle((pad, pad, pad + piece_w, pad + piece_h), fill=255)

    edge_specs = [
        ("top", (pad + piece_w // 2, pad)),
        ("bottom", (pad + piece_w // 2, pad + piece_h)),
        ("left", (pad, pad + piece_h // 2)),
        ("right", (pad + piece_w, pad + piece_h // 2)),
    ]

    for side, center in edge_specs:
        direction = edges.get(side, 0)
        if direction == 0:
            continue
        fill = 255 if direction > 0 else 0
        draw_irregular_tab(draw, center, tab_radius, side, fill)

    return mask


def compute_piece_boxes(
    width: int, height: int, rows: int, cols: int
) -> List[Tuple[int, int, int, int]]:
    if rows <= 0 or cols <= 0:
        raise ValueError("rows and cols must be positive integers")

    piece_w = width // cols
    piece_h = height // rows
    if piece_w == 0 or piece_h == 0:
        raise ValueError("image is too small for the requested grid")

    boxes: List[Tuple[int, int, int, int]] = []
    for r in range(rows):
        for c in range(cols):
            left = c * piece_w
            upper = r * piece_h
            right = left + piece_w
            lower = upper + piece_h
            boxes.append((left, upper, right, lower))
    return boxes


def export_pieces(
    image: Image.Image,
    boxes: List[Tuple[int, int, int, int]],
    edges: List[List[dict]],
    piece_w: int,
    piece_h: int,
    pad: int,
    tab_radius: int,
    rows: int,
    cols: int,
    output_dir: str,
    fmt: str,
) -> List[PieceInfo]:
    os.makedirs(output_dir, exist_ok=True)

    format_map = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP"}
    save_format = format_map[fmt]
    needs_rgb = save_format == "JPEG"

    piece_infos: List[PieceInfo] = []
    idx = 0
    for r in range(rows):
        for c in range(cols):
            left, upper, right, lower = boxes[idx]
            idx += 1

            crop_box = (left, upper, right + 2 * pad, lower + 2 * pad)
            piece = image.crop(crop_box).convert("RGBA")
            mask = build_piece_mask(piece_w, piece_h, pad, edges[r][c], tab_radius)
            existing_alpha = piece.getchannel("A")
            piece.putalpha(ImageChops.multiply(existing_alpha, mask))

            if needs_rgb:
                background = Image.new("RGB", piece.size, (255, 255, 255))
                background.paste(piece, mask=piece.getchannel("A"))
                piece_to_save = background
            else:
                piece_to_save = piece
            filename = f"piece_r{r}_c{c}.{fmt}"
            out_path = os.path.join(output_dir, filename)
            piece_to_save.save(out_path, format=save_format)

            piece_infos.append(
                PieceInfo(
                    row=r,
                    col=c,
                    x=left,
                    y=upper,
                    width=piece_w,
                    height=piece_h,
                    file=filename,
                    offset_x=pad,
                    offset_y=pad,
                    image_width=piece_w + 2 * pad,
                    image_height=piece_h + 2 * pad,
                )
            )

    return piece_infos


def main() -> int:
    args = parse_args()

    if not os.path.exists(args.input):
        raise FileNotFoundError(f"input image not found: {args.input}")

    with Image.open(args.input) as image:
        image = image.convert("RGBA")
        piece_w = image.width // args.cols
        piece_h = image.height // args.rows
        if piece_w == 0 or piece_h == 0:
            raise ValueError("image is too small for the requested grid")

        crop_w = piece_w * args.cols
        crop_h = piece_h * args.rows
        image = image.crop((0, 0, crop_w, crop_h))

        boxes = compute_piece_boxes(crop_w, crop_h, args.rows, args.cols)
        if not 0.1 <= args.tab_size <= 0.45:
            raise ValueError("tab-size must be between 0.1 and 0.45")
        tab_radius = max(2, int(min(piece_w, piece_h) * args.tab_size / 2))
        pad = tab_radius

        rng = random.Random(args.seed)
        edge_map = generate_edge_map(args.rows, args.cols, rng, border_tabs=False)
        padded_image = ImageOps.expand(image, border=pad, fill=(0, 0, 0, 0))

        pieces = export_pieces(
            padded_image,
            boxes,
            edge_map,
            piece_w,
            piece_h,
            pad,
            tab_radius,
            args.rows,
            args.cols,
            args.output,
            args.format,
        )

    if args.metadata:
        metadata_path = os.path.join(args.output, "pieces.json")
        with open(metadata_path, "w", encoding="utf-8") as handle:
            json.dump([piece.__dict__ for piece in pieces], handle, indent=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())