import React from 'react';
import { Beneficiary, Language } from '../../types';
import { getTranslation } from '../../services/localizationService';
import {
  Users,
  Activity,
  AlertTriangle,
  MapPin,
  CheckCircle,
  BarChart2,
  PieChart as PieIcon,
  UserCheck,
  Building,
  ArrowUpRight,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  CartesianGrid,
} from 'recharts';

interface SupervisorDashboardProps {
  beneficiaries: Beneficiary[];
  onSelectBeneficiary: (beneficiary: Beneficiary) => void;
  language: Language;
}

export const SupervisorDashboard: React.FC<SupervisorDashboardProps> = ({
  beneficiaries,
  onSelectBeneficiary,
  language,
}) => {
  const highRiskCases = beneficiaries.filter(
    (b) => b.overallPriority === 'HIGH' || b.anemiaRisk === 'ELEVATED'
  );

  const riskDistributionData = [
    { name: 'Low Risk', value: 720, color: '#10b981' },
    { name: 'Moderate Risk', value: 550, color: '#f59e0b' },
    { name: 'Elevated Risk', value: 150, color: '#f43f5e' },
  ];

  const sectorVolumeData = [
    { centre: 'AWC #01 Sonpur', screened: 320, highRisk: 28 },
    { centre: 'AWC #02 Chandanpur', screened: 410, highRisk: 42 },
    { centre: 'AWC #03 Belpur', screened: 290, highRisk: 18 },
    { centre: 'AWC #04 Ramgarh', screened: 400, highRisk: 54 },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-cyan-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <Building className="w-4 h-4" />
            <span>Ramgarh Health Sector • District Analytics</span>
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Supervisor Operations Portal</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Monitoring 4 Anganwadi Centres, 18 frontline workers, and 1,420 registered beneficiaries.
          </p>
        </div>

        <div className="flex items-center space-x-2 bg-slate-950 px-4 py-2 rounded-xl border border-slate-800 text-xs text-slate-300">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>Sector Status: <strong className="text-white">Active Monitoring</strong></span>
        </div>
      </div>

      {/* 4 Core Supervisor KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800 space-y-1">
          <div className="text-xs text-slate-400 font-semibold">Total Beneficiaries Screened</div>
          <div className="text-3xl font-black text-white">1,420</div>
          <div className="text-[11px] text-emerald-400 font-medium flex items-center">
            <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" /> +12% from last month
          </div>
        </div>

        <div className="bg-slate-900 p-5 rounded-2xl border border-rose-900/40 space-y-1">
          <div className="text-xs text-slate-400 font-semibold">High-Risk Cases Identified</div>
          <div className="text-3xl font-black text-rose-400">142</div>
          <div className="text-[11px] text-rose-300/80">Flagged for PHC laboratory confirmation</div>
        </div>

        <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800 space-y-1">
          <div className="text-xs text-slate-400 font-semibold">Pending Follow-Ups</div>
          <div className="text-3xl font-black text-amber-400">38</div>
          <div className="text-[11px] text-slate-400">Scheduled in next 14 days</div>
        </div>

        <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800 space-y-1">
          <div className="text-xs text-slate-400 font-semibold">Follow-Up Completion Rate</div>
          <div className="text-3xl font-black text-emerald-400">89%</div>
          <div className="text-[11px] text-emerald-400">Exceeds 85% target</div>
        </div>
      </div>

      {/* Analytics Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Screening Volume by AWC */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-white font-bold text-sm">
              <BarChart2 className="w-4 h-4 text-cyan-400" />
              <span>Screening Volume by Anganwadi Centre</span>
            </div>
          </div>
          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sectorVolumeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="centre" stroke="#64748b" fontSize={10} />
                <YAxis stroke="#64748b" fontSize={10} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                <Bar dataKey="screened" fill="#38bdf8" name="Screened" radius={[4, 4, 0, 0]} />
                <Bar dataKey="highRisk" fill="#f43f5e" name="High Risk" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sector Risk Distribution */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-white font-bold text-sm">
              <PieIcon className="w-4 h-4 text-purple-400" />
              <span>Anemia Risk Distribution Across Sector</span>
            </div>
          </div>
          <div className="h-64 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={riskDistributionData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {riskDistributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center space-x-6 text-xs text-slate-400">
            {riskDistributionData.map((item) => (
              <div key={item.name} className="flex items-center space-x-1.5">
                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                <span>{item.name} ({item.value})</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* High-Risk Referral Queue */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-amber-400 font-bold text-base">
            <AlertTriangle className="w-5 h-5" />
            <span>High-Risk Case Referral Tracking Queue</span>
          </div>
          <span className="text-xs text-slate-400">{highRiskCases.length} urgent cases</span>
        </div>

        <div className="space-y-3">
          {highRiskCases.map((b) => (
            <div
              key={b.id}
              onClick={() => onSelectBeneficiary(b)}
              className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 hover:bg-slate-850 transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-3"
            >
              <div>
                <div className="font-bold text-white text-sm">{b.name}</div>
                <div className="text-xs text-slate-400">
                  Village: {b.locationVillage} • Centre: {b.anganwadiCentreId} • Guardian: {b.guardianName}
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <span className="px-2.5 py-1 text-xs font-bold rounded bg-rose-950 text-rose-300 border border-rose-800">
                  {b.anemiaRisk} Risk
                </span>
                <span className="text-xs text-amber-300 font-medium">
                  Trajectory: {b.trajectory.replace('_', ' ')}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
