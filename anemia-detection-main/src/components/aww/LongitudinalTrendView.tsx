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
    <div className="space-y-8 max-w-[1040px] mx-auto pb-16">
      
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-[#00776b] text-[12px] font-semibold mb-1">
          <Activity className="w-4 h-4" />
          <span>Longitudinal Intelligence Engine</span>
        </div>
        <h2 className="text-[28px] sm:text-[34px] font-semibold text-[#1d1d1f] tracking-title">
          Community Trajectory Intelligence
        </h2>
        <p className="text-[14px] text-[#6e6e73]">
          Tracking risk velocity across sequential Anganwadi visits to intercept health decline early
        </p>
      </div>

      {/* Trajectory Breakdown Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        
        <div className="bg-white p-6 rounded-[28px] border border-red-200/80 shadow-sm space-y-2">
          <div className="flex items-center gap-2 text-red-700 font-semibold text-[13px]">
            <TrendingDown className="w-4 h-4" />
            <span>Declining Trajectories</span>
          </div>
          <div className="text-[36px] font-bold text-red-700 font-mono">{decliningList.length}</div>
          <p className="text-[13px] text-[#6e6e73]">
            Beneficiaries showing elevated anemia or growth deficit velocity.
          </p>
        </div>

        <div className="bg-white p-6 rounded-[28px] border border-black/[0.06] shadow-sm space-y-2">
          <div className="flex items-center gap-2 text-[#00776b] font-semibold text-[13px]">
            <Minus className="w-4 h-4" />
            <span>Stable Trajectories</span>
          </div>
          <div className="text-[36px] font-bold text-[#1d1d1f] font-mono">
            {beneficiaries.filter((b) => b.trajectory === 'STABLE').length}
          </div>
          <p className="text-[13px] text-[#6e6e73]">Maintaining baseline health levels within expected variance.</p>
        </div>

        <div className="bg-white p-6 rounded-[28px] border border-emerald-200/80 shadow-sm space-y-2">
          <div className="flex items-center gap-2 text-emerald-700 font-semibold text-[13px]">
            <TrendingUp className="w-4 h-4" />
            <span>Improving Trajectories</span>
          </div>
          <div className="text-[36px] font-bold text-emerald-700 font-mono">
            {beneficiaries.filter((b) => b.trajectory === 'IMPROVING').length}
          </div>
          <p className="text-[13px] text-[#6e6e73]">Responding positively to nutritional supplementation and care.</p>
        </div>

      </div>

      {/* Detailed Declining Risk Trajectory Cards */}
      <div className="bg-white rounded-[32px] p-6 sm:p-8 border border-black/[0.06] shadow-sm space-y-6">
        <div className="flex items-center gap-2.5">
          <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
          <h3 className="text-[18px] font-semibold text-[#1d1d1f] tracking-tight">
            Active Declining Trajectories — Clinical Priority
          </h3>
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
                className="bg-[#fbfbfd] hover:bg-[#f5f5f7] p-6 rounded-2xl border border-black/[0.05] transition-all cursor-pointer space-y-4"
              >
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div>
                    <span className="font-semibold text-[#1d1d1f] text-[16px]">{b.name}</span>
                    <span className="text-[12px] text-[#86868b] ml-2">
                      ({b.category === 'child' ? `Child, ${b.ageYears}y` : `Pregnant, Trimester ${b.trimester}`})
                    </span>
                  </div>

                  <span className="px-3 py-1 text-[11px] font-semibold rounded-full bg-red-50 text-red-800 border border-red-200">
                    Trajectory: {b.trajectory.replace('_', ' ')}
                  </span>
                </div>

                <div className="h-40 w-full pt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f2" />
                      <XAxis dataKey="date" stroke="#86868b" fontSize={11} tickLine={false} />
                      <YAxis
                        domain={[1, 3]}
                        ticks={[1, 2, 3]}
                        tickFormatter={(val) => (val === 3 ? 'ELEVATED' : val === 2 ? 'MODERATE' : 'LOW')}
                        stroke="#86868b"
                        fontSize={11}
                        tickLine={false}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#ffffff',
                          borderRadius: '14px',
                          border: '1px solid rgba(0,0,0,0.08)',
                          boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                        }}
                        formatter={(val: any) => [val === 3 ? 'ELEVATED' : val === 2 ? 'MODERATE' : 'LOW', 'Anemia Risk']}
                      />
                      <Line type="monotone" dataKey="riskScore" stroke="#ef4444" strokeWidth={3} dot={{ r: 5, fill: '#ef4444' }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                <p className="text-[13px] text-[#6e6e73]">
                  <strong className="text-[#1d1d1f]">Clinical Insight:</strong> Risk indicator elevated across the last {b.visitHistory?.length} visits. Rapid referral or dietary escalation recommended.
                </p>
              </div>
            );
          })}
        </div>
      </div>

    </div>
  );
};
