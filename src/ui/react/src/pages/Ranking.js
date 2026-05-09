import React, { useState } from 'react';
import { rankCandidates } from '../api';
import {
  Trophy, AlertCircle, RefreshCw, GraduationCap,
  FlaskConical, Briefcase, BookOpen, TrendingUp,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';

// ── Constants ─────────────────────────────────────────────────────────────────

const TIER_META = {
  prolific_researcher:    { label: 'Prolific',    badge: 'badge-green'  },
  established_researcher: { label: 'Established', badge: 'badge-blue'   },
  emerging_researcher:    { label: 'Emerging',    badge: 'badge-teal'   },
  early_stage_researcher: { label: 'Early-Stage', badge: 'badge-amber'  },
  no_research_output:     { label: 'No Research', badge: ''             },
};

const DIM_META = [
  { key: 'education',  label: 'Education',  icon: GraduationCap, color: 'var(--teal)'    },
  { key: 'research',   label: 'Research',   icon: FlaskConical,  color: 'var(--accent2)' },
  { key: 'experience', label: 'Experience', icon: Briefcase,     color: 'var(--accent)'  },
  { key: 'skills',     label: 'Skills',     icon: BookOpen,      color: 'var(--green)'   },
];

const RANK_COLORS = ['var(--amber)', 'var(--text3)', 'var(--accent2)'];

// ── Helpers ───────────────────────────────────────────────────────────────────

function Spinner() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '40px 0', color: 'var(--text3)', fontSize: 13 }}>
      <div style={{ width: 18, height: 18, border: '2px solid var(--border2)', borderTopColor: 'var(--accent)', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
      Running analysis on all candidates… this may take a moment.
    </div>
  );
}

function MiniBar({ score, color }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div className="progress-bar" style={{ width: 60, height: 5, flexShrink: 0 }}>
        <div className="progress-fill" style={{ width: `${Math.min(score, 100)}%`, background: color }} />
      </div>
      <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text3)' }}>{score}</span>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function RankingPage() {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  const runRanking = () => {
    setLoading(true);
    setError(null);
    rankCandidates()
      .then(d  => { setData(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  };

  const ranked    = data?.ranked_candidates || [];
  const aggregate = data?.aggregate         || {};
  const weights   = data?.weights_used      || {};
  const leaders   = aggregate.dimension_leaders || {};

  const scoreColor = (s) =>
    s >= 70 ? 'var(--green)' : s >= 45 ? 'var(--amber)' : 'var(--red)';

  const chartData = ranked.map(c => ({
    name:  (c.candidate_name || '').split(' ').slice(0, 2).join(' '),
    score: c.composite_score,
    fill:  scoreColor(c.composite_score),
  }));

  return (
    <div className="fade-up">
      <div className="page-header">
        <h1>Candidate Ranking</h1>
        <p className="subtitle">Multi-dimensional scoring across Education · Research · Experience · Skills</p>
      </div>

      {/* ── Trigger button ───────────────────────────────────────────────── */}
      <div className="card" style={{ marginBottom: 24, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>Run ranking across all candidates</div>
          <div style={{ fontSize: 12.5, color: 'var(--text3)' }}>
            Runs all analyzers on every processed candidate and produces a sorted leaderboard.
            {weights.education && (
              <span style={{ marginLeft: 8, fontFamily: 'var(--font-mono)' }}>
                Weights: edu {weights.education} · res {weights.research} · exp {weights.experience} · skills {weights.skills}
              </span>
            )}
          </div>
        </div>
        <button className="btn btn-primary" onClick={runRanking} disabled={loading}
          style={{ flexShrink: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
          {loading
            ? <><RefreshCw size={14} style={{ animation: 'spin 0.8s linear infinite' }} /> Running…</>
            : <><Trophy size={14} /> {data ? 'Re-run Ranking' : 'Run Ranking'}</>}
        </button>
      </div>

      {loading ? (
        <div className="card"><Spinner /></div>
      ) : error ? (
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--red)' }}>
          <AlertCircle size={18} /><span style={{ fontSize: 13 }}>{error}</span>
        </div>
      ) : !data ? null : ranked.length === 0 ? (
        <div className="card">
          <div className="empty-state"><Trophy size={32} /><h3>No candidates found</h3><p>Upload and process some CVs first</p></div>
        </div>
      ) : (
        <>
          {/* ── Aggregate stats ───────────────────────────────────────────── */}
          <div className="stat-grid" style={{ marginBottom: 20 }}>
            {[
              { label: 'Candidates Ranked', value: data.total_candidates,              color: 'var(--accent)'  },
              { label: 'Avg Composite',     value: aggregate.average_composite_score,  color: 'var(--teal)'    },
              { label: 'Highest Score',     value: aggregate.highest_score,            color: 'var(--green)'   },
              { label: 'Lowest Score',      value: aggregate.lowest_score,             color: 'var(--amber)'   },
            ].map(s => (
              <div key={s.label} className="stat-card" style={{ '--accent-color': s.color }}>
                <div className="stat-label">{s.label}</div>
                <div className="stat-value">{s.value}</div>
              </div>
            ))}
          </div>

          {/* ── Dimension leaders ─────────────────────────────────────────── */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
            {DIM_META.map(({ key, label, icon: Icon, color }) => {
              const leader = leaders[key];
              return (
                <div key={key} className="card" style={{ padding: '12px 14px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                    <Icon size={13} color={color} />
                    <span style={{ fontSize: 11.5, color: 'var(--text3)', fontFamily: 'var(--font-mono)' }}>{label} leader</span>
                  </div>
                  {leader ? (
                    <>
                      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginBottom: 4 }}>
                        {(leader.name || '').split(' ').slice(0, 2).join(' ')}
                      </div>
                      <div style={{ fontSize: 20, fontWeight: 700, color, fontFamily: 'var(--font-head)' }}>
                        {leader.score}
                      </div>
                    </>
                  ) : (
                    <div style={{ color: 'var(--text3)', fontSize: 12 }}>—</div>
                  )}
                </div>
              );
            })}
          </div>

          {/* ── Composite score bar chart ─────────────────────────────────── */}
          <div className="card" style={{ marginBottom: 20 }}>
            <div className="card-title">
              <TrendingUp size={13} style={{ display: 'inline', marginRight: 6 }} />
              Composite score overview
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData} margin={{ left: 0, right: 10, top: 4, bottom: 40 }}>
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'var(--text3)' }} angle={-35} textAnchor="end" interval={0} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: 'var(--text3)' }} />
                <Tooltip
                  formatter={(v) => [`${v} / 100`, 'Composite Score']}
                  contentStyle={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }}
                />
                <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* ── Leaderboard table ─────────────────────────────────────────── */}
          <div className="card">
            <div className="card-title">
              <Trophy size={13} style={{ display: 'inline', marginRight: 6 }} />
              Leaderboard
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: 50 }}>Rank</th>
                  <th>Candidate</th>
                  <th>Tier</th>
                  <th style={{ width: 90 }}>Score</th>
                  {DIM_META.map(d => <th key={d.key}>{d.label}</th>)}
                </tr>
              </thead>
              <tbody>
                {ranked.map((c, i) => {
                  const tier = TIER_META[c.profile_tier] || TIER_META.no_research_output;
                  const dim  = c.dimension_scores || {};
                  const sc   = c.composite_score;
                  const rankColor = RANK_COLORS[i] || 'var(--text3)';
                  return (
                    <tr key={c.candidate_id}>
                      <td>
                        <span style={{
                          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                          width: 28, height: 28, borderRadius: '50%',
                          background: i < 3 ? `${rankColor}20` : 'var(--bg3)',
                          color: i < 3 ? rankColor : 'var(--text3)',
                          fontWeight: 700, fontSize: 13, fontFamily: 'var(--font-head)',
                          border: i < 3 ? `1px solid ${rankColor}40` : '1px solid var(--border)',
                        }}>
                          {c.rank}
                        </span>
                      </td>
                      <td style={{ fontWeight: 500 }}>{c.candidate_name}</td>
                      <td><span className={`badge ${tier.badge}`} style={{ fontSize: 11 }}>{tier.label}</span></td>
                      <td>
                        <span style={{
                          fontFamily: 'var(--font-head)', fontWeight: 700, fontSize: 16,
                          color: scoreColor(sc),
                        }}>
                          {sc}
                        </span>
                        <span style={{ fontSize: 10.5, color: 'var(--text3)', fontFamily: 'var(--font-mono)' }}> /100</span>
                      </td>
                      {DIM_META.map(d => (
                        <td key={d.key}><MiniBar score={dim[d.key] ?? 0} color={d.color} /></td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
