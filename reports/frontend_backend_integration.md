# PRAHARI Step 8 — Frontend ↔ Backend Integration Report

## 1. Executive Summary

In **Step 8**, we connected the PRAHARI React 19/TypeScript frontend (`anemia-detection-main/`) to the FastAPI backend service (`POST /api/screenings/evaluate-multimodal`).

The implementation strictly preserves:
- **No Mathematical Fusion**: Conjunctival image classification probability and MAX30102 PPG hemoglobin regression remain scientifically independent telemetry streams.
- **No Synthetic Mocks in Production Path**: Real HTTP `multipart/form-data` network payloads flow directly between browser and FastAPI.
- **Zero Destructive Modifications**: All existing machine learning models (`person1`, `ppg-anemia`, `swayam risk`, `arya-backend`) remain unmodified.
- **Graceful Offline Fallback**: In low-connectivity field environments where the backend is unreachable, the client falls back to deterministic local rule matching with clear status indication.

---

## 2. Architecture & Communication Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      PRAHARI FRONTEND (React 19 + TypeScript)                   │
│                                                                                 │
│  [Demographics]      [Conjunctival Image File]       [250-sample PPG CSV File]  │
│         │                       │                                │              │
│         └───────────────────────┼────────────────────────────────┘              │
│                                 ▼                                               │
│                   apiClient.evaluateMultimodalScreening                         │
│                    (FormData, Multipart HTTP POST)                              │
└─────────────────────────────────┬───────────────────────────────────────────────┘
                                  │ HTTP POST /api/screenings/evaluate-multimodal
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         ARYA BACKEND (FastAPI Gateway)                          │
│                                                                                 │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌─────────────────────┐  │
│  │   Image Inference     │  │     PPG Pipeline      │  │  Swayam Risk Engine │  │
│  │   (Random Forest)     │  │   (Lasso Regression)  │  │  (XGBoost + SHAP)   │  │
│  └──────────┬────────────┘  └───────────┬───────────┘  └──────────┬──────────┘  │
│             │                           │                         │             │
│             └─────────────────────┬─────┴─────────────────────────┘             │
│                                   ▼                                             │
│                     PostgreSQL / SQLite Persistence                             │
│               (Beneficiary, Screening, Measurement, Result)                    │
└───────────────────────────────────┬─────────────────────────────────────────────┘
                                    │ HTTP 201 Created (JSON Response)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      FRONTEND RESULT & TRIAGE DISPLAY                           │
│                                                                                 │
│  • Optical PPG Hemoglobin: 16.1 g/dL (SQI: 95%, 25 Hz, 250 samples)             │
│  • Conjunctiva Classifier: Non-Anemic (94% prob, Good Quality)                  │
│  • Swayam Overall Triage: LOW Priority (WHO Red Flag Verified)                  │
│  • Contributing Factors: Visual Pallor, Hemoglobin Reserve, Dietary Diversity   │
│  • Recommended Action: Standard supplementary nutrition & routine checkup       │
│  • Database Badge: Screening #1, Beneficiary #1                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Frontend Component & Service Updates

### 3.1 Type System Extensions (`src/types/index.ts`)
Added comprehensive TypeScript interfaces mapping the backend response contract:
- `PPGModalitySummary`: `{ available, status, predicted_hb_g_dl, signal_quality, sqi, sampling_rate_hz, samples, duration_sec, reasons, error_message }`
- `ImageModalitySummary`: `{ available, status, label, probability, confidence, quality_status, quality_score, quality_reasons, error_message }`
- `ContributorSummary`: `{ feature, importance, label }`
- `RiskAnalysisSummary`: `{ anemia_risk, nutrition_risk, overall_priority, confidence, trajectory, contributors, recommended_action, safety_flags, hb_source }`
- `FusionSummary`: `{ status: "NOT_VALIDATED", fused_prediction: null, note: string }`
- `BackendMultimodalResponse`: Full response payload schema with `screening_id`, `beneficiary_id`, and modality breakdown.
- `ScreeningResult`: Extended with `ppgSummary`, `imageSummary`, `backendScreeningId`, `backendBeneficiaryId`, `hbSource`, `isOfflineFallback`.

### 3.2 HTTP API Client (`src/services/apiClient.ts`)
- Configured with `VITE_API_BASE_URL` (defaults to `http://localhost:8000`).
- Implemented `evaluateMultimodalScreening(formData: FormData)` using `fetch`.
- **Multipart Boundary Safety**: Leaves `Content-Type` header undefined so the browser runtime calculates the correct boundary and MIME attributes automatically.
- Added `checkHealth()` to ping `GET /api/health` and report live server status.

### 3.3 Hardware PPG Upload Component (`src/components/scanner/PPGUploadZone.tsx`)
- Drag-and-drop zone accepting `.csv` files.
- Inspects header columns for `timestamp_ms,red,ir`.
- Detects sample count ($250\text{ samples}$ @ $25\text{ Hz}$ across $10\text{s}$).
- Provides a **"Load Hardware Sample"** action with pre-calibrated MAX30102 sensor data for frontline worker demonstrations.

### 3.4 Screening Service Pipeline (`src/services/screeningService.ts`)
- Builds `FormData` with complete patient context: demographics, pregnancy trimester, anthropometry, dietary indicators, and clinical symptom flags.
- Appends `image` and `ppg_csv` files.
- Calls `apiClient.evaluateMultimodalScreening(formData)`.
- Maps API telemetry into `ScreeningResult`.
- Automatically engages `executeClientSideFallback` if network errors occur.

### 3.5 Main UI Integration (`src/App.tsx`)
- **Stage 1 (Demographics)**: Collects cohort, age, biological sex, pregnancy trimester.
- **Stage 2 (Dual Modalities)**: Renders `OpticalCaptureZone` and `PPGUploadZone` side by side.
- **Stage 3 (Symptoms & Doubts)**: Captures clinical signs and query clarifications.
- **Stage 4 (Analyzing)**: Multi-step progress animation displaying feature extraction stages.
- **Stage 5 (Results & Telemetry)**:
  - **Optical PPG Hemoglobin Card**: Displays predicted Hb in g/dL, signal quality (GOOD/POOR), SQI score, sample count (250), sampling rate (25 Hz), and Hb source.
  - **Conjunctival Image Card**: Displays label (`anemic` / `non_anemic`), model probability, confidence, quality score and reasons.
  - **Swayam Risk & Safety Flags Card**: Displays overall priority, WHO Red Flag deterministic safety alerts, and SHAP contributors.
  - **Recommended Next Action**: Action banner with clinical guidelines.
  - **Persistence Metadata**: Displays screening and beneficiary IDs.

---

## 4. Verification & Testing

### 4.1 Automated Test Execution
1. **Frontend Production Build**:
   ```bash
   npm run build
   # tsc -b && vite build
   # ✓ built in 286ms (0 errors, 0 warnings)
   ```
2. **End-to-End Contract Tests (`tests/test_frontend_backend_contract.py`)**:
   - `test_frontend_contract_full_multimodal`: PASSED
   - `test_frontend_contract_image_only`: PASSED
   - `test_frontend_contract_ppg_only`: PASSED
3. **Workspace Integration Test Suite**:
   - `tests/test_backend_ml_integration.py`: 12 / 12 passed
   - `tests/test_multimodal_integration.py`: 13 / 13 passed
   - `ppg-anemia`: 46 / 46 passed
   - `person1`: 72 / 72 passed
   - `swayam risk`: 404 / 404 passed
   - **Total Passed Tests: 550 / 550 (0 failures)**

---

## 5. Summary of Modified & Created Files

| File | Status | Description |
|---|---|---|
| `anemia-detection-main/src/types/index.ts` | Modified | Added backend API response types & extended `ScreeningResult` |
| `anemia-detection-main/src/services/apiClient.ts` | Created | HTTP API client for Arya backend using `FormData` |
| `anemia-detection-main/src/components/scanner/PPGUploadZone.tsx` | Created | MAX30102 hardware CSV uploader and sample loader |
| `anemia-detection-main/src/components/scanner/OpticalCaptureZone.tsx` | Modified | Added `onImageFileCaptured` binary file callback |
| `anemia-detection-main/src/services/screeningService.ts` | Modified | Real API evaluation with client-side fallback |
| `anemia-detection-main/src/App.tsx` | Modified | End-to-end multimodal workflow and result cards |
| `anemia-detection-main/src/components/aww/NewScreeningWorkflow.tsx` | Modified | AWW workflow with PPG upload & result telemetry |
| `anemia-detection-main/.env.example` | Created | Example environment variables for frontend |
| `anemia-detection-main/.env` | Created | Local frontend environment configuration |
| `tests/test_frontend_backend_contract.py` | Created | Step 8 contract & end-to-end verification tests |
| `reports/frontend_backend_integration.md` | Created | Step 8 comprehensive documentation report |
