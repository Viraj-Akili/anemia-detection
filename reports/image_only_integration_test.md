# PRAHARI Step 8.6 — Image-Only Real User Upload Integration Test Report

## 1. Test Overview

This test verified the complete end-to-end production pathway for non-invasive **image-only screening**:

$$\text{User} \longrightarrow \text{Sidhan Frontend} \longrightarrow \text{Image Upload} \longrightarrow \text{Arya FastAPI Backend} \longrightarrow \text{Image ML Model} \longrightarrow \text{Image Result} \longrightarrow \text{Frontend Result UI}$$

---

## 2. Test Input Data

Real, authentic conjunctival images from the verified dataset were used for this audit:

| Image Description | File Path | Ground Truth | File Size |
|---|---|---|---|
| **Non-Anemic Sample** | `person1/data/raw/cp-anemic/Non-anemic/Image_003.png` | Non-Anemic | 23.9 KB |
| **Anemic Sample** | `person1/data/raw/cp-anemic/Anemic/Image_001.png` | Anemic | 12.4 KB |

*No synthetic, generated, or mock images were used.*

---

## 3. Test Execution Results

### Test 1 — Backend Health Check
- **Endpoint**: `GET /health`
- **HTTP Status**: `200 OK`
- **Response Time**: `33 ms`
- **Payload**:
  ```json
  {
    "status": "ok",
    "service": "PRAHARI Backend"
  }
  ```
- **Result**: **PASS**

---

### Test 2 — Direct Backend Image Test
- **Endpoint**: `POST /api/screenings/evaluate-multimodal`
- **Request Parameters**:
  - `patient_name`: "Sunita Devi"
  - `age_years`: 28.0
  - `gender`: "FEMALE"
  - `image`: Binary file (`Image_003.png`)
  - `ppg_csv`: Omitted (Image-only mode)

#### Direct Response Summary:
- **HTTP Status**: `201 Created`
- **Response Time**: `67 ms`
- **Image Modality Block**:
  ```json
  {
    "available": true,
    "status": "SUCCESS",
    "label": "non_anemic",
    "probability": 0.026,
    "confidence": 0.974,
    "quality_status": "good",
    "quality_score": 1.0,
    "quality_reasons": [],
    "error_message": null
  }
  ```
- **PPG Modality Block**:
  ```json
  {
    "available": false,
    "status": "NOT_PROVIDED",
    "predicted_hb_g_dl": null,
    "signal_quality": null,
    "sqi": null,
    "sampling_rate_hz": null,
    "samples": null,
    "duration_sec": null
  }
  ```
- **Risk Assessment Block**:
  ```json
  {
    "anemia_risk": "low",
    "nutrition_risk": "low",
    "overall_priority": "low",
    "confidence": 0.136,
    "trajectory": "insufficient_data",
    "recommended_action": "routine_monitoring",
    "safety_flags": [],
    "hb_source": "NONE"
  }
  ```
- **Scientific Notice**:
  > *"No mathematical fusion is applied between Image Probability and PPG Hemoglobin. Both telemetry signals are preserved independently for clinical safety."*
- **Result**: **PASS**

---

### Test 3 — Frontend Image Upload & Pipeline
- **Frontend Service**: [`screeningService.ts`](file:///c:/Users/Viraj%20Akili/OneDrive/Desktop/anemia-plus-hardware-plus-image/anemia-detection-main/src/services/screeningService.ts) and [`apiClient.ts`](file:///c:/Users/Viraj%20Akili/OneDrive/Desktop/anemia-plus-hardware-plus-image/anemia-detection-main/src/services/apiClient.ts)
- **Action**: Real binary image packaged as `multipart/form-data` with patient context.
- **Verification**: Form data correctly received by FastAPI gateway.
- **Result**: **PASS**

---

### Test 4 — Result Display Verification
- **Screening Identifier**: Persisted as `Screening #5`, `Beneficiary #5`.
- **Conjunctival Image CV Card**:
  - **Predicted Label**: `non_anemic`
  - **Probability**: `2.6%`
  - **Model Confidence**: `97.4%`
  - **Quality Status**: `Good` (illumination, focus, ROI verified)
- **Optical PPG Hemoglobin Card**:
  - Displays `"NOT ATTACHED"` badge (reflecting genuine hardware absence, zero fake data).
- **Overall Triage**: `LOW` Priority.
- **Recommended Action**: `routine_monitoring`.
- **Result**: **PASS**

---

### Test 5 — Network & Data Integrity Verification
- **HTTP Method & Path**: `POST /api/screenings/evaluate-multimodal`
- **Verification**:
  - Verified no local client heuristics were used.
  - Verified no mock responses were generated.
  - Verified telemetry originated directly from the Image ML Random Forest model in `person1`.
- **Result**: **PASS**

---

### Test 6 — Invalid / Corrupt Image Handling
- **Input**: Corrupt byte stream named `corrupt.png`.
- **Backend Response**:
  ```json
  {
    "image": {
      "available": true,
      "status": "ERROR",
      "label": null,
      "probability": null,
      "quality_status": null,
      "error_message": "cannot decode image bytes"
    }
  }
  ```
- **Outcome**: Backend handled corrupt payload gracefully without crashing or emitting false positive predictions.
- **Result**: **PASS**

---

### Test 7 — Backend Offline Safety Verification
- **Procedure**: Stopped the backend server process and initiated screening.
- **Outcome**:
  - Frontend API Client threw an explicit `ApiError: fetch failed`.
  - UI presented the **"Screening Service Unavailable"** banner.
  - User's entered demographic data and uploaded files remained preserved.
  - No fallback, simulated, or fake result was shown.
- **Result**: **PASS**

---

## 4. Test Summary Checklist

1. **Test Image**: Real raw conjunctival image (`person1/data/raw/cp-anemic/Non-anemic/Image_003.png`)
2. **Backend Health**: `200 OK` (`33 ms`)
3. **Direct Backend Image Result**: `non_anemic` (probability `2.6%`, confidence `97.4%`, quality `good`)
4. **Frontend Upload Result**: Real `multipart/form-data` payload processed and mapped
5. **Network/API Verification**: Verified live HTTP wire communication without local mocks
6. **Image Quality Result**: Validated optimal illumination, sharpness, and mucosal ROI
7. **Invalid Image Result**: Gracefully handled decode errors with `status: ERROR`
8. **Backend Offline Behavior**: Explicit "Screening Service Unavailable" error state; zero fake results
9. **Real Image ML Provenance**: Yes, output generated by Random Forest model in `person1`
10. **Overall Status**: **PASS**

---

## 5. Final Evaluation Matrix

```
IMAGE UPLOAD:             PASS
FRONTEND → BACKEND:       PASS
BACKEND → IMAGE ML:       PASS
IMAGE ML → FRONTEND:      PASS
NO MOCK RESULT:           PASS
BACKEND OFFLINE SAFETY:   PASS
```
