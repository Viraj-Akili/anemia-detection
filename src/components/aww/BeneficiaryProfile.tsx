import React from 'react';
import { Beneficiary, Language } from '../../types';
import { getTranslation } from '../../services/localizationService';
import { SafetyDisclaimerBanner } from '../common/SafetyDisclaimerBanner';
import {
  ArrowLeft,
  Calendar,
  Activity,
  TrendingDown,
  TrendingUp,
  Minus,
  Plus,
  ShieldCheck,
  ChevronRight,
  Eye,
  Ruler,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  ReferenceLine,
} from 'recharts';

interface BeneficiaryProfileProps {
  beneficiary: Beneficiary;
  onBack: () => void;
  onStartScreening: (beneficiary: Beneficiary) => void;
  language: Language;
}

export const BeneficiaryProfile: React.FC<BeneficiaryProfileProps> = ({
  beneficiary,
  onBack,
  onStartScreening,
  language,
}) => {
  const history = beneficiary.visitHistory || [];

  const growthChartData = history.map((v) => ({
    date: v.date,
    weight: v.weightKg,
    muac: v.muacCm,
    height: v.heightCm,
  }));

  const getTrajectoryIcon = (state: string) => {
    switch (state) {
      case 'IMPROVING':
        return <TrendingUp className="w-4 h-4 text-emerald-600" />;
      case 'DECLINING':
      case 'RAPIDLY_DECLINING':
        return <TrendingDown className="w-4 h-4 text-red-600" />;
      default:
        return <Minus className="w-4 h-4 text-[#00776b]" />;
    }
  };

  return (
    <div className="space-y-6 max-w-[1040px] mx-auto pb-16">
      
      {/* Back Button */}
      <button
        onClick={onBack}
        className="inline-flex items-center gap-1.5 text-[13px] font-medium text-[#6e6e73] hover:text-[#1d1d1f] transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Beneficiary Registry</span>
      </button>

      {/* Profile Health Card Header */}
      <div className="bg-white border border-black/[0.06] rounded-[32px] p-8 shadow-sm space-y-6">
        <div className="flex items-center justify-between border-b border-black/[0.06] pb-4 text-[12px] text-[#86868b]">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[#00776b]" />
            <span className="font-medium text-[#1d1d1f]">RCH Digital Health Record • Verified ABHA ID</span>
          </div>
          {beneficiary.abhaId && (
            <span className="font-mono text-[#1d1d1f] bg-[#f5f5f7] px-3 py-1 rounded-full text-[11px] font-medium">
              {beneficiary.abhaId}
            </span>
          )}
        </div>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-3 flex-wrap">
              <h2 className="text-[32px] font-semibold text-[#1d1d1f] tracking-title">{beneficiary.name}</h2>
              <span className="px-3 py-1 text-[12px] font-medium rounded-full bg-black/[0.05] text-[#1d1d1f]">
                {beneficiary.category === 'child'
                  ? `Age ${beneficiary.ageYears}y • ${beneficiary.sex || 'Child'}`
                  : `Maternal ANC • Trimester ${beneficiary.trimester}`}
              </span>
              {beneficiary.isDemoData && (
                <span className="px-2.5 py-0.5 text-[9px] uppercase font-semibold rounded-full bg-black/[0.05] text-[#6e6e73]">
                  DEMO
                </span>
              )}
            </div>

            <div className="flex items-center gap-4 text-[13px] text-[#6e6e73] flex-wrap">
              <span>Guardian: <strong className="text-[#1d1d1f]">{beneficiary.guardianName}</strong></span>
              <span>•</span>
              <span>Village: <strong className="text-[#1d1d1f]">{beneficiary.locationVillage}</strong></span>
              <span>•</span>
              <span>Phone: <strong className="text-[#1d1d1f]">{beneficiary.phone || 'N/A'}</strong></span>
            </div>
          </div>

          <button
            onClick={() => onStartScreening(beneficiary)}
            className="apple-btn-accent px-6 py-3.5 text-[14px] inline-flex items-center justify-center gap-2 shadow-sm self-start md:self-auto"
          >
            <Plus className="w-4 h-4 stroke-[2.5]" />
            <span>Start Screening Workflow</span>
          </button>
        </div>

        {/* Current Health Metrics Row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-6 border-t border-black/[0.06]">
          <div className="bg-[#fbfbfd] p-4 rounded-2xl border border-black/[0.04]">
            <span className="text-[11px] text-[#86868b] uppercase font-medium">Anemia Status</span>
            <div className="flex items-center gap-2 mt-1">
              <span
                className={`px-2.5 py-0.5 text-[12px] font-semibold rounded-full ${
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
          </div>

          <div className="bg-[#fbfbfd] p-4 rounded-2xl border border-black/[0.04]">
            <span className="text-[11px] text-[#86868b] uppercase font-medium">Nutrition Risk</span>
            <p className="text-[16px] font-semibold text-[#1d1d1f] mt-1">{beneficiary.nutritionRisk}</p>
          </div>

          <div className="bg-[#fbfbfd] p-4 rounded-2xl border border-black/[0.04]">
            <span className="text-[11px] text-[#86868b] uppercase font-medium">Trajectory</span>
            <div className="flex items-center gap-1.5 mt-1 font-semibold text-[14px] text-[#1d1d1f]">
              {getTrajectoryIcon(beneficiary.trajectory)}
              <span>{beneficiary.trajectory.replace('_', ' ')}</span>
            </div>
          </div>

          <div className="bg-[#fbfbfd] p-4 rounded-2xl border border-black/[0.04]">
            <span className="text-[11px] text-[#86868b] uppercase font-medium">Last Visit</span>
            <p className="text-[16px] font-semibold text-[#1d1d1f] mt-1 font-mono">
              {beneficiary.lastVisitDate || 'First Visit'}
            </p>
          </div>
        </div>
      </div>

      {/* Longitudinal Growth & MUAC Trajectory Chart */}
      {growthChartData.length > 0 && (
        <div className="bg-white rounded-[32px] p-6 sm:p-8 border border-black/[0.06] shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-[18px] font-semibold text-[#1d1d1f]">
                Longitudinal MUAC & Weight Trajectory
              </h3>
              <p className="text-[13px] text-[#6e6e73]">
                Monitored against WHO Child Growth Standards across visit history
              </p>
            </div>
            <span className="px-3 py-1 rounded-full text-[11px] font-medium bg-[#f5f5f7] text-[#6e6e73]">
              {growthChartData.length} Recorded Visits
            </span>
          </div>

          <div className="h-64 w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={growthChartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f2" />
                <XAxis dataKey="date" stroke="#86868b" fontSize={12} tickLine={false} />
                <YAxis stroke="#86868b" fontSize={12} domain={[10, 16]} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    borderRadius: '16px',
                    border: '1px solid rgba(0,0,0,0.08)',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                  }}
                />
                <ReferenceLine y={11.5} stroke="#ef4444" strokeDasharray="3 3" label={{ value: 'SAM (11.5cm)', fill: '#ef4444', fontSize: 10 }} />
                <ReferenceLine y={12.5} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: 'MAM (12.5cm)', fill: '#f59e0b', fontSize: 10 }} />
                <Line type="monotone" dataKey="muac" stroke="#00776b" strokeWidth={3} dot={{ r: 4, fill: '#00776b' }} name="MUAC (cm)" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Historical Visit Records */}
      <div className="bg-white rounded-[32px] p-6 sm:p-8 border border-black/[0.06] shadow-sm space-y-4">
        <h3 className="text-[18px] font-semibold text-[#1d1d1f]">Visit Screening History</h3>
        
        {history.length === 0 ? (
          <p className="text-[14px] text-[#86868b] py-8 text-center">No screening visits recorded yet.</p>
        ) : (
          <div className="space-y-3">
            {history.map((visit, idx) => (
              <div
                key={visit.id || idx}
                className="p-5 rounded-2xl bg-[#fbfbfd] border border-black/[0.04] flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-[#1d1d1f] text-[15px]">{visit.date}</span>
                    <span
                      className={`px-2 py-0.5 text-[10px] font-bold rounded-full ${
                        visit.anemiaRisk === 'ELEVATED'
                          ? 'bg-red-50 text-red-800'
                          : 'bg-emerald-50 text-emerald-800'
                      }`}
                    >
                      {visit.anemiaRisk} Risk
                    </span>
                  </div>
                  <p className="text-[13px] text-[#6e6e73] mt-1">
                    MUAC: <strong className="text-[#1d1d1f]">{visit.muacCm} cm</strong> • Weight: <strong className="text-[#1d1d1f]">{visit.weightKg} kg</strong> • Action: {visit.recommendedAction}
                  </p>
                </div>

                <div className="text-[12px] text-[#86868b] font-mono">
                  {visit.imageQuality}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
};
