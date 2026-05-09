import React, { useState, useEffect } from 'react';
import { useApp } from '../AppContext';
import CandidateSelector from '../components/CandidateSelector';
import { getCandidateEmails } from '../api';
import { AlertCircle, Mail, Copy, CheckCircle, Inbox } from 'lucide-react';

// ── Helpers ──────────────────────────────────────────────────────────────────

function Spinner() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '40px 0', color: 'var(--text3)', fontSize: 13 }}>
      <div style={{ width: 18, height: 18, border: '2px solid var(--border2)', borderTopColor: 'var(--accent)', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
      Detecting missing information…
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function MissingInfoPage() {
  const { selectedCandidate: c } = useApp();
  const [emailData, setEmailData]     = useState(null);
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState(null);
  const [activeEmail, setActiveEmail] = useState('contact');
  const [copied, setCopied]           = useState(false);

  useEffect(() => {
    if (!c?.candidate_id) { setEmailData(null); return; }
    setLoading(true);
    setError(null);
    getCandidateEmails(c.candidate_id)
      .then(data => { setEmailData(data); setActiveEmail(Object.keys(data.draft_emails || {})[0] || 'contact'); setLoading(false); })
      .catch(e  => { setError(e.message); setLoading(false); });
  }, [c?.candidate_id]);

  const missing      = emailData?.all_missing      || [];
  const drafts       = emailData?.draft_emails     || {};
  const hasMissing   = emailData?.has_missing_info ?? false;
  const totalMissing = emailData?.total_missing_fields ?? 0;
  const draftKeys    = Object.keys(drafts);

  const copyEmail = () => {
    const text = drafts[activeEmail] || drafts[draftKeys[0]] || '';
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fade-up">
      <div className="page-header">
        <h1>Missing Information</h1>
        <p className="subtitle">Detected gaps in candidate profiles with auto-generated follow-up emails</p>
      </div>

      <CandidateSelector />

      {!c ? (
        <div className="card">
          <div className="empty-state">
            <Inbox size={32} />
            <h3>Select a candidate</h3>
            <p>Choose a candidate above to detect missing information and generate draft emails</p>
          </div>
        </div>
      ) : loading ? (
        <div className="card"><Spinner /></div>
      ) : error ? (
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--red)' }}>
          <AlertCircle size={18} /><span style={{ fontSize: 13 }}>{error}</span>
        </div>
      ) : !hasMissing ? (
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--green)', fontSize: 13 }}>
            <CheckCircle size={15} /> No missing fields detected for <strong style={{ marginLeft: 4 }}>{c.full_name}</strong>. Profile appears complete.
          </div>
        </div>
      ) : (
        <>
          {/* ── Stats row ─────────────────────────────────────────────────── */}
          <div className="stat-grid" style={{ marginBottom: 20 }}>
            {[
              { label: 'Missing Fields',  value: totalMissing,          color: 'var(--red)'    },
              { label: 'Draft Emails',    value: draftKeys.length,      color: 'var(--accent)' },
              { label: 'Status',          value: 'Action Required',     color: 'var(--amber)'  },
            ].map(s => (
              <div key={s.label} className="stat-card" style={{ '--accent-color': s.color }}>
                <div className="stat-label">{s.label}</div>
                <div className="stat-value" style={{ fontSize: typeof s.value === 'string' ? 14 : undefined }}>{s.value}</div>
              </div>
            ))}
          </div>

          {/* ── Missing fields + Draft email ──────────────────────────────── */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>

            {/* Missing fields list */}
            <div className="card">
              <div className="card-title">
                <AlertCircle size={13} style={{ display: 'inline', marginRight: 6 }} />
                Missing fields ({totalMissing})
              </div>
              {missing.length === 0 ? (
                <div style={{ color: 'var(--text3)', fontSize: 13 }}>No field details returned by analyzer.</div>
              ) : (
                missing.map((field, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'flex-start', gap: 10,
                    padding: '9px 0', borderBottom: '1px solid var(--border)',
                  }}>
                    <AlertCircle size={13} color="var(--amber)" style={{ marginTop: 2, flexShrink: 0 }} />
                    <span style={{ fontSize: 13 }}>{field}</span>
                  </div>
                ))
              )}
            </div>

            {/* Email draft */}
            <div className="card">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                <div className="card-title" style={{ margin: 0 }}>
                  <Mail size={13} style={{ display: 'inline', marginRight: 6 }} />
                  Draft emails
                </div>
                <button className="btn btn-ghost" style={{ fontSize: 12, padding: '5px 12px' }} onClick={copyEmail}>
                  {copied
                    ? <><CheckCircle size={12} /> Copied!</>
                    : <><Copy size={12} /> Copy</>}
                </button>
              </div>

              {/* Tab switcher if multiple email types */}
              {draftKeys.length > 1 && (
                <div className="tab-bar" style={{ marginBottom: 12 }}>
                  {draftKeys.map(key => (
                    <button key={key}
                      className={`tab-btn${activeEmail === key ? ' active' : ''}`}
                      onClick={() => { setActiveEmail(key); setCopied(false); }}>
                      {key.charAt(0).toUpperCase() + key.slice(1)}
                    </button>
                  ))}
                </div>
              )}

              <div className="email-draft">
                {drafts[activeEmail] || drafts[draftKeys[0]] || 'No draft available.'}
              </div>
            </div>
          </div>
        </>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
