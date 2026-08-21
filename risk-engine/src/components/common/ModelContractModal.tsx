import React from 'react';
import { X, Cpu, CheckCircle, Code2, Shield, Layers } from 'lucide-react';

interface ModelContractModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ModelContractModal: React.FC<ModelContractModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl text-slate-100 p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-950 text-cyan-400 border border-cyan-800 flex items-center justify-center">
              <Cpu className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">AI Model Integration Contract</h2>
              <p className="text-xs text-slate-400">
                Boundaries for <span className="text-cyan-400">anemia-detection</span> repository API integration
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Integration Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
            <div className="flex items-center space-x-2 text-cyan-400 text-xs font-semibold mb-1">
              <Layers className="w-4 h-4" />
              <span>Input ROI Region</span>
            </div>
            <div className="text-sm font-medium text-white">Palpebral Conjunctiva</div>
            <p className="text-[11px] text-slate-400 mt-1">Lower eyelid mucosa & nail bed tissue optical signal.</p>
          </div>

          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
            <div className="flex items-center space-x-2 text-emerald-400 text-xs font-semibold mb-1">
              <CheckCircle className="w-4 h-4" />
              <span>Normalized Output</span>
            </div>
            <div className="text-sm font-medium text-white">Class Probabilities</div>
            <p className="text-[11px] text-slate-400 mt-1">Risk probability vector: LOW, MODERATE, ELEVATED.</p>
          </div>

          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
            <div className="flex items-center space-x-2 text-amber-400 text-xs font-semibold mb-1">
              <Shield className="w-4 h-4" />
              <span>Safety Contract</span>
            </div>
            <div className="text-sm font-medium text-white">No Clinical Claims</div>
            <p className="text-[11px] text-slate-400 mt-1">Classification probabilities mapped strictly to screening risk.</p>
          </div>
        </div>

        {/* Code Contract Preview */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs font-semibold text-slate-300 flex items-center space-x-2">
              <Code2 className="w-4 h-4 text-cyan-400" />
              <span>Normalized TypeScript Integration Schema</span>
            </div>
            <span className="text-[10px] text-slate-500 font-mono">src/services/anemiaModelService.ts</span>
          </div>
          <pre className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs text-cyan-300/90 overflow-x-auto leading-relaxed">
{`interface AnemiaModelOutput {
  anemiaRisk: 'LOW' | 'MODERATE' | 'ELEVATED';
  confidenceScore: number; // 0.00 to 1.00
  palpebralPallorScore: number; // Optical RGB red-chroma ratio index
  imageQuality: 'GOOD' | 'INSUFFICIENT';
  qualityIssues?: string[];
  modelMetadata: {
    architectureName: string; // e.g. MobileNetV3 / EfficientNet
    version: string;
    expectedInputFormat: 'RGB 224x224 Tensor';
    roiRegion: 'Palpebral Conjunctiva (Lower Eyelid)';
  };
}`}
          </pre>
        </div>

        {/* Integration Guidelines */}
        <div className="bg-cyan-950/40 border border-cyan-800/60 rounded-xl p-4 text-xs text-cyan-200 space-y-2">
          <div className="font-semibold text-cyan-300">Model Coupling Architecture Rules:</div>
          <ul className="list-disc pl-4 space-y-1 text-slate-300">
            <li>The UI consumes normalized result objects from <code className="text-cyan-300">anemiaModelService</code>.</li>
            <li>No hardcoded diagnostic Hb lab values are produced by the computer vision model.</li>
            <li>If the Python backend model is updated, the service abstraction transforms model tensors into the normalized contract without disrupting the frontend screening workflow.</li>
          </ul>
        </div>

        {/* Footer */}
        <div className="flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 text-slate-200 hover:bg-slate-700 text-xs font-semibold transition-colors"
          >
            Close Contract View
          </button>
        </div>
      </div>
    </div>
  );
};
