import React from 'react';
import { Home, Users, Plus, Clock, TrendingUp } from 'lucide-react';

interface MobileBottomNavProps {
  activeTab: 'home' | 'beneficiaries' | 'profile' | 'screening' | 'followups' | 'trend';
  onNavigateTab: (tab: 'home' | 'beneficiaries' | 'profile' | 'screening' | 'followups' | 'trend') => void;
}

export const MobileBottomNav: React.FC<MobileBottomNavProps> = ({ activeTab, onNavigateTab }) => {
  return (
    <div className="md:hidden fixed bottom-0 left-0 right-0 z-40 apple-glass px-3 py-2 flex items-center justify-around shadow-lg border-t border-black/[0.08]">
      <button
        onClick={() => onNavigateTab('home')}
        className={`flex flex-col items-center justify-center py-1 px-2 rounded-xl transition-all ${
          activeTab === 'home' ? 'text-[#00776b] font-semibold' : 'text-[#86868b] hover:text-[#1d1d1f]'
        }`}
      >
        <Home className="w-5 h-5 stroke-[1.75]" />
        <span className="text-[10px] mt-0.5">Home</span>
      </button>

      <button
        onClick={() => onNavigateTab('beneficiaries')}
        className={`flex flex-col items-center justify-center py-1 px-2 rounded-xl transition-all ${
          activeTab === 'beneficiaries' ? 'text-[#00776b] font-semibold' : 'text-[#86868b] hover:text-[#1d1d1f]'
        }`}
      >
        <Users className="w-5 h-5 stroke-[1.75]" />
        <span className="text-[10px] mt-0.5">Registry</span>
      </button>

      {/* Primary Center Action - New Guided Screening */}
      <button
        onClick={() => onNavigateTab('screening')}
        className="flex flex-col items-center justify-center -mt-5 bg-[#00776b] text-white p-3.5 rounded-full shadow-md hover:scale-105 active:scale-95 transition-all border-2 border-white"
        title="Start New Guided Screening"
      >
        <Plus className="w-6 h-6 stroke-[2.5]" />
      </button>

      <button
        onClick={() => onNavigateTab('followups')}
        className={`flex flex-col items-center justify-center py-1 px-2 rounded-xl transition-all ${
          activeTab === 'followups' ? 'text-[#00776b] font-semibold' : 'text-[#86868b] hover:text-[#1d1d1f]'
        }`}
      >
        <Clock className="w-5 h-5 stroke-[1.75]" />
        <span className="text-[10px] mt-0.5">Follow-ups</span>
      </button>

      <button
        onClick={() => onNavigateTab('trend')}
        className={`flex flex-col items-center justify-center py-1 px-2 rounded-xl transition-all ${
          activeTab === 'trend' ? 'text-[#00776b] font-semibold' : 'text-[#86868b] hover:text-[#1d1d1f]'
        }`}
      >
        <TrendingUp className="w-5 h-5 stroke-[1.75]" />
        <span className="text-[10px] mt-0.5">Trends</span>
      </button>
    </div>
  );
};
