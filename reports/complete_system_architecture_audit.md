# PRAHARI — Complete System Architecture Audit (Step 6C)

**Status:** Completed Architecture Audit & Component Inspection  
**Date:** 2026-08-20  
**Target:** Entire Multi-Component PRAHARI Workspace  
**Inspection Type:** Read-Only Interface & Dataflow Audit  

---

## 1. Executive Summary

This audit establishes the full structural, computational, and dataflow baseline for the **PRAHARI System** across all 6 core subsystems in the workspace:

1. **Image/CV Anemia Subsystem** (`person1/`): MobileNetV2 CNN & classical Random Forest tissue pallor classifier.
2. **PPG Hardware ML Subsystem** (`ppg-anemia/`): MAX30102 sensor pipeline (25 Hz, 250 red/IR samples, 10s recording) + 12-feature extraction + Lasso regression for continuous Hemoglobin (g/dL) prediction.
3. **Multimodal ML Integration Layer** (`integration/`): Modality-preserving Python coordinator that invokes both models independently, preserves discrete probability and continuous Hb without unvalidated fusion (`fusion.status = "NOT_VALIDATED"`).
4. **Risk / Clinical Logic Engine** (`swayam risk/`): XGBoost Late-Fusion (20-feature calibrated vector) + WHO 2024 Hemoglobin & Anthropometry Standards + 5 Escalation-Only Red-Flag Safety Rules + SHAP Top-3 Explainability + Longitudinal Visit Trajectory Tracker.
5. **Core Database & Management Backend** (`arya-backend/`): Dockerized FastAPI + PostgreSQL 18 relational persistence service managing Users, Beneficiaries, Screenings, Measurements, Results, and Follow-ups.
6. **Point-of-Care Frontline UI** (`anemia-detection-main/`): React 19 + Vite + TypeScript single-page application with Apple-inspired clinical UI, WHO threshold matching, and offline-first queue simulation.

### Critical System Discovery
- **Scientific Fusion Discipline:** No mathematically fused or averaged clinical score exists across Image + PPG. The system correctly isolates Image Anemia Probability ($[0, 1]$) from Optical PPG Hemoglobin ($[7.0, 18.0]\text{ g/dL}$).
- **The Central Integration Gap:** Each subsystem is individually mature and feature-complete, but they currently operate in **architectural isolation**:
  - `anemia-detection-main` runs mock in-browser inference without calling a backend.
  - `arya-backend` provides relational CRUD endpoints but does not invoke ML models or the risk engine.
  - `swayam risk` has an end-to-end FastAPI risk engine (`POST /api/screening/analyze`), but its `SafetyInput` leaves `hb_gdl=None` because PPG Hb is not yet passed into its request schema.
  - `integration` cleanly combines Image + PPG into a unified Python object, ready to be wired into the backend API and risk engine.

---

## 2. Comprehensive Component Map

```
anemia-plus-hardware-plus-image/
│
├── person1/                      [Subsystem 1: Image / CV ML]
│   ├── app/ai/
│   │   ├── inference.py          # Production inference engine (AnemiaInferenceEngine)
│   │   ├── cnn_model.py          # MobileNetV2 deep learning model
│   │   ├── quality_gate.py       # Blur, lighting & tissue coverage checks
│   │   ├── features.py           # Color extraction (RGB/HSV/Lab/Chroma)
│   │   └── preprocessing.py      # Resize, normalize & alpha composite
│   └── app/main.py               # Standalone FastAPI service (port 8000)
│
├── ppg-anemia/                   [Subsystem 2: Optical PPG Hardware ML]
│   ├── src/
│   │   ├── inference.py          # predict_esp32_recording / predict_from_raw_arrays
│   │   ├── features.py           # 12-feature extractor (AC/DC, PI, PSD, SQI)
│   │   ├── preprocessing.py      # 0.5-5Hz Butterworth bandpass filter & baseline removal
│   │   └── models.py             # Lasso/Ridge regression Hb estimators
│   ├── hardware/                 # ESP32 MAX30102 Arduino C++ firmware (25 Hz)
│   └── data/clean/               # Sample 10-second CSVs (250 red/IR samples)
│
├── integration/                  [Subsystem 3: Multimodal ML Coordinator]
│   ├── schemas.py                # Pydantic schemas (MultimodalScreeningRequest/Result)
│   ├── multimodal.py             # MultimodalScreeningEngine (modality-preserving)
│   └── README.md                 # Integration & schema documentation
│
├── swayam risk/                  [Subsystem 4: Risk / Clinical Logic Engine]
│   ├── backend/
│   │   ├── src/
│   │   │   ├── main.py           # FastAPI entrypoint (app = FastAPI)
│   │   │   ├── api/routes/       # POST /api/screening/analyze & /api/beneficiaries
│   │   │   ├── fusion/           # 20-feature builder, XGBoost late-fusion, SHAP explainers
│   │   │   ├── safety/           # 5 deterministic WHO red flags (escalation-only)
│   │   │   ├── anthropometry/    # WHO 2006 child growth z-scores (WHZ, HAZ, WAZ, MUAC)
│   │   │   ├── context/          # WHO 2024 Hb thresholds, dietary risk, IFA multipliers
│   │   │   ├── trajectory/       # Multi-visit trajectory slope & early warning
│   │   │   └── models/           # Pydantic schemas & SQLAlchemy entities
│   │   └── assets/models/        # Trained XGBoost models (.json) & thresholds (.json)
│   └── src/                      # Prototype React frontend
│
├── arya-backend/                 [Subsystem 5: Database & Management API]
│   └── backend/
│       ├── Dockerfile            # Python 3.12 container
│       ├── docker-compose.yml    # FastAPI + PostgreSQL 18 orchestration
│       └── app/
│           ├── main.py           # FastAPI entrypoint with CORS & healthchecks
│           ├── database.py       # SQLAlchemy engine & session factory
│           ├── models/models.py  # 6 tables: users, beneficiaries, screenings,
│           │                     # measurements, results, followups
│           ├── routers/          # CRUD endpoints for all 6 database entities
│           └── repositories/     # Database transaction queries & longitudinal joins
│
├── anemia-detection-main/        [Subsystem 6: Frontline User Interface]
│   ├── index.html                # HTML entrypoint
│   ├── src/
│   │   ├── main.tsx              # React 19 mount point
│   │   ├── App.tsx               # Primary SPA container & 4-step screening wizard
│   │   ├── components/           # OpticalCaptureZone, DoubtAssistant, Chatbot, AWW tools
│   │   ├── services/             # Client-side mock services (screeningService, syncService)
│   │   └── types/index.ts        # Frontend TypeScript interfaces
│
├── reports/                      # System inspection & interface audit reports
└── tests/                        # Automated unit & integration test suites
```

---

## 3. Subsystem Deep-Dive Audits

### Part 1 — Image/CV ML (`person1/`)
- **Architecture:** MobileNetV2 deep learning classifier (primary) + classical Random Forest on color-space statistics (fallback).
- **Inputs:** Conjunctival image (PIL Image, OpenCV `numpy.ndarray`, or file path) with optional palpebral conjunctiva tissue mask. Resized to $224 \times 224 \times 3$.
- **Outputs:** Class label (`"anemic"` vs. `"non_anemic"`), continuous probability ($0.0-1.0$), confidence score ($0.5-1.0$), quality gate status (`"good"` vs. `"poor"`), quality score ($0.0-1.0$), and quality reasons (`list[str]`).
- **Image Quality Checks:** Laplacian variance for blur ($>100.0$), brightness/underexposure/overexposure boundaries ($40.0-220.0$), tissue mask coverage ($>5.0\%$).
- **Callable Entry Point:** `AnemiaInferenceEngine.predict(image_input)` in `person1/app/ai/inference.py`.

### Part 2 — Optical PPG Hardware ML (`ppg-anemia/`)
- **Hardware Contract:** MAX30102 optical sensor $\to$ ESP32 micro-controller $\to$ 25 Hz sampling rate $\to$ 10-second recording $\to$ exactly 250 RED + 250 IR photodiode samples formatted as `timestamp_ms,red,ir`.
- **Signal Processing:** 4th-order Butterworth bandpass filter ($0.5-5.0\text{ Hz}$), baseline trend removal, min-max normalization, AC/DC pulsatile ratio extraction.
- **Features Extracted:** 12 engineered features (optical modulation ratio $R$, Perfusion Index, pulse peak amplitude, crest factor, spectral peak frequency, spectral entropy, Signal Quality Index SQI, patient age, gender).
- **Model Type:** Lasso / Ridge regression estimator trained on optical pulse ratios.
- **Outputs:** Predicted Hemoglobin (`predicted_hb_g_dl` in $\text{g/dL}$, e.g. $14.60$), Signal Quality Index (`sqi` in $[0, 1]$), signal quality assessment (`"good"` vs. `"poor"`).
- **Callable Entry Point:** `predict_esp32_recording(csv_path_or_df, age, gender)` or `predict_from_raw_arrays(red, ir, age, gender)` in `ppg-anemia/src/inference.py`.

### Part 3 — Multimodal Integration Layer (`integration/`)
- **Architecture:** Modality-preserving Python coordinator that invokes `AnemiaInferenceEngine` and `predict_esp32_recording` in parallel or sequentially.
- **Scientific Boundary:** Preserves independent modality predictions. `fusion.status` is explicitly set to `"NOT_VALIDATED"` and `fusion.fused_prediction` is `None`.
- **Request / Response:** Standardized Pydantic schemas (`MultimodalScreeningRequest` $\to$ `MultimodalScreeningResult`).
- **Callable Entry Point:** `run_multimodal_screening(request)` or `MultimodalScreeningEngine().screen(...)` in `integration/multimodal.py`.

### Part 4 — Swayam Risk / Clinical Logic Engine (`swayam risk/`)
- **Architecture:** Calibrated XGBoost Late-Fusion model over a fixed 20-feature vector + WHO 2024 Hemoglobin thresholds + WHO 2006 Child Growth z-scores + 5 Deterministic Safety Red-Flag Rules + SHAP TreeExplainer + Multi-visit Trajectory slope analysis.
- **Feature Vector (20 Features in exact order):**
  1. `anemia_risk_score` (low=0.0, moderate=0.5, high=1.0)
  2. `anemia_confidence` ($0.0-1.0$)
  3. `whz` (Weight-for-Height z-score)
  4. `haz` (Height-for-Age z-score)
  5. `waz` (Weight-for-Age z-score)
  6. `muac_z` (MUAC z-score)
  7. `whz_cat`, 8. `haz_cat`, 9. `waz_cat`, 10. `muac_cat` (encoded 0-2)
  11. `diet_risk` ($0.0-1.0$, frequency $\times$ diversity)
  12. `ifa_protection` (0.85 adherent, 1.0 non-adherent)
  13. `symptom_flags` (count of red-flag symptoms 0-4)
  14. `age_months`
  15. `sex_enc` (0 female, 1 male)
  16. `pregnancy_enc` (0 no, 1 yes)
  17. `trimester_enc` (0 none, 1-3)
  18. `prev_anemia_risk` (from visit history)
  19. `prev_nutrition_risk` (from visit history)
  20. `visits_count` (integer)
- **5 Deterministic WHO Safety Rules (Escalation-Only):**
  - **Red Flag 1 (`SEVERE_ANEMIA_THRESHOLD`):** Observed Hb $\le$ WHO severe cutoff for cohort (e.g. $\le 7.0\text{ g/dL}$ for children/pregnancy, $\le 8.0\text{ g/dL}$ for adults) $\to$ Escalates Anemia Risk to `HIGH`, action `IMMEDIATE_REFERRAL`.
  - **Red Flag 2 (`SEVERE_MALNUTRITION`):** Severe MUAC ($<115\text{ mm}$ child / $<185\text{ mm}$ adult) OR WHZ $< -3.0$ (Severe Acute Malnutrition) $\to$ Escalates Nutrition Risk to `HIGH`, action `IMMEDIATE_REFERRAL`.
  - **Red Flag 3 (`BILATERAL_OEDEMA`):** Bilateral pitting oedema present $\to$ Escalates Nutrition Risk to `HIGH`, action `IMMEDIATE_REFERRAL`.
  - **Red Flag 4 (`PREGNANCY_RED_FLAGS`):** Pregnancy + severe pallor + breathlessness $\to$ Escalates Anemia Risk to `HIGH`, action `IMMEDIATE_REFERRAL`.
  - **Red Flag 5 (`REPEATED_POOR_QUALITY`):** $\ge 2$ consecutive poor quality attempts $\to$ Action `MANUAL_PROTOCOL_ESCALATION`.
- **Callable Entry Point:** HTTP `POST /api/screening/analyze` on `swayam risk/backend/src/main.py` or programmatic Python `from api.routes.screening import analyze`.

### Part 5 — Arya Backend (`arya-backend/`)
- **Architecture:** Production-ready Dockerized FastAPI service with PostgreSQL 18 relational persistence and Alembic migrations.
- **Relational Schema (6 Tables):**
  - `users`: Frontline workers, supervisors, administrators.
  - `beneficiaries`: Patient demographics, DOB, sex, category (`CHILD`, `PREGNANT_WOMAN`), pregnancy trimester.
  - `screenings`: Individual screening encounters (`IN_PROGRESS`, `COMPLETED`, `ABANDONED`), device ID, timestamps.
  - `measurements`: Weight (kg), Height (cm), MUAC (mm).
  - `results`: Final calculated risks (`anemia_risk`, `nutrition_risk`, `overall_priority`), confidence, trajectory, recommended action, contributors JSONB, model metadata.
  - `followups`: Assigned tasks, due dates, follow-up status (`PENDING`, `COMPLETED`, `OVERDUE`).
- **Callable Entry Points:** HTTP REST API on `http://localhost:8000/api/...`.

### Part 6 — Sidhan Frontend (`anemia-detection-main/`)
- **Architecture:** React 19 + TypeScript single-page application with Apple-inspired UI styling.
- **Workflow:** 4-step wizard: Demographic Setup $\to$ Optical Conjunctiva Capture $\to$ Symptoms & Doubt Resolution $\to$ Point-of-Care Triage Result.
- **Current State:** Fully in-browser mock simulation (0 active HTTP network calls).

---

## 4. Current Interface Matrix

| Component | Input Format | Output Format | Callable / API | Current Consumer | Current Producer | Implementation Status | Integration Gap |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **Image ML** (`person1`) | RGB Image (tensor / numpy / path) | `InferenceResult` (`label`, `probability`, `confidence`, `quality_status`, `quality_reasons`) | `AnemiaInferenceEngine.predict(image)` | `integration/multimodal.py` | Local camera / file upload | ✅ **COMPLETE** | Standalone; needs backend endpoint wiring. |
| **PPG ML** (`ppg-anemia`) | `timestamp_ms,red,ir` CSV / array (25 Hz, 250 samples) + Age + Sex | `PPGResult` (`predicted_hb_g_dl`, `sqi`, `signal_quality`) | `predict_esp32_recording(data, age, gender)` | `integration/multimodal.py` | ESP32 MAX30102 Hardware | ✅ **COMPLETE** | Standalone; needs frontend hardware ingestion and backend wiring. |
| **Multimodal Integration** (`integration`) | `MultimodalScreeningRequest` (Image + PPG + Patient info) | `MultimodalScreeningResult` (Independent Image + PPG outputs) | `run_multimodal_screening(request)` | Unit tests (`tests/`) | Multi-sensor inputs | ✅ **COMPLETE** | Needs to be exposed via backend REST router. |
| **Swayam Risk Engine** (`swayam risk`) | `ScreeningRequest` (Anemia risk, weight, height, muac, diet, symptoms, beneficiary_id) | `ScreeningResponse` (anemia_risk, nutrition_risk, overall_priority, contributors, recommended_action, safety_flags) | `POST /api/screening/analyze` | Frontend prototype in `swayam risk/src` | Frontline questionnaire & CV input | ✅ **COMPLETE** | Currently receives CV risk from JSON; `SafetyInput.hb_gdl` is present in code but hardcoded to `None` in route. |
| **Arya Backend** (`arya-backend`) | REST JSON payloads (`ScreeningCreate`, `MeasurementCreate`, `ResultCreate`) | Relational JSON entities (`BeneficiaryRead`, `ScreeningRead`, `ResultRead`, `History`) | `POST/GET /api/beneficiaries`, `POST /api/screenings`, `GET /history` | External clients / Swagger | Database tables in PostgreSQL 18 | ✅ **COMPLETE** (CRUD only) | No ML inference coordinator or risk engine invocation exists inside the backend router. |
| **Sidhan Frontend** (`anemia-detection-main`) | User UI inputs (Camera capture, demographic form, symptoms) | Rendered React UI (Risk cards, explainability signals, advice) | In-browser React state & `screeningService.ts` | Frontline health worker | User interactions | ⚠️ **ISOLATED** | Has no HTTP client (`fetch`/`axios`); operates on mock timeouts; has no PPG UI cards or Hb telemetry widgets. |

---

## 5. Actual Data Flow Diagram

### Current Codebase Reality:
```
[MAX30102 + ESP32]
       │ (25 Hz CSV)
       ▼
[ppg-anemia ML] ───────┐
                       │
[Conjunctival Camera]  │
       │ (RGB Image)   │
       ▼               ▼
[person1 Image ML] ──> [integration/multimodal.py] ──> [tests/test_multimodal_integration.py] (Isolated)
                                                                 │
                                                            UNKNOWN LINK
                                                                 │
                                                                 ▼
[Frontline Worker Input] ──> [swayam risk/backend] ──> [JSON Response] (Standalone FastAPI)
                                                                 │
                                                            UNKNOWN LINK
                                                                 │
                                                                 ▼
[Frontline Worker Input] ──> [arya-backend/backend] ──> [PostgreSQL 18 DB] (Standalone CRUD)
                                                                 │
                                                            UNKNOWN LINK
                                                                 │
                                                                 ▼
[Browser Camera + Form] ──> [anemia-detection-main] ──> [In-Browser Mock UI] (0 HTTP Calls)
```

### Unified Target Data Flow Architecture:
```
                                 PATIENT ENCOUNTER
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
         [Conjunctival Image]                         [MAX30102 on ESP32]
                    │                                         │
                    │ (Image Upload / DataURL)                │ (25 Hz CSV / Stream)
                    └────────────────────┬────────────────────┘
                                         ▼
                           [anemia-detection-main]
                         (React 19 Point-of-Care UI)
                                         │
                                         │ HTTP POST Multipart / JSON
                                         ▼
                              [PRAHARI BACKEND API]
                           (arya-backend + integration)
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
         [person1 Image Engine]                      [ppg-anemia ML Engine]
         • MobileNetV2 / RF                          • Bandpass Filter (0.5-5Hz)
         • Quality Gate (Blur/Light)                 • 12-Feature Extraction
         • Anemia Probability [0,1]                  • Predicted Hb (g/dL) + SQI
                    │                                         │
                    └────────────────────┬────────────────────┘
                                         │
                                         ▼
                            [Multimodal ML Result]
                         (Modality-Preserving Schema)
                                         │
                                         ▼
                            [Swayam Risk / Safety Engine]
                         • WHO 2024 Demographic Hb Threshold
                         • WHO 2006 Anthropometry (WHZ, HAZ, MUAC)
                         • Dietary Risk (Frequency × Diversity)
                         • 5 Deterministic Safety Red Flags (Hb <= cutoff, SAM, etc.)
                         • 20-Feature Calibrated XGBoost Late-Fusion
                         • SHAP Top-3 Clinical Explainability
                         • Longitudinal Multi-Visit Trajectory Slope
                                         │
                                         ▼
                        [PostgreSQL 18 Relational DB]
                         • Record Screening encounter
                         • Save Measurements (Weight, Height, MUAC)
                         • Save Results (Risks, Hb, Prob, Contributors)
                         • Generate Follow-Up Task if Critical/Declining
                                         │
                                         │ Structured JSON Response
                                         ▼
                           [anemia-detection-main UI]
                         • Anemia Risk & Hemoglobin (g/dL) Card
                         • Optical Conjunctiva & PPG SQI Badges
                         • WHO Safety Escalation Alerts
                         • Top-3 Contributing Explainability Signals
                         • Frontline Action & Longitudinal Trends
```

---

## 6. Categorized Integration Gap Analysis

### Category A: Already Implemented & Verified
- `person1/`: High-performance MobileNetV2 + Random Forest image inference with Laplacian blur and lighting quality gating.
- `ppg-anemia/`: 25 Hz ESP32 10-second signal processor + 12-feature extractor + Lasso Hb estimator.
- `integration/`: Clean Pydantic schemas and `MultimodalScreeningEngine` coordinator.
- `swayam risk/`: Complete 20-feature XGBoost late-fusion model, WHO 2024 Hb thresholds, 5 red-flag safety rules, and SHAP explainability.
- `arya-backend/`: Full PostgreSQL 18 schema, SQLAlchemy ORM entities, and CRUD routers.

### Category B: Interface Exists but Needs Wiring
- **Wiring PPG Hb into Swayam Safety Layer:** `swayam risk/backend/src/safety/rules.py` already implements **Red Flag 1 (`SEVERE_ANEMIA_THRESHOLD`)** expecting `SafetyInput(hb_gdl=...)`. However, `src/api/routes/screening.py` hardcodes `hb_gdl=None`. Wiring `ppg.predicted_hb_g_dl` directly enables automated WHO severe anemia escalation.
- **Connecting Backend to Multimodal ML:** `arya-backend` routers currently accept raw numbers without executing `integration.multimodal.run_multimodal_screening`. Adding an ML execution router binds the entire ML layer directly into the database lifecycle.

### Category C: Interface Missing (Requires Implementation)
- **Frontend HTTP API Client:** `anemia-detection-main` lacks an `apiService.ts` to dispatch `POST /api/screenings/analyze` to the backend.
- **Frontend PPG Ingestion Component:** `anemia-detection-main` currently has only `OpticalCaptureZone.tsx`. A companion `PPGCaptureZone.tsx` (for CSV upload or WebSerial live sensor ingest) is needed.
- **Frontend Hemoglobin UI Display Card:** The triage result screen in `App.tsx` has cards for Anemia Risk, Symptom Load, and Triage Priority, but lacks a dedicated numerical **Hemoglobin ($g/dL$)** gauge and **PPG SQI** badge.

### Category D: Teammate Architecture Alignment
- **Single vs. Split Backend Services:** Determining whether `arya-backend` (PostgreSQL CRUD) and `swayam risk` (XGBoost/WHO engine) run as a single unified FastAPI application or as microservices communicating over HTTP.

### Category E: Scientific Validation Constraints
- **Preserve Independent Modalities:** Keep Image probability ($0.0-1.0$) and PPG Hb ($g/dL$) as distinct biometric telemetry outputs. Do not attempt mathematical averaging or unvalidated unified scoring.

---

## 7. Recommended Implementation Sequence

Based on the actual codebase topology and dependencies, the safest zero-regression implementation sequence is:

1. **Step 1: Stabilize Unified Backend ML Router**  
   Mount `integration/` inside the backend API to expose a single multipart endpoint:  
   `POST /api/screening/evaluate-multimodal` (accepts patient demographics, conjunctiva image, and PPG CSV).
2. **Step 2: Wire PPG Hb into the Risk Engine**  
   Update `swayam risk` request schema to accept `predicted_hb_gdl` and pass it to `SafetyInput(hb_gdl=...)` to activate Red Flag 1.
3. **Step 3: Unify Backend Database & Risk Pipelines**  
   When a screening is submitted, execute ML inference $\to$ pass outputs to Risk Engine $\to$ persist encounter, measurements, and results into PostgreSQL 18.
4. **Step 4: Upgrade Frontend with Real HTTP Client & PPG Support**  
   - Replace in-browser mock services in `anemia-detection-main` with real `fetch()` calls to the backend API.
   - Add PPG capture UI and Hemoglobin (g/dL) result card.
5. **Step 5: End-to-End System Verification**  
   Run end-to-end integration tests validating a full patient flow from raw image + 10s PPG CSV $\to$ ML inference $\to$ WHO risk evaluation $\to$ DB persistence $\to$ UI presentation.
