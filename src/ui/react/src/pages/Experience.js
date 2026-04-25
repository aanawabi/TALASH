import React from 'react';
import { useApp } from '../AppContext';
import CandidateSelector from '../components/CandidateSelector';
import { Briefcase, AlertTriangle, CheckCircle } from 'lucide-react';

function parseDateStr(s) {
  if (!s || s === 'Present') return null;
  const [y, m] = s.split('-');
  return new Date(parseInt(y), parseInt(m || 1) - 1);
}

function monthsBetween(start, end) {
  if (!start) return 0;
  const e = end || new Date();
  return (e.getFullYear() - start.getFullYear()) * 12 + (e.getMonth() - start.getMonth());
}

function formatMonths(m) {
  if (m >= 12) return `${Math.round(m / 12 * 10) / 10} yr${m >= 24 ? 's' : ''}`;
  return `${m} mo${m !== 1 ? 's' : ''}`;
}

function detectGaps(experience) {
  const sorted = [...experience].filter(e => e.start_date)
    .sort((a, b) => new Date(a.start_date) - new Date(b.start_date));
  const gaps = [];
  for (let i = 1; i < sorted.length; i++) {
    const prevEnd   = sorted[i-1].is_current ? null : parseDateStr(sorted[i-1].end_date);
    const nextStart = parseDateStr(sorted[i].start_date);
    if (prevEnd && nextStart) {
      const gapMonths = monthsBetween(prevEnd, nextStart);
      if (gapMonths > 3) gaps.push({ months: gapMonths, between: [sorted[i-1].job_title, sorted[i].job_title] });
    }
  }
  return gaps;
}

function detectOverlaps(experience) {
  const overlaps = [];
  for (let i = 0; i < experience.length; i++) {
    for (let j = i + 1; j < experience.length; j++) {
      const aStart = parseDateStr(experience[i].start_date);
      const aEnd   = experience[i].is_current ? new Date() : parseDateStr(experience[i].end_date);
      const bStart = parseDateStr(experience[j].start_date);
      const bEnd   = experience[j].is_current ? new Date() : parseDateStr(experience[j].end_date);
      if (aStart && aEnd && bStart && bEnd && aStart < bEnd && bStart < aEnd)
        overlaps.push({ a: experience[i].job_title, b: experience[j].job_title });
    }
  }
  return overlaps;
}

const JOB_COLORS = ['var(--accent)', 'var(--teal)', 'var(--accent2)', 'var(--green)', 'var(--amber)'];

export default function ExperiencePage() {
  const { selectedCandidate: c } = useApp();
  const exp = c?.experience || [];
  const sorted = [...exp].sort((a, b) => new Date(a.start_date || 0) - new Date(b.start_date || 0));
  const gaps     = exp.length ? detectGaps(sorted)    : [];
  const overlaps = exp.length ? detectOverlaps(sorted) : [];
  const totalMonths = exp.reduce((sum, e) =>
    sum + monthsBetween(parseDateStr(e.start_date), e.is_current ? new Date() : parseDateStr(e.end_date)), 0);
  const currentJob = exp.find(e => e.is_current);

  return (
    <div className="fade-up">
      <div className="page-header">
        <h1>Experience Analysis</h1>
        <p className="subtitle">Employment timeline, tenure, career progression and gap detection</p>
      </div>

      <CandidateSelector />

      {!c ? (
        <div className="card">
          <div className="empty-state">
            <Briefcase size={32} />
            <h3>Select a candidate</h3>
            <p>Choose a candidate above to view their experience analysis</p>
          </div>
        </div>
      ) : (
        <>
          <div className="grid-4" style={{ marginBottom: 20 }}>
            {[
              { label: 'Total Experience',   value: formatMonths(totalMonths), color: 'var(--accent)' },
              { label: 'Roles on Record',    value: exp.length,                color: 'var(--teal)' },
              { label: 'Employment Gaps',    value: gaps.length,               color: gaps.length ? 'var(--amber)' : 'var(--green)' },
              { label: 'Overlapping Roles',  value: overlaps.length,           color: overlaps.length ? 'var(--red)' : 'var(--green)' },
            ].map(s => (
              <div key={s.label} className="stat-card" style={{ '--accent-color': s.color }}>
                <div className="stat-label">{s.label}</div>
                <div className="stat-value" style={{ fontSize: 22 }}>{s.value}</div>
              </div>
            ))}
          </div>

          {currentJob && (
            <div style={{
              padding: '12px 18px', marginBottom: 20,
              background: 'rgba(34,201,122,0.06)', border: '1px solid rgba(34,201,122,0.2)',
              borderRadius: 'var(--radius)', display: 'flex', alignItems: 'center', gap: 10
            }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--green)', display: 'inline-block' }} />
              <span style={{ fontSize: 13 }}>
                Currently: <strong>{currentJob.job_title}</strong> at {currentJob.organization}
                {currentJob.location && <span style={{ color: 'var(--text3)' }}> · {currentJob.location}</span>}
              </span>
            </div>
          )}

          <div className="grid-2" style={{ gap: 20, marginBottom: 20 }}>
            <div className="card">
              <div className="card-title">Career timeline</div>
              <div className="timeline">
                {sorted.map((e, i) => {
                  const start  = parseDateStr(e.start_date);
                  const end    = e.is_current ? new Date() : parseDateStr(e.end_date);
                  const tenure = monthsBetween(start, end);
                  const color  = JOB_COLORS[i % JOB_COLORS.length];
                  return (
                    <div key={i} className="timeline-item">
                      <div className="timeline-dot" style={{ background: color }} />
                      <div>
                        <div style={{ fontWeight: 500, fontSize: 13.5 }}>{e.job_title}</div>
                        <div style={{ fontSize: 12, color: 'var(--text2)', margin: '2px 0' }}>{e.organization}</div>
                        {e.location && <div style={{ fontSize: 11.5, color: 'var(--text3)' }}>{e.location}</div>}
                        <div style={{ display: 'flex', gap: 6, marginTop: 6, flexWrap: 'wrap' }}>
                          <span className="badge badge-blue">{e.start_date || '?'} → {e.is_current ? 'Present' : e.end_date || '?'}</span>
                          {tenure > 0 && <span className="badge badge-teal">{formatMonths(tenure)}</span>}
                          {e.is_current && <span className="badge badge-green">Current</span>}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="card">
              <div className="card-title">Tenure by role</div>
              {sorted.map((e, i) => {
                const start  = parseDateStr(e.start_date);
                const end    = e.is_current ? new Date() : parseDateStr(e.end_date);
                const months = monthsBetween(start, end);
                const pct    = Math.min((months / 120) * 100, 100);
                const color  = JOB_COLORS[i % JOB_COLORS.length];
                return (
                  <div key={i} style={{ marginBottom: 14 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                      <span style={{ fontSize: 12.5, color: 'var(--text2)' }}>{e.job_title}</span>
                      <span style={{ fontSize: 12.5, fontFamily: 'var(--font-mono)', color }}>{formatMonths(months)}</span>
                    </div>
                    <div className="progress-bar" style={{ height: 5 }}>
                      <div className="progress-fill" style={{ width: `${pct}%`, background: color }} />
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text3)', marginTop: 2 }}>{e.organization}</div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="card" style={{ marginBottom: 20 }}>
            <div className="card-title">Timeline flags</div>
            {gaps.length === 0 && overlaps.length === 0 ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--green)', fontSize: 13 }}>
                <CheckCircle size={15} /> No gaps or overlaps detected.
              </div>
            ) : (
              <>
                {gaps.map((g, i) => (
                  <div key={`g${i}`} style={{
                    display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px',
                    background: 'rgba(245,166,35,0.06)', border: '1px solid rgba(245,166,35,0.2)',
                    borderRadius: 'var(--radius)', marginBottom: 8, fontSize: 13
                  }}>
                    <AlertTriangle size={14} color="var(--amber)" />
                    <span style={{ color: 'var(--text2)' }}>
                      <strong style={{ color: 'var(--text)' }}>{formatMonths(g.months)} gap</strong> between <em>{g.between[0]}</em> and <em>{g.between[1]}</em>
                    </span>
                    <span className="badge badge-amber" style={{ marginLeft: 'auto' }}>Gap</span>
                  </div>
                ))}
                {overlaps.map((o, i) => (
                  <div key={`o${i}`} style={{
                    display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px',
                    background: 'rgba(240,82,82,0.06)', border: '1px solid rgba(240,82,82,0.2)',
                    borderRadius: 'var(--radius)', marginBottom: 8, fontSize: 13
                  }}>
                    <AlertTriangle size={14} color="var(--red)" />
                    <span style={{ color: 'var(--text2)' }}>
                      <strong style={{ color: 'var(--text)' }}>Overlapping roles:</strong> <em>{o.a}</em> and <em>{o.b}</em>
                    </span>
                    <span className="badge badge-red" style={{ marginLeft: 'auto' }}>Overlap</span>
                  </div>
                ))}
              </>
            )}
          </div>

          <div className="section-divider"><span>All experience records</span></div>
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <table className="data-table">
              <thead>
                <tr><th>Title</th><th>Organization</th><th>Location</th><th>From</th><th>To</th><th>Status</th></tr>
              </thead>
              <tbody>
                {sorted.map((e, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 500 }}>{e.job_title}</td>
                    <td className="text-muted">{e.organization}</td>
                    <td className="text-muted">{e.location || '—'}</td>
                    <td className="text-mono">{e.start_date || '—'}</td>
                    <td className="text-mono">{e.is_current ? 'Present' : e.end_date || '—'}</td>
                    <td>{e.is_current ? <span className="badge badge-green">Current</span> : <span className="badge badge-teal">Past</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}