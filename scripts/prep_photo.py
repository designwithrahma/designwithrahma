from __future__ import annotations

import io
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def prepare_photo(input_path: Path, output_path: Path) -> None:
    if not input_path.exists():
        raise FileNotFoundError(
            f"Photo not found: {input_path}\n"
            "Place your photo in the project root as source-photo.jpg"
        )

    print(f"Reading photo: {input_path.name}")

    # Remove the original background.
    removed_background = remove(input_path.read_bytes())
    subject = Image.open(io.BytesIO(removed_background)).convert("RGBA")

    # Remove unnecessary transparent space around the subject.
    bounding_box = subject.getbbox()

    if bounding_box:
        subject = subject.crop(bounding_box)

    # Create a clean white square canvas.
    canvas_size = 900
    margin = 70

    subject.thumbnail(
        (canvas_size - margin * 2, canvas_size - margin * 2),
        Image.Resampling.LANCZOS,
    )

    canvas = Image.new(
        "RGBA",
        (canvas_size, canvas_size),
        (255, 255, 255, 255),
    )

    x_position = (canvas_size - subject.width) // 2
    y_position = (canvas_size - subject.height) // 2

    canvas.alpha_composite(subject, (x_position, y_position))

    # Convert the image to grayscale.
    grayscale = np.array(canvas.convert("RGB").convert("L"))

    # Improve local contrast so facial details work better as ASCII.
    clahe = cv2.createCLAHE(
        clipLimit=2.2,
        tileGridSize=(8, 8),
    )

    enhanced = clahe.apply(grayscale)

    # Blend the enhanced image with the original grayscale image.
    final_image = cv2.addWeighted(
        enhanced,
        0.85,
        grayscale,
        0.15,
        0,
    )

    Image.fromarray(final_image).save(output_path)

    print(f"Prepared photo saved: {output_path}")


def main() -> None:
    input_name = sys.argv[1] if len(sys.argv) > 1 else "source-photo.jpg"
    output_name = sys.argv[2] if len(sys.argv) > 2 else "source-prepped.png"

    input_path = PROJECT_ROOT / input_name
    output_path = PROJECT_ROOT / output_name

    try:
        prepare_photo(input_path, output_path)
    except Exception as error:
        raise SystemExit(f"Photo preparation failed: {error}") from error


if __name__ == "__main__":
    main()