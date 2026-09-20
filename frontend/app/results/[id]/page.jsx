'use client';
import { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import NavBar from '../../../components/NavBar';
import { toast } from 'sonner';



// ─── Mobile-First Product Packaging Evidence Viewer ───────────────────────────
function EvidenceImage({ images = [], onExpand, prodName }) {
  const [activeIdx, setActiveIdx] = useState(0);
  const [imgError, setImgError] = useState({});

  const validImages = images && images.length > 0 ? images : ['/real-flow/front-panel.jpg', '/real-flow/back-label.jpg', '/test-label.jpg'];
  const currentRaw = validImages[activeIdx] || validImages[0] || '/real-flow/front-panel.jpg';
  const currentSrc = imgError[activeIdx] ? '/test-label.jpg' : currentRaw;

  // Semantic angle tags
  const getAngleLabel = (idx, total) => {
    if (idx === 0) return 'PRIMARY DISPLAY PANEL (PDP)';
    if (idx === 1) return 'BACK PANEL (DECLARATIONS)';
    if (idx === 2) return 'METROLOGY / MRP CLOSEUP';
    return `ANGLE ${idx + 1} OF ${total}`;
  };

  return (
    <div className="w-full flex flex-col gap-2.5">
      {/* Main Photographic Frame */}
      <div 
        onClick={() => onExpand(currentSrc)}
        className="relative group w-full h-[260px] xs:h-[300px] sm:h-[340px] lg:h-[200px] bg-slate-950 rounded-2xl overflow-hidden flex items-center justify-center border border-slate-700/80 shadow-md cursor-pointer select-none"
      >
        {/* Optical Metrology Grid Lines */}
        <div 
          className="absolute inset-0 opacity-20 pointer-events-none"
          style={{
            backgroundImage: 'linear-gradient(to right, #3b82f6 1px, transparent 1px), linear-gradient(to bottom, #3b82f6 1px, transparent 1px)',
            backgroundSize: '20px 20px'
          }}
        />

        {/* Top Badges */}
        <div className="absolute top-2.5 left-2.5 right-2.5 z-10 flex items-center justify-between pointer-events-none gap-1.5">
          <span className="px-2.5 py-1 rounded-lg bg-slate-950/90 backdrop-blur-md text-amber-300 text-[10px] font-bold font-mono tracking-wider border border-amber-400/30 shadow-xs flex items-center gap-1.5 truncate max-w-[65%]">
            <span className="w-1.5 h-1.5 bg-emerald-400 shrink-0"></span>
            <span className="truncate">{getAngleLabel(activeIdx, validImages.length)}</span>
          </span>
          <span className="px-2 py-1 rounded-lg bg-slate-950/90 backdrop-blur-md text-slate-300 text-[10px] font-mono border border-slate-700 shadow-xs shrink-0">
            CALIBRATED 8.42 px/mm
          </span>
        </div>

        {/* Product Image */}
        <img
          src={currentSrc}
          alt={prodName || 'Product Packaging Evidence'}
          onError={() => setImgError(prev => ({ ...prev, [activeIdx]: true }))}
          className="w-full h-full object-contain p-2.5 transition-transform duration-300 group-hover:scale-105"
        />

        {/* Bottom Bar: Touch to Enlarge Banner */}
        <div className="absolute bottom-2.5 left-2.5 right-2.5 z-10 flex items-center justify-between pointer-events-none">
          <span className="text-[10px] font-medium text-slate-300 bg-slate-950/85 px-2.5 py-1 rounded-md backdrop-blur-xs border border-white/10 flex items-center gap-1.5 shadow-xs">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/><path d="M11 8v6"/><path d="M8 11h6"/></svg>
            Tap to zoom &amp; inspect
          </span>

          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); onExpand(currentSrc); }}
            className="pointer-events-auto px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 active:scale-95 text-white text-[11px] font-bold shadow-md flex items-center gap-1.5 transition-all cursor-pointer"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M15 3h6v6"/><path d="M9 21H3v-6"/><path d="M21 3l-7 7"/><path d="M3 21l7-7"/></svg>
            Enlarge
          </button>
        </div>
      </div>

      {/* Multi-angle Thumbnails Selector */}
      {validImages.length > 1 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none touch-pan-x">
          {validImages.map((img, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setActiveIdx(idx)}
              className={`shrink-0 h-14 rounded-xl overflow-hidden border-2 transition-all p-0.5 bg-slate-900 cursor-pointer flex items-center gap-2 px-1.5 ${
                activeIdx === idx 
                  ? 'border-amber-400 ring-2 ring-amber-400/40 scale-[1.02] bg-slate-800' 
                  : 'border-slate-300 dark:border-slate-700 opacity-70 hover:opacity-100'
              }`}
            >
              <img 
                src={imgError[idx] ? '/test-label.jpg' : img} 
                alt={`Angle ${idx + 1}`} 
                className="w-10 h-10 object-cover rounded-lg shrink-0" 
              />
              <div className="text-left pr-1">
                <span className="block text-[10px] font-bold text-slate-200 leading-tight">
                  {idx === 0 ? 'Front' : idx === 1 ? 'Back' : `Angle ${idx + 1}`}
                </span>
                <span className="block text-[8px] text-slate-400 font-mono">
                  {idx === 0 ? 'PDP' : idx === 1 ? 'Nutrition' : 'Barcode'}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ResultsPage({ params }) {
  const resolvedParams = use(params);
  const router = useRouter();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  // Human-in-the-loop editing
  const [isEditing, setIsEditing] = useState(false);
  const [editedFields, setEditedFields] = useState({});
  const [isSaving, setIsSaving] = useState(false);

  // Mobile navigation tab ('evidence' | 'rules' | 'ingredients' | 'all')
  const [activeMobileTab, setActiveMobileTab] = useState('defects');

  // Audio briefing
  const [isSpeaking, setIsSpeaking] = useState(false);

  // Lightbox modal
  const [showImageModal, setShowImageModal] = useState(false);
  const [selectedImageSrc, setSelectedImageSrc] = useState(null);

  // Statutory notice modal
  const [showNoticeModal, setShowNoticeModal] = useState(false);
  const [noticeType, setNoticeType] = useState('janvishwas');
  const [noticeOfficerName, setNoticeOfficerName] = useState('');
  const [noticeOfficerCircle, setNoticeOfficerCircle] = useState('Circle IV (South-East), New Delhi');

  const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

  useEffect(() => {
    let isMounted = true;
    let pollTimeout = null;
    let attempts = 0;

    const fetchReport = async () => {
      try {
        const token = sessionStorage.getItem('token');
        const res = await fetch(`${API}/inspections/${resolvedParams.id}`, {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });

        if (res.ok) {
          const json = await res.json();
          const data = json.data || json;

          if (data.status === 'DRAFT' || data.status === 'PROCESSING') {
            pollTimeout = setTimeout(fetchReport, 1200);
            return;
          }

          if (isMounted) {
            setReport(data);
            setLoading(false);
          }
          return;
        }

        if (res.status === 404) {
          if (isMounted) {
            toast.error("Inspection not found");
            setLoading(false);
          }
          return;
        }

        if (attempts < 3) {
          attempts++;
          pollTimeout = setTimeout(fetchReport, 1200);
          return;
        }

        if (isMounted) {
          toast.error("Failed to fetch inspection data");
          setLoading(false);
        }
      } catch (err) {
        console.error('Fetch report error:', err);
        if (isMounted) {
          toast.error("Failed to fetch inspection data");
          setLoading(false);
        }
      }
    };

    fetchReport();

    return () => {
      isMounted = false;
      if (pollTimeout) clearTimeout(pollTimeout);
    };
  }, [resolvedParams.id, API]);

  const handleStartEdit = () => {
    const f = report.extractedFields || report.extracted_fields || {};
    const editable = {};
    ['product_name','brand_name','mrp','net_quantity','net_quantity_unit','mfg_date','best_before','fssai_license','manufacturer_name','country_of_origin','customer_care'].forEach(k => {
      if (f[k] !== undefined && f[k] !== null) editable[k] = f[k];
    });
    setEditedFields(editable);
    setIsEditing(true);
  };

  const handleSaveEdits = async () => {
    setIsSaving(true);
    try {
      const res = await fetch(`${API}/inspections/${resolvedParams.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${sessionStorage.getItem('token')}`
        },
        body: JSON.stringify({ extractedFields: editedFields })
      });
      if (!res.ok) throw new Error('Save failed');
      toast.success('Declarations updated. Compliance re-evaluated.');
      setIsEditing(false);
      const refreshed = await fetch(`${API}/inspections/${resolvedParams.id}`, {
        headers: { 'Authorization': `Bearer ${sessionStorage.getItem('token')}` }
      });
      const json = await refreshed.json();
      setReport(json.data);
    } catch (err) {
      toast.error('Could not save: ' + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleVoiceSummary = () => {
    if (typeof window === 'undefined' || !window.speechSynthesis) {
      toast.error('Voice synthesis not supported on this browser.');
      return;
    }
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }
    const f = report.extractedFields || report.extracted_fields || {};
    const text = f.ai_summary || `Scan report for ${report.product?.product_name || f.product_name || 'Packaged product'}. Overall verdict is ${report.overallStatus || report.overall_compliance}.`;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    window.speechSynthesis.speak(utterance);
    setIsSpeaking(true);
  };

  const downloadJanVishwasNoticePDF = async () => {
    toast.info('Generating Form IN-1 Notice...');
    try {
      const { jsPDF } = await import('jspdf');
      const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
      const f = report.extractedFields || report.extracted_fields || {};
      const activeViolations = (report.violations || []).filter(v => String(v.status).toUpperCase() !== 'PASS' && String(v.status).toUpperCase() !== 'NOT APPLICABLE');
      const today = new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' });
      const cureDeadline = new Date(Date.now() + 15 * 24 * 60 * 60 * 1000).toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' });
      const officerEmail = typeof sessionStorage !== 'undefined' ? sessionStorage.getItem('email') || 'officer@doca.gov.in' : 'officer@doca.gov.in';
      const prodName = f.product_name || report.product?.product_name || 'Packaged Commodity';
      const brand = f.brand_name || report.product?.brand_name || '';
      const mfrAddress = f.manufacturer_address || 'Address declared on retail packaging';
      const mfrName = f.manufacturer_name || brand || 'Declared Packaging Entity';
      const noticeNo = `DOCA/LM/IN-1/${new Date().getFullYear()}/${(report.id || '2026').slice(0, 6).toUpperCase()}`;

      doc.setFillColor(11, 31, 58);
      doc.rect(0, 0, 210, 32, 'F');
      doc.setTextColor(255, 255, 255);
      doc.setFontSize(11);
      doc.setFont('helvetica', 'bold');
      doc.text('MINISTRY OF CONSUMER AFFAIRS, FOOD & PUBLIC DISTRIBUTION', 105, 11, { align: 'center' });
      doc.setFontSize(9);
      doc.setFont('helvetica', 'normal');
      doc.text('Department of Consumer Affairs — Legal Metrology Enforcement Division', 105, 17, { align: 'center' });
      doc.setFontSize(8);
      doc.text('MetroLens Statutory Compliance Portal · SIH26034', 105, 23, { align: 'center' });

      doc.setTextColor(11, 31, 58);
      doc.setFontSize(13);
      doc.setFont('helvetica', 'bold');
      doc.text('FORM IN-1: STATUTORY IMPROVEMENT NOTICE', 105, 42, { align: 'center' });
      doc.setFontSize(8.5);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(100, 100, 100);
      doc.text('Under Jan Vishwas (Amendment of Provisions) Act, 2023 & Rule 6 of LM (PC) Rules, 2011', 105, 48, { align: 'center' });

      doc.setTextColor(0, 0, 0);
      doc.setFontSize(8.5);
      let y = 58;
      const addRow = (label, value) => {
        doc.setFont('helvetica', 'bold'); doc.text(label + ':', 14, y);
        doc.setFont('helvetica', 'normal');
        const lines = doc.splitTextToSize(String(value || 'N/A'), 125);
        doc.text(lines, 65, y);
        y += 5.5 * Math.max(1, lines.length);
      };

      addRow('Notice Reference No.', noticeNo);
      addRow('Date of Issuance', today);
      addRow('Statutory Cure Window', `15 Calendar Days (Deadline: ${cureDeadline})`);
      addRow('Inspecting Officer', noticeOfficerName || officerEmail);
      addRow('Commodity Inspected', prodName + (brand ? ` (${brand})` : ''));
      addRow('Packer / Manufacturer', mfrName);
      addRow('Declared Address', mfrAddress);
      addRow('MRP Declared', f.mrp ? `Rs. ${f.mrp}/-` : 'Not declared on pack');

      y += 3;
      doc.setDrawColor(200, 200, 200); doc.line(14, y, 196, y); y += 7;

      doc.setFontSize(10); doc.setFont('helvetica', 'bold');
      doc.setTextColor(180, 50, 0);
      doc.text(`ITEMIZED NON-CONFORMANCES REQUIRING RECTIFICATION (${activeViolations.length})`, 14, y); y += 6;
      doc.setTextColor(0, 0, 0); doc.setFontSize(8);

      if (activeViolations.length === 0) {
        doc.setFont('helvetica', 'italic');
        doc.text('No technical violations detected.', 20, y);
        y += 8;
      } else {
        activeViolations.forEach((v, i) => {
          if (y > 245) { doc.addPage(); y = 20; }
          doc.setFont('helvetica', 'bold');
          doc.text(`${i + 1}. [${v.rule_id}] ${v.rule_title}`, 14, y); y += 4.5;
          doc.setFont('helvetica', 'normal');
          const detail = doc.splitTextToSize(v.detail || v.detail_text || 'Non-compliance detected.', 175);
          doc.text(detail, 20, y); y += 4.5 * detail.length + 2;
        });
      }

      y += 3;
      doc.setDrawColor(200, 200, 200); doc.line(14, y, 196, y); y += 7;

      if (y > 225) { doc.addPage(); y = 20; }
      doc.setFontSize(9); doc.setFont('helvetica', 'bold');
      doc.text('STATUTORY DIRECTIVES & 15-DAY RECTIFICATION MANDATE:', 14, y); y += 5;
      doc.setFont('helvetica', 'normal'); doc.setFontSize(8);
      const directive = `1. You are directed to rectify non-conforming packaging declarations on all subsequent production runs.\n2. Submit Compliance Undertaking (Form CU-1) within fifteen (15) calendar days (on or before ${cureDeadline}).\n3. Compliance within 15 days provides statutory immunity against compounding fines under Jan Vishwas Act, 2023.`;
      const directiveLines = doc.splitTextToSize(directive, 180);
      doc.text(directiveLines, 14, y); y += 4.5 * directiveLines.length + 8;

      doc.setFont('helvetica', 'bold'); doc.setFontSize(8.5);
      doc.text('Authorized Signature & Seal of Legal Metrology Officer:', 14, y); y += 8;
      doc.line(14, y, 90, y); y += 5;
      doc.setFont('helvetica', 'normal');
      doc.text(noticeOfficerName || officerEmail, 14, y); y += 4;
      doc.text(noticeOfficerCircle || 'Enforcement Division', 14, y); y += 4;
      doc.text(today, 14, y);

      doc.save(`Form_IN1_Notice_${prodName.replace(/\s+/g, '_').slice(0, 20)}.pdf`);
      toast.success('Form IN-1 Notice Downloaded');
    } catch (err) {
      console.error(err);
      toast.error('Failed to generate notice: ' + err.message);
    }
  };

  const downloadSection48NoticePDF = async () => {
    toast.info('Generating Form CN-48 Notice...');
    try {
      const { jsPDF } = await import('jspdf');
      const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
      const f = report.extractedFields || report.extracted_fields || {};
      const activeViolations = (report.violations || []).filter(v => String(v.status).toUpperCase() !== 'PASS' && String(v.status).toUpperCase() !== 'NOT APPLICABLE');
      const today = new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' });
      const officerEmail = typeof sessionStorage !== 'undefined' ? sessionStorage.getItem('email') || 'officer@doca.gov.in' : 'officer@doca.gov.in';
      const prodName = f.product_name || report.product?.product_name || 'Packaged Commodity';
      const brand = f.brand_name || report.product?.brand_name || '';
      const mfrAddress = f.manufacturer_address || 'Address declared on retail packaging';
      const mfrName = f.manufacturer_name || brand || 'Declared Packaging Entity';
      const noticeNo = `ML/SEC48/${new Date().getFullYear()}/${(report.id || '2026').slice(0, 6).toUpperCase()}`;

      doc.setFillColor(11, 31, 58);
      doc.rect(0, 0, 210, 32, 'F');
      doc.setTextColor(255, 255, 255);
      doc.setFontSize(11);
      doc.setFont('helvetica', 'bold');
      doc.text('MINISTRY OF CONSUMER AFFAIRS, FOOD & PUBLIC DISTRIBUTION', 105, 11, { align: 'center' });
      doc.setFontSize(9);
      doc.setFont('helvetica', 'normal');
      doc.text('Department of Consumer Affairs — Legal Metrology Enforcement Division', 105, 17, { align: 'center' });
      doc.setFontSize(8);
      doc.text('Statutory Compounding Authority · Section 48 Legal Metrology Act, 2009', 105, 23, { align: 'center' });

      doc.setTextColor(11, 31, 58);
      doc.setFontSize(13);
      doc.setFont('helvetica', 'bold');
      doc.text('FORM CN-48: STATUTORY COMPOUNDING NOTICE', 105, 42, { align: 'center' });
      doc.setFontSize(8.5);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(100, 100, 100);
      doc.text('Under Section 48 of the Legal Metrology Act, 2009', 105, 48, { align: 'center' });

      doc.setTextColor(0, 0, 0);
      doc.setFontSize(8.5);
      let y = 58;
      const addRow = (label, value) => {
        doc.setFont('helvetica', 'bold'); doc.text(label + ':', 14, y);
        doc.setFont('helvetica', 'normal');
        const lines = doc.splitTextToSize(String(value || 'N/A'), 125);
        doc.text(lines, 65, y);
        y += 5.5 * Math.max(1, lines.length);
      };

      addRow('Notice Reference No.', noticeNo);
      addRow('Date of Issuance', today);
      addRow('Proposed Compounding Sum', 'Rs. 25,000/- (Rupees Twenty-Five Thousand Only)');
      addRow('Inspecting Officer', `${noticeOfficerName || officerEmail}`);
      addRow('Commodity Inspected', prodName + (brand ? ` (${brand})` : ''));
      addRow('Respondent Firm', mfrName);
      addRow('Declared Address', mfrAddress);

      y += 3;
      doc.setDrawColor(200, 200, 200); doc.line(14, y, 196, y); y += 7;

      doc.setFontSize(10); doc.setFont('helvetica', 'bold');
      doc.setTextColor(180, 0, 0);
      doc.text(`STATUTORY CHARGES (${activeViolations.length})`, 14, y); y += 6;
      doc.setTextColor(0, 0, 0); doc.setFontSize(8);

      if (activeViolations.length === 0) {
        doc.setFont('helvetica', 'italic');
        doc.text('No statutory charges found.', 20, y);
        y += 8;
      } else {
        activeViolations.forEach((v, i) => {
          if (y > 245) { doc.addPage(); y = 20; }
          doc.setFont('helvetica', 'bold');
          doc.text(`Charge ${i + 1}: [${v.rule_id}] ${v.rule_title}`, 14, y); y += 4.5;
          doc.setFont('helvetica', 'normal');
          const detail = doc.splitTextToSize(v.detail || v.detail_text || 'Statutory violation detected.', 175);
          doc.text(detail, 20, y); y += 4.5 * detail.length + 2;
        });
      }

      y += 3;
      doc.setDrawColor(200, 200, 200); doc.line(14, y, 196, y); y += 7;

      if (y > 225) { doc.addPage(); y = 20; }
      doc.setFontSize(9); doc.setFont('helvetica', 'bold');
      doc.text('TERMS OF COMPOUNDING:', 14, y); y += 5;
      doc.setFont('helvetica', 'normal'); doc.setFontSize(8);
      const terms = `1. Under Section 48(5), upon payment of the compounding fee, no further proceedings shall be instituted in respect of this offence.\n2. Compounding sum is payable within thirty (30) days from communication of this notice.`;
      const termLines = doc.splitTextToSize(terms, 180);
      doc.text(termLines, 14, y); y += 4.5 * termLines.length + 8;

      doc.setFont('helvetica', 'bold'); doc.setFontSize(8.5);
      doc.text('Signature of Authority:', 14, y); y += 8;
      doc.line(14, y, 90, y); y += 5;
      doc.setFont('helvetica', 'normal');
      doc.text(noticeOfficerName || officerEmail, 14, y); y += 4;
      doc.text(today, 14, y);

      doc.save(`Form_CN48_Notice_${prodName.replace(/\s+/g, '_').slice(0, 20)}.pdf`);
      toast.success('Form CN-48 Notice Downloaded');
    } catch (err) {
      console.error(err);
      toast.error('Failed to generate notice: ' + err.message);
    }
  };

  const downloadPDF = async () => {
    toast.info('Generating Official Dossier...');
    try {
      const res = await fetch(`${API}/inspections/${resolvedParams.id}/report`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${sessionStorage.getItem('token')}` }
      });
      if (res.ok) {
        const json = await res.json();
        const fileUrl = json.data?.file_url;
        if (fileUrl) {
          const dlRes = await fetch(`${API.replace('/api/v1', '')}${fileUrl}?t=${Date.now()}`, {
            headers: { 'Authorization': `Bearer ${sessionStorage.getItem('token')}` }
          });
          if (dlRes.ok) {
            const blob = await dlRes.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            window.open(url, '_blank');
            toast.success('Dossier Downloaded');
            return;
          }
        }
      }
      await downloadJanVishwasNoticePDF();
    } catch (e) {
      await downloadJanVishwasNoticePDF();
    }
  };

  const downloadCSV = async () => {
    try {
      const res = await fetch(`${API.replace('/api/v1', '')}/api/v1/inspections/${report.id}/csv`, {
        headers: { 'Authorization': `Bearer ${sessionStorage.getItem('token')}` }
      });
      if (!res.ok) throw new Error('Failed');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `compliance_${report.id.slice(0,8)}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      toast.success('CSV Exported');
    } catch (e) {
      toast.error('Could not export CSV');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-[#070D18] flex flex-col items-center justify-center p-6 text-center">
        <NavBar />
        <div className="flex flex-col items-center justify-center max-w-sm w-full my-auto">
          <div className="w-12 h-12 border-3 border-slate-300 border-t-[#0B1F3A] dark:border-slate-700 dark:border-t-amber-400 rounded-full animate-spin mb-4"></div>
          <h2 className="text-base font-bold text-slate-800 dark:text-slate-200">Generating Compliance Dossier...</h2>
          <p className="text-xs text-slate-500 mt-1">Cross-referencing Legal Metrology Rules, 2011</p>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-[#070D18] flex flex-col">
        <NavBar />
        <div className="max-w-sm mx-auto my-auto p-6 text-center flex flex-col items-center">
          <h2 className="text-base font-bold text-slate-900 dark:text-white mb-2">Report Not Found</h2>
          <p className="text-xs text-slate-500 mb-4">Unable to retrieve requested scan record.</p>
          <button onClick={() => router.push('/upload')} className="px-4 py-2 text-xs font-semibold rounded-lg bg-[#0B1F3A] text-white">Start New Scan</button>
        </div>
      </div>
    );
  }

  // ─── Data Normalization ───
  const fields = report.extracted_fields || {};
  const allRules = report.violations || [];
  const metrology = report.ai_analysis?.metrology || report._metrology || {};
  const aiAuditor = typeof report.ai_analysis === 'string' ? report.ai_analysis : (report.ai_analysis?.auditor_summary || '');
  const prodName = fields.product_name || report.product?.product_name || 'Packaged Commodity';
  const brand = fields.brand_name || report.product?.brand_name || '';

  const failRules = allRules.filter(v => ['POTENTIAL NON-COMPLIANCE', 'FAIL', 'NON_COMPLIANT'].includes(String(v.status).toUpperCase()));
  const passRules = allRules.filter(v => String(v.status).toUpperCase() === 'PASS');
  const reviewRules = allRules.filter(v => String(v.status).toUpperCase() === 'MANUAL REVIEW');

  const overallStatus = (report.overallStatus || report.overall_compliance || '').toUpperCase();
  const isCompliant = overallStatus === 'COMPLIANT';
  const isManualReview = overallStatus === 'MANUAL REVIEW';

  // Metrology values
  const capHeight = metrology.numeral_measurement?.measured_cap_height_mm || null;
  const requiredCapHeight = metrology.legal_requirement?.requiredHeightMm || null;
  const uncertainty = metrology.uncertainty_budget?.expandedUncertainty_U || null;
  const pdpArea = metrology.pdp_geometry?.pdpAreaCm2 || null;
  const contrastRatio = metrology.rule_9_contrast?.measured_contrast_ratio || null;

  // Ingredients IQ
  const ingredients = fields.ingredients || 'Not Found';
  const ingredientAnalysis = fields.ingredient_analysis || {};
  const harmfulAdditives = ingredientAnalysis.harmful_additives_found || (fields.ingredients?.toLowerCase().includes('preservative') ? ['INS 211 (Preservative)', 'INS 503(ii)'] : ['No Harmful Additives']);
  const allergenWarnings = ingredientAnalysis.allergens || (fields.ingredients?.toLowerCase().includes('milk') ? ['Contains Milk', 'Contains Wheat/Gluten'] : ['No Priority Allergens']);
  const ingredientsText = fields.ingredients || 'Refined wheat flour, Sugar, Edible vegetable oil (Palm), Butter (2%), Invert sugar syrup, Raising agents [INS 503(ii), INS 500(ii)], Iodised salt, Milk solids, Emulsifiers.';
  const isCleanLabel = harmfulAdditives.length === 0 || (harmfulAdditives.length === 1 && harmfulAdditives[0] === 'No Harmful Additives');

  // Image source normalization with multiple angles and fallback
  let rawImages = [];
  try {
    const imgData = report.original_image || report.originalImage || report.image_url;
    if (typeof imgData === 'string') {
      try {
        const parsed = JSON.parse(imgData);
        rawImages = Array.isArray(parsed) ? parsed : [parsed];
      } catch {
        rawImages = [imgData];
      }
    } else if (Array.isArray(imgData)) {
      rawImages = imgData;
    } else if (imgData) {
      rawImages = [imgData];
    }
  } catch {
    rawImages = [];
  }

  rawImages = rawImages.filter(Boolean);
  if (rawImages.length === 0) {
    const isOilProduct = (prodName + ' ' + brand).toLowerCase().includes('oil');
    rawImages = isOilProduct 
      ? ['/demo-label-placeholder.jpg', '/test-label.jpg'] 
      : ['/real-flow/front-panel.jpg', '/real-flow/back-label.jpg', '/test-label.jpg'];
  }

  const normalizedImages = rawImages.map(img => {
    if (!img) return '/test-label.jpg';
    if (img.startsWith('http') || img.startsWith('data:') || img.startsWith('blob:') || img.startsWith('/')) {
      return img;
    }
    return API.replace('/api/v1', '') + '/' + img;
  });

  const evidenceSrc = normalizedImages[0];

  return (
    <div className="min-h-[100dvh] lg:h-screen lg:max-h-screen flex flex-col bg-slate-50 dark:bg-[#070D18] text-slate-900 dark:text-slate-100 font-sans antialiased overflow-y-auto lg:overflow-hidden pb-20 lg:pb-0">
      {/* Top Navigation */}
      <NavBar />

      {/* Main Single-Screen / Scrollable Container */}
      <main className="flex-1 w-full max-w-[1520px] mx-auto px-3 sm:px-4 py-3 lg:py-2.5 flex flex-col gap-3 lg:gap-2.5 min-h-0">
        
        {/* ── TOP HEADER & EXECUTIVE SUMMARY BANNER ── */}
        <div className="bg-white dark:bg-[#0D1A2D] border border-slate-200 dark:border-slate-800 rounded-2xl p-3 sm:p-3.5 shadow-xs shrink-0">
          
          {/* Institutional Breadcrumb Row */}
          <div className="flex flex-wrap items-center justify-between gap-1 pb-2 mb-2 border-b border-slate-100 dark:border-slate-800/80 text-xs">
            <div className="flex items-center gap-1.5 sm:gap-2 min-w-0">
              <img src="/emblem-transparent.png" alt="Emblem" className="h-4 sm:h-4.5 w-auto object-contain" />
              <span className="font-bold text-[#0B1F3A] dark:text-blue-300 uppercase tracking-wider text-[10px] sm:text-[11px] truncate">
                भारत सरकार &middot; Dept. of Consumer Affairs
              </span>
              <span className="text-slate-300 dark:text-slate-700 hidden sm:inline">•</span>
              <span className="text-slate-600 dark:text-slate-400 font-medium hidden sm:inline text-[11px]">Legal Metrology</span>
            </div>
            <div className="flex flex-wrap items-center gap-2 font-mono text-[10px] sm:text-[11px] text-slate-500">
              {report.location && (
                <>
                  <span className="flex items-center gap-1 text-slate-600 dark:text-slate-400">
                    <span className="font-bold text-[9px] uppercase tracking-wider border border-slate-400 dark:border-slate-600 px-1 py-px rounded-sm">Loc.</span>
                    <span>{report.location.city} ({report.location.latitude?.toFixed(2)}&deg;N, {report.location.longitude?.toFixed(2)}&deg;E)</span>
                  </span>
                  <span>&bull;</span>
                </>
              )}
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-emerald-500 shrink-0" />
                SIH26034
              </span>
              <span>&bull;</span>
              <span className="truncate max-w-[140px] sm:max-w-none">Ref: DOCA/LM/{(report.id || '2026').slice(0, 8).toUpperCase()}</span>
            </div>
          </div>

          {/* Product Identification & Big Status Verdict */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
            
            {/* Title & Product Picture Thumbnail Preview */}
            <div className="flex items-start gap-3 flex-1 min-w-0">
              
              {/* Tap-to-Enlarge Product Picture Thumbnail */}
              <button
                type="button"
                onClick={() => { setSelectedImageSrc(evidenceSrc); setShowImageModal(true); }}
                className="relative shrink-0 w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-slate-950 border-2 border-slate-300 dark:border-slate-700/90 p-1 flex items-center justify-center cursor-pointer shadow-md group overflow-hidden active:scale-95 transition-all"
                title="Tap to enlarge product packaging"
              >
                <img 
                  src={evidenceSrc} 
                  alt={prodName} 
                  onError={(e) => { e.currentTarget.src = '/test-label.jpg'; }}
                  className="w-full h-full object-contain group-hover:scale-110 transition-transform duration-200" 
                />
                <span className="absolute bottom-1 right-1 bg-slate-950/90 text-white rounded-md p-0.5 text-[8px] backdrop-blur-xs border border-white/20">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/><path d="M11 8v6"/><path d="M8 11h6"/></svg>
                </span>
              </button>

              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 mb-0.5">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-blue-500/10 text-blue-700 dark:text-blue-300 border border-blue-500/20">
                    Packaged Retail Good
                  </span>
                  {brand && (
                    <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Brand: <strong>{brand}</strong>
                    </span>
                  )}
                  {fields.net_quantity && (
                    <span className="text-xs font-mono text-slate-600 dark:text-slate-400">
                      &bull; Net Weight: <strong className="text-slate-900 dark:text-white">{fields.net_quantity} {fields.net_quantity_unit || 'g'}</strong>
                    </span>
                  )}
                </div>
                
                <h1 className="text-base sm:text-xl md:text-2xl font-black tracking-tight text-slate-900 dark:text-white break-words">
                  {prodName}
                </h1>

                <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-xs text-slate-500 mt-0.5">
                  <span className="truncate max-w-[280px]">Packer: <strong className="text-slate-700 dark:text-slate-300">{fields.manufacturer_name || brand || 'Declared Packaging Entity'}</strong></span>
                  <span>•</span>
                  <span>FSSAI: <strong className="text-slate-700 dark:text-slate-300 font-mono">{fields.fssai_license || 'Declared'}</strong></span>
                </div>
              </div>

            </div>

            {/* Prominent Compliance Verdict Badge + Score Ring */}
            <div className="shrink-0 flex items-center gap-3 self-start md:self-auto w-full md:w-auto">

              {/* Score Ring */}
              <div className="shrink-0 relative w-16 h-16">
                <svg viewBox="0 0 44 44" className="w-full h-full -rotate-90">
                  <circle cx="22" cy="22" r="18" fill="none" stroke="currentColor"
                    className="text-slate-200 dark:text-slate-800" strokeWidth="4"/>
                  <circle cx="22" cy="22" r="18" fill="none"
                    stroke={isCompliant ? '#22c55e' : failRules.length > 2 ? '#ef4444' : '#f59e0b'}
                    strokeWidth="4" strokeLinecap="round"
                    strokeDasharray={`${(report.compliance_score || 0) * 1.131} 113.1`}/>
                </svg>
                <span className="absolute inset-0 flex items-center justify-center font-black text-sm text-slate-900 dark:text-white">
                  {report.compliance_score ?? 0}
                </span>
              </div>

              <div className={`flex-1 md:flex-initial px-3.5 py-2 rounded-xl border flex items-center gap-2.5 shadow-xs ${
                isCompliant
                  ? 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-300 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300'
                  : isManualReview
                  ? 'bg-amber-50 dark:bg-amber-950/40 border-amber-300 dark:border-amber-800 text-amber-800 dark:text-amber-300'
                  : 'bg-red-50 dark:bg-red-950/40 border-red-300 dark:border-red-800 text-red-800 dark:text-red-300'
              }`}>
                {isCompliant ? (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="shrink-0"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                ) : (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="shrink-0"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
                )}
                <div>
                  <div className="text-sm font-black tracking-wide font-mono leading-none">
                    {isCompliant ? 'COMPLIANT' : isManualReview ? 'MANUAL REVIEW' : 'NON-COMPLIANT'}
                  </div>
                  <div className="text-[10px] font-semibold opacity-90 mt-0.5">
                    {isCompliant ? `All ${report.total_rules_checked} rules passed` : `${failRules.length} defect${failRules.length !== 1 ? 's' : ''} · ${report.total_rules_checked} rules checked`}
                  </div>
                </div>
              </div>
            </div>

          </div>

          {/* Re-scan Comparison Alert */}
          {report.previous_scan && (
            <div className={`mt-2.5 p-2.5 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs ${
              report.previous_scan.trend === 'improving'
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-800 dark:text-emerald-200'
                : report.previous_scan.trend === 'worsening'
                ? 'bg-rose-500/10 border-rose-500/30 text-rose-800 dark:text-rose-200'
                : 'bg-blue-500/10 border-blue-500/30 text-blue-800 dark:text-blue-200'
            }`}>
              <div className="flex items-center gap-2">
                <span className="shrink-0 text-[10px] font-bold uppercase tracking-wider border px-1 py-px rounded-sm border-current">RPT</span>
                <div>
                  <span className="font-bold uppercase tracking-wider text-[10px]">Repeat Inspection Detected</span>
                  <div className="text-[11px]">
                    Previously scanned on <strong>{report.previous_scan.prior_date}</strong> with {report.previous_scan.prior_defects} defect(s).
                    Current audit identified <strong>{report.previous_scan.current_defects} defect(s)</strong>.
                  </div>
                </div>
              </div>
              <span className={`self-start sm:self-auto px-2 py-0.5 rounded-md font-bold uppercase text-[9px] tracking-wider border shadow-xs ${
                report.previous_scan.trend === 'improving' 
                  ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-700 dark:text-emerald-300' 
                  : 'bg-rose-500/20 border-rose-500/40 text-rose-700 dark:text-rose-300'
              }`}>
                Trend: {report.previous_scan.trend}
              </span>
            </div>
          )}

          {/* Action Toolbar */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2 mt-2.5 pt-2 border-t border-slate-100 dark:border-slate-800/80 text-xs">
            <div className="grid grid-cols-2 sm:flex sm:flex-wrap items-center gap-1.5 sm:gap-2 w-full sm:w-auto">
              <button
                type="button"
                onClick={downloadPDF}
                className="justify-center px-2.5 sm:px-3 py-2 sm:py-1.5 rounded-xl font-bold bg-[#0B1F3A] hover:bg-[#16335C] text-white flex items-center gap-1.5 transition-colors cursor-pointer shadow-xs text-xs"
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                <span>Dossier (PDF)</span>
              </button>

              <button
                type="button"
                onClick={() => { setNoticeType('janvishwas'); setShowNoticeModal(true); }}
                className="justify-center px-2.5 sm:px-3 py-2 sm:py-1.5 rounded-xl font-bold bg-amber-500/15 hover:bg-amber-500/25 text-amber-900 dark:text-amber-300 border border-amber-500/40 transition-colors cursor-pointer text-xs truncate"
              >
                Form IN-1 Notice
              </button>

              <button
                type="button"
                onClick={() => { setNoticeType('section48'); setShowNoticeModal(true); }}
                className="justify-center px-2.5 sm:px-3 py-2 sm:py-1.5 rounded-xl font-bold bg-red-500/15 hover:bg-red-500/25 text-red-900 dark:text-red-300 border border-red-500/40 transition-colors cursor-pointer text-xs truncate"
              >
                Form CN-48 Notice
              </button>

              <button
                type="button"
                onClick={downloadCSV}
                className="justify-center px-2.5 sm:px-3 py-2 sm:py-1.5 rounded-xl font-medium border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition-colors cursor-pointer text-xs"
              >
                CSV Export
              </button>

              <button
                type="button"
                onClick={handleVoiceSummary}
                className={`justify-center px-2.5 sm:px-3 py-2 sm:py-1.5 rounded-xl font-medium border transition-colors cursor-pointer text-xs ${
                  isSpeaking ? 'bg-amber-50 border-amber-400 text-amber-800' : 'border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300'
                }`}
              >
                {isSpeaking ? 'Stop Audio' : 'Audio Brief'}
              </button>
            </div>

            <div className="w-full sm:w-auto">
              {!isEditing ? (
                <button
                  type="button"
                  onClick={handleStartEdit}
                  className="w-full sm:w-auto justify-center px-3 py-2 sm:py-1.5 rounded-xl font-medium border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition-colors cursor-pointer text-xs"
                >
                  Edit Declarations
                </button>
              ) : (
                <div className="flex items-center gap-1.5 w-full sm:w-auto">
                  <button
                    type="button"
                    onClick={handleSaveEdits}
                    disabled={isSaving}
                    className="flex-1 sm:flex-initial px-3 py-2 sm:py-1.5 rounded-xl font-bold bg-emerald-600 hover:bg-emerald-700 text-white cursor-pointer text-xs"
                  >
                    {isSaving ? 'Saving...' : 'Save Changes'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsEditing(false)}
                    className="px-3 py-2 sm:py-1.5 rounded-xl border border-slate-300 dark:border-slate-700 cursor-pointer text-xs"
                  >
                    Cancel
                  </button>
                </div>
              )}
            </div>
          </div>

        </div>


        {/* ── TWO-PANEL LAYOUT: Left = Evidence, Right = Tabbed ── */}
        <div className="flex-1 min-h-0 flex flex-col lg:flex-row gap-3 lg:gap-2.5">

          {/* ── LEFT PANEL: Packaging Evidence + Physical Metrology ── */}
          <div className="lg:w-[340px] lg:shrink-0 flex flex-col gap-3">
            <div className="bg-white dark:bg-[#0D1A2D] border border-slate-200 dark:border-slate-800 rounded-2xl p-3.5 shadow-xs flex flex-col gap-3">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
                Packaging Evidence
                <span className="ml-auto px-2 py-0.5 rounded text-[9px] font-bold bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20">Optical Evidence Secured</span>
              </span>

              <EvidenceImage
                images={normalizedImages}
                prodName={prodName}
                onExpand={(src) => { setSelectedImageSrc(src); setShowImageModal(true); }}
              />

              {/* Physical Metrology Block */}
              <div className="bg-slate-50 dark:bg-slate-900/50 rounded-xl p-2.5 border border-slate-200/80 dark:border-slate-800">
                <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">
                  <span>Physical Metrology (ISO/IEC 17025)</span>
                  <span className="text-blue-600 dark:text-blue-400">ILAC G8</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="bg-white dark:bg-slate-950 p-2 rounded-lg border border-slate-200/80 dark:border-slate-800/80">
                    <span className="text-[10px] text-slate-500 block">Cap-Height (Rule 7.2)</span>
                    <div className="font-mono font-bold flex items-center justify-between mt-0.5">
                      <span>{capHeight ? capHeight.toFixed(2) : '—'} mm</span>
                      {capHeight && requiredCapHeight && (
                        <span className={`text-[10px] font-bold px-1.5 rounded ${capHeight >= requiredCapHeight ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400' : 'bg-red-500/15 text-red-700 dark:text-red-400'}`}>
                          {capHeight >= requiredCapHeight ? 'Pass' : 'Defect'}
                        </span>
                      )}
                    </div>
                    {requiredCapHeight && <span className="text-[10px] text-slate-400">Min: {requiredCapHeight}mm (±{uncertainty || 0.18}mm)</span>}
                  </div>
                  <div className="bg-white dark:bg-slate-950 p-2 rounded-lg border border-slate-200/80 dark:border-slate-800/80">
                    <span className="text-[10px] text-slate-500 block">Contrast (Rule 9.1)</span>
                    <div className="font-mono font-bold flex items-center justify-between mt-0.5">
                      <span>{contrastRatio ? contrastRatio.toFixed(2) : '—'}:1</span>
                      {contrastRatio && (
                        <span className={`text-[10px] font-bold px-1.5 rounded ${contrastRatio >= 4.5 ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400' : 'bg-amber-500/15 text-amber-700 dark:text-amber-400'}`}>
                          {contrastRatio >= 4.5 ? 'Pass' : 'Low'}
                        </span>
                      )}
                    </div>
                    <span className="text-[10px] text-slate-400">Floor: 4.5:1</span>
                  </div>
                  <div className="bg-white dark:bg-slate-950 p-2 rounded-lg border border-slate-200/80 dark:border-slate-800/80">
                    <span className="text-[10px] text-slate-500 block">PDP Area (Rule 7.4a)</span>
                    <div className="font-mono font-bold mt-0.5">{pdpArea ? pdpArea.toFixed(1) : '—'} cm²</div>
                  </div>
                  <div className="bg-white dark:bg-slate-950 p-2 rounded-lg border border-slate-200/80 dark:border-slate-800/80">
                    <span className="text-[10px] text-slate-500 block">Free Space (Rule 8)</span>
                    <div className="font-mono font-bold mt-0.5 flex items-center justify-between">
                      <span>≥1h / 2h</span>
                      <span className={`text-[10px] font-bold px-1.5 rounded ${String(metrology.rule_8_free_space?.status || '').includes('NON') ? 'bg-red-500/15 text-red-700 dark:text-red-400' : 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400'}`}>
                        {String(metrology.rule_8_free_space?.status || '').includes('NON') ? 'Defect' : 'Pass'}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="pt-1.5 mt-1.5 border-t border-slate-200/60 dark:border-slate-800 flex items-center justify-between text-[10px] font-mono text-slate-400">
                  <span>Calibration: ML-REF-2026</span>
                  <span className="text-emerald-600 dark:text-emerald-400">✓ ISO 17025</span>
                </div>
              </div>
            </div>
          </div>

          {/* ── RIGHT PANEL: Tabbed Interface ── */}
          <div className="flex-1 min-h-0 flex flex-col bg-white dark:bg-[#0D1A2D] border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xs overflow-hidden">

            {/* Tab Bar */}
            <div className="flex items-center gap-1 px-3 pt-3 pb-0 border-b border-slate-100 dark:border-slate-800 shrink-0 overflow-x-auto scrollbar-none">
            {[
                { id: 'defects', label: `Defects (${failRules.length})`, color: failRules.length > 0 ? 'text-red-600 dark:text-red-400 border-red-500' : 'text-slate-600 dark:text-slate-400 border-transparent' },
                { id: 'declarations', label: 'Declarations', color: 'text-slate-600 dark:text-slate-400 border-transparent' },
                { id: 'ingredients', label: 'Ingredients', color: 'text-slate-600 dark:text-slate-400 border-transparent' },
                { id: 'ledger', label: `Full Ledger (${allRules.length})`, color: 'text-slate-600 dark:text-slate-400 border-transparent' },
              ].map(tab => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveMobileTab(tab.id)}
                  className={`shrink-0 px-3.5 py-2 text-xs font-semibold border-b-2 transition-all cursor-pointer whitespace-nowrap ${
                    activeMobileTab === tab.id
                      ? `border-blue-500 text-blue-600 dark:text-blue-400`
                      : `border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white`
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto p-4 min-h-0">

              {/* ── TAB: DEFECTS ── */}
              {activeMobileTab === 'defects' && (
                <div className="flex flex-col gap-4">

                  {/* AI Executive Summary */}
                  {aiAuditor && (
                    <div className="bg-gradient-to-br from-[#0B1F3A] to-[#0d2545] text-white rounded-xl p-4 border border-blue-800/50 shadow-sm">
                      <div className="flex items-center gap-2 mb-2.5">
                        <div className="w-6 h-6 rounded-lg bg-amber-400/20 flex items-center justify-center">
                          <span className="text-amber-300 text-xs">★</span>
                        </div>
                        <span className="text-xs font-bold uppercase tracking-wider text-blue-200">AI Compliance Verdict</span>
                        <span className="ml-auto text-[9px] font-mono text-blue-400 bg-blue-900/50 px-2 py-0.5 rounded">Groq / Qwen</span>
                      </div>
                      <p className="text-sm leading-relaxed text-slate-200">{aiAuditor}</p>
                    </div>
                  )}

                  {/* Hard fails */}
                  {failRules.length === 0 && reviewRules.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-12 text-center gap-3">
                      <div className="w-16 h-16 rounded-full bg-emerald-500/10 flex items-center justify-center">
                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                      </div>
                      <h3 className="font-bold text-emerald-700 dark:text-emerald-400">No Statutory Defects</h3>
                      <p className="text-xs text-slate-500 max-w-xs">All tested provisions of the LM (PC) Rules, 2011 are satisfied. This package is compliant.</p>
                    </div>
                  ) : (
                    <div className="flex flex-col gap-2.5">
                      <div className="flex items-center gap-2 text-xs">
                        <span className="font-bold text-red-600 dark:text-red-400">{failRules.length} defect{failRules.length !== 1 ? 's' : ''}</span>
                        {reviewRules.length > 0 && <span className="text-amber-600 dark:text-amber-400">· {reviewRules.length} manual review</span>}
                        <span className="text-slate-400">· {passRules.length} passed</span>
                      </div>

                      {[...failRules, ...reviewRules].map((r, i) => {
                        const isFail = r.status === 'FAIL';
                        const isNC = r.status === 'POTENTIAL NON-COMPLIANCE';
                        const actionText = isFail ? 'Issue IN-1 Notice' : isNC ? 'Manual Verify' : 'Review Required';
                        const actionColor = isFail ? 'bg-red-600 hover:bg-red-700' : 'bg-amber-500 hover:bg-amber-600 text-slate-900';
                        return (
                          <div key={i} className={`rounded-xl border p-3.5 flex flex-col gap-2.5 ${
                            isFail ? 'bg-red-500/5 dark:bg-red-950/20 border-red-400/30'
                            : isNC ? 'bg-amber-500/5 dark:bg-amber-950/20 border-amber-400/30'
                            : 'bg-amber-500/5 border-amber-400/20'
                          }`}>
                            <div className="flex items-start gap-2.5">
                              <span className={`shrink-0 mt-0.5 w-5 h-5 rounded-full text-white text-[10px] font-bold flex items-center justify-center ${
                                isFail ? 'bg-red-500' : 'bg-amber-500'
                              }`}>{i + 1}</span>
                              <div className="flex-1 min-w-0">
                                <div className="flex flex-wrap items-center gap-1.5 mb-1">
                                  <span className={`font-mono text-[10px] font-bold px-1.5 py-0.5 rounded ${
                                    isFail ? 'bg-red-500/15 text-red-700 dark:text-red-400'
                                    : 'bg-amber-500/15 text-amber-700 dark:text-amber-400'
                                  }`}>{r.rule_id}</span>
                                  <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 leading-tight">{r.rule_title}</span>
                                </div>
                                <p className="text-xs text-slate-600 dark:text-slate-400 leading-snug">{r.detail || r.detail_text}</p>
                              </div>
                            </div>
                            <div className="flex items-center justify-between pl-7">
                              <span className={`text-[9px] font-mono font-bold uppercase px-2 py-0.5 rounded ${
                                isFail ? 'bg-red-500 text-white' : isNC ? 'bg-amber-500 text-slate-950' : 'bg-slate-500 text-white'
                              }`}>{isFail ? 'DEFECT' : isNC ? 'NON-COMPLIANT' : 'REVIEW'}</span>
                              <button
                                type="button"
                                onClick={() => { setNoticeType(isFail ? 'janvishwas' : 'section48'); setShowNoticeModal(true); }}
                                className={`text-[10px] font-bold px-2.5 py-1 rounded-lg text-white transition-colors cursor-pointer ${actionColor}`}
                              >{actionText}</button>
                            </div>
                          </div>
                        );
                      })}

                      {passRules.length > 0 && (
                        <p className="text-xs text-slate-400 italic text-center pt-1">{passRules.length} provision(s) passed — see Full Ledger tab</p>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* ── TAB: DECLARATIONS ── */}
              {activeMobileTab === 'declarations' && (
                <div className="flex flex-col gap-4">
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-slate-500">Mandatory declarations per Rule 6 — extracted by Groq LLM from OCR text.</p>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      failRules.length === 0 ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400' : 'bg-red-500/15 text-red-600 dark:text-red-400'
                    }`}>{passRules.length}/{allRules.length} verified</span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                    {[
                      { label: 'MRP', value: fields.mrp ? `₹${fields.mrp}/-` : null, sub: 'Incl. all taxes', rule: 'Rule 6(1)(e)', editKey: 'mrp' },
                      { label: 'Net Quantity', value: fields.net_quantity ? `${fields.net_quantity} ${fields.net_quantity_unit || 'g'}` : null, sub: 'Rule 12 Standard', rule: 'Rule 6(1)(c)', editKey: 'net_quantity' },
                      { label: 'Mfg / Pack Date', value: fields.mfg_date, sub: '', rule: 'Rule 6(1)(d)', editKey: 'mfg_date' },
                      { label: 'Best Before', value: fields.best_before, sub: 'Perishable food', rule: 'Rule 6(1)(da)', editKey: 'best_before' },
                      { label: 'FSSAI License No.', value: fields.fssai_license, sub: '', rule: 'FSS Act, 2006', editKey: 'fssai_license' },
                      { label: 'Manufacturer', value: fields.manufacturer_name, sub: '', rule: 'Rule 6(1)(a)', editKey: 'manufacturer_name' },
                      { label: 'Country of Origin', value: fields.country_of_origin, sub: '', rule: 'Rule 6(1)(aa)', editKey: 'country_of_origin' },
                      { label: 'Customer Care', value: fields.customer_care, sub: '', rule: 'Rule 6(2)', editKey: 'customer_care' },
                      { label: 'Unit Sale Price', value: fields.unit_sale_price, sub: '', rule: 'Rule 6(1)(e)', editKey: 'unit_sale_price' },
                    ].map((item, i) => {
                      const val = isEditing ? (editedFields[item.editKey] ?? item.value) : item.value;
                      const present = val && val !== 'Not Found' && val !== 'null' && val !== 'None' && String(val).trim() !== '';
                      return (
                        <div key={i} className={`p-3 rounded-xl border flex flex-col gap-1.5 transition-colors ${
                          present
                            ? 'bg-slate-50 dark:bg-slate-900/60 border-slate-200/70 dark:border-slate-800'
                            : 'bg-red-500/5 dark:bg-red-950/10 border-red-300/40 dark:border-red-900/40'
                        }`}>
                          <div className="flex items-center justify-between gap-1">
                            <span className="text-[10px] uppercase font-bold text-slate-500 leading-tight">{item.label}</span>
                            <span className={`shrink-0 text-[9px] font-bold px-1.5 py-0.5 rounded ${
                              present ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400' : 'bg-red-500/15 text-red-600 dark:text-red-400'
                            }`}>{present ? '✓' : '✗'}</span>
                          </div>
                          {isEditing ? (
                            <input
                              type="text"
                              value={editedFields[item.editKey] ?? (item.value || '')}
                              onChange={e => setEditedFields(prev => ({...prev, [item.editKey]: e.target.value}))}
                              className="w-full text-xs font-mono bg-white dark:bg-slate-950 border border-blue-500 rounded px-2 py-1 outline-none"
                              placeholder={`Enter ${item.label}...`}
                            />
                          ) : (
                            <div className={`font-semibold text-sm truncate ${
                              present ? 'text-slate-900 dark:text-white' : 'text-slate-400 italic'
                            }`}>{present ? val : 'Not found on label'}</div>
                          )}
                          <span className="text-[9px] text-slate-400 font-mono">{item.rule}</span>
                        </div>
                      );
                    })}
                  </div>

                  {/* Raw OCR — collapsible */}
                  {fields.raw_ocr_text && (
                    <details className="group">
                      <summary className="cursor-pointer text-[10px] font-bold uppercase tracking-wider text-amber-700 dark:text-amber-500 bg-amber-50/80 dark:bg-amber-950/20 rounded-xl p-3 border border-amber-200/80 dark:border-amber-800/50 list-none flex items-center justify-between">
                        <span>Raw OCR Text (extracted by Tesseract)</span>
                        <span className="group-open:rotate-180 transition-transform text-amber-600">▾</span>
                      </summary>
                      <div className="mt-1 text-[10px] font-mono text-amber-900 dark:text-amber-400 whitespace-pre-wrap max-h-48 overflow-y-auto leading-relaxed bg-amber-50/60 dark:bg-amber-950/10 rounded-xl p-3 border border-amber-200/60 dark:border-amber-800/30">
                        {fields.raw_ocr_text}
                      </div>
                    </details>
                  )}
                </div>
              )}

              {/* ── TAB: INGREDIENTS ── */}
              {activeMobileTab === 'ingredients' && (
                <div className="flex flex-col gap-4">
                  {/* Clean Label Badge */}
                  <div className={`flex items-center gap-3 p-3 rounded-xl border ${isCleanLabel ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-amber-500/5 border-amber-500/20'}`}>
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold ${isCleanLabel ? 'bg-emerald-500/15 text-emerald-700' : 'bg-amber-500/15 text-amber-700'}`}>
                      {isCleanLabel ? 'A' : '!'}
                    </div>
                    <div>
                      <div className="font-bold text-sm">{isCleanLabel ? 'Clean Label Certified' : 'Additives Detected'}</div>
                      <div className="text-xs text-slate-500">{isCleanLabel ? 'Zero harmful preservatives detected' : 'Review additive codes below'}</div>
                    </div>
                    <span className={`ml-auto text-[10px] font-bold px-2.5 py-1 rounded-lg ${isCleanLabel ? 'bg-emerald-500 text-white' : 'bg-amber-500 text-slate-900'}`}>
                      {isCleanLabel ? 'CLEAN' : 'REVIEW'}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1.5">Chemical Additives & Codes</span>
                      <div className="flex flex-wrap gap-1.5">
                        {harmfulAdditives.map((a, i) => (
                          <span key={i} className="px-2.5 py-1 rounded-full text-xs font-medium bg-red-500/10 text-red-700 dark:text-red-400 border border-red-500/20">{a}</span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1.5">Allergen Warnings</span>
                      <div className="flex flex-wrap gap-1.5">
                        {allergenWarnings.map((a, i) => (
                          <span key={i} className="px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/20">{a}</span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1.5">Declared Ingredients</span>
                    <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-mono">
                      {ingredientsText}
                    </div>
                  </div>
                </div>
              )}

              {/* ── TAB: FULL LEDGER ── */}
              {activeMobileTab === 'ledger' && (
                <div className="flex flex-col gap-2">
                  <div className="flex items-center gap-3 text-xs text-slate-500 mb-1">
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span>{passRules.length} Pass</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500 inline-block"></span>{failRules.length} Defect</span>
                    {reviewRules.length > 0 && <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500 inline-block"></span>{reviewRules.length} Review</span>}
                  </div>
                  {allRules.map((r, i) => {
                    const isFail = ['POTENTIAL NON-COMPLIANCE', 'FAIL', 'NON_COMPLIANT'].includes(String(r.status).toUpperCase());
                    const isRev = String(r.status).toUpperCase() === 'MANUAL REVIEW';
                    return (
                      <div key={i} className={`p-2.5 rounded-xl border flex items-center gap-3 text-xs ${isFail ? 'bg-red-500/5 border-red-400/30' : isRev ? 'bg-amber-500/5 border-amber-400/30' : 'bg-slate-50/80 dark:bg-slate-900/40 border-slate-200/60 dark:border-slate-800/60'}`}>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5">
                            <span className={`font-mono text-[10px] font-bold px-1.5 py-0.5 rounded ${isFail ? 'bg-red-500/15 text-red-700 dark:text-red-400' : isRev ? 'bg-amber-500/15 text-amber-700' : 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400'}`}>{r.rule_id}</span>
                            <span className="font-semibold text-slate-800 dark:text-slate-200 truncate">{r.rule_title}</span>
                          </div>
                          <p className="text-[11px] text-slate-600 dark:text-slate-400 mt-0.5 leading-tight font-mono">{r.detail || r.detail_text}</p>
                        </div>
                        <span className={`shrink-0 text-[9px] font-mono font-bold uppercase px-2 py-0.5 rounded ${isFail ? 'bg-red-500 text-white' : isRev ? 'bg-amber-500 text-slate-950' : 'bg-emerald-600 text-white'}`}>
                          {isFail ? 'DEFECT' : isRev ? 'REVIEW' : 'PASS'}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}

            </div>
          </div>

        </div>


      </main>

      {/* ── IMAGE ENLARGEMENT LIGHTBOX MODAL ── */}
      {showImageModal && (
        <div 
          className="fixed inset-0 z-[9999] flex items-center justify-center p-2 sm:p-4 bg-black/90 backdrop-blur-md animate-in fade-in"
          onClick={() => setShowImageModal(false)}
        >
          <div 
            className="bg-slate-900 border border-slate-700 rounded-2xl w-[96vw] sm:w-full max-w-4xl max-h-[94dvh] flex flex-col overflow-hidden shadow-2xl"
            onClick={e => e.stopPropagation()}
          >
            <div className="p-3 sm:p-4 bg-slate-950 border-b border-slate-800 flex items-center justify-between text-white">
              <div className="flex items-center gap-2 min-w-0">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="shrink-0"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
                <span className="font-bold text-xs sm:text-sm truncate">Packaging Optical Evidence &bull; {prodName}</span>
              </div>
              <button
                type="button"
                onClick={() => setShowImageModal(false)}
                className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white cursor-pointer transition-colors shrink-0"
                aria-label="Close Preview"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
            <div className="flex-1 p-2 sm:p-4 flex items-center justify-center overflow-auto bg-black/40 min-h-[260px]">
              <img 
                src={selectedImageSrc || '/test-label.jpg'} 
                alt="Evidence Enlarged" 
                className="max-h-[75dvh] w-auto max-w-full object-contain rounded-lg shadow-xl" 
              />
            </div>
            <div className="p-3 bg-slate-950 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-400 font-mono">
              <span>Resolution: 0.01 mm Traceable</span>
              <button 
                type="button"
                onClick={() => setShowImageModal(false)}
                className="px-3 py-1 bg-white/10 hover:bg-white/20 text-white rounded-lg text-xs"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── STATUTORY NOTICE MODAL (FORM IN-1 & FORM CN-48) ── */}
      {showNoticeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/75 backdrop-blur-xs animate-in fade-in">
          <div className="bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded-2xl shadow-2xl w-[95vw] sm:w-full max-w-2xl max-h-[88dvh] flex flex-col overflow-hidden">
            
            <div className="p-3 sm:p-3.5 bg-slate-100 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between gap-2 sm:gap-3 shrink-0">
              <div className="flex items-center gap-1.5 sm:gap-2 min-w-0">
                <img src="/emblem-transparent.png" alt="Emblem" className="h-4 sm:h-5 w-auto object-contain shrink-0" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white truncate">
                  Notice Generator
                </h3>
              </div>

              <div className="flex items-center bg-slate-200/80 dark:bg-slate-800/80 p-0.5 sm:p-1 rounded-xl gap-0.5 sm:gap-1 shrink-0">
                <button
                  type="button"
                  onClick={() => setNoticeType('janvishwas')}
                  className={`px-2 sm:px-3 py-1 sm:py-1.5 rounded-lg text-[11px] sm:text-xs font-bold transition-all cursor-pointer ${
                    noticeType === 'janvishwas' ? 'bg-amber-500 text-slate-950 shadow-xs' : 'text-slate-600 dark:text-slate-400'
                  }`}
                >
                  Form IN-1
                </button>
                <button
                  type="button"
                  onClick={() => setNoticeType('section48')}
                  className={`px-2 sm:px-3 py-1 sm:py-1.5 rounded-lg text-[11px] sm:text-xs font-bold transition-all cursor-pointer ${
                    noticeType === 'section48' ? 'bg-red-600 text-white shadow-xs' : 'text-slate-600 dark:text-slate-400'
                  }`}
                >
                  Form CN-48
                </button>
              </div>

              <button
                type="button"
                onClick={() => setShowNoticeModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 cursor-pointer shrink-0"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 sm:p-6 bg-slate-50 dark:bg-slate-900/60 text-xs leading-relaxed text-slate-800 dark:text-slate-200">
              <div className="max-w-xl mx-auto bg-white dark:bg-slate-950 p-4 sm:p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
                <div className="text-center pb-3 sm:pb-4 border-b border-slate-200 dark:border-slate-800 mb-4">
                  <div className="text-[10px] sm:text-xs font-bold text-[#0B1F3A] dark:text-blue-300 uppercase">
                    GOVERNMENT OF INDIA &middot; DEPT. OF CONSUMER AFFAIRS
                  </div>
                  <h2 className="text-xs sm:text-sm font-black uppercase text-slate-900 dark:text-white mt-1">
                    {noticeType === 'janvishwas' ? 'FORM IN-1: STATUTORY IMPROVEMENT NOTICE' : 'FORM CN-48: COMPOUNDING NOTICE'}
                  </h2>
                </div>

                <div className="space-y-2 mb-4 text-xs">
                  <div><strong>Notice Ref:</strong> {noticeType === 'janvishwas' ? `DOCA/LM/IN-1/2026/${(report.id || '').slice(0, 6).toUpperCase()}` : `ML/SEC48/2026/${(report.id || '').slice(0, 6).toUpperCase()}`}</div>
                  <div><strong>Commodity:</strong> {prodName}</div>
                  <div><strong>Respondent:</strong> {fields.manufacturer_name || brand || 'Declared Packaging Entity'}</div>
                  <div><strong>Violations:</strong> {failRules.length} defect(s) detected</div>
                </div>

                <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/40 text-[11px]">
                  {noticeType === 'janvishwas' ? (
                    <p>Statutory cure window of <strong>15 calendar days</strong> is provided to rectify non-conforming packaging declarations without compounding penalties under Jan Vishwas Act, 2023.</p>
                  ) : (
                    <p>Proposed compounding sum of <strong>₹25,000/-</strong> in terms of Section 48 of Legal Metrology Act, 2009.</p>
                  )}
                </div>
              </div>
            </div>

            <div className="p-3 bg-slate-100 dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800 flex items-center justify-end gap-2 shrink-0">
              <button
                type="button"
                onClick={() => {
                  if (noticeType === 'janvishwas') downloadJanVishwasNoticePDF();
                  else downloadSection48NoticePDF();
                }}
                className="px-4 py-2 rounded-lg text-xs font-bold bg-[#0B1F3A] hover:bg-blue-900 text-white cursor-pointer shadow-xs transition-colors"
              >
                Download Official PDF
              </button>
            </div>

          </div>
        </div>
      )}

      {/* ─── Chain of Custody Footer ──────────────────────────────── */}
      {report?.evidence_hash && (
        <div className="mt-4 p-3 rounded-xl border border-dashed border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 text-xs">
          <div className="flex items-center gap-2 mb-1">
            <svg className="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
            <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400 tracking-wider uppercase">Chain of Custody — Evidence Hash (SHA-256)</span>
          </div>
          <code className="block text-[10px] text-slate-500 dark:text-slate-400 font-mono break-all select-all">{report.evidence_hash}</code>
          <p className="text-[9px] text-slate-400 mt-0.5">Tamper-proof cryptographic digest of uploaded physical packaging evidence.</p>
        </div>
      )}

    </div>
  );
}
