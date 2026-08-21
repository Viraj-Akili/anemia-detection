#!/usr/bin/env python
"""Train the lightweight CNN (MobileNetV2) for PRAHARI anemia screening (Hour 4).

Reuses the Hour-2 leakage-safe split (data/processed/{train,val,test}).
Two-stage training with best-checkpoint snapshotting:
  Stage 1: frozen backbone, train classification head (AdamW, lr=1e-3)
  Stage 2: unfreeze later backbone blocks, fine-tune (AdamW, lr=1e-4)
The best state (validation anemic-class F1) is snapshotted every epoch.
Test is evaluated ONCE after model selection.

Class imbalance (60/40): the majority class IS the screening-priority class
(anemic), so plain BCE is used by default (matches the published CP-AnemiC
MobileNet work). Use --pos-weight auto for balanced weighting instead.

Run from repository root:  python scripts/train_cnn.py
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from torch.utils.data import DataLoader

import sys as _sys
from pathlib import Path as _Path

_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from app.ai.cnn_model import create_model, save_checkpoint, save_metadata
from app.ai.dataset import eval_transform, load_splits

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
CHECKPOINT_PATH = PROJECT_ROOT / "models" / "mobilenetv2_best.pth"
METADATA_PATH = PROJECT_ROOT / "models" / "mobilenetv2_metadata.json"
HISTORY_PATH = RESULTS_DIR / "cnn_training_history.csv"
ANEMIC_IDX = 0  # dataset classes are sorted: ['anemic', 'non_anemic']


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def evaluate(model, loader: DataLoader, device: torch.device) -> dict:
    """Full metrics on a loader (validation or test). Deterministic."""
    model.eval()
    y_true, y_prob = [], []
    with torch.inference_mode():
        for x, y in loader:
            y_true.extend(y.tolist())
            y_prob.extend(torch.sigmoid(model(x.to(device))).squeeze(1).cpu().tolist())
    y_true = np.array(y_true)
    y_prob = np.array(y_prob)
    y_pred = (y_prob >= 0.5).astype(int)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_anemic": float(precision_score(y_true, y_pred, pos_label=ANEMIC_IDX, zero_division=0)),
        "recall_anemic": float(recall_score(y_true, y_pred, pos_label=ANEMIC_IDX, zero_division=0)),
        "f1_anemic": float(f1_score(y_true, y_pred, pos_label=ANEMIC_IDX, zero_division=0)),
        "precision_non_anemic": float(precision_score(y_true, y_pred, pos_label=1 - ANEMIC_IDX, zero_division=0)),
        "recall_non_anemic": float(recall_score(y_true, y_pred, pos_label=1 - ANEMIC_IDX, zero_division=0)),
        "f1_non_anemic": float(f1_score(y_true, y_pred, pos_label=1 - ANEMIC_IDX, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
        "confusion_matrix": confusion_matrix(
            y_true, y_pred, labels=[1 - ANEMIC_IDX, ANEMIC_IDX]
        ).tolist(),  # [[tn, fp], [fn, tp]] matching baseline convention
        "n_samples": int(len(y_true)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Train MobileNetV2 for anemia screening.")
    parser.add_argument("--backbone", default="mobilenet_v2")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--epochs-head", type=int, default=8, help="stage 1: head-only epochs")
    parser.add_argument("--epochs-finetune", type=int, default=30, help="stage 2: fine-tune epochs")
    parser.add_argument("--lr-head", type=float, default=1e-3)
    parser.add_argument("--lr-finetune", type=float, default=1e-4)
    parser.add_argument("--unfreeze-from", type=int, default=14, help="unfreeze backbone.features[unfreeze_from:] in stage 2")
    parser.add_argument("--patience", type=int, default=15, help="early stop if no val-F1 improvement for N epochs")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--pos-weight", default="none", choices=["none", "auto"],
                        help="BCE positive-class weight: none (default) or auto (n_neg/n_pos from TRAIN)")
    parser.add_argument("--workers", type=int, default=0)
    args = parser.parse_args()

    set_seed(args.seed)

    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    device = torch.device(device)
    print(f"device: {device} ({torch.cuda.get_device_name(0) if device.type == 'cuda' else 'CPU'})")

    train_ds, val_ds, test_ds = load_splits(PROCESSED_DIR)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                              num_workers=args.workers, drop_last=False)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.workers)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.workers)
    print(f"train={len(train_ds)} val={len(val_ds)} test={len(test_ds)}")

    # Class weights from TRAIN only (documented strategy).
    pos_weight = None
    if args.pos_weight == "auto":
        n_pos = sum(1 for _, y in train_ds.samples if y == ANEMIC_IDX)
        n_neg = len(train_ds) - n_pos
        pos_weight = torch.tensor([n_neg / n_pos], device=device)
        print(f"[imbalance] pos_weight = {n_neg}/{n_pos} = {n_neg / n_pos:.3f} (from TRAIN only)")
    else:
        print("[imbalance] unweighted BCE — anemic is the majority class AND the screening-priority class; "
              "this favors anemic recall. Use --pos-weight auto to balance instead.")

    model = create_model(args.backbone, pretrained=True, device=device)
    print(f"[model] {args.backbone} | total params: {model.num_parameters()/1e6:.2f}M")

    criterion = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    history = []
    best_state = None
    best_val_f1 = -1.0
    best_epoch = 0

    def freeze_params(exclude_prefix: str | None = None) -> None:
        """Freeze everything except classifier (+ optionally features[exclude_prefix:])."""
        for name, p in model.named_parameters():
            if "classifier" in name:
                p.requires_grad = True
            elif exclude_prefix and name.startswith(exclude_prefix):
                p.requires_grad = True
            else:
                p.requires_grad = False

    no_improve = 0

    def run_stage(epochs: int, lr: float, stage_name: str) -> None:
        nonlocal best_state, best_val_f1, best_epoch, no_improve
        optimizer = torch.optim.AdamW(
            (p for p in model.parameters() if p.requires_grad), lr=lr, weight_decay=1e-4
        )
        for epoch in range(1, epochs + 1):
            model.train()
            total_loss, n = 0.0, 0
            for x, y in train_loader:
                x, y = x.to(device), y.to(device).float().unsqueeze(1)
                optimizer.zero_grad()
                loss = criterion(model(x), y)
                loss.backward()
                optimizer.step()
                total_loss += loss.item() * len(x)
                n += len(x)
            val = evaluate(model, val_loader, device)
            history.append(
                {"stage": stage_name, "epoch": len(history) + 1, "train_loss": total_loss / n,
                 **{k: v for k, v in val.items() if k != "confusion_matrix"}}
            )
            is_best = val["f1_anemic"] > best_val_f1
            if is_best:
                best_val_f1 = val["f1_anemic"]
                best_epoch = len(history)
                best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
                no_improve = 0
            else:
                no_improve += 1
            print(
                f"  [{stage_name} ep{epoch:02d}] loss={total_loss/n:.4f} "
                f"val acc={val['accuracy']:.3f} rec_an={val['recall_anemic']:.3f} "
                f"f1_an={val['f1_anemic']:.3f} auc={val['roc_auc']:.3f}"
                + ("  <-- best" if is_best else "")
            )
            if no_improve >= args.patience:
                print(f"  [early stop] no val-F1 improvement for {args.patience} epochs")
                break

    print("\n[stage 1] training classification head (backbone frozen) ...")
    freeze_params()
    run_stage(args.epochs_head, args.lr_head, "head")

    print(f"\n[stage 2] fine-tuning backbone.features[{args.unfreeze_from}:] lr={args.lr_finetune} ...")
    freeze_params(exclude_prefix=f"backbone.features.{args.unfreeze_from}")
    run_stage(args.epochs_finetune, args.lr_finetune, "finetune")

    best_val = history[best_epoch - 1]
    print(f"\n[select] best checkpoint = epoch {best_epoch} "
          f"(val anemic F1 = {best_val['f1_anemic']:.3f}, recall = {best_val['recall_anemic']:.3f}, "
          f"AUC = {best_val['roc_auc']:.3f})")

    model.load_state_dict(best_state)

    # --- save checkpoint + metadata ---
    classes = train_ds.classes
    save_checkpoint(model, CHECKPOINT_PATH, extra={"classes": classes, "backbone": args.backbone})
    metadata = {
        "architecture": args.backbone,
        "input_size": [3, 224, 224],
        "class_labels": classes,
        "training_seed": args.seed,
        "preprocessing": ["RGB", "ImageNet normalize", "224x224 white-padded crops"],
        "augmentation": ["RandomHorizontalFlip(0.5)", "RandomRotation(10, fill=255)",
                         "RandomAffine(translate 0.05, scale 0.95-1.05, fill=255)",
                         "ColorJitter(brightness 0.15, contrast 0.15, no hue/saturation)"],
        "loss": "BCEWithLogitsLoss" + (f" pos_weight={pos_weight.item():.3f}" if pos_weight is not None else " (unweighted)"),
        "epochs_head": args.epochs_head,
        "epochs_finetune": args.epochs_finetune,
        "best_epoch": best_epoch,
        "validation": best_val,
        "device": str(device),
        "model_version": "0.2.0-cnn",
        "total_parameters": int(model.num_parameters()),
        "torch_version": torch.__version__,
        "python_version": sys.version.split()[0],
    }
    save_metadata(METADATA_PATH, metadata)
    print(f"[save] checkpoint -> {CHECKPOINT_PATH}")

    # --- training history ---
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(history[0].keys()))
        writer.writeheader()
        writer.writerows(history)

    # --- latency (CPU always; GPU if CUDA) ---
    def measure_latency(dev: torch.device, repeats: int = 3) -> dict:
        m = create_model(args.backbone, pretrained=False, device=dev)
        m.load_state_dict(best_state)
        m.eval()
        tf = eval_transform()
        images = [Image.open(p).convert("RGB") for p, _ in test_ds.samples]
        times = []
        with torch.inference_mode():
            for _ in range(repeats):
                for img in images:
                    x = tf(img).unsqueeze(0).to(dev)
                    t0 = time.perf_counter()
                    m(x)
                    times.append((time.perf_counter() - t0) * 1000.0)
        times = np.array(times)
        return {"mean_ms": float(times.mean()), "median_ms": float(np.median(times)),
                "p95_ms": float(np.percentile(times, 95)), "n": int(len(times)), "device": str(dev)}

    gpu_lat = measure_latency(device) if device.type == "cuda" else None
    cpu_lat = measure_latency(torch.device("cpu"))
    latency = {"gpu": gpu_lat, "cpu": cpu_lat}
    (RESULTS_DIR / "cnn_latency.json").write_text(json.dumps(latency, indent=2), encoding="utf-8")
    print(f"[latency] cpu: mean={cpu_lat['mean_ms']:.1f}ms median={cpu_lat['median_ms']:.1f}ms p95={cpu_lat['p95_ms']:.1f}ms"
          + (f" | gpu: mean={gpu_lat['mean_ms']:.1f}ms" if gpu_lat else ""))

    # --- final TEST evaluation (ONCE, after model selection) ---
    print("\n[test] evaluating TEST once ...")
    test_metrics = evaluate(model, test_loader, device)
    test_metrics["model_path"] = str(CHECKPOINT_PATH)
    (RESULTS_DIR / "cnn_metrics.json").write_text(
        json.dumps({"model": args.backbone, **test_metrics, "latency": latency,
                    "selected_by": "validation anemic-class F1"}, indent=2), encoding="utf-8"
    )
    # confusion matrix figure
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cm = np.array(test_metrics["confusion_matrix"])  # [[tn, fp], [fn, tp]]
    fig, ax = plt.subplots(figsize=(5, 4.5))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1], ["non_anemic", "anemic"])
    ax.set_yticks([0, 1], ["non_anemic", "anemic"])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(f"CNN {args.backbone} — test set")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black")
    fig.colorbar(im, shrink=0.8)
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "cnn_confusion_matrix.png", dpi=120)
    plt.close(fig)
    print(f"[test] acc={test_metrics['accuracy']:.3f} prec_an={test_metrics['precision_anemic']:.3f} "
          f"rec_an={test_metrics['recall_anemic']:.3f} f1_an={test_metrics['f1_anemic']:.3f} "
          f"auc={test_metrics['roc_auc']:.3f}")
    print(f"[test] confusion [[tn,fp],[fn,tp]]: {test_metrics['confusion_matrix']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
