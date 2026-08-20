import React, { useState } from 'react';
import { Eye, Sun, Camera, CheckCircle2, ShieldCheck, Focus } from 'lucide-react';

export const OpticalScreeningSection: React.FC = () => {
  const [selectedZone, setSelectedZone] = useState<'palpebral' | 'erythema' | 'lux'>('palpebral');

  return (
    <section id="optical" className="py-28 md:py-40 bg-[#000000] text-white overflow-hidden relative">
      <div className="max-w-[1180px] mx-auto px-6">
        
        {/* Supertitle & Section Header */}
        <div className="flex items-center gap-3 mb-6">
          <span className="text-[13px] font-mono font-medium text-[#86868b] tracking-wider uppercase">03 — Optical Screening</span>
          <span className="h-[1px] w-12 bg-white/20" />
        </div>

        <div className="max-w-3xl mb-16">
          <h2 className="text-[38px] sm:text-[52px] md:text-[64px] font-semibold tracking-display text-white leading-[1.04] mb-6">
            Micro-vascular pallor.<br />Captured in natural light.
          </h2>
          <p className="text-[19px] sm:text-[22px] text-[#a1a1a6] font-normal leading-[1.45] tracking-tight">
            The lower palpebral conjunctiva provides a direct optical window into capillary hemoglobin saturation. PRAHARI calculates tissue erythema without clinical invasiveness.
          </p>
        </div>

        {/* Interactive Feature Showcase: Big Device Centerpiece + Editorial Callouts */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          
          {/* Left: Real-time Optical Device Viewfinder Mockup */}
          <div className="lg:col-span-7 flex justify-center">
            <div className="w-full max-w-[420px] bg-[#161617] rounded-[48px] p-3.5 iphone-frame-dark border border-white/10 relative">
              
              {/* Device Notch Header */}
              <div className="w-24 h-5 bg-[#0a0a0c] rounded-full mx-auto mb-3 flex items-center justify-center">
                <span className="w-2 h-2 rounded-full bg-white/20" />
              </div>

              {/* Viewfinder Display */}
              <div className="relative rounded-[36px] bg-[#0c0d10] overflow-hidden min-h-[520px] flex flex-col justify-between p-5 border border-white/10">
                
                {/* Top Status Bar */}
                <div className="flex items-center justify-between z-20">
                  <div className="flex items-center gap-2 bg-black/60 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-[11px] font-mono text-emerald-300">Target Acquired</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-[11px] text-white/70 bg-black/60 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10">
                    <Sun className="w-3.5 h-3.5 text-amber-400" />
                    <span>460 Lux (Optimal)</span>
                  </div>
                </div>

                {/* Center Visual: The Anatomical Scanning ROI Frame */}
                <div className="relative my-auto flex flex-col items-center justify-center">
                  
                  {/* Subtle Scanning Grid Pattern */}
                  <div className="w-64 h-48 rounded-3xl border-2 border-[#00776b] clinical-roi-pulse bg-[#00776b]/10 relative flex items-center justify-center overflow-hidden">
                    
                    {/* Crosshair guide */}
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                      <div className="w-12 h-[1px] bg-[#00776b]" />
                      <div className="h-12 w-[1px] bg-[#00776b]" />
                    </div>

                    <div className="text-center p-4 z-10">
                      <Eye className="w-8 h-8 text-emerald-400 mx-auto mb-2 opacity-90" />
                      <p className="text-[13px] font-semibold text-white">Palpebral Mucosa ROI</p>
                      <p className="text-[11px] text-white/60 mt-0.5">Automated Quality Gate: Passed</p>
                    </div>

                    {/* Scanning Beam */}
                    <div className="absolute left-0 right-0 h-1 bg-gradient-to-r from-transparent via-emerald-400 to-transparent animate-scanline" />
                  </div>

                  {/* Dynamic Metric Tag */}
                  <div className="mt-4 px-4 py-2 bg-black/70 backdrop-blur-md rounded-2xl border border-white/10 flex items-center gap-4 text-[12px]">
                    <div>
                      <span className="text-[#86868b] block text-[10px] uppercase">Erythema Index</span>
                      <span className="font-mono font-semibold text-emerald-400">0.389 ΔE</span>
                    </div>
                    <div className="h-6 w-[1px] bg-white/10" />
                    <div>
                      <span className="text-[#86868b] block text-[10px] uppercase">Image Quality</span>
                      <span className="font-mono font-semibold text-white">98.4% Clear</span>
                    </div>
                  </div>
                </div>

                {/* Bottom Viewfinder Instruction */}
                <div className="bg-white/5 backdrop-blur-md rounded-2xl p-3 border border-white/10 text-center">
                  <p className="text-[12px] text-white/80 font-medium">
                    Guidance: Evert lower eyelid gently • Keep distance steady at 15cm
                  </p>
                </div>

              </div>
            </div>
          </div>

          {/* Right: Technical Highlights & Interactive Explanations */}
          <div className="lg:col-span-5 space-y-6">
            
            <div
              onClick={() => setSelectedZone('palpebral')}
              className={`p-6 rounded-3xl border transition-all cursor-pointer ${
                selectedZone === 'palpebral'
                  ? 'bg-white/10 border-white/30 ring-1 ring-white/20'
                  : 'bg-white/5 border-white/5 hover:bg-white/[0.08]'
              }`}
            >
              <div className="flex items-center gap-3 mb-2">
                <Focus className="w-5 h-5 text-emerald-400" />
                <h3 className="text-[18px] font-semibold text-white">Targeted Palpebral Mucosa</h3>
              </div>
              <p className="text-[14px] text-[#a1a1a6] leading-relaxed">
                Unlike external skin with variable melanin pigmentation, the inner eyelid conjunctiva provides an unobstructed vascular bed for optical pallor assessment.
              </p>
            </div>

            <div
              onClick={() => setSelectedZone('erythema')}
              className={`p-6 rounded-3xl border transition-all cursor-pointer ${
                selectedZone === 'erythema'
                  ? 'bg-white/10 border-white/30 ring-1 ring-white/20'
                  : 'bg-white/5 border-white/5 hover:bg-white/[0.08]'
              }`}
            >
              <div className="flex items-center gap-3 mb-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <h3 className="text-[18px] font-semibold text-white">Real-Time Quality Gating</h3>
              </div>
              <p className="text-[14px] text-[#a1a1a6] leading-relaxed">
                Automatic checks reject blurry frames, motion jitter, or glare before inference begins — ensuring only clinically valid captures are analyzed.
              </p>
            </div>

            <div
              onClick={() => setSelectedZone('lux')}
              className={`p-6 rounded-3xl border transition-all cursor-pointer ${
                selectedZone === 'lux'
                  ? 'bg-white/10 border-white/30 ring-1 ring-white/20'
                  : 'bg-white/5 border-white/5 hover:bg-white/[0.08]'
              }`}
            >
              <div className="flex items-center gap-3 mb-2">
                <Sun className="w-5 h-5 text-amber-400" />
                <h3 className="text-[18px] font-semibold text-white">Ambient Light Normalization</h3>
              </div>
              <p className="text-[14px] text-[#a1a1a6] leading-relaxed">
                Calibrates for fluctuating village sunlight, household bulb lighting, or outdoor shade using adaptive on-device white balance compensation.
              </p>
            </div>

          </div>

        </div>

      </div>
    </section>
  );
};
