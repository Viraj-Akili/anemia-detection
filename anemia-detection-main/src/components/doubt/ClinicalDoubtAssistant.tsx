import React, { useState } from 'react';
import {
  HelpCircle,
  Search,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  ChevronRight,
  ArrowRight,
  Info,
  Send,
  MessageCircleQuestion,
  Activity,
  HeartPulse,
  AlertTriangle,
} from 'lucide-react';

export interface SymptomDoubtResponse {
  query: string;
  isRelevant: boolean;
  relevanceLevel: 'HIGH_RELEVANCE' | 'MODERATE_RELEVANCE' | 'LOW_RELEVANCE' | 'UNRECOGNIZED';
  headline: string;
  explanation: string;
  pathophysiology: string;
  commonQuestions: string[];
  recommendedAction: string;
}

const COMMON_DOUBTS: Array<{ query: string; category: string }> = [
  { query: 'I get dizzy when standing up quickly. Is this related to anemia?', category: 'Dizziness' },
  { query: 'My hands and feet are always freezing cold even in warm weather.', category: 'Cold Extremities' },
  { query: 'I feel exhausted even after sleeping 8 to 9 hours.', category: 'Chronic Fatigue' },
  { query: 'My inner eyelids look very pale instead of pink or red.', category: 'Optical Pallor' },
  { query: 'I have intense cravings to chew on ice or starch (Pica).', category: 'Pica & Cravings' },
  { query: 'My heart beats fast or pounds when climbing a single flight of stairs.', category: 'Palpitations' },
  { query: 'My fingernails are brittle and dented inward like a spoon.', category: 'Nails & Hair' },
  { query: 'My tongue feels swollen, smooth, and sore (Glossitis).', category: 'Oral Symptoms' },
];

export const evaluateSymptomDoubt = (userQuery: string): SymptomDoubtResponse => {
  const q = userQuery.toLowerCase().trim();

  if (q.includes('dizzy') || q.includes('lightheaded') || q.includes('faint') || q.includes('spinning') || q.includes('vertigo') || q.includes('blackout') || q.includes('unsteady')) {
    return {
      query: userQuery,
      isRelevant: true,
      relevanceLevel: 'HIGH_RELEVANCE',
      headline: 'Dizziness & Lightheadedness are Classic Anemia Indicators',
      explanation: 'When hemoglobin levels fall, your blood carries less oxygen to your brain (cerebral hypoxia), frequently triggering dizziness, lightheadedness, or feeling faint when standing up.',
      pathophysiology: 'Reduced oxygen delivery to the central nervous system combined with orthostatic blood pressure compensation.',
      commonQuestions: ['Does it worsen when standing quickly?', 'Do you also see brief dark spots or tunnel vision?'],
      recommendedAction: 'Perform an optical conjunctiva scan below and request a complete blood count (CBC) to check Serum Ferritin and Hemoglobin.',
    };
  }

  if (q.includes('cold') || q.includes('feet') || q.includes('hand') || q.includes('chilly') || q.includes('shivering') || q.includes('freezing')) {
    return {
      query: userQuery,
      isRelevant: true,
      relevanceLevel: 'HIGH_RELEVANCE',
      headline: 'Cold Hands & Feet are Directly Linked to Low Hemoglobin',
      explanation: 'With low red blood cell count, the body automatically shunts warm oxygenated blood away from outer extremities (hands and feet) toward critical core organs like the heart and brain.',
      pathophysiology: 'Peripheral vasoconstriction to maintain core organ perfusion in the presence of reduced total oxygen-carrying capacity.',
      commonQuestions: ['Are your fingernails also pale or bluish?', 'Do your fingers feel numb or tingly?'],
      recommendedAction: 'Evaluate conjunctival pallor and increase dietary bioavailable iron (green leafy vegetables, pulses, or animal protein).',
    };
  }

  if (q.includes('tired') || q.includes('fatigue') || q.includes('exhaust') || q.includes('energy') || q.includes('sleep') || q.includes('weak') || q.includes('lazy') || q.includes('letharg') || q.includes('worn out')) {
    return {
      query: userQuery,
      isRelevant: true,
      relevanceLevel: 'HIGH_RELEVANCE',
      headline: 'Unexplained Fatigue is the #1 Most Prevalent Symptom of Anemia',
      explanation: 'Your muscles and vital tissues are starved of sufficient cellular oxygen to generate adenosine triphosphate (ATP) energy, resulting in pervasive physical and mental exhaustion.',
      pathophysiology: 'Systemic cellular hypoxia due to insufficient functional hemoglobin circulating in red blood cells.',
      commonQuestions: ['Does the fatigue persist even after adequate sleep?', 'Do your legs feel heavy after mild walking?'],
      recommendedAction: 'High likelihood of iron deficiency. Screening your conjunctival palpebral mucosa is strongly recommended.',
    };
  }

  if (q.includes('ice') || q.includes('clay') || q.includes('chalk') || q.includes('dirt') || q.includes('pica') || q.includes('craving') || q.includes('starch') || q.includes('chew ice') || q.includes('crunch ice')) {
    return {
      query: userQuery,
      isRelevant: true,
      relevanceLevel: 'HIGH_RELEVANCE',
      headline: 'Pica (Compulsive Cravings for Ice or Non-Food Items) is a Hallmark Sign',
      explanation: 'Compulsive cravings for chewing ice (pagophagia), cornstarch, chalk, or clay is a medically recognized neurological response to severe iron deficiency anemia.',
      pathophysiology: 'Iron depletion alters dopamine and neurotransmitter metabolism in the brain, triggering specialized non-nutritive cravings.',
      commonQuestions: ['Do you crave chewing ice daily?', 'Do you have a metallic taste in your mouth?'],
      recommendedAction: 'Almost always indicates severe iron depletion. Immediate laboratory ferritin testing and iron supplementation are recommended.',
    };
  }

  if (q.includes('heart') || q.includes('breath') || q.includes('palpitation') || q.includes('pulse') || q.includes('chest') || q.includes('panting') || q.includes('gasp') || q.includes('short of breath') || q.includes('racing')) {
    return {
      query: userQuery,
      isRelevant: true,
      relevanceLevel: 'HIGH_RELEVANCE',
      headline: 'Shortness of Breath & Fast Heartbeat (Compensatory Tachycardia)',
      explanation: 'Because each milliliter of blood holds less oxygen, the heart must pump significantly faster and harder to compensate, causing palpitations and rapid breathing during minor activity.',
      pathophysiology: 'Compensatory tachycardia and increased cardiac output to maintain peripheral tissue oxygen supply.',
      commonQuestions: ['Does your heart beat fast while climbing stairs?', 'Do you feel out of breath doing normal chores?'],
      recommendedAction: 'Perform optical mucosal screening. Consult a medical provider if chest tightness occurs.',
    };
  }

  if (q.includes('nail') || q.includes('hair') || q.includes('brittle') || q.includes('spoon') || q.includes('fall') || q.includes('shedding') || q.includes('ridge') || q.includes('dent')) {
    return {
      query: userQuery,
      isRelevant: true,
      relevanceLevel: 'HIGH_RELEVANCE',
      headline: 'Brittle Nails, Hair Thinning & Spoon Nails (Koilonychia)',
      explanation: 'Hair follicles and nail matrix cells have rapid turnover rates requiring abundant iron and oxygen. Low ferritin causes brittle ridged nails and telogen effluvium (diffuse hair shedding).',
      pathophysiology: 'Inadequate iron supply to rapidly proliferating epithelial matrix cells of the nail bed and hair follicles.',
      commonQuestions: ['Are your nails concave/indented in the center?', 'Is your hair shedding noticeably more during brushing?'],
      recommendedAction: 'Check both Serum Ferritin and Hemoglobin levels.',
    };
  }

  if (q.includes('tongue') || q.includes('mouth') || q.includes('sore') || q.includes('swallow') || q.includes('burning') || q.includes('corner') || q.includes('glossitis') || q.includes('cheilitis')) {
    return {
      query: userQuery,
      isRelevant: true,
      relevanceLevel: 'HIGH_RELEVANCE',
      headline: 'Swollen Tongue (Glossitis) & Angular Cheilitis (Cracked Mouth Corners)',
      explanation: 'Iron and Vitamin B12/Folate deficiency cause papillae on the tongue to shrink, making the tongue appear smooth, swollen, and unusually tender or red.',
      pathophysiology: 'Atrophic glossitis resulting from micronutrient depletion in oral mucosal epithelial turnover.',
      commonQuestions: ['Do spicy or acidic foods cause burning?', 'Are the corners of your mouth cracked?'],
      recommendedAction: 'Screening for nutritional iron deficiency and Vitamin B12 deficiency is indicated.',
    };
  }

  if (q.includes('pale') || q.includes('skin') || q.includes('eyelid') || q.includes('face') || q.includes('color') || q.includes('pallor') || q.includes('white') || q.includes('yellow') || q.includes('sallow')) {
    return {
      query: userQuery,
      isRelevant: true,
      relevanceLevel: 'HIGH_RELEVANCE',
      headline: 'Mucosal & Skin Pallor is the Direct Visible Sign of Anemia',
      explanation: 'Hemoglobin gives blood its rich red color. When levels are low, the vascular beds under the inner lower eyelid, gums, and nail beds lose their healthy redness and appear pale white or light pink.',
      pathophysiology: 'Loss of optical light absorption by oxyhemoglobin in microvascular capillary loops.',
      commonQuestions: ['Is your lower palpebral conjunctiva noticeably pale?', 'Are your palm creases lighter than usual?'],
      recommendedAction: 'Capture an optical photo of your lower eyelid below to run the PRAHARI optical pallor algorithm.',
    };
  }

  if (q.includes('headache') || q.includes('brain') || q.includes('focus') || q.includes('concentrat') || q.includes('memory') || q.includes('fog')) {
    return {
      query: userQuery,
      isRelevant: true,
      relevanceLevel: 'MODERATE_RELEVANCE',
      headline: 'Headaches & Brain Fog are Frequently Reported with Anemia',
      explanation: 'Low oxygenation of brain arteries causes mild arterial dilation and intracranial pressure changes, leading to dull tension-like headaches and difficulty focusing.',
      pathophysiology: 'Compensatory cerebral vasodilation in response to reduced oxygen content in arterial blood.',
      commonQuestions: ['Do headaches accompany feeling faint or tired?', 'Does caffeine or resting temporarily relieve it?'],
      recommendedAction: 'Check if you have other symptoms like cold hands or eye pallor.',
    };
  }

  if (q.includes('period') || q.includes('bleed') || q.includes('menstrua') || q.includes('heavy flow') || q.includes('blood loss')) {
    return {
      query: userQuery,
      isRelevant: true,
      relevanceLevel: 'HIGH_RELEVANCE',
      headline: 'Heavy Menstrual Blood Loss is the Leading Cause of Iron Deficiency',
      explanation: 'Each milliliter of lost blood removes approximately 0.5 mg of elemental iron. Chronic heavy periods frequently outpace dietary iron absorption.',
      pathophysiology: 'Negative iron balance when menstrual blood loss exceeds daily intestinal iron absorption capacity.',
      commonQuestions: ['Do periods last longer than 7 days?', 'Do you need to change protection every 1–2 hours?'],
      recommendedAction: 'Routine prophylactic iron supplementation and optical screening are recommended.',
    };
  }

  if (q.includes('leg') || q.includes('restless') || q.includes('cramp') || q.includes('tingl') || q.includes('numb')) {
    return {
      query: userQuery,
      isRelevant: true,
      relevanceLevel: 'MODERATE_RELEVANCE',
      headline: 'Restless Legs Syndrome (RLS) & Muscle Cramps',
      explanation: 'Iron is an essential cofactor for dopamine production in the central nervous system. Brain iron deficiency frequently manifests as irresistible urges to move the legs at night.',
      pathophysiology: 'Central nervous system dopamine dysregulation secondary to striatal iron depletion.',
      commonQuestions: ['Does the crawling or tingling sensation occur mostly in the evening?', 'Does moving your legs provide temporary relief?'],
      recommendedAction: 'Serum Ferritin and CBC evaluation are recommended.',
    };
  }

  if (q.includes('iron') || q.includes('hemoglobin') || q.includes('hb') || q.includes('anemia') || q.includes('anemic') || q.includes('blood test') || q.includes('ferritin') || q.includes('diet') || q.includes('supplement') || q.includes('symptom')) {
    return {
      query: userQuery,
      isRelevant: true,
      relevanceLevel: 'MODERATE_RELEVANCE',
      headline: 'Clinical Inquiry on Anemia & Iron Metabolism',
      explanation: 'Anemia occurs when your blood has a lower than normal concentration of hemoglobin or red blood cells, impairing oxygen delivery throughout the entire body.',
      pathophysiology: 'Impaired erythropoiesis or accelerated red blood cell loss resulting in decreased systemic oxygen transport.',
      commonQuestions: ['Are you experiencing fatigue, dizziness, or paleness?', 'Have you taken a recent hemoglobin test?'],
      recommendedAction: 'Take a 15-second non-invasive optical scan of your lower eyelid conjunctiva below to check your risk level.',
    };
  }

  // Strict Unrecognized Handler for random text, names, gibberish, greetings
  return {
    query: userQuery,
    isRelevant: false,
    relevanceLevel: 'UNRECOGNIZED',
    headline: "Sorry, I didn't recognize a physical symptom or health query",
    explanation: `I couldn't identify any specific physical symptom or clinical question related to anemia in "${userQuery}". Please describe a physical symptom (such as fatigue, dizziness, cold hands, pale eyelids, palpitations, brittle nails, or cravings) to evaluate its clinical relevance.`,
    pathophysiology: 'Clinical symptom triage requires description of physical signs, bodily sensations, or medical history.',
    commonQuestions: [
      'Are you experiencing extreme fatigue or weakness?',
      'Do you feel dizzy or lightheaded when standing up?',
      'Have you noticed paleness in your inner eyelids or cold hands?',
    ],
    recommendedAction: 'Try typing a physical symptom above, or proceed directly to taking an optical conjunctiva scan below.',
  };
};

interface ClinicalDoubtAssistantProps {
  onStartOpticalScan?: () => void;
}

export const ClinicalDoubtAssistant: React.FC<ClinicalDoubtAssistantProps> = ({
  onStartOpticalScan,
}) => {
  const [doubtInput, setDoubtInput] = useState('');
  const [activeResult, setActiveResult] = useState<SymptomDoubtResponse | null>(null);
  const [doubtHistory, setDoubtHistory] = useState<SymptomDoubtResponse[]>([]);

  const handleAsk = (queryText: string) => {
    if (!queryText.trim()) return;
    const res = evaluateSymptomDoubt(queryText.trim());
    setActiveResult(res);
    setDoubtHistory((prev) => [res, ...prev.filter((item) => item.query !== res.query)]);
    setDoubtInput('');
  };

  return (
    <div className="bg-white rounded-[32px] p-8 border border-black/[0.06] shadow-sm space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-black/[0.06] pb-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-[#00776b]/10 text-[#00776b] flex items-center justify-center">
            <MessageCircleQuestion className="w-5 h-5 stroke-[2.2]" />
          </div>
          <div>
            <h3 className="font-semibold text-[18px] text-[#1d1d1f] tracking-tight">
              Anemia Symptom Doubt & Clarification System
            </h3>
            <p className="text-[12px] text-[#6e6e73]">
              Ask any question about your symptoms to check if they are clinically relevant to anemia.
            </p>
          </div>
        </div>
      </div>

      {/* Interactive Doubt Input Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleAsk(doubtInput);
        }}
        className="relative"
      >
        <input
          type="text"
          value={doubtInput}
          onChange={(e) => setDoubtInput(e.target.value)}
          placeholder="e.g. 'I feel dizzy when standing up, is that anemia?' or 'Why are my feet always cold?'"
          className="w-full pl-5 pr-28 py-4 bg-[#fbfbfd] rounded-2xl border border-black/[0.08] text-[15px] focus:outline-none focus:border-[#00776b] transition-all shadow-inner"
        />
        <button
          type="submit"
          disabled={!doubtInput.trim()}
          className="absolute right-2.5 top-2.5 bottom-2.5 apple-btn-accent px-5 text-[13px] font-medium inline-flex items-center gap-1.5 shadow-sm disabled:opacity-40"
        >
          <span>Ask Doubt</span>
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>

      {/* Suggested Quick Doubts Chips */}
      <div className="space-y-2">
        <span className="text-[11px] font-mono text-[#86868b] uppercase tracking-wider block">
          Frequent Patient Doubts (Click to analyze):
        </span>
        <div className="flex flex-wrap gap-2">
          {COMMON_DOUBTS.map((item, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleAsk(item.query)}
              className="px-3.5 py-2 rounded-xl bg-[#f5f5f7] hover:bg-[#e8e8ed] text-[#1d1d1f] text-[12px] font-medium transition-all text-left flex items-center gap-1.5 border border-black/[0.04] cursor-pointer"
            >
              <span>{item.query}</span>
              <ChevronRight className="w-3 h-3 text-[#86868b] shrink-0" />
            </button>
          ))}
        </div>
      </div>

      {/* Active Doubt Clinical Evaluation Report */}
      {activeResult && (
        <div className="p-6 rounded-[28px] bg-[#fbfbfd] border border-black/[0.08] shadow-sm space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-200">
          
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-black/[0.06] pb-3">
            <div>
              <span className="text-[10px] font-mono uppercase text-[#86868b]">
                {activeResult.isRelevant ? 'Clinical Symptom Evaluation' : 'Clarification Required'}
              </span>
              <h4 className="text-[18px] font-bold text-[#1d1d1f] tracking-tight mt-0.5">
                {activeResult.headline}
              </h4>
            </div>

            <span
              className={`px-3 py-1 rounded-full text-[11px] font-semibold border self-start sm:self-auto ${
                activeResult.relevanceLevel === 'HIGH_RELEVANCE'
                  ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                  : activeResult.relevanceLevel === 'MODERATE_RELEVANCE'
                  ? 'bg-amber-50 text-amber-800 border-amber-200'
                  : 'bg-slate-100 text-slate-700 border-slate-300'
              }`}
            >
              {activeResult.relevanceLevel === 'UNRECOGNIZED' ? 'No Symptom Detected' : activeResult.relevanceLevel.replace('_', ' ')}
            </span>
          </div>

          <p className="text-[14px] text-[#1d1d1f] leading-relaxed">
            {activeResult.explanation}
          </p>

          {activeResult.isRelevant && (
            <div className="p-4 rounded-2xl bg-white border border-black/[0.06] space-y-1.5 text-[12px]">
              <span className="font-semibold text-[#00776b] uppercase text-[10px] tracking-wider block">
                Medical Mechanism (Why This Happens)
              </span>
              <p className="text-[#6e6e73] leading-relaxed">
                {activeResult.pathophysiology}
              </p>
            </div>
          )}

          <div
            className={`p-4 rounded-2xl border space-y-1 text-[12px] ${
              activeResult.isRelevant
                ? 'bg-emerald-50/70 border-emerald-200/80'
                : 'bg-[#f5f5f7] border-black/[0.06]'
            }`}
          >
            <span
              className={`font-semibold text-[11px] block ${
                activeResult.isRelevant ? 'text-emerald-900' : 'text-[#1d1d1f]'
              }`}
            >
              Recommended Next Step:
            </span>
            <p className={activeResult.isRelevant ? 'text-emerald-950 font-medium' : 'text-[#6e6e73]'}>
              {activeResult.recommendedAction}
            </p>
          </div>

          {onStartOpticalScan && activeResult.isRelevant && (
            <div className="pt-2 flex justify-end">
              <button
                onClick={onStartOpticalScan}
                className="apple-btn-accent px-6 py-3 text-[13px] font-medium inline-flex items-center gap-2 shadow-sm"
              >
                <Sparkles className="w-4 h-4" />
                <span>Take Optical Eyelid Scan for this Symptom</span>
              </button>
            </div>
          )}

        </div>
      )}

    </div>
  );
};
