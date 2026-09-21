"use client";
import { useEffect, useState } from 'react';
import NavBar from '@/components/NavBar';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';

const FULL_2011_RULES = [
  { id: 'Rule 1', name: 'Short title and commencement', desc: 'Establishes the Legal Metrology (Packaged Commodities) Rules, 2011.' },
  { id: 'Rule 2', name: 'Definitions', desc: 'Defines terms like pre-packaged commodity, principal display panel, MRP, etc.' },
  { id: 'Rule 3', name: 'Applicability', desc: 'Exempts packages > 25kg/25L or those meant for institutional/industrial consumers.' },
  { id: 'Rule 4', name: 'Regulation for pre-packing', desc: 'No person shall pre-pack or sell unless the package complies with these rules.' },
  { id: 'Rule 5', name: 'Specific commodities to be packed in standard quantities', desc: 'Schedule II prescribes standard quantities for specific goods.' },
  { id: 'Rule 6(1)(a)', name: 'Name and address of Manufacturer/Packer/Importer', desc: 'Must be explicitly declared on the package.' },
  { id: 'Rule 6(1)(b)', name: 'Common/Generic name', desc: 'Brand names are not a substitute for the generic name.' },
  { id: 'Rule 6(1)(c)', name: 'Net Quantity', desc: 'Must be in standard SI units (g, kg, ml, L).' },
  { id: 'Rule 6(1)(d)', name: 'Month and Year of Manufacture', desc: 'Must declare when the commodity was manufactured/packed.' },
  { id: 'Rule 6(1)(e)', name: 'Retail Sale Price (MRP)', desc: 'Must include "Inclusive of all taxes" and currency symbol.' },
  { id: 'Rule 6(1)(f)', name: 'Consumer Care Details', desc: 'Name, address, telephone, and email for consumer complaints.' },
  { id: 'Rule 6(10)', name: 'E-Commerce Declarations', desc: 'E-commerce entities must display mandatory declarations on the digital listing.' },
  { id: 'Rule 7', name: 'Principal Display Panel (PDP)', desc: 'Declarations must be grouped together on the PDP.' },
  { id: 'Rule 8', name: 'Declaration of Size', desc: 'Letters and numerals must meet minimum height requirements based on net quantity.' },
  { id: 'Rule 9', name: 'Manner of declaration', desc: 'Declarations must be legible, prominent, and in English or Hindi.' },
  { id: 'Rule 10', name: 'Declaration of name and address', desc: 'Detailed requirements for qualifying the manufacturer/packer address.' },
  { id: 'Rule 11', name: 'General provisions for Net Quantity', desc: 'Rules for declaring weight vs volume vs length vs number.' },
  { id: 'Rule 12', name: 'Declaration of quantity by weight', desc: 'Specifics on using kg, g, or mg.' },
  { id: 'Rule 13', name: 'Declaration of quantity by volume', desc: 'Specifics on using L, ml.' },
  { id: 'Rule 14', name: 'Declaration of quantity by length', desc: 'Specifics on using m, cm, mm.' },
  { id: 'Rule 15', name: 'Declaration of quantity by area', desc: 'Specifics on using sq. m, sq. cm.' },
  { id: 'Rule 16', name: 'Declaration of quantity by number', desc: 'Must use words "N" or "U".' },
  { id: 'Rule 17', name: 'Fractions of units', desc: 'Rules for rounding off non-integer quantities.' },
  { id: 'Rule 18', name: 'Declarations with respect to MRP', desc: 'Rounding off price and tax calculations.' },
  { id: 'Rule 19', name: 'Sale of commodities at lower price', desc: 'Promotional pricing must not obscure original MRP.' },
  { id: 'Rule 20', name: 'Wholesale Packages', desc: 'Different declaration requirements for wholesale vs retail packages.' },
  { id: 'Rule 21', name: 'Export Packages', desc: 'Exemptions and requirements for goods intended strictly for export.' },
  { id: 'Rule 22', name: 'Registration of Manufacturers/Packers', desc: 'Mandatory registration with the Director of Legal Metrology.' },
  { id: 'Rule 23', name: 'Registration of Importers', desc: 'Importers must register before packing/selling.' },
  { id: 'Rule 24', name: 'Objection to Registration', desc: 'Process for revoking or rejecting registration.' },
  { id: 'Rule 25', name: 'Maintenance of Records', desc: 'Registered entities must maintain packing/sales records.' },
  { id: 'Rule 26', name: 'Exemption in respect of certain packages', desc: 'Exempts very small packages (<10g/10ml) from certain declarations.' },
  { id: 'Rule 27', name: 'Registration of shorter address', desc: 'Approval required to use an abbreviated address.' },
  { id: 'Rule 28', name: 'Registration of shorter name', desc: 'Approval required to use an abbreviated name.' },
  { id: 'Rule 29', name: 'Penalty for contravention', desc: 'Fines and prosecution for violating the rules.' },
  { id: 'Rule 30', name: 'Compounding of offences', desc: 'Procedure for paying compounding fees in lieu of prosecution.' },
  { id: 'Rule 31', name: 'Power to remove difficulties', desc: 'Central Government authority to resolve ambiguities.' },
  { id: 'Rule 32', name: 'Repeal and savings', desc: 'Repeals the older Standards of Weights and Measures Rules, 1977.' },
];

const SAMPLE_GAZETTE_TEXT = `MINISTRY OF CONSUMER AFFAIRS, FOOD AND PUBLIC DISTRIBUTION
(Department of Consumer Affairs)
NOTIFICATION
New Delhi, the 14th July, 2026
G.S.R. 512(E).—In exercise of the powers conferred by section 52 of the Legal Metrology Act, 2009, the Central Government hereby makes the following rules further to amend the Legal Metrology (Packaged Commodities) Rules, 2011, namely:—
1. (1) These rules may be called the Legal Metrology (Packaged Commodities) Amendment Rules, 2026.
(2) They shall come into force on the 1st day of October, 2026.
2. In rule 6 of the Legal Metrology (Packaged Commodities) Rules, 2011, in sub-rule (1), after clause (f), the following clause shall be inserted, namely:—
'(g) every package containing an electronic commodity or accessory shall bear a scannable QR code on the principal display panel providing complete statutory declarations, user manuals, and warranty details.'`;

export default function RulesPage() {
  const [rules, setRules] = useState([]);
  const [stats, setStats] = useState(null);
  const [activeTab, setActiveTab] = useState('violated');
  const [loading, setLoading] = useState(true);

  // Gazette AI Sync state
  const [gazetteText, setGazetteText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [newVersion, setNewVersion] = useState('v2');
  const [effectiveFrom, setEffectiveFrom] = useState('2026-10-01');
  const [citation, setCitation] = useState('Gazette Notification G.S.R. 512(E)');
  const [isPublishing, setIsPublishing] = useState(false);
  const [publishedVersion, setPublishedVersion] = useState(null);

  const router = useRouter();
  const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

  const fetchRules = async () => {
    try {
      const token = sessionStorage.getItem('token') || localStorage.getItem('token');
      const res = await fetch(`${API}/admin/rules`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      const statsRes = await fetch(`${API}/dashboard/stats`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      
      if (res.ok) {
        const json = await res.json();
        const d = json.data || json;
        setRules(Array.isArray(d) ? d : (d.rules || []));
      }
      if (statsRes.ok) {
        const sjson = await statsRes.json();
        setStats(sjson.data || sjson);
      }
    } catch {
      setRules([{ rule_id: 'C01', name: 'Product Name', description: 'Must have product name', severity: 'high', active: true }]);
    } finally { setLoading(false); }
  };

  useEffect(() => {
    fetchRules();
  }, [router]);

  const handleAnalyzeGazette = async () => {
    if (!gazetteText.trim()) {
      toast.error('Please paste gazette notification text or load the sample amendment.');
      return;
    }
    setIsAnalyzing(true);
    try {
      const token = sessionStorage.getItem('token') || localStorage.getItem('token');
      const formData = new FormData();
      formData.append('gazette_text', gazetteText);

      const res = await fetch(`${API}/admin/rule-sync/upload`, {
        method: 'POST',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
        body: formData
      });

      if (!res.ok) throw new Error('Analysis failed');
      const json = await res.json();
      const suggs = json.suggestions || [];
      setSuggestions(suggs);
      if (suggs.length > 0) {
        toast.success(`Extracted ${suggs.length} statutory amendment suggestion(s) via Gemini AI.`);
      } else {
        toast.info('No amendments detected in the provided text.');
      }
    } catch (err) {
      toast.error('AI Gazette parsing error: ' + err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handlePublishRulepack = async () => {
    if (suggestions.length === 0) {
      toast.error('No amendment suggestions to publish.');
      return;
    }
    setIsPublishing(true);
    try {
      const token = sessionStorage.getItem('token') || localStorage.getItem('token');
      const approvedChanges = suggestions.map(s => s.value);

      const res = await fetch(`${API}/admin/rule-sync/publish`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          new_version_name: newVersion,
          effective_from: effectiveFrom,
          source_citation: citation,
          approved_changes: approvedChanges
        })
      });

      if (!res.ok) throw new Error('Failed to publish rulepack');
      const json = await res.json();
      setPublishedVersion(json.new_version || newVersion);
      toast.success(`Rulepack ${json.new_version || newVersion} published successfully! Reloaded engine cache.`);
      // Refresh rules catalog
      await fetchRules();
    } catch (err) {
      toast.error('Publish failed: ' + err.message);
    } finally {
      setIsPublishing(false);
    }
  };

  if (loading) return <div className="min-h-screen bg-background text-text-primary animate-fade-in"><NavBar/><div className="p-10 text-text-secondary text-[14px]">Loading...</div></div>;

  return (
    <div className="min-h-screen bg-background text-text-primary">
      <NavBar />
      <div className="max-w-[1000px] mx-auto px-3 sm:px-6 py-4 sm:py-8 md:py-12">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 sm:mb-10">
          <div>
            <h1 className="text-[22px] sm:text-[28px] md:text-[32px] font-medium tracking-tight leading-[1.1] mb-2">Rules Config</h1>
            <p className="text-xs sm:text-[15px] text-text-secondary">Manage Legal Metrology Act constraints and synchronize with official Gazette amendments.</p>
          </div>
          {publishedVersion && (
            <div className="px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 text-xs font-mono font-bold flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              Active Rulepack: {publishedVersion}
            </div>
          )}
        </div>

        <div className="flex gap-4 border-b border-border mb-6 sm:mb-8 overflow-x-auto scrollbar-none">
          <button 
            onClick={() => setActiveTab('violated')}
            className={`pb-3 text-xs sm:text-[14px] font-medium transition-colors border-b-2 whitespace-nowrap cursor-pointer ${activeTab === 'violated' ? 'border-[#f87171] text-[#f87171]' : 'border-transparent text-text-secondary hover:text-text-primary'}`}
          >
            System-Wide Violations
          </button>
          <button 
            onClick={() => setActiveTab('all')}
            className={`pb-3 text-xs sm:text-[14px] font-medium transition-colors border-b-2 whitespace-nowrap cursor-pointer ${activeTab === 'all' ? 'border-blue-500 text-blue-500' : 'border-transparent text-text-secondary hover:text-text-primary'}`}
          >
            All 2011 Act Rules ({FULL_2011_RULES.length})
          </button>
          <button 
            onClick={() => setActiveTab('gazette_sync')}
            className={`pb-3 text-xs sm:text-[14px] font-medium transition-colors border-b-2 whitespace-nowrap cursor-pointer flex items-center gap-2 ${activeTab === 'gazette_sync' ? 'border-purple-500 text-purple-600 dark:text-purple-400 font-bold' : 'border-transparent text-text-secondary hover:text-text-primary'}`}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
            Gazette AI Sync (Gemini)
          </button>
        </div>

        {/* ── TAB 1: SYSTEM-WIDE VIOLATIONS ── */}
        {activeTab === 'violated' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {rules
              .filter(r => {
                const isViolated = stats?.top_violated_rules?.some(tr => tr.rule_id === r.rule_id);
                return isViolated || r.severity === 'high';
              })
              .map((r, i) => {
                const violationStats = stats?.top_violated_rules?.find(tr => tr.rule_id === r.rule_id);
                return (
                  <div key={i} className="glass border border-border/50 shadow-sm hover:-translate-y-1 hover:shadow-md transition-all duration-300 rounded-2xl sm:rounded-[24px] p-4 sm:p-6 flex flex-col group hover:border-mist transition-colors relative overflow-hidden">
                    {violationStats && (
                      <div className="absolute top-0 right-0 bg-[#f87171]/10 text-[#f87171] text-[10px] sm:text-[11px] font-bold px-2.5 sm:px-3 py-1 rounded-bl-lg">
                        Failed {violationStats.count} times
                      </div>
                    )}
                    <div className="flex justify-between items-center mb-3 sm:mb-4 mt-2">
                      <div className="flex items-center gap-2 sm:gap-3">
                        <div className="w-2 h-2 rounded-full bg-[#4ade80]"></div>
                        <span className="font-mono text-xs sm:text-[13px] text-text-secondary">{r.rule_id}</span>
                      </div>
                      <span className="px-2.5 sm:px-3 py-0.5 sm:py-1 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 rounded-full text-[9px] sm:text-[10px] font-bold tracking-widest uppercase">AI Monitored</span>
                    </div>
                    <h3 className="font-medium text-[15px] sm:text-[16px] text-text-primary mb-1.5">{r.name}</h3>
                    <p className="text-xs sm:text-[14px] text-text-muted leading-relaxed mb-4 sm:mb-6 flex-1">{r.description}</p>
                    <div className="pt-3 sm:pt-4 border-t border-border flex justify-between items-center">
                      <span className={`text-[11px] sm:text-[12px] font-medium uppercase tracking-wider ${r.severity === 'high' ? 'text-[#f87171]' : 'text-text-secondary'}`}>{r.severity} severity</span>
                    </div>
                  </div>
                );
            })}
          </div>
        )}

        {/* ── TAB 2: ALL 2011 RULES ── */}
        {activeTab === 'all' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {FULL_2011_RULES.map((r, i) => {
              const isMonitored = rules.some(aiRule => aiRule.rule_id?.includes(r.id) || r.id.includes(aiRule.rule_id));
              return (
                <div key={i} className="glass border border-border/50 shadow-sm hover:-translate-y-1 hover:shadow-md transition-all duration-300 rounded-2xl sm:rounded-[24px] p-4 sm:p-6 flex flex-col group hover:border-mist transition-colors">
                  <div className="flex justify-between items-center mb-3 sm:mb-4">
                    <div className="flex items-center gap-2 sm:gap-3">
                      <div className={`w-2 h-2 rounded-full ${isMonitored ? 'bg-[#4ade80]' : 'bg-text-muted'}`}></div>
                      <span className="font-mono text-xs sm:text-[13px] text-text-secondary">{r.id}</span>
                    </div>
                    <span className={isMonitored ? 'px-2.5 sm:px-3 py-0.5 sm:py-1 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 rounded-full text-[9px] sm:text-[10px] font-bold tracking-widest uppercase' : 'px-2.5 sm:px-3 py-0.5 sm:py-1 bg-text-muted/10 text-text-muted border border-border rounded-full text-[9px] sm:text-[10px] font-bold tracking-widest uppercase'}>{isMonitored ? 'AI Monitored' : 'Manual / Admin'}</span>
                  </div>
                  <h3 className="font-medium text-[15px] sm:text-[16px] text-text-primary mb-1.5">{r.name}</h3>
                  <p className="text-xs sm:text-[14px] text-text-muted leading-relaxed mb-4 sm:mb-6 flex-1">{r.desc}</p>
                </div>
              );
            })}
          </div>
        )}

        {/* ── TAB 3: GAZETTE AI SYNC (GEMINI) ── */}
        {activeTab === 'gazette_sync' && (
          <div className="space-y-6">
            <div className="glass border border-border/50 rounded-2xl sm:rounded-[24px] p-5 sm:p-7 shadow-xs">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                <div>
                  <h3 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-purple-500"></span>
                    Gazette Amendment Parser (Google Gemini AI)
                  </h3>
                  <p className="text-xs text-text-secondary mt-1">
                    Upload or paste official Ministry notifications to extract packaging amendments and publish new versioned rulepacks.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setGazetteText(SAMPLE_GAZETTE_TEXT)}
                  className="px-3 py-1.5 text-xs font-mono rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-600 dark:text-purple-400 hover:bg-purple-500/20 transition-all cursor-pointer text-left sm:text-center shrink-0"
                >
                  Load Sample 2026 Notification
                </button>
              </div>

              <textarea
                rows={6}
                value={gazetteText}
                onChange={e => setGazetteText(e.target.value)}
                placeholder="Paste Gazette Notification text here (e.g. Notification G.S.R. 512(E) on QR Code regulations)..."
                className="w-full font-mono text-xs p-3 rounded-xl border border-border bg-slate-50 dark:bg-slate-900/60 text-slate-800 dark:text-slate-200 focus:outline-hidden focus:ring-1 focus:ring-purple-500"
              />

              <div className="flex justify-end mt-3">
                <button
                  type="button"
                  onClick={handleAnalyzeGazette}
                  disabled={isAnalyzing}
                  className="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold shadow-md cursor-pointer transition-all flex items-center gap-2 disabled:opacity-50"
                >
                  {isAnalyzing ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Gemini AI Analyzing Gazette...</span>
                    </>
                  ) : (
                    <>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                      <span>Analyze with Gemini AI</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Extracted Suggestions Preview */}
            {suggestions.length > 0 && (
              <div className="glass border border-purple-500/30 rounded-2xl sm:rounded-[24px] p-5 sm:p-7 shadow-lg animate-in fade-in slide-in-from-bottom-2">
                <div className="flex items-center justify-between pb-4 border-b border-border mb-4">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                    <h4 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white">
                      AI Extracted Amendments ({suggestions.length})
                    </h4>
                  </div>
                  <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20 font-bold">
                    Confidence: {Math.round((suggestions[0]?.confidence || 0.95) * 100)}%
                  </span>
                </div>

                <div className="space-y-3 mb-6">
                  {suggestions.map((s, idx) => (
                    <div key={idx} className="p-4 rounded-xl border border-border bg-slate-50 dark:bg-slate-900/80 text-xs">
                      <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                        <span className="px-2 py-0.5 rounded font-mono font-bold bg-blue-500/10 text-blue-600 dark:text-blue-400">
                          {s.value?.action || 'AMENDMENT'}
                        </span>
                        <span className="font-mono text-slate-500 dark:text-slate-400">
                          Citation: <strong>{s.value?.details?.citation || 'Rule 6'}</strong>
                        </span>
                      </div>
                      <p className="text-slate-800 dark:text-slate-200 leading-relaxed font-medium mb-2">
                        {s.explanation}
                      </p>
                      <pre className="p-2.5 rounded bg-slate-100 dark:bg-slate-950 font-mono text-[11px] text-slate-600 dark:text-slate-400 overflow-x-auto">
                        {JSON.stringify(s.value?.details, null, 2)}
                      </pre>
                    </div>
                  ))}
                </div>

                {/* Publish configuration */}
                <div className="pt-4 border-t border-border grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4 text-xs">
                  <div>
                    <label className="block text-[10px] font-mono uppercase text-text-secondary mb-1">New Rulepack Version</label>
                    <input
                      type="text"
                      value={newVersion}
                      onChange={e => setNewVersion(e.target.value)}
                      className="w-full p-2 rounded-lg border border-border bg-white dark:bg-slate-900 text-slate-900 dark:text-white font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-mono uppercase text-text-secondary mb-1">Effective Date</label>
                    <input
                      type="date"
                      value={effectiveFrom}
                      onChange={e => setEffectiveFrom(e.target.value)}
                      className="w-full p-2 rounded-lg border border-border bg-white dark:bg-slate-900 text-slate-900 dark:text-white font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-mono uppercase text-text-secondary mb-1">Source Citation</label>
                    <input
                      type="text"
                      value={citation}
                      onChange={e => setCitation(e.target.value)}
                      className="w-full p-2 rounded-lg border border-border bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    />
                  </div>
                </div>

                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={handlePublishRulepack}
                    disabled={isPublishing}
                    className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md cursor-pointer transition-all flex items-center gap-2 disabled:opacity-50"
                  >
                    {isPublishing ? (
                      <>
                        <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        <span>Publishing Rulepack...</span>
                      </>
                    ) : (
                      <>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12"/></svg>
                        <span>Approve & Publish to Active Rulepack</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
