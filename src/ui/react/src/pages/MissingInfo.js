import React, { useState } from 'react';
import { useApp } from '../AppContext';
import CandidateSelector from '../components/CandidateSelector';
import { AlertCircle, Mail, Copy, CheckCircle } from 'lucide-react';

function detectMissingFields(c) {
  const missing = [];
  if (!c?.email) missing.push({ field: 'Email address', section: 'Personal Info', severity: 'high' });
  if (!c?.phone) missing.push({ field: 'Phone number',  section: 'Personal Info', severity: 'high' });

  (c?.education || []).forEach(e => {
    if (!e.grade_value) missing.push({ field: `Grade for ${e.degree_level}`,      section: 'Education', severity: 'medium' });
    if (!e.start_year)  missing.push({ field: `Start year for ${e.degree_level}`,  section: 'Education', severity: 'low' });
    if (!e.institution && !e.board)
      missing.push({ field: `Institution for ${e.degree_level}`, section: 'Education', severity: 'medium' });
  });

  (c?.experience || []).forEach(e => {
    if (!e.start_date) missing.push({ field: `Start date — "${e.job_title}"`, section: 'Experience', severity: 'medium' });
    if (!e.end_date && !e.is_current)
      missing.push({ field: `End date — "${e.job_title}"`, section: 'Experience', severity: 'medium' });
  });

  (c?.journal_publications || []).forEach(p => {
    if (!p.issn)     missing.push({ field: `ISSN — "${(p.title||'').slice(0,40)}…"`,     section: 'Publications', severity: 'low' });
    if (!p.quartile) missing.push({ field: `Quartile — "${(p.title||'').slice(0,40)}…"`, section: 'Publications', severity: 'low' });
  });

  return missing;
}

function generateEmail(candidate, missing) {
  const name     = candidate?.full_name || 'Candidate';
  const lastName = name.split(' ').pop();
  const grouped  = {};
  missing.forEach(m => { grouped[m.section] = grouped[m.section] || []; grouped[m.section].push(m.field); });
  const lines = Object.entries(grouped)
    .map(([section, fields]) => `  ${section}:\n${fields.map(f => `    • ${f}`).join('\n')}`)
    .join('\n\n');

  return `Subject: Application Follow-Up — Additional Information Required

Dear ${lastName},

Thank you for submitting your application. We have reviewed your profile and found the following information is missing or incomplete:

${lines}

Kindly provide an updated CV addressing the above points at your earliest convenience.

Best regards,
TALASH Recruitment Team
NUST SEECS`;
}

const SEVERITY_ORDER = { high: 0, medium: 1, low: 2 };
const SEVERITY_BADGE = { high: 'badge-red', medium: 'badge-amber', low: 'badge-teal' };

export default function MissingInfoPage() {
  const { candidates, selectedCandidate: c, setSelectedId } = useApp();
  const [copied, setCopied]   = useState(false);
  const [viewAll, setViewAll] = useState(false);

  const missing    = c ? detectMissingFields(c) : [];
  const emailDraft = c && missing.length ? generateEmail(c, missing) : '';
  const sortedMissing = [...missing].sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]);

  const copyEmail = () => {
    navigator.clipboard.writeText(emailDraft);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const allSummary = candidates
    .map(cand => ({ candidate: cand, count: detectMissingFields(cand).length }))
    .filter(x => x.count > 0)
    .sort((a, b) => b.count - a.count);

  return (
    <div className="fade-up">
      <div className="page-header">
        <h1>Missing Information</h1>
        <p className="subtitle">Detected gaps in candidate profiles with auto-generated follow-up emails</p>
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div className="card-title">Candidates with missing info</div>
          <button className="btn btn-ghost" style={{ fontSize: 12, padding: '4px 10px' }}
            onClick={() => setViewAll(v => !v)}>
            {viewAll ? 'Show fewer' : 'Show all'}
          </button>
        </div>
        {allSummary.length === 0 ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--green)', fontSize: 13 }}>
            <CheckCircle size={15} /> All candidates have complete profiles.
          </div>
        ) : (
          <table className="data-table">
            <thead><tr><th>Candidate</th><th>Missing Fields</th><th>Action</th></tr></thead>
            <tbody>
              {(viewAll ? allSummary : allSummary.slice(0, 5)).map(({ candidate, count }) => (
                <tr key={candidate.candidate_id}>
                  <td style={{ fontWeight: 500 }}>{candidate.full_name}</td>
                  <td><span className="badge badge-amber">{count} field{count !== 1 ? 's' : ''}</span></td>
                  <td>
                    <button className="btn btn-ghost" style={{ fontSize: 12, padding: '4px 10px' }}
                      onClick={() => setSelectedId(candidate.candidate_id)}>
                      View details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <CandidateSelector label="Generate email for:" />

      {!c ? null : missing.length === 0 ? (
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--green)', fontSize: 13 }}>
            <CheckCircle size={15} /> No missing fields detected for {c.full_name}.
          </div>
        </div>
      ) : (
        <div className="grid-2" style={{ gap: 20 }}>
          <div className="card">
            <div className="card-title">Missing fields ({missing.length})</div>
            {sortedMissing.map((m, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'flex-start', gap: 10,
                padding: '9px 0', borderBottom: '1px solid var(--border)'
              }}>
                <AlertCircle size={13}
                  color={m.severity === 'high' ? 'var(--red)' : m.severity === 'medium' ? 'var(--amber)' : 'var(--teal)'}
                  style={{ marginTop: 2, flexShrink: 0 }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13 }}>{m.field}</div>
                  <div style={{ fontSize: 11.5, color: 'var(--text3)', marginTop: 2 }}>{m.section}</div>
                </div>
                <span className={`badge ${SEVERITY_BADGE[m.severity]}`}>{m.severity}</span>
              </div>
            ))}
          </div>

          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <div className="card-title" style={{ marginBottom: 0 }}>
                <Mail size={13} style={{ display: 'inline', marginRight: 6 }} />
                Draft email
              </div>
              <button className="btn btn-ghost" style={{ fontSize: 12, padding: '5px 12px' }} onClick={copyEmail}>
                {copied ? <><CheckCircle size={12} /> Copied!</> : <><Copy size={12} /> Copy</>}
              </button>
            </div>
            <div className="email-draft">{emailDraft}</div>
          </div>
        </div>
      )}
    </div>
  );
}