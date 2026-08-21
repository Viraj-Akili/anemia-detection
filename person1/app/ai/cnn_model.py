"""Lightweight CNN for the PRAHARI anemia screening signal.

Hour 4: MobileNetV2 (ImageNet-pretrained) with the classifier head replaced
by a binary output (1 logit + sigmoid). The factory is architecture-
agnostic enough to swap in MobileNetV3 / EfficientNet later.

Output: raw logits (shape (N, 1)) — apply sigmoid for P(anemic).
"""

from __future__ import annotations

import json
from pathlib import Path

import torch
import torch.nn as nn
from torchvision import models

BACKBONES = {
    "mobilenet_v2": models.mobilenet_v2,
    "mobilenet_v3_small": models.mobilenet_v3_small,
    "efficientnet_b0": models.efficientnet_b0,
}

# Final linear input features per backbone
_FEAT_DIM = {
    "mobilenet_v2": 1280,
    "mobilenet_v3_small": 576,
    "efficientnet_b0": 1280,
}


class AnemiaCNN(nn.Module):
    """Binary (anemic / non-anemic) classifier built on a pretrained backbone.

    ``forward`` returns logits of shape (N, 1).
    """

    def __init__(self, backbone: str = "mobilenet_v2", num_classes: int = 1, pretrained: bool = True):
        super().__init__()
        if backbone not in BACKBONES:
            raise ValueError(f"unsupported backbone {backbone!r}; choose from {sorted(BACKBONES)}")
        self.backbone_name = backbone
        builder = BACKBONES[backbone]
        self.backbone = builder(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1 if pretrained else None)

        feat_dim = _FEAT_DIM[backbone]
        # Replace the head: backbone.classifier is a Sequential for MobileNet.
        if hasattr(self.backbone, "classifier"):
            self.backbone.classifier = nn.Sequential(
                nn.Dropout(p=0.2, inplace=False),
                nn.Linear(feat_dim, num_classes),
            )
        else:  # e.g. efficientnet has `classifier` too; keep generic fallback
            self.backbone.classifier = nn.Linear(feat_dim, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)

    def num_parameters(self, trainable_only: bool = False) -> int:
        params = self.parameters() if not trainable_only else (p for p in self.parameters() if p.requires_grad)
        return sum(p.numel() for p in params)


def create_model(backbone: str = "mobilenet_v2", pretrained: bool = True, device: str | torch.device = "cpu") -> AnemiaCNN:
    """Create the model and move it to the requested device."""
    model = AnemiaCNN(backbone=backbone, num_classes=1, pretrained=pretrained)
    return model.to(device)


def save_checkpoint(model: AnemiaCNN, path: str | Path, extra: dict | None = None) -> None:
    """Save state dict + metadata to a checkpoint file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"state_dict": model.state_dict(), "backbone": model.backbone_name}
    if extra:
        payload.update(extra)
    torch.save(payload, path)


def load_checkpoint(
    path: str | Path,
    device: str | torch.device = "cpu",
    backbone: str | None = None,
) -> AnemiaCNN:
    """Load a checkpoint saved by save_checkpoint. ``backbone`` overrides on mismatch."""
    path = Path(path)
    payload = torch.load(path, map_location=device, weights_only=False)
    model = create_model(backbone=payload.get("backbone", backbone or "mobilenet_v2"), pretrained=False, device=device)
    model.load_state_dict(payload["state_dict"])
    return model


def predict_proba(model: AnemiaCNN, batch: torch.Tensor, device: str | torch.device = "cpu") -> torch.Tensor:
    """P(anemic) for a normalized (N, 3, H, W) batch. Returns (N,) float."""
    model.eval()
    with torch.inference_mode():
        logits = model(batch.to(device))
        return torch.sigmoid(logits).squeeze(1).cpu()


def save_metadata(path: str | Path, metadata: dict) -> None:
    Path(path).write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")
