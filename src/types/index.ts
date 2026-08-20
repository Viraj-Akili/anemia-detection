export type UserRole = 'aww' | 'supervisor' | 'district_admin';

export type Language = 'en' | 'hi' | 'ta' | 'mr';

export type Gender = 'Male' | 'Female' | 'Other';

export type Category = 'child' | 'adult' | 'pregnant' | 'elderly';

export type AnemiaRiskLevel = 'LOW' | 'MODERATE' | 'ELEVATED';
export type NutritionRiskLevel = 'LOW' | 'MODERATE' | 'HIGH';
export type PriorityLevel = 'LOW' | 'MODERATE' | 'HIGH';

export type TrajectoryState = 'IMPROVING' | 'STABLE' | 'DECLINING' | 'RAPIDLY_DECLINING';

export type ImageQualityStatus = 'GOOD' | 'INSUFFICIENT';

export interface QualityCheckDetail {
  goodLighting: boolean;
  roiDetected: boolean;
  noMotion: boolean;
  sharpnessOk: boolean;
  reasons: string[];
}

export interface AnthropometryData {
  weightKg: number;
  heightCm: number;
  muacCm: number; // Mid-Upper Arm Circumference in cm
}

export interface ContextQuestionsData {
  ironRichDiet: 'YES' | 'NO' | 'NOT_SURE';
  dewormedLast6Mos: 'YES' | 'NO' | 'NOT_SURE';
  recentIllnessFatigue: 'YES' | 'NO' | 'NOT_SURE';
  maternalSupplementTake?: 'YES' | 'NO' | 'NOT_SURE';
}

export interface SignalContribution {
  name: string;
  category: 'IMAGE' | 'ANTHROPOMETRY' | 'DIET' | 'TRAJECTORY';
  value: string;
  impact: 'POSITIVE' | 'NEUTRAL' | 'CONCERN';
  description: string;
}

export interface ModelMetadata {
  architectureName: string;
  version: string;
  expectedInputFormat: string;
  expectedOutputFormat: string;
  confidenceScore: number;
  roiRegion: string;
}

export interface VisitRecord {
  id: string;
  date: string;
  anemiaRisk: AnemiaRiskLevel;
  nutritionRisk: NutritionRiskLevel;
  overallPriority: PriorityLevel;
  weightKg: number;
  heightCm: number;
  muacCm: number;
  imageQuality: ImageQualityStatus;
  recommendedAction: string;
  notes?: string;
}

export interface Beneficiary {
  id: string;
  abhaId?: string;
  rchId?: string;
  name: string;
  category: Category;
  ageYears?: number;
  ageMonths?: number;
  sex?: Gender;
  isPregnant?: boolean;
  trimester?: 1 | 2 | 3;
  guardianName?: string;
  locationVillage: string;
  anganwadiCentreId: string;
  phone?: string;
  anemiaRisk: AnemiaRiskLevel;
  nutritionRisk: NutritionRiskLevel;
  overallPriority: PriorityLevel;
  trajectory: TrajectoryState;
  lastVisitDate: string;
  visitHistory: VisitRecord[];
  isDemoData: boolean;
}

export interface ScreeningResult {
  id: string;
  beneficiaryId: string;
  timestamp: string;
  imageQuality: ImageQualityStatus;
  imageQualityDetails: QualityCheckDetail;
  anemiaRisk: AnemiaRiskLevel;
  nutritionRisk: NutritionRiskLevel;
  overallPriority: PriorityLevel;
  trajectory: TrajectoryState;
  anthropometry: AnthropometryData;
  questions: ContextQuestionsData;
  contributingSignals: SignalContribution[];
  triggeredSafetyRules: string[];
  recommendedAction: string;
  modelMetadata: ModelMetadata;
  synced: boolean;
  isDemoData: boolean;
}

export interface OfflineSyncItem {
  id: string;
  timestamp: string;
  type: 'SCREENING' | 'BENEFICIARY_CREATE' | 'FOLLOWUP_UPDATE';
  payload: any;
  status: 'PENDING' | 'SYNCING' | 'FAILED' | 'SUCCESS';
  attempts: number;
  error?: string;
}
