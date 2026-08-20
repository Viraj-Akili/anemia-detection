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
    <div className="space-y-8 max-w-[1140px] mx-auto pb-16">
      
      {/* Header */}
      <div className="bg-white border border-black/[0.06] rounded-[32px] p-8 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 text-[#00776b] text-[12px] font-semibold mb-1">
            <Building className="w-4 h-4" />
            <span>District Health Administration Command Center</span>
          </div>
          <h2 className="text-[32px] font-semibold text-[#1d1d1f] tracking-title">
            District Population Risk & Intervention Radar
          </h2>
          <p className="text-[14px] text-[#6e6e73] mt-1">
            Aggregated real-time early warning coverage across 4 sub-districts and 142 Anganwadi sectors.
          </p>
        </div>
      </div>

      {/* District High-level KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <div className="bg-white p-6 rounded-[28px] border border-black/[0.06] shadow-sm space-y-1">
          <span className="text-[12px] text-[#86868b] font-medium">Target Population</span>
          <div className="text-[32px] font-bold text-[#1d1d1f] font-mono">90,700</div>
          <div className="text-[12px] text-[#6e6e73]">Children (0-6y) & Pregnant Women</div>
        </div>

        <div className="bg-white p-6 rounded-[28px] border border-black/[0.06] shadow-sm space-y-1">
          <span className="text-[12px] text-[#86868b] font-medium">Screening Coverage Rate</span>
          <div className="text-[32px] font-bold text-[#00776b] font-mono">88.5%</div>
          <div className="text-[12px] text-[#00776b] flex items-center gap-1 font-medium">
            <ArrowUpRight className="w-3.5 h-3.5" /> +4.2% over previous quarter
          </div>
        </div>

        <div className="bg-white p-6 rounded-[28px] border border-amber-200/80 shadow-sm space-y-1">
          <span className="text-[12px] text-amber-900 font-medium">Risk Hotspot Sectors</span>
          <div className="text-[32px] font-bold text-amber-800 font-mono">3 Sectors</div>
          <div className="text-[12px] text-amber-700">Targeted IFA distribution dispatched</div>
        </div>

        <div className="bg-white p-6 rounded-[28px] border border-black/[0.06] shadow-sm space-y-1">
          <span className="text-[12px] text-[#86868b] font-medium">PHC Confirmatory Rate</span>
          <div className="text-[32px] font-bold text-[#1d1d1f] font-mono">92.4%</div>
          <div className="text-[12px] text-[#6e6e73]">Referrals completed at PHCs</div>
        </div>

      </div>

      {/* Sub-district Population Risk Breakdown */}
      <div className="bg-white rounded-[32px] p-8 border border-black/[0.06] shadow-sm space-y-4">
        <h3 className="text-[18px] font-semibold text-[#1d1d1f]">
          Sub-district Screening Coverage & High-Risk Case Volume
        </h3>

        <div className="h-72 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={districtBlocksData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f2" />
              <XAxis dataKey="block" stroke="#86868b" fontSize={11} tickLine={false} />
              <YAxis stroke="#86868b" fontSize={11} tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  borderRadius: '14px',
                  border: '1px solid rgba(0,0,0,0.08)',
                }}
              />
              <Bar dataKey="population" fill="#e5e5ea" name="Eligible Cohort" radius={[6, 6, 0, 0]} />
              <Bar dataKey="screened" fill="#00776b" name="Screened Cohort" radius={[6, 6, 0, 0]} />
              <Bar dataKey="highRisk" fill="#ef4444" name="High Risk Flags" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

    </div>
  );
};
