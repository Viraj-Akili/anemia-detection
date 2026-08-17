import React from 'react';
import { X, BookOpen, ShieldAlert, Award, Layers } from 'lucide-react';

interface ResearchDossierModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ResearchDossierModal: React.FC<ResearchDossierModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
      <div className="bg-white border border-slate-200 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl text-slate-800 p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center justify-center">
              <BookOpen className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">PRAHARI — Research & Clinical Dossier</h2>
              <p className="text-xs text-slate-500">
                30+ Literature References (WHO 2024, Nature, PNAS, PubMed, CDSCO SaMD 2025-26)
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Executive Summary */}
        <div className="bg-emerald-50/70 p-4 rounded-xl border border-emerald-200 space-y-2 text-xs">
          <div className="font-bold text-emerald-900 flex items-center space-x-2 text-sm">
            <Award className="w-4 h-4 text-emerald-700" />
            <span>Problem Definition & Clinical Need</span>
          </div>
          <p className="text-emerald-950 leading-relaxed">
            Anemia and malnutrition share a causal pathway: iron/micronutrient-poor diets, low dietary diversity, infection/inflammation, and low birthweight drive both conditions together. WHO explicitly ties anemia screening for children to malnutrition assessment in program design. In India, NFHS-5 data shows up to 40–70% anemia prevalence in children and pregnant women.
          </p>
        </div>

        {/* WHO 2024 Revised Cutoffs Table */}
        <div className="space-y-2">
          <h3 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
            <Layers className="w-4 h-4 text-emerald-700" />
            <span>WHO 2024 Hemoglobin Thresholds (Revised Guidelines)</span>
          </h3>
          <div className="overflow-x-auto bg-slate-50 rounded-xl border border-slate-200 p-3">
            <table className="w-full text-left text-xs text-slate-700 border-collapse">
              <thead>
                <tr className="border-b border-slate-200 text-emerald-900 font-semibold">
                  <th className="py-2 px-3">Population Group</th>
                  <th className="py-2 px-3">Hb Threshold</th>
                  <th className="py-2 px-3">Guideline Note</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                <tr>
                  <td className="py-2 px-3 font-medium text-slate-900">Children 6–23 months</td>
                  <td className="py-2 px-3 text-amber-700 font-mono font-bold">Revised Cutoff</td>
                  <td className="py-2 px-3 text-slate-600">WHO 2024 revised guideline (PubMed 38910369)</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-medium text-slate-900">Children 24–59 months / 5–11 yrs</td>
                  <td className="py-2 px-3 text-amber-700 font-mono font-bold">&lt; 11.0 g/dL</td>
                  <td className="py-2 px-3 text-slate-600">Standard WHO pediatric threshold</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-medium text-slate-900">Pregnant Women (1st & 3rd Trimester)</td>
                  <td className="py-2 px-3 text-amber-700 font-mono font-bold">&lt; 11.0 g/dL</td>
                  <td className="py-2 px-3 text-slate-600">Standard ANC threshold</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-medium text-slate-900">Pregnant Women (2nd Trimester)</td>
                  <td className="py-2 px-3 text-amber-700 font-mono font-bold">&lt; 10.5 g/dL</td>
                  <td className="py-2 px-3 text-slate-600">Confirmed in WHO 2024 revision</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Competitor Matrix & White Space */}
        <div className="space-y-2">
          <h3 className="text-sm font-bold text-slate-900">State-of-the-Art Research & Competitor Landscape</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-1">
              <div className="font-bold text-emerald-900">AnemoCheck / Sanguina (PNAS 2025)</div>
              <p className="text-slate-600">
                Fingernail photo, &gt;1.4M real-world app uses. 89% sensitivity, 93% specificity. Single-condition (anemia only), US consumer app.
              </p>
            </div>
            <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-1">
              <div className="font-bold text-emerald-900">HemaApp (Univ. of Washington, 2016)</div>
              <p className="text-slate-600">
                Nexus 5 camera + LED transillumination. 79–86% accuracy. Never productized at scale, requires extra light source.
              </p>
            </div>
            <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-1">
              <div className="font-bold text-emerald-900">Child Growth Monitor (Welthungerhilfe/Microsoft)</div>
              <p className="text-slate-600">
                3D depth scan for malnutrition anthropometry in India. Requires depth-sensor phones, cloud dependent, no anemia module.
              </p>
            </div>
            <div className="bg-emerald-50/80 p-3.5 rounded-xl border border-emerald-300 space-y-1">
              <div className="font-bold text-emerald-900">PRAHARI White Space Solution</div>
              <p className="text-emerald-800 font-medium">
                Fuses anemia + malnutrition + longitudinal trend + deterministic safety rules + POSHAN Tracker compatibility into ONE offline app.
              </p>
            </div>
          </div>
        </div>

        {/* Regulatory SaMD Framework */}
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-xs text-amber-900 space-y-2">
          <div className="font-bold text-amber-950 flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4 text-amber-700" />
            <span>CDSCO SaMD & Medical Disclaimer Compliance</span>
          </div>
          <p className="text-amber-900 leading-relaxed">
            Under India's CDSCO Medical Device Software guidance (draft Oct 2025, formalizing 2025-26), disease screening software is captured as Software as a Medical Device (SaMD). PRAHARI is designed explicitly as a non-invasive risk screening and decision support tool — NOT a diagnostic device.
          </p>
        </div>

        <div className="flex justify-end border-t border-slate-100 pt-4">
          <button onClick={onClose} className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs shadow-sm">
            Close Dossier View
          </button>
        </div>
      </div>
    </div>
  );
};
