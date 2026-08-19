"""Image preprocessing for the PRAHARI anemia model.

CP-AnemiC ships ROI-cropped palpebral conjunctiva images as RGBA PNGs of
heterogeneous sizes (verified in Hour 2). Therefore:

- the ROI stage is a pass-through for this dataset (crops are already ROI),
- preprocessing handles alpha compositing (RGBA -> RGB over white),
- non-square crops are resized aspect-preserving and white-padded to a
  square (avoids distorting the thin conjunctiva strip).

Color is preserved throughout: pallor is a color signal.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

# ImageNet statistics used for normalization in training transforms.
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def load_rgb(path: str | Path) -> Image.Image:
    """Open an image and return an RGB PIL image (alpha composited over white).

    Raises OSError for corrupt/unreadable files.
    """
    with Image.open(path) as im:
        im.load()
        if im.mode == "RGB":
            return im.convert("RGB")
        if im.mode in ("RGBA", "LA", "PA"):
            rgba = im.convert("RGBA")
            background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
            composited = Image.alpha_composite(background, rgba)
            return composited.convert("RGB")
        return im.convert("RGB")


def preprocess_image(
    path: str | Path,
    size: int = 224,
) -> np.ndarray:
    """Load, alpha-composite, aspect-preserve resize and white-pad to ``size``.

    Returns a uint8 array of shape (size, size, 3) in RGB order.
    """
    img = load_rgb(path)
    img.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (size, size), (255, 255, 255))
    x = (size - img.width) // 2
    y = (size - img.height) // 2
    canvas.paste(img, (x, y))
    return np.asarray(canvas, dtype=np.uint8)


def normalize(arr: np.ndarray) -> np.ndarray:
    """Normalize a uint8 RGB array (0-255) to float32 with ImageNet stats.

    Shape: (H, W, 3) uint8 in -> (H, W, 3) float32 out.
    """
    if arr.dtype != np.uint8:
        raise ValueError(f"expected uint8 input, got {arr.dtype}")
    img = arr.astype(np.float32) / 255.0
    mean = np.array(IMAGENET_MEAN, dtype=np.float32)
    std = np.array(IMAGENET_STD, dtype=np.float32)
    return (img - mean) / std


def to_chw_tensor(arr: np.ndarray) -> np.ndarray:
    """Convert an (H, W, 3) array to (3, H, W) float32 (PyTorch CHW order)."""
    return np.ascontiguousarray(arr.transpose(2, 0, 1))
