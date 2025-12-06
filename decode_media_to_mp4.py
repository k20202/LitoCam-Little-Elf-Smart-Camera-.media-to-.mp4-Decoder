import subprocess
from pathlib import Path
import shutil
import datetime
import random
import string

# ========= CONFIGURE THESE =========

# Root folder that contains your 1764xxxx_xxxx directories
ROOT_DIR = Path(r"CHANGE ME")

# Name of folder (inside ROOT_DIR) where all final mp4s will be collected.
MOVE_TO_SUBFOLDER = "allmp4s"   # set to None if you don't want them moved

# Extension of camera files
EXTENSION = "media"

# Number of bytes to strip from start of each .media file
HEADER_SIZE = 24

# If ffmpeg is NOT on PATH, put full path here, e.g. r"C:\ffmpeg\bin\ffmpeg.exe"
FFMPEG_PATH = "ffmpeg"  # leave as "ffmpeg" if it's already on PATH

# ===================================


def get_ffmpeg_cmd() -> str:
    """Return ffmpeg executable to use."""
    return FFMPEG_PATH


def is_unix_epoch_string(s: str) -> bool:
    """Return True if s looks like an integer unix epoch."""
    return s.isdigit() and not s.startswith("0")


def date_or_self(folder_name: str, use_hex: bool = False) -> str:
    """
    Emulates dateOrSelf from the bash script:
    - If folder name starts with a unix epoch (before '_'), convert to YYYYMMDD-HHMMSS
    - Otherwise, return the name (plus optional random hex).
    """
    base = folder_name.split("_")[0]
    if is_unix_epoch_string(base):
        try:
            ts = int(base)
            dt = datetime.datetime.fromtimestamp(ts)
            return dt.strftime("%Y%m%d-%H%M%S")
        except (ValueError, OSError):
            pass

    if use_hex:
        rand_hex = "".join(random.choices(string.hexdigits.upper(), k=8))
        return f"{folder_name}_{rand_hex}"
    else:
        return folder_name


def build_hevc_stream_from_media_files(media_files, raw_path: Path):
    """Create a single raw HEVC stream by concatenating .media files without their custom headers."""
    with raw_path.open("wb") as out:
        for mf in media_files:
            with mf.open("rb") as f:
                data = f.read()
            if len(data) <= HEADER_SIZE:
                print(f"  [WARN] Skipping too-small file: {mf.name}")
                continue
            out.write(data[HEADER_SIZE:])


def process_subfolder(subdir: Path):
    """
    For one camera folder (e.g. 1764695917_0600), find all *.media files,
    strip headers, join them into a .h265, then ffmpeg -> .mp4.
    """
    media_files = sorted(subdir.glob(f"*.{EXTENSION}"))
    if not media_files:
        print(f"[SKIP] No *.{EXTENSION} files in {subdir}")
        return None

    # Name for output based on folder name (timestamp etc.)
    output_name = date_or_self(subdir.name)
    raw_hevc = subdir / f"{output_name}.h265"
    output_mp4 = subdir / f"{output_name}.mp4"

    print(f"  [INFO] Building raw HEVC: {raw_hevc.name} from {len(media_files)} chunks")
    build_hevc_stream_from_media_files(media_files, raw_hevc)

    ffmpeg_cmd = [
        get_ffmpeg_cmd(),
        "-y",
        "-f", "hevc",          # tell ffmpeg it's a raw HEVC stream
        "-i", str(raw_hevc),
        "-c", "copy",
        str(output_mp4),
    ]

    print(f"  [FFMPEG] Creating {output_mp4.name}")
    try:
        subprocess.run(ffmpeg_cmd, check=True)
    except FileNotFoundError:
        print("ERROR: ffmpeg not found. Set FFMPEG_PATH at top of the script.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"  [ERROR] ffmpeg failed for {subdir}: {e}")
        return None
    finally:
        # Clean up the temporary raw file
        if raw_hevc.exists():
            raw_hevc.unlink()

    return output_mp4


def main():
    root = ROOT_DIR
    if not root.is_dir():
        print(f"ERROR: ROOT_DIR does not exist or is not a directory: {root}")
        return

    print(f"Root folder: {root}")

    subdirs = [p for p in root.iterdir() if p.is_dir()]
    # don't re-process the output folder if it already exists
    if MOVE_TO_SUBFOLDER and (root / MOVE_TO_SUBFOLDER) in subdirs:
        subdirs.remove(root / MOVE_TO_SUBFOLDER)

    if not subdirs:
        print("No subfolders found to process.")
        return

    created_mp4s = []

    for idx, subdir in enumerate(sorted(subdirs), start=1):
        print(f"\n[{idx}/{len(subdirs)}] Processing folder: {subdir.name}")
        out = process_subfolder(subdir)
        if out is not None and out.exists():
            created_mp4s.append(out)

    if not created_mp4s:
        print("\nNo MP4 files created.")
        return

    # Move all mp4 files into one folder if requested
    if MOVE_TO_SUBFOLDER:
        dest_dir = root / MOVE_TO_SUBFOLDER
        dest_dir.mkdir(exist_ok=True)
        print(f"\nMoving {len(created_mp4s)} MP4 files into: {dest_dir}")
        for mp4 in created_mp4s:
            target = dest_dir / mp4.name
            print(f"  {mp4.name} -> {target}")
            if target.exists():
                target.unlink()
            shutil.move(str(mp4), str(target))

        print("\nDone. Check your MP4 files in:")
        print(f"  {dest_dir}")
    else:
        print("\nDone. MP4 files are in:")
        print(f"  {root}")


if __name__ == "__main__":
    main()

