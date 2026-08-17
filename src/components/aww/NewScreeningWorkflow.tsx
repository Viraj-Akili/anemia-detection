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
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Activity,
  ShieldAlert,
  Zap,
  Check,
  X,
  HeartPulse,
} from 'lucide-react';
import confetti from 'canvas-confetti';

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
  const [simulatedQuality, setSimulatedQuality] = React.useState<'GOOD' | 'BAD'>(initialQualityState);
  const [cameraRoiRegion, setCameraRoiRegion] = React.useState<'Palpebral Conjunctiva' | 'Nail Bed' | 'Palmar'>(
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
    setCurrentStep(5);

    for (let i = 1; i <= 6; i++) {
      setAnalysisStage(i);
      await new Promise((resolve) => setTimeout(resolve, 450));
    }

    const anthropometryData: AnthropometryData = { weightKg, heightCm, muacCm };
    const questionsData: ContextQuestionsData = {
      ironRichDiet,
      dewormedLast6Mos,
      recentIllnessFatigue,
    };

    const result = await screeningService.executeScreening({
      beneficiary,
      imageInput: { roiRegion: cameraRoiRegion, imageUri: capturedImage || undefined },
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
    confetti({ particleCount: 60, spread: 70, origin: { y: 0.6 } });
  };

  const stepsList = [
    { id: 1, label: 'Beneficiary' },
    { id: 2, label: 'Camera' },
    { id: 3, label: 'Quality Check' },
    { id: 4, label: 'Measurements' },
    { id: 5, label: 'Analysis' },
    { id: 6, label: 'Result' },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Form Wizard Progress Bar */}
      <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-600 font-semibold">
          <div className="flex items-center space-x-2">
            <HeartPulse className="w-4 h-4 text-emerald-700" />
            <span className="text-slate-900 font-bold">Guided Clinical Screening Wizard</span>
          </div>
          <button onClick={onCancel} className="text-slate-500 hover:text-slate-900">
            Cancel & Exit
          </button>
        </div>

        {/* Progress Stepper */}
        <div className="grid grid-cols-6 gap-2">
          {stepsList.map((step) => (
            <div key={step.id} className="space-y-1">
              <div
                className={`h-1.5 rounded-full transition-all ${
                  step.id === currentStep
                    ? 'bg-[#0f766e] shadow-sm'
                    : step.id < currentStep
                    ? 'bg-emerald-600'
                    : 'bg-slate-200'
                }`}
              />
              <div
                className={`text-[10px] text-center font-semibold truncate ${
                  step.id === currentStep ? 'text-[#0f766e] font-bold' : 'text-slate-500'
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
        <div className="bg-white rounded-2xl p-6 border border-slate-200 space-y-5 shadow-sm">
          <div>
            <h3 className="text-lg font-bold text-slate-900">Step 1 — Choose beneficiary for screening</h3>
            <p className="text-xs text-slate-500">Select a registered child or pregnant mother</p>
          </div>

          <div className="space-y-3">
            {beneficiaries.map((b) => (
              <div
                key={b.id}
                onClick={() => {
                  setBeneficiary(b);
                  setCurrentStep(2);
                }}
                className={`p-4 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                  beneficiary?.id === b.id
                    ? 'bg-emerald-50/80 border-emerald-600 text-slate-900'
                    : 'bg-slate-50 border-slate-200 text-slate-800 hover:bg-slate-100'
                }`}
              >
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-slate-900 text-base">{b.name}</span>
                    {b.abhaId && (
                      <span className="px-2 py-0.5 text-[10px] font-mono text-emerald-800 bg-emerald-100 border border-emerald-300 rounded">
                        {b.abhaId}
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    {b.category === 'child' ? `Child, Age ${b.ageYears} yrs` : `Pregnant Mother, Trimester ${b.trimester}`} • Village: {b.locationVillage}
                  </div>
                </div>
                <button className="px-4 py-2 rounded-xl bg-[#0f766e] hover:bg-[#0d9488] text-white text-xs font-bold shadow-sm">
                  Select →
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* STEP 2: CAMERA CAPTURE */}
      {currentStep === 2 && (
        <div className="bg-white rounded-2xl p-6 border border-slate-200 space-y-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-slate-900">Step 2 — Optical Image Capture</h3>
              <p className="text-xs text-slate-500">
                Target Region: <span className="text-[#0f766e] font-bold">{cameraRoiRegion}</span>
              </p>
            </div>

            <div className="flex items-center space-x-2 bg-slate-100 p-1 rounded-xl border border-slate-200">
              <button
                onClick={() => setCameraRoiRegion('Palpebral Conjunctiva')}
                className={`px-3 py-1 text-xs rounded-lg font-bold ${
                  cameraRoiRegion === 'Palpebral Conjunctiva'
                    ? 'bg-[#0f766e] text-white'
                    : 'text-slate-600'
                }`}
              >
                Lower Eyelid
              </button>
              <button
                onClick={() => setCameraRoiRegion('Nail Bed')}
                className={`px-3 py-1 text-xs rounded-lg font-bold ${
                  cameraRoiRegion === 'Nail Bed' ? 'bg-[#0f766e] text-white' : 'text-slate-600'
                }`}
              >
                Nail Bed
              </button>
            </div>
          </div>

          {/* Camera Frame Preview Container */}
          <div className="relative bg-slate-900 rounded-2xl border-2 border-emerald-500 overflow-hidden h-72 flex items-center justify-center">
            <div className="absolute inset-8 border-2 border-emerald-400 rounded-2xl roi-guide-emerald flex flex-col justify-between p-3 pointer-events-none z-10">
              <div className="flex justify-between items-center text-[10px] uppercase font-bold text-white bg-slate-900/90 px-2.5 py-1 rounded-md self-start border border-slate-700">
                Target: {cameraRoiRegion}
              </div>
              <div className="text-center text-xs font-bold text-white bg-slate-900/90 py-1 px-3 rounded-lg self-center border border-slate-700">
                Gently center {cameraRoiRegion} inside frame
              </div>
            </div>

            <img
              src={sampleImages[0].url}
              alt="Anatomy ROI Preview"
              className="w-full h-full object-cover opacity-80 filter contrast-110"
            />

            <div className="absolute bottom-3 left-3 right-3 z-20 flex items-center justify-between bg-slate-900/95 p-2.5 rounded-xl border border-slate-700 text-xs">
              <div className="flex items-center space-x-3 text-white">
                <span className="flex items-center text-emerald-400 font-semibold">
                  <Check className="w-3.5 h-3.5 mr-1" /> Good lighting ✓
                </span>
                <span className="flex items-center text-emerald-400 font-semibold">
                  <Check className="w-3.5 h-3.5 mr-1" /> ROI located ✓
                </span>
                <span
                  className={`flex items-center font-semibold ${
                    simulatedQuality === 'BAD' ? 'text-amber-300' : 'text-emerald-400'
                  }`}
                >
                  {simulatedQuality === 'BAD' ? (
                    <>
                      <X className="w-3.5 h-3.5 mr-1 text-amber-300" /> Motion detected ✕
                    </>
                  ) : (
                    <>
                      <Check className="w-3.5 h-3.5 mr-1" /> No motion ✓
                    </>
                  )}
                </span>
              </div>

              <button
                onClick={() =>
                  setSimulatedQuality((prev) => (prev === 'GOOD' ? 'BAD' : 'GOOD'))
                }
                className="px-2.5 py-1 rounded bg-slate-800 text-amber-300 text-[10px] font-bold border border-slate-600 hover:bg-slate-700"
              >
                Simulate: {simulatedQuality === 'GOOD' ? 'Good Capture' : 'Bad Capture'}
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            <button
              onClick={() => setCurrentStep(1)}
              className="px-4 py-2.5 rounded-xl bg-slate-100 text-slate-700 text-xs font-semibold hover:bg-slate-200"
            >
              ← Back
            </button>

            <button
              onClick={() => {
                setCapturedImage(sampleImages[0].url);
                setCurrentStep(3);
              }}
              className="flex items-center space-x-2 px-6 py-3 rounded-xl bg-[#0f766e] hover:bg-[#0d9488] text-white font-bold text-xs shadow-sm"
            >
              <Camera className="w-4 h-4" />
              <span>Capture Frame & Check Quality →</span>
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: IMAGE QUALITY GATE */}
      {currentStep === 3 && (
        <div className="bg-white rounded-2xl p-6 border border-slate-200 space-y-6 shadow-sm">
          <h3 className="text-lg font-bold text-slate-900">Step 3 — Image Quality Gate</h3>

          {simulatedQuality === 'GOOD' ? (
            <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-5 space-y-3">
              <div className="flex items-center space-x-3 text-emerald-800 font-bold text-base">
                <CheckCircle className="w-6 h-6 text-emerald-600" />
                <span>Image Quality: GOOD — Ready for Analysis</span>
              </div>
              <p className="text-xs text-emerald-900">
                Lighting, focus index, and eye mucosa framing meet clinical quality standards.
              </p>
            </div>
          ) : (
            <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 space-y-4">
              <div className="flex items-center space-x-3 text-amber-800 font-bold text-base">
                <AlertTriangle className="w-6 h-6 text-amber-600" />
                <span>Image Quality Insufficient</span>
              </div>

              <div className="space-y-1 text-xs text-amber-900">
                <div className="font-semibold">Possible Reasons:</div>
                <ul className="list-disc pl-4 space-y-1 text-slate-700">
                  <li>Blur / Defocus detected</li>
                  <li>Inadequate ambient lighting</li>
                  <li>Subject motion during capture</li>
                </ul>
              </div>

              <p className="text-[11px] text-amber-800 italic">
                Please retake the photo under clear lighting for optimal risk screening accuracy.
              </p>
            </div>
          )}

          <div className="flex items-center justify-between pt-4 border-t border-slate-100">
            <button
              onClick={() => setCurrentStep(2)}
              className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Retake Photo</span>
            </button>

            <button
              onClick={() => setCurrentStep(4)}
              className="flex items-center space-x-2 px-6 py-3 rounded-xl font-bold text-xs bg-[#0f766e] hover:bg-[#0d9488] text-white shadow-sm"
            >
              <span>{simulatedQuality === 'GOOD' ? 'Proceed to Measurements →' : 'Use Photo Anyway →'}</span>
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: ANTHROPOMETRY */}
      {currentStep === 4 && (
        <div className="bg-white rounded-2xl p-6 border border-slate-200 space-y-6 shadow-sm">
          <h3 className="text-lg font-bold text-slate-900">Step 4 — Measurements & Daily Context</h3>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
              <label className="text-xs text-slate-600 font-semibold">Weight (kg)</label>
              <input
                type="number"
                step="0.1"
                value={weightKg}
                onChange={(e) => setWeightKg(Number(e.target.value))}
                className="w-full bg-white border border-slate-300 rounded-xl px-3 py-2 text-lg font-extrabold text-slate-900 text-center"
              />
              <div className="text-[10px] text-slate-500 text-center">Digital Scale</div>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
              <label className="text-xs text-slate-600 font-semibold">Height / Length (cm)</label>
              <input
                type="number"
                step="0.5"
                value={heightCm}
                onChange={(e) => setHeightCm(Number(e.target.value))}
                className="w-full bg-white border border-slate-300 rounded-xl px-3 py-2 text-lg font-extrabold text-slate-900 text-center"
              />
              <div className="text-[10px] text-slate-500 text-center">Stadiometer / Infantometer</div>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
              <label className="text-xs text-slate-600 font-semibold">MUAC (cm)</label>
              <input
                type="number"
                step="0.1"
                value={muacCm}
                onChange={(e) => setMuacCm(Number(e.target.value))}
                className={`w-full bg-white border rounded-xl px-3 py-2 text-lg font-extrabold text-center ${
                  muacCm < 11.5
                    ? 'border-rose-500 text-rose-700'
                    : muacCm < 12.5
                    ? 'border-amber-500 text-amber-700'
                    : 'border-emerald-500 text-emerald-700'
                }`}
              />
              <div className="text-[10px] text-center font-semibold">
                {muacCm < 11.5 ? (
                  <span className="text-rose-700 font-bold">SAM Red Zone (&lt; 11.5 cm)</span>
                ) : muacCm < 12.5 ? (
                  <span className="text-amber-700">MAM Yellow Zone (&lt; 12.5 cm)</span>
                ) : (
                  <span className="text-emerald-700">Normal Green Zone</span>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-3 pt-2">
            <div className="text-xs font-bold text-slate-900">Daily Context Screening Questions</div>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
              <div className="text-xs text-slate-700 font-semibold">
                1. Regular intake of iron-dense foods reported?
              </div>
              <div className="grid grid-cols-3 gap-2">
                {(['YES', 'NO', 'NOT_SURE'] as const).map((opt) => (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => setIronRichDiet(opt)}
                    className={`py-2 text-xs font-bold rounded-xl border transition-all ${
                      ironRichDiet === opt
                        ? 'bg-[#0f766e] border-teal-700 text-white'
                        : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    {opt.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
              <div className="text-xs text-slate-700 font-semibold">
                2. Albendazole deworming dose received in past 6 months?
              </div>
              <div className="grid grid-cols-3 gap-2">
                {(['YES', 'NO', 'NOT_SURE'] as const).map((opt) => (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => setDewormedLast6Mos(opt)}
                    className={`py-2 text-xs font-bold rounded-xl border transition-all ${
                      dewormedLast6Mos === opt
                        ? 'bg-[#0f766e] border-teal-700 text-white'
                        : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    {opt.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-slate-100">
            <button
              onClick={() => setCurrentStep(3)}
              className="px-4 py-2.5 rounded-xl bg-slate-100 text-slate-700 text-xs font-semibold hover:bg-slate-200"
            >
              ← Back
            </button>

            <button
              onClick={handleStartAnalysis}
              className="flex items-center space-x-2 px-6 py-3 rounded-xl bg-[#0f766e] hover:bg-[#0d9488] text-white font-bold text-xs shadow-sm"
            >
              <Zap className="w-4 h-4 fill-white" />
              <span>Run Multimodal Analysis →</span>
            </button>
          </div>
        </div>
      )}

      {/* STEP 5: ANALYSIS */}
      {currentStep === 5 && (
        <div className="bg-white rounded-2xl p-8 border border-slate-200 space-y-6 shadow-sm text-center">
          <div className="w-16 h-16 rounded-2xl bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center justify-center mx-auto animate-pulse">
            <Activity className="w-8 h-8" />
          </div>

          <div className="space-y-1">
            <h3 className="text-xl font-bold text-slate-900">Multimodal Risk Engine</h3>
            <p className="text-xs text-slate-500">Evaluating clinical screening signals...</p>
          </div>

          <div className="max-w-md mx-auto space-y-2.5 text-left text-xs">
            {[
              { id: 1, name: 'Optical Image Quality & Illumination Gate' },
              { id: 2, name: 'Palpebral Conjunctiva Pallor Feature Signal' },
              { id: 3, name: 'Anthropometric WHO Z-score Evaluation' },
              { id: 4, name: 'Dietary & Context Risk Factors' },
              { id: 5, name: 'Longitudinal Visit Trajectory Analysis' },
              { id: 6, name: 'Clinical Safety Rules & Escalation Check' },
            ].map((stage) => (
              <div
                key={stage.id}
                className={`p-3 rounded-xl border flex items-center justify-between transition-all ${
                  analysisStage >= stage.id
                    ? 'bg-emerald-50 border-emerald-300 text-emerald-900'
                    : 'bg-slate-50 border-slate-200 text-slate-500'
                }`}
              >
                <span>{stage.name}</span>
                {analysisStage >= stage.id ? (
                  <CheckCircle className="w-4 h-4 text-emerald-600" />
                ) : (
                  <span className="w-2 h-2 rounded-full bg-slate-300" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* STEP 6: RESULT */}
      {currentStep === 6 && screeningResult && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
              <div>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-5 h-5 text-emerald-600" />
                  <h3 className="text-xl font-bold text-slate-900">SCREENING COMPLETE</h3>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  Beneficiary: <span className="text-slate-900 font-semibold">{beneficiary?.name}</span>
                </p>
              </div>

              <div className="text-right">
                <span className="px-3 py-1 text-xs font-bold rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200">
                  Multimodal Risk Evaluated
                </span>
              </div>
            </div>

            {/* 3 Core Risk Badges */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-1">
                <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider">
                  Anemia Risk
                </div>
                <div
                  className={`text-2xl font-black ${
                    screeningResult.anemiaRisk === 'ELEVATED'
                      ? 'text-rose-700'
                      : screeningResult.anemiaRisk === 'MODERATE'
                      ? 'text-amber-700'
                      : 'text-emerald-700'
                  }`}
                >
                  {screeningResult.anemiaRisk}
                </div>
                <div className="text-[10px] text-slate-500">Conjunctival Optical Signal</div>
              </div>

              <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-1">
                <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider">
                  Nutrition Risk
                </div>
                <div
                  className={`text-2xl font-black ${
                    screeningResult.nutritionRisk === 'HIGH'
                      ? 'text-rose-700'
                      : screeningResult.nutritionRisk === 'MODERATE'
                      ? 'text-amber-700'
                      : 'text-emerald-700'
                  }`}
                >
                  {screeningResult.nutritionRisk}
                </div>
                <div className="text-[10px] text-slate-500">WHO MUAC Standard</div>
              </div>

              <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-1">
                <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider">
                  Overall Priority
                </div>
                <div
                  className={`text-2xl font-black ${
                    screeningResult.overallPriority === 'HIGH'
                      ? 'text-rose-700'
                      : screeningResult.overallPriority === 'MODERATE'
                      ? 'text-amber-700'
                      : 'text-emerald-700'
                  }`}
                >
                  {screeningResult.overallPriority}
                </div>
                <div className="text-[10px] text-slate-500">Triage Priority</div>
              </div>
            </div>

            {screeningResult.triggeredSafetyRules.length > 0 && (
              <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 text-xs text-rose-900 space-y-1">
                <div className="flex items-center space-x-2 text-rose-800 font-bold">
                  <ShieldAlert className="w-4 h-4 text-rose-600" />
                  <span>Clinical Safety Rule Triggered</span>
                </div>
                {screeningResult.triggeredSafetyRules.map((rule, idx) => (
                  <p key={idx} className="text-rose-900">
                    {rule}
                  </p>
                ))}
              </div>
            )}

            <div className="space-y-3">
              <h4 className="text-sm font-bold text-slate-900">Why This Result? (Contributing Signals)</h4>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {screeningResult.contributingSignals.map((signal, idx) => (
                  <div
                    key={idx}
                    className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-1"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-slate-900">{signal.name}</span>
                      <span
                        className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                          signal.impact === 'CONCERN'
                            ? 'bg-rose-100 text-rose-800 border border-rose-200'
                            : signal.impact === 'NEUTRAL'
                            ? 'bg-amber-100 text-amber-800 border border-amber-200'
                            : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                        }`}
                      >
                        {signal.value}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-600 leading-relaxed">{signal.description}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Recommended Next Step */}
            <div className="bg-slate-50 p-5 rounded-2xl border border-slate-200 space-y-3">
              <div className="text-xs font-semibold text-emerald-800 uppercase tracking-wider">
                Recommended Next Step
              </div>
              <p className="text-sm font-bold text-slate-900 leading-relaxed">
                {screeningResult.recommendedAction}
              </p>

              <div className="flex flex-wrap gap-2 pt-2">
                <button
                  onClick={() => onComplete(screeningResult)}
                  className="px-4 py-2.5 rounded-xl bg-rose-700 hover:bg-rose-600 text-white font-bold text-xs shadow-sm"
                >
                  Flag for PHC Referral
                </button>

                <button
                  onClick={() => onComplete(screeningResult)}
                  className="px-4 py-2.5 rounded-xl bg-[#0f766e] hover:bg-[#0d9488] text-white font-bold text-xs shadow-sm"
                >
                  Schedule 14-Day Follow-Up
                </button>
              </div>
            </div>

            {/* User-requested Explicit Doctor Disclaimer */}
            <SafetyDisclaimerBanner language={language} />

            <div className="flex justify-end">
              <button
                onClick={() => onComplete(screeningResult)}
                className="px-6 py-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs shadow-sm"
              >
                Save & Complete Record
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
