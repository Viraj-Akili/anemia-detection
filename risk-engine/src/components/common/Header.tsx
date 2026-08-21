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
  HeartPulse,
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
    <header className="sticky top-0 z-40 bg-[#064e3b] text-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-3">
        {/* Brand & Logo */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-600 border border-emerald-400 flex items-center justify-center text-white font-bold text-lg shadow-sm">
            <HeartPulse className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-extrabold tracking-tight text-white font-sans">
                {getTranslation(currentLanguage, 'appTitle')}
              </h1>
              <span className="px-2.5 py-0.5 text-[10px] uppercase font-bold rounded-full bg-emerald-800 text-emerald-200 border border-emerald-700">
                Health Sentinel
              </span>
            </div>
            <p className="text-xs text-emerald-100 font-medium hidden sm:block">
              Screening for anemia & malnutrition in mothers and children
            </p>
          </div>
        </div>

        {/* Role Switcher Tabs */}
        <div className="flex items-center bg-[#043e2f] p-1 rounded-xl border border-emerald-800">
          <button
            onClick={() => onRoleChange('aww')}
            className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
              currentRole === 'aww'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-emerald-200 hover:text-white'
            }`}
          >
            <UserCheck className="w-3.5 h-3.5" />
            <span className="hidden md:inline">Frontline Worker</span>
            <span className="md:hidden">Worker</span>
          </button>
          <button
            onClick={() => onRoleChange('supervisor')}
            className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
              currentRole === 'supervisor'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-emerald-200 hover:text-white'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Supervisor</span>
          </button>
          <button
            onClick={() => onRoleChange('district_admin')}
            className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
              currentRole === 'district_admin'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-emerald-200 hover:text-white'
            }`}
          >
            <Building className="w-3.5 h-3.5" />
            <span className="hidden md:inline">District Health</span>
            <span className="md:hidden">District</span>
          </button>
        </div>

        {/* Toolbar Controls */}
        <div className="flex items-center space-x-2">
          {/* Hackathon Demo Presentation Button */}
          <button
            onClick={onStartDemoFlow}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-extrabold shadow-sm transition-all"
            title="Launch interactive presentation walkthrough"
          >
            <Play className="w-3.5 h-3.5 fill-slate-950" />
            <span className="hidden sm:inline">Hackathon Demo Flow</span>
          </button>

          {/* Research Dossier Button */}
          <button
            onClick={onOpenResearchDossier}
            className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs font-bold bg-emerald-800 text-emerald-100 hover:bg-emerald-700 border border-emerald-600 transition-colors"
            title="Open Research & Literature Dossier"
          >
            <BookOpen className="w-3.5 h-3.5 text-emerald-200" />
            <span className="hidden xl:inline">Research Dossier 📚</span>
          </button>

          {/* Mobile Viewport Toggle */}
          <button
            onClick={onToggleMobileSimulated}
            className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
              isMobileSimulated
                ? 'bg-emerald-700 border-emerald-500 text-white shadow-sm'
                : 'bg-[#043e2f] border-emerald-800 text-emerald-200 hover:text-white'
            }`}
            title="Toggle Mobile Smartphone Device View"
          >
            {isMobileSimulated ? <Smartphone className="w-4 h-4 text-emerald-200" /> : <Monitor className="w-4 h-4" />}
            <span className="hidden lg:inline">{isMobileSimulated ? 'Mobile View 📱' : 'Desktop View 💻'}</span>
          </button>

          {/* Model API Contract Inspector */}
          <button
            onClick={onOpenModelContract}
            className="p-1.5 rounded-lg text-emerald-200 hover:text-white hover:bg-emerald-800 border border-emerald-800 transition-colors"
            title="Inspect AI Model Contract"
          >
            <Cpu className="w-4 h-4" />
          </button>

          {/* Reset Demo Data */}
          <button
            onClick={onResetDemoData}
            className="p-1.5 rounded-lg text-emerald-200 hover:text-amber-300 hover:bg-emerald-800 border border-emerald-800 transition-colors"
            title="Reset Demo Beneficiaries Data"
          >
            <RotateCcw className="w-4 h-4" />
          </button>

          {/* Offline Mode Switcher */}
          <button
            onClick={toggleOffline}
            className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
              isOffline
                ? 'bg-amber-950/90 border-amber-800 text-amber-300'
                : 'bg-emerald-950/90 border-emerald-800 text-emerald-300'
            }`}
            title="Toggle Offline mode simulation"
          >
            {isOffline ? <WifiOff className="w-3.5 h-3.5 text-amber-400" /> : <Wifi className="w-3.5 h-3.5 text-emerald-400" />}
            <span className="hidden sm:inline">{isOffline ? 'Offline' : 'Online'}</span>
          </button>

          {/* Sync Status Badge */}
          <button
            onClick={handleManualSync}
            disabled={isOffline || syncQueue.length === 0}
            className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
              syncQueue.length > 0
                ? 'bg-emerald-800 border-emerald-600 text-white'
                : 'bg-[#043e2f] border-emerald-800 text-emerald-200'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isSyncing
                  ? 'bg-emerald-300 animate-ping'
                  : syncQueue.length > 0
                  ? 'bg-amber-400'
                  : 'bg-emerald-400'
              }`}
            />
            <span className="hidden sm:inline">
              {isSyncing
                ? getTranslation(currentLanguage, 'syncing')
                : syncQueue.length > 0
                ? `${syncQueue.length} ${getTranslation(currentLanguage, 'offline')}`
                : getTranslation(currentLanguage, 'synced')}
            </span>
          </button>

          {/* Language Selector */}
          <div className="flex items-center bg-[#043e2f] rounded-lg border border-emerald-800 px-2 py-1">
            <Globe className="w-3.5 h-3.5 text-emerald-300 mr-1.5" />
            <select
              value={currentLanguage}
              onChange={(e) => onLanguageChange(e.target.value as Language)}
              className="bg-transparent text-xs text-white font-semibold focus:outline-none cursor-pointer"
            >
              <option value="en" className="bg-[#043e2f] text-white">
                English
              </option>
              <option value="hi" className="bg-[#043e2f] text-white">
                हिंदी (HI)
              </option>
              <option value="ta" className="bg-[#043e2f] text-white">
                தமிழ் (TA)
              </option>
              <option value="mr" className="bg-[#043e2f] text-white">
                मराठी (MR)
              </option>
            </select>
          </div>
        </div>
      </div>
    </header>
  );
};
