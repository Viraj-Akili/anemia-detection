import React from 'react';
import { ArrowUpRight, Shield, FileText, CheckCircle2, ChevronRight } from 'lucide-react';

interface ImpactSectionProps {
  onLaunchStudio: () => void;
  onOpenModelContract: () => void;
  onOpenResearchDossier: () => void;
}

export const ImpactSection: React.FC<ImpactSectionProps> = ({
  onLaunchStudio,
  onOpenModelContract,
  onOpenResearchDossier,
}) => {
  return (
    <section id="impact" className="py-28 md:py-40 bg-[#fbfbfd]">
      <div className="max-w-[1180px] mx-auto px-6 text-center">
        
        {/* Section Header */}
        <div className="inline-flex items-center gap-3 mb-6">
          <span className="text-[13px] font-mono font-medium text-[#86868b] tracking-wider uppercase">07 — The Bigger Picture</span>
        </div>

        <h2 className="text-[40px] sm:text-[56px] md:text-[68px] font-semibold tracking-display text-[#1d1d1f] leading-[1.04] max-w-4xl mx-auto mb-8">
          Healthcare begins before symptoms appear.
        </h2>

        <p className="text-[19px] sm:text-[22px] md:text-[24px] text-[#6e6e73] font-normal leading-[1.45] max-w-2xl mx-auto mb-12">
          By placing dignified, non-invasive early warning tools in the hands of community frontline workers, we can identify nutritional vulnerability long before it turns into chronic harm.
        </p>

        {/* Primary Launch Action Callout */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-20">
          <button
            onClick={onLaunchStudio}
            className="apple-btn-accent px-8 py-4 text-[16px] inline-flex items-center gap-2 cursor-pointer shadow-lg"
          >
            <span>Launch Frontline Application</span>
            <ChevronRight className="w-4 h-4" />
          </button>

          <button
            onClick={onOpenModelContract}
            className="apple-btn-secondary px-7 py-4 text-[15px] inline-flex items-center gap-2"
          >
            <Shield className="w-4 h-4 text-[#00776b]" />
            <span>Inspect Model Contract</span>
          </button>

          <button
            onClick={onOpenResearchDossier}
            className="apple-btn-secondary px-7 py-4 text-[15px] inline-flex items-center gap-2"
          >
            <FileText className="w-4 h-4 text-[#00776b]" />
            <span>Research Dossier</span>
          </button>
        </div>

        {/* Clinical Transparency & Medical Safety Disclaimer */}
        <div className="max-w-3xl mx-auto p-8 rounded-3xl bg-white border border-black/[0.06] text-left shadow-sm">
          <div className="flex items-center gap-2.5 mb-3">
            <span className="w-2 h-2 rounded-full bg-[#00776b]" />
            <h4 className="text-[13px] font-semibold uppercase tracking-wider text-[#1d1d1f]">
              Medical AI Transparency & Responsibility Statement
            </h4>
          </div>
          <p className="text-[13px] text-[#6e6e73] leading-relaxed">
            PRAHARI is designed strictly as an early-warning non-invasive risk screening sentinel for community triage. It does not replace venous blood draws, laboratory spectrophotometry, or clinical evaluation by a qualified medical practitioner. All screening assessments must be accompanied by appropriate healthcare follow-up according to national health mission guidelines.
          </p>
        </div>

      </div>
    </section>
  );
};
