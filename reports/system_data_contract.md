# PRAHARI — System Data Contract & Field Mapping Specification

**Status:** Final Specification Baseline  
**Date:** 2026-08-20  
**Target:** Multi-Component Data Integration  

---

## 1. Subsystem Schemas & Interface Definitions

### 1.1 Image/CV Subsystem (`person1/`)

#### Input Contract
```python
# Location: person1/app/ai/inference.py
ImageInput = Union[
    str,          # Absolute or relative file path (PNG, JPG, HEIC)
    bytes,        # Raw image buffer bytes
    np.ndarray,   # OpenCV BGR / RGB image array (H, W, 3)
    PIL.Image.Image # Standard PIL RGB image object
]
```

#### Output Contract
```python
# Location: person1/app/ai/inference.py
@dataclass
class InferenceResult:
    label: str               # "anemic" | "non_anemic"
    probability: float       # Anemia probability in [0.0, 1.0]
    confidence: float        # Classification confidence in [0.5, 1.0]
    quality_status: str      # "good" | "poor"
    quality_score: float     # Combined image usability score in [0.0, 1.0]
    quality_reasons: list[str] # Failure flags, e.g. ["blur", "low_brightness"]
    inference_time_ms: float # Execution latency in milliseconds
```

---

### 1.2 Optical PPG Hardware Subsystem (`ppg-anemia/`)

#### Hardware Input Contract
```
Format: CSV (Header: timestamp_ms,red,ir)
Sampling Rate: 25 Hz (± 1 Hz)
Duration: ~10.0 seconds
Samples: Exactly 250 RED samples + 250 IR samples
ADC Counts: Raw integer values (50,000 to 180,000)
Demographics: age (float/int), gender ("M" | "F" | "Male" | "Female")
```

#### Output Contract
```python
# Location: ppg-anemia/src/inference.py & integration/schemas.py
@dataclass / class PPGResult:
    predicted_hb_g_dl: float  # Predicted continuous Hemoglobin in g/dL (e.g. 14.60)
    sqi: float                # Signal Quality Index in [0.0, 1.0] (e.g. 0.996)
    signal_quality: str       # "good" | "poor"
    sampling_rate_hz: float   # 25.0
    samples: int              # 250
    reasons: list[str]        # ["flatline", "clipping", "low_snr"]
```

---

### 1.3 Multimodal Integration Layer (`integration/`)

#### Request Schema
```python
# Location: integration/schemas.py
class MultimodalScreeningRequest(BaseModel):
    patient: PatientDemographics # id, age (years), gender ("male"|"female"), is_pregnant, trimester
    image: Optional[ImageInput]  # file_path, image_bytes, base64_image
    ppg: Optional[PPGInput]      # csv_path, csv_text, samples (list of dicts)
```

#### Response Schema
```python
# Location: integration/schemas.py
class MultimodalScreeningResult(BaseModel):
    patient: PatientDemographics
    image: Optional[ImageModalityResult]
    ppg: Optional[PPGModalityResult]
    fusion: FusionMetadata       # status: "NOT_VALIDATED", method: "INDEPENDENT_MODALITIES"
    overall_status: str          # "SUCCESS" | "PARTIAL_SUCCESS" | "FAILED"
    timestamp: str               # ISO 8601 UTC timestamp
```

---

### 1.4 Swayam Risk / Clinical Logic Engine (`swayam risk/`)

#### Request Schema (`POST /api/screening/analyze`)
```python
# Location: swayam risk/backend/src/models/schemas.py
class ScreeningRequest(BaseModel):
    beneficiary_id: str          # Registered ID (e.g. "B001")
    anemia: AnemiaInput          # risk: "low"|"moderate"|"high", confidence: 0.0-1.0
    weight: float                # Weight in kg (e.g. 13.1)
    height: float                # Height in cm (e.g. 97.0)
    muac: float                  # MUAC in cm (e.g. 12.7)
    diet: DietInput              # iron_rich_food: bool, frequency: str, diversity: 0-9
    pregnancy: bool = False
    trimester: Optional[int] = None # 1, 2, or 3
    ifa: IfaInput                # adherence: "good" | "poor" | "unknown"
    symptoms: SymptomsInput      # severe_pallor, breathlessness, bilateral_oedema, fatigue
```

#### Response Schema (`ScreeningResponse`)
```python
# Location: swayam risk/backend/src/models/schemas.py
class ScreeningResponse(BaseModel):
    anemia_risk: RiskBand            # "low" | "moderate" | "high"
    nutrition_risk: RiskBand         # "low" | "moderate" | "high"
    overall_priority: OverallPriority# "low" | "moderate" | "high" | "critical"
    confidence: float                # Calibrated confidence in [0.0, 1.0]
    trajectory: Trajectory           # "improving" | "stable" | "declining" | "rapidly_declining" | "insufficient_data"
    contributors: list[Contributor]  # [{feature, label, importance}, ...]
    recommended_action: RecommendedAction # "routine_monitoring" | "nutrition_counselling" | "confirmatory_testing" | "immediate_referral" | "manual_protocol_escalation"
    safety_flags: list[str]          # ["SEVERE_ANEMIA_THRESHOLD", "SEVERE_MALNUTRITION", ...]
```

---

### 1.5 Arya Relational Backend (`arya-backend/`)

#### Relational Schema (`PostgreSQL 18`)
```sql
-- Table: beneficiaries
CREATE TABLE beneficiaries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    date_of_birth TIMESTAMPTZ NOT NULL,
    sex VARCHAR(10) NOT NULL, -- 'MALE' | 'FEMALE' | 'OTHER'
    category VARCHAR(20) NOT NULL, -- 'CHILD' | 'PREGNANT_WOMAN'
    is_pregnant BOOLEAN DEFAULT FALSE,
    trimester INTEGER,
    created_by_id INTEGER REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: results
CREATE TABLE results (
    id SERIAL PRIMARY KEY,
    screening_id INTEGER UNIQUE REFERENCES screenings(id) ON DELETE CASCADE,
    anemia_risk VARCHAR(20) NOT NULL, -- 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL'
    nutrition_risk VARCHAR(20) NOT NULL,
    overall_priority VARCHAR(20) NOT NULL,
    confidence FLOAT,
    trajectory VARCHAR(50),
    recommended_action TEXT,
    contributors JSONB,
    model_name VARCHAR(100),
    model_version VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 1.6 Sidhan Frontend (`anemia-detection-main/`)

#### In-Memory Data Model (`src/types/index.ts`)
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

---

## 2. Field Mapping & Cross-Layer Compatibility

The table below maps attributes across all 6 subsystems and defines required type/value transformations:

| Source Entity & Field | Destination Subsystem & Field | Data Types | Compatibility | Transformation Required |
| :--- | :--- | :--- | :---: | :--- |
| **Patient Age** (`PatientDemographics.age`) | Swayam Risk `age_months` | `float` (years) $\to$ `int` (months) | ⚠️ **TRANSFORM** | `age_months = int(age_years * 12)` |
| **Patient Age** (`PatientDemographics.age`) | Arya DB `date_of_birth` | `float` (years) $\to$ `datetime` | ⚠️ **TRANSFORM** | `date_of_birth = now - timedelta(days=age*365.25)` |
| **Patient Gender** (`gender`) | Swayam Risk `sex` | `"male" \| "female"` | ✅ **DIRECT** | Direct lower-case string pass-through. |
| **Patient Gender** (`gender`) | Arya DB `sex` | `"MALE" \| "FEMALE"` | ⚠️ **TRANSFORM** | Uppercase enum conversion (`gender.upper()`). |
| **Image Anemia Label** (`image.label`) | Swayam Risk `anemia.risk` | `"anemic" \| "non_anemic"` $\to$ `"high" \| "low"` | ⚠️ **TRANSFORM** | Map `"anemic"` $\to$ `"high"`, `"non_anemic"` $\to$ `"low"` (or moderate if prob $\in [0.4, 0.6]$). |
| **Image Probability** (`image.probability`) | Frontend `palpebralPallorScore` | `float` $[0.0, 1.0]$ | ✅ **DIRECT** | Direct numerical assignment. |
| **Image Confidence** (`image.confidence`) | Swayam Risk `anemia.confidence` | `float` $[0.5, 1.0]$ | ✅ **DIRECT** | Direct numerical assignment. |
| **Image Quality Status** (`image.quality_status`)| Frontend `imageQuality` | `"good" \| "poor"` $\to$ `'GOOD' \| 'INSUFFICIENT'` | ⚠️ **TRANSFORM** | Map `"good"` $\to$ `'GOOD'`, `"poor"` $\to$ `'INSUFFICIENT'`. |
| **PPG Predicted Hb** (`ppg.predicted_hb_g_dl`) | Swayam Safety `SafetyInput.hb_gdl` | `float` (g/dL, e.g. 14.60) | ✅ **DIRECT** | Direct float pass-through (enables Red Flag 1 severe anemia check). |
| **PPG Predicted Hb** (`ppg.predicted_hb_g_dl`) | Frontend (New Result Card) | `float` (g/dL) | ❌ **NEW FIELD** | Add `predictedHb` to Frontend `ScreeningResult` interface. |
| **PPG SQI** (`ppg.sqi`) | Frontend (New Quality Badge) | `float` $[0.0, 1.0]$ | ❌ **NEW FIELD** | Add `ppgSqi` & `ppgSignalQuality` to Frontend interface. |
| **Risk Band** (`ScreeningResponse.anemia_risk`)| Frontend `anemiaRisk` | `"low" \| "moderate" \| "high"` $\to$ `'LOW' \| 'MODERATE' \| 'ELEVATED'` | ⚠️ **TRANSFORM** | Map `"high"` $\to$ `'ELEVATED'`, `"moderate"` $\to$ `'MODERATE'`, `"low"` $\to$ `'LOW'`. |
| **Risk Priority** (`overall_priority`) | Arya DB `overall_priority` | `"low"..."critical"` $\to$ `"LOW"..."CRITICAL"` | ⚠️ **TRANSFORM** | Uppercase enum conversion (`overall_priority.upper()`). |
| **Contributors** (`contributors`) | Arya DB `contributors` | `list[dict]` $\to$ `JSONB` | ✅ **DIRECT** | Serialized directly into PostgreSQL JSONB column. |
| **Safety Flags** (`safety_flags`) | Frontend `triggeredSafetyRules` | `list[str]` | ✅ **DIRECT** | Direct pass-through of safety flag string array. |

---

## 3. Standardized Error and Status Codes

| Subsystem | HTTP / Status Code | Meaning | Payload Signature |
| :--- | :---: | :--- | :--- |
| **Multimodal ML** | `SUCCESS` | Both Image and PPG processed successfully | `overall_status: "SUCCESS"` |
| **Multimodal ML** | `PARTIAL_SUCCESS` | One modality failed or was omitted; other succeeded | `overall_status: "PARTIAL_SUCCESS"` |
| **Multimodal ML** | `FAILED` | Both modalities failed or threw fatal errors | `overall_status: "FAILED"` |
| **Swayam Risk** | `404 Not Found` | Beneficiary ID not registered in database | `{"detail": "Unknown beneficiary: B001"}` |
| **Swayam Risk** | `422 Unprocessable`| Invalid anthropometry z-scores, negative age, invalid trimester | `{"detail": "Anthropometry validation error: ..."}` |
| **Arya Backend** | `409 Conflict` | Result already exists for specified screening ID | `{"detail": "Result already exists for this screening"}` |
| **Arya Backend** | `503 Service Unavail`| PostgreSQL database connectivity check failed (`SELECT 1`) | `{"status": "error", "database": "disconnected"}` |
