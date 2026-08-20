import React, { useRef, useState } from 'react';
import {
  Camera,
  Upload,
  Check,
  RefreshCw,
  Eye,
  Sliders,
  Image as ImageIcon,
  AlertCircle,
  Sparkles,
} from 'lucide-react';

interface OpticalCaptureZoneProps {
  roiRegion: 'Palpebral Conjunctiva' | 'Nail Bed';
  onChangeRoi: (roi: 'Palpebral Conjunctiva' | 'Nail Bed') => void;
  capturedImage: string | null;
  onImageCaptured: (imageUri: string | null) => void;
  simulatedQuality: 'GOOD' | 'BAD';
  onToggleQuality: () => void;
}

export const OpticalCaptureZone: React.FC<OpticalCaptureZoneProps> = ({
  roiRegion,
  onChangeRoi,
  capturedImage,
  onImageCaptured,
  simulatedQuality,
  onToggleQuality,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) {
          onImageCaptured(event.target.result as string);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) {
          onImageCaptured(event.target.result as string);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="space-y-5">
      
      {/* Header with ROI Selector */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <span className="text-[12px] font-mono text-[#86868b] uppercase tracking-wider">Step 02 of 03</span>
          <h2 className="text-[26px] font-semibold text-[#1d1d1f] tracking-title mt-0.5">
            Optical Conjunctiva Capture
          </h2>
          <p className="text-[14px] text-[#6e6e73]">
            Upload or capture a close-up photo of the lower inner eyelid in natural light.
          </p>
        </div>

        <div className="flex items-center p-1 rounded-full bg-[#f5f5f7] border border-black/[0.04]">
          <button
            type="button"
            onClick={() => onChangeRoi('Palpebral Conjunctiva')}
            className={`px-3.5 py-1.5 rounded-full text-[12px] font-medium transition-all ${
              roiRegion === 'Palpebral Conjunctiva' ? 'bg-white text-[#1d1d1f] shadow-sm font-semibold' : 'text-[#6e6e73]'
            }`}
          >
            Lower Eyelid
          </button>
          <button
            type="button"
            onClick={() => onChangeRoi('Nail Bed')}
            className={`px-3.5 py-1.5 rounded-full text-[12px] font-medium transition-all ${
              roiRegion === 'Nail Bed' ? 'bg-white text-[#1d1d1f] shadow-sm font-semibold' : 'text-[#6e6e73]'
            }`}
          >
            Nail Bed
          </button>
        </div>
      </div>

      {/* Viewfinder / Upload Container */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`relative bg-[#0c0d10] rounded-[32px] overflow-hidden min-h-[340px] flex flex-col items-center justify-center border transition-all ${
          dragActive ? 'border-[#00776b] ring-4 ring-[#00776b]/20' : 'border-black/[0.1]'
        }`}
      >
        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          onChange={handleFileUpload}
          className="hidden"
        />

        {capturedImage ? (
          /* User's Actual Uploaded Image Preview */
          <div className="relative w-full h-[340px] flex items-center justify-center bg-black">
            <img
              src={capturedImage}
              alt="Uploaded Optical Target"
              className="w-full h-full object-contain"
            />

            {/* ROI Overlay Frame */}
            <div className="absolute inset-8 border-2 border-[#00776b] rounded-2xl clinical-roi-pulse flex flex-col justify-between p-3 pointer-events-none z-10 bg-[#00776b]/10">
              <div className="flex justify-between items-center text-[10px] font-medium text-white bg-black/70 backdrop-blur-md px-2.5 py-1 rounded-full self-start border border-white/10">
                Target: {roiRegion}
              </div>
              <div className="text-center text-[11px] font-medium text-white bg-black/70 backdrop-blur-md py-1 px-3 rounded-full self-center border border-white/10">
                Region of Interest (ROI) Locked & Calibrated
              </div>
            </div>

            {/* Clear / Retake button overlay */}
            <button
              onClick={() => onImageCaptured(null)}
              className="absolute top-4 right-4 z-20 px-3 py-1.5 rounded-full bg-black/70 backdrop-blur-md text-white text-[12px] hover:bg-black border border-white/15 flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Change Photo</span>
            </button>
          </div>
        ) : (
          /* Clean Minimal Anatomical Guide (No Person Stock Photos) */
          <div className="p-8 text-center space-y-4 max-w-sm">
            <div className="w-16 h-16 rounded-full bg-[#161617] border border-white/10 flex items-center justify-center text-[#00776b] mx-auto shadow-inner">
              <Eye className="w-8 h-8 stroke-[1.8]" />
            </div>

            <div className="space-y-1">
              <h4 className="text-[16px] font-semibold text-white">
                {roiRegion === 'Palpebral Conjunctiva' ? 'Target: Lower Eyelid Mucosa' : 'Target: Fingernail Bed'}
              </h4>
              <p className="text-[12px] text-white/60 leading-relaxed">
                Gently pull down the lower eyelid to expose the pink inner mucosal vascular bed, then take or upload a photo in bright natural light.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-2 justify-center pt-2">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="apple-btn-accent px-5 py-3 text-[13px] inline-flex items-center justify-center gap-2 shadow-sm"
              >
                <Camera className="w-4 h-4" />
                <span>Take or Upload Photo</span>
              </button>
            </div>

            <span className="text-[11px] text-white/40 block">
              PNG, JPG, or HEIC up to 15MB • No data stored externally
            </span>
          </div>
        )}

        {/* Bottom Illumination & Quality Bar */}
        <div className="w-full bg-black/80 backdrop-blur-md px-5 py-3 border-t border-white/10 flex items-center justify-between text-[11px] text-white">
          <div className="flex items-center gap-3">
            <span className="flex items-center text-emerald-400 font-medium">
              <Check className="w-3.5 h-3.5 mr-1" /> Illumination: 460 lx (Optimal)
            </span>
            <span className="flex items-center text-emerald-400 font-medium hidden sm:flex">
              <Check className="w-3.5 h-3.5 mr-1" /> 2024 WHO Optical Pallor Standard
            </span>
          </div>

          <button
            type="button"
            onClick={onToggleQuality}
            className="px-2.5 py-1 rounded-full bg-white/10 hover:bg-white/20 text-white text-[10px] border border-white/10"
          >
            Quality: {simulatedQuality}
          </button>
        </div>

      </div>

    </div>
  );
};
