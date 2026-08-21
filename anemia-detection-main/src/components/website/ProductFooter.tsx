import React from 'react';
import { Activity } from 'lucide-react';

interface ProductFooterProps {
  onOpenModelContract: () => void;
  onOpenResearchDossier: () => void;
  onLaunchStudio: () => void;
}

export const ProductFooter: React.FC<ProductFooterProps> = ({
  onOpenModelContract,
  onOpenResearchDossier,
  onLaunchStudio,
}) => {
  return (
    <footer className="bg-[#f5f5f7] border-t border-black/[0.08] py-16 text-[#6e6e73] text-[12px] leading-relaxed">
      <div className="max-w-[1180px] mx-auto px-6">
        
        {/* Footnote Disclaimers */}
        <div className="space-y-3 pb-10 border-b border-black/[0.08]">
          <p>
            1. <strong>WHO 2024 Guideline Compliance:</strong> Threshold algorithms enforce the revised World Health Organization hemoglobin concentrations for the diagnosis of anemia and assessment of severity (PubMed ID: 38910369).
          </p>
          <p>
            2. <strong>Optical Sensing Range:</strong> Non-invasive conjunctival pallor screening is optimized for palpebral mucosal erythema index (ΔE) under calibrated ambient illumination (300–800 lux).
          </p>
          <p>
            3. <strong>Data Privacy & Offline Security:</strong> All beneficiary photographic captures and anthropometric data are processed entirely on-device and stored in local encrypted databases.
          </p>
        </div>

        {/* Footer Navigation Columns */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 py-10 border-b border-black/[0.08]">
          <div>
            <h5 className="font-semibold text-[#1d1d1f] mb-3">Product</h5>
            <ul className="space-y-2">
              <li><a href="#overview" className="hover:text-[#1d1d1f]">Overview</a></li>
              <li><a href="#optical" className="hover:text-[#1d1d1f]">Optical Screening</a></li>
              <li><a href="#anthropometry" className="hover:text-[#1d1d1f]">WHO Anthropometry</a></li>
              <li><a href="#safety" className="hover:text-[#1d1d1f]">Safety Engine</a></li>
            </ul>
          </div>

          <div>
            <h5 className="font-semibold text-[#1d1d1f] mb-3">Frontline</h5>
            <ul className="space-y-2">
              <li><a href="#frontline" className="hover:text-[#1d1d1f]">Field Architecture</a></li>
              <li><button onClick={onLaunchStudio} className="hover:text-[#1d1d1f] text-left">Anganwadi Mode</button></li>
              <li><button onClick={onLaunchStudio} className="hover:text-[#1d1d1f] text-left">Supervisor Portal</button></li>
            </ul>
          </div>

          <div>
            <h5 className="font-semibold text-[#1d1d1f] mb-3">Clinical Science</h5>
            <ul className="space-y-2">
              <li><button onClick={onOpenModelContract} className="hover:text-[#1d1d1f] text-left">Model Contract</button></li>
              <li><button onClick={onOpenResearchDossier} className="hover:text-[#1d1d1f] text-left">Research Dossier</button></li>
              <li><a href="#safety" className="hover:text-[#1d1d1f]">WHO 2024 Standards</a></li>
            </ul>
          </div>

          <div>
            <h5 className="font-semibold text-[#1d1d1f] mb-3">Platform</h5>
            <ul className="space-y-2">
              <li><span className="text-[#86868b]">Offline-First Web App</span></li>
              <li><span className="text-[#86868b]">Android PWA Ready</span></li>
              <li><span className="text-[#86868b]">Zero External Sensors</span></li>
            </ul>
          </div>
        </div>

        {/* Copyright & Bottom Bar */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-[#1d1d1f] flex items-center justify-center text-white">
              <Activity className="w-2.5 h-2.5 stroke-[2.5]" />
            </div>
            <span className="font-medium text-[#1d1d1f]">PRAHARI Health System</span>
            <span className="text-[#86868b]">— Smartphone-First Early Warning Platform</span>
          </div>

          <p className="text-[#86868b]">
            Designed for Frontline Community Health Workers
          </p>
        </div>

      </div>
    </footer>
  );
};
