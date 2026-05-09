import React, { useState, useEffect } from 'react';
import { useApp } from '../AppContext';
import CandidateSelector from '../components/CandidateSelector';
import { analyzeCandidate } from '../api';
import {
  Briefcase, AlertTriangle, CheckCircle, TrendingUp,
  AlertCircle, ArrowUpRight, Minus, ArrowDownRight,
} from 'lucide-react';

// ── Helpers ──────────────────────────────────────────────────────────────────

function Spinner() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '40px 0', color: 'var(--text3)', fontSize: 13 }}>
      <div style={{ width: 18, height: 18, border: '2px solid var(--border2)', borderTopColor: 'var(--accent)', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
      Running analysis…
    </div>
  );
}

const JOB_COLORS = ['var(--accent)', 'var(--teal)', 'var(--accent2)', 'var(--green)', 'var(--amber)'];

const TRAJECTORY_META = {
  ascending:   { icon: ArrowUpRight,   color: 'var(--green)',   label: 'Ascending' },
  lateral:     { icon: Minus,          color: 'var(--amber)',   label: 'Lateral'   },
  descending:  { icon: ArrowDownRight, color: 'var(--red)',     label: 'Descending'},
  no_experience:{ icon: Minus,         color: 'var(--text3)',   label: 'No Data'   },
  single_position:{ icon: Minus,       color: 'var(--teal)',    label: 'Single Role'},
};

function GapCard({ gap, index }) {
  const severity = gap.severity || 'minor';
  const color = { minor: 'var(--teal)', moderate: 'var(--amber)', significant: 'var(--red)' }[severity] || 'var(--amber)';
  const bg    = { minor: 'rgba(20,184,166,0.06)', moderate: 'rgba(245,166,35,0.06)', significant: 'rgba(240,82,82,0.06)' }[severity];
  const border= { minor: 'rgba(20,184,166,0.2)',  moderate: 'rgba(245,166,35,0.2)',  significant: 'rgba(240,82,82,0.2)'  }[severity];
  return (
    <div style={{ padding: '12px 14px', background: bg, border: `1px solid ${border}`, borderRadius: 'var(--radius)', marginBottom: 8 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <AlertTriangle size={13} color={color} />
        <span style={{ fontSize: 12.5, fontWeight: 600, color }}>
          {gap.gap_months} month gap ({gap.severity})
        </span>
        <span className="badge" style={{ marginLeft: 'auto', background: `${color}18`, color, border: `1px solid ${color}40`, fontSize: 11 }}>
          {gap.gap_start} → {gap.gap_end}
        </span>
      </div>
      <div style={{ fontSize: 12, color: 'var(--text3)', marginBottom: 4 }}>
        {gap.after_role} &nbsp;→&nbsp; {gap.before_role}
      </div>
      <div style={{ fontSize: 12, color: gap.is_explained ? 'var(--green)' : 'var(--amber)' }}>
        {gap.is_explained ? '✓' : '⚠'} {gap.justification}
      </div>
    </div>
  );
}

function OverlapCard({ overlap }) {
  const flagColor = {
    suspicious:        'var(--red)',
    likely_legitimate: 'var(--green)',
    transitional:      'var(--teal)',
  }[overlap.flag] || 'var(--amber)';
  const flagBg = {
    suspicious:        'rgba(240,82,82,0.06)',
    likely_legitimate: 'rgba(34,201,122,0.06)',
    transitional:      'rgba(20,184,166,0.06)',
  }[overlap.flag] || 'rgba(245,166,35,0.06)';
  return (
    <div style={{ padding: '12px 14px', background: flagBg, border: `1px solid ${flagColor}30`, borderRadius: 'var(--radius)', marginBottom: 8 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <AlertTriangle size={13} color={flagColor} />
        <span className="badge" style={{ background: `${flagColor}18`, color: flagColor, border: `1px solid ${flagColor}40`, fontSize: 11 }}>
          {overlap.flag?.replace('_', ' ')}
        </span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text3)', marginLeft: 'auto' }}>
          {overlap.overlap_months} mo overlap
        </span>
      </div>
      <div style={{ fontSize: 12, color: 'var(--text2)', marginBottom: 4 }}>
        {overlap.role_a} &nbsp;↔&nbsp; {overlap.role_b}
      </div>
      <div style={{ fontSize: 12, color: 'var(--text3)' }}>{overlap.interpretation}</div>
    </div>
  );
}

function EduOverlapCard({ overlap }) {
  const legit = overlap.is_likely_legitimate;
  return (
    <div style={{
      padding: '12px 14px',
      background: legit ? 'rgba(34,201,122,0.06)' : 'rgba(245,166,35,0.06)',
      border: `1px solid ${legit ? 'rgba(34,201,122,0.2)' : 'rgba(245,166,35,0.2)'}`,
      borderRadius: 'var(--radius)', marginBottom: 8,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        {legit ? <CheckCircle size={13} color="var(--green)" /> : <AlertTriangle size={13} color="var(--amber)" />}
        <span style={{ fontSize: 12.5, fontWeight: 500, color: legit ? 'var(--green)' : 'var(--amber)' }}>
          Edu–Employment overlap · {overlap.overlap_months} mo
        </span>
      </div>
      <div style={{ fontSize: 12, color: 'var(--text2)', marginBottom: 4 }}>
        <strong>{overlap.job_title}</strong> @ {overlap.organization} during <em>{overlap.degree_level}</em>
      </div>
      <div style={{ fontSize: 12, color: 'var(--text3)' }}>{overlap.interpretation}</div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function ExperiencePage() {
  const { selectedCandidate: c } = useApp();
  const [analysis, setAnalysis]  = useState(null);
  const [loading, setLoading]    = useState(false);
  const [error, setError]        = useState(null);
  const [tab, setTab]            = useState('timeline');

  useEffect(() => {
    if (!c?.candidate_id) { setAnalysis(null); return; }
    setLoading(true);
    setError(null);
    analyzeCandidate(c.candidate_id)
      .then(data => { setAnalysis(data); setLoading(false); })
      .catch(e  => { setError(e.message); setLoading(false); });
  }, [c?.candidate_id]);

  const exp = analysis?.exp_analysis || {};
  const roles       = exp.role_details           || [];
  const jobOverlaps = exp.job_overlaps           || [];
  const eduOverlaps = exp.edu_employment_overlaps|| [];
  const gaps        = exp.employment_gaps        || [];

  const tMeta = TRAJECTORY_META[exp.career_trajectory] || TRAJECTORY_META.no_experience;
  const TIcon = tMeta.icon;

  const maxDuration = Math.max(...roles.map(r => r.duration_years || 0), 1);

  const TABS = [
    { id: 'timeline',    label: 'Career Timeline' },
    { id: 'progression', label: 'Career Progression' },
    { id: 'flags',       label: `Timeline Flags (${gaps.length + jobOverlaps.length + eduOverlaps.length})` },
    { id: 'records',     label: 'All Records' },
  ];

  return (
    <div className="fade-up">
      <div className="page-header">
        <h1>Experience Analysis</h1>
        <p className="subtitle">
          Employment timeline · career progression · overlap detection · gap justification
        </p>
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
      ) : loading ? (
        <div className="card"><Spinner /></div>
      ) : error ? (
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--red)' }}>
          <AlertCircle size={18} /><span style={{ fontSize: 13 }}>{error}</span>
        </div>
      ) : (
        <>
          {/* ── Stats row ─────────────────────────────────────────────────── */}
          <div className="stat-grid" style={{ marginBottom: 20 }}>
            {[
              { label: 'Total Experience',     value: exp.total_years_experience != null ? `${exp.total_years_experience} yrs` : '—', color: 'var(--accent)' },
              { label: 'Roles on Record',      value: exp.number_of_positions    ?? '—', color: 'var(--teal)' },
              { label: 'Unexplained Gaps',     value: exp.unexplained_gap_count  ?? '—', color: exp.unexplained_gap_count ? 'var(--amber)' : 'var(--green)' },
              { label: 'Suspicious Overlaps',  value: exp.suspicious_overlap_count ?? '—', color: exp.suspicious_overlap_count ? 'var(--red)' : 'var(--green)' },
            ].map(s => (
              <div key={s.label} className="stat-card" style={{ '--accent-color': s.color }}>
                <div className="stat-label">{s.label}</div>
                <div className="stat-value" style={{ fontSize: 22 }}>{s.value}</div>
              </div>
            ))}
          </div>

          {/* ── Timeline consistency banner ───────────────────────────────── */}
          {exp.timeline_consistent === true && (
            <div style={{ padding: '10px 16px', marginBottom: 16, background: 'rgba(34,201,122,0.06)', border: '1px solid rgba(34,201,122,0.2)', borderRadius: 'var(--radius)', display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--green)' }}>
              <CheckCircle size={14} /> Timeline is consistent — no suspicious overlaps or unexplained gaps detected.
            </div>
          )}
          {exp.consistency_flags?.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              {exp.consistency_flags.map((f, i) => (
                <div key={i} style={{ padding: '8px 14px', marginBottom: 6, background: 'rgba(245,166,35,0.06)', border: '1px solid rgba(245,166,35,0.2)', borderRadius: 'var(--radius)', display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
                  <AlertTriangle size={13} color="var(--amber)" />
                  <span style={{ color: 'var(--text2)' }}>{f}</span>
                </div>
              ))}
            </div>
          )}

          {/* ── Current role banner ───────────────────────────────────────── */}
          {exp.is_currently_employed && (
            <div style={{ padding: '12px 18px', marginBottom: 20, background: 'rgba(34,201,122,0.06)', border: '1px solid rgba(34,201,122,0.2)', borderRadius: 'var(--radius)', display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--green)', display: 'inline-block', flexShrink: 0 }} />
              <span style={{ fontSize: 13 }}>
                Currently: <strong>{exp.current_position}</strong> at {exp.current_organization}
              </span>
              {exp.average_tenure_years != null && (
                <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--text3)' }}>
                  Avg tenure: {exp.average_tenure_years} yrs
                </span>
              )}
            </div>
          )}

          {/* ── Tabs ──────────────────────────────────────────────────────── */}
          <div className="tab-bar">
            {TABS.map(t => (
              <button key={t.id} className={`tab-btn${tab === t.id ? ' active' : ''}`} onClick={() => setTab(t.id)}>
                {t.label}
              </button>
            ))}
          </div>

          {/* ── Tab: Timeline ─────────────────────────────────────────────── */}
          {tab === 'timeline' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
              <div className="card">
                <div className="card-title">Career timeline</div>
                <div className="timeline">
                  {roles.map((r, i) => {
                    const color = JOB_COLORS[i % JOB_COLORS.length];
                    return (
                      <div key={i} className="timeline-item">
                        <div className="timeline-dot" style={{ background: color }} />
                        <div>
                          <div style={{ fontWeight: 500, fontSize: 13.5 }}>{r.job_title}</div>
                          <div style={{ fontSize: 12, color: 'var(--text2)', margin: '2px 0' }}>
                            {r.organization}
                            {r.department ? ` · ${r.department}` : ''}
                          </div>
                          {r.location && <div style={{ fontSize: 11.5, color: 'var(--text3)' }}>{r.location}</div>}
                          <div style={{ display: 'flex', gap: 6, marginTop: 6, flexWrap: 'wrap' }}>
                            <span className="badge badge-blue">
                              {r.start_date || '?'} → {r.is_current ? 'Present' : r.end_date || '?'}
                            </span>
                            {r.duration_years != null && (
                              <span className="badge badge-teal">{r.duration_years} yrs</span>
                            )}
                            {r.employment_type && (
                              <span className="badge badge-purple">{r.employment_type}</span>
                            )}
                            {r.is_current && <span className="badge badge-green">Current</span>}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                  {roles.length === 0 && <div style={{ color: 'var(--text3)', fontSize: 13 }}>No experience records.</div>}
                </div>
              </div>

              <div className="card">
                <div className="card-title">Tenure by role</div>
                {roles.map((r, i) => {
                  const dur = r.duration_years || 0;
                  const pct = (dur / maxDuration) * 100;
                  const color = JOB_COLORS[i % JOB_COLORS.length];
                  return (
                    <div key={i} style={{ marginBottom: 14 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <span style={{ fontSize: 12.5, color: 'var(--text2)' }}>{r.job_title}</span>
                        <span style={{ fontSize: 12.5, fontFamily: 'var(--font-mono)', color }}>
                          {dur != null ? `${dur} yrs` : '—'}
                        </span>
                      </div>
                      <div className="progress-bar" style={{ height: 5 }}>
                        <div className="progress-fill" style={{ width: `${pct}%`, background: color }} />
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--text3)', marginTop: 2 }}>{r.organization}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ── Tab: Progression ──────────────────────────────────────────── */}
          {tab === 'progression' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div className="card">
                <div className="card-title">Career trajectory</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                  <div style={{
                    width: 40, height: 40, borderRadius: '50%',
                    background: `${tMeta.color}18`, border: `1px solid ${tMeta.color}40`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <TIcon size={18} color={tMeta.color} />
                  </div>
                  <div>
                    <div style={{ fontSize: 15, fontWeight: 600, color: tMeta.color }}>
                      {exp.career_trajectory_label || tMeta.label}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text3)' }}>
                      {exp.is_progressive ? 'Progressive career path' : 'Non-linear career path'}
                    </div>
                  </div>
                </div>
                {exp.progression_narrative && (
                  <p style={{ fontSize: 13, color: 'var(--text2)', lineHeight: 1.7 }}>
                    {exp.progression_narrative}
                  </p>
                )}
              </div>

              {exp.seniority_scores?.length > 0 && (
                <div className="card">
                  <div className="card-title">Seniority ladder</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {exp.seniority_scores.map(([title, score], i) => {
                      const pct = (score / 11) * 100;
                      return (
                        <div key={i}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                            <span style={{ fontSize: 12.5, color: 'var(--text2)' }}>{title}</span>
                            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--accent)' }}>
                              {score} / 11
                            </span>
                          </div>
                          <div className="progress-bar" style={{ height: 5 }}>
                            <div className="progress-fill" style={{ width: `${pct}%`, background: 'var(--accent)' }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              <div className="stat-grid">
                {[
                  { label: 'Total Experience', value: exp.total_years_experience != null ? `${exp.total_years_experience} yrs` : '—', color: 'var(--accent)' },
                  { label: 'Avg Tenure',       value: exp.average_tenure_years != null ? `${exp.average_tenure_years} yrs` : '—', color: 'var(--teal)' },
                  { label: 'Longest Role',     value: exp.longest_tenure_years != null ? `${exp.longest_tenure_years} yrs` : '—', color: 'var(--green)' },
                  { label: 'Roles',            value: exp.number_of_positions ?? '—', color: 'var(--accent2)' },
                ].map(s => (
                  <div key={s.label} className="stat-card" style={{ '--accent-color': s.color }}>
                    <div className="stat-label">{s.label}</div>
                    <div className="stat-value" style={{ fontSize: 20 }}>{s.value}</div>
                  </div>
                ))}
              </div>

              {exp.longest_role && (
                <div style={{ padding: '10px 14px', background: 'var(--bg3)', borderRadius: 'var(--radius)', fontSize: 13, color: 'var(--text2)' }}>
                  Longest role: <strong style={{ color: 'var(--text)' }}>{exp.longest_role}</strong> ({exp.longest_tenure_years} yrs)
                </div>
              )}
            </div>
          )}

          {/* ── Tab: Timeline Flags ───────────────────────────────────────── */}
          {tab === 'flags' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              {/* Employment gaps */}
              <div className="card">
                <div className="card-title">
                  Employment gaps ({gaps.length}) — {exp.unexplained_gap_count ?? 0} unexplained
                </div>
                {gaps.length === 0 ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--green)', fontSize: 13 }}>
                    <CheckCircle size={15} /> No employment gaps detected.
                  </div>
                ) : gaps.map((g, i) => <GapCard key={i} gap={g} index={i} />)}
              </div>

              {/* Job–Job overlaps */}
              <div className="card">
                <div className="card-title">
                  Job overlaps ({jobOverlaps.length}) — {exp.suspicious_overlap_count ?? 0} suspicious
                </div>
                {jobOverlaps.length === 0 ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--green)', fontSize: 13 }}>
                    <CheckCircle size={15} /> No overlapping job periods detected.
                  </div>
                ) : jobOverlaps.map((o, i) => <OverlapCard key={i} overlap={o} />)}
              </div>

              {/* Education–Employment overlaps */}
              <div className="card">
                <div className="card-title">
                  Education–Employment overlaps ({eduOverlaps.length})
                  {exp.edu_employment_scrutiny_count > 0 && (
                    <span className="badge badge-amber" style={{ marginLeft: 8, fontSize: 10 }}>
                      {exp.edu_employment_scrutiny_count} require scrutiny
                    </span>
                  )}
                </div>
                {eduOverlaps.length === 0 ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--green)', fontSize: 13 }}>
                    <CheckCircle size={15} /> No education–employment overlaps detected.
                  </div>
                ) : eduOverlaps.map((o, i) => <EduOverlapCard key={i} overlap={o} />)}
              </div>
            </div>
          )}

          {/* ── Tab: All Records ──────────────────────────────────────────── */}
          {tab === 'records' && (
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Title</th><th>Organization</th><th>Type</th>
                    <th>From</th><th>To</th><th>Duration</th><th>Seniority</th>
                  </tr>
                </thead>
                <tbody>
                  {roles.length === 0 ? (
                    <tr><td colSpan={7} style={{ color: 'var(--text3)', textAlign: 'center' }}>No experience records.</td></tr>
                  ) : roles.map((r, i) => (
                    <tr key={i}>
                      <td>
                        <div style={{ fontWeight: 500, fontSize: 13 }}>{r.job_title}</div>
                        {r.department && <div style={{ fontSize: 11, color: 'var(--text3)' }}>{r.department}</div>}
                        {r.responsibilities?.length > 0 && (
                          <div style={{ fontSize: 11, color: 'var(--text3)', marginTop: 4, lineHeight: 1.5 }}>
                            {r.responsibilities.slice(0, 2).join(' · ')}
                          </div>
                        )}
                      </td>
                      <td className="text-muted">{r.organization}</td>
                      <td>{r.employment_type ? <span className="badge badge-teal" style={{ fontSize: 11 }}>{r.employment_type}</span> : <span style={{ color: 'var(--text3)' }}>—</span>}</td>
                      <td className="text-mono">{r.start_date || '—'}</td>
                      <td className="text-mono">{r.is_current ? <span className="badge badge-green" style={{ fontSize: 11 }}>Present</span> : r.end_date || '—'}</td>
                      <td className="text-mono">{r.duration_years != null ? `${r.duration_years} yrs` : '—'}</td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <div style={{ flex: 1, height: 4, background: 'var(--border)', borderRadius: 99, overflow: 'hidden' }}>
                            <div style={{ height: '100%', width: `${((r.seniority_score || 0) / 11) * 100}%`, background: 'var(--accent)', borderRadius: 99 }} />
                          </div>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text3)', flexShrink: 0 }}>
                            {r.seniority_score ?? '—'}
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
