import React from 'react';
import { WifiOff, Sun, Smartphone, Globe2, Zap, BatteryCharging } from 'lucide-react';

export const FrontlineDesignSection: React.FC = () => {
  const fieldFeatures = [
    {
      icon: WifiOff,
      title: '100% Offline-First',
      description: 'Zero dependence on cellular towers or rural internet. All computer vision and WHO algorithms execute locally on-device.',
    },
    {
      icon: Sun,
      title: 'Outdoor Sunlight Legibility',
      description: 'High-contrast typography and clear indicator bands engineered for harsh outdoor daylight and unshaded village courtyards.',
    },
    {
      icon: Smartphone,
      title: 'Runs on Everyday Hardware',
      description: 'Optimized for entry-level Android devices commonly supplied in national frontline health programs, requiring no expensive external attachments.',
    },
    {
      icon: Globe2,
      title: 'Native Multilingual Support',
      description: 'Instant zero-lag interface translation between English, Hindi, and Odia to match community worker language preferences.',
    },
    {
      icon: Zap,
      title: '45-Second Screening Time',
      description: 'Streamlined step-by-step workflow designed to minimize screening friction during high-volume village Anganwadi sessions.',
    },
    {
      icon: BatteryCharging,
      title: 'Low Power Consumption',
      description: 'Lightweight on-device processing maintains full-day battery life on budget smartphone hardware.',
    },
  ];

  return (
    <section id="frontline" className="py-28 md:py-36 bg-[#ffffff] border-t border-black/[0.04]">
      <div className="max-w-[1180px] mx-auto px-6">
        
        {/* Section Header */}
        <div className="flex items-center gap-3 mb-6">
          <span className="text-[13px] font-mono font-medium text-[#86868b] tracking-wider uppercase">06 — Designed for the Frontline</span>
          <span className="h-[1px] w-12 bg-black/[0.1]" />
        </div>

        <div className="max-w-3xl mb-16">
          <h2 className="text-[36px] sm:text-[48px] md:text-[56px] font-semibold tracking-title text-[#1d1d1f] leading-[1.08] mb-6">
            Engineered for the realities of the field.
          </h2>
          <p className="text-[19px] sm:text-[21px] text-[#6e6e73] font-normal leading-[1.5]">
            Real-world community health happens in rural hamlets without broadband, under direct sunlight, on budget smartphones. PRAHARI is built from the ground up for these exact environments.
          </p>
        </div>

        {/* 6-Grid Feature Layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {fieldFeatures.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.title}
                className="p-8 rounded-[28px] bg-[#fbfbfd] border border-black/[0.05] hover:border-black/[0.12] transition-colors"
              >
                <div className="w-12 h-12 rounded-2xl bg-white flex items-center justify-center text-[#1d1d1f] shadow-sm mb-6 border border-black/[0.04]">
                  <Icon className="w-6 h-6 stroke-[1.75]" />
                </div>
                <h3 className="text-[19px] font-semibold text-[#1d1d1f] tracking-tight mb-2">
                  {item.title}
                </h3>
                <p className="text-[14px] text-[#6e6e73] leading-relaxed">
                  {item.description}
                </p>
              </div>
            );
          })}
        </div>

      </div>
    </section>
  );
};
