import React from 'react';
import { AlertCircle, Clock, Droplets, Ban } from 'lucide-react';

export const ProblemSection: React.FC = () => {
  return (
    <section id="problem" className="py-28 md:py-36 bg-[#ffffff] border-t border-black/[0.04]">
      <div className="max-w-[1180px] mx-auto px-6">
        
        {/* Section Numbering & Supertitle */}
        <div className="flex items-center gap-3 mb-6">
          <span className="text-[13px] font-mono font-medium text-[#86868b] tracking-wider uppercase">01 — The Challenge</span>
          <span className="h-[1px] w-12 bg-black/[0.1]" />
        </div>

        {/* Core Problem Headline */}
        <h2 className="text-[36px] sm:text-[48px] md:text-[56px] font-semibold tracking-title text-[#1d1d1f] leading-[1.08] max-w-3xl mb-8">
          The earliest signs of anemia and malnutrition are invisible until clinical damage begins.
        </h2>

        {/* Narrative introduction */}
        <p className="text-[19px] sm:text-[21px] text-[#6e6e73] font-normal leading-[1.5] max-w-3xl mb-20">
          In community health programs, frontline workers often rely on subjective visual checks or delayed laboratory blood tests. By the time noticeable weakness appears, nutritional deficits have already affected cognitive and physical development.
        </p>

        {/* Editorial Comparison: Traditional Diagnostics vs The Frontline Reality */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pt-6 border-t border-black/[0.06]">
          
          <div className="space-y-4">
            <div className="w-10 h-10 rounded-full bg-black/[0.04] flex items-center justify-center text-[#1d1d1f]">
              <Droplets className="w-5 h-5 stroke-[1.75]" />
            </div>
            <h3 className="text-[20px] font-semibold text-[#1d1d1f] tracking-tight">
              Invasive & Painful for Children
            </h3>
            <p className="text-[15px] text-[#6e6e73] leading-relaxed">
              Standard hemoglobin checks require needle pricks or venous blood collection, creating distress and hesitation during routine community visits.
            </p>
          </div>

          <div className="space-y-4">
            <div className="w-10 h-10 rounded-full bg-black/[0.04] flex items-center justify-center text-[#1d1d1f]">
              <Clock className="w-5 h-5 stroke-[1.75]" />
            </div>
            <h3 className="text-[20px] font-semibold text-[#1d1d1f] tracking-tight">
              Turnaround Latency
            </h3>
            <p className="text-[15px] text-[#6e6e73] leading-relaxed">
              Laboratory processing in rural centers takes days. Critical opportunities for early nutritional intervention and counseling slip away.
            </p>
          </div>

          <div className="space-y-4">
            <div className="w-10 h-10 rounded-full bg-black/[0.04] flex items-center justify-center text-[#1d1d1f]">
              <Ban className="w-5 h-5 stroke-[1.75]" />
            </div>
            <h3 className="text-[20px] font-semibold text-[#1d1d1f] tracking-tight">
              Isolated Data Points
            </h3>
            <p className="text-[15px] text-[#6e6e73] leading-relaxed">
              Paper registers and one-off visits miss subtle downward trajectories in growth and pallor before severe malnutrition (SAM) sets in.
            </p>
          </div>

        </div>

        {/* Editorial Pull Quote */}
        <div className="mt-20 p-8 sm:p-12 rounded-3xl bg-[#f5f5f7] border border-black/[0.04] max-w-4xl">
          <p className="text-[20px] sm:text-[24px] font-medium text-[#1d1d1f] tracking-tight leading-snug">
            "Frontline healthcare workers do not need more administrative complexity. They need immediate, non-invasive point-of-care triage tools that work reliably in any field setting."
          </p>
        </div>

      </div>
    </section>
  );
};
