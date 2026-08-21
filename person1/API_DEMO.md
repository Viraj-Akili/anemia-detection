# API Demo & Integration Guide — PRAHARI AI/CV Service

This document provides exact, tested `curl` commands, real JSON response payloads, and integration contracts for Frontend, Swayam (Multimodal Risk Engine), and Arya (Main Backend).

---

## 1. Quick Start / Running the Service

Start the FastAPI AI screening service:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- **Base URL:** `http://127.0.0.1:8000`
- **Swagger Docs:** `http://127.0.0.1:8000/docs`
- **OpenAPI Schema:** `http://127.0.0.1:8000/openapi.json`

---

## 2. Tested cURL Examples

### 2.1. Health Check (`GET /health`)

Verify service availability and model status.

```bash
curl -X GET http://127.0.0.1:8000/health
```

**Real Response (HTTP 200):**
```json
{
  "status": "ok",
  "model_loaded": true,
  "model": "random_forest_color_baseline",
  "version": "1.0"
}
```

When degraded (model not loaded):
```json
{
  "status": "degraded",
  "model_loaded": false,
  "model": "none",
  "version": "n/a"
}
```

---

### 2.2. Screening — Successful Image (`POST /api/v1/anemia/screen`)

Submit a valid conjunctival image for screening.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/anemia/screen \
  -F "image=@data/samples/example.png"
```

**Real Response (HTTP 200):**
```json
{
  "success": true,
  "prediction": {
    "label": "non_anemic",
    "model_probability": 0.29,
    "model_confidence": 0.71
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
    "latency_ms": 126.26
  },
  "api_latency_ms": 127.45
}
```

---

### 2.3. Screening — Poor Quality Image Rejection (`POST /api/v1/anemia/screen`)

Submit a blurry, dark, or low-quality image. The quality gate catches and rejects it gracefully before model prediction.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/anemia/screen \
  -F "image=@data/samples/example_poor.png"
```

**Real Response (HTTP 200, success=false):**
```json
{
  "success": false,
  "prediction": null,
  "image_quality": {
    "status": "poor",
    "score": 1.0,
    "checks": {
      "blur": "pass",
      "brightness": "fail",
      "contrast": "fail",
      "resolution": "pass"
    },
    "reasons": [
      "brightness",
      "contrast"
    ]
  },
  "inference": null,
  "error": {
    "code": "IMAGE_QUALITY_LOW",
    "message": "Image quality is insufficient. Please retake the image."
  },
  "api_latency_ms": 7.254
}
```

---

### 2.4. Screening — Invalid / Unsupported Format (`POST /api/v1/anemia/screen`)

Submit an unreadable or non-image file.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/anemia/screen \
  -F "image=@requirements.txt"
```

**Real Response (HTTP 415):**
```json
{
  "detail": {
    "success": false,
    "error": {
      "code": "UNSUPPORTED_IMAGE",
      "message": "Unsupported content type 'text/plain'.  Supported: image/bmp, image/jpeg, image/png, image/tiff, image/webp."
    }
  }
}
```

---

## 3. Frontend Integration Contract

The frontend interacts with the AI service using standard browser multipart `FormData`. The frontend does **not** need to understand internal machine learning models, features, or pipelines.

### JavaScript / TypeScript Example

```javascript
// API configuration
const API_BASE_URL = process.env.VITE_AI_API_URL || "http://127.0.0.1:8000";

/**
 * Screen a conjunctival photo for anemia risk signal.
 * @param {File|Blob} imageFile - Image file captured from camera or file picker.
 * @returns {Promise<Object>} Screening result.
 */
async function screenAnemiaImage(imageFile) {
  const formData = new FormData();
  formData.append("image", imageFile);

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/anemia/screen`, {
      method: "POST",
      body: formData,
    });

    const result = await response.json();

    if (!response.ok) {
      // Handle HTTP 4xx / 5xx errors
      const errorMsg = result.detail?.error?.message || "Screening service error";
      console.error("HTTP Error:", response.status, errorMsg);
      return { success: false, error: { message: errorMsg } };
    }

    if (result.success) {
      // Successful prediction
      console.log("Prediction:", result.prediction.label);
      console.log("Probability:", result.prediction.model_probability);
      console.log("Confidence:", result.prediction.model_confidence);
      return result;
    } else {
      // Quality gate rejection
      console.warn("Quality Rejection:", result.error.message, result.image_quality.reasons);
      return result;
    }
  } catch (err) {
    console.error("Network connection failure:", err);
    return {
      success: false,
      error: { code: "NETWORK_ERROR", message: "Failed to connect to AI screening service." },
    };
  }
}
```

### Key Frontend Contract Rules
- **Base URL:** `http://127.0.0.1:8000` (or injected env var)
- **Endpoint:** `POST /api/v1/anemia/screen`
- **Field Name:** `image` (multipart/form-data)
- **Supported Formats:** PNG, JPEG, WebP, BMP, TIFF
- **Maximum Upload Size:** 4 MB

---

## 4. Swayam Integration Contract (Multimodal Risk Engine)

The AI/CV service outputs an **image-based screening signal** only. It does not compute clinical diagnosis, hemoglobin level, WHO classification, or final risk scoring.

### AI Signal Output Shape
Swayam receives the structured prediction object:

```json
{
  "label": "anemic",
  "model_probability": 0.88,
  "model_confidence": 0.88
}
```

### Responsibility Matrix
| Domain | Component | Owner |
|---|---|---|
| Image Quality Gate | AI/CV Service | Viraj |
| Conjunctival Feature Extraction | AI/CV Service | Viraj |
| Random Forest Screening Signal | AI/CV Service | Viraj |
| Anthropometry (MUAC, Z-scores) | Multimodal Risk Engine | Swayam |
| Dietary & Nutrition Intake | Multimodal Risk Engine | Swayam |
| Symptoms & Clinical History | Multimodal Risk Engine | Swayam |
| Final Multimodal PRAHARI Score | Multimodal Risk Engine | Swayam |
| Triage / Referral Recommendation | Multimodal Risk Engine | Swayam |

---

## 5. Arya Integration Contract (Main Backend & Database)

Arya's backend communicates with the AI service via HTTP REST calls. The AI service remains an independently deployable microservice; ML model weights are never loaded into the main backend process.

### Python Integration Example (for Arya's Backend)

```python
import requests
from typing import Optional, Dict, Any

AI_SERVICE_URL = "http://127.0.0.1:8000"

def request_anemia_screening(image_bytes: bytes, filename: str = "capture.png") -> Dict[str, Any]:
    """Call the standalone AI microservice to obtain anemia screening signal."""
    files = {"image": (filename, image_bytes, "image/png")}
    response = requests.post(
        f"{AI_SERVICE_URL}/api/v1/anemia/screen",
        files=files,
        timeout=15.0,
    )
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 415:
        return {"success": False, "error": {"code": "UNSUPPORTED_FORMAT", "message": "Invalid image format."}}
    elif response.status_code == 503:
        return {"success": False, "error": {"code": "AI_SERVICE_UNAVAILABLE", "message": "AI service model loading."}}
    else:
        return {"success": False, "error": {"code": "API_ERROR", "message": f"HTTP {response.status_code}"}}
```

---

## 6. Response Schema Summary

### Success Response (`200 OK`)
| Field | Type | Description |
|---|---|---|
| `success` | `boolean` | `true` |
| `prediction.label` | `string` | `"anemic"` or `"non_anemic"` |
| `prediction.model_probability` | `float` | Random Forest probability for anemic class (0.0–1.0) |
| `prediction.model_confidence` | `float` | Probability for predicted class (0.0–1.0) |
| `image_quality.status` | `string` | `"good"` |
| `image_quality.score` | `float` | Engineering quality score |
| `inference.model` | `string` | `"random_forest_color_baseline"` |
| `inference.version` | `string` | `"1.0"` |
| `inference.latency_ms` | `float` | Core inference engine runtime (ms) |
| `api_latency_ms` | `float` | Full HTTP request handling runtime (ms) |

### Quality Rejection (`200 OK, success: false`)
| Field | Type | Description |
|---|---|---|
| `success` | `boolean` | `false` |
| `prediction` | `null` | No prediction generated |
| `image_quality.status` | `string` | `"poor"` |
| `image_quality.reasons` | `array[string]` | List of failing checks (e.g. `["brightness", "contrast"]`) |
| `error.code` | `string` | `"IMAGE_QUALITY_LOW"` |
| `error.message` | `string` | Human-readable instruction |
