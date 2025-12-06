# LitoCam / Little Elf Smart Camera – .media to .mp4 Decoder

This tool converts the proprietary `.media` video chunks stored on
the internal SD card of LitoCam / Little Elf smart cameras into playable `.mp4` files.

It works by:
1. Reading each `.media` file
2. Stripping the first 24 bytes of the custom header
3. Concatenating the raw HEVC stream
4. Passing it to FFmpeg to produce a proper `.mp4` file

This Python implementation is based on research into the camera’s storage format
and reliably rebuilds recordings into watchable videos.

---

## ✔ Features

- Converts **all folders** containing `.media` files
- Automatically names output files using the camera timestamp
- Produces `.mp4` files without re-encoding (lossless)
- Optionally collects all MP4 output into one folder
- Fully cross-platform (Windows, Linux, macOS)

---

## 📦 Requirements

- Python 3.8+
- FFmpeg installed and available on the PATH  
  (or provide full path inside the script)

---

## 🔧 Usage

1. Edit the script and set:

```python
ROOT_DIR = r"C:\\path\\to\\your\\camera\\folder"
