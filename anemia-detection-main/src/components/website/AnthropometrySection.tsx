import React, { useState } from 'react';
import { Ruler, Check, Info } from 'lucide-react';

export const AnthropometrySection: React.FC = () => {
  const [muacValue, setMuacValue] = useState<number>(12.2);
  const [ageMonths, setAgeMonths] = useState<number>(24);

  // WHO Standard MUAC Classification for Children 6-59 months
  const getClassification = (val: number) => {
    if (val < 11.5) {
      return {
        label: 'Severe Acute Malnutrition (SAM)',
        color: 'text-red-700 bg-red-50 border-red-200',
        bandColor: '#ef4444',
        action: 'Immediate Urgent Clinical Escalation to NRC',
      };
    }
    if (val < 12.5) {
      return {
        label: 'Moderate Acute Malnutrition (MAM)',
        color: 'text-amber-800 bg-amber-50 border-amber-200',
        bandColor: '#f59e0b',
        action: 'Supplementary Nutrition & 14-Day Review',
      };
    }
    return {
      label: 'Normal Nutritional Range',
      color: 'text-emerald-800 bg-emerald-50 border-emerald-200',
      bandColor: '#10b981',
      action: 'Routine Growth Monitoring Schedule',
    };
  };

  const currentClass = getClassification(muacValue);

  return (
    <section id="anthropometry" className="py-28 md:py-36 bg-[#ffffff]">
      <div className="max-w-[1180px] mx-auto px-6">
        
        {/* Section Header */}
        <div className="flex items-center gap-3 mb-6">
          <span className="text-[13px] font-mono font-medium text-[#86868b] tracking-wider uppercase">04 — WHO Anthropometry</span>
          <span className="h-[1px] w-12 bg-black/[0.1]" />
        </div>

        <div className="max-w-3xl mb-16">
          <h2 className="text-[36px] sm:text-[48px] md:text-[56px] font-semibold tracking-title text-[#1d1d1f] leading-[1.08] mb-6">
            WHO growth standards.<br />Incredibly simple to capture.
          </h2>
          <p className="text-[19px] sm:text-[21px] text-[#6e6e73] font-normal leading-[1.5]">
            Frontline workers record standard Mid-Upper Arm Circumference (MUAC) and weight in seconds. PRAHARI instantly verifies values against WHO Child Growth Standards.
          </p>
        </div>

        {/* Interactive Field Anthropometry Interactive Mockup */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          
          {/* Left: Interactive Field Input Component */}
          <div className="lg:col-span-7 bg-[#fbfbfd] p-8 sm:p-12 rounded-[40px] border border-black/[0.06] shadow-sm">
            <div className="flex items-center justify-between mb-8">
              <div>
                <span className="text-[12px] font-mono text-[#86868b] uppercase tracking-wider">Field Instrument</span>
                <h3 className="text-[20px] font-semibold text-[#1d1d1f]">WHO MUAC Tape Simulation</h3>
              </div>
              <span className="px-3 py-1 rounded-full text-[12px] font-medium bg-black/[0.04] text-[#1d1d1f]">
                Ages 6–59 months
              </span>
            </div>

            {/* Big Numeric Value Display */}
            <div className="flex items-baseline gap-3 mb-6">
              <span className="text-[64px] font-bold text-[#1d1d1f] tracking-display font-mono leading-none">
                {muacValue.toFixed(1)}
              </span>
              <span className="text-[22px] font-medium text-[#86868b]">cm</span>
            </div>

            {/* Visual WHO Color Ribbon */}
            <div className="relative mb-8">
              <div className="h-4 w-full rounded-full overflow-hidden flex shadow-inner">
                <div className="h-full bg-red-500 w-[25%]" title="Severe <11.5cm" />
                <div className="h-full bg-amber-400 w-[20%]" title="Moderate 11.5-12.4cm" />
                <div className="h-full bg-emerald-500 flex-1" title="Normal >=12.5cm" />
              </div>
              
              {/* Range labels */}
              <div className="flex justify-between text-[11px] text-[#86868b] mt-2 font-mono">
                <span>10.0 cm (Severe)</span>
                <span>11.5 cm</span>
                <span>12.5 cm</span>
                <span>16.0 cm (Normal)</span>
              </div>
            </div>

            {/* Slider Control */}
            <div className="space-y-2 mb-8">
              <div className="flex justify-between text-[13px] text-[#6e6e73]">
                <span>Drag to adjust field reading:</span>
                <span className="font-medium text-[#1d1d1f]">{muacValue} cm</span>
              </div>
              <input
                type="range"
                min="10.0"
                max="16.0"
                step="0.1"
                value={muacValue}
                onChange={(e) => setMuacValue(parseFloat(e.target.value))}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#00776b]"
              />
            </div>

            {/* Live Classification Result Card */}
            <div className={`p-5 rounded-2xl border ${currentClass.color} transition-all`}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[12px] font-bold uppercase tracking-wide">WHO Classification</span>
                <span className="text-[11px] font-mono">Cutoff Enforced</span>
              </div>
              <p className="text-[17px] font-semibold">{currentClass.label}</p>
              <p className="text-[13px] opacity-90 mt-1">Recommended Action: {currentClass.action}</p>
            </div>
          </div>

          {/* Right: Product Details & Field Design */}
          <div className="lg:col-span-5 space-y-6">
            
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-full bg-[#f5f5f7] flex items-center justify-center text-[#1d1d1f]">
                <Ruler className="w-5 h-5 stroke-[1.75]" />
              </div>
              <h3 className="text-[22px] font-semibold text-[#1d1d1f] tracking-tight">
                No Complex Math in the Field
              </h3>
              <p className="text-[15px] text-[#6e6e73] leading-relaxed">
                Frontline Anganwadi and ASHA workers enter exact tape measurements. The system automatically computes age-adjusted z-scores and WHO cutoffs without requiring manual look-up charts.
              </p>
            </div>

            <div className="pt-6 border-t border-black/[0.06] space-y-3">
              <h4 className="text-[16px] font-semibold text-[#1d1d1f]">
                WHO 2024 Threshold Conformance
              </h4>
              <ul className="space-y-2 text-[14px] text-[#6e6e73]">
                <li className="flex items-start gap-2">
                  <span className="text-[#00776b] font-bold">✓</span>
                  <span>Children 6–23 months revised cutoffs</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-[#00776b] font-bold">✓</span>
                  <span>Children 24–59 months (&lt; 11.0 g/dL threshold)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-[#00776b] font-bold">✓</span>
                  <span>Maternal pregnancy trimesters (1st, 2nd, 3rd)</span>
                </li>
              </ul>
            </div>

          </div>

        </div>

      </div>
    </section>
  );
};
