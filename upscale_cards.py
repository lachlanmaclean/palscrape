#!/usr/bin/env python3
"""
Batch-upscales the landscape-oriented "Structure" card images (the ones
that print rotated 90deg and looked noticeably soft at their native
400x286 source resolution) using Real-ESRGAN 4x, then updates both the
root card_images/ and the Vite app's public/card_images/ in place.

Requires tools/realesrgan/ -- run tools/setup_upscaler.py first.

Usage:
    python upscale_cards.py
"""

import glob
import os
import shutil
import subprocess
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
UPSCALER_EXE = os.path.join(ROOT, "tools", "realesrgan", "realesrgan-ncnn-vulkan.exe")
UPSCALER_MODELS = os.path.join(ROOT, "tools", "realesrgan", "models")
CARD_DIRS = [
    os.path.join(ROOT, "card_images"),
    os.path.join(ROOT, "public", "card_images"),
]


def find_landscape_images(base_dir):
    landscape = []
    for path in sorted(glob.glob(os.path.join(base_dir, "*", "*.png"))):
        with Image.open(path) as im:
            if im.width > im.height:
                landscape.append(path)
    return landscape


def upscale_in_place(path):
    tmp_out = path + ".upscaled.png"
    result = subprocess.run(
        [
            UPSCALER_EXE,
            "-i", path,
            "-o", tmp_out,
            "-n", "realesrgan-x4plus",
            "-m", UPSCALER_MODELS,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not os.path.exists(tmp_out):
        print(f"  FAILED: {path}\n{result.stderr}")
        return False
    os.replace(tmp_out, path)
    return True


def main():
    if not os.path.exists(UPSCALER_EXE):
        print("Upscaler not found. Run: python tools/setup_upscaler.py")
        sys.exit(1)

    primary_dir = os.path.join(ROOT, "card_images")
    landscape_paths = find_landscape_images(primary_dir)
    print(f"Found {len(landscape_paths)} landscape card images to upscale.")

    for path in landscape_paths:
        rel = os.path.relpath(path, primary_dir)
        print(f"Upscaling {rel} ...")
        if not upscale_in_place(path):
            continue

        # Mirror the upscaled file into public/card_images (the Vite static copy).
        mirror_path = os.path.join(ROOT, "public", "card_images", rel)
        if os.path.exists(mirror_path):
            shutil.copy2(path, mirror_path)

    print("Done.")


if __name__ == "__main__":
    main()
