import React from 'react';
import { UserRole, Language, Beneficiary, ScreeningResult } from './types';
import { INITIAL_BENEFICIARIES } from './services/mockData';
import { Header } from './components/common/Header';
import { HackathonDemoBar } from './components/common/HackathonDemoBar';
import { ModelContractModal } from './components/common/ModelContractModal';
import { ResearchDossierModal } from './components/common/ResearchDossierModal';

// AWW Components
import { AWWHome } from './components/aww/AWWHome';
import { BeneficiaryList } from './components/aww/BeneficiaryList';
import { BeneficiaryProfile } from './components/aww/BeneficiaryProfile';
import { NewScreeningWorkflow } from './components/aww/NewScreeningWorkflow';
import { FollowUpList } from './components/aww/FollowUpList';
import { LongitudinalTrendView } from './components/aww/LongitudinalTrendView';
import { MobileBottomNav } from './components/common/MobileBottomNav';

// Supervisor & Admin Components
import { SupervisorDashboard } from './components/supervisor/SupervisorDashboard';
import { DistrictAdminDashboard } from './components/admin/DistrictAdminDashboard';

export function App() {
  const [currentRole, setCurrentRole] = React.useState<UserRole>('aww');
  const [currentLanguage, setCurrentLanguage] = React.useState<Language>('en');

  // Mobile Device Viewport Simulation Mode State
  const [isMobileSimulated, setIsMobileSimulated] = React.useState<boolean>(false);

  // Navigation tab for AWW mode
  const [activeTab, setActiveTab] = React.useState<
    'home' | 'beneficiaries' | 'profile' | 'screening' | 'followups' | 'trend'
  >('home');

  // Beneficiary State
  const [beneficiaries, setBeneficiaries] = React.useState<Beneficiary[]>(INITIAL_BENEFICIARIES);
  const [selectedBeneficiary, setSelectedBeneficiary] = React.useState<Beneficiary | undefined>(
    INITIAL_BENEFICIARIES[0] // Default to Rahul Kumar
  );

  // Hackathon Presentation Guide State
  const [isDemoFlowActive, setIsDemoFlowActive] = React.useState<boolean>(false);
  const [demoStep, setDemoStep] = React.useState<number>(1);

  // Modals
  const [isModelContractOpen, setIsModelContractOpen] = React.useState<boolean>(false);
  const [isResearchDossierOpen, setIsResearchDossierOpen] = React.useState<boolean>(false);

  // Quality gate state override for step 5 vs 6 in demo flow
  const [simulatedQuality, setSimulatedQuality] = React.useState<'GOOD' | 'BAD'>('GOOD');

  // Handler for adding a new beneficiary
  const handleAddBeneficiary = (newB: Omit<Beneficiary, 'id' | 'lastVisitDate' | 'visitHistory'>) => {
    const created: Beneficiary = {
      ...newB,
      id: `BEN-${Date.now()}`,
      lastVisitDate: new Date().toISOString().split('T')[0],
      visitHistory: [],
    };
    setBeneficiaries((prev) => [created, ...prev]);
    setSelectedBeneficiary(created);
    setActiveTab('profile');
  };

  // Handler when screening completes
  const handleScreeningComplete = (result: ScreeningResult) => {
    if (!selectedBeneficiary) return;

    const newVisit = {
      id: result.id,
      date: new Date().toISOString().split('T')[0],
      anemiaRisk: result.anemiaRisk,
      nutritionRisk: result.nutritionRisk,
      overallPriority: result.overallPriority,
      weightKg: result.anthropometry.weightKg,
      heightCm: result.anthropometry.heightCm,
      muacCm: result.anthropometry.muacCm,
      imageQuality: result.imageQuality,
      recommendedAction: result.recommendedAction,
      notes: 'Screened via PRAHARI Multimodal Guided Workflow.',
    };

    const updatedBeneficiary: Beneficiary = {
      ...selectedBeneficiary,
      anemiaRisk: result.anemiaRisk,
      nutritionRisk: result.nutritionRisk,
      overallPriority: result.overallPriority,
      trajectory: result.trajectory,
      lastVisitDate: newVisit.date,
      visitHistory: [...(selectedBeneficiary.visitHistory || []), newVisit],
    };

    setBeneficiaries((prev) =>
      prev.map((b) => (b.id === updatedBeneficiary.id ? updatedBeneficiary : b))
    );
    setSelectedBeneficiary(updatedBeneficiary);
    setActiveTab('profile');
  };

  // Handle Judge Demo Presentation Flow Step Jump
  const handleDemoStepJump = (stepId: number) => {
    setDemoStep(stepId);
    switch (stepId) {
      case 1:
      case 2:
        setCurrentRole('aww');
        setActiveTab('home');
        break;
      case 3:
        setCurrentRole('aww');
        setSelectedBeneficiary(INITIAL_BENEFICIARIES[0]); // Rahul Kumar
        setActiveTab('profile');
        break;
      case 4:
        setCurrentRole('aww');
        setSelectedBeneficiary(INITIAL_BENEFICIARIES[0]);
        setActiveTab('screening');
        setSimulatedQuality('GOOD');
        break;
      case 5:
        setCurrentRole('aww');
        setSelectedBeneficiary(INITIAL_BENEFICIARIES[0]);
        setActiveTab('screening');
        setSimulatedQuality('BAD');
        break;
      case 6:
      case 7:
      case 8:
      case 9:
      case 10:
      case 11:
      case 12:
      case 13:
      case 14:
      case 15:
        setCurrentRole('aww');
        setSelectedBeneficiary(INITIAL_BENEFICIARIES[0]);
        setActiveTab('screening');
        setSimulatedQuality('GOOD');
        break;
      case 16:
        setCurrentRole('aww');
        setSelectedBeneficiary(INITIAL_BENEFICIARIES[0]);
        setActiveTab('profile');
        break;
      case 17:
        setCurrentRole('aww');
        setActiveTab('trend');
        break;
      case 18:
        setCurrentRole('supervisor');
        break;
    }
  };

  const resetDemoData = () => {
    setBeneficiaries(INITIAL_BENEFICIARIES);
    setSelectedBeneficiary(INITIAL_BENEFICIARIES[0]);
    setActiveTab('home');
  };

  return (
    <div className="min-h-screen bg-[#f4f7f6] text-slate-900 flex flex-col font-sans selection:bg-emerald-500 selection:text-white">
      {/* Top Main Navigation Header */}
      <Header
        currentRole={currentRole}
        onRoleChange={(role) => setCurrentRole(role)}
        currentLanguage={currentLanguage}
        onLanguageChange={(lang) => setCurrentLanguage(lang)}
        onOpenModelContract={() => setIsModelContractOpen(true)}
        onOpenResearchDossier={() => setIsResearchDossierOpen(true)}
        onStartDemoFlow={() => {
          setIsDemoFlowActive(true);
          handleDemoStepJump(1);
        }}
        onResetDemoData={resetDemoData}
        isMobileSimulated={isMobileSimulated}
        onToggleMobileSimulated={() => setIsMobileSimulated((prev) => !prev)}
      />

      {/* Top Floating Hackathon Presentation Guide Bar */}
      {isDemoFlowActive && (
        <HackathonDemoBar
          currentStep={demoStep}
          onSelectStep={handleDemoStepJump}
          onClose={() => setIsDemoFlowActive(false)}
        />
      )}

      {/* Sub Navigation Bar for AWW Role */}
      {currentRole === 'aww' && (
        <div className="bg-[#044e46] px-4 py-2 sticky top-[61px] z-20 shadow-sm border-t border-emerald-800">
          <div className="max-w-4xl mx-auto flex items-center justify-between overflow-x-auto text-xs font-bold space-x-1">
            <button
              onClick={() => setActiveTab('home')}
              className={`px-3.5 py-1.5 rounded-lg transition-all ${
                activeTab === 'home'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-emerald-100 hover:bg-emerald-800/60'
              }`}
            >
              Home Dashboard
            </button>
            <button
              onClick={() => setActiveTab('beneficiaries')}
              className={`px-3.5 py-1.5 rounded-lg transition-all ${
                activeTab === 'beneficiaries'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-emerald-100 hover:bg-emerald-800/60'
              }`}
            >
              Beneficiary Registry
            </button>
            <button
              onClick={() => {
                setSelectedBeneficiary(beneficiaries[0]);
                setActiveTab('screening');
              }}
              className={`px-3.5 py-1.5 rounded-lg transition-all ${
                activeTab === 'screening'
                  ? 'bg-[#0f766e] text-white font-extrabold shadow-sm'
                  : 'bg-emerald-700 text-white hover:bg-emerald-600'
              }`}
            >
              + New Guided Screening
            </button>
            <button
              onClick={() => setActiveTab('followups')}
              className={`px-3.5 py-1.5 rounded-lg transition-all ${
                activeTab === 'followups'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-emerald-100 hover:bg-emerald-800/60'
              }`}
            >
              Follow-ups & Queue
            </button>
            <button
              onClick={() => setActiveTab('trend')}
              className={`px-3.5 py-1.5 rounded-lg transition-all ${
                activeTab === 'trend'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-emerald-100 hover:bg-emerald-800/60'
              }`}
            >
              Longitudinal Trends
            </button>
          </div>
        </div>
      )}

      {/* Main Container Content */}
      <main className={`flex-1 w-full mx-auto px-4 py-6 transition-all ${
        isMobileSimulated
          ? 'max-w-[410px] bg-slate-900 my-6 border-4 border-slate-700 rounded-[40px] shadow-2xl overflow-hidden min-h-[760px] pb-16 relative'
          : 'max-w-7xl'
      }`}>
        {/* Mobile Device Top Notch Indicator when in simulated view */}
        {isMobileSimulated && (
          <div className="w-32 h-4 bg-slate-950 rounded-b-xl mx-auto -mt-6 mb-4 flex items-center justify-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-slate-800" />
            <span className="w-10 h-1 rounded-full bg-slate-800" />
          </div>
        )}

        {/* ROLE 1: AWW MOBILE VIEWS */}
        {currentRole === 'aww' && (
          <>
            {activeTab === 'home' && (
              <AWWHome
                beneficiaries={beneficiaries}
                onStartNewScreening={(b) => {
                  if (b) setSelectedBeneficiary(b);
                  setActiveTab('screening');
                }}
                onSelectBeneficiary={(b) => {
                  setSelectedBeneficiary(b);
                  setActiveTab('profile');
                }}
                onNavigateTab={(tab) => setActiveTab(tab)}
                language={currentLanguage}
              />
            )}

            {activeTab === 'beneficiaries' && (
              <BeneficiaryList
                beneficiaries={beneficiaries}
                onSelectBeneficiary={(b) => {
                  setSelectedBeneficiary(b);
                  setActiveTab('profile');
                }}
                onStartScreening={(b) => {
                  setSelectedBeneficiary(b);
                  setActiveTab('screening');
                }}
                onAddBeneficiary={handleAddBeneficiary}
                language={currentLanguage}
              />
            )}

            {activeTab === 'profile' && selectedBeneficiary && (
              <BeneficiaryProfile
                beneficiary={selectedBeneficiary}
                onBack={() => setActiveTab('beneficiaries')}
                onStartScreening={(b) => {
                  setSelectedBeneficiary(b);
                  setActiveTab('screening');
                }}
                language={currentLanguage}
              />
            )}

            {activeTab === 'screening' && (
              <NewScreeningWorkflow
                beneficiaries={beneficiaries}
                selectedBeneficiary={selectedBeneficiary}
                onComplete={handleScreeningComplete}
                onCancel={() => setActiveTab('home')}
                language={currentLanguage}
                initialQualityState={simulatedQuality}
              />
            )}

            {activeTab === 'followups' && (
              <FollowUpList
                beneficiaries={beneficiaries}
                onSelectBeneficiary={(b) => {
                  setSelectedBeneficiary(b);
                  setActiveTab('profile');
                }}
                onStartScreening={(b) => {
                  setSelectedBeneficiary(b);
                  setActiveTab('screening');
                }}
                language={currentLanguage}
              />
            )}

            {activeTab === 'trend' && (
              <LongitudinalTrendView
                beneficiaries={beneficiaries}
                onSelectBeneficiary={(b) => {
                  setSelectedBeneficiary(b);
                  setActiveTab('profile');
                }}
                language={currentLanguage}
              />
            )}
          </>
        )}

        {/* ROLE 2: SUPERVISOR DASHBOARD */}
        {currentRole === 'supervisor' && (
          <SupervisorDashboard
            beneficiaries={beneficiaries}
            onSelectBeneficiary={(b) => {
              setSelectedBeneficiary(b);
              setCurrentRole('aww');
              setActiveTab('profile');
            }}
            language={currentLanguage}
          />
        )}

        {/* ROLE 3: DISTRICT ADMIN DASHBOARD */}
        {currentRole === 'district_admin' && (
          <DistrictAdminDashboard language={currentLanguage} />
        )}
      </main>

      {/* Native Mobile Bottom Navigation Bar for AWW Role */}
      {currentRole === 'aww' && (
        <MobileBottomNav
          activeTab={activeTab}
          onNavigateTab={(tab) => {
            if (tab === 'screening' && !selectedBeneficiary) {
              setSelectedBeneficiary(beneficiaries[0]);
            }
            setActiveTab(tab);
          }}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950 py-4 text-center text-xs text-slate-500 mb-14 md:mb-0">
        <p>PRAHARI Health System • Non-Invasive Early-Warning Risk Screening Architecture</p>
      </footer>

      {/* Model Contract Inspector Modal */}
      <ModelContractModal
        isOpen={isModelContractOpen}
        onClose={() => setIsModelContractOpen(false)}
      />

      {/* Research & Literature Dossier Modal */}
      <ResearchDossierModal
        isOpen={isResearchDossierOpen}
        onClose={() => setIsResearchDossierOpen(false)}
      />
    </div>
  );
}

export default App;
