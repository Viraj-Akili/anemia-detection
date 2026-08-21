import React from 'react';
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  FileCheck,
  HeartPulse,
  Info,
  Layers,
  ListOrdered,
  Scale,
  ShieldAlert,
  ShieldCheck,
  Stethoscope,
} from 'lucide-react';
import { Beneficiary, ScreeningResult } from '../../types';

interface WhatToDoNextCardProps {
  screeningResult: ScreeningResult;
  beneficiary?: Beneficiary;
}

export const WhatToDoNextCard: React.FC<WhatToDoNextCardProps> = ({
  screeningResult,
  beneficiary,
}) => {
  const {
    overallPriority,
    anemiaRisk,
    nutritionRisk,
    triggeredSafetyRules = [],
    imageSummary,
    ppgSummary,
    imageQuality,
    recommendedAction = '',
  } = screeningResult;

  const hasRedFlags = triggeredSafetyRules.length > 0;
  const isCriticalOrUrgent =
    overallPriority === 'HIGH' && (hasRedFlags || recommendedAction.includes('REFERRAL'));
  const isHighRisk =
    !isCriticalOrUrgent &&
    (overallPriority === 'HIGH' || anemiaRisk === 'ELEVATED' || recommendedAction.includes('CONFIRMATORY'));
  const isModerateRisk =
    !isCriticalOrUrgent &&
    !isHighRisk &&
    (anemiaRisk === 'MODERATE' || overallPriority === 'MODERATE' || nutritionRisk === 'MODERATE' || nutritionRisk === 'HIGH');
  const isLowRisk = !isCriticalOrUrgent && !isHighRisk && !isModerateRisk;

  const isImagePoor =
    imageQuality === 'INSUFFICIENT' ||
    imageSummary?.quality_status === 'poor' ||
    imageSummary?.status === 'REJECTED' ||
    imageSummary?.status === 'ERROR';

  const isPpgRejected =
    ppgSummary?.available &&
    (ppgSummary.status === 'REJECTED' || ppgSummary.status === 'ERROR');

  const isPpgValid =
    ppgSummary?.available &&
    ppgSummary.status === 'SUCCESS' &&
    ppgSummary.predicted_hb_g_dl != null;

  // 1 & 5. RESULT RISK HIGHLIGHTING MAPPING
  const triageDetails = isCriticalOrUrgent
    ? {
        label: 'CRITICAL / URGENT',
        cardBg: 'bg-red-50/90 border-red-300 text-red-950',
        badgeColor: 'bg-red-600 text-white',
        dotColor: 'bg-white',
        oneLiner:
          'Screening indicates an urgent clinical or maternal/pediatric safety concern requiring immediate medical triage.',
      }
    : isHighRisk
    ? {
        label: 'HIGH RISK',
        cardBg: 'bg-red-50/70 border-red-200 text-red-950',
        badgeColor: 'bg-red-500 text-white',
        dotColor: 'bg-white',
        oneLiner:
          'Screening indicates an elevated likelihood of anemia or acute nutritional deficit warranting prompt confirmatory evaluation.',
      }
    : isModerateRisk
    ? {
        label: 'MODERATE RISK',
        cardBg: 'bg-amber-50/80 border-amber-200 text-amber-950',
        badgeColor: 'bg-amber-500 text-white',
        dotColor: 'bg-white',
        oneLiner:
          'Screening indicates a possible nutritional or anemia-related concern requiring clinical follow-up and dietary review.',
      }
    : {
        label: 'LOW RISK',
        cardBg: 'bg-emerald-50/80 border-emerald-200 text-emerald-950',
        badgeColor: 'bg-emerald-600 text-white',
        dotColor: 'bg-white',
        oneLiner:
          'Current screening findings do not indicate an immediate high-risk concern; routine monitoring is advised.',
      };

  // SECTION B: Why This Result? (3-5 strictly factual evidence bullets)
  const evidenceBullets: string[] = [];

  // 1. Conjunctival Image evidence
  if (imageSummary?.available && imageSummary.status === 'SUCCESS') {
    if (imageSummary.label === 'anemic' || anemiaRisk === 'ELEVATED') {
      evidenceBullets.push(
        `Conjunctival assessment indicates an increased anemia probability (${((imageSummary.probability || 0) * 100).toFixed(0)}% probability)`
      );
    } else {
      evidenceBullets.push(
        `Conjunctival mucosal assessment indicates a non-anemic visual pattern (${((imageSummary.probability || 0) * 100).toFixed(0)}% probability)`
      );
    }
  } else if (isImagePoor) {
    evidenceBullets.push('Conjunctival image quality was insufficient for definitive visual evaluation');
  }

  // 2. PPG Hemoglobin evidence
  if (isPpgValid && ppgSummary) {
    const hb = ppgSummary.predicted_hb_g_dl;
    if (hb != null && hb < 11.0) {
      evidenceBullets.push(
        `Optical PPG hemoglobin estimate (${hb.toFixed(1)} g/dL) is below the expected reference range`
      );
    } else if (hb != null) {
      evidenceBullets.push(
        `Optical PPG hemoglobin estimate (${hb.toFixed(1)} g/dL) is within expected physiological bounds`
      );
    }
  } else if (isPpgRejected) {
    evidenceBullets.push('Optical PPG recording was rejected by hardware quality gates and excluded');
  }

  // 3. Nutrition & Dietary evidence
  if (nutritionRisk === 'HIGH') {
    evidenceBullets.push('Dietary diversity and anthropometric indicators suggest elevated nutritional risk');
  } else if (nutritionRisk === 'MODERATE') {
    evidenceBullets.push('Dietary indicators or body mass suggest mild nutritional vulnerability');
  } else {
    evidenceBullets.push('Nutritional and growth indicators fall within expected healthy baseline parameters');
  }

  // 4. Red-flag & safety rules evidence
  if (hasRedFlags) {
    evidenceBullets.push(
      `${triggeredSafetyRules.length} priority clinical safety rule(s) triggered risk escalation`
    );
  } else {
    evidenceBullets.push('No critical WHO red flags or severe symptom triggers detected');
  }

  // SECTION C: Recommended Next Steps (Ordered Practical Steps)
  const nextSteps: string[] = isCriticalOrUrgent
    ? [
        'Seek urgent clinical evaluation at a primary health centre (PHC), community health centre, or hospital.',
        'Request urgent confirmatory laboratory venous blood testing (Complete Blood Count / CBC with Hemoglobin & Ferritin).',
        'Discuss acute symptoms, hydration, and nutritional support with an attending physician.',
        'Follow formal medical triage instructions before initiating any therapeutic interventions.',
      ]
    : isHighRisk
    ? [
        'Confirm the screening finding with a comprehensive clinical examination by a qualified healthcare provider.',
        'Consider confirmatory laboratory testing such as a Complete Blood Count (CBC) where clinically indicated.',
        'Review dietary iron bioavailability, vitamin intake, and absorption with a health worker or physician.',
        'Repeat the screening in 14 to 30 days to track trajectory and treatment response.',
      ]
    : isModerateRisk
    ? [
        'Confirm the screening finding with appropriate clinical evaluation during routine health visits.',
        'Discuss nutrition and dietary intake with a qualified healthcare professional, emphasizing iron-rich foods and Vitamin C.',
        'Ensure scheduled bi-annual deworming and preventive micronutrient supplementation are up to date.',
        'Repeat the point-of-care optical scan if symptoms such as fatigue or pallor persist.',
      ]
    : [
        'Maintain a balanced, diverse diet rich in legumes, seasonal green vegetables, and clean water.',
        'Continue routine community health monitoring and standard preventive checkups.',
        'Follow recommended public health prophylaxis (routine deworming and age-appropriate vitamins).',
        'Repeat point-of-care screening if fatigue, weakness, or unusual pallor develops.',
      ];

  return (
    <div className="bg-white rounded-[28px] p-6 sm:p-8 border border-black/[0.08] shadow-sm space-y-6">
      
      {/* Header with Prominent Risk Badge */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-black/[0.06] pb-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-[#00776b]/10 text-[#00776b] flex items-center justify-center shrink-0">
            <ClipboardCheck className="w-5 h-5 stroke-[2.2]" />
          </div>
          <div>
            <h3 className="text-[20px] font-bold text-[#1d1d1f] tracking-tight">
              WHAT TO DO NEXT
            </h3>
            <p className="text-[12px] text-[#6e6e73]">
              Recommended next steps based on the screening assessment
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-[12px] font-bold shadow-xs ${triageDetails.badgeColor}`}
          >
            <span className={`w-2 h-2 rounded-full ${triageDetails.dotColor}`} />
            <span>{triageDetails.label}</span>
          </span>
        </div>
      </div>

      {/* SECTION A: Current Assessment */}
      <div
        className={`p-5 rounded-2xl border space-y-1.5 ${triageDetails.cardBg}`}
      >
        <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider opacity-80">
          <Stethoscope className="w-3.5 h-3.5" />
          <span>Section A: Current Assessment</span>
        </div>
        <p className="text-[15px] font-bold leading-snug">
          {triageDetails.oneLiner}
        </p>
      </div>

      {/* URGENT MEDICAL CONCERN Callout (If Critical / High-Risk Safety Indicators Trigger) */}
      {isCriticalOrUrgent && (
        <div className="p-5 rounded-2xl bg-red-50 border-2 border-red-400 text-red-950 space-y-2">
          <div className="flex items-center gap-2 font-bold text-red-900 text-[14px]">
            <ShieldAlert className="w-5 h-5 text-red-600 shrink-0" />
            <span>URGENT MEDICAL CONCERN</span>
          </div>
          <p className="text-[13px] text-red-900 font-medium leading-relaxed pl-7">
            Immediate clinical evaluation is recommended based on the identified safety indicators:
          </p>
          <ul className="list-disc pl-11 space-y-1 text-[12px] text-red-900 font-medium">
            {triggeredSafetyRules.map((rule, idx) => (
              <li key={idx}>{rule}</li>
            ))}
          </ul>
        </div>
      )}

      {/* LOW RISK — ROUTINE MONITORING Callout (If Low Risk) */}
      {isLowRisk && (
        <div className="p-5 rounded-2xl bg-emerald-50/80 border border-emerald-300 text-emerald-950 space-y-1.5">
          <div className="flex items-center gap-2 font-bold text-emerald-900 text-[14px]">
            <ShieldCheck className="w-5 h-5 text-emerald-700 shrink-0" />
            <span>LOW RISK — ROUTINE MONITORING</span>
          </div>
          <p className="text-[13px] text-emerald-900 leading-relaxed pl-7">
            Current screening findings do not indicate an immediate high-risk concern. Continue standard maternal/child health checkups, maintain dietary diversity, and follow routine preventive care schedules.
          </p>
        </div>
      )}

      {/* SECTION B: Why This Result? */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-[#00776b]">
          <Layers className="w-4 h-4" />
          <h4 className="text-[13px] font-bold text-[#1d1d1f] uppercase tracking-wider">
            Section B: Why This Result?
          </h4>
        </div>
        <div className="space-y-2 pl-1">
          {evidenceBullets.map((bullet, idx) => (
            <div key={idx} className="flex items-start gap-2.5 text-[13px] text-[#333336]">
              <span className="text-[#00776b] font-bold">✓</span>
              <span className="leading-relaxed">{bullet}</span>
            </div>
          ))}
        </div>
      </div>

      {/* SECTION C: Recommended Next Steps */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-[#00776b]">
          <ListOrdered className="w-4 h-4" />
          <h4 className="text-[13px] font-bold text-[#1d1d1f] uppercase tracking-wider">
            Section C: Recommended Next Steps
          </h4>
        </div>
        <div className="space-y-2.5">
          {nextSteps.map((step, idx) => (
            <div
              key={idx}
              className="p-3.5 rounded-2xl bg-[#fbfbfd] border border-black/[0.05] text-[13px] flex items-start gap-3"
            >
              <div className="w-6 h-6 rounded-full bg-[#00776b] text-white flex items-center justify-center font-bold text-[11px] shrink-0">
                {idx + 1}
              </div>
              <span className="text-[#1d1d1f] leading-snug pt-0.5">{step}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Image / PPG Quality Warning Callouts */}
      {isImagePoor && (
        <div className="p-4 rounded-2xl bg-amber-50/90 border border-amber-200 text-amber-900 text-[12px] space-y-1">
          <div className="flex items-center gap-2 font-semibold text-amber-800">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>IMAGE QUALITY INSUFFICIENT</span>
          </div>
          <p className="leading-relaxed pl-6">
            Please recapture the conjunctival image under suitable lighting and positioning. The current image should not be used to draw a definitive screening conclusion.
          </p>
        </div>
      )}

      {isPpgRejected && (
        <div className="p-4 rounded-2xl bg-amber-50/90 border border-amber-200 text-amber-900 text-[12px] space-y-1">
          <div className="flex items-center gap-2 font-semibold text-amber-800">
            <HeartPulse className="w-4 h-4 shrink-0" />
            <span>PPG SIGNAL QUALITY INSUFFICIENT</span>
          </div>
          <p className="leading-relaxed pl-6">
            Repeat the 10-second optical PPG recording while maintaining stable finger placement. The rejected reading was excluded from clinical decisions.
          </p>
        </div>
      )}

      {/* Urgent Warning Disclaimer */}
      {(isCriticalOrUrgent || hasRedFlags) && (
        <div className="p-4 rounded-2xl bg-red-50/90 border border-red-200 text-red-950 text-[12px] space-y-1">
          <div className="flex items-center gap-2 font-bold text-red-800">
            <ShieldAlert className="w-4 h-4 text-red-600 shrink-0" />
            <span>⚠️ When to Seek Urgent Emergency Care:</span>
          </div>
          <p className="leading-relaxed pl-6">
            If severe symptoms are observed — such as <strong>marked shortness of breath at rest, chest palpitations, sudden fainting, severe confusion, or extreme physical lethargy</strong> — arrange immediate transportation to an emergency healthcare facility.
          </p>
        </div>
      )}

      {/* Safety Screening Disclaimer */}
      <div className="pt-2 border-t border-black/[0.06] flex items-start gap-2.5 text-[11px] text-[#86868b] leading-relaxed">
        <Info className="w-4 h-4 shrink-0 text-[#86868b] mt-0.5" />
        <span>
          <strong>Screening Support Disclaimer:</strong> PRAHARI is a point-of-care screening aid designed for risk stratification. It does not provide definitive medical diagnoses, prescriptions, or treatment plans. All findings should be reviewed and verified by a qualified healthcare professional.
        </span>
      </div>

    </div>
  );
};
