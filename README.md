# PRAHARI — Multimodal Point-of-Care Anemia & Malnutrition Screening System

PRAHARI is an integrated, non-invasive point-of-care clinical decision support system designed for frontline healthcare workers (such as Anganwadi workers and primary health center staff). It provides rapid, safe risk stratification for anemia and malnutrition across maternal, pediatric, and general adult populations.

---

## 🌟 System Architecture

```
anemia-plus-hardware-plus-image/
│
├── anemia-detection-main/       # React + TypeScript Frontline Screening Dashboard
│   ├── src/components/aww/     # Workflow for point-of-care screening
│   ├── src/components/results/ # Comprehensive Screening Summary & Clinical Actions
│   ├── src/components/nutrition/ # Age-aware anthropometric evaluation (BMI & MUAC)
│   └── src/services/           # API clients & hardware bridge services
│
├── arya-backend/                # FastAPI + PostgreSQL Production Backend
│   ├── backend/app/routers/    # Screening, Beneficiary, Nutrition endpoints
│   ├── backend/app/services/   # ML orchestration, clinical safety gates, anthropometry
│   └── backend/docker-compose.yml # Containerized database & services
│
├── integration/                 # Multimodal Telemetry Coordinator
│   ├── multimodal.py           # Independent stream aggregation & non-fusion orchestration
│   └── schemas.py              # Normalized data exchange contracts
│
├── person1/                     # Palpebral Conjunctiva Computer Vision Pipeline
│   ├── app/ai/inference.py     # Random Forest + MobileNetV2 feature extraction & inference
│   ├── app/ai/preprocessing.py # HSV/Lab/RGB colorimetric analysis & quality gates
│   └── models/                 # Pretrained weights & metadata
│
├── ppg-anemia/                  # Optical PPG Hemoglobin Estimation Pipeline
│   ├── src/preprocessing/      # 25 Hz signal filtering, peak detection & SQI calculation
│   ├── src/models/             # Dual-wavelength AC/DC ratio feature regression
│   └── esp32/                  # MAX30102 sensor firmware & Arduino capture sketch
│
├── risk-engine/                 # Clinical Risk Assessment & WHO Safety Engine
│   ├── backend/src/safety/     # Deterministic WHO safety rules & red-flag overrides
│   ├── backend/src/anthropometry/ # WHO 2006/2007 growth standards & z-score engine
│   └── backend/src/context/    # Maternal trimester & pediatric threshold matrices
│
├── tests/                       # Comprehensive Integration & Quality Test Suite
│   ├── test_anthropometry_nutrition.py
│   ├── test_backend_ml_integration.py
│   ├── test_clinical_action_layer.py
│   ├── test_frontend_backend_contract.py
│   └── test_multimodal_integration.py
│
├── reports/                     # Architecture & Validation Documentation
└── .gitignore                   # Repository security & data exclusion rules
```

---

## 🔬 Core Screening Streams (Independent Telemetry)

1. **Conjunctival Computer Vision**: Analyzes palpebral conjunctiva erythema and mucosal pallor from standardized smartphone camera images.
2. **Optical PPG Hemoglobin**: Predicts blood hemoglobin concentration ($g/dL$) via dual-wavelength (660nm Red / 880nm Infrared) pulsatile photoplethysmography captured with a MAX30102 sensor at 25 Hz over 10 seconds.
3. **Anthropometric & Nutritional Evaluation**: Computes live body mass index ($\text{BMI} = \text{kg}/\text{m}^2$), age-aware reference bands (WHO 2007 $5\text{--}19\text{y}$ BMI-for-age), and mid-upper arm circumference (MUAC $6\text{--}59\text{m}$) integrated with dietary diversity scoring.
4. **Clinical Risk & WHO Safety Engine**: Evaluates maternal trimester thresholds, pediatric risk factors, and deterministic safety rules to provide appropriate triage escalation (*LOW*, *MODERATE*, *HIGH*, *CRITICAL*).

---

## 🚀 Quick Start

### 1. Backend Server
```bash
cd arya-backend/backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
- Health Check: `http://127.0.0.1:8000/health`
- Interactive API Docs: `http://127.0.0.1:8000/docs`

### 2. Frontend Application
```bash
cd anemia-detection-main
npm install
npm run dev
```
- Web Application: `http://localhost:5173`

### 3. Run Automated Tests
```bash
pytest tests/
```

---

## 🛡️ Safety & Clinical Disclaimer

PRAHARI is an assistive point-of-care screening aid designed for risk stratification and triage prioritization in frontline community health settings. It is **not a diagnostic device** and does not issue medical prescriptions. All critical findings must be confirmed via clinical examination and laboratory testing (CBC/Hemocue).
