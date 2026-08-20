import React, { useState } from 'react';
import { ArrowRight, ShieldCheck, CheckCircle2, AlertTriangle, HelpCircle } from 'lucide-react';

export const RiskEngineSection: React.FC = () => {
  const [selectedCase, setSelectedCase] = useState<'mild' | 'moderate' | 'severe'>('moderate');

  const cases = {
    mild: {
      title: 'Low Clinical Risk',
      eyelid: 'Optimal Vascular Erythema (0.520)',
      muac: '13.4 cm (Normal Green Band)',
      triage: 'Routine Growth Monitoring',
      action: 'Schedule standard 30-day village nutrition follow-up.',
      badgeColor: 'bg-emerald-50 text-emerald-800 border-emerald-200',
      status: 'Low Priority',
    },
    moderate: {
      title: 'Moderate Vulnerability',
      eyelid: 'Mild Pallor Detected (0.412)',
      muac: '12.1 cm (Borderline MAM Yellow)',
      triage: 'Targeted Nutritional Intervention',
      action: 'Provide IFA syrup, dietary counseling, and 14-day re-screening.',
      badgeColor: 'bg-amber-50 text-amber-800 border-amber-200',
      status: 'Action Required',
    },
    severe: {
      title: 'High Risk Escalation',
      eyelid: 'Marked Conjunctival Pallor (0.280)',
      muac: '11.1 cm (Severe SAM Red Band)',
      triage: 'Immediate Clinical Escalation',
      action: 'Urgent referral to PHC / Nutrition Rehabilitation Centre (NRC).',
      badgeColor: 'bg-red-50 text-red-800 border-red-200',
      status: 'Urgent Referral',
    },
  };

  const active = cases[selectedCase];

  return (
    <section id="safety" className="py-28 md:py-36 bg-[#fbfbfd]">
      <div className="max-w-[1180px] mx-auto px-6">
        
        {/* Section Header */}
        <div className="flex items-center gap-3 mb-6">
          <span className="text-[13px] font-mono font-medium text-[#86868b] tracking-wider uppercase">05 — Risk Scoring</span>
          <span className="h-[1px] w-12 bg-black/[0.1]" />
        </div>

        <div className="max-w-3xl mb-16">
          <h2 className="text-[36px] sm:text-[48px] md:text-[56px] font-semibold tracking-title text-[#1d1d1f] leading-[1.08] mb-6">
            Input → Analysis → Risk indication.<br />Protected by deterministic safety.
          </h2>
          <p className="text-[19px] sm:text-[21px] text-[#6e6e73] font-normal leading-[1.5]">
            PRAHARI wraps statistical screening inside hardcoded WHO clinical guardrails. The safety layer can escalate clinical urgency, but can never downgrade clinical vigilance.
          </p>
        </div>

        {/* Case Toggle Selector */}
        <div className="flex items-center gap-2 mb-8">
          <button
            onClick={() => setSelectedCase('mild')}
            className={`px-4 py-2 rounded-full text-[13px] font-medium transition-all ${
              selectedCase === 'mild'
                ? 'bg-[#1d1d1f] text-white shadow-sm'
                : 'bg-white text-[#6e6e73] border border-black/[0.08] hover:text-[#1d1d1f]'
            }`}
          >
            Scenario A: Normal
          </button>
          <button
            onClick={() => setSelectedCase('moderate')}
            className={`px-4 py-2 rounded-full text-[13px] font-medium transition-all ${
              selectedCase === 'moderate'
                ? 'bg-[#1d1d1f] text-white shadow-sm'
                : 'bg-white text-[#6e6e73] border border-black/[0.08] hover:text-[#1d1d1f]'
            }`}
          >
            Scenario B: Borderline
          </button>
          <button
            onClick={() => setSelectedCase('severe')}
            className={`px-4 py-2 rounded-full text-[13px] font-medium transition-all ${
              selectedCase === 'severe'
                ? 'bg-[#1d1d1f] text-white shadow-sm'
                : 'bg-white text-[#6e6e73] border border-black/[0.08] hover:text-[#1d1d1f]'
            }`}
          >
            Scenario C: Severe
          </button>
        </div>

        {/* The Pipeline Architecture Card: Input -> Analysis -> Output */}
        <div className="bg-white rounded-[36px] p-8 sm:p-12 border border-black/[0.06] shadow-sm">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            
            {/* Step 1: Input Signals */}
            <div className="lg:col-span-4 space-y-4">
              <span className="text-[11px] font-mono uppercase text-[#86868b] tracking-wider">1. Dual Input Signals</span>
              <div className="space-y-3">
                <div className="p-4 rounded-2xl bg-[#f5f5f7] border border-black/[0.04]">
                  <span className="text-[11px] text-[#86868b] uppercase font-semibold">Optical Sensor</span>
                  <p className="text-[14px] font-medium text-[#1d1d1f] mt-0.5">{active.eyelid}</p>
                </div>
                <div className="p-4 rounded-2xl bg-[#f5f5f7] border border-black/[0.04]">
                  <span className="text-[11px] text-[#86868b] uppercase font-semibold">WHO Anthropometry</span>
                  <p className="text-[14px] font-medium text-[#1d1d1f] mt-0.5">{active.muac}</p>
                </div>
              </div>
            </div>

            {/* Connecting Arrow */}
            <div className="hidden lg:flex lg:col-span-1 justify-center">
              <ArrowRight className="w-6 h-6 text-[#86868b]" />
            </div>

            {/* Step 2: Deterministic Safety Engine */}
            <div className="lg:col-span-3 p-5 rounded-2xl bg-[#00776b]/5 border border-[#00776b]/20 space-y-2">
              <div className="flex items-center gap-2 text-[#00776b]">
                <ShieldCheck className="w-5 h-5" />
                <span className="text-[13px] font-semibold">Deterministic Wrapper</span>
              </div>
              <p className="text-[12px] text-[#6e6e73] leading-relaxed">
                Evaluates WHO 2024 Pediatric thresholds. Non-downgrade policy active.
              </p>
            </div>

            {/* Connecting Arrow */}
            <div className="hidden lg:flex lg:col-span-1 justify-center">
              <ArrowRight className="w-6 h-6 text-[#86868b]" />
            </div>

            {/* Step 3: Triage & Action Result */}
            <div className="lg:col-span-3 space-y-3">
              <span className="text-[11px] font-mono uppercase text-[#86868b] tracking-wider">3. Actionable Triage</span>
              <div className={`p-5 rounded-2xl border ${active.badgeColor}`}>
                <span className="text-[11px] font-bold uppercase tracking-wider">{active.status}</span>
                <h4 className="text-[17px] font-semibold mt-1">{active.title}</h4>
                <p className="text-[13px] mt-2 opacity-90 leading-snug">{active.action}</p>
              </div>
            </div>

          </div>
        </div>

        {/* Explainability Callout */}
        <div className="mt-8 flex items-start gap-4 p-6 rounded-2xl bg-white border border-black/[0.06] text-[#6e6e73] text-[14px]">
          <HelpCircle className="w-5 h-5 text-[#86868b] shrink-0 mt-0.5" />
          <p>
            <strong className="text-[#1d1d1f] font-semibold">Explainability First:</strong> PRAHARI does not provide opaque numerical black-box scores. Every screening result produces clear, human-understandable contributing factors and immediate protocol guidelines for the healthcare worker.
          </p>
        </div>

      </div>
    </section>
  );
};
