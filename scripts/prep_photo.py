"""Prepare a portrait for clean ASCII conversion."""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT = Path(sys.argv[1]) if len(sys.argv) > 1 else PROJECT_ROOT / "source-photo.jpg"
OUTPUT = Path(sys.argv[2]) if len(sys.argv) > 2 else PROJECT_ROOT / "source-prepped.png"


def prepare_photo(input_path: Path, output_path: Path) -> None:
    if not input_path.exists():
        raise FileNotFoundError(f"Photo not found: {input_path}")

    cutout = remove(Image.open(input_path).convert("RGBA"))
    rgba = np.array(cutout)
    rgb = rgba[:, :, :3]
    alpha = rgba[:, :, 3]

    grayscale = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.6, tileGridSize=(8, 8))
    grayscale = clahe.apply(grayscale)
    grayscale = cv2.convertScaleAbs(grayscale, alpha=1.05, beta=18)

    mask = alpha.astype(np.float32) / 255.0
    mask = cv2.GaussianBlur(mask, (0, 0), 1.0)
    composed = grayscale.astype(np.float32) * mask + 255.0 * (1.0 - mask)
    composed = np.clip(composed, 0, 255).astype(np.uint8)

    Image.fromarray(composed, mode="L").save(output_path)
    print(f"wrote {output_path} {composed.shape}")


def main() -> None:
    try:
        prepare_photo(INPUT, OUTPUT)
    except Exception as error:
        raise SystemExit(f"Photo preparation failed: {error}") from error


if __name__ == "__main__":
    main()
