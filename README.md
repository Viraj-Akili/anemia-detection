# PRAHARI — Smartphone-First Early Warning System for Anemia & Malnutrition

> **HTAD-06 Hackathon Platform** | Aligned with **WHO 2024 Guidelines**, **Anemia Mukt Bharat (MoHFW)**, and **POSHAN Abhiyaan (MWCD)**

### 🌐 Frontend Web Application Link:
👉 **[http://localhost:3000/](http://localhost:3000/)** *(Local Web App Server)*

---

PRAHARI turns any frontline Anganwadi Worker (AWW) or ASHA worker's smartphone into an **offline, non-invasive, early-warning sentinel** for anemia and malnutrition in children (6–59 months) and pregnant women. 

Unlike one-shot diagnostic tools, PRAHARI combines **optical camera screening**, **WHO anthropometry (MUAC/weight/height)**, and **longitudinal trajectory intelligence** to flag health decline *before* visible clinical damage occurs.

---

## 🌟 Key Capabilities

* **Multimodal Risk Screening Engine**: Fuses optical conjunctiva/nail-bed pallor signals, WHO MUAC/weight z-score rules, and dietary/deworming context into a single calibrated risk score.
* **Longitudinal Intelligence**: Tracks patient visit trajectories (`Improving`, `Stable`, `Declining`, `Rapidly Declining`) to catch downward trends across visits.
* **Deterministic Clinical Safety Layer**: Hardcoded WHO 2024 guidelines wrap the AI — deterministic safety rules can only *escalate* urgency, never downgrade below WHO-mandated clinical actions.
* **Explainable & Uncertainty-Aware AI**: Outputs plain-language contributing signals ("Why this result?"), calibrated confidence scores, and region-of-interest (ROI) overlays.
* **100% Offline-First**: Works on budget Android devices without active internet connection, with local encrypted storage and automatic background sync.
* **Human-Centered Real-World UI**: Designed with clean, human-centered healthcare interfaces (Deep Emerald Teal & Forest Green design system) with zero robotic AI clutter.

---

## 🩺 Medical AI Disclaimer

> **Notice:** This screening result is an AI-generated risk assessment and NOT a clinical diagnosis. Please consult a qualified doctor or healthcare professional for full medical evaluation and confirmatory laboratory testing.

---

## 🔬 Scientific Foundations & WHO 2024 Thresholds

PRAHARI strictly enforces the revised **WHO 2024 Hemoglobin Thresholds** and **Child Growth Standards**:

| Population Group | Anemia Threshold (Hb) | Guideline Source |
| :--- | :--- | :--- |
| **Children 6–23 months** | Revised Cutoff | WHO 2024 Revised Guidelines (PubMed 38910369) |
| **Children 24–59 months / 5–11 yrs** | `< 11.0 g/dL` | Standard WHO Pediatric Cutoffs |
| **Pregnant Women (1st & 3rd Trimester)** | `< 11.0 g/dL` | Standard ANC Guidelines |
| **Pregnant Women (2nd Trimester)** | `< 10.5 g/dL` | Confirmed in WHO 2024 Revision |

---

## 🚀 Quick Start (Running Locally)

### Prerequisites
* Node.js v18.0+ 
* npm v9.0+

### 1. Clone the Repository
```bash
git clone https://github.com/Viraj-Akili/anemia-detection.git
cd anemia-detection
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Start Development Server
```bash
npm run dev
```
Open **[http://localhost:3000/](http://localhost:3000/)** in your web browser.

---

## 💻 1-Click Launch on Windows

For instant launching without terminal commands, simply double-click:
```
start_prahari.bat
```

---

## 🏗️ Production Build

To test or generate the minified production distribution bundle:
```bash
npm run build
```

The output bundle will be generated in `dist/`.

---

## 📄 Regulatory & SaMD Compliance
Under India's **CDSCO Medical Device Software guidance (draft Oct 2025, formalizing 2025–26)**, software performing disease screening is classified as **Software as a Medical Device (SaMD)**. PRAHARI is engineered specifically as a non-invasive decision support and pre-screening tool, simplifying future CDSCO Class A/B regulatory clearance.

---

## 📜 License & Acknowledgments
Built for the **HTAD-06 Hackathon**. Designed for frontline healthcare workers across Anganwadi Centres and Primary Health Centres (PHC) in India.
