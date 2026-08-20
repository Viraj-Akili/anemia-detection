import React from 'react';
import { Beneficiary, Language } from '../../types';
import { getTranslation } from '../../services/localizationService';
import {
  Users,
  Activity,
  AlertTriangle,
  MapPin,
  CheckCircle2,
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
    { name: 'Low Risk', value: 720, color: '#00776b' },
    { name: 'Moderate Risk', value: 550, color: '#f59e0b' },
    { name: 'Elevated Risk', value: 150, color: '#ef4444' },
  ];

  const sectorVolumeData = [
    { centre: 'AWC #01 Sonpur', screened: 320, highRisk: 28 },
    { centre: 'AWC #02 Chandanpur', screened: 410, highRisk: 42 },
    { centre: 'AWC #03 Belpur', screened: 290, highRisk: 18 },
    { centre: 'AWC #04 Ramgarh', screened: 400, highRisk: 54 },
  ];

  return (
    <div className="space-y-8 max-w-[1140px] mx-auto pb-16">
      
      {/* Header Banner */}
      <div className="bg-white border border-black/[0.06] rounded-[32px] p-8 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 text-[#00776b] text-[12px] font-semibold mb-1">
            <Building className="w-4 h-4" />
            <span>Ramgarh Sector • Sector Supervisor Dashboard</span>
          </div>
          <h2 className="text-[32px] font-semibold text-[#1d1d1f] tracking-title">
            Supervisor Operations Portal
          </h2>
          <p className="text-[14px] text-[#6e6e73] mt-1">
            Monitoring 4 Anganwadi Centres, 18 frontline workers, and 1,420 registered beneficiaries.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-[#fbfbfd] px-4 py-2 rounded-full border border-black/[0.05] text-[12px] text-[#1d1d1f]">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>Status: <strong className="font-semibold">Active Sector Monitoring</strong></span>
        </div>
      </div>

      {/* 4 Core Supervisor KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <div className="bg-white p-6 rounded-[28px] border border-black/[0.06] shadow-sm space-y-1">
          <span className="text-[12px] text-[#86868b] font-medium">Total Registered</span>
          <div className="text-[32px] font-bold text-[#1d1d1f] font-mono">1,420</div>
          <div className="text-[12px] text-[#00776b] font-medium">4 Sector Centres</div>
        </div>

        <div className="bg-white p-6 rounded-[28px] border border-black/[0.06] shadow-sm space-y-1">
          <span className="text-[12px] text-[#86868b] font-medium">Monthly Screened</span>
          <div className="text-[32px] font-bold text-[#1d1d1f] font-mono">1,164</div>
          <div className="text-[12px] text-[#00776b] font-medium">82.0% Coverage (Target 80%)</div>
        </div>

        <div className="bg-white p-6 rounded-[28px] border border-red-200/80 shadow-sm space-y-1">
          <span className="text-[12px] text-red-700 font-medium">Severe / High Risk Flags</span>
          <div className="text-[32px] font-bold text-red-700 font-mono">142</div>
          <div className="text-[12px] text-red-600 font-medium">100% Referred to PHC</div>
        </div>

        <div className="bg-white p-6 rounded-[28px] border border-black/[0.06] shadow-sm space-y-1">
          <span className="text-[12px] text-[#86868b] font-medium">Average Screening Time</span>
          <div className="text-[32px] font-bold text-[#1d1d1f] font-mono">48s</div>
          <div className="text-[12px] text-[#00776b] font-medium">Zero External Hardware</div>
        </div>

      </div>

      {/* Analytics Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Sector Screening Volume Chart */}
        <div className="lg:col-span-8 bg-white p-8 rounded-[32px] border border-black/[0.06] shadow-sm space-y-4">
          <h3 className="text-[18px] font-semibold text-[#1d1d1f]">
            Screening Volume by Anganwadi Centre
          </h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sectorVolumeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f2" />
                <XAxis dataKey="centre" stroke="#86868b" fontSize={11} tickLine={false} />
                <YAxis stroke="#86868b" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    borderRadius: '14px',
                    border: '1px solid rgba(0,0,0,0.08)',
                  }}
                />
                <Bar dataKey="screened" fill="#00776b" name="Screened" radius={[6, 6, 0, 0]} />
                <Bar dataKey="highRisk" fill="#ef4444" name="High Risk Flags" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk Distribution Pie Chart */}
        <div className="lg:col-span-4 bg-white p-8 rounded-[32px] border border-black/[0.06] shadow-sm space-y-4">
          <h3 className="text-[18px] font-semibold text-[#1d1d1f]">Risk Distribution</h3>
          <div className="h-56 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={riskDistributionData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {riskDistributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="space-y-2 text-[12px]">
            {riskDistributionData.map((item) => (
              <div key={item.name} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="text-[#6e6e73]">{item.name}</span>
                </div>
                <span className="font-semibold text-[#1d1d1f] font-mono">{item.value} ({((item.value/1420)*100).toFixed(0)}%)</span>
              </div>
            ))}
          </div>
        </div>

      </div>

    </div>
  );
};
