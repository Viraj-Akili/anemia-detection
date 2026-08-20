import React from 'react';
import { ShieldCheck } from 'lucide-react';
import { Language } from '../../types';

interface SafetyDisclaimerBannerProps {
  language?: Language;
  compact?: boolean;
}

export const SafetyDisclaimerBanner: React.FC<SafetyDisclaimerBannerProps> = ({
  compact = false,
}) => {
  if (compact) {
    return (
      <div className="flex items-center gap-2 bg-[#fbfbfd] border border-black/[0.06] rounded-full px-4 py-2 text-[#6e6e73] text-[12px]">
        <ShieldCheck className="w-4 h-4 text-[#00776b] shrink-0" />
        <span>
          <strong className="text-[#1d1d1f]">Notice:</strong> Point-of-care risk screening sentinel. Confirmatory laboratory testing and medical evaluation are required for clinical diagnosis.
        </span>
      </div>
    );
  }

  return (
    <div className="bg-white border border-black/[0.06] rounded-[24px] p-5 flex items-start gap-3.5 text-[12px] shadow-sm">
      <div className="w-8 h-8 rounded-full bg-[#00776b]/10 flex items-center justify-center text-[#00776b] shrink-0">
        <ShieldCheck className="w-4 h-4" />
      </div>
      <div className="space-y-1">
        <div className="font-semibold text-[#1d1d1f] text-[13px]">
          Medical AI Screening Statement & Clinical Disclaimer
        </div>
        <p className="text-[#6e6e73] leading-relaxed">
          PRAHARI is designed as an early-warning risk screening aid for frontline community health workers. It does not provide a definitive medical diagnosis and does not replace confirmatory laboratory testing or physician evaluation.
        </p>
      </div>
    </div>
  );
};
