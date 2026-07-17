#!/usr/bin/env python3
"""
Downloads the Real-ESRGAN ncnn-vulkan Windows binary + model weights into
tools/realesrgan/, for use by upscale_cards.py. Not committed to git (it's
~50MB) -- run this once before running upscale_cards.py.

Source: the official xinntao/Real-ESRGAN release, which bundles the
prebuilt Windows exe together with the .param/.bin model weights (unlike
the newer upscayl-ncnn releases, which ship the binary alone).
"""

import io
import os
import urllib.request
import zipfile

RELEASE_URL = (
    "https://github.com/xinntao/Real-ESRGAN/releases/download/"
    "v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip"
)

DEST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "realesrgan")


def main():
    if os.path.exists(os.path.join(DEST_DIR, "realesrgan-ncnn-vulkan.exe")):
        print(f"Already installed at {DEST_DIR}")
        return

    print(f"Downloading {RELEASE_URL} ...")
    req = urllib.request.Request(RELEASE_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()

    os.makedirs(DEST_DIR, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for member in zf.namelist():
            basename = os.path.basename(member)
            if not basename:
                continue
            # Flatten the zip's single top-level folder into DEST_DIR directly.
            rel_parts = member.split("/")[1:]
            if not rel_parts:
                continue
            target = os.path.join(DEST_DIR, *rel_parts)
            if member.endswith("/"):
                os.makedirs(target, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with zf.open(member) as src, open(target, "wb") as out:
                out.write(src.read())

    print(f"Installed to {DEST_DIR}")


if __name__ == "__main__":
    main()
