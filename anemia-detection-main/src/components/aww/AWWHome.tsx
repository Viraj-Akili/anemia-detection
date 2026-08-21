import React from 'react';
import { Beneficiary, Language } from '../../types';
import { getTranslation } from '../../services/localizationService';
import { SafetyDisclaimerBanner } from '../common/SafetyDisclaimerBanner';
import {
  Users,
  Plus,
  Clock,
  TrendingUp,
  AlertTriangle,
  ChevronRight,
  HeartPulse,
  CheckCircle2,
  ArrowUpRight,
} from 'lucide-react';

interface AWWHomeProps {
  beneficiaries: Beneficiary[];
  onStartNewScreening: (beneficiary?: Beneficiary) => void;
  onSelectBeneficiary: (beneficiary: Beneficiary) => void;
  onNavigateTab: (tab: 'beneficiaries' | 'followups' | 'trend') => void;
  language: Language;
}

export const AWWHome: React.FC<AWWHomeProps> = ({
  beneficiaries,
  onStartNewScreening,
  onSelectBeneficiary,
  onNavigateTab,
  language,
}) => {
  const highRiskList = beneficiaries.filter(
    (b) => b.overallPriority === 'HIGH' || b.anemiaRisk === 'ELEVATED'
  );

  return (
    <div className="space-y-8 pb-16 max-w-[1040px] mx-auto">
      
      {/* Frontline Worker Greeting & Daily Agenda Header */}
      <div className="bg-white rounded-[32px] p-8 sm:p-10 border border-black/[0.06] shadow-sm relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="flex items-center gap-2 text-[#00776b] text-[12px] font-semibold mb-2">
              <span className="w-2 h-2 rounded-full bg-[#00776b]" />
              <span>Ramgarh Sector • Anganwadi Centre #04</span>
            </div>
            <h2 className="text-[32px] sm:text-[40px] font-semibold tracking-title text-[#1d1d1f] leading-[1.1]">
              Good morning, Meena.
            </h2>
            <p className="text-[15px] text-[#6e6e73] mt-2 leading-relaxed max-w-xl">
              Here is your daily screening agenda and health updates for the 142 mothers and children under your care.
            </p>
          </div>

          <button
            onClick={() => onStartNewScreening()}
            className="apple-btn-accent px-6 py-3.5 text-[14px] inline-flex items-center justify-center gap-2 cursor-pointer shadow-md self-start md:self-auto"
          >
            <Plus className="w-4 h-4 stroke-[2.5]" />
            <span>{getTranslation(language, 'newScreening')}</span>
          </button>
        </div>

        {/* 4 Health Metric Cards (Apple Restrained Style) */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-8 pt-8 border-t border-black/[0.06]">
          
          <div className="bg-[#fbfbfd] rounded-2xl p-4 border border-black/[0.05]">
            <span className="text-[12px] font-medium text-[#86868b] block">
              {getTranslation(language, 'screenedToday')}
            </span>
            <div className="text-[28px] font-semibold text-[#1d1d1f] tracking-tight font-mono mt-1">24</div>
            <div className="text-[11px] text-[#00776b] mt-1 flex items-center gap-1 font-medium">
              <CheckCircle2 className="w-3 h-3" />
              <span>Daily Target Met</span>
            </div>
          </div>

          <div className="bg-amber-50/60 rounded-2xl p-4 border border-amber-200/80">
            <span className="text-[12px] font-medium text-amber-900 block">
              {getTranslation(language, 'highRiskCases')}
            </span>
            <div className="text-[28px] font-semibold text-amber-800 tracking-tight font-mono mt-1">
              {highRiskList.length}
            </div>
            <div className="text-[11px] text-amber-700 mt-1 font-medium">
              Requires follow-up
            </div>
          </div>

          <div className="bg-[#fbfbfd] rounded-2xl p-4 border border-black/[0.05]">
            <span className="text-[12px] font-medium text-[#86868b] block">
              {getTranslation(language, 'followupsDue')}
            </span>
            <div className="text-[28px] font-semibold text-[#1d1d1f] tracking-tight font-mono mt-1">7</div>
            <div className="text-[11px] text-[#6e6e73] mt-1 font-medium">
              Next 14 days
            </div>
          </div>

          <div className="bg-[#fbfbfd] rounded-2xl p-4 border border-black/[0.05]">
            <span className="text-[12px] font-medium text-[#86868b] block">
              {getTranslation(language, 'weeklyCoverage')}
            </span>
            <div className="text-[28px] font-semibold text-[#00776b] tracking-tight font-mono mt-1">82%</div>
            <div className="text-[11px] text-[#86868b] mt-1 font-medium">
              Target 80%
            </div>
          </div>

        </div>
      </div>

      {/* Medical AI Safety Disclaimer Banner */}
      <SafetyDisclaimerBanner language={language} />

      {/* Quick Navigation Rows */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        
        <button
          onClick={() => onNavigateTab('beneficiaries')}
          className="flex items-center justify-between p-5 rounded-2xl bg-white hover:bg-[#fbfbfd] border border-black/[0.06] transition-all text-left group shadow-sm"
        >
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-[#f5f5f7] text-[#1d1d1f] flex items-center justify-center">
              <Users className="w-5 h-5 stroke-[1.75]" />
            </div>
            <div>
              <div className="text-[15px] font-semibold text-[#1d1d1f] group-hover:text-[#00776b] transition-colors">
                {getTranslation(language, 'beneficiaries')}
              </div>
              <p className="text-[12px] text-[#86868b]">Search & registry records</p>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-[#86868b] group-hover:text-[#1d1d1f] transition-transform group-hover:translate-x-0.5" />
        </button>

        <button
          onClick={() => onNavigateTab('followups')}
          className="flex items-center justify-between p-5 rounded-2xl bg-white hover:bg-[#fbfbfd] border border-black/[0.06] transition-all text-left group shadow-sm"
        >
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-[#f5f5f7] text-[#1d1d1f] flex items-center justify-center">
              <Clock className="w-5 h-5 stroke-[1.75]" />
            </div>
            <div>
              <div className="text-[15px] font-semibold text-[#1d1d1f] group-hover:text-[#00776b] transition-colors">
                {getTranslation(language, 'followUps')}
              </div>
              <p className="text-[12px] text-[#86868b]">7 pending visits</p>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-[#86868b] group-hover:text-[#1d1d1f] transition-transform group-hover:translate-x-0.5" />
        </button>

        <button
          onClick={() => onNavigateTab('trend')}
          className="flex items-center justify-between p-5 rounded-2xl bg-white hover:bg-[#fbfbfd] border border-black/[0.06] transition-all text-left group shadow-sm"
        >
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-[#f5f5f7] text-[#1d1d1f] flex items-center justify-center">
              <TrendingUp className="w-5 h-5 stroke-[1.75]" />
            </div>
            <div>
              <div className="text-[15px] font-semibold text-[#1d1d1f] group-hover:text-[#00776b] transition-colors">
                Longitudinal Trends
              </div>
              <p className="text-[12px] text-[#86868b]">Growth & risk trajectories</p>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-[#86868b] group-hover:text-[#1d1d1f] transition-transform group-hover:translate-x-0.5" />
        </button>

      </div>

      {/* Priority Follow-up Cases Section */}
      <div className="bg-white rounded-[32px] p-6 sm:p-8 border border-black/[0.06] shadow-sm space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            <h3 className="text-[18px] font-semibold text-[#1d1d1f] tracking-tight">
              Priority Follow-Up Cases
            </h3>
          </div>
          <button
            onClick={() => onNavigateTab('beneficiaries')}
            className="text-[13px] text-[#00776b] hover:text-[#006359] font-medium flex items-center gap-1"
          >
            <span>View all registry</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="space-y-3">
          {highRiskList.map((beneficiary) => (
            <div
              key={beneficiary.id}
              onClick={() => onSelectBeneficiary(beneficiary)}
              className="p-5 rounded-2xl bg-[#fbfbfd] hover:bg-[#f5f5f7] border border-black/[0.04] transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4 group"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-semibold text-[#1d1d1f] text-[16px] group-hover:text-[#00776b] transition-colors">
                    {beneficiary.name}
                  </span>
                  <span className="text-[12px] text-[#86868b]">
                    ({beneficiary.category === 'child' ? `Child, Age ${beneficiary.ageYears}y` : `Pregnant, Trimester ${beneficiary.trimester}`})
                  </span>
                  {beneficiary.isDemoData && (
                    <span className="px-2 py-0.5 text-[9px] font-medium rounded-full bg-black/[0.05] text-[#6e6e73]">
                      DEMO
                    </span>
                  )}
                </div>
                <div className="text-[12px] text-[#6e6e73]">
                  Village: {beneficiary.locationVillage} • Guardian: {beneficiary.guardianName}
                </div>
              </div>

              <div className="flex items-center gap-4 self-end sm:self-auto">
                <div className="text-right">
                  <div className="flex items-center gap-1.5 justify-end">
                    <span className="text-[11px] text-[#86868b]">Anemia Risk:</span>
                    <span
                      className={`px-2.5 py-0.5 text-[11px] font-semibold rounded-full ${
                        beneficiary.anemiaRisk === 'ELEVATED'
                          ? 'bg-red-50 text-red-800 border border-red-200'
                          : beneficiary.anemiaRisk === 'MODERATE'
                          ? 'bg-amber-50 text-amber-800 border border-amber-200'
                          : 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                      }`}
                    >
                      {beneficiary.anemiaRisk}
                    </span>
                  </div>
                  <div className="text-[11px] text-[#86868b] mt-0.5">
                    Trajectory: <span className="font-medium text-[#1d1d1f]">{beneficiary.trajectory.replace('_', ' ')}</span>
                  </div>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onStartNewScreening(beneficiary);
                  }}
                  className="apple-btn-accent px-4 py-2 text-[12px] font-medium shadow-sm"
                >
                  Screen Now
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
};
