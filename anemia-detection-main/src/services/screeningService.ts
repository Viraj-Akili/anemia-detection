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
  ImageQualityStatus,
  BackendMultimodalResponse,
} from '../types';
import { apiClient } from './apiClient';
import { anemiaModelService, ModelInferenceInput } from './anemiaModelService';

export interface ExecuteScreeningParams {
  beneficiary: Beneficiary;
  imageInput?: ModelInferenceInput;
  imageFile?: File | Blob | null;
  ppgFile?: File | Blob | null;
  anthropometry: AnthropometryData;
  questions: ContextQuestionsData;
  symptoms?: string[];
  simulatedImageQuality?: 'GOOD' | 'BAD';
  forcedModelRisk?: AnemiaRiskLevel;
}

// Helper to convert base64 DataURL to File
async function dataUrlToFile(dataUrl: string, filename: string): Promise<File> {
  const res = await fetch(dataUrl);
  const blob = await res.blob();
  return new File([blob], filename, { type: blob.type || 'image/png' });
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
   * Executes the Production Multimodal Screening Pipeline via the Arya Backend Gateway:
   * POST /api/screenings/evaluate-multimodal
   *
   * PRODUCTION SAFETY GUARANTEE:
   * If the backend is unreachable, timed out, or returns an error, this method
   * will THROW an error rather than silently generating an artificial or fake
   * clinical result.
   */
  public async executeScreening(params: ExecuteScreeningParams): Promise<ScreeningResult> {
    const {
      beneficiary,
      imageInput,
      imageFile: rawImageFile,
      ppgFile,
      anthropometry,
      questions,
      symptoms = [],
    } = params;

    // 1. Resolve image file from imageFile or imageInput.imageUri
    let imageFileToUpload: File | Blob | null = rawImageFile || null;
    if (!imageFileToUpload && imageInput?.imageUri && imageInput.imageUri.startsWith('data:')) {
      try {
        imageFileToUpload = await dataUrlToFile(imageInput.imageUri, 'conjunctiva_capture.png');
      } catch (e) {
        console.warn('Failed to convert imageUri dataURL to File:', e);
      }
    }

    // 2. Build Multipart Form Data Payload
    const formData = new FormData();

    // Demographic fields
    const ageYears = beneficiary.ageYears || (beneficiary.category === 'child' ? 3.0 : 28.0);
    formData.append('age_years', ageYears.toString());
    formData.append('gender', (beneficiary.sex || 'Female').toUpperCase());
    formData.append('patient_name', beneficiary.name || 'Patient');

    const isPregnant = beneficiary.category === 'pregnant' || beneficiary.isPregnant === true;
    formData.append('is_pregnant', isPregnant ? 'true' : 'false');
    if (isPregnant) {
      formData.append('trimester', (beneficiary.trimester || 2).toString());
    }

    // Anthropometry fields
    if (anthropometry.weightKg > 0) {
      formData.append('weight_kg', anthropometry.weightKg.toString());
    }
    if (anthropometry.heightCm > 0) {
      formData.append('height_cm', anthropometry.heightCm.toString());
    }
    if (anthropometry.muacCm > 0) {
      formData.append('muac_cm', anthropometry.muacCm.toString());
    }

    // Context & Nutrition
    const dietIron = questions.ironRichDiet === 'YES';
    formData.append('diet_iron_rich', dietIron ? 'true' : 'false');
    formData.append('diet_frequency', dietIron ? 'often' : 'rare');
    formData.append('diet_diversity', dietIron ? '6' : '2');
    formData.append(
      'ifa_adherence',
      questions.maternalSupplementTake === 'YES' ? 'good' : 'unknown'
    );

    // Symptoms flags
    formData.append('symptom_severe_pallor', symptoms.includes('pale_eyelid') ? 'true' : 'false');
    formData.append('symptom_breathlessness', symptoms.includes('heart_racing') ? 'true' : 'false');
    formData.append(
      'symptom_fatigue',
      symptoms.includes('fatigue') || questions.recentIllnessFatigue === 'YES' ? 'true' : 'false'
    );
    formData.append('symptom_bilateral_oedema', 'false');
    formData.append('device_id', 'PRAHARI_FRONTEND_WEB');

    // Modality files
    if (imageFileToUpload) {
      formData.append('image', imageFileToUpload, 'conjunctiva.png');
    }
    if (ppgFile) {
      formData.append('ppg_csv', ppgFile, 'recording.csv');
    }

    // 3. Execute live API call to Arya Backend Gateway (Throws on failure - No silent mocks)
    const backendResp: BackendMultimodalResponse =
      await apiClient.evaluateMultimodalScreening(formData);

    return this.mapBackendResponseToScreeningResult(
      backendResp,
      beneficiary,
      anthropometry,
      questions,
      imageInput
    );
  }

  /**
   * Maps Arya Backend MultimodalEvaluationResponse to the frontend's ScreeningResult schema.
   */
  private mapBackendResponseToScreeningResult(
    resp: BackendMultimodalResponse,
    beneficiary: Beneficiary,
    anthropometry: AnthropometryData,
    questions: ContextQuestionsData,
    imageInput?: ModelInferenceInput
  ): ScreeningResult {
    // Map Risk Levels
    const anemiaRiskMap: Record<string, AnemiaRiskLevel> = {
      low: 'LOW',
      moderate: 'MODERATE',
      high: 'ELEVATED',
      critical: 'ELEVATED',
    };
    const nutritionRiskMap: Record<string, NutritionRiskLevel> = {
      low: 'LOW',
      moderate: 'MODERATE',
      high: 'HIGH',
      critical: 'HIGH',
    };
    const priorityMap: Record<string, PriorityLevel> = {
      low: 'LOW',
      moderate: 'MODERATE',
      high: 'HIGH',
      critical: 'HIGH',
    };
    const trajectoryMap: Record<string, TrajectoryState> = {
      improving: 'IMPROVING',
      stable: 'STABLE',
      declining: 'DECLINING',
      rapidly_declining: 'RAPIDLY_DECLINING',
      insufficient_data: 'STABLE',
    };

    const anemiaRisk: AnemiaRiskLevel = anemiaRiskMap[resp.risk.anemia_risk.toLowerCase()] || 'LOW';
    const nutritionRisk: NutritionRiskLevel =
      nutritionRiskMap[resp.risk.nutrition_risk.toLowerCase()] || 'LOW';
    const overallPriority: PriorityLevel =
      priorityMap[resp.risk.overall_priority.toLowerCase()] || 'LOW';
    const trajectory: TrajectoryState =
      trajectoryMap[resp.risk.trajectory.toLowerCase()] || 'STABLE';

    // Map Image Quality
    const imageQuality: ImageQualityStatus =
      resp.image.quality_status === 'poor' || resp.image.status === 'REJECTED'
        ? 'INSUFFICIENT'
        : 'GOOD';

    // Map Contributing Signals
    const contributingSignals: SignalContribution[] = [];

    // 1. PPG Signal (if present)
    if (resp.ppg.available && resp.ppg.status === 'SUCCESS' && resp.ppg.predicted_hb_g_dl != null) {
      const hb = resp.ppg.predicted_hb_g_dl;
      const hbImpact = hb < 8.0 ? 'CONCERN' : hb < 11.0 ? 'NEUTRAL' : 'POSITIVE';
      contributingSignals.push({
        name: 'Optical PPG Hemoglobin',
        category: 'IMAGE',
        value: `${hb.toFixed(1)} g/dL (SQI ${((resp.ppg.sqi || 0) * 100).toFixed(0)}%)`,
        impact: hbImpact,
        description: `Dual-wavelength MAX30102 sensor: ${resp.ppg.samples || 250} samples @ ${resp.ppg.sampling_rate_hz || 25} Hz. Signal Quality: ${resp.ppg.signal_quality || 'GOOD'}.`,
      });
    } else if (resp.ppg.available && (resp.ppg.status === 'REJECTED' || resp.ppg.status === 'ERROR')) {
      contributingSignals.push({
        name: 'Optical PPG Sensor',
        category: 'IMAGE',
        value: 'Signal Rejected',
        impact: 'CONCERN',
        description: resp.ppg.error_message || (resp.ppg.reasons && resp.ppg.reasons[0]) || 'PPG signal failed quality validation standards.',
      });
    }

    // 2. Image Signal (if present)
    if (resp.image.available && resp.image.status === 'SUCCESS') {
      const prob = (resp.image.probability || 0) * 100;
      contributingSignals.push({
        name: 'Conjunctival Image Classifier',
        category: 'IMAGE',
        value: `${resp.image.label === 'anemic' ? 'Anemic' : 'Non-Anemic'} (${prob.toFixed(0)}% prob)`,
        impact: resp.image.label === 'anemic' ? 'CONCERN' : 'POSITIVE',
        description: `AI conjunctival mucosal feature analysis (confidence: ${((resp.image.confidence || 0.85) * 100).toFixed(0)}%).`,
      });
    }

    // 3. Clinical Risk Assessment SHAP feature contributions
    if (resp.risk.contributors && resp.risk.contributors.length > 0) {
      for (const c of resp.risk.contributors) {
        contributingSignals.push({
          name: c.label || c.feature,
          category: c.feature.includes('whz') || c.feature.includes('muac') ? 'ANTHROPOMETRY' : 'DIET',
          value: `${(c.importance * 100).toFixed(0)}% Weight`,
          impact: c.importance > 0.25 ? 'CONCERN' : 'NEUTRAL',
          description: `Clinical Risk Assessment feature attribution for ${c.label}.`,
        });
      }
    }

    return {
      id: `SCR-LIVE-${resp.screening_id}`,
      beneficiaryId: beneficiary.id,
      timestamp: resp.timestamp || new Date().toISOString(),
      imageQuality,
      imageQualityDetails: {
        goodLighting: imageQuality === 'GOOD',
        roiDetected: true,
        noMotion: imageQuality === 'GOOD',
        sharpnessOk: imageQuality === 'GOOD',
        reasons: resp.image.quality_reasons || [],
      },
      anemiaRisk,
      nutritionRisk,
      overallPriority,
      trajectory,
      anthropometry,
      questions,
      contributingSignals,
      triggeredSafetyRules: resp.risk.safety_flags || [],
      recommendedAction: resp.risk.recommended_action.replace(/_/g, ' ').toUpperCase(),
      modelMetadata: {
        architectureName: 'PRAHARI Multimodal AI (Conjunctival Image Analysis + Optical PPG + Clinical Risk Assessment)',
        version: '1.0.0-prod',
        expectedInputFormat: 'Conjunctival Photo + 25Hz MAX30102 PPG CSV',
        expectedOutputFormat: 'Independent Telemetry + Calibrated Triage + WHO Safety Floor',
        confidenceScore: resp.risk.confidence || 0.85,
        roiRegion: imageInput?.roiRegion || 'Palpebral Conjunctiva',
      },
      synced: true,
      isDemoData: false,
      ppgSummary: resp.ppg,
      imageSummary: resp.image,
      backendScreeningId: resp.screening_id,
      backendBeneficiaryId: resp.beneficiary_id,
      hbSource: resp.risk.hb_source,
      isOfflineFallback: false,
    };
  }

  /**
   * Explicit Development Mock Method (ONLY for standalone UI layout testing).
   * NEVER invoked silently on backend failure.
   */
  public async executeDevMockScreening(params: {
    beneficiary: Beneficiary;
    imageInput: ModelInferenceInput;
    anthropometry: AnthropometryData;
    questions: ContextQuestionsData;
    simulatedImageQuality?: 'GOOD' | 'BAD';
    forcedModelRisk?: AnemiaRiskLevel;
  }): Promise<ScreeningResult> {
    const { beneficiary, imageInput, anthropometry, questions, simulatedImageQuality, forcedModelRisk } = params;

    const modelResult = await anemiaModelService.runInference(
      imageInput,
      simulatedImageQuality || 'GOOD',
      forcedModelRisk
    );

    const { nutritionRisk, anthropometrySignals, triggeredSafetyRules } =
      this.evaluateAnthropometry(beneficiary, anthropometry);

    const dietSignals = this.evaluateContextQuestions(questions);
    const { trajectory, trajectorySignals } = this.evaluateTrajectory(beneficiary);

    const anemiaRisk = modelResult.anemiaRisk;
    let overallPriority: PriorityLevel = 'LOW';
    if (anemiaRisk === 'ELEVATED' || nutritionRisk === 'HIGH' || triggeredSafetyRules.length > 0) {
      overallPriority = 'HIGH';
    } else if (anemiaRisk === 'MODERATE' || nutritionRisk === 'MODERATE' || trajectory === 'DECLINING') {
      overallPriority = 'MODERATE';
    }

    const contributingSignals: SignalContribution[] = [
      {
        name: '[DEV DEMO] Conjunctival Image Signal',
        category: 'IMAGE',
        value: `${anemiaRisk} Risk`,
        impact: anemiaRisk === 'ELEVATED' ? 'CONCERN' : anemiaRisk === 'MODERATE' ? 'NEUTRAL' : 'POSITIVE',
        description: `[DEVELOPMENT DEMO MOCK] Synthetic feature calculation. Not a clinical diagnosis.`,
      },
      ...anthropometrySignals,
      ...dietSignals,
      ...trajectorySignals,
    ];

    return {
      id: `DEMO-MOCK-${Date.now()}`,
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
      recommendedAction: '[DEV MOCK DEMO ONLY] This is an artificial frontend mock for UI layout validation. Real screenings require the PRAHARI Backend.',
      modelMetadata: {
        ...modelResult.metadata,
        architectureName: '[DEV DEMO ONLY] Simulated Offline Heuristic - NOT A CLINICAL RESULT',
      },
      synced: false,
      isDemoData: true,
      isOfflineFallback: true,
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
}

export const screeningService = ScreeningService.getInstance();
