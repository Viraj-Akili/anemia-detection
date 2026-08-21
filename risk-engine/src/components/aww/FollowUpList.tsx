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
    <div className="space-y-5 max-w-4xl mx-auto pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Scheduled Follow-Ups & Referrals</h2>
          <p className="text-xs text-slate-400">
            {followUpQueue.length} priority beneficiaries due for re-screening or PHC confirmation
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {followUpQueue.map((beneficiary) => (
          <div
            key={beneficiary.id}
            onClick={() => onSelectBeneficiary(beneficiary)}
            className="bg-slate-900 hover:bg-slate-850 border border-slate-800 rounded-2xl p-5 transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4 group"
          >
            <div className="space-y-1.5">
              <div className="flex items-center space-x-2">
                <span className="font-bold text-white text-base group-hover:text-cyan-300">
                  {beneficiary.name}
                </span>
                <span className="text-xs text-slate-400">
                  ({beneficiary.category === 'child' ? `Child, Age ${beneficiary.ageYears}` : `Pregnant Woman, Trimester ${beneficiary.trimester}`})
                </span>
              </div>
              <div className="text-xs text-slate-400">
                Village: <span className="text-slate-200">{beneficiary.locationVillage}</span> • Guardian:{' '}
                <span className="text-slate-200">{beneficiary.guardianName}</span>
              </div>
              <div className="text-xs text-amber-300 font-medium">
                Last Action: {beneficiary.visitHistory?.[beneficiary.visitHistory.length - 1]?.recommendedAction || 'Follow-up recommended'}
              </div>
            </div>

            <div className="flex items-center space-x-3 self-end sm:self-auto">
              <div className="text-right">
                <div className="flex items-center space-x-1.5 justify-end">
                  <span className="text-xs text-slate-400">Priority:</span>
                  <span
                    className={`px-2.5 py-0.5 text-xs font-bold rounded-md ${
                      beneficiary.overallPriority === 'HIGH'
                        ? 'bg-rose-950 text-rose-300 border border-rose-800'
                        : 'bg-amber-950 text-amber-300 border border-amber-800'
                    }`}
                  >
                    {beneficiary.overallPriority}
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 mt-1">
                  Trajectory: <span className="text-cyan-400">{beneficiary.trajectory.replace('_', ' ')}</span>
                </div>
              </div>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onStartScreening(beneficiary);
                }}
                className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold shadow-sm"
              >
                Perform Follow-Up →
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
