import {
  AnthropometryData,
  Beneficiary,
  ContextQuestionsData,
  PriorityLevel,
  ScreeningResult,
  SignalContribution,
  TrajectoryState,
  NutritionRiskLevel,
  AnemiaRiskLevel,
} from '../types';
import { anemiaModelService, ModelInferenceInput } from './anemiaModelService';

export interface ExecuteScreeningParams {
  beneficiary: Beneficiary;
  imageInput: ModelInferenceInput;
  anthropometry: AnthropometryData;
  questions: ContextQuestionsData;
  simulatedImageQuality?: 'GOOD' | 'BAD';
  forcedModelRisk?: AnemiaRiskLevel;
}

export class ScreeningService {
  private static instance: ScreeningService;

  private constructor() {}

  public static getInstance(): ScreeningService {
    if (!ScreeningService.instance) {
      ScreeningService.instance = new ScreeningService();
    }
    return ScreeningService.instance;
  }

  /**
   * Executes the full Multimodal Screening Pipeline combining:
   * 1. Computer Vision Image Signal (Palpebral Conjunctiva / Nailbed)
   * 2. Anthropometric Measurement Z-scores (MUAC, Weight, Height)
   * 3. Context & Dietary Factors
   * 4. Historical Visit Trajectory
   * 5. Clinical Safety Rules Verification
   */
  public async executeScreening(params: ExecuteScreeningParams): Promise<ScreeningResult> {
    const { beneficiary, imageInput, anthropometry, questions, simulatedImageQuality, forcedModelRisk } = params;

    // 1. Run AI Model Inference on Image Signal
    const modelResult = await anemiaModelService.runInference(
      imageInput,
      simulatedImageQuality || 'GOOD',
      forcedModelRisk
    );

    // 2. Evaluate Anthropometry & Nutrition Risk
    const { nutritionRisk, anthropometrySignals, triggeredSafetyRules } =
      this.evaluateAnthropometry(beneficiary, anthropometry);

    // 3. Evaluate Context & Diet Factors
    const dietSignals = this.evaluateContextQuestions(questions);

    // 4. Evaluate Historical Visit Trajectory
    const { trajectory, trajectorySignals } = this.evaluateTrajectory(beneficiary);

    // 5. Combine Multimodal Signals & Determine Overall Priority
    const anemiaRisk = modelResult.anemiaRisk;

    let overallPriority: PriorityLevel = 'LOW';
    if (anemiaRisk === 'ELEVATED' || nutritionRisk === 'HIGH' || triggeredSafetyRules.length > 0) {
      overallPriority = 'HIGH';
    } else if (anemiaRisk === 'MODERATE' || nutritionRisk === 'MODERATE' || trajectory === 'DECLINING') {
      overallPriority = 'MODERATE';
    }

    // 6. Generate Clinical Recommended Next Step
    const recommendedAction = this.generateRecommendedAction(
      anemiaRisk,
      nutritionRisk,
      overallPriority,
      triggeredSafetyRules,
      beneficiary
    );

    // Assemble signal breakdown for explainability component
    const contributingSignals: SignalContribution[] = [
      {
        name: 'Conjunctival Image Signal',
        category: 'IMAGE',
        value: `${anemiaRisk} Risk (Pallor Score ${modelResult.palpebralPallorScore.toFixed(2)})`,
        impact: anemiaRisk === 'ELEVATED' ? 'CONCERN' : anemiaRisk === 'MODERATE' ? 'NEUTRAL' : 'POSITIVE',
        description: `Visual pallor feature extraction on ${modelResult.metadata.roiRegion} with ${(modelResult.confidenceScore * 100).toFixed(0)}% confidence score.`,
      },
      ...anthropometrySignals,
      ...dietSignals,
      ...trajectorySignals,
    ];

    return {
      id: `SCR-${Date.now()}`,
      beneficiaryId: beneficiary.id,
      timestamp: new Date().toISOString(),
      imageQuality: modelResult.imageQuality,
      imageQualityDetails: modelResult.qualityDetails,
      anemiaRisk,
      nutritionRisk,
      overallPriority,
      trajectory,
      anthropometry,
      questions,
      contributingSignals,
      triggeredSafetyRules,
      recommendedAction,
      modelMetadata: modelResult.metadata,
      synced: false,
      isDemoData: beneficiary.isDemoData,
    };
  }

  private evaluateAnthropometry(
    beneficiary: Beneficiary,
    anthropometry: AnthropometryData
  ): {
    nutritionRisk: NutritionRiskLevel;
    anthropometrySignals: SignalContribution[];
    triggeredSafetyRules: string[];
  } {
    const signals: SignalContribution[] = [];
    const safetyRules: string[] = [];
    let nutritionRisk: NutritionRiskLevel = 'LOW';

    // 1. Child Anthropometry (6–59 months)
    if (beneficiary.category === 'child') {
      if (anthropometry.muacCm < 11.5) {
        nutritionRisk = 'HIGH';
        safetyRules.push(
          'CLINICAL RULE #1 (SAM Escalation): Child MUAC < 11.5 cm indicates Severe Acute Malnutrition requiring immediate medical officer referral.'
        );
        signals.push({
          name: 'Pediatric MUAC',
          category: 'ANTHROPOMETRY',
          value: `${anthropometry.muacCm} cm (SAM Red Zone)`,
          impact: 'CONCERN',
          description: 'MUAC measurement falls below the WHO 11.5 cm pediatric cutoff.',
        });
      } else if (anthropometry.muacCm < 12.5) {
        nutritionRisk = 'MODERATE';
        signals.push({
          name: 'Pediatric MUAC',
          category: 'ANTHROPOMETRY',
          value: `${anthropometry.muacCm} cm (MAM Yellow Zone)`,
          impact: 'CONCERN',
          description: 'MUAC indicates Moderate Acute Malnutrition.',
        });
      } else {
        signals.push({
          name: 'Pediatric MUAC',
          category: 'ANTHROPOMETRY',
          value: `${anthropometry.muacCm} cm (Normal Green Zone)`,
          impact: 'POSITIVE',
          description: 'Pediatric MUAC is within healthy range (>= 12.5 cm).',
        });
      }
    } else if (beneficiary.category === 'pregnant') {
      // 2. Pregnant Women Anthropometry
      if (anthropometry.muacCm < 21.0) {
        nutritionRisk = 'HIGH';
        signals.push({
          name: 'Maternal MUAC',
          category: 'ANTHROPOMETRY',
          value: `${anthropometry.muacCm} cm (Low Maternal Reserve)`,
          impact: 'CONCERN',
          description: 'Maternal MUAC indicates severe undernutrition.',
        });
      } else if (anthropometry.muacCm < 23.0) {
        nutritionRisk = 'MODERATE';
        signals.push({
          name: 'Maternal MUAC',
          category: 'ANTHROPOMETRY',
          value: `${anthropometry.muacCm} cm (Borderline Reserve)`,
          impact: 'NEUTRAL',
          description: 'Maternal MUAC requires dietary supplementation.',
        });
      } else {
        signals.push({
          name: 'Maternal MUAC',
          category: 'ANTHROPOMETRY',
          value: `${anthropometry.muacCm} cm (Adequate)`,
          impact: 'POSITIVE',
          description: 'Maternal MUAC indicates adequate muscle mass.',
        });
      }
    } else {
      // 3. Adult & Elderly Anthropometry (BMI & Adult MUAC)
      const heightM = anthropometry.heightCm > 0 ? anthropometry.heightCm / 100 : 1.65;
      const bmi = anthropometry.weightKg > 0 ? anthropometry.weightKg / (heightM * heightM) : 21.0;

      if (bmi < 16.0 || anthropometry.muacCm < 18.5) {
        nutritionRisk = 'HIGH';
        safetyRules.push(
          'CLINICAL RULE #2 (Adult Severe Undernutrition): Adult BMI < 16.0 or MUAC < 18.5 cm indicates severe wasting.'
        );
        signals.push({
          name: 'Adult BMI & Wasting',
          category: 'ANTHROPOMETRY',
          value: `BMI ${bmi.toFixed(1)} (Severe Undernutrition)`,
          impact: 'CONCERN',
          description: 'Significant somatic muscle and adipose tissue depletion.',
        });
      } else if (bmi < 18.5 || anthropometry.muacCm < 23.0) {
        nutritionRisk = 'MODERATE';
        signals.push({
          name: 'Adult BMI',
          category: 'ANTHROPOMETRY',
          value: `BMI ${bmi.toFixed(1)} (Underweight)`,
          impact: 'CONCERN',
          description: 'Body Mass Index falls below the WHO normal threshold (18.5–24.9).',
        });
      } else {
        signals.push({
          name: 'Adult BMI',
          category: 'ANTHROPOMETRY',
          value: `BMI ${bmi.toFixed(1)} (Normal Range)`,
          impact: 'POSITIVE',
          description: 'Body Mass Index is within healthy WHO reference range.',
        });
      }
    }

    return { nutritionRisk, anthropometrySignals: signals, triggeredSafetyRules: safetyRules };
  }

  private evaluateContextQuestions(questions: ContextQuestionsData): SignalContribution[] {
    const signals: SignalContribution[] = [];

    if (questions.ironRichDiet === 'NO') {
      signals.push({
        name: 'Dietary Iron Intake',
        category: 'DIET',
        value: 'Inadequate Iron Intake',
        impact: 'CONCERN',
        description: 'Infrequent consumption of iron-dense foods (green leafy vegetables, pulses, fortified foods).',
      });
    } else {
      signals.push({
        name: 'Dietary Iron Intake',
        category: 'DIET',
        value: 'Regular Iron Intake',
        impact: 'POSITIVE',
        description: 'Regular consumption of iron-rich foods reported.',
      });
    }

    if (questions.dewormedLast6Mos === 'NO') {
      signals.push({
        name: 'Albendazole Deworming',
        category: 'DIET',
        value: 'Overdue for Deworming',
        impact: 'CONCERN',
        description: 'No deworming tablet received in the past 6 months.',
      });
    }

    return signals;
  }

  private evaluateTrajectory(beneficiary: Beneficiary): {
    trajectory: TrajectoryState;
    trajectorySignals: SignalContribution[];
  } {
    const history = beneficiary.visitHistory || [];
    if (history.length < 2) {
      return {
        trajectory: 'STABLE',
        trajectorySignals: [
          {
            name: 'Historical Trend',
            category: 'TRAJECTORY',
            value: 'Initial Screening Visit',
            impact: 'NEUTRAL',
            description: 'First formal screening record established.',
          },
        ],
      };
    }

    // Check last 2-3 visits for trajectory classification
    const recent = history.slice(-3);
    const risks = recent.map((v) => (v.anemiaRisk === 'ELEVATED' ? 3 : v.anemiaRisk === 'MODERATE' ? 2 : 1));

    let trajectory: TrajectoryState = 'STABLE';
    if (risks[risks.length - 1] > risks[0]) {
      trajectory = risks[risks.length - 1] === 3 ? 'RAPIDLY_DECLINING' : 'DECLINING';
    } else if (risks[risks.length - 1] < risks[0]) {
      trajectory = 'IMPROVING';
    }

    const impact = trajectory === 'DECLINING' || trajectory === 'RAPIDLY_DECLINING' ? 'CONCERN' : 'POSITIVE';

    return {
      trajectory,
      trajectorySignals: [
        {
          name: 'Longitudinal Trajectory',
          category: 'TRAJECTORY',
          value: trajectory.replace('_', ' '),
          impact,
          description: `Analysis across ${history.length} previous visit records indicates a ${trajectory.toLowerCase().replace('_', ' ')} trend.`,
        },
      ],
    };
  }

  private generateRecommendedAction(
    anemiaRisk: AnemiaRiskLevel,
    nutritionRisk: NutritionRiskLevel,
    priority: PriorityLevel,
    safetyRules: string[],
    beneficiary: Beneficiary
  ): string {
    if (safetyRules.length > 0) {
      return 'URGENT MEDICAL OFFICER REFERRAL: Safety rule trigger requires immediate PHC evaluation and confirmatory Hb testing.';
    }

    if (priority === 'HIGH' || anemiaRisk === 'ELEVATED') {
      return 'Confirmatory hemoglobin (Hb) laboratory testing is strongly recommended at Primary Health Centre (PHC). Schedule 14-day follow-up visit.';
    }

    if (priority === 'MODERATE' || anemiaRisk === 'MODERATE' || nutritionRisk === 'HIGH') {
      return 'Provide targeted IFA supplementation, advice local iron-dense meal plan, and schedule 30-day follow-up monitoring.';
    }

    return 'Growth and screening indicators are healthy. Continue standard Anganwadi supplementary nutrition and schedule routine 60-day checkup.';
  }
}

export const screeningService = ScreeningService.getInstance();
