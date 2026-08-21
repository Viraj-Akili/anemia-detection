# PRAHARI — Risk Logic Backend

**Early-warning screening backend for anemia & malnutrition risk**

PRAHARI fuses CV-pipeline output, WHO anthropometry, dietary context, and visit history into an explainable, safety-railed risk assessment. Screening only — never a diagnosis.

## Features

- **Multi-modal Fusion**: Combines AI camera-based anemia detection with anthropometric measurements, dietary intake, and medical history
- **WHO Standards**: Uses primary-source WHO Child Growth Standards (2006) for z-score calculations
- **Safety Layer**: 5 deterministic red-flag rules with escalation-only logic
- **Trajectory Tracking**: Detects declining health trends across visit history
- **Explainability**: SHAP-based top-3 contributors for every risk assessment
- **Production-Ready**: P95 latency <50ms, comprehensive error handling, structured logging

## Quick Start

### Prerequisites

- Python 3.12+
- Virtual environment (recommended)

### Installation

```bash
# Clone repository
git clone <repository-url>
cd HackProj

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
.venv/bin/alembic upgrade head

# Seed test data (optional)
python3 scripts/seed_trajectory_data.py
```

### Running the Server

```bash
# Development server with auto-reload
.venv/bin/uvicorn src.main:app --reload

# Production server
.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**API Documentation**: http://127.0.0.1:8000/docs  
**Health Check**: http://127.0.0.1:8000/health

## API Usage

### Register a Beneficiary

```bash
curl -X POST http://localhost:8000/api/beneficiaries \
  -H "Content-Type: application/json" \
  -d '{
    "id": "B001",
    "name": "Child Name",
    "age_months": 36,
    "sex": "female",
    "pregnancy": false
  }'
```

**Response**:
```json
{
  "id": "B001",
  "name": "Child Name",
  "age_months": 36,
  "sex": "female",
  "pregnancy": false,
  "created_at": "2026-08-18T19:20:00.000Z"
}
```

### Screen a Beneficiary

```bash
curl -X POST http://localhost:8000/api/screening/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "beneficiary_id": "B001",
    "anemia": {
      "risk": "moderate",
      "confidence": 0.82
    },
    "weight": 13.1,
    "height": 97,
    "muac": 12.7,
    "diet": {
      "iron_rich_food": false,
      "frequency": "sometimes",
      "diversity": 5
    }
  }'
```

**Response** (Appendix A Contract):
```json
{
  "anemia_risk": "moderate",
  "nutrition_risk": "high",
  "overall_priority": "high",
  "confidence": 0.81,
  "trajectory": "insufficient_data",
  "contributors": [
    {
      "feature": "anemia_risk_score",
      "label": "AI camera-based anemia estimate",
      "importance": 0.45
    },
    {
      "feature": "diet_risk",
      "label": "Low reported dietary iron intake",
      "importance": 0.32
    },
    {
      "feature": "muac_z",
      "label": "Low mid-upper arm circumference",
      "importance": 0.28
    }
  ],
  "recommended_action": "confirmatory_testing",
  "safety_flags": []
}
```

### Get Beneficiary Details

```bash
curl http://localhost:8000/api/beneficiaries/B001
```

## API Contract

### POST /api/screening/analyze

**Request Fields**:
- `beneficiary_id` (required): Registered beneficiary ID
- `anemia` (required): CV-pipeline output
  - `risk`: "low" | "moderate" | "high"
  - `confidence`: 0.0-1.0
- `weight` (required): Weight in kg
- `height` (required): Height in cm
- `muac` (required): Mid-upper arm circumference in cm
- `diet` (optional): Dietary intake
  - `iron_rich_food`: boolean
  - `frequency`: "never" | "rare" | "sometimes" | "often"
  - `diversity`: 0-9 (food groups)
- `pregnancy` (optional): boolean
- `trimester` (required if pregnant): 1 | 2 | 3
- `ifa` (optional): Iron-folic acid adherence
  - `adherence`: "good" | "poor" | "unknown"
- `symptoms` (optional): Red-flag symptoms
  - `severe_pallor`: boolean
  - `breathlessness`: boolean
  - `bilateral_oedema`: boolean
  - `fatigue`: boolean

**Response Fields** (Appendix A):
- `anemia_risk`: "low" | "moderate" | "high"
- `nutrition_risk`: "low" | "moderate" | "high"
- `overall_priority`: "low" | "moderate" | "high" | "critical"
- `confidence`: 0.0-1.0
- `trajectory`: "improving" | "stable" | "declining" | "rapidly_declining" | "insufficient_data"
- `contributors`: Array of {feature, label, importance}
- `recommended_action`: "routine_monitoring" | "nutrition_counselling" | "confirmatory_testing" | "immediate_referral" | "manual_protocol_escalation"
- `safety_flags`: Array of red-flag identifiers

**Error Responses**:
- **404**: Unknown beneficiary
- **422**: Validation failure (invalid measurements, missing fields, enum values)
- **500**: Internal server error

## Retraining the Fusion Model

The fusion model combines anthropometry, context, and AI estimates into calibrated risk probabilities.

### Generate Training Data

```bash
# Create synthetic training data or load from CSV
python3 src/fusion/model_train.py --generate-data
```

### Train the Model

```bash
# Train both heads (anemia + nutrition) with Platt calibration
python3 src/fusion/model_train.py --train

# Artifacts saved to: assets/models/
# - anemia_model.json
# - nutrition_model.json
# - thresholds.json (operating thresholds + Platt coefficients)
# - features.json (20-feature order)
```

### Validate Model Performance

```bash
# Run model tests
.venv/bin/pytest src/fusion/tests.py -v

# Expected metrics:
# - AUROC > 0.85 on validation split
# - Calibration slope ~1.0 ± 0.1
# - Load time < 1 second
```

## Testing

### Run All Tests

```bash
# Full test suite
.venv/bin/pytest src/ -v

# With coverage
.venv/bin/pytest src/ --cov=src --cov-report=html
```

### Test Categories

```bash
# Integration tests (screening pipeline)
.venv/bin/pytest src/api/tests/test_screening_integration.py -v

# Edge cases and safety properties
.venv/bin/pytest src/api/tests/test_edge_cases.py -v

# Anthropometry (WHO z-scores)
.venv/bin/pytest src/anthropometry/tests.py -v

# Context modifiers
.venv/bin/pytest src/context/tests.py -v

# Fusion model
.venv/bin/pytest src/fusion/tests.py -v

# Safety layer
.venv/bin/pytest src/safety/tests.py -v

# Trajectory engine
.venv/bin/pytest src/trajectory/tests.py -v
```

### Performance Benchmarks

```bash
# Latency benchmark (P95 < 500ms target)
.venv/bin/pytest src/api/tests/test_screening_integration.py::TestLatencyBenchmark -v -s
```

## Architecture

### Pipeline Flow

```
Request
  ↓
Load Beneficiary (age, sex, pregnancy)
  ↓
Load Visit History (last 5 visits)
  ↓
Anthropometry Engine (WHO z-scores + categories)
  ↓
Context Engine (diet risk, IFA, symptoms, Hb threshold)
  ↓
Feature Builder (20-feature fusion vector)
  ↓
Fusion Model (XGBoost → Platt calibration → risk probabilities)
  ↓
Safety Rules (5 WHO red flags → risk floors)
  ↓
Safety Layer (max(fusion, rules) → overall priority + action)
  ↓
Trajectory Engine (slope-based trend + early intervention)
  ↓
Persist Visit (append-only history)
  ↓
Response (Appendix A contract)
```

### Key Components

**Anthropometry Engine** (`src/anthropometry/`)
- WHO Child Growth Standards (0-60 months)
- LMS method for z-score calculation
- MUAC categories (SAM/MAM cutoffs)
- Linear interpolation between table rows

**Context Engine** (`src/context/`)
- Dietary risk score (frequency × diversity)
- IFA protection multiplier
- Symptom red-flag scan
- WHO 2024 Hb thresholds (pregnancy-aware)

**Fusion Engine** (`src/fusion/`)
- Dual-head XGBoost (anemia + nutrition)
- Platt calibration for probability reliability
- SHAP explainer for top-3 contributors
- 20-feature vector (fixed order)

**Safety Layer** (`src/safety/`)
- 5 deterministic WHO red-flag rules
- Escalation-only: `final_risk = max(fusion, rules)`
- Risk floors never downgrade fusion output
- Immediate referral triggers

**Trajectory Engine** (`src/trajectory/`)
- Slope-based classification over last ≤5 visits
- Early intervention rule (2 consecutive rising)
- Auto-escalates priority when flagged

## Database Schema

### Beneficiaries Table

```sql
CREATE TABLE beneficiaries (
    id VARCHAR PRIMARY KEY,  -- e.g., "B001"
    name TEXT,
    age_months INTEGER NOT NULL,
    sex VARCHAR(10) NOT NULL,  -- "male" | "female"
    pregnancy BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Visits Table (Append-Only)

```sql
CREATE TABLE visits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    beneficiary_id VARCHAR REFERENCES beneficiaries(id),
    visit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Anthropometry
    weight_kg NUMERIC(5,2),
    height_cm NUMERIC(5,2),
    muac_mm NUMERIC(5,1),
    whz NUMERIC(4,2),
    haz NUMERIC(4,2),
    waz NUMERIC(4,2),
    muac_category VARCHAR(20),
    whz_category VARCHAR(20),
    haz_category VARCHAR(20),
    waz_category VARCHAR(20),
    
    -- CV Pipeline Input
    anemia_ai_risk VARCHAR(20),
    anemia_ai_confidence NUMERIC(3,2),
    
    -- Screening Output
    anemia_risk VARCHAR(20),
    nutrition_risk VARCHAR(20),
    overall_priority VARCHAR(20),
    confidence NUMERIC(3,2),
    trajectory VARCHAR(30),
    contributors JSONB,
    recommended_action VARCHAR(50),
    safety_flags JSONB,
    escalated BOOLEAN,
    context_snapshot JSONB,
    
    INDEX idx_visits_beneficiary_date (beneficiary_id, visit_date)
);
```

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=sqlite:///./prahari.db  # Default: SQLite
# DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/prahari

# Logging
LOG_LEVEL=INFO  # DEBUG | INFO | WARNING | ERROR

# Model Path
MODELS_DIR=assets/models  # Fusion model artifacts
```

### Database Migrations

```bash
# Create new migration
.venv/bin/alembic revision --autogenerate -m "description"

# Apply migrations
.venv/bin/alembic upgrade head

# Rollback
.venv/bin/alembic downgrade -1
```

## Development

### Project Structure

```
HackProj/
├── src/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── beneficiaries.py  # CRUD endpoints
│   │   │   └── screening.py      # Full pipeline
│   │   ├── deps.py               # FastAPI dependencies
│   │   └── tests/                # Integration tests
│   ├── anthropometry/
│   │   ├── engine.py             # WHO z-scores
│   │   ├── who_tables.py         # WHO data
│   │   └── tests.py
│   ├── context/
│   │   ├── engine.py             # Modifiers
│   │   ├── thresholds.py         # Hb cutoffs
│   │   └── tests.py
│   ├── fusion/
│   │   ├── engine.py             # Model inference
│   │   ├── features.py           # Feature builder
│   │   ├── model_train.py        # Training script
│   │   └── tests.py
│   ├── safety/
│   │   ├── engine.py             # Escalation layer
│   │   ├── rules.py              # WHO red flags
│   │   └── tests.py
│   ├── trajectory/
│   │   ├── engine.py             # Trend detection
│   │   └── tests.py
│   ├── models/
│   │   ├── database.py           # SQLAlchemy setup
│   │   ├── entities.py           # ORM models
│   │   └── schemas.py            # Pydantic models
│   └── main.py                   # FastAPI app
├── assets/models/                # Fusion artifacts
├── alembic/                      # DB migrations
├── scripts/                      # Utilities
└── requirements.txt
```

### Code Style

```bash
# Format code
black src/

# Lint
ruff check src/

# Type check
mypy src/
```

## Performance

### Latency (100 requests)

```
Min:    35ms
Median: 42ms
P95:    48ms  ✓ (target: <500ms)
Max:    65ms
```

### Throughput

- Single worker: ~20 req/sec
- 4 workers: ~75 req/sec

### Resource Usage

- Memory: ~200MB (fusion models loaded)
- CPU: <5% idle, ~30% under load (single core)

## License

[License information]

## References

- WHO Child Growth Standards (2006): https://www.who.int/tools/child-growth-standards
- WHO Hemoglobin Concentrations (2024): https://www.who.int/publications/i/item/WHO-NMH-NHD-MNM-11.1
- MUAC-for-age Reference (Mramba et al. 2017): BMJ 358:j3423

## Support

For questions or issues, please contact [support contact].

---

**Version**: 0.1.0  
**Last Updated**: 2026-08-18
