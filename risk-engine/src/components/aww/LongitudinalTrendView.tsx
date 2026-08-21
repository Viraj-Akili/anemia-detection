import React from 'react';
import { Beneficiary, Language } from '../../types';
import { getTranslation } from '../../services/localizationService';
import { TrendingDown, TrendingUp, Minus, Activity, AlertTriangle, ShieldCheck } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';

interface LongitudinalTrendViewProps {
  beneficiaries: Beneficiary[];
  onSelectBeneficiary: (beneficiary: Beneficiary) => void;
  language: Language;
}

export const LongitudinalTrendView: React.FC<LongitudinalTrendViewProps> = ({
  beneficiaries,
  onSelectBeneficiary,
  language,
}) => {
  const decliningList = beneficiaries.filter(
    (b) => b.trajectory === 'DECLINING' || b.trajectory === 'RAPIDLY_DECLINING'
  );

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      <div>
        <h2 className="text-xl font-bold text-white">Longitudinal Intelligence Engine</h2>
        <p className="text-xs text-slate-400">
          Tracking screening risk trajectories across sequential Anganwadi visits rather than single moments
        </p>
      </div>

      {/* Trajectory Breakdown Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900 p-5 rounded-2xl border border-rose-900/50 space-y-2">
          <div className="flex items-center space-x-2 text-rose-400 font-bold text-xs">
            <TrendingDown className="w-4 h-4" />
            <span>Declining Trajectories</span>
          </div>
          <div className="text-3xl font-black text-white">{decliningList.length}</div>
          <p className="text-xs text-slate-400">
            Beneficiaries showing increased anemia or malnutrition risk across recent visits.
          </p>
        </div>

        <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800 space-y-2">
          <div className="flex items-center space-x-2 text-cyan-400 font-bold text-xs">
            <Minus className="w-4 h-4" />
            <span>Stable Trajectories</span>
          </div>
          <div className="text-3xl font-black text-white">
            {beneficiaries.filter((b) => b.trajectory === 'STABLE').length}
          </div>
          <p className="text-xs text-slate-400">Maintaining baseline health risk levels.</p>
        </div>

        <div className="bg-slate-900 p-5 rounded-2xl border border-emerald-900/50 space-y-2">
          <div className="flex items-center space-x-2 text-emerald-400 font-bold text-xs">
            <TrendingUp className="w-4 h-4" />
            <span>Improving Trajectories</span>
          </div>
          <div className="text-3xl font-black text-white">
            {beneficiaries.filter((b) => b.trajectory === 'IMPROVING').length}
          </div>
          <p className="text-xs text-slate-400">Responding positively to nutrition interventions.</p>
        </div>
      </div>

      {/* Detailed Declining Risk Trajectory Cards */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
        <div className="flex items-center space-x-2 text-amber-400 font-bold text-base">
          <AlertTriangle className="w-5 h-5" />
          <span>Active Declining Trajectories — Clinical Priority</span>
        </div>

        <div className="space-y-4">
          {decliningList.map((b) => {
            const chartData = (b.visitHistory || []).map((v) => ({
              date: v.date,
              riskScore: v.anemiaRisk === 'ELEVATED' ? 3 : v.anemiaRisk === 'MODERATE' ? 2 : 1,
            }));

            return (
              <div
                key={b.id}
                onClick={() => onSelectBeneficiary(b)}
                className="bg-slate-950 p-5 rounded-2xl border border-slate-800 hover:border-slate-700 transition-all cursor-pointer space-y-3"
              >
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div>
                    <span className="font-bold text-white text-base">{b.name}</span>
                    <span className="text-xs text-slate-400 ml-2">
                      ({b.category === 'child' ? `Child, ${b.ageYears} yrs` : `Pregnant, Trimester ${b.trimester}`})
                    </span>
                  </div>

                  <span className="px-3 py-1 text-xs font-bold rounded-lg bg-rose-950 text-rose-300 border border-rose-800">
                    Trajectory: {b.trajectory.replace('_', ' ')}
                  </span>
                </div>

                <div className="h-36 w-full pt-1">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="date" stroke="#64748b" fontSize={10} />
                      <YAxis
                        domain={[1, 3]}
                        ticks={[1, 2, 3]}
                        tickFormatter={(val) => (val === 3 ? 'ELEVATED' : val === 2 ? 'MODERATE' : 'LOW')}
                        stroke="#94a3b8"
                        fontSize={10}
                      />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }}
                        formatter={(val: any) => [val === 3 ? 'ELEVATED' : val === 2 ? 'MODERATE' : 'LOW', 'Anemia Risk']}
                      />
                      <Line type="monotone" dataKey="riskScore" stroke="#f43f5e" strokeWidth={3} dot={{ r: 6 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                <p className="text-xs text-slate-300">
                  <span className="text-slate-400 font-semibold">Clinical Insight:</span> Risk score has increased across the last {b.visitHistory?.length} visits. Early intervention recommended.
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
