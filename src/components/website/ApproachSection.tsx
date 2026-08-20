import React, { useState } from 'react';
import { Eye, Ruler, ShieldCheck, ArrowRight } from 'lucide-react';

export const ApproachSection: React.FC = () => {
  const [activeStep, setActiveStep] = useState<number>(0);

  const pillars = [
    {
      step: '01',
      title: 'Optical Conjunctiva Screening',
      icon: Eye,
      tag: 'Non-Invasive Vision',
      description: 'Quantifies micro-vascular erythema and tissue pallor from the lower palpebral conjunctiva using standard smartphone camera sensors.',
      metric: 'Zero blood extraction',
    },
    {
      step: '02',
      title: 'WHO Anthropometry Integration',
      icon: Ruler,
      tag: 'Growth Standards',
      description: 'Embeds WHO child growth tables and color-banded MUAC measurements to evaluate acute and chronic nutritional status in seconds.',
      metric: 'WHO 2024 Calibrated',
    },
    {
      step: '03',
      title: 'Deterministic Safety Risk Engine',
      icon: ShieldCheck,
      tag: 'Clinical Guardrails',
      description: 'Hardcoded clinical rules enforce priority triage. The safety layer can escalate urgency, but never downgrade clinical vigilance.',
      metric: 'Strict Non-Downgrade Safety',
    },
  ];

  return (
    <section id="approach" className="py-28 md:py-36 bg-[#fbfbfd]">
      <div className="max-w-[1180px] mx-auto px-6">
        
        {/* Section Header */}
        <div className="flex items-center gap-3 mb-6">
          <span className="text-[13px] font-mono font-medium text-[#86868b] tracking-wider uppercase">02 — The PRAHARI Approach</span>
          <span className="h-[1px] w-12 bg-black/[0.1]" />
        </div>

        <h2 className="text-[36px] sm:text-[48px] md:text-[56px] font-semibold tracking-title text-[#1d1d1f] leading-[1.08] max-w-3xl mb-6">
          Three modalities.<br />One clear frontline assessment.
        </h2>

        <p className="text-[19px] sm:text-[21px] text-[#6e6e73] font-normal leading-[1.5] max-w-2xl mb-16">
          PRAHARI merges non-invasive optical screening with proven anthropometric standards and deterministic clinical safety guardrails.
        </p>

        {/* Large Tri-Modal Visual Storytelling Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {pillars.map((pillar, idx) => {
            const Icon = pillar.icon;
            const isSelected = activeStep === idx;
            return (
              <div
                key={pillar.step}
                onClick={() => setActiveStep(idx)}
                className={`p-8 rounded-[32px] transition-all duration-300 cursor-pointer border flex flex-col justify-between min-h-[360px] ${
                  isSelected
                    ? 'bg-white border-black/[0.12] shadow-xl ring-1 ring-black/[0.05]'
                    : 'bg-white/60 border-black/[0.04] hover:bg-white hover:border-black/[0.08]'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-8">
                    <span className="font-mono text-[13px] font-semibold text-[#86868b]">
                      {pillar.step}
                    </span>
                    <span className="text-[11px] font-medium px-3 py-1 rounded-full bg-black/[0.04] text-[#1d1d1f]">
                      {pillar.tag}
                    </span>
                  </div>

                  <div className="w-12 h-12 rounded-2xl bg-[#f5f5f7] flex items-center justify-center text-[#1d1d1f] mb-6">
                    <Icon className="w-6 h-6 stroke-[1.75]" />
                  </div>

                  <h3 className="text-[22px] font-semibold text-[#1d1d1f] tracking-tight mb-3">
                    {pillar.title}
                  </h3>

                  <p className="text-[15px] text-[#6e6e73] leading-relaxed">
                    {pillar.description}
                  </p>
                </div>

                <div className="pt-6 border-t border-black/[0.06] flex items-center justify-between">
                  <span className="text-[12px] font-semibold text-[#00776b]">
                    {pillar.metric}
                  </span>
                  <ArrowRight className={`w-4 h-4 text-[#1d1d1f] transition-transform ${isSelected ? 'translate-x-1' : 'opacity-40'}`} />
                </div>
              </div>
            );
          })}
        </div>

      </div>
    </section>
  );
};
