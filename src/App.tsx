import React, { useState } from 'react';
import {
  Beneficiary,
  ScreeningResult,
  AnthropometryData,
  ContextQuestionsData,
  Category,
  Gender,
} from './types';
import { screeningService } from './services/screeningService';
import { ModelContractModal } from './components/common/ModelContractModal';
import { ResearchDossierModal } from './components/common/ResearchDossierModal';
import { SafetyDisclaimerBanner } from './components/common/SafetyDisclaimerBanner';
import { MalnutritionAIChatbot } from './components/chat/MalnutritionAIChatbot';
import { ClinicalDoubtAssistant, evaluateSymptomDoubt } from './components/doubt/ClinicalDoubtAssistant';
import { OpticalCaptureZone } from './components/scanner/OpticalCaptureZone';
import {
  Activity,
  Camera,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Plus,
  ShieldCheck,
  ShieldAlert,
  Zap,
  Check,
  WifiOff,
  Sliders,
  ChevronRight,
  BookOpen,
  Cpu,
  History,
  RotateCcw,
  Sparkles,
  MessageSquare,
  Scan,
  User,
  MessageCircleQuestion,
  HelpCircle,
  Stethoscope,
  Eye,
  Send,
} from 'lucide-react';

const COMMON_SYMPTOMS = [
  { id: 'fatigue', label: 'Unexplained Fatigue / Weakness', desc: 'Feeling worn out despite adequate sleep' },
  { id: 'dizziness', label: 'Dizziness or Lightheadedness', desc: 'Faintness or spinning sensation when standing' },
  { id: 'cold_hands', label: 'Cold Hands & Feet', desc: 'Extremities always cold or chilly' },
  { id: 'pale_eyelid', label: 'Pale Inner Eyelids or Nails', desc: 'Loss of healthy pink/red vascular color' },
  { id: 'heart_racing', label: 'Fast Heartbeat / Shortness of Breath', desc: 'Palpitations after minor exertion' },
  { id: 'pica_cravings', label: 'Ice or Starch Cravings (Pica)', desc: 'Compulsive desire to chew ice or non-foods' },
];

export function App() {
  // Top navigation view mode: 'scanner' | 'doubt' | 'chatbot'
  const [viewMode, setViewMode] = useState<'scanner' | 'doubt' | 'chatbot'>('scanner');

  // Scanner workflow stage: 'input' -> 'camera' -> 'symptoms' -> 'analyzing' -> 'result'
  const [stage, setStage] = useState<'input' | 'camera' | 'symptoms' | 'analyzing' | 'result'>('input');

  // Modals
  const [isModelContractOpen, setIsModelContractOpen] = useState(false);
  const [isResearchDossierOpen, setIsResearchDossierOpen] = useState(false);

  // Beneficiary Data
  const [name, setName] = useState('Person #1');
  const [category, setCategory] = useState<Category>('adult');
  const [ageYears, setAgeYears] = useState<number>(28);
  const [sex, setSex] = useState<Gender>('Female');
  const [trimester, setTrimester] = useState<1 | 2 | 3>(2);
  const [locationVillage, setLocationVillage] = useState('Urban Centre');

  // Camera & Image State
  const [cameraRoiRegion, setCameraRoiRegion] = useState<'Palpebral Conjunctiva' | 'Nail Bed'>('Palpebral Conjunctiva');
  const [simulatedQuality, setSimulatedQuality] = useState<'GOOD' | 'BAD'>('GOOD');
  const [capturedImage, setCapturedImage] = useState<string | null>(null);

  // Symptom Checklist & Doubt Query State
  const [selectedSymptoms, setSelectedSymptoms] = useState<string[]>(['fatigue', 'dizziness']);
  const [customDoubt, setCustomDoubt] = useState('');
  const [doubtAnalysis, setDoubtAnalysis] = useState<ReturnType<typeof evaluateSymptomDoubt> | null>(null);

  // Result & History State
  const [screeningResult, setScreeningResult] = useState<ScreeningResult | null>(null);
  const [analysisStep, setAnalysisStep] = useState(0);
  const [history, setHistory] = useState<Array<{ name: string; date: string; result: ScreeningResult }>>([]);

  const toggleSymptom = (id: string) => {
    setSelectedSymptoms((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  };

  // Quick Reset / Start New Screening
  const handleStartNewScreening = () => {
    setName(`Person #${history.length + 2}`);
    setCapturedImage(null);
    setScreeningResult(null);
    setAnalysisStep(0);
    setSelectedSymptoms([]);
    setCustomDoubt('');
    setDoubtAnalysis(null);
    setStage('input');
    setViewMode('scanner');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Run Optical & Clinical Screening Analysis
  const handleRunAnalysis = async () => {
    setStage('analyzing');
    window.scrollTo({ top: 0, behavior: 'smooth' });

    for (let i = 1; i <= 5; i++) {
      setAnalysisStep(i);
      await new Promise((r) => setTimeout(r, 380));
    }

    const currentBeneficiary: Beneficiary = {
      id: `BEN-${Date.now()}`,
      name: name.trim() || 'Patient',
      category,
      ageYears: ageYears || (category === 'child' ? 3 : 28),
      sex,
      isPregnant: category === 'pregnant',
      trimester: category === 'pregnant' ? trimester : undefined,
      locationVillage: locationVillage || 'Community Health Wing',
      anganwadiCentreId: 'AWC-1049281',
      anemiaRisk: 'LOW',
      nutritionRisk: 'LOW',
      overallPriority: 'LOW',
      trajectory: 'STABLE',
      lastVisitDate: new Date().toISOString().split('T')[0],
      visitHistory: [],
      isDemoData: false,
    };

    // Default neutral anthropometry data since user removed measurement requirement for anemia
    const anthropometryData: AnthropometryData = {
      weightKg: category === 'child' ? 14.0 : 60.0,
      heightCm: category === 'child' ? 95.0 : 165.0,
      muacCm: category === 'child' ? 13.5 : 26.0,
    };

    const questionsData: ContextQuestionsData = {
      ironRichDiet: selectedSymptoms.includes('fatigue') ? 'NO' : 'YES',
      dewormedLast6Mos: 'YES',
      recentIllnessFatigue: selectedSymptoms.length > 0 ? 'YES' : 'NO',
    };

    const res = await screeningService.executeScreening({
      beneficiary: currentBeneficiary,
      imageInput: { roiRegion: cameraRoiRegion, imageUri: capturedImage || undefined },
      anthropometry: anthropometryData,
      questions: questionsData,
      simulatedImageQuality: simulatedQuality,
    });

    // Enhance contributing signals with user's symptoms
    if (selectedSymptoms.length > 0) {
      res.contributingSignals.unshift({
        name: 'Reported Clinical Symptoms',
        category: 'DIET',
        value: `${selectedSymptoms.length} Symptoms Flagged`,
        impact: selectedSymptoms.length >= 2 ? 'CONCERN' : 'NEUTRAL',
        description: `Patient reported: ${selectedSymptoms.map((s) => COMMON_SYMPTOMS.find((cs) => cs.id === s)?.label).join(', ')}.`,
      });
    }

    setScreeningResult(res);
    setHistory((prev) => [
      {
        name: currentBeneficiary.name,
        date: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        result: res,
      },
      ...prev,
    ]);
    setStage('result');
  };

  return (
    <div className="min-h-screen bg-[#fbfbfd] text-[#1d1d1f] flex flex-col font-sans selection:bg-[#00776b] selection:text-white">
      
      {/* Top Minimal Apple Header */}
      <header className="sticky top-0 z-40 apple-glass border-b border-black/[0.06] py-3.5 px-6">
        <div className="max-w-[980px] mx-auto flex items-center justify-between">
          
          {/* Logo & Product Tag */}
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-[#1d1d1f] flex items-center justify-center text-white shadow-sm">
              <Activity className="w-4 h-4 stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-[17px] tracking-tight text-[#1d1d1f]">PRAHARI</span>
                <span className="px-2 py-0.5 text-[10px] uppercase font-semibold rounded-full bg-black/[0.05] text-[#6e6e73]">
                  Non-Invasive Sentinel
                </span>
              </div>
              <p className="text-[11px] text-[#86868b] hidden sm:block">
                Optical Conjunctiva Anemia Screening & Symptom Clarifier
              </p>
            </div>
          </div>

          {/* Right Action Tools */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-[11px] font-medium">
              <WifiOff className="w-3 h-3" />
              <span>Offline Ready</span>
            </div>

            <button
              onClick={() => setIsModelContractOpen(true)}
              className="p-2 rounded-full bg-white border border-black/[0.08] text-[#6e6e73] hover:text-[#1d1d1f] transition-colors"
              title="Inspect Model Contract"
            >
              <Cpu className="w-3.5 h-3.5" />
            </button>

            <button
              onClick={() => setIsResearchDossierOpen(true)}
              className="p-2 rounded-full bg-white border border-black/[0.08] text-[#6e6e73] hover:text-[#1d1d1f] transition-colors"
              title="Research Dossier"
            >
              <BookOpen className="w-3.5 h-3.5" />
            </button>

            <button
              onClick={handleStartNewScreening}
              className="apple-btn-accent px-4 py-1.5 text-[12px] inline-flex items-center gap-1.5 shadow-sm cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5 stroke-[2.5]" />
              <span>New Screening</span>
            </button>
          </div>

        </div>
      </header>

      {/* Main Content Container */}
      <main className="flex-1 max-w-[840px] w-full mx-auto px-6 py-8 space-y-6">
        
        {/* Apple 3-Mode Segmented Switcher */}
        <div className="flex items-center p-1 rounded-2xl bg-black/[0.05] border border-black/[0.04] max-w-lg mx-auto">
          <button
            onClick={() => setViewMode('scanner')}
            className={`flex-1 py-2.5 rounded-xl text-[13px] font-medium transition-all flex items-center justify-center gap-1.5 ${
              viewMode === 'scanner'
                ? 'bg-white text-[#1d1d1f] shadow-sm font-semibold'
                : 'text-[#6e6e73] hover:text-[#1d1d1f]'
            }`}
          >
            <Scan className="w-4 h-4 text-[#00776b]" />
            <span>Optical Anemia Scan</span>
          </button>

          <button
            onClick={() => setViewMode('doubt')}
            className={`flex-1 py-2.5 rounded-xl text-[13px] font-medium transition-all flex items-center justify-center gap-1.5 ${
              viewMode === 'doubt'
                ? 'bg-white text-[#1d1d1f] shadow-sm font-semibold'
                : 'text-[#6e6e73] hover:text-[#1d1d1f]'
            }`}
          >
            <MessageCircleQuestion className="w-4 h-4 text-[#00776b]" />
            <span>Ask a Doubt</span>
          </button>

          <button
            onClick={() => setViewMode('chatbot')}
            className={`flex-1 py-2.5 rounded-xl text-[13px] font-medium transition-all flex items-center justify-center gap-1.5 ${
              viewMode === 'chatbot'
                ? 'bg-white text-[#1d1d1f] shadow-sm font-semibold'
                : 'text-[#6e6e73] hover:text-[#1d1d1f]'
            }`}
          >
            <MessageSquare className="w-4 h-4 text-[#00776b]" />
            <span>Nutrition Chat</span>
          </button>
        </div>

        {/* ========================================================================= */}
        {/* VIEW 2: SYMPTOM DOUBT RESOLUTION SYSTEM                                   */}
        {/* ========================================================================= */}
        {viewMode === 'doubt' && (
          <ClinicalDoubtAssistant
            onStartOpticalScan={() => {
              setViewMode('scanner');
              setStage('camera');
            }}
          />
        )}

        {/* ========================================================================= */}
        {/* VIEW 3: AI MALNUTRITION CHATBOT                                           */}
        {/* ========================================================================= */}
        {viewMode === 'chatbot' && (
          <MalnutritionAIChatbot
            onProceedToOpticalScan={() => {
              setViewMode('scanner');
              setStage('camera');
            }}
          />
        )}

        {/* ========================================================================= */}
        {/* VIEW 1: OPTICAL ANEMIA SCREENING WIZARD (NO MEASUREMENTS)                 */}
        {/* ========================================================================= */}
        {viewMode === 'scanner' && (
          <div className="space-y-6">
            
            {/* Step Indicator Pills */}
            <div className="flex items-center justify-between gap-2 p-1.5 rounded-2xl bg-black/[0.04] border border-black/[0.04] text-[12px]">
              <button
                onClick={() => setStage('input')}
                className={`flex-1 py-2 rounded-xl font-medium transition-all ${
                  stage === 'input' ? 'bg-white text-[#1d1d1f] shadow-sm font-semibold' : 'text-[#86868b] hover:text-[#1d1d1f]'
                }`}
              >
                1. Patient Cohort
              </button>
              <button
                onClick={() => setStage('camera')}
                className={`flex-1 py-2 rounded-xl font-medium transition-all ${
                  stage === 'camera' ? 'bg-white text-[#1d1d1f] shadow-sm font-semibold' : 'text-[#86868b] hover:text-[#1d1d1f]'
                }`}
              >
                2. Optical Capture
              </button>
              <button
                onClick={() => setStage('symptoms')}
                className={`flex-1 py-2 rounded-xl font-medium transition-all ${
                  stage === 'symptoms' ? 'bg-white text-[#1d1d1f] shadow-sm font-semibold' : 'text-[#86868b] hover:text-[#1d1d1f]'
                }`}
              >
                3. Symptoms & Doubts
              </button>
              <button
                disabled={!screeningResult}
                onClick={() => setStage('result')}
                className={`flex-1 py-2 rounded-xl font-medium transition-all ${
                  stage === 'result' ? 'bg-white text-[#1d1d1f] shadow-sm font-semibold' : 'text-[#86868b] disabled:opacity-40'
                }`}
              >
                4. Triage Result
              </button>
            </div>

            {/* STAGE 1: PATIENT DEMOGRAPHIC */}
            {stage === 'input' && (
              <div className="bg-white rounded-[32px] p-8 border border-black/[0.06] shadow-sm space-y-6">
                <div>
                  <span className="text-[12px] font-mono text-[#86868b] uppercase tracking-wider">Step 01 of 03</span>
                  <h2 className="text-[28px] font-semibold text-[#1d1d1f] tracking-title mt-1">
                    Patient Demographic Setup
                  </h2>
                  <p className="text-[14px] text-[#6e6e73]">
                    Select demographic cohort to apply WHO hemoglobin threshold cutoffs.
                  </p>
                </div>

                <div className="space-y-5">
                  <div>
                    <label className="text-[12px] font-semibold text-[#1d1d1f] block mb-1.5">
                      Patient Name or ID
                    </label>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="e.g. Rahul Sharma or ID #1042"
                      className="w-full px-4 py-3 rounded-2xl border border-black/[0.08] text-[15px] focus:outline-none focus:border-[#00776b] transition-colors"
                    />
                  </div>

                  {/* 4-Pill Demographic Category Selector */}
                  <div>
                    <label className="text-[12px] font-semibold text-[#1d1d1f] block mb-1.5">
                      Demographic Cohort
                    </label>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 p-1.5 rounded-2xl bg-[#f5f5f7] border border-black/[0.04]">
                      <button
                        type="button"
                        onClick={() => {
                          setCategory('adult');
                          setAgeYears(30);
                        }}
                        className={`py-2.5 rounded-xl text-[12px] font-medium transition-all ${
                          category === 'adult' ? 'bg-white text-[#1d1d1f] shadow-sm font-semibold' : 'text-[#6e6e73]'
                        }`}
                      >
                        Adult (18–64y)
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setCategory('child');
                          setAgeYears(3);
                        }}
                        className={`py-2.5 rounded-xl text-[12px] font-medium transition-all ${
                          category === 'child' ? 'bg-white text-[#1d1d1f] shadow-sm font-semibold' : 'text-[#6e6e73]'
                        }`}
                      >
                        Child (6m–11y)
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setCategory('pregnant');
                          setAgeYears(26);
                          setSex('Female');
                        }}
                        className={`py-2.5 rounded-xl text-[12px] font-medium transition-all ${
                          category === 'pregnant' ? 'bg-white text-[#1d1d1f] shadow-sm font-semibold' : 'text-[#6e6e73]'
                        }`}
                      >
                        Pregnant Mother
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setCategory('elderly');
                          setAgeYears(70);
                        }}
                        className={`py-2.5 rounded-xl text-[12px] font-medium transition-all ${
                          category === 'elderly' ? 'bg-white text-[#1d1d1f] shadow-sm font-semibold' : 'text-[#6e6e73]'
                        }`}
                      >
                        Elderly (65+y)
                      </button>
                    </div>
                  </div>

                  {/* Biological Sex & Age */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                    {category !== 'pregnant' && (
                      <div>
                        <label className="text-[12px] font-semibold text-[#1d1d1f] block mb-1.5">
                          Biological Sex
                        </label>
                        <div className="grid grid-cols-2 gap-2 p-1 rounded-2xl bg-[#f5f5f7] border border-black/[0.04]">
                          <button
                            type="button"
                            onClick={() => setSex('Male')}
                            className={`py-2 rounded-xl text-[12px] font-medium transition-all ${
                              sex === 'Male' ? 'bg-white text-[#1d1d1f] shadow-sm font-semibold' : 'text-[#6e6e73]'
                            }`}
                          >
                            Male (Hb &lt;13.0 g/dL)
                          </button>
                          <button
                            type="button"
                            onClick={() => setSex('Female')}
                            className={`py-2 rounded-xl text-[12px] font-medium transition-all ${
                              sex === 'Female' ? 'bg-white text-[#1d1d1f] shadow-sm font-semibold' : 'text-[#6e6e73]'
                            }`}
                          >
                            Female (Hb &lt;12.0 g/dL)
                          </button>
                        </div>
                      </div>
                    )}

                    <div>
                      <label className="text-[12px] font-semibold text-[#1d1d1f] block mb-1.5">
                        Age (Years)
                      </label>
                      <input
                        type="number"
                        min={category === 'child' ? 0.5 : category === 'elderly' ? 65 : 18}
                        max={110}
                        step={category === 'child' ? 0.5 : 1}
                        value={ageYears}
                        onChange={(e) => setAgeYears(parseFloat(e.target.value) || 0)}
                        className="w-full px-4 py-2.5 rounded-2xl border border-black/[0.08] text-[15px] focus:outline-none focus:border-[#00776b]"
                      />
                    </div>

                    {category === 'pregnant' && (
                      <div>
                        <label className="text-[12px] font-semibold text-[#1d1d1f] block mb-1.5">
                          Pregnancy Trimester
                        </label>
                        <select
                          value={trimester}
                          onChange={(e) => setTrimester(parseInt(e.target.value) as 1 | 2 | 3)}
                          className="w-full px-4 py-2.5 rounded-2xl border border-black/[0.08] text-[14px] bg-white focus:outline-none focus:border-[#00776b]"
                        >
                          <option value={1}>1st Trimester (Hb &lt; 11.0 g/dL)</option>
                          <option value={2}>2nd Trimester (Hb &lt; 10.5 g/dL)</option>
                          <option value={3}>3rd Trimester (Hb &lt; 11.0 g/dL)</option>
                        </select>
                      </div>
                    )}
                  </div>
                </div>

                <div className="pt-4 flex justify-end">
                  <button
                    onClick={() => setStage('camera')}
                    className="apple-btn-accent px-7 py-3.5 text-[14px] inline-flex items-center gap-2 shadow-sm"
                  >
                    <span>Proceed to Optical Capture</span>
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {/* STAGE 2: OPTICAL CAPTURE (NO STOCK WOMAN PHOTO) */}
            {stage === 'camera' && (
              <div className="bg-white rounded-[32px] p-8 border border-black/[0.06] shadow-sm space-y-6">
                <OpticalCaptureZone
                  roiRegion={cameraRoiRegion}
                  onChangeRoi={(roi) => setCameraRoiRegion(roi)}
                  capturedImage={capturedImage}
                  onImageCaptured={(img) => setCapturedImage(img)}
                  simulatedQuality={simulatedQuality}
                  onToggleQuality={() => setSimulatedQuality((q) => (q === 'GOOD' ? 'BAD' : 'GOOD'))}
                />

                <div className="flex items-center justify-between pt-2 border-t border-black/[0.06]">
                  <button
                    onClick={() => setStage('input')}
                    className="apple-btn-secondary px-5 py-3 text-[13px]"
                  >
                    ← Back
                  </button>

                  <button
                    onClick={() => setStage('symptoms')}
                    className="apple-btn-accent px-7 py-3.5 text-[13px] inline-flex items-center gap-2 shadow-sm font-medium"
                  >
                    <span>Proceed to Symptoms & Doubts</span>
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {/* STAGE 3: SYMPTOMS CHECKLIST & LIVE DOUBT CLARIFIER */}
            {stage === 'symptoms' && (
              <div className="bg-white rounded-[32px] p-8 border border-black/[0.06] shadow-sm space-y-8">
                <div>
                  <span className="text-[12px] font-mono text-[#86868b] uppercase tracking-wider">Step 03 of 03</span>
                  <h2 className="text-[28px] font-semibold text-[#1d1d1f] tracking-title mt-1">
                    Symptoms Checklist & Doubt Clarifier
                  </h2>
                  <p className="text-[14px] text-[#6e6e73]">
                    Select any symptoms experienced, or ask a doubt to check its clinical relevance to anemia.
                  </p>
                </div>

                {/* Common Symptoms Checklist */}
                <div className="space-y-3">
                  <label className="text-[12px] font-semibold text-[#1d1d1f] uppercase tracking-wider">
                    Select Experienced Symptoms (Optional):
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {COMMON_SYMPTOMS.map((sym) => {
                      const isChecked = selectedSymptoms.includes(sym.id);
                      return (
                        <div
                          key={sym.id}
                          onClick={() => toggleSymptom(sym.id)}
                          className={`p-4 rounded-2xl border transition-all cursor-pointer flex items-start gap-3 ${
                            isChecked
                              ? 'bg-[#fbfbfd] border-[#00776b] ring-1 ring-[#00776b]/20 shadow-sm'
                              : 'bg-white border-black/[0.06] hover:bg-[#fbfbfd]'
                          }`}
                        >
                          <div
                            className={`w-5 h-5 rounded-lg flex items-center justify-center shrink-0 mt-0.5 transition-all ${
                              isChecked
                                ? 'bg-[#00776b] text-white shadow-sm'
                                : 'border border-black/[0.15] bg-white'
                            }`}
                          >
                            {isChecked && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                          </div>
                          <div>
                            <span className="font-semibold text-[13px] text-[#1d1d1f] block">{sym.label}</span>
                            <span className="text-[12px] text-[#6e6e73]">{sym.desc}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Inline Symptom Doubt Query Box */}
                <div className="p-6 rounded-[28px] bg-[#fbfbfd] border border-black/[0.06] space-y-4">
                  <div className="flex items-center gap-2">
                    <HelpCircle className="w-4 h-4 text-[#00776b]" />
                    <span className="text-[13px] font-semibold text-[#1d1d1f]">
                      Have a specific doubt or unusual symptom?
                    </span>
                  </div>

                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={customDoubt}
                      onChange={(e) => setCustomDoubt(e.target.value)}
                      placeholder="e.g. 'I feel dizzy after standing' or 'My fingernails have dents'"
                      className="flex-1 px-4 py-3 bg-white rounded-2xl border border-black/[0.08] text-[14px] focus:outline-none focus:border-[#00776b]"
                    />
                    <button
                      type="button"
                      onClick={() => {
                        if (customDoubt.trim()) {
                          setDoubtAnalysis(evaluateSymptomDoubt(customDoubt.trim()));
                        }
                      }}
                      disabled={!customDoubt.trim()}
                      className="apple-btn-secondary px-5 py-3 text-[13px] font-medium disabled:opacity-40"
                    >
                      Check Doubt
                    </button>
                  </div>

                  {doubtAnalysis && (
                    <div className="p-4 rounded-2xl bg-white border border-black/[0.06] space-y-2 text-[13px] animate-in fade-in">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-[#1d1d1f]">{doubtAnalysis.headline}</span>
                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                          {doubtAnalysis.relevanceLevel.replace('_', ' ')}
                        </span>
                      </div>
                      <p className="text-[#6e6e73] leading-relaxed">{doubtAnalysis.explanation}</p>
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-black/[0.06]">
                  <button
                    onClick={() => setStage('camera')}
                    className="apple-btn-secondary px-5 py-3 text-[13px]"
                  >
                    ← Back
                  </button>

                  <button
                    onClick={handleRunAnalysis}
                    className="apple-btn-accent px-8 py-3.5 text-[14px] inline-flex items-center gap-2 shadow-sm font-medium"
                  >
                    <Zap className="w-4 h-4 fill-current" />
                    <span>Run Optical Anemia Assessment</span>
                  </button>
                </div>
              </div>
            )}

            {/* STAGE 4: ANALYZING */}
            {stage === 'analyzing' && (
              <div className="bg-white rounded-[32px] p-12 border border-black/[0.06] shadow-sm space-y-6 text-center">
                <div className="w-14 h-14 rounded-full bg-[#00776b]/10 text-[#00776b] flex items-center justify-center mx-auto animate-pulse">
                  <Activity className="w-7 h-7" />
                </div>

                <div className="space-y-1">
                  <h3 className="text-[22px] font-semibold text-[#1d1d1f]">Evaluating Optical & Clinical Signals</h3>
                  <p className="text-[13px] text-[#86868b]">Running on-device WHO optical pallor matching for {category} cohort...</p>
                </div>

                <div className="max-w-md mx-auto space-y-2 text-left text-[12px]">
                  {[
                    { id: 1, name: 'Palpebral Conjunctiva Pallor Feature Extraction' },
                    { id: 2, name: `WHO 2024 Threshold Matching (${category === 'child' ? 'Pediatric' : sex === 'Male' ? 'Adult Male <13g/dL' : 'Adult Female <12g/dL'})` },
                    { id: 3, name: `Clinical Symptom Matrix Correlation (${selectedSymptoms.length} Reported)` },
                    { id: 4, name: 'Deterministic Safety Non-Downgrade Layer' },
                    { id: 5, name: 'Generating Plain-Language Explainability' },
                  ].map((s) => (
                    <div
                      key={s.id}
                      className={`p-3.5 rounded-xl border flex items-center justify-between transition-all ${
                        analysisStep >= s.id
                          ? 'bg-[#fbfbfd] border-[#00776b]/40 text-[#1d1d1f]'
                          : 'bg-white border-black/[0.05] text-[#86868b]'
                      }`}
                    >
                      <span>{s.name}</span>
                      {analysisStep >= s.id ? (
                        <CheckCircle2 className="w-4 h-4 text-[#00776b]" />
                      ) : (
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-300" />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* STAGE 5: RESULT */}
            {stage === 'result' && screeningResult && (
              <div className="bg-white rounded-[32px] p-8 border border-black/[0.06] shadow-sm space-y-8">
                
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-black/[0.06] pb-6">
                  <div>
                    <div className="flex items-center gap-2 text-[#00776b] text-[12px] font-semibold mb-1">
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Point-of-Care Optical Assessment Complete</span>
                    </div>
                    <h3 className="text-[28px] font-semibold text-[#1d1d1f] tracking-title">
                      {name}
                    </h3>
                    <p className="text-[13px] text-[#6e6e73]">
                      {category === 'child'
                        ? `Child, Age ${ageYears}y`
                        : category === 'pregnant'
                        ? `Pregnant Mother (Trimester ${trimester})`
                        : category === 'elderly'
                        ? `Elderly (${sex}, Age ${ageYears}y)`
                        : `Adult (${sex}, Age ${ageYears}y)`} • {locationVillage}
                    </p>
                  </div>

                  <button
                    onClick={handleStartNewScreening}
                    className="apple-btn-accent px-5 py-2.5 text-[13px] inline-flex items-center gap-1.5 shadow-sm self-start sm:self-auto"
                  >
                    <Plus className="w-3.5 h-3.5 stroke-[2.5]" />
                    <span>Screen Next Person</span>
                  </button>
                </div>

                {/* 3 Core Result Chips */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="bg-[#fbfbfd] p-5 rounded-2xl border border-black/[0.06] space-y-1">
                    <span className="text-[11px] text-[#86868b] uppercase font-medium">Anemia Risk</span>
                    <div
                      className={`text-[26px] font-bold font-mono ${
                        screeningResult.anemiaRisk === 'ELEVATED'
                          ? 'text-red-700'
                          : screeningResult.anemiaRisk === 'MODERATE'
                          ? 'text-amber-700'
                          : 'text-[#00776b]'
                      }`}
                    >
                      {screeningResult.anemiaRisk}
                    </div>
                    <p className="text-[11px] text-[#86868b]">Optical Conjunctival Pallor</p>
                  </div>

                  <div className="bg-[#fbfbfd] p-5 rounded-2xl border border-black/[0.06] space-y-1">
                    <span className="text-[11px] text-[#86868b] uppercase font-medium">Symptom Load</span>
                    <div className="text-[26px] font-bold font-mono text-[#1d1d1f]">
                      {selectedSymptoms.length} Flagged
                    </div>
                    <p className="text-[11px] text-[#86868b]">Reported Clinical Signs</p>
                  </div>

                  <div className="bg-[#fbfbfd] p-5 rounded-2xl border border-black/[0.06] space-y-1">
                    <span className="text-[11px] text-[#86868b] uppercase font-medium">Overall Triage</span>
                    <div
                      className={`text-[26px] font-bold font-mono ${
                        screeningResult.overallPriority === 'HIGH'
                          ? 'text-red-700'
                          : screeningResult.overallPriority === 'MODERATE'
                          ? 'text-amber-700'
                          : 'text-[#00776b]'
                      }`}
                    >
                      {screeningResult.overallPriority}
                    </div>
                    <p className="text-[11px] text-[#86868b]">Triage Priority</p>
                  </div>
                </div>

                {/* Safety Rule Triggered Alert */}
                {screeningResult.triggeredSafetyRules.length > 0 && (
                  <div className="bg-red-50/80 border border-red-200 rounded-2xl p-5 text-[12px] text-red-900 space-y-1">
                    <div className="flex items-center gap-2 font-semibold text-red-800 text-[13px]">
                      <ShieldAlert className="w-4 h-4 text-red-600" />
                      <span>Deterministic WHO Safety Escalation Active</span>
                    </div>
                    {screeningResult.triggeredSafetyRules.map((rule, idx) => (
                      <p key={idx}>{rule}</p>
                    ))}
                  </div>
                )}

                {/* Contributing Signals & Explainability */}
                <div className="space-y-3">
                  <h4 className="text-[15px] font-semibold text-[#1d1d1f]">Contributing Signals & Clinical Explainability</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {screeningResult.contributingSignals.map((signal, idx) => (
                      <div key={idx} className="bg-[#fbfbfd] p-4 rounded-2xl border border-black/[0.05] space-y-1">
                        <div className="flex items-center justify-between text-[12px]">
                          <span className="font-semibold text-[#1d1d1f]">{signal.name}</span>
                          <span
                            className={`px-2 py-0.5 text-[10px] font-semibold rounded-full ${
                              signal.impact === 'CONCERN'
                                ? 'bg-red-50 text-red-800'
                                : 'bg-emerald-50 text-emerald-800'
                            }`}
                          >
                            {signal.value}
                          </span>
                        </div>
                        <p className="text-[12px] text-[#6e6e73]">{signal.description}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recommended Action */}
                <div className="bg-[#f5f5f7] p-6 rounded-2xl border border-black/[0.05] space-y-2">
                  <span className="text-[11px] font-semibold text-[#00776b] uppercase tracking-wider">
                    Clinical Recommendation
                  </span>
                  <p className="text-[15px] font-semibold text-[#1d1d1f]">
                    {screeningResult.recommendedAction}
                  </p>
                </div>

                <SafetyDisclaimerBanner />

                <div className="flex justify-end gap-3 pt-2">
                  <button
                    onClick={handleStartNewScreening}
                    className="apple-btn-primary px-8 py-3.5 text-[14px] shadow-sm font-medium"
                  >
                    Start Another Screening
                  </button>
                </div>

              </div>
            )}

            {/* RECENT SESSION LOGS */}
            {history.length > 0 && (
              <div className="bg-white rounded-[32px] p-8 border border-black/[0.06] shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <History className="w-4 h-4 text-[#86868b]" />
                    <h3 className="text-[16px] font-semibold text-[#1d1d1f]">Session Screening Log</h3>
                  </div>
                  <span className="text-[11px] text-[#86868b] font-mono">{history.length} completed</span>
                </div>

                <div className="space-y-2.5">
                  {history.map((item, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-2xl bg-[#fbfbfd] border border-black/[0.04] flex items-center justify-between text-[13px]"
                    >
                      <div>
                        <span className="font-semibold text-[#1d1d1f]">{item.name}</span>
                        <span className="text-[#86868b] ml-2 font-mono text-[11px]">at {item.date}</span>
                      </div>
                      <span
                        className={`px-2.5 py-0.5 text-[11px] font-semibold rounded-full ${
                          item.result.overallPriority === 'HIGH'
                            ? 'bg-red-50 text-red-800'
                            : item.result.overallPriority === 'MODERATE'
                            ? 'bg-amber-50 text-amber-800'
                            : 'bg-emerald-50 text-emerald-800'
                        }`}
                      >
                        {item.result.overallPriority} Priority
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

      </main>

      {/* Clean Apple Footer */}
      <footer className="border-t border-black/[0.06] bg-[#f5f5f7] py-8 text-center text-[12px] text-[#86868b]">
        <p className="max-w-[840px] mx-auto px-6">
          PRAHARI Health Sentinel • WHO 2024 Pediatric, Maternal & Adult Hemoglobin Thresholds • Non-Invasive Optical Screening
        </p>
      </footer>

      {/* Shared Modals */}
      <ModelContractModal
        isOpen={isModelContractOpen}
        onClose={() => setIsModelContractOpen(false)}
      />

      <ResearchDossierModal
        isOpen={isResearchDossierOpen}
        onClose={() => setIsResearchDossierOpen(false)}
      />

    </div>
  );
}

export default App;
