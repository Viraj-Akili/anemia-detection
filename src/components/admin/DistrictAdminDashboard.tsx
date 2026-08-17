import React from 'react';
import { Language } from '../../types';
import { getTranslation } from '../../services/localizationService';
import { Building, MapPin, Activity, ShieldCheck, ArrowUpRight, AlertCircle, Layers } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';

interface DistrictAdminDashboardProps {
  language: Language;
}

export const DistrictAdminDashboard: React.FC<DistrictAdminDashboardProps> = ({ language }) => {
  const districtBlocksData = [
    { block: 'Ramgarh Sub-district', population: 24500, screened: 21200, highRisk: 1850 },
    { block: 'Sonpur Sub-district', population: 19800, screened: 16900, highRisk: 1240 },
    { block: 'Chandanpur Sub-district', population: 31000, screened: 28400, highRisk: 2910 },
    { block: 'Belpur Sub-district', population: 15400, screened: 13800, highRisk: 890 },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-cyan-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <Building className="w-4 h-4" />
            <span>District Health Administration Command Center</span>
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">District Population Risk & Intervention Radar</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Aggregated real-time early warning coverage across 4 sub-districts and 142 Anganwadi sectors.
          </p>
        </div>
      </div>

      {/* District High-level KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800 space-y-1">
          <div className="text-xs text-slate-400 font-semibold">Total Target Population</div>
          <div className="text-3xl font-black text-white">90,700</div>
          <div className="text-[11px] text-slate-400">Children (0-6 yrs) & Pregnant Women</div>
        </div>

        <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800 space-y-1">
          <div className="text-xs text-slate-400 font-semibold">Screening Coverage Rate</div>
          <div className="text-3xl font-black text-emerald-400">88.5%</div>
          <div className="text-[11px] text-emerald-400 flex items-center">
            <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" /> +4.2% over previous quarter
          </div>
        </div>

        <div className="bg-slate-900 p-5 rounded-2xl border border-amber-900/40 space-y-1">
          <div className="text-xs text-slate-400 font-semibold">Risk Hotspot Sectors</div>
          <div className="text-3xl font-black text-amber-400">3 Sectors</div>
          <div className="text-[11px] text-amber-300/80">Requires targeted IFA distribution</div>
        </div>

        <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800 space-y-1">
          <div className="text-xs text-slate-400 font-semibold">PHC Confirmatory Testing Rate</div>
          <div className="text-3xl font-black text-cyan-400">92.4%</div>
          <div className="text-[11px] text-slate-400">Referrals completed at PHCs</div>
        </div>
      </div>

      {/* Sub-district Population Risk Breakdown */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
        <div className="flex items-center space-x-2 text-white font-bold text-sm">
          <Layers className="w-4 h-4 text-cyan-400" />
          <span>Sub-district Screening Coverage & High-Risk Case Volume</span>
        </div>

        <div className="h-72 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={districtBlocksData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="block" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
              <Bar dataKey="screened" fill="#38bdf8" name="Screened Population" radius={[4, 4, 0, 0]} />
              <Bar dataKey="highRisk" fill="#f43f5e" name="High Risk Cases" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Aggregate Village Risk Map/List */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
        <div className="flex items-center space-x-2 text-amber-400 font-bold text-base">
          <MapPin className="w-5 h-5" />
          <span>Geographic Aggregated Risk Hotspots (Non-PII Aggregate View)</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { village: 'Chandanpur Sector A', highRiskPct: '14.2%', priority: 'HIGH', workers: 6 },
            { village: 'Ramgarh Sector B', highRiskPct: '12.8%', priority: 'HIGH', workers: 5 },
            { village: 'Sonpur Sector C', highRiskPct: '7.4%', priority: 'MODERATE', workers: 4 },
            { village: 'Belpur Sector D', highRiskPct: '5.1%', priority: 'LOW', workers: 3 },
          ].map((item, idx) => (
            <div key={idx} className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white text-sm">{item.village}</span>
                <span
                  className={`px-2.5 py-0.5 text-xs font-bold rounded ${
                    item.priority === 'HIGH'
                      ? 'bg-rose-950 text-rose-300 border border-rose-800'
                      : item.priority === 'MODERATE'
                      ? 'bg-amber-950 text-amber-300 border border-amber-800'
                      : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                  }`}
                >
                  {item.priority} Priority
                </span>
              </div>
              <div className="text-xs text-slate-400">
                Elevated Risk Prevalence: <strong className="text-amber-300">{item.highRiskPct}</strong> • Active Frontline Staff: {item.workers}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
