import React from 'react';
import { UserRole, Language } from '../../types';
import { getTranslation } from '../../services/localizationService';
import { syncService } from '../../services/syncService';
import {
  Wifi,
  WifiOff,
  Globe,
  UserCheck,
  Building,
  Activity,
  Cpu,
  Play,
  RotateCcw,
  Smartphone,
  Monitor,
  BookOpen,
} from 'lucide-react';

interface HeaderProps {
  currentRole: UserRole;
  onRoleChange: (role: UserRole) => void;
  currentLanguage: Language;
  onLanguageChange: (lang: Language) => void;
  onOpenModelContract: () => void;
  onOpenResearchDossier: () => void;
  onStartDemoFlow: () => void;
  onResetDemoData: () => void;
  isMobileSimulated: boolean;
  onToggleMobileSimulated: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentRole,
  onRoleChange,
  currentLanguage,
  onLanguageChange,
  onOpenModelContract,
  onOpenResearchDossier,
  onStartDemoFlow,
  onResetDemoData,
  isMobileSimulated,
  onToggleMobileSimulated,
}) => {
  const [isOffline, setIsOffline] = React.useState(syncService.getIsSimulatedOffline());
  const [syncQueue, setSyncQueue] = React.useState(syncService.getSyncQueue());
  const [isSyncing, setIsSyncing] = React.useState(false);

  React.useEffect(() => {
    const unsubscribe = syncService.subscribe(() => {
      setIsOffline(syncService.getIsSimulatedOffline());
      setSyncQueue(syncService.getSyncQueue());
    });
    return () => unsubscribe();
  }, []);

  const toggleOffline = () => {
    const nextState = !isOffline;
    syncService.setSimulatedOffline(nextState);
  };

  const handleManualSync = async () => {
    if (isOffline) return;
    setIsSyncing(true);
    await syncService.triggerSync();
    setIsSyncing(false);
  };

  return (
    <header className="sticky top-0 z-40 apple-glass text-[#1d1d1f] border-b border-black/[0.06]">
      <div className="max-w-[1240px] mx-auto px-6 py-3.5 flex flex-wrap items-center justify-between gap-4">
        
        {/* Brand Wordmark & Sector Tag */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-[#1d1d1f] flex items-center justify-center text-white shadow-sm">
            <Activity className="w-4 h-4 stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-[17px] tracking-tight text-[#1d1d1f]">
                {getTranslation(currentLanguage, 'appTitle')}
              </span>
              <span className="px-2 py-0.5 text-[10px] uppercase font-semibold rounded-full bg-black/[0.05] text-[#6e6e73] tracking-wider">
                WHO 2024 Sentinel
              </span>
            </div>
            <p className="text-[11px] text-[#86868b] font-normal hidden sm:block">
              Point-of-care optical pallor & WHO growth screening
            </p>
          </div>
        </div>

        {/* Apple Segmented Role Switcher */}
        <div className="flex items-center p-1 rounded-full bg-black/[0.05] border border-black/[0.04]">
          <button
            onClick={() => onRoleChange('aww')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-[12px] font-medium transition-all ${
              currentRole === 'aww'
                ? 'bg-white text-[#1d1d1f] shadow-sm'
                : 'text-[#6e6e73] hover:text-[#1d1d1f]'
            }`}
          >
            <UserCheck className="w-3.5 h-3.5" />
            <span>Frontline Worker</span>
          </button>

          <button
            onClick={() => onRoleChange('supervisor')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-[12px] font-medium transition-all ${
              currentRole === 'supervisor'
                ? 'bg-white text-[#1d1d1f] shadow-sm'
                : 'text-[#6e6e73] hover:text-[#1d1d1f]'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Supervisor</span>
          </button>

          <button
            onClick={() => onRoleChange('district_admin')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-[12px] font-medium transition-all ${
              currentRole === 'district_admin'
                ? 'bg-white text-[#1d1d1f] shadow-sm'
                : 'text-[#6e6e73] hover:text-[#1d1d1f]'
            }`}
          >
            <Building className="w-3.5 h-3.5" />
            <span className="hidden md:inline">District Health</span>
            <span className="md:hidden">District</span>
          </button>
        </div>

        {/* Toolbar Controls */}
        <div className="flex items-center gap-2">
          {/* Hackathon Demo Presentation Button */}
          <button
            onClick={onStartDemoFlow}
            className="apple-btn-primary px-3.5 py-1.5 text-[12px] inline-flex items-center gap-1.5 cursor-pointer shadow-sm"
            title="Launch interactive presentation walkthrough"
          >
            <Play className="w-3 h-3 fill-current" />
            <span className="hidden sm:inline">Demo Flow</span>
          </button>

          {/* Research Dossier Button */}
          <button
            onClick={onOpenResearchDossier}
            className="apple-btn-secondary px-3 py-1.5 text-[12px] inline-flex items-center gap-1.5"
            title="Open Research & Literature Dossier"
          >
            <BookOpen className="w-3.5 h-3.5 text-[#00776b]" />
            <span className="hidden xl:inline">Research Dossier</span>
          </button>

          {/* Mobile Simulation Toggle */}
          <button
            onClick={onToggleMobileSimulated}
            className={`p-2 rounded-full border transition-all ${
              isMobileSimulated
                ? 'bg-[#1d1d1f] border-[#1d1d1f] text-white shadow-sm'
                : 'bg-white border-black/[0.08] text-[#6e6e73] hover:text-[#1d1d1f]'
            }`}
            title="Toggle Mobile Viewport Simulation"
          >
            {isMobileSimulated ? <Smartphone className="w-3.5 h-3.5" /> : <Monitor className="w-3.5 h-3.5" />}
          </button>

          {/* Model AI Contract Inspector */}
          <button
            onClick={onOpenModelContract}
            className="p-2 rounded-full bg-white border border-black/[0.08] text-[#6e6e73] hover:text-[#1d1d1f] transition-colors"
            title="Inspect AI Model Contract"
          >
            <Cpu className="w-3.5 h-3.5" />
          </button>

          {/* Reset Demo Data */}
          <button
            onClick={onResetDemoData}
            className="p-2 rounded-full bg-white border border-black/[0.08] text-[#6e6e73] hover:text-amber-600 transition-colors"
            title="Reset Demo Data"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          {/* Offline Mode Indicator */}
          <button
            onClick={toggleOffline}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-medium border transition-all ${
              isOffline
                ? 'bg-amber-50 border-amber-200 text-amber-800'
                : 'bg-emerald-50 border-emerald-200 text-emerald-800'
            }`}
            title="Toggle Offline mode simulation"
          >
            {isOffline ? <WifiOff className="w-3 h-3 text-amber-600" /> : <Wifi className="w-3 h-3 text-emerald-600" />}
            <span className="hidden sm:inline">{isOffline ? 'Offline' : 'Online'}</span>
          </button>

          {/* Sync Status Badge */}
          <button
            onClick={handleManualSync}
            disabled={isOffline || syncQueue.length === 0}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium bg-black/[0.04] text-[#6e6e73] border border-black/[0.04]"
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isSyncing
                  ? 'bg-emerald-500 animate-ping'
                  : syncQueue.length > 0
                  ? 'bg-amber-500'
                  : 'bg-emerald-500'
              }`}
            />
            <span className="hidden sm:inline">
              {isSyncing
                ? 'Syncing...'
                : syncQueue.length > 0
                ? `${syncQueue.length} queued`
                : 'Synced'}
            </span>
          </button>

          {/* Language Selector */}
          <div className="flex items-center bg-white rounded-full border border-black/[0.08] px-2.5 py-1">
            <Globe className="w-3 h-3 text-[#86868b] mr-1.5" />
            <select
              value={currentLanguage}
              onChange={(e) => onLanguageChange(e.target.value as Language)}
              className="bg-transparent text-[11px] text-[#1d1d1f] font-medium focus:outline-none cursor-pointer"
            >
              <option value="en">English</option>
              <option value="hi">हिंदी (HI)</option>
              <option value="ta">தமிழ் (TA)</option>
              <option value="mr">मराठी (MR)</option>
            </select>
          </div>
        </div>

      </div>
    </header>
  );
};
