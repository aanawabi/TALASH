import React, { useState, useEffect } from 'react';
import { useApp } from '../AppContext';
import CandidateSelector from '../components/CandidateSelector';
import { analyzeCandidate } from '../api';
import {
  FileText, GraduationCap, Briefcase, FlaskConical,
  Star, AlertCircle, Sparkles, RefreshCw,
} from 'lucide-react';

// ── Helpers ──────────────────────────────────────────────────────────────────

function Spinner({ label = 'Running analysis…' }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '40px 0', color: 'var(--text3)', fontSize: 13 }}>
      <div style={{ width: 18, height: 18, border: '2px solid var(--border2)', borderTopColor: 'var(--accent)', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
      {label}
    </div>
  );
}

function ScoreBar({ label, score, max = 100, color = 'var(--accent)' }) {
  const pct = Math.min((score / max) * 100, 100);
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
        <span style={{ fontSize: 12.5, color: 'var(--text2)' }}>{label}</span>
        <span style={{ fontSize: 12.5, fontFamily: 'var(--font-mono)', color }}>{score} / {max}</span>
      </div>
      <div className="progress-bar" style={{ height: 6 }}>
        <div className="progress-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

const TIER_META = {
  prolific_researcher:    { label: 'Prolific Researcher',    color: 'var(--green)',   badge: 'badge-green'  },
  established_researcher: { label: 'Established Researcher', color: 'var(--accent)',  badge: 'badge-blue'   },
  emerging_researcher:    { label: 'Emerging Researcher',    color: 'var(--teal)',    badge: 'badge-teal'   },
  early_stage_researcher: { label: 'Early-Stage Researcher', color: 'var(--amber)',   badge: 'badge-amber'  },
  no_research_output:     { label: 'No Research Output',     color: 'var(--text3)',   badge: ''             },
};

// ── Main component ────────────────────────────────────────────────────────────
export default function SummaryPage() {
  const { selectedCandidate: c } = useApp();
  const [analysis, setAnalysis]       = useState(null);
  const [analysisLoading, setALoading]= useState(false);
  const [analysisError, setAError]    = useState(null);
  const [narrative, setNarrative]     = useState(null);
  const [narLoading, setNarLoading]   = useState(false);
  const [narError, setNarError]       = useState(null);

  // Load base analysis (no LLM summary) on candidate change
  useEffect(() => {
    if (!c?.candidate_id) { setAnalysis(null); setNarrative(null); return; }
    setALoading(true);
    setAError(null);
    setNarrative(null);
    analyzeCandidate(c.candidate_id, false)
      .then(data => { setAnalysis(data); setALoading(false); })
      .catch(e  => { setAError(e.message); setALoading(false); });
  }, [c?.candidate_id]);

  // Separately trigger LLM narrative on demand
  const generateNarrative = () => {
    if (!c?.candidate_id) return;
    setNarLoading(true);
    setNarError(null);
    analyzeCandidate(c.candidate_id, true)
      .then(data => { setNarrative(data.summary?.narrative || null); setNarLoading(false); })
      .catch(e  => { setNarError(e.message); setNarLoading(false); });
  };

  const edu  = analysis?.edu_analysis || {};
  const exp  = analysis?.exp_analysis || {};
  const res  = analysis?.res_analysis || {};
  const rank = analysis?.rank_result  || {};
  const dim  = rank.dimension_scores  || {};

  const tierMeta = TIER_META[res.profile_tier] || TIER_META.no_research_output;
  const compositeScore = rank.composite_score ?? null;
  const scoreColor = compositeScore >= 70 ? 'var(--green)' : compositeScore >= 45 ? 'var(--amber)' : 'var(--red)';

  const topDeg     = c?.education?.find(e => e.degree_level === 'PhD')
                  || c?.education?.find(e => e.degree_level?.includes('Master'))
                  || c?.education?.[0];
  const currentJob = c?.experience?.find(e => e.is_current);
  const pubs       = (c?.journal_publications?.length || 0) + (c?.conference_publications?.length || 0);

  return (
    <div className="fade-up">
      <div className="page-header">
        <h1>Candidate Summary</h1>
        <p className="subtitle">Overall profile assessment, ranking scores and AI-generated narrative</p>
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
      ) : analysisLoading ? (
        <div className="card"><Spinner /></div>
      ) : analysisError ? (
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--red)' }}>
          <AlertCircle size={18} /><span style={{ fontSize: 13 }}>{analysisError}</span>
        </div>
      ) : (
        <>
          {/* ── Candidate header ───────────────────────────────────────────── */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24, padding: '16px 20px', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)' }}>
            <div style={{
              width: 54, height: 54, borderRadius: '50%', flexShrink: 0,
              background: 'rgba(79,124,255,0.15)', border: '1px solid rgba(79,124,255,0.3)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontFamily: 'var(--font-head)', fontSize: 18, fontWeight: 700, color: 'var(--accent)',
            }}>
              {(c.full_name || '?').split(' ').slice(0, 2).map(w => w[0]).join('')}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontFamily: 'var(--font-head)', fontSize: 18, fontWeight: 700 }}>{c.full_name}</div>
              <div style={{ fontSize: 12.5, color: 'var(--text3)', marginTop: 3 }}>
                {edu.highest_degree || topDeg?.degree_level || '—'}
                {edu.highest_degree_institution ? ` · ${edu.highest_degree_institution}` : ''}
                {exp.current_position ? ` · ${exp.current_position}` : ''}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
              <span className={`badge ${tierMeta.badge}`} style={{ fontSize: 12 }}>
                <Star size={11} /> {tierMeta.label}
              </span>
              {compositeScore != null && (
                <span className="badge" style={{ fontSize: 12, background: `${scoreColor}18`, color: scoreColor, border: `1px solid ${scoreColor}40` }}>
                  Score: {compositeScore} / 100
                </span>
              )}
            </div>
          </div>

          {/* ── Score breakdown + Key facts ───────────────────────────────── */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
            <div className="card">
              <div className="card-title">Ranking scores</div>
              {compositeScore != null ? (
                <>
                  <div style={{ textAlign: 'center', marginBottom: 20 }}>
                    <div style={{
                      width: 90, height: 90, borderRadius: '50%',
                      border: `3px solid ${scoreColor}`,
                      display: 'flex', flexDirection: 'column',
                      alignItems: 'center', justifyContent: 'center', margin: '0 auto',
                    }}>
                      <div style={{ fontFamily: 'var(--font-head)', fontSize: 26, fontWeight: 700, color: scoreColor }}>
                        {compositeScore}
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--text3)', fontFamily: 'var(--font-mono)' }}>/ 100</div>
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text3)', marginTop: 8 }}>Composite score</div>
                  </div>
                  <ScoreBar label="Education"  score={dim.education  ?? 0} color="var(--teal)"    />
                  <ScoreBar label="Research"   score={dim.research   ?? 0} color="var(--accent2)" />
                  <ScoreBar label="Experience" score={dim.experience ?? 0} color="var(--accent)"  />
                  <ScoreBar label="Skills"     score={dim.skills     ?? 0} color="var(--green)"   />
                  {rank.weights_used && (
                    <div style={{ marginTop: 12, fontSize: 11.5, color: 'var(--text3)', fontFamily: 'var(--font-mono)', lineHeight: 1.6 }}>
                      Weights: edu {rank.weights_used.education} · res {rank.weights_used.research} · exp {rank.weights_used.experience} · skills {rank.weights_used.skills}
                    </div>
                  )}
                </>
              ) : (
                <div style={{ color: 'var(--text3)', fontSize: 13 }}>Score unavailable.</div>
              )}
            </div>

            <div className="card">
              <div className="card-title">Key profile facts</div>
              {[
                { icon: GraduationCap, label: 'Highest Degree',    value: edu.highest_degree_title || edu.highest_degree || topDeg?.degree_title || '—',  color: 'var(--teal)' },
                { icon: GraduationCap, label: 'Institution',       value: edu.highest_degree_institution || topDeg?.institution || '—',                    color: 'var(--teal)' },
                { icon: GraduationCap, label: 'Avg Grade',         value: edu.average_percentage != null ? `${edu.average_percentage}%` : '—',             color: 'var(--teal)' },
                { icon: Briefcase,     label: 'Total Experience',  value: exp.total_years_experience != null ? `${exp.total_years_experience} yrs` : '—',  color: 'var(--accent)' },
                { icon: Briefcase,     label: 'Career Trajectory', value: exp.career_trajectory_label || '—',                                              color: 'var(--accent)' },
                { icon: FlaskConical,  label: 'Publications',      value: `${res.total_publications ?? pubs} (${res.high_impact_count ?? 0} Q1/Q2)`,       color: 'var(--accent2)' },
                { icon: FlaskConical,  label: 'Research Impact',   value: res.research_impact_score ?? '—',                                                color: 'var(--accent2)' },
                { icon: FlaskConical,  label: 'PhD Supervised',    value: res.phd_supervised ?? '—',                                                       color: 'var(--accent2)' },
              ].map((row, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '9px 0', borderBottom: '1px solid var(--border)' }}>
                  <row.icon size={14} color={row.color} style={{ flexShrink: 0 }} />
                  <span style={{ fontSize: 12, color: 'var(--text3)', width: 130, flexShrink: 0 }}>{row.label}</span>
                  <span style={{ fontSize: 13, fontWeight: 500 }}>{row.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* ── Quick summary pills ───────────────────────────────────────── */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 20 }}>
            {edu.has_phd && <span className="badge badge-green">PhD</span>}
            {edu.has_foreign_education && <span className="badge badge-purple">Foreign Education</span>}
            {exp.is_currently_employed && <span className="badge badge-green">Currently Employed</span>}
            {exp.timeline_consistent && <span className="badge badge-teal">Consistent Timeline</span>}
            {(exp.suspicious_overlap_count || 0) > 0 && <span className="badge badge-red">{exp.suspicious_overlap_count} Suspicious Overlap(s)</span>}
            {(exp.unexplained_gap_count || 0) > 0 && <span className="badge badge-amber">{exp.unexplained_gap_count} Unexplained Gap(s)</span>}
            {(res.astar_conference_count || 0) > 0 && <span className="badge badge-blue">{res.astar_conference_count} A* Conference(s)</span>}
            {(res.granted_patents || 0) > 0 && <span className="badge badge-teal">{res.granted_patents} Patent(s)</span>}
            {(res.total_books || 0) > 0 && <span className="badge badge-purple">{res.total_books} Book(s)</span>}
          </div>

          {/* ── LLM Narrative section ──────────────────────────────────────── */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
              <div className="card-title" style={{ margin: 0 }}>
                <Sparkles size={13} style={{ display: 'inline', marginRight: 6 }} />
                AI-generated profile narrative
              </div>
              <button
                className="btn btn-ghost"
                style={{ fontSize: 12, padding: '6px 14px' }}
                onClick={generateNarrative}
                disabled={narLoading}
              >
                {narLoading
                  ? <><RefreshCw size={12} style={{ animation: 'spin 0.8s linear infinite' }} /> Generating…</>
                  : narrative
                  ? <><RefreshCw size={12} /> Regenerate</>
                  : <><Sparkles size={12} /> Generate Narrative</>
                }
              </button>
            </div>

            {narLoading ? (
              <Spinner label="Generating narrative with Gemini…" />
            ) : narError ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--red)', fontSize: 13 }}>
                <AlertCircle size={14} /> {narError}
              </div>
            ) : narrative ? (
              <div style={{ fontSize: 13.5, lineHeight: 1.85, color: 'var(--text2)', whiteSpace: 'pre-wrap' }}>
                {narrative}
              </div>
            ) : (
              <div style={{ fontSize: 13, color: 'var(--text3)', padding: '20px 0', textAlign: 'center' }}>
                Click <strong style={{ color: 'var(--text2)' }}>Generate Narrative</strong> to produce an AI-written candidate summary using Gemini.
              </div>
            )}
          </div>
        </>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
