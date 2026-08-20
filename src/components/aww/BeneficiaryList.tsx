import React from 'react';
import { Beneficiary, Category, Gender, Language } from '../../types';
import { getTranslation } from '../../services/localizationService';
import { Search, Plus, User, Baby, HeartPulse, Filter, ShieldCheck, ChevronRight, X } from 'lucide-react';

interface BeneficiaryListProps {
  beneficiaries: Beneficiary[];
  onSelectBeneficiary: (beneficiary: Beneficiary) => void;
  onStartScreening: (beneficiary: Beneficiary) => void;
  onAddBeneficiary: (newBeneficiary: Omit<Beneficiary, 'id' | 'lastVisitDate' | 'visitHistory'>) => void;
  language: Language;
}

export const BeneficiaryList: React.FC<BeneficiaryListProps> = ({
  beneficiaries,
  onSelectBeneficiary,
  onStartScreening,
  onAddBeneficiary,
  language,
}) => {
  const [searchTerm, setSearchTerm] = React.useState('');
  const [categoryFilter, setCategoryFilter] = React.useState<'all' | Category>('all');
  const [showAddModal, setShowAddModal] = React.useState(false);

  // New Beneficiary Form State
  const [name, setName] = React.useState('');
  const [category, setCategory] = React.useState<Category>('child');
  const [ageYears, setAgeYears] = React.useState<number>(3);
  const [sex, setSex] = React.useState<Gender>('Male');
  const [trimester, setTrimester] = React.useState<1 | 2 | 3>(2);
  const [guardianName, setGuardianName] = React.useState('');
  const [locationVillage, setLocationVillage] = React.useState('Ramgarh');
  const [phone, setPhone] = React.useState('');
  const [abhaId, setAbhaId] = React.useState('');

  const filtered = beneficiaries.filter((b) => {
    const matchesSearch =
      b.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      b.guardianName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      b.locationVillage.toLowerCase().includes(searchTerm.toLowerCase()) ||
      b.abhaId?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCat = categoryFilter === 'all' || b.category === categoryFilter;
    return matchesSearch && matchesCat;
  });

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    onAddBeneficiary({
      name: name.trim(),
      category,
      ageYears: category === 'child' ? ageYears : undefined,
      sex: category === 'child' ? sex : undefined,
      isPregnant: category === 'pregnant',
      trimester: category === 'pregnant' ? trimester : undefined,
      guardianName: guardianName.trim() || 'Guardian',
      locationVillage: locationVillage.trim() || 'Ramgarh',
      anganwadiCentreId: 'AWC-1049281',
      phone: phone.trim() || '+91 98000 00000',
      abhaId: abhaId.trim() || `ABHA 91-${Math.floor(1000 + Math.random() * 9000)}-${Math.floor(1000 + Math.random() * 9000)}-${Math.floor(1000 + Math.random() * 9000)}`,
      rchId: `RCH-${Math.floor(10000000000 + Math.random() * 90000000000)}`,
      anemiaRisk: 'LOW',
      nutritionRisk: 'LOW',
      overallPriority: 'LOW',
      trajectory: 'STABLE',
      isDemoData: false,
    });

    setShowAddModal(false);
    setName('');
  };

  return (
    <div className="space-y-6 max-w-[1040px] mx-auto pb-16">
      
      {/* Header Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-[#00776b] text-[12px] font-semibold mb-1">
            <ShieldCheck className="w-4 h-4" />
            <span>Anganwadi Centre #1049281 • Ramgarh Sector</span>
          </div>
          <h2 className="text-[28px] sm:text-[34px] font-semibold text-[#1d1d1f] tracking-title">
            Beneficiary Registry
          </h2>
          <p className="text-[14px] text-[#6e6e73]">
            {beneficiaries.length} verified community records linked with ABHA Health Accounts
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="apple-btn-accent px-5 py-3 text-[13px] inline-flex items-center gap-2 shadow-sm self-start sm:self-auto"
        >
          <Plus className="w-4 h-4 stroke-[2.5]" />
          <span>Register New Beneficiary</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="w-full sm:flex-1 relative">
          <Search className="w-4 h-4 text-[#86868b] absolute left-4 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by name, guardian, village, or ABHA ID..."
            className="w-full pl-11 pr-4 py-3 bg-white rounded-2xl border border-black/[0.08] text-[14px] text-[#1d1d1f] placeholder:text-[#86868b] focus:outline-none focus:ring-2 focus:ring-[#00776b]/20 focus:border-[#00776b] transition-all shadow-sm"
          />
        </div>

        {/* Category Pill Controls */}
        <div className="flex items-center p-1 rounded-2xl bg-black/[0.05] border border-black/[0.04] w-full sm:w-auto">
          <button
            onClick={() => setCategoryFilter('all')}
            className={`flex-1 sm:flex-none px-4 py-2 rounded-xl text-[12px] font-medium transition-all ${
              categoryFilter === 'all'
                ? 'bg-white text-[#1d1d1f] shadow-sm'
                : 'text-[#6e6e73] hover:text-[#1d1d1f]'
            }`}
          >
            All ({beneficiaries.length})
          </button>
          <button
            onClick={() => setCategoryFilter('child')}
            className={`flex-1 sm:flex-none px-4 py-2 rounded-xl text-[12px] font-medium transition-all ${
              categoryFilter === 'child'
                ? 'bg-white text-[#1d1d1f] shadow-sm'
                : 'text-[#6e6e73] hover:text-[#1d1d1f]'
            }`}
          >
            Children (6–59m)
          </button>
          <button
            onClick={() => setCategoryFilter('pregnant')}
            className={`flex-1 sm:flex-none px-4 py-2 rounded-xl text-[12px] font-medium transition-all ${
              categoryFilter === 'pregnant'
                ? 'bg-white text-[#1d1d1f] shadow-sm'
                : 'text-[#6e6e73] hover:text-[#1d1d1f]'
            }`}
          >
            Maternal ANC
          </button>
        </div>
      </div>

      {/* Beneficiaries List */}
      <div className="bg-white rounded-[32px] p-6 sm:p-8 border border-black/[0.06] shadow-sm space-y-3">
        {filtered.length === 0 ? (
          <div className="py-16 text-center text-[#86868b]">
            <p className="text-[15px]">No beneficiary records found matching "{searchTerm}".</p>
          </div>
        ) : (
          filtered.map((beneficiary) => (
            <div
              key={beneficiary.id}
              onClick={() => onSelectBeneficiary(beneficiary)}
              className="p-5 rounded-2xl bg-[#fbfbfd] hover:bg-[#f5f5f7] border border-black/[0.04] transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4 group"
            >
              <div className="flex items-center gap-4">
                <div className="w-11 h-11 rounded-2xl bg-white border border-black/[0.06] flex items-center justify-center text-[#1d1d1f] shadow-sm shrink-0">
                  {beneficiary.category === 'child' ? (
                    <Baby className="w-5 h-5 stroke-[1.75]" />
                  ) : (
                    <HeartPulse className="w-5 h-5 text-[#00776b] stroke-[1.75]" />
                  )}
                </div>

                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-[#1d1d1f] text-[16px] group-hover:text-[#00776b] transition-colors">
                      {beneficiary.name}
                    </span>
                    <span className="text-[12px] text-[#86868b]">
                      {beneficiary.category === 'child'
                        ? `Age ${beneficiary.ageYears}y (${beneficiary.sex || 'Child'})`
                        : `Maternal ANC • Trimester ${beneficiary.trimester}`}
                    </span>
                    {beneficiary.isDemoData && (
                      <span className="px-2 py-0.5 text-[9px] font-medium rounded-full bg-black/[0.05] text-[#6e6e73]">
                        DEMO
                      </span>
                    )}
                  </div>
                  <div className="text-[12px] text-[#6e6e73] mt-0.5">
                    Guardian: {beneficiary.guardianName} • Village: {beneficiary.locationVillage} • {beneficiary.abhaId}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 self-end sm:self-auto">
                <div className="text-right hidden sm:block">
                  <span
                    className={`px-2.5 py-0.5 text-[11px] font-semibold rounded-full ${
                      beneficiary.anemiaRisk === 'ELEVATED'
                        ? 'bg-red-50 text-red-800 border border-red-200'
                        : beneficiary.anemiaRisk === 'MODERATE'
                        ? 'bg-amber-50 text-amber-800 border border-amber-200'
                        : 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                    }`}
                  >
                    {beneficiary.anemiaRisk} Risk
                  </span>
                  <p className="text-[11px] text-[#86868b] mt-0.5">
                    Last: {beneficiary.lastVisitDate || 'Never'}
                  </p>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onStartScreening(beneficiary);
                  }}
                  className="apple-btn-accent px-4 py-2 text-[12px] font-medium shadow-sm"
                >
                  Screen
                </button>

                <ChevronRight className="w-4 h-4 text-[#86868b] group-hover:text-[#1d1d1f] transition-transform group-hover:translate-x-0.5" />
              </div>
            </div>
          ))
        )}
      </div>

      {/* Apple-style Register Beneficiary Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-[32px] p-8 max-w-lg w-full border border-black/[0.08] shadow-2xl space-y-6 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-[20px] font-semibold text-[#1d1d1f]">Register New Beneficiary</h3>
                <p className="text-[13px] text-[#6e6e73]">Add a mother or child to Anganwadi registry</p>
              </div>
              <button
                onClick={() => setShowAddModal(false)}
                className="p-2 rounded-full hover:bg-black/[0.05] text-[#86868b]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="space-y-4 text-left">
              <div>
                <label className="text-[12px] font-semibold text-[#1d1d1f] block mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Priya Sharma"
                  className="w-full px-4 py-2.5 rounded-xl border border-black/[0.1] text-[14px] focus:outline-none focus:border-[#00776b]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[12px] font-semibold text-[#1d1d1f] block mb-1">Category</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value as Category)}
                    className="w-full px-3 py-2.5 rounded-xl border border-black/[0.1] text-[13px]"
                  >
                    <option value="child">Child (6–59m)</option>
                    <option value="pregnant">Pregnant Mother</option>
                  </select>
                </div>

                {category === 'child' ? (
                  <div>
                    <label className="text-[12px] font-semibold text-[#1d1d1f] block mb-1">Age (Years)</label>
                    <input
                      type="number"
                      min={0.5}
                      max={5}
                      step={0.5}
                      value={ageYears}
                      onChange={(e) => setAgeYears(parseFloat(e.target.value))}
                      className="w-full px-3 py-2.5 rounded-xl border border-black/[0.1] text-[13px]"
                    />
                  </div>
                ) : (
                  <div>
                    <label className="text-[12px] font-semibold text-[#1d1d1f] block mb-1">Trimester</label>
                    <select
                      value={trimester}
                      onChange={(e) => setTrimester(parseInt(e.target.value) as 1 | 2 | 3)}
                      className="w-full px-3 py-2.5 rounded-xl border border-black/[0.1] text-[13px]"
                    >
                      <option value={1}>1st Trimester</option>
                      <option value={2}>2nd Trimester</option>
                      <option value={3}>3rd Trimester</option>
                    </select>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[12px] font-semibold text-[#1d1d1f] block mb-1">Guardian Name</label>
                  <input
                    type="text"
                    value={guardianName}
                    onChange={(e) => setGuardianName(e.target.value)}
                    placeholder="Mother / Father"
                    className="w-full px-3 py-2.5 rounded-xl border border-black/[0.1] text-[13px]"
                  />
                </div>
                <div>
                  <label className="text-[12px] font-semibold text-[#1d1d1f] block mb-1">Village Hamlet</label>
                  <input
                    type="text"
                    value={locationVillage}
                    onChange={(e) => setLocationVillage(e.target.value)}
                    placeholder="Ramgarh"
                    className="w-full px-3 py-2.5 rounded-xl border border-black/[0.1] text-[13px]"
                  />
                </div>
              </div>

              <div className="pt-4 flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 py-3 rounded-xl border border-black/[0.1] text-[13px] font-medium text-[#6e6e73] hover:bg-[#f5f5f7]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 apple-btn-accent py-3 text-[13px] font-medium shadow-sm"
                >
                  Save Beneficiary
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
