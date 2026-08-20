import React, { useState, useEffect, useRef } from 'react';
import {
  Bot,
  User,
  Sparkles,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  ArrowRight,
  ShieldCheck,
  ChevronRight,
  HeartPulse,
  Scale,
  Activity,
  Check,
  X,
  Stethoscope,
  ClipboardList,
  AlertCircle,
} from 'lucide-react';

export interface QuestionOption {
  label: string;
  subtext?: string;
  points: number; // Internal scoring only (hidden from UI)
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
  selectedOption: string;
  statusLabel: string;
  status: 'HEALTHY' | 'BORDERLINE' | 'UNHEALTHY' | 'CRITICAL';
}

export interface ClinicalActionItem {
  step: string;
  title: string;
  description: string;
  isUrgent?: boolean;
}

export interface NutritionDiagnosisReport {
  rating: 'HEALTHY' | 'MILD_DEFICIT' | 'UNHEALTHY' | 'CRITICALLY_UNHEALTHY';
  ratingLabel: string;
  badgeText: string;
  badgeColor: string;
  clinicalImpression: string;
  physiologicalImpact: string;
  factors: FactorBreakdown[];
  actionItems: ClinicalActionItem[];
  protocolName: string;
}

export interface ChatMessage {
  id: string;
  sender: 'ai' | 'user';
  text: string;
  timestamp: string;
  questionKey?: string;
  options?: QuestionOption[];
  isDiagnosis?: boolean;
  diagnosisData?: NutritionDiagnosisReport;
}

interface MalnutritionAIChatbotProps {
  onProceedToOpticalScan?: () => void;
}

const QUESTIONS_TREE: NutritionQuestion[] = [
  {
    key: 'demographic',
    title: 'Demographic Group',
    prompt: "Hello. I will evaluate nutritional health and potential malnutrition risk based on clinical guidelines.\n\nFirst, who is being evaluated?",
    options: [
      { label: 'Adult (18–64 years)', points: 0, healthLevel: 'HEALTHY' },
      { label: 'Child (2–11 years)', points: 0, healthLevel: 'HEALTHY' },
      { label: 'Infant / Toddler (6–23 months)', points: 0, healthLevel: 'HEALTHY' },
      { label: 'Pregnant / Lactating Mother', points: 0, healthLevel: 'HEALTHY' },
      { label: 'Elderly Senior (65+ years)', points: 0, healthLevel: 'HEALTHY' },
    ],
  },
  {
    key: 'appetite',
    title: 'Appetite & Food Intake',
    prompt: "How has appetite and solid food intake been over the past 7 days?",
    options: [
      {
        label: 'Normal & Active Appetite',
        subtext: 'Consistently eating full meals with healthy hunger cues',
        points: 25,
        healthLevel: 'HEALTHY',
      },
      {
        label: 'Reduced Food Intake',
        subtext: 'Eating only ~half of usual meals, occasional food refusal',
        points: 10,
        healthLevel: 'BORDERLINE',
      },
      {
        label: 'Poor / Refusing Solids & Lethargic',
        subtext: 'Severe lack of appetite, refusing feeds, constant sluggishness',
        points: 0,
        healthLevel: 'CRITICAL',
      },
    ],
  },
  {
    key: 'physical_signs',
    title: 'Physical & Muscle Signs',
    prompt: "Do you observe any visible swelling in both feet/legs (bilateral pitting edema), visible severe thinness (ribs showing), or muscle wasting?",
    options: [
      {
        label: 'No Visible Swelling or Severe Wasting',
        subtext: 'Normal physical posture and adequate muscle tone',
        points: 25,
        healthLevel: 'HEALTHY',
      },
      {
        label: 'Mild Visible Thinness',
        subtext: 'Slightly low energy or mild weight reduction',
        points: 10,
        healthLevel: 'BORDERLINE',
      },
      {
        label: 'Bilateral Swollen Feet / Legs (Pitting Edema)',
        subtext: 'Fluid retention on both feet that leaves a visible dent when pressed',
        points: 0,
        healthLevel: 'CRITICAL',
      },
      {
        label: 'Severe Muscle Wasting & Prominent Ribs',
        subtext: 'Marked loss of subcutaneous fat and muscle mass',
        points: 0,
        healthLevel: 'CRITICAL',
      },
    ],
  },
  {
    key: 'illness',
    title: 'Recent Illness & Digestion',
    prompt: "Has there been persistent diarrhea (>14 days), high fever, or frequent vomiting recently?",
    options: [
      {
        label: 'No Recent Chronic Illness',
        subtext: 'No gastrointestinal infection or fluid retention issues',
        points: 20,
        healthLevel: 'HEALTHY',
      },
      {
        label: 'Brief Mild Cold or Low Fever',
        subtext: 'Short-term minor seasonal symptoms, currently resolving',
        points: 15,
        healthLevel: 'BORDERLINE',
      },
      {
        label: 'Persistent Diarrhea (>14 Days)',
        subtext: 'Chronic fluid and nutrient malabsorption impairing recovery',
        points: 0,
        healthLevel: 'UNHEALTHY',
      },
      {
        label: 'Frequent Vomiting & Dehydration',
        subtext: 'Inability to retain liquids or solid nutrition',
        points: 0,
        healthLevel: 'UNHEALTHY',
      },
    ],
  },
  {
    key: 'dietary_diversity',
    title: '24-Hour Dietary Diversity',
    prompt: "In the last 24 hours, how many distinct food groups were consumed? (e.g. cereals/staples, pulses/beans, dairy, eggs/meat, green vegetables, orange fruits)",
    options: [
      {
        label: 'Diverse Diet (4 or More Food Groups)',
        subtext: 'Balanced intake of proteins, micronutrients, vitamins, and calories',
        points: 20,
        healthLevel: 'HEALTHY',
      },
      {
        label: 'Limited Diet (2 to 3 Food Groups)',
        subtext: 'Missing key animal/plant proteins or fresh fruits and vegetables',
        points: 10,
        healthLevel: 'BORDERLINE',
      },
      {
        label: 'Monotonous Diet (Only 1 Staple / Plain Rice or Gruel)',
        subtext: 'Severe macronutrient and micronutrient imbalance',
        points: 0,
        healthLevel: 'UNHEALTHY',
      },
    ],
  },
  {
    key: 'supplements',
    title: 'Supplements & Prophylaxis',
    prompt: "Are routine bi-annual deworming (Albendazole) and Vitamin A / Iron supplements up to date?",
    options: [
      {
        label: 'Yes, Up to Date',
        subtext: 'Received recommended prophylaxis within the past 6 months',
        points: 10,
        healthLevel: 'HEALTHY',
      },
      {
        label: 'Not Sure / Unknown',
        subtext: 'Supplementation record not currently verified',
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

export const MalnutritionAIChatbot: React.FC<MalnutritionAIChatbotProps> = ({
  onProceedToOpticalScan,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, QuestionOption>>({});
  const [isEvaluating, setIsEvaluating] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    startAssessment();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isEvaluating]);

  const startAssessment = () => {
    setCurrentStepIndex(0);
    setSelectedAnswers({});
    const firstQ = QUESTIONS_TREE[0];
    setMessages([
      {
        id: 'msg-0',
        sender: 'ai',
        text: firstQ.prompt,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        questionKey: firstQ.key,
        options: firstQ.options,
      },
    ]);
  };

  const handleSelectOption = (option: QuestionOption) => {
    const currentQ = QUESTIONS_TREE[currentStepIndex];
    const updatedAnswers = { ...selectedAnswers, [currentQ.key]: option };
    setSelectedAnswers(updatedAnswers);

    // Add user response bubble
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: option.label,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsEvaluating(true);

    const nextIndex = currentStepIndex + 1;

    setTimeout(() => {
      setIsEvaluating(false);

      if (nextIndex < QUESTIONS_TREE.length) {
        setCurrentStepIndex(nextIndex);
        const nextQ = QUESTIONS_TREE[nextIndex];
        const aiMsg: ChatMessage = {
          id: `ai-${Date.now()}`,
          sender: 'ai',
          text: nextQ.prompt,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          questionKey: nextQ.key,
          options: nextQ.options,
        };
        setMessages((prev) => [...prev, aiMsg]);
      } else {
        computeProfessionalDiagnosis(updatedAnswers);
      }
    }, 450);
  };

  const computeProfessionalDiagnosis = (answers: Record<string, QuestionOption>) => {
    const demoOpt = answers['demographic'];
    const appetiteOpt = answers['appetite'];
    const physicalOpt = answers['physical_signs'];
    const illnessOpt = answers['illness'];
    const dietOpt = answers['dietary_diversity'];
    const suppOpt = answers['supplements'];

    // Internal calculation (hidden from UI display)
    const score =
      (appetiteOpt?.points || 0) +
      (physicalOpt?.points || 0) +
      (illnessOpt?.points || 0) +
      (dietOpt?.points || 0) +
      (suppOpt?.points || 0);

    const hasEdema = physicalOpt?.label.includes('Pitting Edema');
    const hasSevereWasting = physicalOpt?.label.includes('Severe Muscle Wasting');
    const hasSevereAppetiteLoss = appetiteOpt?.label.includes('Poor / Refusing');

    const getStatusLabel = (level: QuestionOption['healthLevel']) => {
      switch (level) {
        case 'HEALTHY':
          return 'Optimal';
        case 'BORDERLINE':
          return 'Borderline';
        case 'UNHEALTHY':
          return 'Nutritional Concern';
        case 'CRITICAL':
          return 'Severe Clinical Risk';
      }
    };

    const factors: FactorBreakdown[] = [
      {
        category: 'Appetite & Intake',
        selectedOption: appetiteOpt?.label || 'Not evaluated',
        statusLabel: getStatusLabel(appetiteOpt?.healthLevel || 'HEALTHY'),
        status: appetiteOpt?.healthLevel || 'HEALTHY',
      },
      {
        category: 'Physical & Muscle Signs',
        selectedOption: physicalOpt?.label || 'Not evaluated',
        statusLabel: getStatusLabel(physicalOpt?.healthLevel || 'HEALTHY'),
        status: physicalOpt?.healthLevel || 'HEALTHY',
      },
      {
        category: 'Infection & Digestion',
        selectedOption: illnessOpt?.label || 'Not evaluated',
        statusLabel: getStatusLabel(illnessOpt?.healthLevel || 'HEALTHY'),
        status: illnessOpt?.healthLevel || 'HEALTHY',
      },
      {
        category: 'Dietary Diversity',
        selectedOption: dietOpt?.label || 'Not evaluated',
        statusLabel: getStatusLabel(dietOpt?.healthLevel || 'HEALTHY'),
        status: dietOpt?.healthLevel || 'HEALTHY',
      },
      {
        category: 'Supplements & Prophylaxis',
        selectedOption: suppOpt?.label || 'Not evaluated',
        statusLabel: getStatusLabel(suppOpt?.healthLevel || 'HEALTHY'),
        status: suppOpt?.healthLevel || 'HEALTHY',
      },
    ];

    let rating: NutritionDiagnosisReport['rating'];
    let ratingLabel: string;
    let badgeText: string;
    let badgeColor: string;
    let clinicalImpression: string;
    let physiologicalImpact: string;
    let actionItems: ClinicalActionItem[];
    let protocolName: string;

    if (hasEdema || hasSevereWasting || (hasSevereAppetiteLoss && score < 40)) {
      rating = 'CRITICALLY_UNHEALTHY';
      ratingLabel = 'Severe Acute Malnutrition (SAM)';
      badgeText = 'Critical Risk • Urgent Action';
      badgeColor = 'bg-red-50 text-red-800 border-red-300';
      clinicalImpression = hasEdema
        ? 'The individual presents with bilateral pitting edema (fluid swelling on both feet), which is a definitive clinical hallmark of Kwashiorkor / Severe Acute Malnutrition requiring immediate inpatient stabilization.'
        : 'The individual exhibits severe physical wasting and severe appetite loss, indicating critical depletion of muscle and adipose reserves consistent with Severe Acute Malnutrition (SAM).';
      physiologicalImpact =
        'Severe acute macronutrient depletion impairs cellular immunity, cardiac output, and metabolic stability, significantly increasing vulnerability to secondary systemic infection.';
      actionItems = [
        {
          step: '1',
          title: 'Immediate Clinical Referral',
          description: 'Refer immediately to the nearest Primary Health Centre (PHC) or Nutrition Rehabilitation Centre (NRC) for emergency medical triage.',
          isUrgent: true,
        },
        {
          step: '2',
          title: 'Medical Evaluation & Diagnostic Labs',
          description: 'Perform confirmatory blood tests (Serum Albumin, Complete Blood Count, Blood Glucose) and screen for underlying systemic infection.',
          isUrgent: true,
        },
        {
          step: '3',
          title: 'Therapeutic Nutrition Protocol',
          description: 'Initiate therapeutic feeding with Ready-to-Use Therapeutic Food (RUTF) or F-75/F-100 milk diets under strict physician supervision.',
        },
      ];
      protocolName = 'WHO Severe Acute Malnutrition Emergency Protocol';
    } else if (score < 60) {
      rating = 'UNHEALTHY';
      ratingLabel = 'Moderate Malnutrition Risk (MAM)';
      badgeText = 'Unhealthy • Targeted Intervention';
      badgeColor = 'bg-amber-50 text-amber-900 border-amber-300';
      clinicalImpression =
        'Based on reported reduced meal intake (~50%), a single-staple monotonous diet, or ongoing gastrointestinal illness, the individual is experiencing Moderate Acute Malnutrition (MAM) with clear caloric and micronutrient deficits.';
      physiologicalImpact =
        'Inadequate dietary diversity impairs linear growth velocity, compromises cellular iron and zinc stores, and leads to progressive muscle depletion and physical fatigue.';
      actionItems = [
        {
          step: '1',
          title: 'Supplementary Nutrition Enrollment',
          description: 'Enroll in community supplementary feeding programs (Take-Home Ration / Energy-Dense Nutritious Foods) to bridge daily caloric and protein deficits.',
        },
        {
          step: '2',
          title: 'Targeted Micronutrient Supplementation',
          description: 'Administer therapeutic Iron-Folic Acid (IFA) syrup/tablets, Zinc supplementation, and a single dose of Albendazole deworming.',
        },
        {
          step: '3',
          title: '14-Day Mandatory Follow-Up',
          description: 'Schedule a mandatory follow-up within 14 days to re-assess Mid-Upper Arm Circumference (MUAC) and weight gain velocity.',
        },
      ];
      protocolName = 'POSHAN Abhiyaan MAM Community Intervention Plan';
    } else if (score < 85) {
      rating = 'MILD_DEFICIT';
      ratingLabel = 'Nutritional Vulnerability / Mild Deficit';
      badgeText = 'Mild Vulnerability • Preventive Care';
      badgeColor = 'bg-amber-50/70 text-amber-800 border-amber-200';
      clinicalImpression =
        'The individual maintains an acceptable physical status but demonstrates dietary vulnerabilities—such as consuming fewer than 4 distinct food groups daily or missing routine bi-annual deworming and Vitamin A drops.';
      physiologicalImpact =
        'Sub-optimal micronutrient intake can lead to latent iron deficiency and fatigue before physical wasting becomes visually apparent.';
      actionItems = [
        {
          step: '1',
          title: 'Dietary Diversity Counseling',
          description: 'Incorporate at least 2 additional food groups daily—specifically iron-rich green leafy vegetables, pulses/lentils, eggs, or dairy.',
        },
        {
          step: '2',
          title: 'Routine Prophylactic Dosing',
          description: 'Visit the local health centre to receive routine bi-annual Albendazole deworming and prophylactic Vitamin A drops.',
        },
        {
          step: '3',
          title: 'Periodic Health Screening',
          description: 'Perform a non-invasive optical conjunctiva scan to ensure hemoglobin levels remain within normal reference ranges.',
        },
      ];
      protocolName = 'Community Preventive Nutrition Counseling';
    } else {
      rating = 'HEALTHY';
      ratingLabel = 'Optimal Nutritional Health';
      badgeText = 'Healthy • Optimal Status';
      badgeColor = 'bg-emerald-50 text-emerald-800 border-emerald-300';
      clinicalImpression =
        'The individual exhibits an optimal nutritional profile characterized by a strong appetite, diverse dietary intake (4+ food groups), up-to-date supplementation, and zero physical signs of wasting or edema.';
      physiologicalImpact =
        'Adequate protein, caloric, and micronutrient intake supports healthy tissue development, robust immune resistance, and normal metabolic stamina.';
      actionItems = [
        {
          step: '1',
          title: 'Maintain Balanced Diet',
          description: 'Continue daily consumption of diverse whole foods, legumes, seasonal vegetables, and clean potable water.',
        },
        {
          step: '2',
          title: 'Sustain Preventive Schedule',
          description: 'Stay on track with routine bi-annual deworming and standard immunization milestones.',
        },
        {
          step: '3',
          title: 'Routine Community Monitoring',
          description: 'Continue periodic growth and wellness tracking at standard scheduled health checkups.',
        },
      ];
      protocolName = 'Standard WHO Healthy Nutrition Trajectory';
    }

    const report: NutritionDiagnosisReport = {
      rating,
      ratingLabel,
      badgeText,
      badgeColor,
      clinicalImpression,
      physiologicalImpact,
      factors,
      actionItems,
      protocolName,
    };

    const diagnosisMsg: ChatMessage = {
      id: `diag-${Date.now()}`,
      sender: 'ai',
      text: "Evaluation complete. Here is the clinical summary and tailored recommendation plan:",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isDiagnosis: true,
      diagnosisData: report,
    };

    setMessages((prev) => [...prev, diagnosisMsg]);
  };

  const isCompleted = messages.some((m) => m.isDiagnosis);

  return (
    <div className="bg-white rounded-[32px] border border-black/[0.06] shadow-sm overflow-hidden flex flex-col min-h-[600px]">
      
      {/* Top Header */}
      <div className="px-6 py-4 border-b border-black/[0.06] bg-[#fbfbfd] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-2xl bg-[#00776b] flex items-center justify-center text-white shadow-sm">
            <Bot className="w-5 h-5 stroke-[2]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-[15px] text-[#1d1d1f]">AI Nutrition Clinical Evaluation</h3>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            </div>
            <p className="text-[11px] text-[#86868b]">1-Tap Clinical Questionnaire • Diagnostic Summary & Action Plan</p>
          </div>
        </div>

        <button
          onClick={startAssessment}
          className="p-2 rounded-full hover:bg-black/[0.05] text-[#86868b] hover:text-[#1d1d1f] transition-colors cursor-pointer"
          title="Restart Assessment"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Progress Pill Bar */}
      <div className="bg-[#f5f5f7] px-6 py-2 border-b border-black/[0.04] flex items-center justify-between text-[11px] text-[#6e6e73]">
        <span>
          Question {Math.min(currentStepIndex + 1, QUESTIONS_TREE.length)} of {QUESTIONS_TREE.length}:{' '}
          <strong className="text-[#1d1d1f]">{QUESTIONS_TREE[Math.min(currentStepIndex, QUESTIONS_TREE.length - 1)].title}</strong>
        </span>
        <span className="font-mono">
          {Math.round((Math.min(currentStepIndex + 1, QUESTIONS_TREE.length) / QUESTIONS_TREE.length) * 100)}% Completed
        </span>
      </div>

      {/* Messages / Option Selection Area */}
      <div className="flex-1 p-6 overflow-y-auto space-y-5">
        {messages.map((msg, msgIdx) => {
          const isAI = msg.sender === 'ai';
          const isLastAIMsg = isAI && msgIdx === messages.length - 1 && !isCompleted;

          return (
            <div
              key={msg.id}
              className={`flex gap-3 ${isAI ? 'justify-start' : 'justify-end'} animate-in fade-in slide-in-from-bottom-2 duration-200`}
            >
              {isAI && (
                <div className="w-7 h-7 rounded-xl bg-[#00776b]/10 text-[#00776b] flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div className={`max-w-[90%] sm:max-w-[80%] space-y-3 ${isAI ? 'text-left' : 'text-right'}`}>
                {/* Bubble Text */}
                <div
                  className={`p-4 rounded-2xl text-[14px] leading-relaxed whitespace-pre-line ${
                    isAI
                      ? 'bg-[#f5f5f7] text-[#1d1d1f] rounded-tl-sm'
                      : 'bg-[#1d1d1f] text-white rounded-tr-sm font-medium'
                  }`}
                >
                  {msg.text}
                </div>

                {/* Clickable Option Cards */}
                {isLastAIMsg && msg.options && (
                  <div className="space-y-2 pt-1">
                    {msg.options.map((opt, i) => (
                      <button
                        key={i}
                        type="button"
                        onClick={() => handleSelectOption(opt)}
                        className="w-full p-4 rounded-2xl bg-white hover:bg-[#fbfbfd] border border-black/[0.08] hover:border-[#00776b] text-[#1d1d1f] text-left transition-all flex items-center justify-between group cursor-pointer shadow-sm"
                      >
                        <div className="space-y-0.5 pr-2">
                          <span className="font-semibold text-[14px] text-[#1d1d1f] group-hover:text-[#00776b] transition-colors block">
                            {opt.label}
                          </span>
                          {opt.subtext && (
                            <p className="text-[12px] text-[#6e6e73] leading-relaxed">
                              {opt.subtext}
                            </p>
                          )}
                        </div>

                        <div className="w-8 h-8 rounded-full bg-black/[0.04] group-hover:bg-[#00776b] text-[#86868b] group-hover:text-white flex items-center justify-center shrink-0 transition-all">
                          <ChevronRight className="w-4 h-4" />
                        </div>
                      </button>
                    ))}
                  </div>
                )}

                {/* Professional Clinical Diagnostic Report */}
                {msg.isDiagnosis && msg.diagnosisData && (
                  <div className="p-6 sm:p-8 rounded-[28px] bg-white border border-black/[0.08] shadow-md space-y-6 text-left mt-2">
                    
                    {/* Header Rating Status */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-black/[0.06] pb-4">
                      <div>
                        <span className="text-[11px] font-mono uppercase text-[#86868b] tracking-wider block">
                          Nutritional Health Assessment
                        </span>
                        <h4 className="text-[22px] font-bold text-[#1d1d1f] tracking-tight mt-0.5">
                          {msg.diagnosisData.ratingLabel}
                        </h4>
                      </div>

                      <span className={`px-4 py-1.5 rounded-full text-[12px] font-semibold border self-start sm:self-auto ${msg.diagnosisData.badgeColor}`}>
                        {msg.diagnosisData.badgeText}
                      </span>
                    </div>

                    {/* Section 1: Clinical Summary & Impression ("What this is") */}
                    <div className="p-5 rounded-2xl bg-[#fbfbfd] border border-black/[0.05] space-y-3">
                      <div className="flex items-center gap-2 text-[#00776b]">
                        <Stethoscope className="w-4 h-4" />
                        <span className="font-semibold text-[13px] uppercase tracking-wider text-[#1d1d1f]">
                          Clinical Summary & Impression
                        </span>
                      </div>

                      <p className="text-[14px] text-[#1d1d1f] leading-relaxed">
                        {msg.diagnosisData.clinicalImpression}
                      </p>

                      <p className="text-[12px] text-[#6e6e73] leading-relaxed border-t border-black/[0.04] pt-2">
                        <strong className="text-[#1d1d1f]">Physiological Impact:</strong> {msg.diagnosisData.physiologicalImpact}
                      </p>
                    </div>

                    {/* Section 2: Clinical Factors Analysis */}
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <ClipboardList className="w-4 h-4 text-[#86868b]" />
                        <span className="text-[12px] font-semibold text-[#1d1d1f] uppercase tracking-wider">
                          Key Evaluation Factors
                        </span>
                      </div>

                      <div className="space-y-2">
                        {msg.diagnosisData.factors.map((f, idx) => (
                          <div
                            key={idx}
                            className="p-3.5 rounded-2xl bg-[#fbfbfd] border border-black/[0.04] flex items-center justify-between text-[13px]"
                          >
                            <div className="space-y-0.5">
                              <span className="font-semibold text-[#1d1d1f] block">{f.category}</span>
                              <span className="text-[12px] text-[#6e6e73]">{f.selectedOption}</span>
                            </div>

                            <span
                              className={`px-3 py-1 rounded-full text-[11px] font-semibold border ${
                                f.status === 'HEALTHY'
                                  ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                                  : f.status === 'BORDERLINE'
                                  ? 'bg-amber-50 text-amber-800 border-amber-200'
                                  : 'bg-red-50 text-red-800 border-red-200'
                              }`}
                            >
                              {f.statusLabel}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Section 3: Recommended Action Plan ("What to do accordingly") */}
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-[12px] font-semibold text-[#1d1d1f] uppercase tracking-wider block">
                          Recommended Clinical Action Plan
                        </span>
                        <span className="text-[11px] text-[#86868b] font-mono">
                          {msg.diagnosisData.protocolName}
                        </span>
                      </div>

                      <div className="space-y-2.5">
                        {msg.diagnosisData.actionItems.map((item, idx) => (
                          <div
                            key={idx}
                            className={`p-4 rounded-2xl border text-[13px] flex items-start gap-3.5 ${
                              item.isUrgent
                                ? 'bg-red-50/60 border-red-200 text-red-950'
                                : 'bg-[#fbfbfd] border-black/[0.05] text-[#1d1d1f]'
                            }`}
                          >
                            <div
                              className={`w-6 h-6 rounded-full flex items-center justify-center font-bold text-[11px] shrink-0 ${
                                item.isUrgent
                                  ? 'bg-red-600 text-white'
                                  : 'bg-[#00776b] text-white'
                              }`}
                            >
                              {item.step}
                            </div>
                            <div className="space-y-0.5">
                              <span className="font-bold text-[13px] block">{item.title}</span>
                              <p className={item.isUrgent ? 'text-red-900 leading-relaxed' : 'text-[#6e6e73] leading-relaxed'}>
                                {item.description}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Next Action Triggers */}
                    <div className="pt-2 flex flex-col sm:flex-row gap-3 border-t border-black/[0.06]">
                      {onProceedToOpticalScan && (
                        <button
                          onClick={onProceedToOpticalScan}
                          className="apple-btn-accent flex-1 py-3.5 text-[13px] font-medium inline-flex items-center justify-center gap-2 shadow-sm"
                        >
                          <Sparkles className="w-4 h-4" />
                          <span>Run Optical Eyelid Anemia Scan</span>
                        </button>
                      )}
                      <button
                        onClick={startAssessment}
                        className="apple-btn-secondary px-6 py-3.5 text-[13px] font-medium"
                      >
                        Evaluate Another Person
                      </button>
                    </div>

                  </div>
                )}

                <span className="text-[10px] text-[#86868b] block px-1">
                  {msg.timestamp}
                </span>
              </div>

              {!isAI && (
                <div className="w-7 h-7 rounded-xl bg-[#1d1d1f] text-white flex items-center justify-center shrink-0 mt-0.5">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          );
        })}

        {/* Calculating Loading State */}
        {isEvaluating && (
          <div className="flex gap-3 items-center text-[#86868b] text-[13px]">
            <div className="w-7 h-7 rounded-xl bg-[#00776b]/10 text-[#00776b] flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4 animate-bounce" />
            </div>
            <div className="bg-[#f5f5f7] px-4 py-2.5 rounded-2xl text-[12px] flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#00776b] animate-pulse" />
              <span>Analyzing clinical indicators...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

    </div>
  );
};
