# API.md

**PRAHARI — Person 1 (AI/CV) · FastAPI AI Service (Hour 6, 2026-08-17)**

## Setup

```bash
# Install dependencies (if not already installed)
pip install fastapi uvicorn python-multipart python-dotenv

# Start the server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Open Swagger UI
# http://localhost:8000/docs
```

## Configuration (environment variables)

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_MODEL` | `random_forest` | Model to use (`random_forest` or `cnn`) |
| `MAX_IMAGE_SIZE` | `4096` | Max long-side of uploaded image (px) |
| `CONFIDENCE_THRESHOLD` | `0.5` | Probability threshold for anemic/non_anemic |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Allowed CORS origins |
| `QUALITY_MIN_BRIGHTNESS` | `30` | Min brightness (0-255) |
| `QUALITY_MIN_SHARPNESS` | `50` | Min Laplacian variance |
| `QUALITY_MIN_CONTRAST` | `10` | Min grayscale std |

## Endpoints

### GET /health

```json
{
  "status": "ok",
  "model_loaded": true,
  "model": "random_forest_color_baseline",
  "version": "1.0"
}
```

### GET /models

```json
{
  "name": "random_forest_color_baseline",
  "version": "1.0",
  "type": "sklearn RandomForestClassifier (binary)",
  "dataset": "CP-AnemiC (Mendeley 10.17632/m53vz6b7fx.1)",
  "labels": ["non_anemic", "anemic"],
  "feature_pipeline": "alpha-masked RGB/LAB tissue features (19) + StandardScaler",
  "training_seed": 42,
  "notes": "non-clinical model version; screening research prototype"
}
```

### POST /api/v1/anemia/screen

**Request:** `multipart/form-data` with field `image`

**Example (curl):**

```bash
curl -X POST \
  -F "image=@path/to/conjunctiva_image.png" \
  http://127.0.0.1:8000/api/v1/anemia/screen
```

**Success (200):**

```json
{
  "success": true,
  "prediction": {
    "label": "anemic",
    "model_probability": 0.912,
    "model_confidence": 0.912
  },
  "image_quality": {
    "status": "good",
    "score": 1.0,
    "checks": {"blur": "pass", "brightness": "pass", "contrast": "pass", "resolution": "pass"},
    "reasons": []
  },
  "inference": {
    "model": "random_forest_color_baseline",
    "version": "1.0",
    "dataset": "CP-AnemiC (Mendeley 10.17632/m53vz6b7fx.1)",
    "latency_ms": 58.4
  },
  "api_latency_ms": 59.1
}
```

**Quality rejected (200, success=false):**

```json
{
  "success": false,
  "prediction": null,
  "image_quality": {
    "status": "poor",
    "score": 0.35,
    "checks": {"blur": "fail"},
    "reasons": ["blur"]
  },
  "inference": null,
  "error": {
    "code": "IMAGE_QUALITY_LOW",
    "message": "Image quality is insufficient. Please retake the image."
  }
}
```

**Error responses:**

| HTTP | Code | Meaning |
|------|------|---------|
| 400 | `INVALID_IMAGE` | Empty, unreadable, or too-small file |
| 400 | `IMAGE_TOO_LARGE` | Exceeds max upload size |
| 415 | `UNSUPPORTED_IMAGE` | Unsupported content type |
| 503 | `MODEL_NOT_LOADED` | Model not loaded (service starting) |
| 500 | `INFERENCE_FAILED` | Unexpected error |

## Error handling

- No Python stack traces are exposed in responses.
- Quality failures return HTTP 200 with `success: false` (application-level).
- Hard failures (invalid input, model down) return appropriate HTTP error codes.

## Integration

- **Frontend:** See `AI_API_CONTRACT.md` for JavaScript fetch examples.
- **Swayam:** Consume `prediction.label` and `prediction.model_probability` as the image-based anemia signal.
- **Arya:** Call the API independently from the backend (Python requests or httpx).

## Medical disclaimer

This endpoint provides an **image-based anemia screening prediction** and is
not a clinical diagnostic tool. The model was trained on the CP-AnemiC dataset
(708 conjunctival images, children aged 6–59 months in Ghana). Results should
be interpreted by qualified healthcare professionals within the PRAHARI
screening workflow.
