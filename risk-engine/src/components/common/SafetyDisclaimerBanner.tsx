import React from 'react';
import { AlertTriangle, Stethoscope } from 'lucide-react';
import { Language } from '../../types';

interface SafetyDisclaimerBannerProps {
  language?: Language;
  compact?: boolean;
}

export const SafetyDisclaimerBanner: React.FC<SafetyDisclaimerBannerProps> = ({
  compact = false,
}) => {
  if (compact) {
    return (
      <div className="flex items-center space-x-2 bg-amber-50 border border-amber-200 rounded-lg px-3 py-1.5 text-amber-900 text-xs shadow-sm">
        <Stethoscope className="w-4 h-4 text-emerald-700 shrink-0" />
        <span>
          <strong>Notice:</strong> This is an AI-generated risk assessment result and NOT a clinical diagnosis. Please visit a qualified doctor for full diagnosis and confirmatory testing.
        </span>
      </div>
    );
  }

  return (
    <div className="bg-amber-50/90 border-2 border-amber-200 rounded-xl p-3.5 flex items-start space-x-3 text-xs text-amber-950 shadow-sm">
      <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
      <div>
        <div className="font-bold text-amber-900 text-sm mb-1 flex items-center space-x-1.5">
          <Stethoscope className="w-4 h-4 text-emerald-700" />
          <span>Medical AI Disclaimer</span>
        </div>
        <p className="text-amber-900 leading-relaxed font-medium">
          Notice: This screening result is an AI-generated risk assessment and NOT a clinical diagnosis. Please visit a doctor or qualified healthcare professional if you need a full diagnosis or confirmatory laboratory testing.
        </p>
      </div>
    </div>
  );
};
