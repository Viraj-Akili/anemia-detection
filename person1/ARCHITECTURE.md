# PRAHARI System Architecture & Data Flow

**Hackathon Architecture — End-to-End Multimodal Anemia & Malnutrition Screening Platform**

---

## 1. Team Ownership & Responsibilities

```
+--------------------------------------------------------------------------------+
|                             PRAHARI TEAM ROLES                                 |
+----------------------+--------------------+-----------------+------------------+
| Sidhan    | Arya               | Viraj (Person 1)| Swayam           |
| UI / Mobile App      | Backend / Database | AI / CV Service | Risk Engine      |
+----------------------+--------------------+-----------------+------------------+
```

| Role / Domain | Owner | Key Responsibilities |
|---|---|---|
| **UI / Client Application** | **Frontend Teammate** | Mobile/Web camera interface, image capture guidance, patient intake forms, interactive screening report display. |
| **Main Backend & Database** | **Arya** | Central API gateway, PostgreSQL database, beneficiary records, session persistence, audit logging, auth. |
| **AI / Computer Vision** | **Viraj (Person 1)** | Image quality gate, tissue feature extraction (RGB/LAB/HSV), Random Forest screening inference, standalone FastAPI service. |
| **Multimodal Risk Engine** | **Swayam** | Fusion of AI screening signal + anthropometry (MUAC) + diet recall + symptoms + history -> Final PRAHARI Risk Score & referral. |

---

## 2. End-to-End Data Flow

```mermaid
flowchart TD
    subgraph UI ["Frontend (Mobile / Web Client) [Frontend Teammate]"]
        A[User captures eye photo & patient intake data] --> B[FormData with image & survey]
    end

    subgraph BackendGateway ["Main Backend & API Gateway [Arya]"]
        B --> C[Arya Main Backend / API]
        C -->|Persist beneficiary| DB[(PostgreSQL Database)]
        C -->|HTTP POST /api/v1/anemia/screen| D[AI / CV Service Entrypoint]
    end

    subgraph AIService ["AI / CV Microservice [Viraj - Person 1]"]
        D --> E[Input Validation & MIME Check]
        E --> F[Quality Gate: Blur, Brightness, Contrast, Resolution]
        F -->|Quality Pass| G[Tissue ROI & Alpha-Masked Feature Extraction]
        F -->|Quality Fail| H[Return HTTP 200 success=false + IMAGE_QUALITY_LOW]
        G --> I[Random Forest Color Classifier v1.0]
        I --> J[Anemia Screening Signal: label + model_probability]
    end

    subgraph RiskEngine ["Multimodal Risk Engine [Swayam]"]
        J --> K[Swayam PRAHARI Risk Engine]
        C -->|Anthropometry MUAC, Diet, Symptoms, History| K
        K --> L[WHO Guidelines & Clinical Decision Rules Fusion]
        L --> M[Final PRAHARI Result: Risk Level & Action Plan]
    end

    M --> C
    C -->|Complete Screening Summary| A
```

---

## 3. Detailed Data Flow Description

```
Frontend (UI)
   ↓ (Multipart FormData: image + patient data)
Arya / Main Backend
   ↓ (HTTP POST /api/v1/anemia/screen with image bytes)
AI Service (Viraj)
   ↓
Quality Gate (checks brightness, contrast, sharpness, resolution)
   ↓
ROI / Features (alpha-masked palpebral conjunctiva color features: 19 features in RGB/LAB/HSV)
   ↓
Random Forest Primary Model (random_forest_color_baseline v1.0)
   ↓
Anemia Screening Signal (prediction.label + prediction.model_probability)
   ↓
Swayam Risk Engine (fuses AI signal + MUAC + diet + clinical symptoms + history)
   ↓
Final PRAHARI Result (Risk Tier: High/Medium/Low + Action Plan / Referral)
```

---

## 4. Component Boundaries & Isolation Guarantees

1. **AI Service Independence:**
   - The AI service operates as an autonomous microservice on port 8000.
   - It maintains zero dependency on PostgreSQL, user authentication, or mobile UI frameworks.
   - It performs one task with high reliability: validating image quality and predicting conjunctival anemia signal.

2. **Decoupled Risk Calculation:**
   - The AI service does **not** compute final patient risk, does not predict hemoglobin g/dL, and does not prescribe treatments.
   - Swayam's engine remains the single source of truth for clinical triage logic and multi-factor fusion.

3. **Arya Backend Decoupling:**
   - Arya's backend does not embed or execute machine learning inference pipelines locally; it communicates with the AI service over lightweight HTTP REST.
