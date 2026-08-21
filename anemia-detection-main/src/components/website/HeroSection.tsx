import React, { useState } from 'react';
import { Eye, Shield, CheckCircle2, ChevronRight, Sparkles, RefreshCw } from 'lucide-react';

interface HeroSectionProps {
  onLaunchStudio: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ onLaunchStudio }) => {
  const [activePreviewTab, setActivePreviewTab] = useState<'optical' | 'anthro' | 'result'>('optical');

  return (
    <section id="overview" className="relative pt-32 pb-24 md:pt-44 md:pb-36 overflow-hidden bg-[#fbfbfd]">
      <div className="max-w-[1180px] mx-auto px-6 text-center">
        
        {/* Category Superhead */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-black/[0.04] text-[#6e6e73] text-[13px] font-medium mb-6 tracking-tight">
          <span>Non-Invasive Frontline Health Sentinel</span>
          <span className="w-1 h-1 rounded-full bg-[#86868b]" />
          <span className="text-[#00776b] font-semibold">WHO 2024 Aligned</span>
        </div>

        {/* Confident, Large Headline */}
        <h1 className="text-[44px] sm:text-[64px] md:text-[76px] lg:text-[84px] font-semibold tracking-display text-[#1d1d1f] leading-[1.04] max-w-4xl mx-auto mb-6">
          Early screening.<br className="hidden sm:inline" />
          <span className="text-[#1d1d1f]">Closer to the people who need it.</span>
        </h1>

        {/* Short, Editorial Explanation */}
        <p className="text-[19px] sm:text-[22px] md:text-[24px] text-[#86868b] font-normal leading-[1.45] tracking-tight max-w-2xl mx-auto mb-10">
          PRAHARI turns standard frontline smartphones into point-of-care early warning sentinels for anemia and child malnutrition.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-20">
          <button
            onClick={onLaunchStudio}
            className="apple-btn-primary px-7 py-3.5 text-[16px] inline-flex items-center gap-2 cursor-pointer shadow-md"
          >
            <span>Explore Frontline App</span>
            <ChevronRight className="w-4 h-4" />
          </button>
          
          <a
            href="#optical"
            className="apple-btn-secondary px-7 py-3.5 text-[16px] inline-flex items-center gap-2 hover:text-[#1d1d1f]"
          >
            <span>See How It Works</span>
          </a>
        </div>

        {/* Device Showcase Frame with Interactive Phone UI */}
        <div className="relative max-w-[860px] mx-auto">
          {/* Subtle Phone UI Mode Selector Pills */}
          <div className="inline-flex p-1 rounded-full bg-black/[0.05] mb-8 gap-1">
            <button
              onClick={() => setActivePreviewTab('optical')}
              className={`px-4 py-1.5 rounded-full text-[13px] font-medium transition-all ${
                activePreviewTab === 'optical'
                  ? 'bg-white text-[#1d1d1f] shadow-sm'
                  : 'text-[#6e6e73] hover:text-[#1d1d1f]'
              }`}
            >
              1. Optical Viewfinder
            </button>
            <button
              onClick={() => setActivePreviewTab('anthro')}
              className={`px-4 py-1.5 rounded-full text-[13px] font-medium transition-all ${
                activePreviewTab === 'anthro'
                  ? 'bg-white text-[#1d1d1f] shadow-sm'
                  : 'text-[#6e6e73] hover:text-[#1d1d1f]'
              }`}
            >
              2. Anthropometry Input
            </button>
            <button
              onClick={() => setActivePreviewTab('result')}
              className={`px-4 py-1.5 rounded-full text-[13px] font-medium transition-all ${
                activePreviewTab === 'result'
                  ? 'bg-white text-[#1d1d1f] shadow-sm'
                  : 'text-[#6e6e73] hover:text-[#1d1d1f]'
              }`}
            >
              3. Triage Card
            </button>
          </div>

          {/* Physical Phone Container */}
          <div className="relative mx-auto w-full max-w-[360px] sm:max-w-[380px] bg-[#000000] rounded-[52px] p-3.5 iphone-frame text-left">
            {/* Dynamic Island / Speaker Pill */}
            <div className="absolute top-6 left-1/2 -translate-x-1/2 w-28 h-6 bg-[#161617] rounded-full z-30 flex items-center justify-between px-3">
              <span className="w-2.5 h-2.5 rounded-full bg-[#0d0d0e] border border-white/10" />
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[9px] text-white/70 font-mono tracking-tighter">PRAHARI</span>
              </div>
            </div>

            {/* Phone Screen Glass */}
            <div className="relative bg-[#ffffff] rounded-[42px] overflow-hidden min-h-[640px] flex flex-col border border-white/20">
              
              {/* App Bar inside phone */}
              <div className="pt-10 px-5 pb-3 border-b border-black/[0.06] bg-white flex items-center justify-between">
                <div>
                  <p className="text-[10px] uppercase font-semibold text-[#86868b] tracking-wider">Screening Sentinel</p>
                  <p className="text-[14px] font-semibold text-[#1d1d1f]">Aarav Sharma (28m)</p>
                </div>
                <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 text-[10px] font-medium border border-emerald-200/60">
                  Offline Mode
                </span>
              </div>

              {/* Viewport 1: Optical Viewfinder */}
              {activePreviewTab === 'optical' && (
                <div className="flex-1 p-4 bg-[#0a0a0c] text-white flex flex-col justify-between relative overflow-hidden">
                  {/* Subtle Camera Grid Overlay */}
                  <div className="absolute inset-0 opacity-15 pointer-events-none bg-[radial-gradient(#ffffff_1px,transparent_1px)] [background-size:16px_16px]" />
                  
                  {/* Scanning active line */}
                  <div className="absolute left-4 right-4 h-0.5 bg-gradient-to-r from-transparent via-[#00776b] to-transparent animate-scanline" />

                  {/* Top Status Indicators inside camera */}
                  <div className="relative z-10 flex items-center justify-between bg-black/40 backdrop-blur-md px-3 py-2 rounded-xl border border-white/10 text-[11px]">
                    <div className="flex items-center gap-1.5 text-emerald-400">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Lux Optimal (420 lx)</span>
                    </div>
                    <span className="font-mono text-white/70">ROI: Palpebral</span>
                  </div>

                  {/* Anatomical Palpebral Conjunctiva ROI Target Box */}
                  <div className="relative my-auto mx-auto w-56 h-36 rounded-2xl border-2 border-dashed border-[#00776b] clinical-roi-pulse flex flex-col items-center justify-center p-3 bg-[#00776b]/10 text-center">
                    <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center mb-2">
                      <Eye className="w-5 h-5 text-[#34d399]" />
                    </div>
                    <p className="text-[12px] font-medium text-white">Lower Palpebral Conjunctiva</p>
                    <p className="text-[10px] text-white/60 mt-0.5">Hold steady • 15 cm distance</p>
                  </div>

                  {/* Bottom Camera Action */}
                  <div className="relative z-10 space-y-2">
                    <div className="bg-white/10 backdrop-blur-md rounded-xl p-2.5 text-[11px] text-white/80 flex items-center justify-between border border-white/10">
                      <span>Vascular Erythema Index</span>
                      <span className="font-mono text-emerald-400 font-semibold">0.412 (Calibrated)</span>
                    </div>
                    <button
                      onClick={() => setActivePreviewTab('anthro')}
                      className="w-full py-3 bg-[#00776b] text-white rounded-xl text-[13px] font-medium flex items-center justify-center gap-1.5 hover:bg-[#006359] transition-colors"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Capture & Proceed to MUAC</span>
                    </button>
                  </div>
                </div>
              )}

              {/* Viewport 2: Anthropometry Input */}
              {activePreviewTab === 'anthro' && (
                <div className="flex-1 p-5 bg-[#fbfbfd] flex flex-col justify-between">
                  <div className="space-y-4">
                    <div className="bg-white p-3.5 rounded-2xl border border-black/[0.06] shadow-sm">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[12px] font-medium text-[#6e6e73]">WHO MUAC Tape</span>
                        <span className="text-[11px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-md border border-amber-200/60">
                          12.1 cm (MAM Borderline)
                        </span>
                      </div>
                      {/* WHO Tri-color band representation */}
                      <div className="h-2.5 w-full rounded-full bg-slate-200 overflow-hidden flex my-2">
                        <div className="h-full bg-red-500 w-[25%]" title="Severe <11.5cm" />
                        <div className="h-full bg-amber-400 w-[20%]" title="Moderate 11.5-12.4cm" />
                        <div className="h-full bg-emerald-500 flex-1" title="Normal >=12.5cm" />
                      </div>
                      <p className="text-[11px] text-[#86868b]">Child 28 months • Target ≥ 12.5 cm</p>
                    </div>

                    <div className="grid grid-cols-2 gap-2.5">
                      <div className="bg-white p-3 rounded-xl border border-black/[0.06]">
                        <span className="text-[10px] text-[#86868b] uppercase font-semibold">Weight</span>
                        <p className="text-[16px] font-semibold text-[#1d1d1f] mt-0.5">10.8 kg</p>
                        <span className="text-[10px] text-emerald-700 font-medium">-1.2 Z-Score</span>
                      </div>
                      <div className="bg-white p-3 rounded-xl border border-black/[0.06]">
                        <span className="text-[10px] text-[#86868b] uppercase font-semibold">Height</span>
                        <p className="text-[16px] font-semibold text-[#1d1d1f] mt-0.5">86.2 cm</p>
                        <span className="text-[10px] text-emerald-700 font-medium">Within WHO range</span>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => setActivePreviewTab('result')}
                    className="w-full py-3 bg-[#1d1d1f] text-white rounded-xl text-[13px] font-medium flex items-center justify-center gap-1.5"
                  >
                    <span>Compute Risk Assessment</span>
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              )}

              {/* Viewport 3: Triage Result Card */}
              {activePreviewTab === 'result' && (
                <div className="flex-1 p-5 bg-[#fbfbfd] flex flex-col justify-between">
                  <div className="space-y-3">
                    <div className="bg-white p-4 rounded-2xl border border-amber-200/80 shadow-sm">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[11px] font-bold uppercase tracking-wider text-amber-700">Moderate Risk Flag</span>
                        <span className="text-[10px] bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full font-semibold">WHO Protocol</span>
                      </div>
                      <h4 className="text-[16px] font-semibold text-[#1d1d1f]">Potential Mild Pallor & Borderline MUAC</h4>
                      <p className="text-[12px] text-[#6e6e73] mt-1 leading-relaxed">
                        Optical pallor index (0.412) coupled with 12.1 cm MUAC indicates early nutritional vulnerability.
                      </p>
                    </div>

                    <div className="bg-white p-3.5 rounded-xl border border-black/[0.06] space-y-2">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-[#6e6e73]">Recommended Action</span>
                        <span className="font-semibold text-[#00776b]">IFA Syrup + 14-Day Review</span>
                      </div>
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-[#6e6e73]">Safety Layer Policy</span>
                        <span className="text-[#1d1d1f] font-medium">Deterministic Non-Downgrade</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <button
                      onClick={onLaunchStudio}
                      className="w-full py-3 bg-[#00776b] text-white rounded-xl text-[13px] font-medium flex items-center justify-center gap-1.5"
                    >
                      <Shield className="w-3.5 h-3.5" />
                      <span>Open in Full Studio</span>
                    </button>
                    <button
                      onClick={() => setActivePreviewTab('optical')}
                      className="w-full py-2 text-[11px] text-[#86868b] hover:text-[#1d1d1f] flex items-center justify-center gap-1"
                    >
                      <RefreshCw className="w-3 h-3" />
                      <span>Reset Mockup Preview</span>
                    </button>
                  </div>
                </div>
              )}

            </div>
          </div>

          {/* Subtext below hero showcase */}
          <p className="text-[13px] text-[#86868b] mt-8 max-w-md mx-auto">
            Interactive device preview. Operates with zero network connectivity on frontline hardware.
          </p>
        </div>

      </div>
    </section>
  );
};
