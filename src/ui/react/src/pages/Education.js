import React, { useState, useEffect } from 'react';
import { useApp } from '../AppContext';
import CandidateSelector from '../components/CandidateSelector';
import { analyzeCandidate } from '../api';
import {
  GraduationCap, AlertTriangle, CheckCircle, Globe,
  BookOpen, AlertCircle, TrendingUp, Award, Sparkles,
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

// ── Helpers ──────────────────────────────────────────────────────────────────

function Spinner() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '40px 0', color: 'var(--text3)', fontSize: 13 }}>
      <div style={{ width: 18, height: 18, border: '2px solid var(--border2)', borderTopColor: 'var(--accent)', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
      Running analysis…
    </div>
  );
}

function gradeColor(pct) {
  if (pct >= 75) return 'var(--green)';
  if (pct >= 55) return 'var(--amber)';
  return 'var(--red)';
}

function GradeBar({ label, pct, display }) {
  if (pct == null) return null;
  const color = gradeColor(pct);
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
        <span style={{ fontSize: 12.5, color: 'var(--text2)' }}>{label}</span>
        <span style={{ fontSize: 12.5, fontFamily: 'var(--font-mono)', color }}>{display}</span>
      </div>
      <div className="progress-bar" style={{ height: 5 }}>
        <div className="progress-fill" style={{ width: `${Math.min(pct, 100)}%`, background: color }} />
      </div>
    </div>
  );
}

const DEGREE_COLORS = {
  'SSC/Matric':          'var(--teal)',
  'HSSC/Intermediate':   'var(--teal)',
  'Bachelor (14-year)':  'var(--accent)',
  'Bachelor (16-year)':  'var(--accent)',
  'Master (16-year)':    'var(--accent2)',
  'Master (18-year)':    'var(--accent2)',
  'PhD':                 'var(--green)',
};

// ── Main component ────────────────────────────────────────────────────────────
export default function EducationPage() {
  const { selectedCandidate: c } = useApp();
  const [analysis, setAnalysis]  = useState(null);
  const [loading, setLoading]    = useState(false);
  const [error, setError]        = useState(null);

  useEffect(() => {
    if (!c?.candidate_id) { setAnalysis(null); return; }
    setLoading(true);
    setError(null);
    analyzeCandidate(c.candidate_id)
      .then(data => { setAnalysis(data); setLoading(false); })
      .catch(e  => { setError(e.message); setLoading(false); });
  }, [c?.candidate_id]);

  const edu = analysis?.edu_analysis || {};
  const detail = edu.education_detail || [];

  // Grade chart — only records that have a normalized_percentage
  const chartData = detail
    .filter(e => e.normalized_percentage != null)
    .map(e => ({
      name:  e.degree_level.replace(' (16-year)', '').replace(' (18-year)', '').replace(' (14-year)', ''),
      grade: Math.round(e.normalized_percentage),
      raw:   e.grade_value != null ? `${e.grade_value} (${e.grade_type || ''})` : `${e.normalized_percentage}%`,
    }));

  const gaps            = edu.gaps_detected             || [];
  const gapsJustified   = edu.gaps_with_justification   || [];
  const theses          = edu.theses                    || [];
  const foreignInst     = edu.foreign_institutions      || [];
  const rankings        = edu.institutional_rankings    || [];
  const interpretation  = edu.educational_strength_interpretation || null;

  return (
    <div className="fade-up">
      <div className="page-header">
        <h1>Education Analysis</h1>
        <p className="subtitle">
          Academic progression · grade normalization · institutional quality · gap detection
        </p>
      </div>

      <CandidateSelector />

      {!c ? (
        <div className="card">
          <div className="empty-state">
            <GraduationCap size={32} />
            <h3>Select a candidate</h3>
            <p>Choose a candidate above to view their education analysis</p>
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
              { label: 'Highest Degree',   value: edu.highest_degree           || '—', color: 'var(--green)',   small: true },
              { label: 'Total Degrees',    value: edu.total_degrees             ?? '—', color: 'var(--accent)' },
              { label: 'Avg Grade',        value: edu.average_percentage != null ? `${edu.average_percentage}%` : '—', color: 'var(--teal)' },
              { label: 'Edu Gaps',         value: gaps.length,                          color: gaps.length ? 'var(--amber)' : 'var(--green)' },
            ].map(s => (
              <div key={s.label} className="stat-card" style={{ '--accent-color': s.color }}>
                <div className="stat-label">{s.label}</div>
                <div className="stat-value" style={{ fontSize: s.small ? 16 : 28 }}>{s.value}</div>
              </div>
            ))}
          </div>

          {/* ── Flags row ─────────────────────────────────────────────────── */}
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 20 }}>
            <span className={`badge ${edu.has_phd ? 'badge-green' : 'badge-teal'}`}>
              {edu.has_phd ? '✓ PhD' : 'No PhD'}
            </span>
            <span className={`badge ${edu.has_masters ? 'badge-teal' : 'badge-amber'}`}>
              {edu.has_masters ? '✓ Masters' : 'No Masters'}
            </span>
            {edu.has_foreign_education && (
              <span className="badge badge-purple" style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <Globe size={11} /> Foreign education
              </span>
            )}
            {edu.education_span_years != null && (
              <span className="badge badge-blue">
                Education span: {edu.education_span_years} yr(s)
              </span>
            )}
          </div>

          {/* ── Highest degree summary ────────────────────────────────────── */}
          {edu.highest_degree && (
            <div className="card" style={{ marginBottom: 20 }}>
              <div className="card-title">Highest qualification</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, alignItems: 'flex-start' }}>
                <div>
                  <div style={{ fontSize: 18, fontWeight: 600, color: 'var(--green)' }}>
                    {edu.highest_degree_title || edu.highest_degree}
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--text2)', marginTop: 4 }}>
                    {edu.highest_degree_institution || '—'}
                    {edu.highest_degree_country ? ` · ${edu.highest_degree_country}` : ''}
                    {edu.highest_degree_year    ? ` · ${edu.highest_degree_year}` : ''}
                  </div>
                </div>
                {edu.highest_degree_rank != null && (
                  <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
                    <div style={{ fontSize: 11, color: 'var(--text3)', fontFamily: 'var(--font-mono)' }}>Degree rank</div>
                    <div style={{ fontFamily: 'var(--font-head)', fontSize: 22, color: 'var(--accent)' }}>{edu.highest_degree_rank}</div>
                    <div style={{ fontSize: 11, color: 'var(--text3)' }}>(7 = PhD)</div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── Timeline + Grade chart ────────────────────────────────────── */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
            <div className="card">
              <div className="card-title">Degree timeline</div>
              <div className="timeline">
                {detail.map((e, i) => {
                  const color = DEGREE_COLORS[e.degree_level] || 'var(--accent)';
                  return (
                    <div key={i} className="timeline-item">
                      <div className="timeline-dot" style={{ background: color }} />
                      <div>
                        <div style={{ fontWeight: 500, fontSize: 13.5 }}>{e.degree_title}</div>
                        <div style={{ fontSize: 12, color: 'var(--text2)', margin: '2px 0' }}>
                          {e.institution || '—'}
                          {e.country ? ` · ${e.country}` : ''}
                        </div>
                        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 4 }}>
                          {e.start_year && e.end_year && (
                            <span className="badge badge-blue">{e.start_year} – {e.end_year}</span>
                          )}
                          {e.specialization && (
                            <span className="badge badge-teal">{e.specialization}</span>
                          )}
                          {e.normalized_percentage != null && (
                            <span className="badge badge-purple">
                              {e.grade_value} {e.grade_type ? `(${e.grade_type})` : ''}
                            </span>
                          )}
                        </div>
                        {e.thesis_title && (
                          <div style={{ marginTop: 6, fontSize: 11.5, color: 'var(--text3)', fontStyle: 'italic' }}>
                            Thesis: {e.thesis_title}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="card">
              <div className="card-title">Grade progression (normalised to %)</div>
              {chartData.length > 0 ? (
                <>
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                      <XAxis dataKey="name" tick={{ fontSize: 10, fill: 'var(--text3)' }} />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: 'var(--text3)' }} unit="%" />
                      <Tooltip
                        contentStyle={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }}
                        formatter={(val, _name, props) => [props.payload.raw, 'Grade']}
                      />
                      <Bar dataKey="grade" radius={[4, 4, 0, 0]}>
                        {chartData.map((entry, i) => (
                          <Cell key={i} fill={gradeColor(entry.grade)} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                  <div style={{ marginTop: 16 }}>
                    {detail.filter(e => e.normalized_percentage != null).map((e, i) => (
                      <GradeBar
                        key={i}
                        label={e.degree_level.replace(/\s*\(.*?\)/g, '')}
                        pct={e.normalized_percentage}
                        display={`${e.grade_value} ${e.grade_type ? `(${e.grade_type})` : ''}`}
                      />
                    ))}
                  </div>
                </>
              ) : (
                <div style={{ color: 'var(--text3)', fontSize: 13, padding: '20px 0' }}>No grade data available.</div>
              )}

              {/* Grade stats */}
              {(edu.average_percentage != null || edu.highest_percentage != null) && (
                <div style={{ display: 'flex', gap: 14, marginTop: 16, flexWrap: 'wrap' }}>
                  {edu.highest_percentage != null && (
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 11, color: 'var(--text3)', fontFamily: 'var(--font-mono)' }}>Highest</div>
                      <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--green)', fontFamily: 'var(--font-head)' }}>
                        {edu.highest_percentage}%
                      </div>
                    </div>
                  )}
                  {edu.average_percentage != null && (
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 11, color: 'var(--text3)', fontFamily: 'var(--font-mono)' }}>Average</div>
                      <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--accent)', fontFamily: 'var(--font-head)' }}>
                        {edu.average_percentage}%
                      </div>
                    </div>
                  )}
                  {edu.lowest_percentage != null && (
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 11, color: 'var(--text3)', fontFamily: 'var(--font-mono)' }}>Lowest</div>
                      <div style={{ fontSize: 18, fontWeight: 700, color: gradeColor(edu.lowest_percentage), fontFamily: 'var(--font-head)' }}>
                        {edu.lowest_percentage}%
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* ── Educational strength interpretation ──────────────────────── */}
          {interpretation && (
            <div style={{
              padding: '12px 16px', marginBottom: 20,
              background: 'rgba(79,124,255,0.06)', border: '1px solid rgba(79,124,255,0.2)',
              borderRadius: 'var(--radius)', display: 'flex', gap: 10, alignItems: 'flex-start',
            }}>
              <Sparkles size={14} color="var(--accent)" style={{ flexShrink: 0, marginTop: 2 }} />
              <span style={{ fontSize: 13, color: 'var(--text2)', lineHeight: 1.6 }}>{interpretation}</span>
            </div>
          )}

          {/* ── Gap detection with justification ─────────────────────────── */}
          <div className="card" style={{ marginBottom: 20 }}>
            <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <TrendingUp size={13} /> Gap detection
            </div>
            {gapsJustified.length === 0 ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--green)', fontSize: 13 }}>
                <CheckCircle size={15} /> No significant educational gaps detected.
              </div>
            ) : gapsJustified.map((g, i) => {
              const color  = g.justified ? 'var(--teal)' : 'var(--amber)';
              const bg     = g.justified ? 'rgba(34,201,163,0.06)' : 'rgba(245,166,35,0.06)';
              const border = g.justified ? 'rgba(34,201,163,0.2)'  : 'rgba(245,166,35,0.2)';
              return (
                <div key={i} style={{
                  padding: '10px 14px', marginBottom: 8,
                  background: bg, border: `1px solid ${border}`, borderRadius: 'var(--radius)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 5 }}>
                    {g.justified
                      ? <CheckCircle size={13} color={color} style={{ flexShrink: 0 }} />
                      : <AlertTriangle size={13} color={color} style={{ flexShrink: 0 }} />}
                    <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text)' }}>
                      {g.gap_years} year(s) between {g.from_degree} and {g.to_degree}
                    </span>
                    <span style={{ marginLeft: 'auto' }}>
                      <span className={`badge ${g.justified ? 'badge-teal' : 'badge-amber'}`} style={{ fontSize: 10.5 }}>
                        {g.justified ? 'Justified' : 'Unexplained'}
                      </span>
                    </span>
                  </div>
                  <div style={{ fontSize: 12, color, paddingLeft: 23 }}>{g.justification}</div>
                  {g.gap_start_year && (
                    <div style={{ fontSize: 11, color: 'var(--text3)', paddingLeft: 23, marginTop: 3, fontFamily: 'var(--font-mono)' }}>
                      Period: {g.gap_start_year} – {g.gap_end_year}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* ── Degree progression ───────────────────────────────────────── */}
          {edu.degree_progression?.length > 0 && (
            <div className="card" style={{ marginBottom: 20 }}>
              <div className="card-title">Degree progression</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                {edu.degree_progression.map((d, i) => (
                  <React.Fragment key={i}>
                    <span className="badge badge-blue" style={{ fontSize: 12 }}>{d}</span>
                    {i < edu.degree_progression.length - 1 && (
                      <span style={{ color: 'var(--text3)', fontSize: 12 }}>→</span>
                    )}
                  </React.Fragment>
                ))}
              </div>
            </div>
          )}

          {/* ── Foreign education ─────────────────────────────────────────── */}
          {foreignInst.length > 0 && (
            <div className="card" style={{ marginBottom: 20 }}>
              <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Globe size={13} /> Foreign institutions
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {foreignInst.map((inst, i) => (
                  <span key={i} className="badge badge-purple">{inst}</span>
                ))}
              </div>
            </div>
          )}

          {/* ── Theses ────────────────────────────────────────────────────── */}
          {theses.length > 0 && (
            <div className="card" style={{ marginBottom: 20 }}>
              <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <BookOpen size={13} /> Thesis / dissertation titles
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {theses.map((t, i) => (
                  <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                    <span className="badge badge-teal" style={{ flexShrink: 0 }}>{t.degree}</span>
                    <span style={{ fontSize: 13, color: 'var(--text2)', lineHeight: 1.5 }}>{t.title}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── THE / QS institutional rankings ──────────────────────────── */}
          <div className="card" style={{ marginBottom: 20 }}>
            <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Award size={13} /> Institutional quality (QS World University Rankings 2024)
            </div>
            {rankings.length === 0 ? (
              <div style={{ fontSize: 13, color: 'var(--text3)' }}>
                No ranked institutions matched in the QS / THE lookup for this candidate's education records.
              </div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr><th>Institution (as listed)</th><th>Matched Name</th><th>QS Rank</th><th>Tier</th></tr>
                </thead>
                <tbody>
                  {rankings.map((r, i) => (
                    <tr key={i}>
                      <td style={{ fontWeight: 500 }}>{r.institution}</td>
                      <td style={{ color: 'var(--text2)' }}>{r.official_name}</td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent)' }}>
                        #{r.rank_number}
                      </td>
                      <td>
                        <span className={`badge ${r.rank_number <= 100 ? 'badge-green' : r.rank_number <= 300 ? 'badge-teal' : r.rank_number <= 500 ? 'badge-blue' : 'badge-amber'}`}>
                          {r.tier}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* ── All records table ─────────────────────────────────────────── */}
          <div className="section-divider"><span>All education records</span></div>
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Degree Title</th><th>Level</th><th>Institution</th>
                  <th>Country</th><th>Years</th><th>Grade</th><th>Normalised %</th>
                </tr>
              </thead>
              <tbody>
                {detail.length === 0 ? (
                  <tr><td colSpan={7} style={{ color: 'var(--text3)', textAlign: 'center' }}>No education records.</td></tr>
                ) : detail.map((e, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 500, fontSize: 13 }}>
                      {e.degree_title}
                      {e.thesis_title && (
                        <div style={{ fontSize: 11, color: 'var(--text3)', fontStyle: 'italic', marginTop: 2 }}>
                          {e.thesis_title}
                        </div>
                      )}
                    </td>
                    <td><span className="badge badge-blue" style={{ fontSize: 11 }}>{e.degree_level}</span></td>
                    <td className="text-muted">{e.institution || '—'}</td>
                    <td className="text-muted">{e.country || '—'}</td>
                    <td className="text-mono">
                      {e.start_year && e.end_year ? `${e.start_year}–${e.end_year}` : e.end_year || '—'}
                    </td>
                    <td className="text-mono">{e.grade_value != null ? `${e.grade_value} ${e.grade_type ? `(${e.grade_type})` : ''}` : '—'}</td>
                    <td>
                      {e.normalized_percentage != null ? (
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: gradeColor(e.normalized_percentage) }}>
                          {e.normalized_percentage}%
                        </span>
                      ) : <span style={{ color: 'var(--text3)' }}>—</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
