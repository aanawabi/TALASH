import React from 'react';
import { useApp } from '../AppContext';
import CandidateSelector from '../components/CandidateSelector';
import { FileText, GraduationCap, Briefcase, FlaskConical, Star } from 'lucide-react';

function ScoreBar({ label, score, max = 100, color = 'var(--accent)' }) {
  const pct = Math.min((score / max) * 100, 100);
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
        <span style={{ fontSize: 12.5, color: 'var(--text2)' }}>{label}</span>
        <span style={{ fontSize: 12.5, fontFamily: 'var(--font-mono)', color }}>{score}/{max}</span>
      </div>
      <div className="progress-bar" style={{ height: 6 }}>
        <div className="progress-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

function computeScores(c) {
  if (!c) return null;
  const edu = c.education || [];
  const exp = c.experience || [];
  const pubs = (c.journal_publications || []).length + (c.conference_publications || []).length;

  const hasPhD = edu.some(e => e.degree_level === 'PhD');
  const hasMS  = edu.some(e => e.degree_level?.includes('Master'));
  const eduScore = Math.min(
    (hasPhD ? 40 : hasMS ? 25 : 10) +
    edu.filter(e => e.grade_value).length * 8,
    40
  );

  const expYears = exp.reduce((s, e) => {
    const start = e.start_date ? new Date(e.start_date) : null;
    const end   = e.is_current ? new Date() : (e.end_date ? new Date(e.end_date) : null);
    if (start && end) s += (end - start) / (1000 * 60 * 60 * 24 * 365);
    return s;
  }, 0);
  const expScore = Math.min(Math.round(expYears * 3), 30);

  const researchScore = Math.min(pubs * 5, 30);

  const total = eduScore + expScore + researchScore;

  return { eduScore, expScore, researchScore, total, expYears: Math.round(expYears * 10) / 10 };
}

export default function SummaryPage() {
  const { selectedCandidate: c } = useApp();
  const scores = computeScores(c);

  const topDeg = c?.education?.find(e => e.degree_level === 'PhD') ||
                 c?.education?.find(e => e.degree_level?.includes('Master')) ||
                 c?.education?.[0];

  const currentJob = c?.experience?.find(e => e.is_current);
  const pubs = (c?.journal_publications?.length || 0) + (c?.conference_publications?.length || 0);

  const strengthLevel = scores?.total >= 70 ? { label: 'Strong', color: 'var(--green)', badge: 'badge-green' }
    : scores?.total >= 45 ? { label: 'Moderate', color: 'var(--amber)', badge: 'badge-amber' }
    : { label: 'Weak', color: 'var(--red)', badge: 'badge-red' };

  return (
    <div className="fade-up">
      <div className="page-header">
        <h1>Candidate Summary</h1>
        <p className="subtitle">Overall profile assessment and suitability interpretation</p>
      </div>

      <CandidateSelector />

      {!c ? (
        <div className="card">
          <div className="empty-state">
            <FileText size={32} />
            <h3>Select a candidate</h3>
            <p>Choose a candidate above to view their summary</p>
          </div>
        </div>
      ) : (
        <>
          {/* Candidate header */}
          <div className="cand-header" style={{ marginBottom: 20 }}>
            <div className="cand-avatar">
              {(c.full_name || '?').split(' ').slice(0,2).map(w=>w[0]).join('')}
            </div>
            <div style={{ flex: 1 }}>
              <div className="cand-name">{c.full_name}</div>
              <div className="cand-meta">
                {topDeg?.degree_level} · {currentJob ? currentJob.job_title + ' at ' + currentJob.organization : 'No current role on record'}
              </div>
            </div>
            <span className={`badge ${strengthLevel.badge}`} style={{ fontSize: 13, padding: '6px 14px' }}>
              <Star size={12} /> {strengthLevel.label} Profile
            </span>
          </div>

          <div className="grid-2" style={{ gap: 20, marginBottom: 20 }}>
            {/* Score breakdown */}
            <div className="card">
              <div className="card-title">Profile scores</div>
              <div style={{ textAlign: 'center', marginBottom: 20 }}>
                <div style={{
                  width: 90, height: 90, borderRadius: '50%',
                  border: `3px solid ${strengthLevel.color}`,
                  display: 'flex', flexDirection: 'column',
                  alignItems: 'center', justifyContent: 'center',
                  margin: '0 auto',
                }}>
                  <div style={{ fontFamily: 'var(--font-head)', fontSize: 26, fontWeight: 700, color: strengthLevel.color }}>
                    {scores.total}
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--text3)', fontFamily: 'var(--font-mono)' }}>/ 100</div>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text3)', marginTop: 8 }}>Overall score</div>
              </div>
              <ScoreBar label="Education" score={scores.eduScore} max={40} color="var(--teal)" />
              <ScoreBar label="Experience" score={scores.expScore} max={30} color="var(--accent)" />
              <ScoreBar label="Research" score={scores.researchScore} max={30} color="var(--accent2)" />
            </div>

            {/* Key facts */}
            <div className="card">
              <div className="card-title">Key profile facts</div>
              {[
                { icon: GraduationCap, label: 'Highest Degree',   value: topDeg ? `${topDeg.degree_title} (${topDeg.end_year || '?'})` : '—', color: 'var(--teal)' },
                { icon: GraduationCap, label: 'Institution',      value: topDeg?.institution || '—', color: 'var(--teal)' },
                { icon: Briefcase,     label: 'Total Experience', value: `${scores.expYears} years`, color: 'var(--accent)' },
                { icon: Briefcase,     label: 'Current Role',     value: currentJob ? `${currentJob.job_title}, ${currentJob.organization}` : 'Not specified', color: 'var(--accent)' },
                { icon: FlaskConical,  label: 'Total Publications', value: pubs, color: 'var(--accent2)' },
                { icon: FlaskConical,  label: 'Journal Papers',   value: c.journal_publications?.length || 0, color: 'var(--accent2)' },
              ].map((row, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '9px 0', borderBottom: '1px solid var(--border)'
                }}>
                  <row.icon size={14} color={row.color} style={{ flexShrink: 0 }} />
                  <span style={{ fontSize: 12.5, color: 'var(--text3)', width: 130, flexShrink: 0 }}>{row.label}</span>
                  <span style={{ fontSize: 13, fontWeight: 500 }}>{row.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Narrative summary */}
          <div className="card">
            <div className="card-title">Profile narrative</div>
            <div style={{ fontSize: 13.5, lineHeight: 1.8, color: 'var(--text2)' }}>
              <p>
                <strong style={{ color: 'var(--text)' }}>{c.full_name}</strong> holds a{' '}
                <strong style={{ color: 'var(--text)' }}>{topDeg?.degree_title || 'degree'}</strong>
                {topDeg?.institution ? ` from ${topDeg.institution}` : ''}.{' '}
                {scores.expYears > 0
                  ? `They have approximately ${scores.expYears} years of professional experience`
                  : 'No professional experience is recorded'
                }
                {currentJob ? `, currently serving as ${currentJob.job_title} at ${currentJob.organization}.` : '.'}
              </p>
              <p style={{ marginTop: 12 }}>
                Their research portfolio includes{' '}
                <strong style={{ color: 'var(--text)' }}>{pubs} publication{pubs !== 1 ? 's' : ''}</strong>
                {c.journal_publications?.length ? `, of which ${c.journal_publications.length} appeared in journals` : ''}.
                {c.journal_publications?.some(p => p.impact_factor)
                  ? ` The average impact factor across indexed journals is ${(c.journal_publications.filter(p=>p.impact_factor).reduce((s,p)=>s+parseFloat(p.impact_factor),0)/c.journal_publications.filter(p=>p.impact_factor).length).toFixed(2)}.`
                  : ''}
              </p>
              <p style={{ marginTop: 12 }}>
                Overall, this candidate presents a{' '}
                <strong style={{ color: strengthLevel.color }}>{strengthLevel.label.toLowerCase()}</strong> profile
                with a composite score of <strong style={{ color: strengthLevel.color }}>{scores.total}/100</strong>.
                {scores.total >= 70
                  ? ' The profile demonstrates solid academic credentials, sustained professional engagement, and measurable research output.'
                  : scores.total >= 45
                  ? ' The profile shows adequate qualifications with some areas that may benefit from further clarification or documentation.'
                  : ' The profile has limited documented credentials and may require additional verification before proceeding.'}
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}