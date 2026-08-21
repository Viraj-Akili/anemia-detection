# PRAHARI Nutrition Chatbot Anthropometric Integration Report

## Executive Summary
This document provides the clinical, mathematical, and architectural documentation for **STEP 10: Nutrition Chatbot Anthropometric Integration** within Project PRAHARI. 

Anthropometric indicators—**Height in centimeters (Required)**, **Weight in kilograms (Required)**, **Body Mass Index (BMI, auto-calculated)**, and **Mid-Upper Arm Circumference (MUAC, Optional)**—are integrated into the frontend interactive chatbot and backend clinical risk engines in a scientifically defensible, age-aware manner that adheres to World Health Organization (WHO) Child Growth Standards and Adult Reference Methodology.

---

## 1. Mathematical Formulas & Core Calculations

### 1.1 Body Mass Index (BMI)
$$\text{BMI} = \frac{\text{Weight (kg)}}{(\text{Height (m)})^2} = \frac{\text{Weight (kg)}}{\left(\frac{\text{Height (cm)}}{100}\right)^2}$$

- **Precision**: Calculated and rendered to **1 decimal place** (e.g., $21.5\text{ kg/m}^2$).
- **Guards**: Division by zero and non-positive measurements are strictly prevented at both the TypeScript and Python layers.

### 1.2 MUAC Normalization
$$\text{MUAC (mm)} = \begin{cases} \text{MUAC}_{\text{cm}} \times 10 & \text{if unit is cm} \\ \text{MUAC}_{\text{mm}} & \text{if unit is mm} \end{cases}$$

- Accepts inputs in centimeters ($\text{cm}$) or millimeters ($\text{mm}$) and normalizes internally to millimeters ($\text{mm}$) for physiological evaluation.

---

## 2. Age-Aware Anthropometric Interpretation

### 2.1 Adult BMI Interpretation ($\ge 19$ Years)
Evaluated against standard WHO international adult cutoffs:
| BMI Range ($\text{kg/m}^2$) | WHO Nutritional Classification | Clinical Risk Level |
| :--- | :--- | :--- |
| $< 16.0$ | Severe Underweight (Severe Chronic Energy Deficiency) | `CRITICAL` |
| $16.0 - 16.9$ | Moderate Underweight | `UNHEALTHY` |
| $17.0 - 18.4$ | Mild Underweight / Low BMI | `BORDERLINE` |
| $18.5 - 24.9$ | Normal Weight Range | `HEALTHY` |
| $25.0 - 29.9$ | Overweight | `BORDERLINE` |
| $\ge 30.0$ | Obesity | `UNHEALTHY` |

### 2.2 Child & Adolescent BMI-for-Age ($5\text{--}19$ Years / $60\text{--}228$ Months)
Based on the **WHO 2007 Growth Reference for School-Aged Children and Adolescents**:
- **Distinction**: Raw BMI value ($\text{kg/m}^2$) is clearly distinguished from the BMI-for-age distribution.
- **Severe Thinness**: $<-3\text{ SD}$ below age/sex reference median ($\to \text{CRITICAL}$).
- **Thinness / Underweight**: $<-2\text{ SD}$ below age/sex reference median ($\to \text{UNHEALTHY}$).
- **Normal Range**: $-2\text{ SD}$ to $+1\text{ SD}$ ($\to \text{HEALTHY}$).
- **Overweight**: $>+1\text{ SD}$ ($\to \text{BORDERLINE}$).
- **Obesity**: $>+2\text{ SD}$ ($\to \text{UNHEALTHY}$).

### 2.3 Preschool Children Under 5 Years ($6\text{--}59$ Months / $<60$ Months)
- According to **WHO Child Growth Standards (2006)**, adult BMI thresholds do NOT apply to infants and young children.
- Weight-for-Height z-score (WHZ) and MUAC are prioritized as the primary acute malnutrition indices. The application explicitly notes that preschool BMI is evaluated alongside WHZ/MUAC.

---

## 3. Mid-Upper Arm Circumference (MUAC) Methodology

### 3.1 Children $6\text{--}59$ Months (WHO/UNICEF Standard)
| MUAC Measurement | WHO Standard Cutoff | Clinical Classification | Triage Escalation |
| :--- | :--- | :--- | :--- |
| $< 115\text{ mm}$ ($< 11.5\text{ cm}$) | Severe Acute Malnutrition (SAM) | Severe Acute Wasting | `CRITICAL` (Immediate Referral) |
| $115\text{ mm} \le \text{MUAC} < 125\text{ mm}$ ($11.5\text{--}12.4\text{ cm}$) | Moderate Acute Malnutrition (MAM) | Moderate Acute Wasting | `UNHEALTHY` (Targeted Nutrition) |
| $\ge 125\text{ mm}$ ($\ge 12.5\text{ cm}$) | Normal Reference Range | Adequate Arm Circumference | `HEALTHY` (No acute wasting) |

### 3.2 Adults ($\ge 19$ Years)
- **WHO / FANTA Undernutrition Indicator**: $\text{MUAC} < 230\text{ mm}$ ($< 23.0\text{ cm}$) correlates with chronic energy deficiency ($\text{BMI} < 18.5\text{ kg/m}^2$) and is categorized as `BORDERLINE` vulnerability.
- $\text{MUAC} \ge 230\text{ mm}$ is classified as `HEALTHY`.

### 3.3 Adolescents ($5\text{--}18$ Years) & Non-Applicable Age Cohorts
- Displayed and recorded informatively without fabricating non-standard WHO cutoffs.

### 3.4 Missing Data Handling (Optional MUAC)
- When MUAC is omitted, the system logs: *"MUAC not provided — MUAC-based assessment was not applied."*
- **Zero Penalty**: Omission of optional MUAC does NOT decrease the patient's nutrition score or penalize the beneficiary.

---

## 4. Scientifically Defensible Scoring & Deduplication

### 4.1 Bounded Scoring Architecture
$$\text{Final Nutrition Score} = \max\Big(0, \min\big(100, \text{Base Questionnaire Score} + \text{Anthropometric Component}\big)\Big)$$

- **Base Questionnaire Score**: $0\text{ to }100$ points based on appetite ($25$), physical signs ($25$), infection/illness ($20$), dietary diversity ($20$), and prophylaxis ($10$).
- **Anthropometric Risk Component**:
  - `HEALTHY`: $0\text{ points}$
  - `BORDERLINE`: $-10\text{ points}$ (Bounded)
  - `UNHEALTHY`: $-25\text{ points}$ (Bounded)
  - `CRITICAL`: $-40\text{ points}$ / Priority Escalation

### 4.2 Overlap & Double-Counting Mitigation
If both BMI and MUAC indicate deficits (e.g. an adult with $\text{BMI} < 18.5$ and $\text{MUAC} < 230\text{ mm}$, or a child with low BMI and $\text{MUAC} < 115\text{ mm}$):
$$\text{Anthropometric Component} = \min\big(\text{Penalty}(\text{BMI}), \text{Penalty}(\text{MUAC})\big)$$
*(Note: Penalties are negative integers; taking the minimum selects the worst-case single deficit).*
- **Result**: Risk is not artificially doubled (e.g. $-25 + -25 = -50$ is prevented).
- **Safety**: Entering an optional normal MUAC never degrades a score, and entering a secondary deficit does not cause runaway score inflation.

---

## 5. Input Validation Rules

| Input Parameter | Minimum Valid Bound | Maximum Valid Bound | Validation Enforcement |
| :--- | :--- | :--- | :--- |
| **Height** | $30.0\text{ cm}$ | $250.0\text{ cm}$ | Strictly $>0$, finite float, rejects negatives/zeros |
| **Weight** | $1.0\text{ kg}$ | $250.0\text{ kg}$ | Strictly $>0$, finite float, rejects negatives/zeros |
| **MUAC** | $50.0\text{ mm}$ ($5.0\text{ cm}$) | $500.0\text{ mm}$ ($50.0\text{ cm}$) | Strictly $>0$, finite float, rejects negatives/zeros |
| **Age** | $0.5\text{ years}$ ($6\text{ months}$) | $110.0\text{ years}$ | Bounded by pediatric and adult demographic ranges |

---

## 6. Verification & Automated Test Results

### 6.1 Test Suite Breakdown (`tests/test_anthropometry_nutrition.py`)
| Test Case | Description | Result |
| :--- | :--- | :--- |
| **Test 1** | Valid height + weight yields mathematically exact BMI ($175\text{ cm}, 70\text{ kg} \to 22.9$) | **PASSED** |
| **Test 2** | Zero height ($0\text{ cm}$) rejected with 422 / validation exception | **PASSED** |
| **Test 3** | Negative height ($-160\text{ cm}$) rejected | **PASSED** |
| **Test 4** | Zero weight ($0\text{ kg}$) rejected | **PASSED** |
| **Test 5** | Negative weight ($-55\text{ kg}$) rejected | **PASSED** |
| **Test 6** | Adult BMI classification across all 4 WHO tiers ($<18.5, 18.5-24.9, 25-29.9, \ge 30$) | **PASSED** |
| **Test 7** | Child BMI uses age-aware WHO 2007 logic ($7\text{y with BMI } 15.0\text{ is normal}$) | **PASSED** |
| **Test 8** | MUAC omitted causes zero penalty and records `"not_provided"` | **PASSED** |
| **Test 9** | MUAC unit conversion ($13.5\text{ cm} \to 135.0\text{ mm}$) | **PASSED** |
| **Test 10** | Child $6\text{--}59\text{m MUAC } < 115\text{ mm}$ triggers SAM / Critical risk | **PASSED** |
| **Test 11** | Child $6\text{--}59\text{m MUAC } 115\text{--}124\text{ mm}$ triggers MAM / Unhealthy | **PASSED** |
| **Test 12** | Child $6\text{--}59\text{m MUAC } \ge 125\text{ mm}$ classified as Normal | **PASSED** |
| **Test 13** | Adult MUAC ($180\text{ mm}$) uses adult $<230\text{ mm}$ threshold, not pediatric SAM | **PASSED** |
| **Test 14** | Overlap deduplication verified (low BMI + low MUAC bounds penalty at $-40$) | **PASSED** |
| **Test 15** | Endpoint `POST /api/nutrition/evaluate-anthropometry` functions accurately | **PASSED** |
| **Test 16** | End-to-end multimodal screening pipeline (`evaluate-multimodal`) unchanged & verified | **PASSED** |
| **Test 17** | Missing anthropometric parameters handled gracefully | **PASSED** |
| **Test 18** | Frontend production build passes (`npm run build` in $795\text{ms}$) | **PASSED** |
| **Test 19** | Full workspace test suite passes ($57 / 57\text{ tests passed}$) | **PASSED** |

---

## 7. Clinical Safety Scope & Limitations

1. **Screening Support Only**: PRAHARI is designed as a point-of-care screening aid for risk stratification in community settings. It does not issue definitive medical diagnoses.
2. **No Anemia Diagnosis from Anthropometry**: The system strictly refrains from claiming that BMI or MUAC diagnoses anemia. Anemia screening is reserved for validated optical conjunctival ML and PPG hemoglobin regression.
3. **No Pharmacological Prescriptions**: The chatbot does not prescribe medication, therapeutic dosages, or medical drugs.
4. **Pediatric Scope**: For children $< 6\text{ months}$, MUAC cutoffs are not applied as per WHO guidelines. For children $5\text{--}19\text{ years}$, BMI-for-age is the primary standardized metric.

---

## 8. Primary Medical & Scientific References
1. **World Health Organization (2006)**. *WHO Child Growth Standards: Length/height-for-age, weight-for-age, weight-for-length, weight-for-height and body mass index-for-age*. Geneva: World Health Organization.
2. **World Health Organization (2007)**. *Growth reference data for 5-19 years*. Geneva: World Health Organization.
3. **WHO/UNICEF (2009/2013)**. *WHO child growth standards and the identification of severe acute malnutrition in infants and children: A Joint Statement*. Geneva / New York.
4. **Food and Nutrition Technical Assistance (FANTA) Project (2016)**. *Anthropometric Indicators Measurement Guide*. Washington, DC: FHI 360.
