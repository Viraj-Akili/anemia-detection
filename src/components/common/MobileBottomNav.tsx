import React from 'react';
import { Home, Users, PlusCircle, Clock, TrendingUp } from 'lucide-react';

interface MobileBottomNavProps {
  activeTab: 'home' | 'beneficiaries' | 'profile' | 'screening' | 'followups' | 'trend';
  onNavigateTab: (tab: 'home' | 'beneficiaries' | 'profile' | 'screening' | 'followups' | 'trend') => void;
}

export const MobileBottomNav: React.FC<MobileBottomNavProps> = ({ activeTab, onNavigateTab }) => {
  return (
    <div className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-slate-900/95 backdrop-blur-lg border-t border-slate-800 px-2 py-2 flex items-center justify-around shadow-2xl">
      <button
        onClick={() => onNavigateTab('home')}
        className={`flex flex-col items-center justify-center py-1 px-2 rounded-xl transition-all ${
          activeTab === 'home' ? 'text-cyan-400 font-bold' : 'text-slate-400 hover:text-slate-200'
        }`}
      >
        <Home className="w-5 h-5" />
        <span className="text-[10px] mt-0.5">Home</span>
      </button>

      <button
        onClick={() => onNavigateTab('beneficiaries')}
        className={`flex flex-col items-center justify-center py-1 px-2 rounded-xl transition-all ${
          activeTab === 'beneficiaries' ? 'text-cyan-400 font-bold' : 'text-slate-400 hover:text-slate-200'
        }`}
      >
        <Users className="w-5 h-5" />
        <span className="text-[10px] mt-0.5">Records</span>
      </button>

      {/* Primary Center Action - New Guided Screening */}
      <button
        onClick={() => onNavigateTab('screening')}
        className="flex flex-col items-center justify-center -mt-5 bg-gradient-to-tr from-cyan-600 to-blue-600 text-white p-3 rounded-full shadow-lg shadow-cyan-900/60 hover:scale-105 active:scale-95 transition-all border-2 border-slate-950"
        title="Start New Guided Screening"
      >
        <PlusCircle className="w-6 h-6" />
      </button>

      <button
        onClick={() => onNavigateTab('followups')}
        className={`flex flex-col items-center justify-center py-1 px-2 rounded-xl transition-all ${
          activeTab === 'followups' ? 'text-cyan-400 font-bold' : 'text-slate-400 hover:text-slate-200'
        }`}
      >
        <Clock className="w-5 h-5" />
        <span className="text-[10px] mt-0.5">Follow-ups</span>
      </button>

      <button
        onClick={() => onNavigateTab('trend')}
        className={`flex flex-col items-center justify-center py-1 px-2 rounded-xl transition-all ${
          activeTab === 'trend' ? 'text-purple-400 font-bold' : 'text-slate-400 hover:text-slate-200'
        }`}
      >
        <TrendingUp className="w-5 h-5" />
        <span className="text-[10px] mt-0.5">Trends</span>
      </button>
    </div>
  );
};
