import React from 'react';
import { Beneficiary, Language } from '../../types';
import { getTranslation } from '../../services/localizationService';
import { SafetyDisclaimerBanner } from '../common/SafetyDisclaimerBanner';
import {
  Users,
  PlusCircle,
  Clock,
  TrendingUp,
  AlertTriangle,
  ChevronRight,
  HeartPulse,
  CheckCircle,
  Search,
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
    <div className="space-y-6 pb-12 max-w-5xl mx-auto">
      {/* Frontline Worker Greeting Header Card */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm relative overflow-hidden">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center space-x-2 text-emerald-700 text-xs font-semibold mb-1">
              <HeartPulse className="w-4 h-4 text-emerald-600" />
              <span>Ramgarh Sector • Anganwadi Centre #04</span>
            </div>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Good morning, Meena 👋</h2>
            <p className="text-xs text-slate-600 mt-1 leading-relaxed">
              Here is your screening agenda and health updates for the 142 mothers and children under your care.
            </p>
          </div>

          <button
            onClick={() => onStartNewScreening()}
            className="flex items-center justify-center space-x-2 px-5 py-3 rounded-xl bg-[#0f766e] hover:bg-[#0d9488] text-white font-bold text-sm shadow-sm transition-all hover:scale-[1.01] active:scale-[0.99]"
          >
            <PlusCircle className="w-5 h-5" />
            <span>{getTranslation(language, 'newScreening')}</span>
          </button>
        </div>

        {/* 4 Health Metrics Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6 pt-5 border-t border-slate-100">
          <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200">
            <div className="text-slate-600 text-xs font-semibold">
              {getTranslation(language, 'screenedToday')}
            </div>
            <div className="text-2xl font-black text-slate-900 mt-1">24</div>
            <div className="text-[10px] text-emerald-700 mt-1 flex items-center font-medium">
              <CheckCircle className="w-3 h-3 mr-0.5" /> Daily Target Met
            </div>
          </div>

          <div className="bg-amber-50/70 rounded-xl p-3.5 border border-amber-200">
            <div className="text-amber-900 text-xs font-semibold">
              {getTranslation(language, 'highRiskCases')}
            </div>
            <div className="text-2xl font-black text-amber-700 mt-1">{highRiskList.length}</div>
            <div className="text-[10px] text-amber-800 mt-1">Requires follow-up</div>
          </div>

          <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200">
            <div className="text-slate-600 text-xs font-semibold">
              {getTranslation(language, 'followupsDue')}
            </div>
            <div className="text-2xl font-black text-slate-900 mt-1">7</div>
            <div className="text-[10px] text-emerald-700 mt-1">Next 14 days</div>
          </div>

          <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200">
            <div className="text-slate-600 text-xs font-semibold">
              {getTranslation(language, 'weeklyCoverage')}
            </div>
            <div className="text-2xl font-black text-emerald-700 mt-1">82%</div>
            <div className="text-[10px] text-slate-500 mt-1">Target 80%</div>
          </div>
        </div>
      </div>

      {/* Human AI Medical Disclaimer */}
      <SafetyDisclaimerBanner language={language} />

      {/* Quick Actions Navigation Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <button
          onClick={() => onNavigateTab('beneficiaries')}
          className="flex items-center justify-between p-4 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 transition-all text-left group shadow-sm"
        >
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center justify-center">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-bold text-slate-900 group-hover:text-emerald-800">
                {getTranslation(language, 'beneficiaries')}
              </div>
              <p className="text-xs text-slate-500">Search & health profiles</p>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-emerald-700 transition-all" />
        </button>

        <button
          onClick={() => onNavigateTab('followups')}
          className="flex items-center justify-between p-4 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 transition-all text-left group shadow-sm"
        >
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-amber-50 text-amber-700 border border-amber-200 flex items-center justify-center">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-bold text-slate-900 group-hover:text-amber-800">
                {getTranslation(language, 'followUps')}
              </div>
              <p className="text-xs text-slate-500">7 pending actions</p>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-amber-700 transition-all" />
        </button>

        <button
          onClick={() => onNavigateTab('trend')}
          className="flex items-center justify-between p-4 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 transition-all text-left group shadow-sm"
        >
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-purple-50 text-purple-700 border border-purple-200 flex items-center justify-center">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-bold text-slate-900 group-hover:text-purple-800">
                Longitudinal Intelligence
              </div>
              <p className="text-xs text-slate-500">Risk trajectory trends</p>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-purple-700 transition-all" />
        </button>
      </div>

      {/* Priority Cases List (Standard Web Portal Table/List) */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <h3 className="text-base font-bold text-slate-900">Priority Follow-Up Cases</h3>
          </div>
          <button
            onClick={() => onNavigateTab('beneficiaries')}
            className="text-xs text-emerald-700 hover:underline font-semibold"
          >
            View all records →
          </button>
        </div>

        <div className="space-y-3">
          {highRiskList.map((beneficiary) => (
            <div
              key={beneficiary.id}
              onClick={() => onSelectBeneficiary(beneficiary)}
              className="p-4 rounded-xl bg-slate-50 hover:bg-emerald-50/50 border border-slate-200 transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-3 group"
            >
              <div className="space-y-1">
                <div className="flex items-center space-x-2 flex-wrap">
                  <span className="font-bold text-slate-900 text-base group-hover:text-emerald-800">
                    {beneficiary.name}
                  </span>
                  <span className="text-xs text-slate-500">
                    ({beneficiary.category === 'child' ? `Child, Age ${beneficiary.ageYears}` : `Pregnant, Trimester ${beneficiary.trimester}`})
                  </span>
                  {beneficiary.isDemoData && (
                    <span className="px-2 py-0.5 text-[9px] font-bold rounded bg-slate-200 text-slate-700">
                      DEMO RECORD
                    </span>
                  )}
                </div>
                <div className="text-xs text-slate-600">
                  Village: {beneficiary.locationVillage} • Guardian: {beneficiary.guardianName}
                </div>
              </div>

              <div className="flex items-center space-x-3 self-end sm:self-auto">
                <div className="text-right">
                  <div className="flex items-center space-x-1.5 justify-end">
                    <span className="text-xs text-slate-500">Anemia Risk:</span>
                    <span
                      className={`px-2.5 py-0.5 text-xs font-bold rounded-md ${
                        beneficiary.anemiaRisk === 'ELEVATED'
                          ? 'bg-rose-100 text-rose-800 border border-rose-200'
                          : beneficiary.anemiaRisk === 'MODERATE'
                          ? 'bg-amber-100 text-amber-800 border border-amber-200'
                          : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                      }`}
                    >
                      {beneficiary.anemiaRisk}
                    </span>
                  </div>
                  <div className="text-[11px] text-amber-800 font-medium mt-1">
                    Trajectory: {beneficiary.trajectory.replace('_', ' ')}
                  </div>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onStartNewScreening(beneficiary);
                  }}
                  className="px-4 py-2 rounded-xl bg-[#0f766e] hover:bg-[#0d9488] text-white text-xs font-bold shadow-sm"
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
