import React, { useState, useEffect } from 'react';
import { useApp } from '../AppContext';
import CandidateSelector from '../components/CandidateSelector';
import { analyzeCandidate, analyzeSkillsWithJD } from '../api';
import { BookOpen, AlertCircle, CheckCircle, AlertTriangle, Minus, Briefcase, ChevronDown, ChevronUp, Target } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis } from 'recharts';

// ── Colour maps ──────────────────────────────────────────────────────────────
const CAT_PALETTE = ['var(--accent)', 'var(--teal)', 'var(--accent2)', 'var(--green)', 'var(--amber)'];

const STRENGTH_META = {
  strongly_evidenced:  { color: 'var(--green)',  bg: 'rgba(34,201,122,0.08)',  border: 'rgba(34,201,122,0.25)',  icon: CheckCircle,    label: 'Strongly Evidenced'  },
  partially_evidenced: { color: 'var(--accent)',  bg: 'rgba(79,124,255,0.08)', border: 'rgba(79,124,255,0.25)', icon: CheckCircle,    label: 'Partially Evidenced' },
  weakly_evidenced:    { color: 'var(--amber)',   bg: 'rgba(245,166,35,0.08)', border: 'rgba(245,166,35,0.25)', icon: Minus,          label: 'Weakly Evidenced'    },
  unsupported:         { color: 'var(--red)',     bg: 'rgba(240,82,82,0.08)',  border: 'rgba(240,82,82,0.25)',  icon: AlertTriangle,  label: 'Unsupported'         },
};

// ── Helpers ──────────────────────────────────────────────────────────────────

function Spinner() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '40px 0', color: 'var(--text3)', fontSize: 13 }}>
      <div style={{ width: 18, height: 18, border: '2px solid var(--border2)', borderTopColor: 'var(--accent)', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
      Running analysis…
    </div>
  );
}

function SkillEvidenceCard({ assessment }) {
  const meta = STRENGTH_META[assessment.strength] || STRENGTH_META.unsupported;
  const Icon = meta.icon;
  const detail = assessment.evidence_detail || {};

  return (
    <div style={{
      padding: '12px 14px', marginBottom: 8,
      background: meta.bg, border: `1px solid ${meta.border}`, borderRadius: 'var(--radius)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
        <Icon size={14} color={meta.color} style={{ flexShrink: 0 }} />
        <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text)' }}>{assessment.skill}</span>
        <span className="badge" style={{ marginLeft: 'auto', background: meta.bg, color: meta.color, border: `1px solid ${meta.border}`, fontSize: 10.5 }}>
          {meta.label}
        </span>
      </div>
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        {['employment', 'publications', 'education'].map(src => {
          const info = detail[src] || {};
          const matched = info.matched;
          const kws = info.keywords_found || [];
          return (
            <div key={src} style={{ fontSize: 11.5 }}>
              <span style={{ color: matched ? meta.color : 'var(--text3)', fontFamily: 'var(--font-mono)' }}>
                {matched ? '✓' : '✗'} {src.charAt(0).toUpperCase() + src.slice(1)}
              </span>
              {kws.length > 0 && (
                <span style={{ color: 'var(--text3)', marginLeft: 5 }}>({kws.slice(0,3).join(', ')})</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

const JD_ALIGNMENT_META = {
  'Closely Aligned':   { badge: 'badge-green',  color: 'var(--green)'  },
  'Partially Aligned': { badge: 'badge-amber',  color: 'var(--amber)'  },
  'Weakly Aligned':    { badge: 'badge-red',    color: 'var(--red)'    },
};

// ── Main component ────────────────────────────────────────────────────────────
export default function SkillsPage() {
  const { selectedCandidate: c } = useApp();
  const [analysis, setAnalysis]  = useState(null);
  const [loading, setLoading]    = useState(false);
  const [error, setError]        = useState(null);
  const [filter, setFilter]      = useState('all');

  // JD alignment state
  const [jdText, setJdText]       = useState('');
  const [jdOpen, setJdOpen]       = useState(false);
  const [jdResult, setJdResult]   = useState(null);
  const [jdLoading, setJdLoading] = useState(false);
  const [jdError, setJdError]     = useState(null);

  useEffect(() => {
    if (!c?.candidate_id) { setAnalysis(null); setJdResult(null); return; }
    setLoading(true);
    setError(null);
    setJdResult(null);
    analyzeCandidate(c.candidate_id)
      .then(data => { setAnalysis(data); setLoading(false); })
      .catch(e  => { setError(e.message); setLoading(false); });
  }, [c?.candidate_id]);

  const runJDAlignment = () => {
    if (!c?.candidate_id || !jdText.trim()) return;
    setJdLoading(true);
    setJdError(null);
    analyzeSkillsWithJD(c.candidate_id, jdText.trim())
      .then(data => { setJdResult(data); setJdLoading(false); })
      .catch(e   => { setJdError(e.message); setJdLoading(false); });
  };

  const skillData  = analysis?.skill_analysis || {};
  const rawSkills  = c?.skills || [];
  const assessments= skillData.skill_assessments || [];
  const summary    = skillData.summary || {};
  const bySource   = skillData.skills_by_source || {};

  // Category grouping from raw skills (for the pie/overview)
  const grouped = rawSkills.reduce((acc, s) => {
    const cat = s.skill_category || 'Other';
    acc[cat] = (acc[cat] || 0) + 1;
    return acc;
  }, {});
  const pieData = Object.entries(grouped).map(([name, value]) => ({ name, value }));

  // Summary bar chart data
  const summaryBarData = Object.entries(summary).map(([key, val]) => ({
    name: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    value: val,
    key,
  }));

  // Filtered assessments
  const filtered = filter === 'all'
    ? assessments
    : assessments.filter(a => a.strength === filter);

  const FILTERS = [
    { id: 'all',                 label: `All (${assessments.length})` },
    { id: 'strongly_evidenced',  label: `Strongly (${summary.strongly_evidenced ?? 0})` },
    { id: 'partially_evidenced', label: `Partially (${summary.partially_evidenced ?? 0})` },
    { id: 'weakly_evidenced',    label: `Weakly (${summary.weakly_evidenced ?? 0})` },
    { id: 'unsupported',         label: `Unsupported (${summary.unsupported ?? 0})` },
  ];

  return (
    <div className="fade-up">
      <div className="page-header">
        <h1>Skills Analysis</h1>
        <p className="subtitle">
          Skill alignment with employment · publications · education · evidence strength
        </p>
      </div>

      <CandidateSelector />

      {!c ? (
        <div className="card">
          <div className="empty-state"><BookOpen size={32} /><h3>Select a candidate</h3></div>
        </div>
      ) : loading ? (
        <div className="card"><Spinner /></div>
      ) : error ? (
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--red)' }}>
          <AlertCircle size={18} /><span style={{ fontSize: 13 }}>{error}</span>
        </div>
      ) : rawSkills.length === 0 ? (
        <div className="card">
          <div className="empty-state"><BookOpen size={32} /><h3>No skills extracted</h3><p>The CV may not have a dedicated skills section</p></div>
        </div>
      ) : (
        <>
          {/* ── Stats row ─────────────────────────────────────────────────── */}
          <div className="stat-grid" style={{ marginBottom: 20 }}>
            {[
              { label: 'Total Skills',       value: skillData.total_skills     ?? rawSkills.length, color: 'var(--accent)' },
              { label: 'Strongly Evidenced', value: summary.strongly_evidenced  ?? '—',             color: 'var(--green)' },
              { label: 'Partially Evidenced',value: summary.partially_evidenced ?? '—',             color: 'var(--teal)' },
              { label: 'Unsupported',        value: summary.unsupported         ?? '—',             color: summary.unsupported > 0 ? 'var(--red)' : 'var(--green)' },
            ].map(s => (
              <div key={s.label} className="stat-card" style={{ '--accent-color': s.color }}>
                <div className="stat-label">{s.label}</div>
                <div className="stat-value">{s.value}</div>
              </div>
            ))}
          </div>

          {/* ── Interpretation banner ─────────────────────────────────────── */}
          {skillData.interpretation && (
            <div style={{ padding: '12px 16px', marginBottom: 20, background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', fontSize: 13, color: 'var(--text2)', lineHeight: 1.6 }}>
              {skillData.interpretation}
            </div>
          )}

          {/* ── Overview charts ───────────────────────────────────────────── */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
            <div className="card">
              <div className="card-title">Skills by category</div>
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80}
                    label={({ name, percent }) => `${name} ${Math.round(percent * 100)}%`} labelLine={false} fontSize={11}>
                    {pieData.map((_, i) => (
                      <Cell key={i} fill={CAT_PALETTE[i % CAT_PALETTE.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <div className="card-title">Evidence strength breakdown</div>
              {summaryBarData.length > 0 ? (
                <ResponsiveContainer width="100%" height={160}>
                  <BarChart data={summaryBarData} layout="vertical" margin={{ left: 30 }}>
                    <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11, fill: 'var(--text3)' }} />
                    <YAxis type="category" dataKey="name" tick={{ fontSize: 10.5, fill: 'var(--text2)' }} width={130} />
                    <Tooltip contentStyle={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }} />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                      {summaryBarData.map((entry, i) => (
                        <Cell key={i} fill={STRENGTH_META[entry.key]?.color || 'var(--accent)'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : <div style={{ color: 'var(--text3)', fontSize: 13 }}>No analysis data.</div>}

              {/* Evidence source breakdown */}
              {Object.keys(bySource).length > 0 && (
                <div style={{ marginTop: 14, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                  {[
                    { label: 'Employment', key: 'employment_evidenced',   color: 'var(--accent)' },
                    { label: 'Publications', key: 'publication_evidenced', color: 'var(--teal)' },
                    { label: 'Education',  key: 'education_evidenced',     color: 'var(--green)' },
                  ].map(s => (
                    <div key={s.key} style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 10.5, color: 'var(--text3)', fontFamily: 'var(--font-mono)' }}>{s.label}</div>
                      <div style={{ fontSize: 20, fontWeight: 700, color: s.color, fontFamily: 'var(--font-head)' }}>
                        {bySource[s.key] ?? '—'}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* ── Per-skill evidence breakdown ──────────────────────────────── */}
          {assessments.length > 0 && (
            <>
              <div className="section-divider"><span>Per-skill evidence breakdown</span></div>

              {/* Filter bar */}
              <div className="tab-bar" style={{ marginBottom: 16 }}>
                {FILTERS.map(f => (
                  <button key={f.id} className={`tab-btn${filter === f.id ? ' active' : ''}`} onClick={() => setFilter(f.id)}>
                    {f.label}
                  </button>
                ))}
              </div>

              <div>
                {filtered.length === 0
                  ? <div style={{ color: 'var(--text3)', fontSize: 13 }}>No skills in this category.</div>
                  : filtered.map((a, i) => <SkillEvidenceCard key={i} assessment={a} />)
                }
              </div>
            </>
          )}

          {/* ── Raw skills by category ────────────────────────────────────── */}
          <div className="section-divider"><span>All skills by category</span></div>
          {Object.entries(grouped).map(([cat, count], ci) => {
            const color = CAT_PALETTE[ci % CAT_PALETTE.length];
            const catSkills = rawSkills.filter(s => (s.skill_category || 'Other') === cat);
            return (
              <div key={cat} style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <span style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color, fontWeight: 600 }}>{cat}</span>
                  <span style={{ fontSize: 11, color: 'var(--text3)' }}>{count} skill{count !== 1 ? 's' : ''}</span>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {catSkills.map((s, i) => {
                    const assessment = assessments.find(a => a.skill === s.skill_name);
                    const meta = assessment ? STRENGTH_META[assessment.strength] : null;
                    return (
                      <span key={i} title={meta ? meta.label : 'Not analysed'} style={{
                        padding: '5px 12px', borderRadius: 99, fontSize: 12.5,
                        background: meta ? meta.bg : `${color}15`,
                        border: `1px solid ${meta ? meta.border : `${color}35`}`,
                        color: meta ? meta.color : color,
                        cursor: 'default',
                      }}>
                        {s.skill_name}
                      </span>
                    );
                  })}
                </div>
              </div>
            );
          })}
          {/* ── Job Description Alignment ─────────────────────────────────── */}
          <div className="section-divider" style={{ margin: '28px 0 16px' }}>
            <span>
              <Target size={12} style={{ display: 'inline', marginRight: 6 }} />
              Job Description Alignment (Req 3.9)
            </span>
          </div>

          <div className="card" style={{ marginBottom: 8 }}>
            {/* Collapsible header */}
            <div
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}
              onClick={() => setJdOpen(v => !v)}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: 13.5, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Briefcase size={13} color="var(--accent)" /> Paste a job description to measure skill relevance
                </div>
                <div style={{ fontSize: 12, color: 'var(--text3)', marginTop: 3 }}>
                  Identifies which of the candidate's skills match the role, and which JD requirements are missing.
                </div>
              </div>
              {jdOpen
                ? <ChevronUp size={16} color="var(--text3)" />
                : <ChevronDown size={16} color="var(--text3)" />}
            </div>

            {jdOpen && (
              <div style={{ marginTop: 14 }}>
                <textarea
                  value={jdText}
                  onChange={e => setJdText(e.target.value)}
                  placeholder="Paste the job description here…"
                  style={{
                    width: '100%', minHeight: 140, padding: '10px 12px',
                    background: 'var(--bg3)', border: '1px solid var(--border2)',
                    borderRadius: 'var(--radius)', color: 'var(--text)', fontSize: 13,
                    fontFamily: 'inherit', resize: 'vertical', outline: 'none',
                    boxSizing: 'border-box',
                  }}
                />
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 10 }}>
                  <button
                    className="btn btn-primary"
                    onClick={runJDAlignment}
                    disabled={jdLoading || !jdText.trim()}
                    style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}
                  >
                    {jdLoading
                      ? <><div style={{ width: 13, height: 13, border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} /> Analysing…</>
                      : <><Target size={13} /> Analyse against JD</>}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* JD alignment results */}
          {jdError && (
            <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--red)', marginBottom: 8 }}>
              <AlertCircle size={15} /><span style={{ fontSize: 13 }}>{jdError}</span>
            </div>
          )}

          {jdResult && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
              {/* Summary card */}
              <div className="card">
                <div className="card-title">
                  <Target size={13} style={{ display: 'inline', marginRight: 6 }} />
                  JD alignment result
                </div>
                {(() => {
                  const label = jdResult.jd_alignment_label;
                  const score = jdResult.alignment_score;
                  const meta  = JD_ALIGNMENT_META[label] || JD_ALIGNMENT_META['Weakly Aligned'];
                  const pct   = score != null ? Math.round(score * 100) : null;
                  return (
                    <>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                        <div style={{
                          width: 72, height: 72, borderRadius: '50%', flexShrink: 0,
                          border: `3px solid ${meta.color}`,
                          display: 'flex', flexDirection: 'column',
                          alignItems: 'center', justifyContent: 'center',
                        }}>
                          <div style={{ fontFamily: 'var(--font-head)', fontSize: 22, fontWeight: 700, color: meta.color }}>
                            {pct != null ? `${pct}%` : '—'}
                          </div>
                        </div>
                        <div>
                          <span className={`badge ${meta.badge}`} style={{ fontSize: 12 }}>{label || '—'}</span>
                          <div style={{ fontSize: 12, color: 'var(--text3)', marginTop: 6 }}>
                            {jdResult.job_relevant_skills?.length ?? 0} of {jdResult.total_skills} skills matched JD
                          </div>
                        </div>
                      </div>

                      {/* Progress bar */}
                      {pct != null && (
                        <div className="progress-bar" style={{ height: 6, marginBottom: 14 }}>
                          <div className="progress-fill" style={{ width: `${pct}%`, background: meta.color }} />
                        </div>
                      )}

                      {jdResult.interpretation && (
                        <div style={{ fontSize: 12.5, color: 'var(--text2)', lineHeight: 1.6 }}>
                          {jdResult.interpretation}
                        </div>
                      )}
                    </>
                  );
                })()}
              </div>

              {/* Matched + missing skills */}
              <div className="card">
                <div className="card-title">Skill match breakdown</div>

                {(jdResult.job_relevant_skills?.length > 0) && (
                  <>
                    <div style={{ fontSize: 11.5, color: 'var(--green)', fontFamily: 'var(--font-mono)', marginBottom: 6 }}>
                      ✓ Matched in JD ({jdResult.job_relevant_skills.length})
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 14 }}>
                      {jdResult.job_relevant_skills.map((s, i) => (
                        <span key={i} style={{
                          padding: '4px 10px', borderRadius: 99, fontSize: 12,
                          background: 'rgba(34,201,122,0.1)', border: '1px solid rgba(34,201,122,0.3)',
                          color: 'var(--green)',
                        }}>{s}</span>
                      ))}
                    </div>
                  </>
                )}

                {(jdResult.missing_jd_skills?.length > 0) && (
                  <>
                    <div style={{ fontSize: 11.5, color: 'var(--amber)', fontFamily: 'var(--font-mono)', marginBottom: 6 }}>
                      ⚠ JD keywords not covered ({jdResult.missing_jd_skills.length})
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {jdResult.missing_jd_skills.map((s, i) => (
                        <span key={i} style={{
                          padding: '4px 10px', borderRadius: 99, fontSize: 12,
                          background: 'rgba(245,166,35,0.1)', border: '1px solid rgba(245,166,35,0.3)',
                          color: 'var(--amber)',
                        }}>{s}</span>
                      ))}
                    </div>
                  </>
                )}

                {!jdResult.job_relevant_skills?.length && !jdResult.missing_jd_skills?.length && (
                  <div style={{ color: 'var(--text3)', fontSize: 13 }}>No overlap detected.</div>
                )}
              </div>
            </div>
          )}
        </>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
