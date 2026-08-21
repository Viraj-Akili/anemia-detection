import React from 'react';
import { Beneficiary, Category, Gender, Language } from '../../types';
import { getTranslation } from '../../services/localizationService';
import { Search, Plus, User, Baby, HeartPulse, Filter, ShieldCheck } from 'lucide-react';

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
    <div className="space-y-5 max-w-4xl mx-auto">
      {/* Header Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2 text-cyan-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <ShieldCheck className="w-4 h-4" />
            <span>Anganwadi Centre #1049281 • Ramgarh Sector</span>
          </div>
          <h2 className="text-xl font-bold text-white">Registered Beneficiaries Database</h2>
          <p className="text-xs text-slate-400">
            {beneficiaries.length} verified records linked with ABHA Health Accounts & RCH Registry
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 text-xs font-bold shadow-sm"
        >
          <Plus className="w-4 h-4" />
          <span>Register New Beneficiary</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="sm:col-span-2 relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search by beneficiary name, ABHA Number, guardian, or village..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="flex items-center bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5">
          <Filter className="w-3.5 h-3.5 text-slate-400 mr-2" />
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value as any)}
            className="bg-transparent text-xs text-slate-200 focus:outline-none cursor-pointer w-full font-semibold"
          >
            <option value="all" className="bg-slate-900">
              All Categories
            </option>
            <option value="child" className="bg-slate-900">
              Children (0-6 yrs)
            </option>
            <option value="pregnant" className="bg-slate-900">
              Pregnant Women (WRA)
            </option>
          </select>
        </div>
      </div>

      {/* Beneficiaries Cards List */}
      <div className="space-y-3">
        {filtered.map((b) => (
          <div
            key={b.id}
            onClick={() => onSelectBeneficiary(b)}
            className="bg-slate-900 hover:bg-slate-850 border border-slate-800 rounded-2xl p-4 transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4 group shadow-sm"
          >
            <div className="flex items-start space-x-3">
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center border shrink-0 mt-0.5 ${
                  b.category === 'pregnant'
                    ? 'bg-rose-950/60 text-rose-400 border-rose-800/80'
                    : 'bg-slate-950 text-cyan-400 border-slate-800'
                }`}
              >
                {b.category === 'pregnant' ? (
                  <HeartPulse className="w-5 h-5" />
                ) : (
                  <Baby className="w-5 h-5" />
                )}
              </div>

              <div className="space-y-1">
                <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                  <span className="font-bold text-white text-base group-hover:text-cyan-300">
                    {b.name}
                  </span>
                  <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-slate-800 text-slate-300 border border-slate-700">
                    {b.category === 'child'
                      ? `Child (${b.ageYears} yrs, ${b.sex})`
                      : `Pregnant (Trimester ${b.trimester})`}
                  </span>
                  {b.abhaId && (
                    <span className="px-2 py-0.5 text-[10px] font-mono font-medium rounded bg-slate-950 text-emerald-400 border border-emerald-900">
                      {b.abhaId}
                    </span>
                  )}
                </div>
                <div className="text-xs text-slate-400">
                  Village: <span className="text-slate-300 font-medium">{b.locationVillage}</span> • Guardian:{' '}
                  <span className="text-slate-300 font-medium">{b.guardianName}</span> • AWC:{' '}
                  <span className="text-slate-300 font-mono">{b.anganwadiCentreId}</span>
                </div>
                <div className="text-[11px] text-slate-500">
                  Last Screened: {b.lastVisitDate} ({b.visitHistory?.length || 1} official records)
                </div>
              </div>
            </div>

            {/* Right Risk Badges & Action */}
            <div className="flex items-center space-x-3 self-end sm:self-auto">
              <div className="text-right">
                <div className="flex items-center space-x-1.5 justify-end">
                  <span className="text-xs text-slate-400">Anemia Risk:</span>
                  <span
                    className={`px-2.5 py-0.5 text-xs font-bold rounded-md ${
                      b.anemiaRisk === 'ELEVATED'
                        ? 'bg-rose-950 text-rose-300 border border-rose-800'
                        : b.anemiaRisk === 'MODERATE'
                        ? 'bg-amber-950 text-amber-300 border border-amber-800'
                        : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                    }`}
                  >
                    {b.anemiaRisk}
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 mt-1">
                  Trajectory:{' '}
                  <span className="text-cyan-400 font-semibold">
                    {b.trajectory.replace('_', ' ')}
                  </span>
                </div>
              </div>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onStartScreening(b);
                }}
                className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold border border-slate-700"
              >
                Screen Now
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Register New Beneficiary Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl text-slate-100">
            <div className="border-b border-slate-800 pb-3">
              <h3 className="text-lg font-bold text-white">Register New Beneficiary</h3>
              <p className="text-xs text-slate-400">Poshan Tracker & ABHA Registration Form</p>
            </div>

            <form onSubmit={handleCreateSubmit} className="space-y-4">
              <div>
                <label className="text-xs text-slate-400 font-semibold">Category</label>
                <div className="grid grid-cols-2 gap-2 mt-1">
                  <button
                    type="button"
                    onClick={() => setCategory('child')}
                    className={`py-2 text-xs font-bold rounded-xl border ${
                      category === 'child'
                        ? 'bg-slate-800 border-cyan-500 text-cyan-300'
                        : 'bg-slate-950 border-slate-800 text-slate-400'
                    }`}
                  >
                    Child (0-6 Years)
                  </button>
                  <button
                    type="button"
                    onClick={() => setCategory('pregnant')}
                    className={`py-2 text-xs font-bold rounded-xl border ${
                      category === 'pregnant'
                        ? 'bg-rose-950 border-rose-500 text-rose-300'
                        : 'bg-slate-950 border-slate-800 text-slate-400'
                    }`}
                  >
                    Pregnant Woman
                  </button>
                </div>
              </div>

              <div>
                <label className="text-xs text-slate-400 font-semibold">Full Name (as per Aadhaar / ABHA)</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Aarav Sharma"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
                />
              </div>

              <div>
                <label className="text-xs text-slate-400 font-semibold">ABHA Health ID (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. ABHA 91-4829-1029-3841"
                  value={abhaId}
                  onChange={(e) => setAbhaId(e.target.value)}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-emerald-400 font-mono"
                />
              </div>

              {category === 'child' ? (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-slate-400 font-semibold">Age (Years)</label>
                    <input
                      type="number"
                      min={0}
                      max={6}
                      value={ageYears}
                      onChange={(e) => setAgeYears(Number(e.target.value))}
                      className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 font-semibold">Sex</label>
                    <select
                      value={sex}
                      onChange={(e) => setSex(e.target.value as Gender)}
                      className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
                    >
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                    </select>
                  </div>
                </div>
              ) : (
                <div>
                  <label className="text-xs text-slate-400 font-semibold">Gestational Trimester</label>
                  <select
                    value={trimester}
                    onChange={(e) => setTrimester(Number(e.target.value) as any)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
                  >
                    <option value={1}>Trimester 1 (Weeks 1-12)</option>
                    <option value={2}>Trimester 2 (Weeks 13-27)</option>
                    <option value={3}>Trimester 3 (Weeks 28-40)</option>
                  </select>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-slate-400 font-semibold">Guardian / Spouse</label>
                  <input
                    type="text"
                    placeholder="Guardian Name"
                    value={guardianName}
                    onChange={(e) => setGuardianName(e.target.value)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 font-semibold">Village / Habitation</label>
                  <input
                    type="text"
                    placeholder="Village Name"
                    value={locationVillage}
                    onChange={(e) => setLocationVillage(e.target.value)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold"
                >
                  Save & Issue Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
