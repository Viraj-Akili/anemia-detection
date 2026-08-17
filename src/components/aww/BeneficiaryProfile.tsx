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
  PlusCircle,
  ShieldCheck,
  CreditCard,
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
        return <TrendingUp className="w-4 h-4 text-emerald-400" />;
      case 'DECLINING':
      case 'RAPIDLY_DECLINING':
        return <TrendingDown className="w-4 h-4 text-rose-400" />;
      default:
        return <Minus className="w-4 h-4 text-cyan-400" />;
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      {/* Back Button */}
      <button
        onClick={onBack}
        className="flex items-center space-x-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Beneficiary Registry</span>
      </button>

      {/* Official RCH & Poshan Health Card Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 text-xs text-slate-400">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span className="font-semibold text-slate-200">RCH Digital Health Record • Ministry of Health & Family Welfare</span>
          </div>
          {beneficiary.abhaId && (
            <span className="font-mono text-emerald-400 bg-slate-950 px-2.5 py-1 rounded-md border border-emerald-900 font-semibold">
              {beneficiary.abhaId}
            </span>
          )}
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2 flex-wrap">
              <h2 className="text-2xl font-bold text-white tracking-tight">{beneficiary.name}</h2>
              <span className="px-2.5 py-0.5 text-xs font-semibold rounded bg-slate-800 text-slate-300 border border-slate-700">
                {beneficiary.category === 'child'
                  ? `Age ${beneficiary.ageYears} yrs • ${beneficiary.sex}`
                  : `Pregnant Woman • Trimester ${beneficiary.trimester}`}
              </span>
              {beneficiary.isDemoData && (
                <span className="px-2 py-0.5 text-[9px] uppercase font-bold rounded bg-amber-950 text-amber-300 border border-amber-800">
                  DEMO DATA
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400">
              RCH Number: <span className="font-mono text-slate-300">{beneficiary.rchId || 'RCH-10928471920'}</span> • Village:{' '}
              <span className="text-slate-200 font-medium">{beneficiary.locationVillage}</span> • Guardian:{' '}
              <span className="text-slate-200 font-medium">{beneficiary.guardianName}</span> • AWC ID:{' '}
              <span className="font-mono text-slate-300">{beneficiary.anganwadiCentreId}</span>
            </p>
          </div>

          <button
            onClick={() => onStartScreening(beneficiary)}
            className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-cyan-300 font-bold text-xs border border-slate-700 shadow-sm"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Perform Guided Screening</span>
          </button>
        </div>

        {/* 3 Official Risk Badges */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1">
            <div className="text-xs text-slate-400 font-medium">Anemia Risk Classification</div>
            <div className="flex items-center space-x-2">
              <span
                className={`px-3 py-1 text-xs font-extrabold rounded-lg ${
                  beneficiary.anemiaRisk === 'ELEVATED'
                    ? 'bg-rose-950 text-rose-300 border border-rose-800'
                    : beneficiary.anemiaRisk === 'MODERATE'
                    ? 'bg-amber-950 text-amber-300 border border-amber-800'
                    : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                }`}
              >
                {beneficiary.anemiaRisk}
              </span>
            </div>
          </div>

          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1">
            <div className="text-xs text-slate-400 font-medium">Nutrition Risk Classification</div>
            <div className="flex items-center space-x-2">
              <span
                className={`px-3 py-1 text-xs font-extrabold rounded-lg ${
                  beneficiary.nutritionRisk === 'HIGH'
                    ? 'bg-rose-950 text-rose-300 border border-rose-800'
                    : beneficiary.nutritionRisk === 'MODERATE'
                    ? 'bg-amber-950 text-amber-300 border border-amber-800'
                    : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                }`}
              >
                {beneficiary.nutritionRisk}
              </span>
            </div>
          </div>

          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1">
            <div className="text-xs text-slate-400 font-medium">Longitudinal Risk Trajectory</div>
            <div className="flex items-center space-x-2">
              {getTrajectoryIcon(beneficiary.trajectory)}
              <span className="text-sm font-bold text-white">
                {beneficiary.trajectory.replace('_', ' ')}
              </span>
            </div>
          </div>
        </div>
      </div>

      <SafetyDisclaimerBanner language={language} />

      {/* WHO / Poshan Standard Growth Chart */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Activity className="w-5 h-5 text-cyan-400" />
            <h3 className="text-base font-bold text-white">WHO / Poshan Tracker Growth & MUAC Chart</h3>
          </div>
          <span className="text-xs text-slate-400 font-medium">Across {history.length} Sequential Visits</span>
        </div>

        <div className="h-56 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={growthChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
              <YAxis yAxisId="left" stroke="#38bdf8" fontSize={11} />
              <YAxis yAxisId="right" orientation="right" stroke="#f59e0b" fontSize={11} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                itemStyle={{ fontSize: '12px' }}
              />
              <ReferenceLine yAxisId="right" y={11.5} stroke="#f43f5e" strokeDasharray="3 3" label={{ value: 'SAM Threshold 11.5cm', fill: '#f43f5e', fontSize: 10 }} />
              <Line yAxisId="left" type="monotone" dataKey="weight" name="Weight (kg)" stroke="#38bdf8" strokeWidth={3} dot={{ r: 5 }} />
              <Line yAxisId="right" type="monotone" dataKey="muac" name="MUAC (cm)" stroke="#f59e0b" strokeWidth={3} dot={{ r: 5 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="flex items-center justify-center space-x-6 text-xs text-slate-400">
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-cyan-400 inline-block" />
            <span>Weight (kg)</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-amber-400 inline-block" />
            <span>MUAC (cm)</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 border-b-2 border-rose-500 inline-block" />
            <span>WHO SAM Cutoff (11.5 cm)</span>
          </div>
        </div>
      </div>

      {/* RCH Official Screening Timeline */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
        <div className="flex items-center space-x-2">
          <Calendar className="w-5 h-5 text-purple-400" />
          <h3 className="text-base font-bold text-white">Official RCH Visit History Timeline</h3>
        </div>

        <div className="space-y-4 border-l-2 border-slate-800 pl-4 ml-2">
          {history.map((visit, idx) => (
            <div key={visit.id || idx} className="relative space-y-2 group">
              <div className="absolute -left-[23px] top-1.5 w-3 h-3 rounded-full bg-cyan-500 border-2 border-slate-900" />

              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 space-y-2">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-cyan-400">{visit.date}</span>
                    <span className="text-xs text-slate-500">Official Checkup #{idx + 1}</span>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-slate-400">Anemia Risk:</span>
                    <span
                      className={`px-2 py-0.5 text-[11px] font-bold rounded ${
                        visit.anemiaRisk === 'ELEVATED'
                          ? 'bg-rose-950 text-rose-300 border border-rose-800'
                          : visit.anemiaRisk === 'MODERATE'
                          ? 'bg-amber-950 text-amber-300 border border-amber-800'
                          : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                      }`}
                    >
                      {visit.anemiaRisk}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 text-xs text-slate-300 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                  <div>
                    Weight: <span className="font-bold text-white">{visit.weightKg} kg</span>
                  </div>
                  <div>
                    Height: <span className="font-bold text-white">{visit.heightCm} cm</span>
                  </div>
                  <div>
                    MUAC: <span className="font-bold text-amber-300">{visit.muacCm} cm</span>
                  </div>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed font-medium">
                  <span className="text-slate-400">Action Issued:</span> {visit.recommendedAction}
                </p>

                {visit.notes && (
                  <p className="text-[11px] text-slate-400 italic bg-slate-900/40 p-2 rounded">
                    Field Notes: {visit.notes}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
