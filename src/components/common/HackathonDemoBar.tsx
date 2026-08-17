import React from 'react';
import { ChevronRight, ChevronLeft, Sparkles, X, Play } from 'lucide-react';

export interface DemoStep {
  id: number;
  title: string;
  actionHint: string;
}

export const DEMO_STEPS: DemoStep[] = [
  { id: 1, title: '1. Open PRAHARI System', actionHint: 'Welcome view initialized.' },
  { id: 2, title: '2. AWW Dashboard Overview', actionHint: 'Reviewing daily metrics & priority follow-ups.' },
  { id: 3, title: '3. Select Beneficiary Rahul Kumar', actionHint: 'Opening Rahul Kumar profile (Age 4).' },
  { id: 4, title: '4. Start New Guided Screening', actionHint: 'Launching 6-step screening wizard.' },
  { id: 5, title: '5. Deliberately Bad Image Capture', actionHint: 'Image Quality Gate rejects due to blur/lighting.' },
  { id: 6, title: '6. Retake with High Quality Image', actionHint: 'Palpebral conjunctiva ROI detected & validated.' },
  { id: 7, title: '7. Enter Anthropometry Measurements', actionHint: 'Weight 13.2kg, Height 99cm, MUAC 11.4cm.' },
  { id: 8, title: '8. Answer Context & Diet Questions', actionHint: 'Iron intake gap and deworming status logged.' },
  { id: 9, title: '9. Turn Airplane Mode ON (Offline)', actionHint: 'Demonstrating offline-first edge capability.' },
  { id: 10, title: '10. Run Multimodal AI Pipeline', actionHint: 'Processing staged signal pipeline...' },
  { id: 11, title: '11. Multimodal Signal Staging', actionHint: 'CV signal + MUAC z-score + Diet + Trajectory.' },
  { id: 12, title: '12. Review Risk Screening Result', actionHint: 'Anemia Risk: MODERATE | Nutrition: HIGH.' },
  { id: 13, title: '13. Inspect Multimodal Explanation', actionHint: 'Reviewing signal contribution breakdown.' },
  { id: 14, title: '14. Escalated Safety Rule & Referral', actionHint: 'SAM Rule #1 triggered PHC Referral action.' },
  { id: 15, title: '15. Save Screening to Offline Queue', actionHint: 'Screening saved locally to IndexedDB queue.' },
  { id: 16, title: '16. Open Rahul Previous Visits', actionHint: 'Navigating to historical visit record timeline.' },
  { id: 17, title: '17. Analyze Declining Trajectory', actionHint: 'Longitudinal intelligence across 3 visits.' },
  { id: 18, title: '18. Switch to Supervisor Dashboard', actionHint: 'Reviewing sector analytics and referral queue.' },
];

interface HackathonDemoBarProps {
  currentStep: number;
  onSelectStep: (stepId: number) => void;
  onClose: () => void;
}

export const HackathonDemoBar: React.FC<HackathonDemoBarProps> = ({
  currentStep,
  onSelectStep,
  onClose,
}) => {
  const activeStep = DEMO_STEPS.find((s) => s.id === currentStep) || DEMO_STEPS[0];

  const handlePrev = () => {
    if (currentStep > 1) {
      onSelectStep(currentStep - 1);
    }
  };

  const handleNext = () => {
    if (currentStep < DEMO_STEPS.length) {
      onSelectStep(currentStep + 1);
    }
  };

  return (
    <div className="bg-gradient-to-r from-slate-900 via-amber-950/90 to-slate-900 border-b border-amber-500/30 px-4 py-2.5 shadow-xl text-slate-100 sticky top-[65px] z-30">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Left Badge & Current Step Indicator */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-amber-500/20 text-amber-300 border border-amber-500/40 text-xs font-semibold uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Judge Demo Mode</span>
          </div>
          <div>
            <div className="text-xs font-bold text-amber-200 flex items-center space-x-2">
              <span>{activeStep.title}</span>
              <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full border border-slate-700">
                Step {currentStep} of {DEMO_STEPS.length}
              </span>
            </div>
            <p className="text-[11px] text-amber-100/70">{activeStep.actionHint}</p>
          </div>
        </div>

        {/* Center Progress Pips */}
        <div className="hidden lg:flex items-center space-x-1 overflow-x-auto py-1 max-w-md">
          {DEMO_STEPS.map((step) => (
            <button
              key={step.id}
              onClick={() => onSelectStep(step.id)}
              className={`w-6 h-2 rounded-full transition-all ${
                step.id === currentStep
                  ? 'bg-amber-400 w-8 shadow-sm shadow-amber-400/50'
                  : step.id < currentStep
                  ? 'bg-amber-700 hover:bg-amber-600'
                  : 'bg-slate-800 hover:bg-slate-700'
              }`}
              title={step.title}
            />
          ))}
        </div>

        {/* Right Prev / Next Navigation Controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={handlePrev}
            disabled={currentStep === 1}
            className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-slate-800 text-slate-200 hover:bg-slate-700 disabled:opacity-40 text-xs font-medium border border-slate-700"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
            <span>Prev Step</span>
          </button>
          <button
            onClick={handleNext}
            disabled={currentStep === DEMO_STEPS.length}
            className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-amber-500 text-slate-950 font-bold hover:bg-amber-400 disabled:opacity-40 text-xs shadow-md shadow-amber-500/20"
          >
            <span>Next Step</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 ml-2"
            title="Close presentation guide"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
