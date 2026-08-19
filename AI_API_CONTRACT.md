# AI_API_CONTRACT.md

**PRAHARI — Person 1 (AI/CV) · API Integration Contract (Hour 6, 2026-08-17)**

## 1. Overview

The AI/CV service exposes a FastAPI application providing image-based
anemia **screening predictions**.  This is a research prototype and is NOT
a clinical diagnostic tool.

The prediction is an **image-based signal only**.  Final risk determination
is handled by Swayam's multimodal PRAHARI risk engine, which combines the
AI signal with anthropometry, nutrition data, symptoms, and visit history.

## 2. Service URL

```
http://localhost:8000
```

Configurable via environment variables:
- `HOST` (default: `127.0.0.1`)
- `PORT` (default: `8000`)

## 3. Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check — model loading status |
| `GET` | `/models` | Model metadata (optional) |
| `POST` | `/api/v1/anemia/screen` | **Main endpoint** — screening prediction |
| `GET` | `/docs` | Swagger UI (auto-generated) |
| `GET` | `/openapi.json` | OpenAPI schema |

---

## 4. POST /api/v1/anemia/screen

### Request

```
Content-Type: multipart/form-data
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image` | file | Yes | Conjunctival (eye) image |

**Supported formats:** PNG, JPEG, WebP, BMP, TIFF

**Max file size:** Configurable via `MAX_IMAGE_SIZE_MB` (default: 4 MB)

### Success Response (200)

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
    "checks": {
      "blur": "pass",
      "brightness": "pass",
      "contrast": "pass",
      "resolution": "pass"
    },
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

### Quality Rejection Response (200, success=false)

```json
{
  "success": false,
  "prediction": null,
  "image_quality": {
    "status": "poor",
    "score": 0.35,
    "checks": {
      "blur": "fail",
      "brightness": "pass",
      "contrast": "pass",
      "resolution": "pass"
    },
    "reasons": ["blur"]
  },
  "inference": null,
  "error": {
    "code": "IMAGE_QUALITY_LOW",
    "message": "Image quality is insufficient. Please retake the image."
  },
  "api_latency_ms": 5.2
}
```

### Error Responses

| HTTP | Code | When |
|------|------|------|
| 400 | `INVALID_IMAGE` | Missing file, empty upload, unreadable |
| 400 | `IMAGE_TOO_LARGE` | Exceeds max upload size |
| 415 | `UNSUPPORTED_IMAGE` | Unsupported content type |
| 422 | `IMAGE_QUALITY_LOW` | Quality gate rejection (returned inside 200 success=false) |
| 503 | `MODEL_NOT_LOADED` | Service starting up or model unavailable |
| 500 | `INFERENCE_FAILED` | Unexpected internal error |

Error response shape:

```json
{
  "detail": {
    "success": false,
    "error": {
      "code": "UNSUPPORTED_IMAGE",
      "message": "Unsupported content type 'text/plain'. Supported: image/bmp, image/jpeg, image/png, image/tiff, image/webp."
    }
  }
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `prediction.label` | string | `"anemic"` or `"non_anemic"` (dataset labels) |
| `prediction.model_probability` | float | Random Forest model probability for the anemic class (0–1) |
| `prediction.model_confidence` | float | Model probability for the predicted class (0–1) |
| `image_quality.status` | string | `"good"` or `"poor"` |
| `image_quality.score` | float | Engineering quality score (0–1), higher is better |
| `image_quality.checks` | object | Per-check pass/fail: blur, brightness, contrast, resolution |
| `image_quality.reasons` | array | Failed check names (empty when quality is good) |
| `inference.model` | string | Model identifier |
| `inference.version` | string | Model version |
| `inference.latency_ms` | float | Total inference time in milliseconds |

**Important:** `model_probability` is the Random Forest model probability for
the anemic class. It is NOT clinical probability, NOT a diagnosis, and NOT
a hemoglobin value.

---

## 5. Frontend Integration Example

```javascript
async function screenAnemia(imageFile) {
  const formData = new FormData();
  formData.append("image", imageFile);

  const response = await fetch(
    `${process.env.REACT_APP_API_URL || "http://localhost:8000"}/api/v1/anemia/screen`,
    {
      method: "POST",
      body: formData,
    }
  );

  const result = await response.json();

  if (result.success) {
    console.log("Prediction:", result.prediction.label);
    console.log("Confidence:", result.prediction.model_confidence);
  } else {
    console.log("Quality issue:", result.error.message);
  }

  return result;
}
```

---

## 6. Swayam Integration

The AI service returns an image-based anemia signal.  Swayam's multimodal
risk engine should consume:

```json
{
  "anemia_prediction": "anemic",
  "anemia_model_probability": 0.912,
  "anemia_model_confidence": 0.912
}
```

Swayam combines this with:
- MUAC / anthropometry
- Nutrition information
- Symptoms
- Previous visits
- Other context

to determine the final PRAHARI risk level and recommended action.

The AI service does NOT compute:
- final risk level
- severity classification
- WHO decision rules
- referral recommendations
- hemoglobin values

---

## 7. Arya Integration

The AI service runs independently at `http://localhost:8000`.

Arya can call it directly from the backend:

```python
import requests

def screen_image(image_path: str) -> dict:
    with open(image_path, "rb") as f:
        response = requests.post(
            "http://localhost:8000/api/v1/anemia/screen",
            files={"image": f},
        )
    return response.json()
```

The AI service does NOT implement PostgreSQL, beneficiary management,
screening persistence, or follow-ups — those are Arya's responsibility.

---

## 8. CORS

Configured via `CORS_ORIGINS` environment variable:

```
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

Default allows `localhost:3000` and `localhost:5173` (React/Vite dev servers).

---

## 9. Medical Disclaimer

This endpoint provides an **image-based anemia screening prediction** and
is not a clinical diagnostic tool.  The model was trained on 708
conjunctival images from the CP-AnemiC dataset (children aged 6–59 months
in Ghana).  Results should be interpreted by qualified healthcare
professionals within the PRAHARI screening workflow.
