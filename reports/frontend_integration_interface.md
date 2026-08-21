# PRAHARI — Frontend Integration Interface Audit (Step 6A)

**Status:** Completed Inspection & Architecture Audit  
**Date:** 2026-08-20  
**Inspection Target:** `anemia-detection-main/` (PRAHARI Frontend Web Application)  
**Reference ML Target:** `integration/` & `person1/` & `ppg-anemia/`  

---

## 1. Executive Summary

This inspection audits the existing frontend web application (`anemia-detection-main/`) to determine its framework, UI routing, data models, service boundaries, and communication architecture.

### Key Takeaway:
- The frontend is a modern **React 19 + TypeScript + Vite** Single-Page Application (SPA).
- **NO EXISTING API CONTRACT FOUND:** The frontend currently contains **zero network calls (`fetch`, `axios`, XHR, or WebSockets)**. It operates entirely as an **in-browser / simulated offline system** using modular TypeScript services (`screeningService.ts`, `anemiaModelService.ts`, `syncService.ts`).
- The frontend has rich UI support for **Conjunctival Image Pallor Signals**, **Symptom Clarification**, **WHO Anthropometry Rules**, and **Longitudinal Trajectories**, but currently has **ZERO fields, UI cards, or hooks for Optical PPG / MAX30102 / Hemoglobin (g/dL) telemetry**.

---

## 2. Frontend Framework & Project Architecture

- **Core Framework:** **React 19.2.8** (`react`, `react-dom`)
- **Language:** **TypeScript 6.0.2** (`strict` typing, Pydantic/DTO equivalents in `src/types/index.ts`)
- **Build Tool:** **Vite 8.2.0** with `@vitejs/plugin-react`
- **Styling System:** **Tailwind CSS v4.3.3** (`@tailwindcss/vite`, `tailwind-merge`, `clsx`) using Apple-inspired clean healthcare design (`#00776b` Deep Emerald Teal, `#fbfbfd` light background, `#1d1d1f` dark text)
- **Icons & Visuals:** `lucide-react` (v1.31.0), `canvas-confetti` (v1.9.4), `recharts` (v3.10.1)
- **Local Dev Server:** Runs on port 3000 (`http://localhost:3000/`)

### Application Directory Structure
```
anemia-detection-main/
├── index.html                    # HTML entrypoint (<div id="root">)
├── package.json                  # Dependencies and scripts
├── vite.config.ts                # Vite config (port 3000)
└── src/
    ├── main.tsx                  # React DOM mount point
    ├── App.tsx                   # Main SPA container & view coordinator
    ├── App.css / index.css       # Tailwind & glassmorphism utilities
    ├── types/
    │   └── index.ts              # Data contracts, models & enums
    ├── services/
    │   ├── anemiaModelService.ts # CV model service boundary (mock/simulated)
    │   ├── screeningService.ts   # Rule-based multimodal scoring engine
    │   ├── syncService.ts        # LocalStorage offline sync queue
    │   ├── localizationService.ts# Multi-language translation dictionary
    │   └── mockData.ts           # Demo beneficiaries and clinical cases
    └── components/
        ├── scanner/
        │   └── OpticalCaptureZone.tsx # Image capture & ROI viewfinder
        ├── aww/                  # Anganwadi Worker portal & workflow components
        ├── chat/                 # AI Malnutrition Chatbot
        ├── doubt/                # Clinical Symptom Doubt Assistant
        ├── common/               # Modals, disclaimer banners, demo bars
        ├── admin/ / supervisor/  # Dashboard views
        └── website/              # Public product landing sections
```

---

## 3. Application Entry Point & Main Routes

### Entry Point
- `index.html` $\to$ `src/main.tsx` $\to$ `src/App.tsx`.

### Main Pages & View Modes
The application does not use URL-based routing (no `react-router-dom`). Instead, it is structured as a **State-Driven Multi-View SPA**:

1. **Top-Level Navigation Modes (`viewMode` in `App.tsx`):**
   - `'scanner'` — **Optical Anemia Scan Wizard** (Primary Point-of-Care Workflow).
   - `'doubt'` — **Clinical Doubt Assistant** (`ClinicalDoubtAssistant.tsx` — Symptom NLP evaluator).
   - `'chatbot'` — **Malnutrition & Nutrition AI Chatbot** (`MalnutritionAIChatbot.tsx`).
2. **Scanner Workflow Stages (`stage` in `App.tsx`):**
   - `stage = 'input'`: **Step 1: Patient Cohort & Demographic Setup** (Name, Category [Child, Adult, Pregnant, Elderly], Age, Biological Sex, Pregnancy Trimester).
   - `stage = 'camera'`: **Step 2: Optical Conjunctiva Capture** (`OpticalCaptureZone.tsx` — Drag-and-drop or camera file upload, ROI targeting, illumination indicator).
   - `stage = 'symptoms'`: **Step 3: Symptoms Checklist & Doubt Clarifier** (6 common symptoms + custom clinical doubt query).
   - `stage = 'analyzing'`: **Step 4: Analyzing Animation** (5-step progressive signal processing simulator).
   - `stage = 'result'`: **Step 5: Triage Result & Recommendations** (Core triage dashboard).

---

## 4. Screening Components & UI Result Presentation

The screening result is rendered in `src/App.tsx` (lines 700–835) under `{stage === 'result' && screeningResult && (...)}`:

### Result UI Elements Displayed:
1. **Patient Header:** Name, Age, Demographic Cohort, Village/Center.
2. **Core Metric Chips (3 Cards):**
   - **Anemia Risk:** Displays `screeningResult.anemiaRisk` (`'LOW'`, `'MODERATE'`, `'ELEVATED'`), color-coded (`text-red-700`, `text-amber-700`, `text-[#00776b]`). Subtitle: *"Optical Conjunctival Pallor"*.
   - **Symptom Load:** Number of flagged symptoms (e.g. `2 Flagged`). Subtitle: *"Reported Clinical Signs"*.
   - **Overall Triage Priority:** Displays `screeningResult.overallPriority` (`'LOW'`, `'MODERATE'`, `'HIGH'`).
3. **Deterministic WHO Safety Alert:** Displays `screeningResult.triggeredSafetyRules` (e.g. child SAM escalation or adult severe undernutrition rules).
4. **Contributing Signals & Clinical Explainability:** Grid of signal cards from `screeningResult.contributingSignals` (shows Signal Name, Category `IMAGE`/`ANTHROPOMETRY`/`DIET`/`TRAJECTORY`, Value Badge, Impact `POSITIVE`/`NEUTRAL`/`CONCERN`, and Description).
5. **Clinical Recommendation Box:** Formatted text from `screeningResult.recommendedAction`.
6. **Medical Safety Disclaimer:** Rendered via `<SafetyDisclaimerBanner />`.
7. **Session Screening History Log:** Recent completed screenings with timestamps and priority badges.

---

## 5. Existing API Calls & Network Contracts

### Search Audit:
- **`fetch()` calls found:** `0`
- **`axios` instances found:** `0`
- **HTTP endpoints (`/api/...`) found:** `0`
- **Backend URLs (`localhost:...`, `http://...`) found:** `0` (only external image Unsplash placeholders and local documentation links).

### Status Verdict:
**NO EXISTING API CONTRACT FOUND.**

The frontend currently uses simulated client-side service calls:
```typescript
// Current frontend call in App.tsx (line 151):
const res = await screeningService.executeScreening({
  beneficiary: currentBeneficiary,
  imageInput: { roiRegion: cameraRoiRegion, imageUri: capturedImage || undefined },
  anthropometry: anthropometryData,
  questions: questionsData,
  simulatedImageQuality: simulatedQuality,
});
```

---

## 6. Frontend Data Models & Field Names

All data structures are defined in `src/types/index.ts`:

### 1. Screening Result Model (`ScreeningResult`)
```typescript
export interface ScreeningResult {
  id: string;
  beneficiaryId: string;
  timestamp: string;
  imageQuality: 'GOOD' | 'INSUFFICIENT';
  imageQualityDetails: QualityCheckDetail;
  anemiaRisk: 'LOW' | 'MODERATE' | 'ELEVATED';
  nutritionRisk: 'LOW' | 'MODERATE' | 'HIGH';
  overallPriority: 'LOW' | 'MODERATE' | 'HIGH';
  trajectory: 'IMPROVING' | 'STABLE' | 'DECLINING' | 'RAPIDLY_DECLINING';
  anthropometry: AnthropometryData;
  questions: ContextQuestionsData;
  contributingSignals: SignalContribution[];
  triggeredSafetyRules: string[];
  recommendedAction: string;
  modelMetadata: ModelMetadata;
  synced: boolean;
  isDemoData: boolean;
}
```

### 2. Image Model Boundary Schema (`ModelInferenceResult`)
```typescript
export interface ModelInferenceResult {
  imageQuality: 'GOOD' | 'INSUFFICIENT';
  qualityDetails: {
    goodLighting: boolean;
    roiDetected: boolean;
    noMotion: boolean;
    sharpnessOk: boolean;
    reasons: string[];
  };
  anemiaRisk: 'LOW' | 'MODERATE' | 'ELEVATED';
  confidenceScore: number;
  palpebralPallorScore: number; // 0.0 to 1.0 pallor ratio
  metadata: ModelMetadata;
}
```

---

## 7. Comparison Table: Frontend Data Models vs. ML Unified Output

Below is a detailed comparison between our existing unified ML output (from `integration/multimodal.py`) and the frontend's existing fields:

| Frontend Field | Exists in Frontend? | Corresponding ML Output Field | Compatible? | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Patient Age** | `ageYears` (`number`) | `patient.age` (`float`) | ✅ **YES** | Direct 1:1 match. |
| **Patient Gender** | `sex` (`'Male' \| 'Female'`) | `patient.gender` (`str`) | ✅ **YES** | Direct 1:1 match. |
| **Anemia Class/Status** | `anemiaRisk` (`'LOW' \| 'MODERATE' \| 'ELEVATED'`) | `image.label` (`"anemic"` / `"non_anemic"`) | ⚠️ **MAPPING NEEDED** | ML produces binary (`"anemic"` / `"non_anemic"`); Frontend expects 3-tier risk (`'LOW'`, `'MODERATE'`, `'ELEVATED'`). |
| **Anemia Probability** | `palpebralPallorScore` ($0.0-1.0$) | `image.probability` ($0.0-1.0$) | ✅ **YES** | Direct continuous numerical probability $[0, 1]$. |
| **Model Confidence** | `confidenceScore` ($0.0-1.0$) | `image.confidence` ($0.5-1.0$) | ✅ **YES** | Direct continuous confidence score. |
| **Image Quality Status** | `imageQuality` (`'GOOD' \| 'INSUFFICIENT'`) | `image.quality_status` (`"good"` / `"poor"`) | ⚠️ **MAPPING NEEDED** | Case & string mapping: `"good"` $\to$ `'GOOD'`, `"poor"` $\to$ `'INSUFFICIENT'`. |
| **Image Quality Score** | ❌ (Implicit in checks) | `image.quality_score` ($0.0-1.0$) | ✅ **COMPATIBLE** | Can be passed directly into UI. |
| **Image Quality Checks** | `imageQualityDetails.reasons` | `image.quality_reasons` | ✅ **YES** | Direct list of failed checks (e.g. `["blur"]`). |
| **Hemoglobin (Hb)** | ❌ **NOT IN FRONTEND** | `ppg.predicted_hb_g_dl` (e.g. $14.60\text{ g/dL}$) | ❌ **NEW FIELD NEEDED** | The frontend currently has **no Hb numerical display card**. |
| **PPG Telemetry / Sensor** | ❌ **NOT IN FRONTEND** | `ppg.available`, `ppg.status`, `ppg.samples` | ❌ **NEW FIELD NEEDED** | No PPG hardware card or capture step exists in UI. |
| **Signal Quality (SQI)** | ❌ **NOT IN FRONTEND** (Only image quality) | `ppg.signal_quality`, `ppg.sqi` | ❌ **NEW FIELD NEEDED** | PPG SQI ($0.996$) needs a dedicated UI badge. |
| **Clinical Recommendation** | `recommendedAction` (`string`) | Produced by `screeningService` | ✅ **YES** | Maintained in frontend clinical logic. |
| **Contributing Signals** | `contributingSignals` (`SignalContribution[]`) | Can ingest both Image + PPG signals | ✅ **YES** | Rich explainability list can display PPG Hb and Image Pallor. |
| **Fusion Status** | ❌ **NOT IN FRONTEND** | `fusion.status` (`"NOT_VALIDATED"`) | ✅ **COMPATIBLE** | Can be displayed in metadata / disclaimer modals. |

---

## 8. Current Patient Flow & Proposed PPG Hardware Integration Point

### Current 4-Step Patient Flow:
```
1. Patient Cohort (App.tsx: stage='input')
   - Enter Name, Age, Sex, Cohort (Adult / Child / Pregnant / Elderly)
        ↓
2. Optical Capture (App.tsx: stage='camera')
   - Upload or take Palpebral Conjunctiva photo
        ↓
3. Symptoms & Doubts (App.tsx: stage='symptoms')
   - Check fatigue, dizziness, pale eyelids; ask custom doubt
        ↓
4. Analysis & Triage Results (App.tsx: stage='result')
   - Displays Anemia Risk, Symptom Load, Triage Priority, Explainability
```

### Where PPG Hardware Data Logically Enters:
PPG recording is a **10-second physical sensor touchpoint** using the MAX30102 sensor. Logically, it can enter either:
- **Option 1 (Unified Sensor Step):** Expand Step 2 into **"Optical & PPG Sensor Capture"** (Side-by-side: Camera capture on the left, ESP32 USB/Bluetooth/CSV upload on the right).
- **Option 2 (Dedicated Step 2B):** Insert a dedicated **"Step 2B: MAX30102 Pulse Oximeter & PPG"** immediately following the optical photo capture before symptoms.

---

## 9. Current Architecture Topology

Based on direct inspection of all source files in `anemia-detection-main/`:

### Current State:
```
                               Current Topology (Option C)
                               
   ┌────────────────────────────────────────────────────────────────────────┐
   │                          FRONTEND (Browser)                            │
   │                                                                        │
   │  ┌──────────────┐     ┌────────────────────────┐     ┌──────────────┐  │
   │  │   App.tsx    │ ──> │  screeningService.ts   │ ──> │ Mock Models  │  │
   │  │  UI / State  │     │ (In-browser WHO rules) │     │ (Simulated)  │  │
   │  └──────────────┘     └────────────────────────┘     └──────────────┘  │
   │                                                                        │
   └────────────────────────────────────────────────────────────────────────┘
```

### Future Production Target:
```
                               Target Topology (Option A/B)
                               
   ┌──────────────────────┐                    ┌────────────────────────────┐
   │  FRONTEND (React 19) │                    │    PRAHARI BACKEND API     │
   │   anemia-detection   │ ── HTTP POST ───>  │  (FastAPI / integration)   │
   │                      │    (Multipart/JSON)│                            │
   │  • Patient Form      │                    │  • Multimodal Coordinator  │
   │  • Image Capture     │ <── JSON Result ── │  • Person 1 Image Engine   │
   │  • ESP32 PPG Upload  │                    │  • PPG Hardware Pipeline   │
   └──────────────────────┘                    └────────────────────────────┘
```

---

## 10. Missing Pieces Required for Full Integration (Gap Analysis)

1. **Backend HTTP Client Service in Frontend:**
   - A dedicated `apiService.ts` or real implementation of `anemiaModelService.ts` that issues `fetch()` / `POST` requests to our backend (e.g. `http://localhost:8000`).
2. **PPG Hardware Ingestion in UI:**
   - An upload or live serial/Bluetooth ingest component in the frontend to supply the 10-second ESP32 CSV (`timestamp_ms,red,ir`) alongside patient age and gender.
3. **Hemoglobin (Hb in g/dL) UI Display Card:**
   - A dedicated Hemoglobin metric card in the result view (e.g. showing `14.60 g/dL` with normal/low color-coded range indicators based on WHO cutoffs).
4. **Data Contract Mapping Layer:**
   - Adapters to convert between backend JSON format (`image.label: "anemic"`, `ppg.predicted_hb_g_dl: 14.6`) and frontend UI state (`anemiaRisk: "ELEVATED"`, `contributingSignals`).

---

## 11. Unknowns & Unresolved Items

1. **Standalone Backend Repository or Direct Integration:**
   - *Observation:* `anemia-detection-main` currently has no backend folder (it is purely a Vite frontend).
   - *Status:* `UNRESOLVED — whether the frontend will connect directly to person1's FastAPI server or a unified PRAHARI gateway.`
2. **Real-time Live WebSerial / Bluetooth PPG vs. CSV File Upload:**
   - *Observation:* `ppg-anemia` currently tests with CSV files. Whether the frontend will support WebSerial API for live MAX30102 streaming directly from the ESP32 in the browser or upload recorded CSV files is not yet implemented.
   - *Status:* `UNRESOLVED — evidence not found in current project for WebSerial hardware driver in frontend.`
3. **Authentication & User Sessions:**
   - *Observation:* No JWT tokens, cookies, or auth headers exist in the frontend code.
   - *Status:* `NO AUTHENTICATION PRESENT in current frontend prototype.`
