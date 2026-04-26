import React, { useState } from 'react';
import { useApp } from '../AppContext';
import CandidateSelector from '../components/CandidateSelector';
import { FlaskConical, BookOpen, Users } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const QUARTILE_COLORS = { Q1: '#22c97a', Q2: '#4f7cff', Q3: '#f5a623', Q4: '#f05252' };

function AuthorBadge({ role }) {
  const cls = {
    'First Author':        'badge-green',
    'Corresponding Author':'badge-blue',
    'Co-Author':           'badge-teal',
  }[role] || 'badge-teal';
  return <span className={`badge ${cls}`}>{role || '—'}</span>;
}

export default function ResearchPage() {
  const { selectedCandidate: c } = useApp();
  const [tab, setTab] = useState('journals');

  const journals = c?.journal_publications || [];
  const confs    = c?.conference_publications || [];
  const allPubs  = [...journals, ...confs];

  const byYear = {};
  allPubs.forEach(p => { const y = p.publication_year || 'Unknown'; byYear[y] = (byYear[y] || 0) + 1; });
  const yearData = Object.entries(byYear).sort(([a],[b]) => a - b).map(([year, count]) => ({ year, count }));

  const authCounts = {};
  allPubs.forEach(p => { const r = p.author_role || 'Other'; authCounts[r] = (authCounts[r] || 0) + 1; });

  const withIF = journals.filter(p => p.impact_factor);
  const avgIF  = withIF.length
    ? (withIF.reduce((s, p) => s + parseFloat(p.impact_factor), 0) / withIF.length).toFixed(2)
    : '—';

  const coauthors = {};
  allPubs.forEach(p => {
    (p.authors || []).forEach(a => {
      const firstName = (c?.full_name || '').split(' ')[0]?.toLowerCase();
      if (!firstName || !a.toLowerCase().includes(firstName)) {
        coauthors[a] = (coauthors[a] || 0) + 1;
      }
    });
  });
  const topCoauthors = Object.entries(coauthors).sort(([,a],[,b]) => b - a).slice(0, 8);

  return (
    <div className="fade-up">
      <div className="page-header">
        <h1>Research Profile</h1>
        <p className="subtitle">Publications, impact factors, authorship roles and collaboration patterns</p>
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
      ) : (
        <>
          <div className="grid-4" style={{ marginBottom: 20 }}>
            {[
              { label: 'Journal Papers',    value: journals.length,                 color: 'var(--accent)' },
              { label: 'Conference Papers', value: confs.length,                    color: 'var(--teal)' },
              { label: 'Avg Impact Factor', value: avgIF,                           color: 'var(--green)' },
              { label: 'Unique Co-authors', value: Object.keys(coauthors).length,  color: 'var(--accent2)' },
            ].map(s => (
              <div key={s.label} className="stat-card" style={{ '--accent-color': s.color }}>
                <div className="stat-label">{s.label}</div>
                <div className="stat-value" style={{ fontSize: 22 }}>{s.value}</div>
              </div>
            ))}
          </div>

          <div className="grid-2" style={{ gap: 20, marginBottom: 20 }}>
            <div className="card">
              <div className="card-title">Publications by year</div>
              {yearData.length ? (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={yearData}>
                    <XAxis dataKey="year" tick={{ fontSize: 11, fill: 'var(--text3)' }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: 'var(--text3)' }} />
                    <Tooltip contentStyle={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }} />
                    <Bar dataKey="count" fill="var(--accent)" radius={[4,4,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : <div style={{ color: 'var(--text3)', fontSize: 13, padding: '20px 0' }}>No publication data.</div>}
            </div>

            <div className="card">
              <div className="card-title">Authorship breakdown</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 8 }}>
                {Object.entries(authCounts).map(([role, count]) => {
                  const pct = allPubs.length ? Math.round((count / allPubs.length) * 100) : 0;
                  return (
                    <div key={role}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <AuthorBadge role={role} />
                        <span style={{ fontSize: 12.5, fontFamily: 'var(--font-mono)', color: 'var(--text2)' }}>{count} ({pct}%)</span>
                      </div>
                      <div className="progress-bar" style={{ height: 5 }}>
                        <div className="progress-fill" style={{ width: `${pct}%`, background: 'var(--accent)' }} />
                      </div>
                    </div>
                  );
                })}
                {allPubs.length === 0 && <div style={{ color: 'var(--text3)', fontSize: 13 }}>No publications on record.</div>}
              </div>
            </div>
          </div>

          {topCoauthors.length > 0 && (
            <div className="card" style={{ marginBottom: 20 }}>
              <div className="card-title">Top collaborators</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {topCoauthors.map(([name, count]) => (
                  <div key={name} style={{
                    display: 'flex', alignItems: 'center', gap: 7,
                    padding: '5px 12px', background: 'var(--bg3)',
                    border: '1px solid var(--border)', borderRadius: 99, fontSize: 12.5
                  }}>
                    <Users size={11} color="var(--text3)" />
                    <span>{name}</span>
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent)', fontSize: 11 }}>×{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="tab-bar">
            <button className={`tab-btn${tab === 'journals' ? ' active' : ''}`} onClick={() => setTab('journals')}>
              <BookOpen size={13} /> Journal Papers ({journals.length})
            </button>
            <button className={`tab-btn${tab === 'conferences' ? ' active' : ''}`} onClick={() => setTab('conferences')}>
              <FlaskConical size={13} /> Conference Papers ({confs.length})
            </button>
          </div>

          {tab === 'journals' && (
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              {journals.length === 0 ? (
                <div className="empty-state"><BookOpen size={24} /><h3>No journal publications</h3></div>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr><th>Title</th><th>Journal</th><th>Year</th><th>IF</th><th>Quartile</th><th>WoS</th><th>Scopus</th><th>Role</th></tr>
                  </thead>
                  <tbody>
                    {journals.map((p, i) => (
                      <tr key={i}>
                        <td style={{ maxWidth: 260 }}>
                          <div style={{ fontWeight: 500, fontSize: 12.5, lineHeight: 1.4 }}>{p.title}</div>
                          <div className="text-muted" style={{ marginTop: 2, fontSize: 11.5 }}>{(p.authors || []).join(', ')}</div>
                        </td>
                        <td className="text-muted">{p.journal_name || '—'}</td>
                        <td className="text-mono">{p.publication_year || '—'}</td>
                        <td>
                          {p.impact_factor
                            ? <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--green)', fontSize: 12 }}>{p.impact_factor}</span>
                            : <span style={{ color: 'var(--text3)' }}>—</span>}
                        </td>
                        <td>
                          {p.quartile
                            ? <span className="badge" style={{ background: `${QUARTILE_COLORS[p.quartile]}18`, color: QUARTILE_COLORS[p.quartile], border: `1px solid ${QUARTILE_COLORS[p.quartile]}40` }}>{p.quartile}</span>
                            : <span style={{ color: 'var(--text3)', fontSize: 12 }}>—</span>}
                        </td>
                        <td>{p.is_wos_indexed === true ? <span className="badge badge-green">Yes</span> : p.is_wos_indexed === false ? <span className="badge badge-red">No</span> : <span style={{ color: 'var(--text3)', fontSize: 12 }}>—</span>}</td>
                        <td>{p.is_scopus_indexed === true ? <span className="badge badge-green">Yes</span> : p.is_scopus_indexed === false ? <span className="badge badge-red">No</span> : <span style={{ color: 'var(--text3)', fontSize: 12 }}>—</span>}</td>
                        <td><AuthorBadge role={p.author_role} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {tab === 'conferences' && (
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              {confs.length === 0 ? (
                <div className="empty-state"><FlaskConical size={24} /><h3>No conference publications</h3></div>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr><th>Title</th><th>Conference</th><th>Year</th><th>Rank</th><th>Indexed</th><th>Role</th></tr>
                  </thead>
                  <tbody>
                    {confs.map((p, i) => (
                      <tr key={i}>
                        <td style={{ maxWidth: 300 }}>
                          <div style={{ fontWeight: 500, fontSize: 12.5, lineHeight: 1.4 }}>{p.title}</div>
                        </td>
                        <td className="text-muted">{p.conference_name || '—'}</td>
                        <td className="text-mono">{p.publication_year || '—'}</td>
                        <td>{p.conference_rank ? <span className="badge badge-blue">{p.conference_rank}</span> : <span style={{ color: 'var(--text3)', fontSize: 12 }}>—</span>}</td>
                        <td>{p.is_indexed === true ? <span className="badge badge-green">Yes</span> : p.is_indexed === false ? <span className="badge badge-red">No</span> : <span style={{ color: 'var(--text3)', fontSize: 12 }}>—</span>}</td>
                        <td><AuthorBadge role={p.author_role} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}