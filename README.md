<div align="center">

# Puzzle Generator

Generate jigsaw-style puzzle pieces from an image with a simple desktop GUI or command-line interface.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

## Notice

Update will be on [JigsawGenProject](https://github.com/NonInertialObserver/jigsawgen). This repo will be public archived.

## Overview

Puzzle Generator cuts an input image into a configurable grid of jigsaw-like pieces. Each piece is exported as an individual image with irregular tabs and blanks. The project includes:

- A Tkinter GUI for interactive use.
- A CLI for scripted/batch generation.
- Live preview of the first generated piece in the GUI.
- English and Chinese UI translations.
- Optional `pieces.json` metadata output.
- Reproducible piece shapes through a random seed.

Repository: <https://github.com/NonInertialObserver/puzzlegenerator/>

## Features

- Choose input image and output folder.
- Configure rows and columns.
- Export as `png`, `jpg`, `jpeg`, or `webp`.
- Adjust tab size between `0.10` and `0.45`.
- Use a seed for repeatable edge directions.
- Generate transparent pieces for formats that support alpha, such as PNG and WebP.
- Write optional metadata describing each generated piece.
- Switch GUI language between English and Chinese.

## Requirements

- Python 3.10 or newer is recommended.
- [Pillow](https://python-pillow.org/)
- Tkinter, which is included with most standard Python distributions.

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Or install Pillow directly:

```bash
pip install pillow
```

## Usage

### GUI

Run the desktop application:

```bash
python gui.pyw
```

In the GUI:

1. Select an input image.
2. Choose an output folder.
3. Configure rows, columns, output format, tab size, and seed.
4. Optionally enable `pieces.json` metadata output.
5. Use the language selector at the bottom of the window to switch between English and Chinese.
6. Click **Generate Pieces**.

The GUI shows a live preview of the first puzzle piece after an image is selected.

### CLI

Basic example:

```bash
python main.py input.png --rows 4 --cols 4 --output pieces --format png --metadata
```

With custom tab size and seed:

```bash
python main.py input.jpg --rows 6 --cols 8 --output output_pieces --format webp --tab-size 0.3 --seed 42 --metadata
```

CLI options:

```text
input                 Path to the source image.
--rows ROWS           Number of rows. Default: 4
--cols COLS           Number of columns. Default: 4
--output OUTPUT       Output directory. Default: pieces
--format FORMAT       Output format: png, jpg, jpeg, webp. Default: png
--metadata            Also write pieces.json with piece metadata.
--tab-size TAB_SIZE   Tab diameter ratio relative to piece size, from 0.1 to 0.45. Default: 0.35
--seed SEED           Random seed for reproducible edge directions. Default: 0
```

## Output

Generated pieces are named by row and column:

```text
piece_r0_c0.png
piece_r0_c1.png
piece_r1_c0.png
...
```

When metadata output is enabled, the output folder also contains `pieces.json`. Each entry includes information such as:

- `row` and `col`
- original image position `x` and `y`
- piece `width` and `height`
- output `file` name
- transparent padding offsets
- final piece image dimensions

## Internationalization

Translations are stored in:

```text
locale/lp.json
```

Currently supported languages:

- English (`en`)
- Chinese (`zh`)

The GUI language can be changed from the language selector at the bottom of the window. The language loader also supports environment-based detection through variables such as `PUZZLEGEN_LANG`, `LANGUAGE`, and `LANG`.

Example:

```bash
PUZZLEGEN_LANG=zh python gui.pyw
```

On Windows PowerShell:

```powershell
$env:PUZZLEGEN_LANG="zh"; python gui.pyw
```

## Building a Windows executable

The repository includes a PyInstaller spec file:

```text
gui.spec
```

Install PyInstaller if needed:

```bash
pip install pyinstaller
```

Build the GUI executable:

```bash
pyinstaller gui.spec
```

The build output is created under `dist/`.

> Note: The GUI uses `icon.ico` and translation data from `locale/lp.json`. If you change the packaging setup, make sure these resources are included with the distributed application.

## Project structure

```text
puzzlegenerator/
├── main.py              # CLI and core puzzle-piece generation functions
├── gui.pyw              # Tkinter desktop GUI
├── i18n.py              # Translation loader and language helpers
├── locale/lp.json       # English and Chinese translations
├── requirements.txt     # Python dependencies
├── gui.spec             # PyInstaller build configuration
├── icon.ico             # Application icon
└── LICENSE              # MIT license
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Third Party Notice

The icon file is from Google Material, which is under Apache 2.0 License
