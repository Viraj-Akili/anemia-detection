/**
 * anemia-detection-main/src/services/anthropometryService.ts
 *
 * Age-Aware Anthropometry and Nutrition Calculation Engine for PRAHARI Frontend.
 * Implements WHO Reference Standards, bounded scoring contributions, and overlap deduplication.
 */

export interface AnthropometryInputs {
  heightCm: number;
  weightKg: number;
  ageYears: number;
  gender: 'Male' | 'Female' | 'MALE' | 'FEMALE';
  muacValue?: number;
  muacUnit?: 'mm' | 'cm';
}

export interface AnthropometryEvaluation {
  heightCm: number;
  weightKg: number;
  bmi: number;
  bmiCategory: string;
  bmiInterpretation: string;
  ageGroupClassification: string;
  muacMm?: number;
  muacCm?: number;
  muacCategory: 'severe' | 'moderate' | 'normal' | 'informative' | 'not_provided';
  muacInterpretation: string;
  riskLevel: 'HEALTHY' | 'BORDERLINE' | 'UNHEALTHY' | 'CRITICAL';
  scoreAdjustment: number;
  deduplicationApplied: boolean;
  clinicalExplanation: string;
  overlapNote: string;
}

export function calculateBMI(heightCm: number, weightKg: number): number {
  if (!heightCm || heightCm <= 0) {
    throw new Error('Height must be greater than 0 cm.');
  }
  if (!weightKg || weightKg <= 0) {
    throw new Error('Weight must be greater than 0 kg.');
  }
  if (heightCm < 30 || heightCm > 250) {
    throw new Error(`Height ${heightCm} cm is outside realistic range [30, 250] cm.`);
  }
  if (weightKg < 1 || weightKg > 250) {
    throw new Error(`Weight ${weightKg} kg is outside realistic range [1, 250] kg.`);
  }

  const heightM = heightCm / 100.0;
  const rawBMI = weightKg / (heightM * heightM);
  return Math.round(rawBMI * 10) / 10;
}

export function normalizeMUAC(value?: number, unit: 'mm' | 'cm' = 'mm'): number | undefined {
  if (value == null || isNaN(value) || value <= 0) {
    return undefined;
  }
  const valMM = unit === 'cm' || value < 50 ? value * 10 : value;
  if (valMM < 50 || valMM > 500) {
    throw new Error(`MUAC ${valMM} mm is outside physiological range [50, 500] mm.`);
  }
  return Math.round(valMM * 10) / 10;
}

export function interpretBMI(
  bmi: number,
  ageYears: number
): {
  category: string;
  interpretation: string;
  ageGroup: string;
  riskLevel: 'HEALTHY' | 'BORDERLINE' | 'UNHEALTHY' | 'CRITICAL';
} {
  if (ageYears >= 19) {
    const ageGroup = 'Adult (≥19 years)';
    if (bmi < 16.0) {
      return {
        category: 'Severe Underweight',
        interpretation: `BMI ${bmi.toFixed(1)} kg/m² — Severe chronic energy deficit (WHO Adult <16.0)`,
        ageGroup,
        riskLevel: 'CRITICAL',
      };
    }
    if (bmi < 17.0) {
      return {
        category: 'Moderate Underweight',
        interpretation: `BMI ${bmi.toFixed(1)} kg/m² — Moderate chronic energy deficit (WHO Adult 16.0–16.9)`,
        ageGroup,
        riskLevel: 'UNHEALTHY',
      };
    }
    if (bmi < 18.5) {
      return {
        category: 'Mild Underweight / Low BMI',
        interpretation: `BMI ${bmi.toFixed(1)} kg/m² — Low adult body mass (WHO Adult 17.0–18.4)`,
        ageGroup,
        riskLevel: 'BORDERLINE',
      };
    }
    if (bmi <= 24.9) {
      return {
        category: 'Normal Weight',
        interpretation: `BMI ${bmi.toFixed(1)} kg/m² — Normal healthy adult range (WHO 18.5–24.9)`,
        ageGroup,
        riskLevel: 'HEALTHY',
      };
    }
    if (bmi <= 29.9) {
      return {
        category: 'Overweight',
        interpretation: `BMI ${bmi.toFixed(1)} kg/m² — Overweight range (WHO Adult 25.0–29.9)`,
        ageGroup,
        riskLevel: 'BORDERLINE',
      };
    }
    return {
      category: 'Obesity',
      interpretation: `BMI ${bmi.toFixed(1)} kg/m² — Obesity range (WHO Adult ≥30.0)`,
      ageGroup,
      riskLevel: 'UNHEALTHY',
    };
  }

  if (ageYears >= 5) {
    const ageGroup = 'Child / Adolescent (5–19 years)';
    // WHO 2007 Reference for 5-19 years median curve interpolation
    const medianBMI = 15.0 + (ageYears - 5.0) * (21.5 - 15.0) / 14.0;
    const thinCutoff = medianBMI - 2.5;
    const severeThinCutoff = medianBMI - 3.8;
    const overCutoff = medianBMI + 3.0;

    if (bmi < severeThinCutoff) {
      return {
        category: 'Severe Thinness',
        interpretation: `BMI ${bmi.toFixed(1)} kg/m² — Severe Thinness for age (WHO 2007 < -3 SD range)`,
        ageGroup,
        riskLevel: 'CRITICAL',
      };
    }
    if (bmi < thinCutoff) {
      return {
        category: 'Thinness / Underweight',
        interpretation: `BMI ${bmi.toFixed(1)} kg/m² — Thinness for age (WHO 2007 < -2 SD range)`,
        ageGroup,
        riskLevel: 'UNHEALTHY',
      };
    }
    if (bmi > overCutoff + 3.0) {
      return {
        category: 'Obese for Age',
        interpretation: `BMI ${bmi.toFixed(1)} kg/m² — Obese for age (WHO 2007 > +2 SD range)`,
        ageGroup,
        riskLevel: 'UNHEALTHY',
      };
    }
    if (bmi > overCutoff) {
      return {
        category: 'Overweight for Age',
        interpretation: `BMI ${bmi.toFixed(1)} kg/m² — Overweight for age (WHO 2007 > +1 SD range)`,
        ageGroup,
        riskLevel: 'BORDERLINE',
      };
    }
    return {
      category: 'Normal BMI-for-Age',
      interpretation: `BMI ${bmi.toFixed(1)} kg/m² — Healthy BMI-for-age (within -2 SD to +1 SD WHO reference)`,
      ageGroup,
      riskLevel: 'HEALTHY',
    };
  }

  // Children under 5 years (<60 months)
  const ageGroup = 'Child (<5 years / 6–59 months)';
  if (bmi < 13.0) {
    return {
      category: 'Low Body Mass Index',
      interpretation: `BMI ${bmi.toFixed(1)} kg/m². (WHO Child Growth Standards prioritize Weight-for-Height and MUAC over adult BMI).`,
      ageGroup,
      riskLevel: 'UNHEALTHY',
    };
  }
  return {
    category: 'Preschool Growth Tracking',
    interpretation: `BMI ${bmi.toFixed(1)} kg/m². (Weight-for-Height WHZ and MUAC are standard for acute preschool growth evaluation).`,
    ageGroup,
    riskLevel: 'HEALTHY',
  };
}

export function interpretMUAC(
  muacMm: number | undefined,
  ageYears: number
): {
  category: 'severe' | 'moderate' | 'normal' | 'informative' | 'not_provided';
  interpretation: string;
  riskLevel: 'HEALTHY' | 'BORDERLINE' | 'UNHEALTHY' | 'CRITICAL';
} {
  if (muacMm == null) {
    return {
      category: 'not_provided',
      interpretation: 'MUAC not provided — MUAC-based assessment was not applied.',
      riskLevel: 'HEALTHY',
    };
  }

  const ageMonths = Math.round(ageYears * 12);

  if (ageMonths >= 6 && ageMonths < 60) {
    if (muacMm < 115) {
      return {
        category: 'severe',
        interpretation: `MUAC ${muacMm} mm (${(muacMm / 10).toFixed(1)} cm) — Severe Acute Malnutrition (SAM) criterion for children 6–59 months (<115 mm).`,
        riskLevel: 'CRITICAL',
      };
    }
    if (muacMm < 125) {
      return {
        category: 'moderate',
        interpretation: `MUAC ${muacMm} mm (${(muacMm / 10).toFixed(1)} cm) — Moderate Acute Malnutrition (MAM) range for children 6–59 months (115–124 mm).`,
        riskLevel: 'UNHEALTHY',
      };
    }
    return {
      category: 'normal',
      interpretation: `MUAC ${muacMm} mm (${(muacMm / 10).toFixed(1)} cm) — Within normal reference range (≥125 mm) for children 6–59 months.`,
      riskLevel: 'HEALTHY',
    };
  }

  if (ageYears >= 19) {
    if (muacMm < 230) {
      return {
        category: 'moderate',
        interpretation: `MUAC ${muacMm} mm (${(muacMm / 10).toFixed(1)} cm) — Low adult arm circumference (<230 mm, WHO/FANTA undernutrition indicator).`,
        riskLevel: 'BORDERLINE',
      };
    }
    return {
      category: 'normal',
      interpretation: `MUAC ${muacMm} mm (${(muacMm / 10).toFixed(1)} cm) — Adequate adult arm circumference (≥230 mm).`,
      riskLevel: 'HEALTHY',
    };
  }

  // 5 to <19 years
  return {
    category: 'informative',
    interpretation: `MUAC ${muacMm} mm (${(muacMm / 10).toFixed(1)} cm) recorded informatively. (WHO SAM/MAM cutoffs apply strictly to 6–59 months; BMI-for-age is primary for 5–19 years).`,
    riskLevel: 'HEALTHY',
  };
}

export function evaluateAnthropometrics(inputs: AnthropometryInputs): AnthropometryEvaluation {
  const bmi = calculateBMI(inputs.heightCm, inputs.weightKg);
  const muacMm = normalizeMUAC(inputs.muacValue, inputs.muacUnit);
  const muacCm = muacMm != null ? Math.round(muacMm / 10.0 * 10) / 10 : undefined;

  const bmiEval = interpretBMI(bmi, inputs.ageYears);
  const muacEval = interpretMUAC(muacMm, inputs.ageYears);

  // Bounded scoring penalty and overlap deduplication
  const penaltyTable = {
    HEALTHY: 0,
    BORDERLINE: -10,
    UNHEALTHY: -25,
    CRITICAL: -40,
  };

  const bmiPenalty = penaltyTable[bmiEval.riskLevel];
  const muacPenalty = penaltyTable[muacEval.riskLevel];

  // Take the worst penalty, avoiding double penalty addition
  const scoreAdjustment = Math.min(bmiPenalty, muacPenalty);
  const deduplicationApplied =
    (bmiEval.riskLevel === 'UNHEALTHY' || bmiEval.riskLevel === 'CRITICAL') &&
    (muacEval.riskLevel === 'UNHEALTHY' || muacEval.riskLevel === 'CRITICAL');

  const rankTable = { HEALTHY: 0, BORDERLINE: 1, UNHEALTHY: 2, CRITICAL: 3 };
  const overallRank = Math.max(rankTable[bmiEval.riskLevel], rankTable[muacEval.riskLevel]);
  const invRank: Record<number, 'HEALTHY' | 'BORDERLINE' | 'UNHEALTHY' | 'CRITICAL'> = {
    0: 'HEALTHY',
    1: 'BORDERLINE',
    2: 'UNHEALTHY',
    3: 'CRITICAL',
  };
  const compositeRisk = invRank[overallRank];

  let clinicalExplanation = '';
  if (compositeRisk === 'CRITICAL') {
    clinicalExplanation = `Critical anthropometric risk identified (${bmiEval.category} / ${muacEval.category}). Immediate clinical evaluation and nutrition referral recommended.`;
  } else if (compositeRisk === 'UNHEALTHY') {
    clinicalExplanation = `Nutritional concern identified from physical measurements (${bmiEval.category} / ${muacEval.category}). Targeted dietary counseling recommended.`;
  } else if (compositeRisk === 'BORDERLINE') {
    clinicalExplanation = 'Mild anthropometric vulnerability noted. Routine dietary diversification and growth monitoring advised.';
  } else {
    clinicalExplanation = `Body measurements (BMI ${bmi.toFixed(1)} kg/m²) fall within expected healthy reference parameters.`;
  }

  const overlapNote = deduplicationApplied
    ? 'BMI and MUAC were evaluated as complementary indicators. Overlap deduplication was enforced to prevent artificial risk inflation.'
    : 'Individual anthropometric indicators evaluated independently without artificial inflation.';

  return {
    heightCm: inputs.heightCm,
    weightKg: inputs.weightKg,
    bmi,
    bmiCategory: bmiEval.category,
    bmiInterpretation: bmiEval.interpretation,
    ageGroupClassification: bmiEval.ageGroup,
    muacMm,
    muacCm,
    muacCategory: muacEval.category,
    muacInterpretation: muacEval.interpretation,
    riskLevel: compositeRisk,
    scoreAdjustment,
    deduplicationApplied,
    clinicalExplanation,
    overlapNote,
  };
}
