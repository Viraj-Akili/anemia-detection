import React from 'react';
import {
  AnthropometryData,
  Beneficiary,
  ContextQuestionsData,
  Language,
  ScreeningResult,
} from '../../types';
import { getTranslation } from '../../services/localizationService';
import { screeningService } from '../../services/screeningService';
import { syncService } from '../../services/syncService';
import { SafetyDisclaimerBanner } from '../common/SafetyDisclaimerBanner';
import {
  Camera,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  RefreshCw,
  Activity,
  ShieldAlert,
  Zap,
  Check,
  X,
  ChevronRight,
  Sparkles,
} from 'lucide-react';

import { PPGUploadZone } from '../scanner/PPGUploadZone';
import { WhatToDoNextCard } from '../results/WhatToDoNextCard';
import { ComprehensiveScreeningSummary } from '../results/ComprehensiveScreeningSummary';

interface NewScreeningWorkflowProps {
  beneficiaries: Beneficiary[];
  selectedBeneficiary?: Beneficiary;
  onComplete: (result: ScreeningResult) => void;
  onCancel: () => void;
  language: Language;
  initialQualityState?: 'GOOD' | 'BAD';
}

export const NewScreeningWorkflow: React.FC<NewScreeningWorkflowProps> = ({
  beneficiaries,
  selectedBeneficiary: initialBeneficiary,
  onComplete,
  onCancel,
  language,
  initialQualityState = 'GOOD',
}) => {
  const [currentStep, setCurrentStep] = React.useState<number>(initialBeneficiary ? 2 : 1);
  const [beneficiary, setBeneficiary] = React.useState<Beneficiary | undefined>(initialBeneficiary);

  const [capturedImage, setCapturedImage] = React.useState<string | null>(null);
  const [imageFile, setImageFile] = React.useState<File | null>(null);
  const [ppgFile, setPpgFile] = React.useState<File | null>(null);
  const [simulatedQuality, setSimulatedQuality] = React.useState<'GOOD' | 'BAD'>(initialQualityState);
  const [cameraRoiRegion, setCameraRoiRegion] = React.useState<'Palpebral Conjunctiva'>(
    'Palpebral Conjunctiva'
  );

  const [weightKg, setWeightKg] = React.useState<number>(beneficiary?.category === 'pregnant' ? 52.8 : 13.2);
  const [heightCm, setHeightCm] = React.useState<number>(beneficiary?.category === 'pregnant' ? 156 : 99);
  const [muacCm, setMuacCm] = React.useState<number>(beneficiary?.category === 'pregnant' ? 22.8 : 11.4);

  const [ironRichDiet, setIronRichDiet] = React.useState<'YES' | 'NO' | 'NOT_SURE'>('NO');
  const [dewormedLast6Mos, setDewormedLast6Mos] = React.useState<'YES' | 'NO' | 'NOT_SURE'>('NO');
  const [recentIllnessFatigue, setRecentIllnessFatigue] = React.useState<'YES' | 'NO' | 'NOT_SURE'>('YES');

  const [analysisStage, setAnalysisStage] = React.useState<number>(0);
  const [screeningResult, setScreeningResult] = React.useState<ScreeningResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = React.useState(false);
  const [analysisError, setAnalysisError] = React.useState<string | null>(null);

  const sampleImages = [
    {
      id: 'conjunctiva-1',
      name: 'Lower Eyelid Conjunctiva',
      roi: 'Palpebral Conjunctiva' as const,
      url: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=400&q=80',
    },
  ];

  const handleStartAnalysis = async () => {
    if (!beneficiary) return;
    setIsAnalyzing(true);
    setAnalysisError(null);
    setCurrentStep(5);

    for (let i = 1; i <= 6; i++) {
      setAnalysisStage(i);
      await new Promise((resolve) => setTimeout(resolve, 200));
    }

    const anthropometryData: AnthropometryData = { weightKg, heightCm, muacCm };
    const questionsData: ContextQuestionsData = {
      ironRichDiet,
      dewormedLast6Mos,
      recentIllnessFatigue,
    };

    try {
      const result = await screeningService.executeScreening({
        beneficiary,
        imageInput: { roiRegion: cameraRoiRegion, imageUri: capturedImage || undefined },
        imageFile,
        ppgFile,
        anthropometry: anthropometryData,
        questions: questionsData,
        simulatedImageQuality: simulatedQuality,
      });

      syncService.addToQueue({
        type: 'SCREENING',
        payload: result,
      });

      setScreeningResult(result);
      setIsAnalyzing(false);
      setCurrentStep(6);
    } catch (err: any) {
      setIsAnalyzing(false);
      setAnalysisError(
        err?.message ||
          'Screening service unavailable. Unable to connect to backend server. Please verify the backend is running and retry.'
      );
      setCurrentStep(4);
    }
  };

  const stepsList = [
    { id: 1, label: 'Beneficiary' },
    { id: 2, label: 'Optical Camera' },
    { id: 3, label: 'Quality Check' },
    { id: 4, label: 'Measurements' },
    { id: 5, label: 'Analysis' },
    { id: 6, label: 'Result' },
  ];

  return (
    <div className="max-w-[860px] mx-auto space-y-6 pb-16">
      
      {/* Form Stepper Navigation Header */}
      <div className="bg-white rounded-[28px] p-6 border border-black/[0.06] shadow-sm space-y-4">
        <div className="flex items-center justify-between text-[13px] text-[#6e6e73]">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#00776b]" />
            <span className="font-semibold text-[#1d1d1f]">Guided Screening Wizard</span>
          </div>
          <button
            onClick={onCancel}
            className="text-[#86868b] hover:text-[#1d1d1f] transition-colors text-[12px]"
          >
            Cancel & Exit
          </button>
        </div>

        {/* Progress Stepper Bars */}
        <div className="grid grid-cols-6 gap-2">
          {stepsList.map((step) => (
            <div key={step.id} className="space-y-1.5">
              <div
                className={`h-1.5 rounded-full transition-all ${
                  step.id === currentStep
                    ? 'bg-[#00776b]'
                    : step.id < currentStep
                    ? 'bg-[#00776b]/40'
                    : 'bg-black/[0.06]'
                }`}
              />
              <div
                className={`text-[10px] text-center font-medium truncate ${
                  step.id === currentStep ? 'text-[#1d1d1f] font-semibold' : 'text-[#86868b]'
                }`}
              >
                {step.id}. {step.label}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* STEP 1: SELECT BENEFICIARY */}
      {currentStep === 1 && (
        <div className="bg-white rounded-[32px] p-8 border border-black/[0.06] space-y-6 shadow-sm">
          <div>
            <span className="text-[12px] font-mono text-[#86868b] uppercase tracking-wider">Step 01</span>
            <h3 className="text-[24px] font-semibold text-[#1d1d1f] tracking-title mt-1">
              Select Beneficiary for Screening
            </h3>
            <p className="text-[14px] text-[#6e6e73]">Choose a registered child (6–59 months) or pregnant mother</p>
          </div>

          <div className="space-y-3">
            {beneficiaries.map((b) => (
              <div
                key={b.id}
                onClick={() => {
                  setBeneficiary(b);
                  setCurrentStep(2);
                }}
                className={`p-5 rounded-2xl border transition-all cursor-pointer flex items-center justify-between ${
                  beneficiary?.id === b.id
                    ? 'bg-[#fbfbfd] border-[#00776b] ring-1 ring-[#00776b]/20 shadow-sm'
                    : 'bg-[#fbfbfd] border-black/[0.04] hover:bg-[#f5f5f7]'
                }`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-[#1d1d1f] text-[16px]">{b.name}</span>
                    {b.abhaId && (
                      <span className="px-2 py-0.5 text-[10px] font-mono text-[#00776b] bg-[#00776b]/10 rounded-full">
                        {b.abhaId}
                      </span>
                    )}
                  </div>
                  <div className="text-[12px] text-[#6e6e73] mt-0.5">
                    {b.category === 'child' ? `Child, Age ${b.ageYears}y` : `Pregnant Mother, Trimester ${b.trimester}`} • Village: {b.locationVillage}
                  </div>
                </div>
                <button className="apple-btn-accent px-4 py-2 text-[12px] font-medium shadow-sm">
                  Select
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* STEP 2: CAMERA CAPTURE */}
      {currentStep === 2 && (
        <div className="bg-white rounded-[32px] p-8 border border-black/[0.06] space-y-6 shadow-sm">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <span className="text-[12px] font-mono text-[#86868b] uppercase tracking-wider">Step 02</span>
              <h3 className="text-[24px] font-semibold text-[#1d1d1f] tracking-title mt-1">
                Optical Conjunctiva Capture
              </h3>
              <p className="text-[14px] text-[#6e6e73]">
                Target: <strong className="text-[#1d1d1f]">Palpebral Conjunctiva</strong> for {beneficiary?.name}
              </p>
            </div>

            <div className="flex items-center">
              <span className="px-3.5 py-1.5 rounded-full text-[12px] font-semibold bg-[#00776b]/10 text-[#00776b] border border-[#00776b]/20">
                Palpebral Conjunctiva Target
              </span>
            </div>
          </div>

          {/* Camera Viewfinder Dark Frame */}
          <div className="relative bg-[#0c0d10] rounded-[32px] overflow-hidden h-80 flex items-center justify-center border border-black/[0.1] iphone-frame-dark">
            <div className="absolute inset-8 border-2 border-[#00776b] rounded-2xl clinical-roi-pulse flex flex-col justify-between p-3 pointer-events-none z-10 bg-[#00776b]/10">
              <div className="flex justify-between items-center text-[10px] font-medium text-white bg-black/60 backdrop-blur-md px-2.5 py-1 rounded-full self-start border border-white/10">
                Target: Palpebral Conjunctiva
              </div>
              <div className="text-center text-[11px] font-medium text-white bg-black/60 backdrop-blur-md py-1 px-3 rounded-full self-center border border-white/10">
                Gently evert lower eyelid • Hold steady at 15 cm
              </div>
            </div>

            <img
              src={sampleImages[0].url}
              alt="Anatomy ROI Preview"
              className="w-full h-full object-cover opacity-75 contrast-110"
            />

            <div className="absolute bottom-3 left-3 right-3 z-20 flex items-center justify-between bg-black/70 backdrop-blur-md p-2.5 rounded-2xl border border-white/10 text-[11px]">
              <div className="flex items-center gap-3 text-white">
                <span className="flex items-center text-emerald-400 font-medium">
                  <Check className="w-3 h-3 mr-1" /> Illumination Optimal (460 lx)
                </span>
                <span className="flex items-center text-emerald-400 font-medium">
                  <Check className="w-3 h-3 mr-1" /> Mucosa in Focus
                </span>
              </div>

              <button
                onClick={() =>
                  setSimulatedQuality((prev) => (prev === 'GOOD' ? 'BAD' : 'GOOD'))
                }
                className="px-2.5 py-1 rounded-full bg-white/10 text-white text-[10px] hover:bg-white/20 border border-white/10"
              >
                Toggle Quality: {simulatedQuality}
              </button>
            </div>
          </div>

          {/* Optional PPG Hardware Sensor Attachment */}
          <div className="pt-4 border-t border-black/[0.06]">
            <PPGUploadZone
              ppgFile={ppgFile}
              onPPGFileChange={(file) => setPpgFile(file)}
            />
          </div>

          <div className="flex items-center justify-between pt-2">
            <button
              onClick={() => setCurrentStep(1)}
              className="apple-btn-secondary px-5 py-3 text-[13px]"
            >
              ← Back
            </button>

            <button
              onClick={() => {
                setCapturedImage(sampleImages[0].url);
                setCurrentStep(3);
              }}
              className="apple-btn-accent px-6 py-3.5 text-[13px] inline-flex items-center gap-2 shadow-sm"
            >
              <Camera className="w-4 h-4" />
              <span>Capture & Check Quality</span>
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: QUALITY CHECK */}
      {currentStep === 3 && (
        <div className="bg-white rounded-[32px] p-8 border border-black/[0.06] space-y-6 shadow-sm">
          <div>
            <span className="text-[12px] font-mono text-[#86868b] uppercase tracking-wider">Step 03</span>
            <h3 className="text-[24px] font-semibold text-[#1d1d1f] tracking-title mt-1">
              Image Quality Validation Gate
            </h3>
          </div>

          {simulatedQuality === 'GOOD' ? (
            <div className="bg-emerald-50/80 border border-emerald-200 rounded-2xl p-6 space-y-2">
              <div className="flex items-center gap-2 text-emerald-800 font-semibold text-[16px]">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <span>Image Quality: Optimal — Ready for Assessment</span>
              </div>
              <p className="text-[13px] text-emerald-900 leading-relaxed">
                Ambient illumination, focus sharpness, and palpebral mucosa exposure meet clinical calibration standards.
              </p>
            </div>
          ) : (
            <div className="bg-amber-50/80 border border-amber-200 rounded-2xl p-6 space-y-3">
              <div className="flex items-center gap-2 text-amber-800 font-semibold text-[16px]">
                <AlertTriangle className="w-5 h-5 text-amber-600" />
                <span>Image Quality Insufficient</span>
              </div>
              <p className="text-[13px] text-amber-900 leading-relaxed">
                Motion jitter or low illumination detected. Please retake under steady natural light for optimal accuracy.
              </p>
            </div>
          )}

          <div className="flex items-center justify-between pt-4 border-t border-black/[0.06]">
            <button
              onClick={() => setCurrentStep(2)}
              className="apple-btn-secondary px-5 py-3 text-[13px] inline-flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retake Photo</span>
            </button>

            <button
              onClick={() => setCurrentStep(4)}
              className="apple-btn-accent px-6 py-3.5 text-[13px] inline-flex items-center gap-2 shadow-sm"
            >
              <span>{simulatedQuality === 'GOOD' ? 'Proceed to Measurements' : 'Use Anyway'}</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: ANTHROPOMETRY & CONTEXT */}
      {currentStep === 4 && (
        <div className="bg-white rounded-[32px] p-8 border border-black/[0.06] space-y-6 shadow-sm">
          <div>
            <span className="text-[12px] font-mono text-[#86868b] uppercase tracking-wider">Step 04</span>
            <h3 className="text-[24px] font-semibold text-[#1d1d1f] tracking-title mt-1">
              WHO Anthropometry & Clinical Context
            </h3>
          </div>

          {analysisError && (
            <div className="bg-red-50 border border-red-200 rounded-2xl p-4 flex items-start gap-3 text-[13px] text-red-900">
              <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <p className="font-semibold text-red-800">Screening Service Unavailable</p>
                <p>{analysisError}</p>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-[#fbfbfd] p-4 rounded-2xl border border-black/[0.06] space-y-2">
              <label className="text-[12px] text-[#6e6e73] font-medium">Weight (kg)</label>
              <input
                type="number"
                step="0.1"
                value={weightKg}
                onChange={(e) => setWeightKg(Number(e.target.value))}
                className="w-full bg-white border border-black/[0.1] rounded-xl px-3 py-2.5 text-[20px] font-bold text-[#1d1d1f] text-center font-mono focus:outline-none focus:border-[#00776b]"
              />
              <div className="text-[11px] text-[#86868b] text-center">Digital Scale Reading</div>
            </div>

            <div className="bg-[#fbfbfd] p-4 rounded-2xl border border-black/[0.06] space-y-2">
              <label className="text-[12px] text-[#6e6e73] font-medium">Height / Length (cm)</label>
              <input
                type="number"
                step="0.5"
                value={heightCm}
                onChange={(e) => setHeightCm(Number(e.target.value))}
                className="w-full bg-white border border-black/[0.1] rounded-xl px-3 py-2.5 text-[20px] font-bold text-[#1d1d1f] text-center font-mono focus:outline-none focus:border-[#00776b]"
              />
              <div className="text-[11px] text-[#86868b] text-center">Stadiometer</div>
            </div>

            <div className="bg-[#fbfbfd] p-4 rounded-2xl border border-black/[0.06] space-y-2">
              <label className="text-[12px] text-[#6e6e73] font-medium">WHO MUAC (cm)</label>
              <input
                type="number"
                step="0.1"
                value={muacCm}
                onChange={(e) => setMuacCm(Number(e.target.value))}
                className={`w-full bg-white border rounded-xl px-3 py-2.5 text-[20px] font-bold text-center font-mono focus:outline-none ${
                  muacCm < 11.5
                    ? 'border-red-400 text-red-700'
                    : muacCm < 12.5
                    ? 'border-amber-400 text-amber-700'
                    : 'border-emerald-400 text-emerald-700'
                }`}
              />
              <div className="text-[11px] text-center font-medium">
                {muacCm < 11.5 ? (
                  <span className="text-red-700 font-semibold">SAM Red Zone (&lt;11.5 cm)</span>
                ) : muacCm < 12.5 ? (
                  <span className="text-amber-700 font-semibold">MAM Yellow Zone (11.5–12.4 cm)</span>
                ) : (
                  <span className="text-emerald-700 font-semibold">Normal Green Zone (≥12.5 cm)</span>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-4 pt-2">
            <h4 className="text-[14px] font-semibold text-[#1d1d1f]">Dietary & Infection Context</h4>

            <div className="bg-[#fbfbfd] p-4 rounded-2xl border border-black/[0.05] space-y-2">
              <span className="text-[13px] text-[#1d1d1f]">1. Regular consumption of iron-rich foods?</span>
              <div className="grid grid-cols-3 gap-2">
                {(['YES', 'NO', 'NOT_SURE'] as const).map((opt) => (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => setIronRichDiet(opt)}
                    className={`py-2 rounded-xl text-[12px] font-medium transition-all ${
                      ironRichDiet === opt
                        ? 'bg-[#1d1d1f] text-white shadow-sm'
                        : 'bg-white border border-black/[0.08] text-[#6e6e73] hover:text-[#1d1d1f]'
                    }`}
                  >
                    {opt.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>

            <div className="bg-[#fbfbfd] p-4 rounded-2xl border border-black/[0.05] space-y-2">
              <span className="text-[13px] text-[#1d1d1f]">2. Albendazole deworming dose in past 6 months?</span>
              <div className="grid grid-cols-3 gap-2">
                {(['YES', 'NO', 'NOT_SURE'] as const).map((opt) => (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => setDewormedLast6Mos(opt)}
                    className={`py-2 rounded-xl text-[12px] font-medium transition-all ${
                      dewormedLast6Mos === opt
                        ? 'bg-[#1d1d1f] text-white shadow-sm'
                        : 'bg-white border border-black/[0.08] text-[#6e6e73] hover:text-[#1d1d1f]'
                    }`}
                  >
                    {opt.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-black/[0.06]">
            <button
              onClick={() => setCurrentStep(3)}
              className="apple-btn-secondary px-5 py-3 text-[13px]"
            >
              ← Back
            </button>

            <button
              onClick={handleStartAnalysis}
              className="apple-btn-accent px-7 py-3.5 text-[13px] inline-flex items-center gap-2 shadow-sm"
            >
              <Zap className="w-4 h-4 fill-current" />
              <span>Run Multimodal Analysis</span>
            </button>
          </div>
        </div>
      )}

      {/* STEP 5: ANALYSIS ANIMATION */}
      {currentStep === 5 && (
        <div className="bg-white rounded-[32px] p-12 border border-black/[0.06] space-y-6 shadow-sm text-center">
          <div className="w-14 h-14 rounded-full bg-[#00776b]/10 text-[#00776b] flex items-center justify-center mx-auto animate-pulse">
            <Activity className="w-7 h-7" />
          </div>

          <div className="space-y-1">
            <h3 className="text-[22px] font-semibold text-[#1d1d1f]">Evaluating Clinical Signals</h3>
            <p className="text-[13px] text-[#86868b]">Running on-device WHO deterministic safety evaluation...</p>
          </div>

          <div className="max-w-md mx-auto space-y-2 text-left text-[12px]">
            {[
              { id: 1, name: 'Optical Conjunctival Pallor Extraction' },
              { id: 2, name: 'WHO 2024 Hemoglobin Threshold Matching' },
              { id: 3, name: 'Anthropometric Growth Z-Score Calculation' },
              { id: 4, name: 'Longitudinal Trajectory Gradient' },
              { id: 5, name: 'Deterministic Safety Non-Downgrade Layer' },
            ].map((stage) => (
              <div
                key={stage.id}
                className={`p-3.5 rounded-xl border flex items-center justify-between transition-all ${
                  analysisStage >= stage.id
                    ? 'bg-[#fbfbfd] border-[#00776b]/40 text-[#1d1d1f]'
                    : 'bg-white border-black/[0.05] text-[#86868b]'
                }`}
              >
                <span>{stage.name}</span>
                {analysisStage >= stage.id ? (
                  <CheckCircle2 className="w-4 h-4 text-[#00776b]" />
                ) : (
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-300" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* STEP 6: SCREENING RESULT */}
      {currentStep === 6 && screeningResult && (
        <div className="bg-white rounded-[32px] p-8 border border-black/[0.06] shadow-sm space-y-8">
          
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-black/[0.06] pb-6">
            <div>
              <div className="flex items-center gap-2 text-[#00776b] text-[12px] font-semibold mb-1">
                <CheckCircle2 className="w-4 h-4" />
                <span>Screening Complete • Calibrated Result</span>
              </div>
              <h3 className="text-[28px] font-semibold text-[#1d1d1f] tracking-title">
                {beneficiary?.name}
              </h3>
              <p className="text-[13px] text-[#6e6e73]">
                {beneficiary?.category === 'child' ? `Age ${beneficiary?.ageYears}y` : 'Maternal ANC'} • Village: {beneficiary?.locationVillage}
              </p>
            </div>

            <span className="px-3.5 py-1.5 rounded-full text-[12px] font-semibold bg-[#f5f5f7] text-[#1d1d1f] self-start sm:self-auto">
              WHO 2024 Compliant
            </span>
          </div>

          {/* COMPREHENSIVE SCREENING SUMMARY & DUAL MODALITY TELEMETRY */}
          <ComprehensiveScreeningSummary
            screeningResult={screeningResult}
            beneficiary={beneficiary}
          />

          {/* Rule-Based Clinical Action & What To Do Next Section */}
          <WhatToDoNextCard
            screeningResult={screeningResult}
            beneficiary={beneficiary}
          />

          <SafetyDisclaimerBanner language={language} />

          <div className="flex justify-end gap-3 pt-2">
            <button
              onClick={() => onComplete(screeningResult)}
              className="apple-btn-primary px-8 py-3.5 text-[14px] shadow-sm"
            >
              Save & Complete Screening
            </button>
          </div>

        </div>
      )}

    </div>
  );
};
