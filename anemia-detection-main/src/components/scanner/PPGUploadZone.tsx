import React, { useRef, useState } from 'react';
import { Activity, Upload, Check, AlertCircle, FileText, Sparkles, X, RefreshCw } from 'lucide-react';

interface PPGUploadZoneProps {
  ppgFile: File | null;
  onPPGFileChange: (file: File | null) => void;
}

// Embedded real 10-second 25Hz MAX30102 hardware recording from Arya hardware pipeline
const SAMPLE_HARDWARE_CSV = `timestamp_ms,red,ir
0,217942,248355
40,217615,247730
80,217392,247592
120,217550,248161
160,217939,248861
200,218274,249339
240,218320,249258
280,218086,248740
320,217730,248039
360,217435,247492
400,217325,247462
440,217466,247849
480,217769,248496
520,218063,248981
560,218206,249089
600,218076,248729
640,217757,248074
680,217454,247490
720,217336,247427
760,217458,247805
800,217743,248408
840,218029,248911
880,218171,249045
920,218064,248741
960,217772,248119
1000,217466,247545
1040,217328,247444
1080,217415,247775
1120,217696,248348
1160,217983,248849
1200,218131,248995
1240,218041,248700
1280,217744,248099
1320,217441,247530
1360,217316,247443
1400,217417,247777
1440,217688,248350
1480,217987,248881
1520,218151,249056
1560,218086,248809
1600,217805,248232
1640,217498,247656
1680,217348,247514
1720,217416,247814
1760,217666,248355
1800,217937,248840
1840,218084,248972
1880,218015,248714
1920,217740,248141
1960,217450,247576
2000,217322,247468
2040,217387,247766
2080,217631,248301
2120,217894,248777
2160,218037,248911
2200,217970,248671
2240,217700,248113
2280,217424,247565
2320,217309,247467
2360,217377,247763
2400,217615,248283
2440,217872,248744
2480,218004,248873
2520,217938,248630
2560,217677,248083
2600,217409,247545
2640,217301,247448
2680,217366,247738
2720,217591,248234
2760,217838,248684
2800,217967,248812
2840,217904,248574
2880,217646,248037
2920,217385,247514
2960,217281,247425
3000,217336,247701
3040,217551,248186
3080,217789,248625
3120,217918,248753
3160,217859,248523
3200,217604,247990
3240,217349,247477
3280,217247,247385
3320,217296,247653
3360,217502,248128
3400,217734,248555
3440,217859,248679
3480,217798,248446
3520,217544,247915
3560,217292,247407
3600,217192,247318
3640,217237,247576
3680,217435,248038
3720,217660,248455
3760,217778,248574
3800,217714,248338
3840,217459,247812
3880,217210,247314
3920,217112,247228
3960,217154,247481
4000,217346,247934
4040,217565,248342
4080,217679,248457
4120,217614,248220
4160,217359,247697
4200,217113,247206
4240,217017,247124
4280,217056,247372
4320,217243,247817
4360,217457,248216
4400,217567,248327
4440,217501,248089
4480,217247,247569
4520,217005,247087
4560,216912,247009
4600,216949,247250
4640,217130,247688
4680,217338,248080
4720,217446,248188
4760,217380,247952
4800,217128,247436
4840,216891,246961
4880,216801,246889
4920,216838,247125
4960,217014,247556
5000,217217,247940
5040,217322,248046
5080,217256,247810
5120,217007,247298
5160,216773,246828
5200,216688,246761
5240,216726,246995
5280,216898,247419
5320,217096,247796
5360,217198,247898
5400,217133,247664
5440,216887,247157
5480,216658,246695
5520,216578,246634
5560,216616,246864
5600,216784,247282
5640,216977,247653
5680,217076,247752
5720,217011,247520
5760,216770,247020
5800,216546,246566
5840,216472,246511
5880,216510,246738
5920,216674,247150
5960,216863,247514
6000,216960,247610
6040,216896,247380
6080,216659,246888
6120,216441,246445
6160,216373,246397
6200,216410,246620
6240,216570,247026
6280,216755,247384
6320,216850,247477
6360,216788,247250
6400,216556,246767
6440,216345,246334
6480,216284,246294
6520,216321,246513
6560,216476,246914
6600,216655,247264
6640,216747,247353
6680,216687,247130
6720,216462,246659
6760,216259,246237
6800,216206,246205
6840,216242,246421
6880,216393,246814
6920,216566,247156
6960,216655,247241
7000,216597,247022
7040,216378,246561
7080,216183,246150
7120,216138,246128
7160,216174,246342
7200,216320,246727
7240,216487,247060
7280,216572,247141
7320,216515,246924
7360,216301,246473
7400,216113,246074
7440,216075,246061
7480,216111,246272
7520,216253,246648
7560,216414,246973
7600,216495,247049
7640,216439,246834
7680,216230,246394
7720,216049,246006
7760,216018,246002
7800,216053,246210
7840,216190,246578
7880,216346,246894
7920,216422,246965
7960,216367,246751
8000,216162,246320
8040,215988,245943
8080,215964,245948
8120,215998,246153
8160,216131,246513
8200,216281,246820
8240,216353,246886
8280,216298,246673
8320,216098,246251
8360,215931,245885
8400,215913,245898
8440,215946,246101
8480,216075,246452
8520,216218,246750
8560,216285,246811
8600,216229,246598
8640,216035,246184
8680,215876,245828
8720,215865,245849
8760,215897,246051
8800,216021,246394
8840,216158,246682
8880,216219,246737
8920,216161,246522
8960,215972,246115
9000,215821,245770
9040,215816,245799
9080,215848,245999
9120,215968,246334
9160,216099,246613
9200,216154,246661
9240,216093,246443
9280,215910,246044
9320,215767,245709
9360,215767,245747
9400,215798,245946
9440,215913,246271
9480,216039,246540
9520,216089,246581
9560,216023,246358
9600,215847,245967
9640,215712,245642
9680,215717,245689
9720,215747,245888
9760,215858,246203
9800,215977,246462
9840,216021,246497
9880,215951,246267
9920,215781,245882
9960,215654,245567
`;

export const PPGUploadZone: React.FC<PPGUploadZoneProps> = ({ ppgFile, onPPGFileChange }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [sampleCount, setSampleCount] = useState<number | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  const validateAndSetFile = (file: File) => {
    setValidationError(null);
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setValidationError('Please select a CSV file (.csv)');
      onPPGFileChange(null);
      return;
    }

    // Set file immediately into state to prevent race conditions with async reader
    onPPGFileChange(file);

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        const lines = text.trim().split(/\r?\n/);
        if (lines.length < 2) {
          setValidationError('CSV file appears empty or missing header');
          return;
        }
        const header = lines[0].toLowerCase();
        if (!header.includes('red') || !header.includes('ir')) {
          setValidationError('Invalid header. Expected columns: timestamp_ms,red,ir');
          return;
        }

        const count = lines.length - 1;
        setSampleCount(count);
      } catch (err: any) {
        console.warn('PPG CSV parsing notice:', err);
      }
    };
    reader.onerror = () => {
      setValidationError('Failed to read CSV file content');
    };
    reader.readAsText(file);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      validateAndSetFile(file);
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
      validateAndSetFile(file);
    }
  };

  const handleLoadSampleCSV = () => {
    const blob = new Blob([SAMPLE_HARDWARE_CSV], { type: 'text/csv' });
    const sampleFile = new File([blob], 'prahari_max30102_10s_25hz.csv', { type: 'text/csv' });
    setSampleCount(250);
    setValidationError(null);
    onPPGFileChange(sampleFile);
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    setSampleCount(null);
    setValidationError(null);
    onPPGFileChange(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="bg-white rounded-3xl p-6 border border-black/[0.06] shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-teal-50 text-[#00776b] flex items-center justify-center">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-[15px] font-semibold text-[#1d1d1f]">Optical PPG Measurement</h3>
            <p className="text-[12px] text-[#6e6e73]">MAX30102 10-Second Dual-Wavelength Recording (25 Hz • 250 samples)</p>
          </div>
        </div>

        <button
          type="button"
          onClick={handleLoadSampleCSV}
          className="apple-btn-secondary px-3 py-1.5 text-[11px] inline-flex items-center gap-1.5 text-[#00776b] font-semibold"
          title="Load pre-calibrated 10s MAX30102 recording (Benchmark / Test Data)"
        >
          <Sparkles className="w-3 h-3 fill-current" />
          <span>Load Benchmark Data (Test)</span>
        </button>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".csv,text/csv"
        onChange={handleFileUpload}
        className="hidden"
      />

      {!ppgFile ? (
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all ${
            dragActive
              ? 'border-[#00776b] bg-[#00776b]/5'
              : 'border-black/[0.12] hover:border-black/[0.24] bg-[#fbfbfd]'
          }`}
        >
          <Upload className="w-7 h-7 text-[#86868b] mx-auto mb-2" />
          <p className="text-[13px] font-medium text-[#1d1d1f]">
            Drop MAX30102 PPG CSV here or <span className="text-[#00776b] underline">browse</span>
          </p>
          <p className="text-[11px] text-[#86868b] mt-0.5">
            Expected: 250 samples • 25Hz • timestamp_ms,red,ir format (Optional)
          </p>
        </div>
      ) : (
        <div className="bg-emerald-50/60 border border-emerald-200/80 rounded-2xl p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[13px] font-semibold text-emerald-900">{ppgFile.name}</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                  READY
                </span>
              </div>
              <p className="text-[11px] text-emerald-700">
                {sampleCount ? `${sampleCount} samples (~${(sampleCount / 25).toFixed(1)}s @ 25Hz)` : 'Hardware PPG attached'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="p-2 text-emerald-800 hover:text-emerald-950 rounded-lg hover:bg-emerald-100/50"
              title="Replace CSV"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={handleClear}
              className="p-2 text-red-600 hover:text-red-800 rounded-lg hover:bg-red-50"
              title="Remove CSV"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {validationError && (
        <div className="flex items-center gap-2 text-red-700 bg-red-50 border border-red-200 rounded-xl p-3 text-[12px]">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{validationError}</span>
        </div>
      )}
    </div>
  );
};
