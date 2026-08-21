import React from 'react';
import { Beneficiary, Language } from '../../types';
import { getTranslation } from '../../services/localizationService';
import { Clock, AlertTriangle, CheckCircle2, ChevronRight, UserCheck } from 'lucide-react';

interface FollowUpListProps {
  beneficiaries: Beneficiary[];
  onSelectBeneficiary: (beneficiary: Beneficiary) => void;
  onStartScreening: (beneficiary: Beneficiary) => void;
  language: Language;
}

export const FollowUpList: React.FC<FollowUpListProps> = ({
  beneficiaries,
  onSelectBeneficiary,
  onStartScreening,
  language,
}) => {
  const followUpQueue = beneficiaries.filter(
    (b) => b.overallPriority === 'HIGH' || b.anemiaRisk === 'MODERATE' || b.anemiaRisk === 'ELEVATED'
  );

  return (
    <div className="space-y-6 max-w-[1040px] mx-auto pb-16">
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-[#00776b] text-[12px] font-semibold mb-1">
            <Clock className="w-4 h-4" />
            <span>Community Care Protocol</span>
          </div>
          <h2 className="text-[28px] sm:text-[34px] font-semibold text-[#1d1d1f] tracking-title">
            Scheduled Follow-Ups & Referrals
          </h2>
          <p className="text-[14px] text-[#6e6e73]">
            {followUpQueue.length} priority beneficiaries due for re-screening or primary health centre review
          </p>
        </div>
      </div>

      {/* Queue List Cards */}
      <div className="bg-white rounded-[32px] p-6 sm:p-8 border border-black/[0.06] shadow-sm space-y-3">
        {followUpQueue.map((beneficiary) => (
          <div
            key={beneficiary.id}
            onClick={() => onSelectBeneficiary(beneficiary)}
            className="p-5 rounded-2xl bg-[#fbfbfd] hover:bg-[#f5f5f7] border border-black/[0.04] transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4 group"
          >
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold text-[#1d1d1f] text-[16px] group-hover:text-[#00776b] transition-colors">
                  {beneficiary.name}
                </span>
                <span className="text-[12px] text-[#86868b]">
                  ({beneficiary.category === 'child' ? `Child, Age ${beneficiary.ageYears}y` : `Pregnant Woman, Trimester ${beneficiary.trimester}`})
                </span>
              </div>
              <div className="text-[12px] text-[#6e6e73]">
                Village: <strong className="text-[#1d1d1f]">{beneficiary.locationVillage}</strong> • Guardian:{' '}
                <strong className="text-[#1d1d1f]">{beneficiary.guardianName}</strong>
              </div>
              <div className="text-[12px] text-[#00776b] font-medium">
                Action: {beneficiary.visitHistory?.[beneficiary.visitHistory.length - 1]?.recommendedAction || '14-Day nutritional review'}
              </div>
            </div>

            <div className="flex items-center gap-4 self-end sm:self-auto">
              <div className="text-right">
                <div className="flex items-center gap-1.5 justify-end">
                  <span className="text-[11px] text-[#86868b]">Priority:</span>
                  <span
                    className={`px-2.5 py-0.5 text-[11px] font-semibold rounded-full ${
                      beneficiary.overallPriority === 'HIGH'
                        ? 'bg-red-50 text-red-800 border border-red-200'
                        : 'bg-amber-50 text-amber-800 border border-amber-200'
                    }`}
                  >
                    {beneficiary.overallPriority}
                  </span>
                </div>
                <div className="text-[11px] text-[#86868b] mt-0.5">
                  Trajectory: <span className="font-medium text-[#1d1d1f]">{beneficiary.trajectory.replace('_', ' ')}</span>
                </div>
              </div>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onStartScreening(beneficiary);
                }}
                className="apple-btn-accent px-4 py-2 text-[12px] font-medium shadow-sm"
              >
                Perform Screening
              </button>
            </div>
          </div>
        ))}
      </div>

    </div>
  );
};
