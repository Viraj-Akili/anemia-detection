"""Datasets + transforms for the CNN (Hour 4).

Reuses the Hour-2 leakage-safe split: data/processed/{train,val,test}/{class}/.
Train gets conservative augmentation; val/test are deterministic.

Augmentation rationale (must preserve the pallor signal):
- horizontal flip: conjunctiva crops are approximately left-right symmetric
- small rotation / small affine translate+scale: field capture variation
- mild brightness/contrast jitter: lighting variation, NO hue/saturation shifts
No aggressive crops, color shifts, or large rotations.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms

from app.ai.preprocessing import IMAGENET_MEAN, IMAGENET_STD

IMAGE_SIZE = 224


def _base_transform() -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )


def train_transform() -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=10, fill=255),
            transforms.RandomAffine(degrees=0, translate=(0.05, 0.05), scale=(0.95, 1.05), fill=255),
            transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.0, hue=0.0),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )


def eval_transform() -> transforms.Compose:
    """Deterministic transform for validation AND test."""
    return _base_transform()


class ImageFolderDataset(Dataset):
    """ImageFolder-style dataset: dir/{class_name}/*.png.

    Class order is sorted (deterministic): ['anemic', 'non_anemic'].
    """

    def __init__(self, root: str | Path, transform=None):
        root = Path(root)
        self.classes = sorted(p.name for p in root.iterdir() if p.is_dir())
        self.class_to_idx = {c: i for i, c in enumerate(self.classes)}
        self.samples: list[tuple[Path, int]] = []
        for cls in self.classes:
            for img in sorted((root / cls).glob("*.png")):
                self.samples.append((img, self.class_to_idx[cls]))
        self.transform = transform

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        path, label = self.samples[idx]
        img = Image.open(path).convert("RGB")
        if self.transform is not None:
            img = self.transform(img)
        return img, label


def load_splits(processed_root: str | Path):
    """Return (train_ds, val_ds, test_ds) using the existing processed split."""
    root = Path(processed_root)
    train_ds = ImageFolderDataset(root / "train", transform=train_transform())
    val_ds = ImageFolderDataset(root / "val", transform=eval_transform())
    test_ds = ImageFolderDataset(root / "test", transform=eval_transform())
    return train_ds, val_ds, test_ds
