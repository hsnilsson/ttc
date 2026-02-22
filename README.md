# Test Target Cropper (ttc)

Creates composite images from test target photos (DNG or PNG) for pixel peeping—4 corner crops plus center crop in a 2×2 grid with center overlay. Good for lens sharpness and resolution analysis.

## Installation

**Easiest (Windows):** Download `ttc.exe` from the [Releases](https://github.com/hsnilsson/ttc/releases) page. No Python required.

**Unix/Linux/macOS (install script):**
```bash
curl -sSL https://raw.githubusercontent.com/hsnilsson/ttc/main/install.sh | bash
```

**Windows (install script):**
```cmd
curl -sSL https://raw.githubusercontent.com/hsnilsson/ttc/main/install.bat | cmd
```

**From source:**
```bash
git clone https://github.com/hsnilsson/ttc.git && cd ttc
pip install -r requirements.txt
python ttc.py --help
```

**Build your own .exe:** From repo root, run `python build_exe.py`. Produces `ttc.exe` (includes rawpy for full‑res DNG).

## Requirements

Python 3.7+. Install deps: `pip install -r requirements.txt` (Pillow, rawpy, numpy).

## Usage

```bash
ttc                          # current directory → ./crops
ttc /path/to/photos           # custom input
ttc /path/to/photos -o out    # custom output dir
```

**DNG vs PNG:** By default ttc prefers **DNG** (processes only DNGs if present). If there are no DNGs but there are PNGs, it asks before using PNGs. To use only PNGs: `ttc --use-pngs` (or `--use-pngs-only`).

### Command line options

```
usage: ttc [-h] [-o OUTPUT] [--use-pngs-only] [-v] [input_dir]

Create composite images from Vlad's test target photos

positional arguments:
  input_dir             Directory containing PNG/DNG files (default: current directory)

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output directory for composite images (default: INPUT_DIR/crops)
  --use-pngs-only, --use-pngs
                        Only process PNG files; default is to prefer DNG and fall back to PNG only after asking
  -v, --version         show program's version number and exit

Examples:
  ttc                    # Process current directory
  ttc ../test_photos     # Process parent directory
  ttc /path/to/photos    # Process absolute path
  ttc . -o results       # Custom output directory
```

## Configuration

Crop positions are percentage-based and set in `ttc.py`: `corner_positions` and `center_crop_percent`. Edit those to match your test target layout.

## Output

One composite per input file: `filename_composite.png` in the output directory (default `INPUT_DIR/crops/`). No compression; square corner crops; center overlay.

## License

MIT
