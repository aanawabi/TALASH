import React from 'react';
import { useApp } from '../AppContext';
import CandidateSelector from '../components/CandidateSelector';
import { GraduationCap, AlertTriangle, CheckCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const DEGREE_ORDER = ['SSC','HSSC','Bachelor (16-year)','Master (16-year)','PhD'];
const DEGREE_COLORS = {
  'SSC': 'var(--teal)', 'HSSC': 'var(--teal)',
  'Bachelor (16-year)': 'var(--accent)',
  'Master (16-year)': 'var(--accent2)',
  'PhD': 'var(--green)',
};

function normalizeGrade(edu) {
  if (!edu.grade_value) return null;
  if (edu.grade_type?.includes('CGPA')) {
    return { display: `${edu.grade_value} / 4.0`, pct: (parseFloat(edu.grade_value) / 4) * 100 };
  }
  if (edu.grade_type === 'Percentage' || edu.normalized_percentage) {
    const pct = edu.normalized_percentage || parseFloat(edu.grade_value);
    return { display: `${pct}%`, pct };
  }
  return { display: edu.grade_value, pct: null };
}

function GradeBar({ label, edu }) {
  const g = normalizeGrade(edu);
  if (!g) return null;
  const pct = g.pct || 0;
  const color = pct >= 75 ? 'var(--green)' : pct >= 55 ? 'var(--amber)' : 'var(--red)';
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
        <span style={{ fontSize: 12.5, color: 'var(--text2)' }}>{label}</span>
        <span style={{ fontSize: 12.5, fontFamily: 'var(--font-mono)', color }}>{g.display}</span>
      </div>
      <div className="progress-bar" style={{ height: 5 }}>
        <div className="progress-fill" style={{ width: `${Math.min(pct, 100)}%`, background: color }} />
      </div>
    </div>
  );
}

function detectGaps(education) {
  const sorted = [...education].filter(e => e.end_year).sort((a, b) => a.end_year - b.end_year);
  const gaps = [];
  for (let i = 1; i < sorted.length; i++) {
    const gap = (sorted[i].start_year || sorted[i].end_year) - sorted[i - 1].end_year;
    if (gap > 1) gaps.push({ from: sorted[i-1].degree_level, to: sorted[i].degree_level, years: gap });
  }
  return gaps;
}

export default function EducationPage() {
  const { selectedCandidate: c } = useApp();
  const edu = c?.education || [];
  const sorted = [...edu].sort((a, b) =>
    DEGREE_ORDER.indexOf(a.degree_level) - DEGREE_ORDER.indexOf(b.degree_level));

  const chartData = sorted.map(e => {
    const g = normalizeGrade(e);
    return g?.pct ? { name: e.degree_level.replace(' (16-year)', ''), grade: Math.round(g.pct), raw: g.display } : null;
  }).filter(Boolean);

  const gaps = edu.length ? detectGaps(edu) : [];
  const highestDeg = sorted[sorted.length - 1];

  return (
    <div className="fade-up">
      <div className="page-header">
        <h1>Education Analysis</h1>
        <p className="subtitle">Academic progression, grades, institutional quality and gap detection</p>
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
      ) : (
        <>
          <div className="grid-4" style={{ marginBottom: 20 }}>
            {[
              { label: 'Highest Degree',  value: highestDeg?.degree_level || '—',                                    color: 'var(--green)' },
              { label: 'Degrees on File', value: edu.length,                                                          color: 'var(--accent)' },
              { label: 'PhD CGPA',        value: edu.find(e=>e.degree_level==='PhD')?.grade_value ? `${edu.find(e=>e.degree_level==='PhD').grade_value}/4.0` : '—', color: 'var(--teal)' },
              { label: 'Edu Gaps',        value: gaps.length,                                                         color: gaps.length ? 'var(--amber)' : 'var(--green)' },
            ].map(s => (
              <div key={s.label} className="stat-card" style={{ '--accent-color': s.color }}>
                <div className="stat-label">{s.label}</div>
                <div className="stat-value" style={{ fontSize: 22 }}>{s.value}</div>
              </div>
            ))}
          </div>

          <div className="grid-2" style={{ gap: 20, marginBottom: 20 }}>
            <div className="card">
              <div className="card-title">Degree timeline</div>
              <div className="timeline">
                {sorted.map((e, i) => {
                  const g = normalizeGrade(e);
                  const color = DEGREE_COLORS[e.degree_level] || 'var(--accent)';
                  return (
                    <div key={i} className="timeline-item">
                      <div className="timeline-dot" style={{ background: color }} />
                      <div>
                        <div style={{ fontWeight: 500, fontSize: 13.5 }}>{e.degree_title}</div>
                        <div style={{ fontSize: 12, color: 'var(--text2)', margin: '2px 0' }}>
                          {e.institution || e.board || '—'}
                        </div>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 4 }}>
                          {e.end_year    && <span className="badge badge-blue">{e.end_year}</span>}
                          {e.specialization && <span className="badge badge-teal">{e.specialization}</span>}
                          {g             && <span className="badge badge-purple">{g.display}</span>}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="card">
              <div className="card-title">Grade progression</div>
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                    <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'var(--text3)' }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: 'var(--text3)' }} unit="%" />
                    <Tooltip
                      contentStyle={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }}
                      formatter={(val, name, props) => [props.payload.raw, 'Grade']}
                    />
                    <Bar dataKey="grade" radius={[4, 4, 0, 0]}>
                      {chartData.map((entry, i) => (
                        <Cell key={i} fill={entry.grade >= 75 ? '#22c97a' : entry.grade >= 55 ? '#f5a623' : '#f05252'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div style={{ color: 'var(--text3)', fontSize: 13, padding: '20px 0' }}>No grade data to chart.</div>
              )}
              <div style={{ marginTop: 16 }}>
                {sorted.map((e, i) => (
                  <GradeBar key={i} label={e.degree_level.replace(' (16-year)', '')} edu={e} />
                ))}
              </div>
            </div>
          </div>

          <div className="card" style={{ marginBottom: 20 }}>
            <div className="card-title">Gap detection</div>
            {gaps.length === 0 ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--green)', fontSize: 13 }}>
                <CheckCircle size={15} /> No significant gaps detected.
              </div>
            ) : gaps.map((g, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '10px 14px', background: 'rgba(245,166,35,0.06)',
                border: '1px solid rgba(245,166,35,0.2)', borderRadius: 'var(--radius)', marginBottom: 8, fontSize: 13
              }}>
                <AlertTriangle size={14} color="var(--amber)" />
                <span style={{ color: 'var(--text2)' }}>
                  <strong style={{ color: 'var(--text)' }}>{g.years}-year gap</strong> between <em>{g.from}</em> and <em>{g.to}</em>
                </span>
                <span className="badge badge-amber" style={{ marginLeft: 'auto' }}>{g.years} yr{g.years !== 1 ? 's' : ''}</span>
              </div>
            ))}
          </div>

          <div className="section-divider"><span>All education records</span></div>
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <table className="data-table">
              <thead>
                <tr><th>Degree</th><th>Level</th><th>Institution</th><th>Year</th><th>Grade</th><th>Grade Type</th></tr>
              </thead>
              <tbody>
                {sorted.map((e, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 500 }}>{e.degree_title}</td>
                    <td><span className="badge badge-blue">{e.degree_level}</span></td>
                    <td className="text-muted">{e.institution || e.board || '—'}</td>
                    <td className="text-mono">{e.end_year || '—'}</td>
                    <td className="text-mono">{e.grade_value || '—'}</td>
                    <td className="text-muted">{e.grade_type || '—'}</td>
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