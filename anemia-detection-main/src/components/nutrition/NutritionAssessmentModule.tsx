import React, { useState } from 'react';
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronRight,
  ClipboardList,
  Info,
  Layers,
  RefreshCw,
  Ruler,
  Scale,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  User,
} from 'lucide-react';
import {
  AnthropometryEvaluation,
  calculateBMI,
  evaluateAnthropometrics,
  interpretBMI,
  interpretMUAC,
  normalizeMUAC,
} from '../../services/anthropometryService';

export interface QuestionOption {
  label: string;
  subtext?: string;
  points: number;
  healthLevel: 'HEALTHY' | 'BORDERLINE' | 'UNHEALTHY' | 'CRITICAL';
}

export interface NutritionQuestion {
  key: string;
  title: string;
  prompt: string;
  options: QuestionOption[];
}

export interface FactorBreakdown {
  category: string;
  value: string;
  statusLabel: 'Within expected range' | 'Borderline' | 'Concerning' | 'Critical';
  status: 'HEALTHY' | 'BORDERLINE' | 'UNHEALTHY' | 'CRITICAL';
  explanation: string;
}

export interface ClinicalActionItem {
  step: string;
  title: string;
  description: string;
  isUrgent?: boolean;
}

export interface NutritionAssessmentReport {
  overallRisk: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
  ratingLabel: string;
  badgeColor: string;
  clinicalImpression: string;
  physiologicalImpact: string;
  anthropometry: AnthropometryEvaluation;
  factors: FactorBreakdown[];
  actionItems: ClinicalActionItem[];
  protocolName: string;
}

interface NutritionAssessmentModuleProps {
  onProceedToOpticalScan?: () => void;
  initialAgeYears?: number;
  initialGender?: 'Male' | 'Female' | 'MALE' | 'FEMALE';
  initialCategory?: 'adult' | 'child' | 'pregnant' | 'elderly';
  initialHeightCm?: number;
  initialWeightKg?: number;
  initialMuacCm?: number;
}

const QUESTIONS_TREE: NutritionQuestion[] = [
  {
    key: 'appetite',
    title: 'Appetite & Intake',
    prompt: 'How has the beneficiary’s appetite and solid food intake been over the past 7 days?',
    options: [
      {
        label: 'Normal & Active Appetite',
        subtext: 'Consistently consuming full meals with age-appropriate hunger cues',
        points: 25,
        healthLevel: 'HEALTHY',
      },
      {
        label: 'Reduced Food Intake',
        subtext: 'Eating approximately half of usual meal volume, occasional food refusal',
        points: 10,
        healthLevel: 'BORDERLINE',
      },
      {
        label: 'Poor / Refusing Solids & Lethargic',
        subtext: 'Severe lack of appetite, refusing feeds, persistent lethargy',
        points: 0,
        healthLevel: 'CRITICAL',
      },
    ],
  },
  {
    key: 'physical_signs',
    title: 'Physical & Muscle Signs',
    prompt:
      'Are there observable clinical signs such as bilateral pitting edema (swollen feet/legs), visible severe wasting, or marked muscle loss?',
    options: [
      {
        label: 'No Visible Swelling or Severe Wasting',
        subtext: 'Normal physical posture, preserved subcutaneous fat, and healthy muscle tone',
        points: 25,
        healthLevel: 'HEALTHY',
      },
      {
        label: 'Mild Visible Thinness',
        subtext: 'Minor loss of body mass without edema or severe skeletal prominence',
        points: 10,
        healthLevel: 'BORDERLINE',
      },
      {
        label: 'Bilateral Swollen Feet / Legs (Pitting Edema)',
        subtext: 'Fluid retention in both lower extremities leaving an indentation on pressure',
        points: 0,
        healthLevel: 'CRITICAL',
      },
      {
        label: 'Severe Muscle Wasting & Prominent Ribs',
        subtext: 'Marked depletion of subcutaneous adipose tissue and skeletal muscle mass',
        points: 0,
        healthLevel: 'CRITICAL',
      },
    ],
  },
  {
    key: 'illness',
    title: 'Recent Illness & Digestion',
    prompt: 'Has there been persistent diarrhea (>14 days), recurring high fever, or frequent vomiting recently?',
    options: [
      {
        label: 'No Recent Chronic Illness',
        subtext: 'No gastrointestinal infection, fever episodes, or nutrient malabsorption',
        points: 20,
        healthLevel: 'HEALTHY',
      },
      {
        label: 'Brief Mild Cold or Low Fever',
        subtext: 'Short-term minor seasonal symptoms, currently resolving without dehydration',
        points: 15,
        healthLevel: 'BORDERLINE',
      },
      {
        label: 'Persistent Diarrhea (>14 Days)',
        subtext: 'Chronic fluid and nutrient malabsorption impairing recovery and linear growth',
        points: 0,
        healthLevel: 'UNHEALTHY',
      },
      {
        label: 'Frequent Vomiting & Dehydration',
        subtext: 'Inability to retain liquids or solid nutrition; dehydration risk',
        points: 0,
        healthLevel: 'UNHEALTHY',
      },
    ],
  },
  {
    key: 'dietary_diversity',
    title: '24-Hour Dietary Diversity',
    prompt:
      'In the last 24 hours, how many distinct food groups were consumed? (e.g., grains/staples, legumes/pulses, dairy, eggs/meat, dark green leafy vegetables, Vitamin A fruits)',
    options: [
      {
        label: 'Diverse Diet (4 or More Food Groups)',
        subtext: 'Adequate intake of bioavailable proteins, micronutrients, vitamins, and calories',
        points: 20,
        healthLevel: 'HEALTHY',
      },
      {
        label: 'Limited Diet (2 to 3 Food Groups)',
        subtext: 'Missing key animal/plant proteins or protective fresh vegetables and fruits',
        points: 10,
        healthLevel: 'BORDERLINE',
      },
      {
        label: 'Monotonous Diet (Only 1 Staple / Plain Rice or Gruel)',
        subtext: 'Severe macronutrient and micronutrient imbalance with low nutrient density',
        points: 0,
        healthLevel: 'UNHEALTHY',
      },
    ],
  },
  {
    key: 'supplements',
    title: 'Preventive / Prophylaxis Indicators',
    prompt:
      'Are routine bi-annual deworming (Albendazole) and Vitamin A / Iron-Folic Acid prophylaxis up to date?',
    options: [
      {
        label: 'Yes, Fully Up to Date',
        subtext: 'Received scheduled public health prophylaxis within the past 6 months',
        points: 10,
        healthLevel: 'HEALTHY',
      },
      {
        label: 'Not Sure / Record Unverified',
        subtext: 'Prophylaxis documentation not currently available at screening',
        points: 5,
        healthLevel: 'BORDERLINE',
      },
      {
        label: 'No, Overdue or Never Received',
        subtext: 'Elevated risk of parasitic nutrient loss and micronutrient deficiency',
        points: 0,
        healthLevel: 'UNHEALTHY',
      },
    ],
  },
];

export const NutritionAssessmentModule: React.FC<NutritionAssessmentModuleProps> = ({
  onProceedToOpticalScan,
  initialAgeYears = 28,
  initialGender = 'Female',
  initialCategory = 'adult',
  initialHeightCm,
  initialWeightKg,
  initialMuacCm,
}) => {
  // Workflow Step: 'inputs' | 'evaluating' | 'summary'
  const [assessmentStep, setAssessmentStep] = useState<'inputs' | 'evaluating' | 'summary'>('inputs');

  // Section 1: Patient Profile
  const [ageYears, setAgeYears] = useState<number>(initialAgeYears);
  const [gender, setGender] = useState<'Male' | 'Female'>(
    initialGender === 'Male' || initialGender === 'MALE' ? 'Male' : 'Female'
  );
  const [category, setCategory] = useState<'adult' | 'child' | 'pregnant' | 'elderly'>(initialCategory);
  const [trimester, setTrimester] = useState<number>(2);

  // Section 2: Body Measurements
  const [heightCm, setHeightCm] = useState<string>(
    initialHeightCm ? initialHeightCm.toString() : initialCategory === 'child' ? '95.0' : '160.0'
  );
  const [weightKg, setWeightKg] = useState<string>(
    initialWeightKg ? initialWeightKg.toString() : initialCategory === 'child' ? '14.0' : '55.0'
  );
  const [muacInput, setMuacInput] = useState<string>(
    initialMuacCm ? (initialMuacCm * 10).toString() : initialCategory === 'child' ? '135' : ''
  );
  const [muacUnit, setMuacUnit] = useState<'mm' | 'cm'>('mm');
  const [inputError, setInputError] = useState<string | null>(null);

  // Section 3: Clinical Questionnaire Answers
  const [answers, setAnswers] = useState<Record<string, QuestionOption>>({
    appetite: QUESTIONS_TREE[0].options[0],
    physical_signs: QUESTIONS_TREE[1].options[0],
    illness: QUESTIONS_TREE[2].options[0],
    dietary_diversity: QUESTIONS_TREE[3].options[0],
    supplements: QUESTIONS_TREE[4].options[0],
  });

  // Final Generated Report
  const [report, setReport] = useState<NutritionAssessmentReport | null>(null);

  // Live BMI Calculation
  const parsedH = parseFloat(heightCm) || 0;
  const parsedW = parseFloat(weightKg) || 0;
  let liveBMI: number | null = null;
  let liveBMIEval: ReturnType<typeof interpretBMI> | null = null;

  if (parsedH > 0 && parsedW > 0) {
    try {
      liveBMI = calculateBMI(parsedH, parsedW);
      liveBMIEval = interpretBMI(liveBMI, ageYears);
    } catch {
      liveBMI = null;
      liveBMIEval = null;
    }
  }

  // Live MUAC Normalization
  const parsedMUAC = parseFloat(muacInput) || undefined;
  let normalizedMUAC: number | undefined = undefined;
  let liveMUACEval: ReturnType<typeof interpretMUAC> | null = null;

  if (parsedMUAC != null && !isNaN(parsedMUAC)) {
    try {
      normalizedMUAC = normalizeMUAC(parsedMUAC, muacUnit);
      liveMUACEval = interpretMUAC(normalizedMUAC, ageYears);
    } catch {
      normalizedMUAC = undefined;
      liveMUACEval = null;
    }
  } else {
    liveMUACEval = interpretMUAC(undefined, ageYears);
  }

  const handleCohortSelect = (newCat: 'adult' | 'child' | 'pregnant' | 'elderly') => {
    setCategory(newCat);
    if (newCat === 'child') {
      setAgeYears(3);
      setHeightCm('95.0');
      setWeightKg('14.0');
      setMuacInput('135');
    } else if (newCat === 'pregnant') {
      setAgeYears(26);
      setGender('Female');
      setHeightCm('158.0');
      setWeightKg('58.0');
      setMuacInput('');
    } else if (newCat === 'elderly') {
      setAgeYears(68);
      setHeightCm('160.0');
      setWeightKg('54.0');
      setMuacInput('');
    } else {
      setAgeYears(28);
      setHeightCm('160.0');
      setWeightKg('55.0');
      setMuacInput('');
    }
  };

  const handleRunEvaluation = async () => {
    setInputError(null);
    const h = parseFloat(heightCm);
    const w = parseFloat(weightKg);
    const m = muacInput.trim() ? parseFloat(muacInput) : undefined;

    if (!h || h <= 0) {
      setInputError('Height in centimeters is required and must be greater than 0.');
      return;
    }
    if (h < 30 || h > 250) {
      setInputError(`Height ${h} cm is outside realistic physiological range [30, 250] cm.`);
      return;
    }
    if (!w || w <= 0) {
      setInputError('Weight in kilograms is required and must be greater than 0.');
      return;
    }
    if (w < 1 || w > 250) {
      setInputError(`Weight ${w} kg is outside realistic physiological range [1, 250] kg.`);
      return;
    }

    let anthroResult: AnthropometryEvaluation;
    try {
      anthroResult = evaluateAnthropometrics({
        heightCm: h,
        weightKg: w,
        ageYears,
        gender,
        muacValue: m,
        muacUnit,
      });
    } catch (err: any) {
      setInputError(err.message || 'Invalid anthropometric measurements.');
      return;
    }

    setAssessmentStep('evaluating');

    // Simulate clean clinical scoring compilation
    await new Promise((resolve) => setTimeout(resolve, 350));

    const appetiteOpt = answers['appetite'];
    const physicalOpt = answers['physical_signs'];
    const illnessOpt = answers['illness'];
    const dietOpt = answers['dietary_diversity'];
    const suppOpt = answers['supplements'];

    // 1. Base questionnaire score (0 - 100)
    const baseScore =
      appetiteOpt.points +
      physicalOpt.points +
      illnessOpt.points +
      dietOpt.points +
      suppOpt.points;

    // 2. Bounded Anthropometric Score Contribution (with overlap deduplication)
    const finalScore = Math.max(0, Math.min(100, baseScore + anthroResult.scoreAdjustment));

    const hasEdema = physicalOpt.label.includes('Pitting Edema');
    const hasSevereWasting = physicalOpt.label.includes('Severe Muscle Wasting');
    const hasSevereAppetiteLoss = appetiteOpt.label.includes('Poor / Refusing');
    const isAnthroCritical = anthroResult.riskLevel === 'CRITICAL';
    const isAnthroUnhealthy = anthroResult.riskLevel === 'UNHEALTHY';

    const getStatusChip = (
      level: QuestionOption['healthLevel']
    ): {
      label: 'Within expected range' | 'Borderline' | 'Concerning' | 'Critical';
      status: 'HEALTHY' | 'BORDERLINE' | 'UNHEALTHY' | 'CRITICAL';
    } => {
      switch (level) {
        case 'HEALTHY':
          return { label: 'Within expected range', status: 'HEALTHY' };
        case 'BORDERLINE':
          return { label: 'Borderline', status: 'BORDERLINE' };
        case 'UNHEALTHY':
          return { label: 'Concerning', status: 'UNHEALTHY' };
        case 'CRITICAL':
          return { label: 'Critical', status: 'CRITICAL' };
      }
    };

    // Assessment Factors breakdown chips
    const factors: FactorBreakdown[] = [
      {
        category: 'Anthropometric Status',
        value: `BMI: ${anthroResult.bmi.toFixed(1)} kg/m²`,
        statusLabel:
          anthroResult.riskLevel === 'CRITICAL'
            ? 'Critical'
            : anthroResult.riskLevel === 'UNHEALTHY'
            ? 'Concerning'
            : anthroResult.riskLevel === 'BORDERLINE'
            ? 'Borderline'
            : 'Within expected range',
        status: anthroResult.riskLevel,
        explanation:
          anthroResult.riskLevel === 'HEALTHY'
            ? 'Body mass index is within standard healthy reference limits.'
            : anthroResult.riskLevel === 'BORDERLINE'
            ? 'Mild underweight or energy vulnerability identified.'
            : 'Nutritional concern identified from physical body mass.',
      },
      {
        category: 'Appetite / Intake',
        value: appetiteOpt.label,
        statusLabel: getStatusChip(appetiteOpt.healthLevel).label,
        status: appetiteOpt.healthLevel,
        explanation:
          appetiteOpt.healthLevel === 'HEALTHY'
            ? 'Active appetite and full meal consumption support metabolic stability.'
            : 'Reduced intake may increase nutritional risk and micronutrient deficits.',
      },
      {
        category: 'Physical Signs',
        value: physicalOpt.label,
        statusLabel: getStatusChip(physicalOpt.healthLevel).label,
        status: physicalOpt.healthLevel,
        explanation: hasEdema
          ? 'Bilateral pitting edema requires immediate clinical evaluation for Kwashiorkor.'
          : hasSevereWasting
          ? 'Marked subcutaneous fat and muscle depletion indicates acute wasting.'
          : 'Preserved muscle tone and absence of bilateral edema.',
      },
      {
        category: 'Recent Illness',
        value: illnessOpt.label,
        statusLabel: getStatusChip(illnessOpt.healthLevel).label,
        status: illnessOpt.healthLevel,
        explanation:
          illnessOpt.healthLevel === 'HEALTHY'
            ? 'No recent chronic gastrointestinal infection or malabsorption episodes.'
            : 'Persistent illness impairs intestinal nutrient absorption and recovery.',
      },
      {
        category: 'Dietary Diversity',
        value: dietOpt.label,
        statusLabel: getStatusChip(dietOpt.healthLevel).label,
        status: dietOpt.healthLevel,
        explanation:
          dietOpt.healthLevel === 'HEALTHY'
            ? 'Consuming 4+ food groups ensures balanced micronutrient and bioavailable iron intake.'
            : 'Low dietary diversity reported → may increase nutritional risk.',
      },
      {
        category: 'Preventive / Prophylaxis',
        value: suppOpt.label,
        statusLabel: getStatusChip(suppOpt.healthLevel).label,
        status: suppOpt.healthLevel,
        explanation:
          suppOpt.healthLevel === 'HEALTHY'
            ? 'Up-to-date deworming and micronutrient prophylaxis protect against parasitic loss.'
            : 'Overdue prophylaxis elevates vulnerability to secondary micronutrient deficits.',
      },
    ];

    if (anthroResult.muacMm != null) {
      factors.splice(1, 0, {
        category: 'MUAC Indicator',
        value: `${anthroResult.muacMm} mm (${(anthroResult.muacMm / 10).toFixed(1)} cm)`,
        statusLabel:
          anthroResult.muacCategory === 'severe'
            ? 'Critical'
            : anthroResult.muacCategory === 'moderate'
            ? 'Concerning'
            : 'Within expected range',
        status:
          anthroResult.muacCategory === 'severe'
            ? 'CRITICAL'
            : anthroResult.muacCategory === 'moderate'
            ? 'UNHEALTHY'
            : 'HEALTHY',
        explanation: anthroResult.muacInterpretation,
      });
    }

    let overallRisk: NutritionAssessmentReport['overallRisk'];
    let ratingLabel: string;
    let badgeColor: string;
    let clinicalImpression: string;
    let physiologicalImpact: string;
    let actionItems: ClinicalActionItem[];
    let protocolName: string;

    if (
      hasEdema ||
      hasSevereWasting ||
      isAnthroCritical ||
      (hasSevereAppetiteLoss && finalScore < 40)
    ) {
      overallRisk = 'CRITICAL';
      ratingLabel = 'CRITICAL — Severe Acute Malnutrition Risk';
      badgeColor = 'bg-red-50 text-red-800 border-red-300';
      clinicalImpression = hasEdema
        ? 'The beneficiary presents with bilateral pitting edema, a definitive clinical indicator of Kwashiorkor requiring urgent inpatient medical triage.'
        : isAnthroCritical && anthroResult.muacCategory === 'severe'
        ? `The beneficiary meets the WHO Severe Acute Malnutrition (SAM) criterion with MUAC ${anthroResult.muacMm} mm (<115 mm for children 6–59 months) alongside clinical risk markers.`
        : 'The assessment identifies severe macronutrient depletion and acute body mass deficit consistent with Severe Acute Malnutrition (SAM).';
      physiologicalImpact =
        'Severe acute macronutrient depletion impairs cellular immunity, cardiac output, and metabolic stability, significantly increasing vulnerability to secondary infection.';
      actionItems = [
        {
          step: '1',
          title: 'Immediate Clinical Referral',
          description:
            'Refer immediately to the nearest Primary Health Centre (PHC) or Nutrition Rehabilitation Centre (NRC) for urgent clinical evaluation.',
          isUrgent: true,
        },
        {
          step: '2',
          title: 'Comprehensive Diagnostic Workup',
          description:
            'Conduct confirmatory laboratory diagnostics (Complete Blood Count, Serum Albumin, Blood Glucose) and screen for underlying systemic infections.',
          isUrgent: true,
        },
        {
          step: '3',
          title: 'Therapeutic Nutrition Protocol',
          description:
            'Initiate therapeutic feeding with Ready-to-Use Therapeutic Food (RUTF) or therapeutic milk formulations under direct medical supervision.',
        },
      ];
      protocolName = 'WHO Severe Acute Malnutrition Emergency Protocol';
    } else if (finalScore < 60 || isAnthroUnhealthy) {
      overallRisk = 'HIGH';
      ratingLabel = 'HIGH — Moderate Acute Malnutrition Risk';
      badgeColor = 'bg-amber-50 text-amber-900 border-amber-300';
      clinicalImpression =
        anthroResult.bmiCategory.includes('Underweight') || anthroResult.muacCategory === 'moderate'
          ? `Anthropometric measurements (${anthroResult.bmiCategory}${anthroResult.muacMm ? `, MUAC ${anthroResult.muacMm} mm` : ''}) combined with dietary/symptom indicators signify Moderate Acute Malnutrition (MAM) with clear caloric and protein deficits.`
          : 'Based on reported reduced meal intake (~50%), limited dietary diversity, or gastrointestinal illness, the individual demonstrates Moderate Malnutrition risk requiring intervention.';
      physiologicalImpact =
        'Inadequate dietary diversity and low body mass impair linear growth velocity, compromise cellular iron stores, and lead to progressive muscle depletion and physical fatigue.';
      actionItems = [
        {
          step: '1',
          title: 'Supplementary Nutrition Enrollment',
          description:
            'Enroll in community supplementary nutrition programs (Take-Home Ration / Energy-Dense Nutritious Foods) to bridge daily caloric and protein deficits.',
        },
        {
          step: '2',
          title: 'Targeted Micronutrient Supplementation',
          description:
            'Provide age-appropriate Iron-Folic Acid supplementation, Zinc support, and ensure bi-annual Albendazole deworming is completed.',
        },
        {
          step: '3',
          title: '14-Day Growth & MUAC Follow-Up',
          description:
            'Schedule a mandatory follow-up within 14 days to re-assess Mid-Upper Arm Circumference (MUAC) and weight gain velocity.',
        },
      ];
      protocolName = 'Community MAM Targeted Intervention Plan';
    } else if (finalScore < 85 || anthroResult.riskLevel === 'BORDERLINE') {
      overallRisk = 'MODERATE';
      ratingLabel = 'MODERATE — Nutritional Vulnerability / Mild Deficit';
      badgeColor = 'bg-amber-50/70 text-amber-800 border-amber-200';
      clinicalImpression =
        'The individual maintains acceptable physical status but demonstrates dietary or body mass vulnerabilities—such as consuming fewer than 4 distinct food groups daily or low-normal BMI.';
      physiologicalImpact =
        'Sub-optimal micronutrient intake can lead to latent iron deficiency and fatigue before severe physical wasting becomes apparent.';
      actionItems = [
        {
          step: '1',
          title: 'Dietary Diversity Counseling',
          description:
            'Incorporate at least 2 additional food groups daily—specifically iron-rich green leafy vegetables, pulses/lentils, eggs, or dairy.',
        },
        {
          step: '2',
          title: 'Routine Prophylactic Dosing',
          description:
            'Ensure routine bi-annual Albendazole deworming and prophylactic Vitamin A drops are up to date.',
        },
        {
          step: '3',
          title: 'Periodic Point-of-Care Screening',
          description:
            'Perform a non-invasive optical conjunctiva scan to track hemoglobin levels and prevent progression to clinical anemia.',
        },
      ];
      protocolName = 'Community Preventive Nutrition Counseling';
    } else {
      overallRisk = 'LOW';
      ratingLabel = 'LOW — Optimal Nutritional Health';
      badgeColor = 'bg-emerald-50 text-emerald-800 border-emerald-300';
      clinicalImpression =
        'The individual exhibits an optimal nutritional profile characterized by healthy anthropometrics (BMI within reference range), diverse dietary intake (4+ food groups), and zero physical signs of wasting or edema.';
      physiologicalImpact =
        'Adequate protein, caloric, and micronutrient intake supports healthy tissue development, robust immune resistance, and normal metabolic stamina.';
      actionItems = [
        {
          step: '1',
          title: 'Maintain Balanced Diet',
          description:
            'Continue daily consumption of diverse whole foods, legumes, seasonal vegetables, and clean potable water.',
        },
        {
          step: '2',
          title: 'Sustain Preventive Schedule',
          description:
            'Stay on track with routine bi-annual deworming and standard immunization milestones.',
        },
        {
          step: '3',
          title: 'Routine Community Monitoring',
          description:
            'Continue periodic growth and wellness tracking at standard scheduled health checkups.',
        },
      ];
      protocolName = 'Standard WHO Healthy Nutrition Trajectory';
    }

    setReport({
      overallRisk,
      ratingLabel,
      badgeColor,
      clinicalImpression,
      physiologicalImpact,
      anthropometry: anthroResult,
      factors,
      actionItems,
      protocolName,
    });

    setAssessmentStep('summary');
  };

  const handleReset = () => {
    setAssessmentStep('inputs');
    setReport(null);
    setInputError(null);
  };

  return (
    <div className="bg-white rounded-[32px] border border-black/[0.06] shadow-sm overflow-hidden flex flex-col min-h-[650px]">
      
      {/* Top Header */}
      <div className="px-6 sm:px-8 py-5 border-b border-black/[0.06] bg-[#fbfbfd] flex items-center justify-between">
        <div className="flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-2xl bg-[#00776b] flex items-center justify-center text-white shadow-sm">
            <Scale className="w-5 h-5 stroke-[2.2]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-bold text-[18px] text-[#1d1d1f] tracking-tight">
                Nutrition & Anthropometric Assessment
              </h2>
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            </div>
            <p className="text-[12px] text-[#6e6e73]">
              Evaluate nutritional status using dietary indicators and validated anthropometric measurements.
            </p>
          </div>
        </div>

        <button
          onClick={handleReset}
          className="p-2 rounded-full hover:bg-black/[0.05] text-[#86868b] hover:text-[#1d1d1f] transition-colors cursor-pointer"
          title="Reset Assessment"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Main Body */}
      <div className="p-6 sm:p-8 flex-1 space-y-8">
        
        {assessmentStep === 'inputs' && (
          <div className="space-y-8 animate-in fade-in duration-200">
            
            {/* SECTION 1: Patient Profile */}
            <div className="bg-[#fbfbfd] p-6 rounded-[24px] border border-black/[0.05] space-y-4">
              <div className="flex items-center justify-between border-b border-black/[0.05] pb-3">
                <div className="flex items-center gap-2 text-[#00776b]">
                  <User className="w-4 h-4" />
                  <h3 className="font-bold text-[13px] uppercase tracking-wider text-[#1d1d1f]">
                    Section 1: Patient Profile
                  </h3>
                </div>
                <span className="text-[11px] text-[#86868b] font-mono">Cohort Demographic Setup</span>
              </div>

              {/* Cohort Buttons */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                {(['adult', 'child', 'pregnant', 'elderly'] as const).map((cat) => (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => handleCohortSelect(cat)}
                    className={`py-2.5 px-3 rounded-2xl text-[12px] font-medium border text-center transition-all cursor-pointer ${
                      category === cat
                        ? 'bg-[#00776b] text-white border-[#00776b] font-semibold shadow-xs'
                        : 'bg-white text-[#6e6e73] border-black/[0.08] hover:border-black/[0.2]'
                    }`}
                  >
                    {cat === 'adult'
                      ? 'Adult (18–64y)'
                      : cat === 'child'
                      ? 'Child (6m–11y)'
                      : cat === 'pregnant'
                      ? 'Pregnant Mother'
                      : 'Elderly (65+)'}
                  </button>
                ))}
              </div>

              {/* Profile Details Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-1">
                <div>
                  <label className="text-[12px] font-semibold text-[#1d1d1f] block mb-1">
                    Age (Years)
                  </label>
                  <input
                    type="number"
                    min="0.5"
                    max="110"
                    step={category === 'child' ? '0.5' : '1'}
                    value={ageYears}
                    onChange={(e) => setAgeYears(parseFloat(e.target.value) || 0)}
                    className="w-full px-4 py-2.5 rounded-xl border border-black/[0.08] text-[14px] bg-white focus:outline-none focus:border-[#00776b]"
                  />
                </div>

                <div>
                  <label className="text-[12px] font-semibold text-[#1d1d1f] block mb-1">
                    Biological Sex
                  </label>
                  <div className="grid grid-cols-2 gap-1.5 p-1 rounded-xl bg-white border border-black/[0.08]">
                    <button
                      type="button"
                      onClick={() => setGender('Male')}
                      disabled={category === 'pregnant'}
                      className={`py-1.5 rounded-lg text-[12px] font-medium transition-all ${
                        gender === 'Male' && category !== 'pregnant'
                          ? 'bg-[#1d1d1f] text-white shadow-xs font-semibold'
                          : 'text-[#6e6e73]'
                      }`}
                    >
                      Male
                    </button>
                    <button
                      type="button"
                      onClick={() => setGender('Female')}
                      className={`py-1.5 rounded-lg text-[12px] font-medium transition-all ${
                        gender === 'Female' || category === 'pregnant'
                          ? 'bg-[#1d1d1f] text-white shadow-xs font-semibold'
                          : 'text-[#6e6e73]'
                      }`}
                    >
                      Female
                    </button>
                  </div>
                </div>

                {category === 'pregnant' ? (
                  <div>
                    <label className="text-[12px] font-semibold text-[#1d1d1f] block mb-1">
                      Pregnancy Trimester
                    </label>
                    <select
                      value={trimester}
                      onChange={(e) => setTrimester(parseInt(e.target.value))}
                      className="w-full px-4 py-2.5 rounded-xl border border-black/[0.08] text-[13px] bg-white focus:outline-none focus:border-[#00776b]"
                    >
                      <option value={1}>1st Trimester (Hb &lt; 11.0 g/dL)</option>
                      <option value={2}>2nd Trimester (Hb &lt; 10.5 g/dL)</option>
                      <option value={3}>3rd Trimester (Hb &lt; 11.0 g/dL)</option>
                    </select>
                  </div>
                ) : (
                  <div>
                    <label className="text-[12px] font-semibold text-[#1d1d1f] block mb-1">
                      Target Protocol
                    </label>
                    <div className="px-4 py-2.5 rounded-xl border border-black/[0.05] bg-black/[0.02] text-[13px] text-[#6e6e73]">
                      {category === 'child' ? 'WHO Child Growth 2006' : 'WHO Adult Reference 2024'}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* SECTION 2: Body Measurements */}
            <div className="bg-[#fbfbfd] p-6 rounded-[24px] border border-black/[0.05] space-y-4">
              <div className="flex items-center justify-between border-b border-black/[0.05] pb-3">
                <div className="flex items-center gap-2 text-[#00776b]">
                  <Ruler className="w-4 h-4" />
                  <h3 className="font-bold text-[13px] uppercase tracking-wider text-[#1d1d1f]">
                    Section 2: Body Measurements
                  </h3>
                </div>
                <span className="text-[11px] text-[#86868b] font-mono">Live BMI & MUAC Engine</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {/* Height cm (Required) */}
                <div>
                  <label className="text-[12px] font-semibold text-[#1d1d1f] flex items-center justify-between mb-1">
                    <span>Height (cm) *</span>
                    <span className="text-[10px] text-[#86868b] font-normal">[30–250 cm]</span>
                  </label>
                  <div className="relative">
                    <input
                      type="number"
                      min="30"
                      max="250"
                      step="0.5"
                      value={heightCm}
                      onChange={(e) => setHeightCm(e.target.value)}
                      placeholder="160.0"
                      className="w-full px-4 py-2.5 rounded-xl border border-black/[0.08] text-[14px] bg-white focus:outline-none focus:border-[#00776b]"
                    />
                    <span className="absolute right-3 top-2.5 text-[12px] text-[#86868b] font-mono">
                      cm
                    </span>
                  </div>
                </div>

                {/* Weight kg (Required) */}
                <div>
                  <label className="text-[12px] font-semibold text-[#1d1d1f] flex items-center justify-between mb-1">
                    <span>Weight (kg) *</span>
                    <span className="text-[10px] text-[#86868b] font-normal">[1–250 kg]</span>
                  </label>
                  <div className="relative">
                    <input
                      type="number"
                      min="1"
                      max="250"
                      step="0.1"
                      value={weightKg}
                      onChange={(e) => setWeightKg(e.target.value)}
                      placeholder="55.0"
                      className="w-full px-4 py-2.5 rounded-xl border border-black/[0.08] text-[14px] bg-white focus:outline-none focus:border-[#00776b]"
                    />
                    <span className="absolute right-3 top-2.5 text-[12px] text-[#86868b] font-mono">
                      kg
                    </span>
                  </div>
                </div>

                {/* MUAC (Optional) */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-[12px] font-semibold text-[#1d1d1f] flex items-center gap-1">
                      <span>MUAC</span>
                      <span className="text-[10px] text-[#86868b] font-normal">(Optional)</span>
                    </label>
                    <div className="flex items-center gap-1 bg-black/[0.04] p-0.5 rounded-md text-[10px]">
                      <button
                        type="button"
                        onClick={() => setMuacUnit('mm')}
                        className={`px-1.5 py-0.5 rounded ${
                          muacUnit === 'mm' ? 'bg-white font-bold shadow-xs' : 'text-[#6e6e73]'
                        }`}
                      >
                        mm
                      </button>
                      <button
                        type="button"
                        onClick={() => setMuacUnit('cm')}
                        className={`px-1.5 py-0.5 rounded ${
                          muacUnit === 'cm' ? 'bg-white font-bold shadow-xs' : 'text-[#6e6e73]'
                        }`}
                      >
                        cm
                      </button>
                    </div>
                  </div>
                  <div className="relative">
                    <input
                      type="number"
                      min="5"
                      max="500"
                      step="0.1"
                      value={muacInput}
                      onChange={(e) => setMuacInput(e.target.value)}
                      placeholder={muacUnit === 'mm' ? 'e.g. 135 (mm)' : 'e.g. 13.5 (cm)'}
                      className="w-full px-4 py-2.5 rounded-xl border border-black/[0.08] text-[14px] bg-white focus:outline-none focus:border-[#00776b]"
                    />
                    <span className="absolute right-3 top-2.5 text-[12px] text-[#86868b] font-mono">
                      {muacUnit}
                    </span>
                  </div>
                </div>
              </div>

              {/* Live Calculated Metric Display Card */}
              <div className="p-4 rounded-2xl bg-white border border-black/[0.06] grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <span className="text-[11px] uppercase font-bold tracking-wider text-[#86868b] block">
                    Calculated Body Mass Index
                  </span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-[28px] font-bold font-mono text-[#00776b]">
                      {liveBMI ? liveBMI.toFixed(1) : '—'}
                    </span>
                    <span className="text-[13px] text-[#6e6e73] font-medium">kg/m²</span>
                  </div>
                  <p className="text-[12px] text-[#1d1d1f] font-medium">
                    {liveBMIEval ? (
                      ageYears < 19 ? (
                        <>
                          <span className="font-semibold">BMI-for-age assessment:</span>{' '}
                          {liveBMIEval.category}
                        </>
                      ) : (
                        <>
                          <span className="font-semibold">BMI Assessment:</span>{' '}
                          {liveBMIEval.category}
                        </>
                      )
                    ) : (
                      <span className="text-[#86868b] italic">Enter height and weight</span>
                    )}
                  </p>
                </div>

                <div className="space-y-1 sm:border-l sm:border-black/[0.05] sm:pl-4">
                  <span className="text-[11px] uppercase font-bold tracking-wider text-[#86868b] block">
                    Arm Circumference (MUAC)
                  </span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-[28px] font-bold font-mono text-[#1d1d1f]">
                      {normalizedMUAC ? `${normalizedMUAC}` : '—'}
                    </span>
                    <span className="text-[13px] text-[#6e6e73] font-medium">
                      {normalizedMUAC ? `mm (${(normalizedMUAC / 10).toFixed(1)} cm)` : 'Not provided'}
                    </span>
                  </div>
                  <p className="text-[12px] text-[#1d1d1f] font-medium">
                    {liveMUACEval ? (
                      <>
                        <span className="font-semibold">MUAC Assessment:</span>{' '}
                        {liveMUACEval.interpretation}
                      </>
                    ) : (
                      'Optional measurement'
                    )}
                  </p>
                </div>
              </div>
            </div>

            {/* SECTION 3: Clinical & Dietary Indicators */}
            <div className="bg-[#fbfbfd] p-6 rounded-[24px] border border-black/[0.05] space-y-6">
              <div className="flex items-center justify-between border-b border-black/[0.05] pb-3">
                <div className="flex items-center gap-2 text-[#00776b]">
                  <ClipboardList className="w-4 h-4" />
                  <h3 className="font-bold text-[13px] uppercase tracking-wider text-[#1d1d1f]">
                    Section 3: Dietary & Physical Indicators
                  </h3>
                </div>
                <span className="text-[11px] text-[#86868b] font-mono">5 Clinical Dimensions</span>
              </div>

              <div className="space-y-5">
                {QUESTIONS_TREE.map((q) => {
                  const selected = answers[q.key];
                  return (
                    <div key={q.key} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <label className="text-[13px] font-bold text-[#1d1d1f]">
                          {q.title}
                        </label>
                        <span className="text-[11px] text-[#86868b] font-medium">
                          Selected: <strong className="text-[#00776b]">{selected.label}</strong>
                        </span>
                      </div>
                      <p className="text-[12px] text-[#6e6e73]">{q.prompt}</p>

                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1">
                        {q.options.map((opt, optIdx) => {
                          const isPicked = selected.label === opt.label;
                          return (
                            <button
                              key={optIdx}
                              type="button"
                              onClick={() => setAnswers((prev) => ({ ...prev, [q.key]: opt }))}
                              className={`p-3 rounded-2xl border text-left transition-all cursor-pointer ${
                                isPicked
                                  ? 'bg-white border-[#00776b] ring-1 ring-[#00776b]/20 shadow-xs'
                                  : 'bg-white/60 border-black/[0.06] hover:bg-white hover:border-black/[0.15]'
                              }`}
                            >
                              <div className="flex items-center justify-between mb-1">
                                <span
                                  className={`text-[12px] font-semibold ${
                                    isPicked ? 'text-[#00776b]' : 'text-[#1d1d1f]'
                                  }`}
                                >
                                  {opt.label}
                                </span>
                                {isPicked && <Check className="w-3.5 h-3.5 text-[#00776b]" />}
                              </div>
                              {opt.subtext && (
                                <p className="text-[11px] text-[#6e6e73] leading-snug">
                                  {opt.subtext}
                                </p>
                              )}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {inputError && (
              <div className="p-4 rounded-2xl bg-red-50 border border-red-200 text-red-800 text-[13px] flex items-center gap-2.5">
                <AlertCircle className="w-5 h-5 shrink-0" />
                <span>{inputError}</span>
              </div>
            )}

            {/* Run Assessment Button */}
            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={handleRunEvaluation}
                className="apple-btn-accent px-8 py-4 text-[14px] inline-flex items-center gap-2 shadow-sm font-semibold cursor-pointer"
              >
                <span>Generate Comprehensive Nutrition Assessment</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>

          </div>
        )}

        {assessmentStep === 'evaluating' && (
          <div className="py-16 text-center space-y-4">
            <div className="w-14 h-14 rounded-full bg-[#00776b]/10 text-[#00776b] flex items-center justify-center mx-auto animate-bounce">
              <Scale className="w-7 h-7" />
            </div>
            <div className="space-y-1">
              <h3 className="text-[20px] font-bold text-[#1d1d1f]">
                Evaluating Anthropometric & Nutritional Signals
              </h3>
              <p className="text-[13px] text-[#86868b]">
                Applying WHO reference curves, bounded scoring integration, and deduplication rules...
              </p>
            </div>
          </div>
        )}

        {assessmentStep === 'summary' && report && (
          <div className="space-y-8 animate-in fade-in duration-200">
            
            {/* PART 3: Professional Summary Card (NUTRITION STATUS ASSESSMENT) */}
            <div className="p-6 sm:p-8 rounded-[28px] bg-[#fbfbfd] border border-black/[0.08] shadow-sm space-y-6">
              
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-black/[0.06] pb-5">
                <div>
                  <span className="text-[11px] font-mono uppercase text-[#86868b] tracking-wider block">
                    NUTRITION STATUS ASSESSMENT
                  </span>
                  <h3 className="text-[24px] font-bold text-[#1d1d1f] tracking-tight mt-0.5">
                    {report.ratingLabel}
                  </h3>
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className={`px-4 py-1.5 rounded-full text-[12px] font-bold border shadow-xs ${
                      report.overallRisk === 'LOW'
                        ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                        : report.overallRisk === 'MODERATE'
                        ? 'bg-amber-50 text-amber-800 border-amber-200'
                        : 'bg-red-50 text-red-800 border-red-200'
                    }`}
                  >
                    NUTRITION RISK: {report.overallRisk}
                  </span>
                </div>
              </div>

              {/* Prominent Values Summary Layout */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-[13px]">
                <div className="p-4 rounded-2xl bg-white border border-black/[0.05] space-y-1 shadow-xs">
                  <span className="text-[10px] text-[#86868b] uppercase font-bold tracking-wider block">
                    Body Mass Index (BMI)
                  </span>
                  <span className="text-[24px] font-bold font-mono text-[#00776b] block">
                    {report.anthropometry.bmi.toFixed(1)} <span className="text-[14px] text-[#6e6e73] font-sans font-medium">kg/m²</span>
                  </span>
                  <p className="text-[11px] text-[#6e6e73]">
                    {report.anthropometry.heightCm} cm • {report.anthropometry.weightKg} kg
                  </p>
                </div>

                <div className="p-4 rounded-2xl bg-white border border-black/[0.05] space-y-1 shadow-xs">
                  <span className="text-[10px] text-[#86868b] uppercase font-bold tracking-wider block">
                    BMI Assessment
                  </span>
                  <span className="text-[16px] font-bold text-[#1d1d1f] block leading-snug">
                    {report.anthropometry.bmiCategory}
                  </span>
                  <p className="text-[11px] text-[#6e6e73]">
                    {report.anthropometry.ageGroupClassification}
                  </p>
                </div>

                <div className="p-4 rounded-2xl bg-white border border-black/[0.05] space-y-1 shadow-xs">
                  <span className="text-[10px] text-[#86868b] uppercase font-bold tracking-wider block">
                    MUAC Measurement
                  </span>
                  <span className="text-[24px] font-bold font-mono text-[#1d1d1f] block">
                    {report.anthropometry.muacMm
                      ? `${report.anthropometry.muacMm}`
                      : 'Not Provided'}
                    {report.anthropometry.muacMm && <span className="text-[14px] text-[#6e6e73] font-sans font-medium"> mm</span>}
                  </span>
                  <p className="text-[11px] text-[#6e6e73]">
                    {report.anthropometry.muacMm ? `${(report.anthropometry.muacMm / 10).toFixed(1)} cm` : 'Optional measurement'}
                  </p>
                </div>

                <div className="p-4 rounded-2xl bg-white border border-black/[0.05] space-y-1 shadow-xs">
                  <span className="text-[10px] text-[#86868b] uppercase font-bold tracking-wider block">
                    MUAC Assessment
                  </span>
                  <span className="text-[15px] font-bold text-[#1d1d1f] block leading-snug">
                    {report.anthropometry.muacCategory === 'severe'
                      ? 'Severe Malnutrition'
                      : report.anthropometry.muacCategory === 'moderate'
                      ? 'Moderate Malnutrition'
                      : report.anthropometry.muacCategory === 'normal'
                      ? 'Within reference range'
                      : report.anthropometry.muacCategory === 'informative'
                      ? 'Recorded informatively'
                      : 'Not applied'}
                  </span>
                  <p className="text-[11px] text-[#6e6e73] truncate">
                    {report.anthropometry.muacInterpretation}
                  </p>
                </div>
              </div>

              {/* Clinical Summary & Impression */}
              <div className="p-5 rounded-2xl bg-white border border-black/[0.05] space-y-2">
                <div className="flex items-center gap-2 text-[#00776b]">
                  <Stethoscope className="w-4 h-4" />
                  <span className="font-bold text-[13px] uppercase tracking-wider text-[#1d1d1f]">
                    Clinical Summary & Impression
                  </span>
                </div>
                <p className="text-[14px] text-[#1d1d1f] leading-relaxed">
                  {report.clinicalImpression}
                </p>
                <p className="text-[12px] text-[#6e6e73] border-t border-black/[0.04] pt-2">
                  <strong className="text-[#1d1d1f]">Physiological Impact:</strong>{' '}
                  {report.physiologicalImpact}
                </p>
              </div>
            </div>

            {/* PART 4: Assessment Factors Compact Scan Cards */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-[#00776b]" />
                  <h4 className="font-bold text-[15px] text-[#1d1d1f]">
                    Assessment Factors
                  </h4>
                </div>
                <span className="text-[11px] text-[#86868b]">
                  Scannable individual dimensions
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {report.factors.map((f, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-2xl bg-white border border-black/[0.06] space-y-2 shadow-xs"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-bold text-[13px] text-[#1d1d1f]">{f.category}</span>
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold border shrink-0 ${
                          f.status === 'HEALTHY'
                            ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                            : f.status === 'BORDERLINE'
                            ? 'bg-amber-50 text-amber-800 border-amber-200'
                            : f.status === 'UNHEALTHY'
                            ? 'bg-orange-50 text-orange-900 border-orange-200'
                            : 'bg-red-50 text-red-800 border-red-200'
                        }`}
                      >
                        {f.status === 'HEALTHY' ? (
                          <span>✓</span>
                        ) : f.status === 'BORDERLINE' ? (
                          <span>⚠</span>
                        ) : (
                          <span>✕</span>
                        )}
                        <span>{f.statusLabel}</span>
                      </span>
                    </div>

                    <div className="text-[12px] font-medium text-[#1d1d1f]">{f.value}</div>
                    <p className="text-[11px] text-[#6e6e73] leading-relaxed">{f.explanation}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Recommended Next Steps */}
            <div className="p-6 rounded-[24px] bg-[#fbfbfd] border border-black/[0.06] space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="font-bold text-[14px] text-[#1d1d1f] uppercase tracking-wider">
                  Recommended Clinical Follow-Up Protocol
                </h4>
                <span className="text-[11px] text-[#86868b] font-mono">
                  {report.protocolName}
                </span>
              </div>

              <div className="space-y-2.5">
                {report.actionItems.map((item, idx) => (
                  <div
                    key={idx}
                    className={`p-4 rounded-2xl border text-[13px] flex items-start gap-3.5 ${
                      item.isUrgent
                        ? 'bg-red-50/70 border-red-200 text-red-950'
                        : 'bg-white border-black/[0.05] text-[#1d1d1f]'
                    }`}
                  >
                    <div
                      className={`w-6 h-6 rounded-full flex items-center justify-center font-bold text-[11px] shrink-0 ${
                        item.isUrgent ? 'bg-red-600 text-white' : 'bg-[#00776b] text-white'
                      }`}
                    >
                      {item.step}
                    </div>
                    <div className="space-y-0.5">
                      <span className="font-bold text-[13px] block">{item.title}</span>
                      <p
                        className={
                          item.isUrgent
                            ? 'text-red-900 leading-relaxed text-[12px]'
                            : 'text-[#6e6e73] leading-relaxed text-[12px]'
                        }
                      >
                        {item.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Clear Safety Disclaimer */}
            <div className="p-4 rounded-2xl bg-amber-50/80 border border-amber-200 text-[12px] text-amber-950 flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0 text-amber-700 mt-0.5" />
              <span>
                <strong>Nutritional Screening Disclaimer:</strong> Anthropometric measurements contribute to nutritional-risk assessment and are not diagnostic of anemia. Body mass indices and questionnaire indicators serve as point-of-care screening aids and do not replace formal clinical or laboratory evaluation.
              </span>
            </div>

            {/* Action Bar */}
            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              {onProceedToOpticalScan && (
                <button
                  onClick={onProceedToOpticalScan}
                  className="apple-btn-accent flex-1 py-4 text-[14px] font-semibold inline-flex items-center justify-center gap-2 shadow-sm cursor-pointer"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>Proceed to Optical Eyelid & PPG Screening</span>
                </button>
              )}
              <button
                onClick={handleReset}
                className="apple-btn-secondary px-8 py-4 text-[13px] font-medium cursor-pointer"
              >
                Perform New Evaluation
              </button>
            </div>

          </div>
        )}

      </div>

    </div>
  );
};
