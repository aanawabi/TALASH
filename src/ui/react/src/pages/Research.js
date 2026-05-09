import React, { useState, useEffect } from 'react';
import { useApp } from '../AppContext';
import CandidateSelector from '../components/CandidateSelector';
import { analyzeCandidate } from '../api';
import {
  FlaskConical, BookOpen, Users, Award, FileText,
  BarChart2, Network, Layers, ChevronRight, AlertCircle,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts';

// ── Colour maps ──────────────────────────────────────────────────────────────
const Q_COLORS = { Q1: '#22c97a', Q2: '#4f7cff', Q3: '#f5a623', Q4: '#f05252', Unranked: '#555f6e' };
const TIER_COLORS = {
  prolific_researcher:   '#22c97a',
  established_researcher:'#4f7cff',
  emerging_researcher:   '#f5a623',
  early_stage_researcher:'#14b8a6',
  no_research_output:    '#555f6e',
};
const STRENGTH_COLORS = {
  strongly_evidenced:  '#22c97a',
  partially_evidenced: '#4f7cff',
  weakly_evidenced:    '#f5a623',
  unsupported:         '#f05252',
};

// ── Small helpers ────────────────────────────────────────────────────────────
function AuthorBadge({ role }) {
  const cls = {
    'First Author':                  'badge-green',
    'First and Corresponding Author':'badge-green',
    'Corresponding Author':          'badge-blue',
    'Co-Author':                     'badge-teal',
  }[role] || 'badge-teal';
  return <span className={`badge ${cls}`}>{role || '—'}</span>;
}

function QBadge({ q }) {
  if (!q) return <span style={{ color: 'var(--text3)' }}>—</span>;
  const c = Q_COLORS[q] || '#888';
  return (
    <span className="badge" style={{ background: `${c}18`, color: c, border: `1px solid ${c}40` }}>
      {q}
    </span>
  );
}

function YesNo({ val }) {
  if (val === true)  return <span className="badge badge-green">Yes</span>;
  if (val === false) return <span className="badge badge-red">No</span>;
  return <span style={{ color: 'var(--text3)' }}>—</span>;
}

function QualityBadge({ label }) {
  if (!label) return null;
  const l = label.toLowerCase();
  const cls = l.includes('high') || l.includes('excellent') ? 'badge-green'
            : l.includes('very good') ? 'badge-teal'
            : l.includes('acceptable') || l.includes('moderate') ? 'badge-blue'
            : l.includes('low') || l.includes('predatory') ? 'badge-red'
            : 'badge-amber';
  return <span className={`badge ${cls}`} style={{ fontSize: 11, maxWidth: 200, whiteSpace: 'normal', lineHeight: 1.3, padding: '3px 8px' }}>{label}</span>;
}

function Spinner() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '40px 0', color: 'var(--text3)', fontSize: 13 }}>
      <div style={{ width: 18, height: 18, border: '2px solid var(--border2)', borderTopColor: 'var(--accent)', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
      Running analysis…
    </div>
  );
}

// ── Sub-sections ─────────────────────────────────────────────────────────────

function JournalsTab({ analyses }) {
  if (!analyses?.length) return <div className="empty-state"><BookOpen size={24} /><h3>No journal publications</h3></div>;
  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <table className="data-table">
        <thead>
          <tr>
            <th>Title / Authors</th><th>Journal</th><th>Year</th>
            <th>IF</th><th>Quartile</th><th>WoS</th><th>Scopus</th>
            <th>Role</th><th>Quality</th>
          </tr>
        </thead>
        <tbody>
          {analyses.map((p, i) => (
            <tr key={i}>
              <td style={{ maxWidth: 240 }}>
                <div style={{ fontWeight: 500, fontSize: 12.5, lineHeight: 1.4 }}>{p.title}</div>
                <div className="text-muted" style={{ marginTop: 2, fontSize: 11.5 }}>
                  {(p.authors || []).join(', ')}
                </div>
              </td>
              <td className="text-muted">{p.journal_name || '—'}</td>
              <td className="text-mono">{p.publication_year || '—'}</td>
              <td>
                {p.impact_factor
                  ? <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--green)', fontSize: 12 }}>{p.impact_factor}</span>
                  : <span style={{ color: 'var(--text3)' }}>—</span>}
              </td>
              <td><QBadge q={p.quartile} /></td>
              <td><YesNo val={p.wos_indexed} /></td>
              <td><YesNo val={p.scopus_indexed} /></td>
              <td><AuthorBadge role={p.author_role} /></td>
              <td><QualityBadge label={p.quality_label} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ConferencesTab({ analyses }) {
  if (!analyses?.length) return <div className="empty-state"><FlaskConical size={24} /><h3>No conference publications</h3></div>;
  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <table className="data-table">
        <thead>
          <tr>
            <th>Title</th><th>Conference</th><th>Year</th>
            <th>CORE Rank</th><th>A*</th><th>Maturity</th><th>Indexed</th>
            <th>Role</th><th>Quality</th>
          </tr>
        </thead>
        <tbody>
          {analyses.map((p, i) => (
            <tr key={i}>
              <td style={{ maxWidth: 260 }}>
                <div style={{ fontWeight: 500, fontSize: 12.5, lineHeight: 1.4 }}>{p.title}</div>
              </td>
              <td className="text-muted">{p.conference_name || '—'}</td>
              <td className="text-mono">{p.publication_year || '—'}</td>
              <td>
                {p.core_rank
                  ? <span className="badge badge-blue">{p.core_rank}</span>
                  : <span style={{ color: 'var(--text3)' }}>—</span>}
              </td>
              <td><YesNo val={p.is_a_star} /></td>
              <td className="text-muted" style={{ fontSize: 11.5 }}>{p.maturity_label || '—'}</td>
              <td><YesNo val={p.is_indexed} /></td>
              <td><AuthorBadge role={p.author_role} /></td>
              <td><QualityBadge label={p.quality_label} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SupervisionTab({ supervision }) {
  if (!supervision) return null;
  const papers = supervision.paper_details_with_students || [];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="stat-grid">
        {[
          { label: 'PhD (Main Supervisor)',   value: supervision.phd_main_supervisor  ?? '—', color: 'var(--accent)' },
          { label: 'PhD (Co-Supervisor)',      value: supervision.phd_co_supervisor   ?? '—', color: 'var(--teal)' },
          { label: 'MS (Main Supervisor)',     value: supervision.ms_main_supervisor  ?? '—', color: 'var(--green)' },
          { label: 'MS (Co-Supervisor)',       value: supervision.ms_co_supervisor    ?? '—', color: 'var(--accent2)' },
        ].map(s => (
          <div key={s.label} className="stat-card" style={{ '--accent-color': s.color }}>
            <div className="stat-label">{s.label}</div>
            <div className="stat-value">{s.value}</div>
          </div>
        ))}
      </div>
      <div className="card">
        <div className="card-title">Papers co-authored with supervised students</div>
        <div style={{ color: 'var(--text2)', fontSize: 13, marginBottom: 12 }}>
          {supervision.papers_with_students ?? 0} paper(s) &nbsp;·&nbsp;
          {supervision.corresponding_on_student_papers ?? 0} as corresponding author
        </div>
        {papers.length > 0 ? (
          <table className="data-table">
            <thead><tr><th>Title</th><th>Year</th><th>Student Authors</th><th>Candidate Pattern</th></tr></thead>
            <tbody>
              {papers.map((p, i) => (
                <tr key={i}>
                  <td style={{ maxWidth: 280, fontSize: 12.5 }}>{p.title}</td>
                  <td className="text-mono">{p.year || '—'}</td>
                  <td className="text-muted">{(p.student_authors || []).join(', ')}</td>
                  <td><span className="badge badge-purple">{p.authorship_pattern || '—'}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={{ color: 'var(--text3)', fontSize: 13 }}>No co-authored papers with students found.</div>
        )}
      </div>
    </div>
  );
}

function BooksPanentsTab({ books, patents }) {
  const bookList    = books?.book_details   || [];
  const patentList  = patents?.patent_details || [];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div className="card">
        <div className="card-title">Books ({books?.total_books ?? 0})</div>
        {bookList.length === 0
          ? <div style={{ color: 'var(--text3)', fontSize: 13 }}>No books recorded.</div>
          : (
            <table className="data-table">
              <thead><tr><th>Title</th><th>Publisher</th><th>Year</th><th>ISBN</th><th>Role</th><th>Credibility</th></tr></thead>
              <tbody>
                {bookList.map((b, i) => (
                  <tr key={i}>
                    <td style={{ maxWidth: 240 }}>
                      <div style={{ fontWeight: 500, fontSize: 12.5 }}>{b.book_title}</div>
                      <div className="text-muted" style={{ fontSize: 11.5 }}>{(b.authors || []).join(', ')}</div>
                    </td>
                    <td className="text-muted">{b.publisher || '—'}</td>
                    <td className="text-mono">{b.publication_year || '—'}</td>
                    <td className="text-mono" style={{ fontSize: 11.5 }}>{b.isbn || '—'}</td>
                    <td><span className="badge badge-purple">{b.authorship_role || '—'}</span></td>
                    <td>
                      <span className={`badge ${b.is_reputable_publisher ? 'badge-green' : 'badge-amber'}`} style={{ fontSize: 10.5, whiteSpace: 'normal', lineHeight: 1.3 }}>
                        {b.is_reputable_publisher ? 'Reputable publisher' : 'Unconfirmed publisher'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
      </div>

      <div className="card">
        <div className="card-title">Patents ({patents?.total_patents ?? 0})</div>
        <div style={{ display: 'flex', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 12.5, color: 'var(--text2)' }}>
            Granted: <strong style={{ color: 'var(--green)' }}>{patents?.granted_patents ?? 0}</strong>
          </span>
          <span style={{ fontSize: 12.5, color: 'var(--text2)' }}>
            Filed/Pending: <strong style={{ color: 'var(--amber)' }}>{patents?.filed_patents ?? 0}</strong>
          </span>
          <span style={{ fontSize: 12.5, color: 'var(--text2)' }}>
            Innovation profile: <strong style={{ color: 'var(--text)' }}>{patents?.innovation_profile || '—'}</strong>
          </span>
        </div>
        {patentList.length === 0
          ? <div style={{ color: 'var(--text3)', fontSize: 13 }}>No patents recorded.</div>
          : (
            <table className="data-table">
              <thead><tr><th>Title</th><th>Number</th><th>Country</th><th>Status</th><th>Role</th><th>Credibility</th></tr></thead>
              <tbody>
                {patentList.map((p, i) => (
                  <tr key={i}>
                    <td style={{ maxWidth: 240 }}>
                      <div style={{ fontWeight: 500, fontSize: 12.5 }}>{p.patent_title}</div>
                      <div className="text-muted" style={{ fontSize: 11.5 }}>{(p.inventors || []).join(', ')}</div>
                    </td>
                    <td className="text-mono" style={{ fontSize: 11.5 }}>{p.patent_number || '—'}</td>
                    <td className="text-muted">{p.country || '—'}</td>
                    <td>
                      <span className={`badge ${p.status?.toLowerCase().includes('grant') ? 'badge-green' : 'badge-amber'}`}>
                        {p.status || '—'}
                      </span>
                    </td>
                    <td><span className="badge badge-purple">{p.inventor_role || '—'}</span></td>
                    <td style={{ fontSize: 11.5, color: 'var(--text3)', maxWidth: 180 }}>{p.credibility}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
      </div>
    </div>
  );
}

function TopicsTab({ topicAnalysis }) {
  if (!topicAnalysis) return null;
  const dist = topicAnalysis.theme_distribution || {};
  const themes = Object.entries(dist).slice(0, 10);
  const totalPubs = topicAnalysis.total_publications_analyzed || 0;
  const trendData = Object.entries(topicAnalysis.topic_trend_by_year || {})
    .sort(([a], [b]) => Number(a) - Number(b))
    .map(([year, themes]) => ({ year, ...themes }));

  const labelColors = {
    'Highly Focused':      'var(--green)',
    'Moderately Focused':  'var(--accent)',
    'Interdisciplinary':   'var(--teal)',
    'Highly Diverse':      'var(--accent2)',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="stat-grid">
        {[
          { label: 'Publications Analysed', value: totalPubs,                              color: 'var(--accent)' },
          { label: 'Research Themes',        value: topicAnalysis.theme_count ?? '—',      color: 'var(--teal)' },
          { label: 'Diversity Score',        value: topicAnalysis.diversity_score ?? '—',  color: 'var(--accent2)' },
          { label: 'Focus Shifted',          value: topicAnalysis.focus_shifted_over_time ? 'Yes' : 'No', color: 'var(--amber)' },
        ].map(s => (
          <div key={s.label} className="stat-card" style={{ '--accent-color': s.color }}>
            <div className="stat-label">{s.label}</div>
            <div className="stat-value" style={{ fontSize: 22 }}>{s.value}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-title">Variability label</div>
        <span className="badge" style={{
          fontSize: 13, padding: '5px 14px',
          background: `${labelColors[topicAnalysis.variability_label] || 'var(--accent)'}18`,
          color: labelColors[topicAnalysis.variability_label] || 'var(--accent)',
          border: `1px solid ${labelColors[topicAnalysis.variability_label] || 'var(--accent)'}40`,
        }}>
          {topicAnalysis.variability_label}
        </span>
        {topicAnalysis.interpretation && (
          <p style={{ marginTop: 12, fontSize: 13, color: 'var(--text2)', lineHeight: 1.7 }}>
            {topicAnalysis.interpretation}
          </p>
        )}
      </div>

      {themes.length > 0 && (
        <div className="card">
          <div className="card-title">Theme distribution</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {themes.map(([theme, data]) => (
              <div key={theme}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 12.5, color: 'var(--text)' }}>{theme}</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text2)' }}>
                    {data.count} pubs &nbsp;({data.percentage}%)
                  </span>
                </div>
                <div className="progress-bar" style={{ height: 6 }}>
                  <div className="progress-fill" style={{ width: `${data.percentage}%`, background: 'var(--accent)' }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {trendData.length >= 2 && (
        <div className="card">
          <div className="card-title">Topic trend by year</div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={trendData}>
              <XAxis dataKey="year" tick={{ fontSize: 11, fill: 'var(--text3)' }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: 'var(--text3)' }} />
              <Tooltip contentStyle={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }} />
              {Object.keys(topicAnalysis.topic_trend_by_year?.[Object.keys(topicAnalysis.topic_trend_by_year || {})[0]] || {})
                .slice(0, 5)
                .map((theme, idx) => {
                  const colors = ['var(--accent)', 'var(--green)', 'var(--teal)', 'var(--accent2)', 'var(--amber)'];
                  return <Bar key={theme} dataKey={theme} stackId="a" fill={colors[idx % colors.length]} radius={idx === 0 ? [0,0,4,4] : [0,0,0,0]} />;
                })}
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

function CoauthorTab({ coauthorAnalysis }) {
  if (!coauthorAnalysis) return null;
  const topCollabs = coauthorAnalysis.most_frequent_collaborators || [];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="stat-grid">
        {[
          { label: 'Unique Co-authors',    value: coauthorAnalysis.total_unique_coauthors         ?? '—', color: 'var(--accent)' },
          { label: 'Recurring Collaborators', value: coauthorAnalysis.recurring_collaborators_count ?? '—', color: 'var(--green)' },
          { label: 'Avg Authors / Paper',  value: coauthorAnalysis.average_authors_per_paper       ?? '—', color: 'var(--teal)' },
          { label: 'Diversity Score',      value: coauthorAnalysis.collaboration_diversity_score   ?? '—', color: 'var(--accent2)' },
        ].map(s => (
          <div key={s.label} className="stat-card" style={{ '--accent-color': s.color }}>
            <div className="stat-label">{s.label}</div>
            <div className="stat-value" style={{ fontSize: 22 }}>{s.value}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-title">Collaboration profile</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, marginBottom: 10 }}>
          <span style={{ fontSize: 13, color: 'var(--text2)' }}>
            Team size: <strong style={{ color: 'var(--text)' }}>{coauthorAnalysis.avg_team_size_label}</strong>
          </span>
          <span style={{ fontSize: 13, color: 'var(--text2)' }}>
            Papers with recurring collaborators: <strong style={{ color: 'var(--text)' }}>
              {((coauthorAnalysis.proportion_papers_with_recurring || 0) * 100).toFixed(0)}%
            </strong>
          </span>
          {coauthorAnalysis.student_supervisor_papers > 0 && (
            <span style={{ fontSize: 13, color: 'var(--text2)' }}>
              Student co-authored papers: <strong style={{ color: 'var(--green)' }}>{coauthorAnalysis.student_supervisor_papers}</strong>
            </span>
          )}
        </div>
        {coauthorAnalysis.interpretation && (
          <p style={{ fontSize: 13, color: 'var(--text2)', lineHeight: 1.7, marginTop: 8 }}>
            {coauthorAnalysis.interpretation}
          </p>
        )}
      </div>

      {topCollabs.length > 0 && (
        <div className="card">
          <div className="card-title">Most frequent collaborators</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {topCollabs.map((c, i) => {
              const pct = topCollabs[0]?.papers ? Math.round((c.papers / topCollabs[0].papers) * 100) : 0;
              return (
                <div key={i}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: 13 }}>{c.name}</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text2)' }}>{c.papers} paper(s)</span>
                  </div>
                  <div className="progress-bar" style={{ height: 5 }}>
                    <div className="progress-fill" style={{ width: `${pct}%`, background: 'var(--teal)' }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function ResearchPage() {
  const { selectedCandidate: c } = useApp();
  const [tab, setTab]             = useState('journals');
  const [analysis, setAnalysis]   = useState(null);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState(null);

  useEffect(() => {
    if (!c?.candidate_id) { setAnalysis(null); return; }
    setLoading(true);
    setError(null);
    analyzeCandidate(c.candidate_id)
      .then(data => { setAnalysis(data); setLoading(false); })
      .catch(e  => { setError(e.message); setLoading(false); });
  }, [c?.candidate_id]);

  const res  = analysis?.res_analysis   || {};
  const top  = analysis?.topic_analysis || null;
  const coau = analysis?.coauthor_analysis || null;

  const journalAnalyses    = res.journal_analyses    || [];
  const conferenceAnalyses = res.conference_analyses || [];
  const qDist = res.quartile_distribution || {};
  const qPieData = Object.entries(qDist)
    .filter(([, v]) => v > 0)
    .map(([name, value]) => ({ name, value }));

  const tierLabel = (res.profile_tier || '').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

  const TABS = [
    { id: 'journals',     label: `Journal Papers (${journalAnalyses.length})`,     icon: BookOpen },
    { id: 'conferences',  label: `Conference Papers (${conferenceAnalyses.length})`,icon: FlaskConical },
    { id: 'supervision',  label: 'Supervision',                                     icon: Users },
    { id: 'books_patents',label: 'Books & Patents',                                 icon: Award },
    { id: 'topics',       label: 'Topic Variability',                               icon: Layers },
    { id: 'coauthors',    label: 'Co-Author Network',                               icon: Network },
  ];

  return (
    <div className="fade-up">
      <div className="page-header">
        <h1>Research Profile</h1>
        <p className="subtitle">
          Verified publication quality · supervision · topic variability · collaboration network
        </p>
      </div>

      <CandidateSelector />

      {!c ? (
        <div className="card">
          <div className="empty-state">
            <FlaskConical size={32} />
            <h3>Select a candidate</h3>
            <p>Choose a candidate above to view their research profile</p>
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
              { label: 'Total Publications',   value: res.total_publications   ?? '—', color: 'var(--accent)' },
              { label: 'Research Impact Score',value: res.research_impact_score ?? '—', color: 'var(--green)' },
              { label: 'Q1 / Q2 Publications', value: res.high_impact_count    ?? '—', color: 'var(--teal)' },
              { label: 'Profile Tier',          value: tierLabel || '—',               color: TIER_COLORS[res.profile_tier] || 'var(--text2)', small: true },
            ].map(s => (
              <div key={s.label} className="stat-card" style={{ '--accent-color': s.color }}>
                <div className="stat-label">{s.label}</div>
                <div className="stat-value" style={{ fontSize: s.small ? 14 : 28 }}>{s.value}</div>
              </div>
            ))}
          </div>

          {/* ── Overview charts ───────────────────────────────────────────── */}
          <div className="grid-2" style={{ gap: 20, display: 'grid', gridTemplateColumns: '1fr 1fr', marginBottom: 20 }}>
            <div className="card">
              <div className="card-title">Publications by year</div>
              {Object.keys(res.publications_by_year || {}).length ? (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={
                    Object.entries(res.publications_by_year).sort(([a],[b]) => a-b)
                      .map(([year, count]) => ({ year, count }))
                  }>
                    <XAxis dataKey="year" tick={{ fontSize: 11, fill: 'var(--text3)' }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: 'var(--text3)' }} />
                    <Tooltip contentStyle={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }} />
                    <Bar dataKey="count" fill="var(--accent)" radius={[4,4,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : <div style={{ color: 'var(--text3)', fontSize: 13, padding: '20px 0' }}>No publication data.</div>}
            </div>

            <div className="card">
              <div className="card-title">Quartile distribution (journals)</div>
              {qPieData.length ? (
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={qPieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} label={({ name, value }) => `${name}: ${value}`} labelLine={false} fontSize={11}>
                      {qPieData.map((entry, i) => (
                        <Cell key={i} fill={Q_COLORS[entry.name] || '#888'} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }} />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                  </PieChart>
                </ResponsiveContainer>
              ) : <div style={{ color: 'var(--text3)', fontSize: 13, padding: '20px 0' }}>No journal data.</div>}
            </div>
          </div>

          {/* ── WoS / Scopus / IF summary ──────────────────────────────────── */}
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 20 }}>
            {[
              { label: 'WoS Indexed',     value: res.wos_indexed_count    ?? 0, color: 'var(--green)' },
              { label: 'Scopus Indexed',  value: res.scopus_indexed_count  ?? 0, color: 'var(--teal)' },
              { label: 'Avg Impact Factor', value: res.average_impact_factor ?? '—', color: 'var(--amber)' },
              { label: 'A* Conferences',  value: res.astar_conference_count ?? 0, color: 'var(--accent2)' },
              { label: 'PhD Supervised',  value: res.phd_supervised        ?? 0, color: 'var(--accent)' },
              { label: 'MS Supervised',   value: res.ms_supervised         ?? 0, color: 'var(--accent)' },
              { label: 'Granted Patents', value: res.granted_patents        ?? 0, color: 'var(--green)' },
              { label: 'Books',           value: res.total_books            ?? 0, color: 'var(--accent2)' },
            ].map(s => (
              <div key={s.label} style={{
                padding: '8px 14px', background: 'var(--bg2)', border: '1px solid var(--border)',
                borderRadius: 8, minWidth: 100, textAlign: 'center'
              }}>
                <div style={{ fontSize: 11, color: 'var(--text3)', fontFamily: 'var(--font-mono)', marginBottom: 3 }}>{s.label}</div>
                <div style={{ fontFamily: 'var(--font-head)', fontSize: 18, fontWeight: 700, color: s.color }}>{s.value}</div>
              </div>
            ))}
          </div>

          {/* ── Tabs ──────────────────────────────────────────────────────── */}
          <div className="tab-bar">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button key={id} className={`tab-btn${tab === id ? ' active' : ''}`} onClick={() => setTab(id)}>
                <Icon size={13} /> {label}
              </button>
            ))}
          </div>

          {tab === 'journals'     && <JournalsTab     analyses={journalAnalyses} />}
          {tab === 'conferences'  && <ConferencesTab  analyses={conferenceAnalyses} />}
          {tab === 'supervision'  && <SupervisionTab  supervision={res.supervision} />}
          {tab === 'books_patents'&& <BooksPanentsTab books={res.books} patents={res.patents} />}
          {tab === 'topics'       && <TopicsTab       topicAnalysis={top} />}
          {tab === 'coauthors'    && <CoauthorTab     coauthorAnalysis={coau} />}
        </>
      )}

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
