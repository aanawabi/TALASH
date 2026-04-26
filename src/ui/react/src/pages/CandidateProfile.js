import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useApp } from '../AppContext';
import { ArrowLeft, User, GraduationCap, Briefcase, BookOpen, FlaskConical } from 'lucide-react';

export default function CandidateProfile() {
  const { id } = useParams();
  const { candidates } = useApp();
  const navigate = useNavigate();
  const [tab, setTab] = useState('personal');

  const c = candidates.find(x => x.candidate_id === id);
  if (!c) return (
    <div className="fade-up">
      <button className="btn btn-ghost" onClick={() => navigate('/candidates')} style={{ marginBottom: 20 }}>
        <ArrowLeft size={14} /> Back
      </button>
      <div className="card"><div className="empty-state"><User size={32} /><h3>Candidate not found</h3></div></div>
    </div>
  );

  const initials = (c.full_name || '?').split(' ').slice(0,2).map(w=>w[0]).join('');
  const topDeg = c.education?.find(e=>e.degree_level==='PhD') || c.education?.find(e=>e.degree_level?.includes('Master')) || c.education?.[0];
  const currentJob = c.experience?.find(e=>e.is_current);

  const tabs = [
    { key: 'personal',   icon: User,          label: 'Personal' },
    { key: 'education',  icon: GraduationCap, label: 'Education' },
    { key: 'experience', icon: Briefcase,     label: 'Experience' },
    { key: 'skills',     icon: BookOpen,      label: 'Skills' },
    { key: 'pubs',       icon: FlaskConical,  label: 'Publications' },
  ];

  return (
    <div className="fade-up">
      <button className="btn btn-ghost" onClick={() => navigate('/candidates')} style={{ marginBottom: 20 }}>
        <ArrowLeft size={14} /> Back to candidates
      </button>

      <div className="cand-header">
        <div className="cand-avatar">{initials}</div>
        <div>
          <div className="cand-name">{c.full_name}</div>
          <div className="cand-meta">
            {topDeg?.degree_level}
            {currentJob ? ` · ${currentJob.job_title} at ${currentJob.organization}` : ''}
          </div>
          <div style={{ marginTop: 6, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {c.email && <span className="badge badge-teal">{c.email}</span>}
            {c.phone && <span className="badge badge-blue">{c.phone}</span>}
            <span className="badge badge-green">Processed</span>
          </div>
        </div>
      </div>

      <div className="tab-bar">
        {tabs.map(t => (
          <button key={t.key} className={`tab-btn${tab===t.key?' active':''}`} onClick={()=>setTab(t.key)}>
            <t.icon size={13} />{t.label}
          </button>
        ))}
      </div>

      {tab === 'personal' && (
        <div className="card">
          <div className="card-title">Personal information</div>
          {[
            ['Full Name', c.full_name],
            ['Email', c.email],
            ['Phone', c.phone],
            ['LinkedIn', c.linkedin],
            ['GitHub / Website', c.website],
            ['Source File', c.source_file],
            ['Extracted', c.extraction_timestamp ? new Date(c.extraction_timestamp).toLocaleString() : '—'],
          ].map(([key, val]) => val && (
            <div key={key} style={{ display: 'flex', gap: 16, padding: '9px 0', borderBottom: '1px solid var(--border)' }}>
              <span style={{ width: 160, color: 'var(--text3)', fontSize: 12.5, flexShrink: 0 }}>{key}</span>
              <span style={{ fontSize: 13 }}>{val}</span>
            </div>
          ))}
        </div>
      )}

      {tab === 'education' && (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="data-table">
            <thead><tr><th>Degree</th><th>Level</th><th>Institution</th><th>Year</th><th>Grade</th></tr></thead>
            <tbody>
              {(c.education || []).map((e,i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 500 }}>{e.degree_title}</td>
                  <td><span className="badge badge-blue">{e.degree_level}</span></td>
                  <td className="text-muted">{e.institution || e.board || '—'}</td>
                  <td className="text-mono">{e.end_year || '—'}</td>
                  <td className="text-mono">{e.grade_value || '—'}</td>
                </tr>
              ))}
              {!c.education?.length && <tr><td colSpan={5} style={{ color: 'var(--text3)', textAlign: 'center' }}>No records</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'experience' && (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="data-table">
            <thead><tr><th>Title</th><th>Organization</th><th>From</th><th>To</th><th>Status</th></tr></thead>
            <tbody>
              {(c.experience || []).map((e,i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 500 }}>{e.job_title}</td>
                  <td className="text-muted">{e.organization}{e.location ? ` · ${e.location}` : ''}</td>
                  <td className="text-mono">{e.start_date || '—'}</td>
                  <td className="text-mono">{e.is_current ? 'Present' : e.end_date || '—'}</td>
                  <td>{e.is_current ? <span className="badge badge-green">Current</span> : <span className="badge badge-teal">Past</span>}</td>
                </tr>
              ))}
              {!c.experience?.length && <tr><td colSpan={5} style={{ color: 'var(--text3)', textAlign: 'center' }}>No records</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'skills' && (
        <div className="card">
          {(c.skills || []).length === 0
            ? <div style={{ color: 'var(--text3)', fontSize: 13 }}>No skills extracted.</div>
            : <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {c.skills.map((s,i) => (
                  <span key={i} style={{ padding: '5px 13px', borderRadius: 99, fontSize: 12.5, background: 'var(--bg3)', border: '1px solid var(--border)', color: 'var(--text2)' }}>
                    {s.skill_name}
                  </span>
                ))}
              </div>
          }
        </div>
      )}

      {tab === 'pubs' && (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="data-table">
            <thead><tr><th>Title</th><th>Venue</th><th>Year</th><th>IF</th><th>Role</th><th>Type</th></tr></thead>
            <tbody>
              {[...(c.journal_publications||[]).map(p=>({...p,type:'Journal'})), ...(c.conference_publications||[]).map(p=>({...p,type:'Conference'}))]
                .map((p,i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 500, fontSize: 12.5, maxWidth: 300 }}>{p.title}</td>
                    <td className="text-muted">{p.journal_name || p.conference_name || '—'}</td>
                    <td className="text-mono">{p.publication_year || '—'}</td>
                    <td className="text-mono">{p.impact_factor || '—'}</td>
                    <td><span className="badge badge-teal">{p.author_role || '—'}</span></td>
                    <td><span className={`badge ${p.type==='Journal'?'badge-blue':'badge-purple'}`}>{p.type}</span></td>
                  </tr>
                ))}
              {!c.journal_publications?.length && !c.conference_publications?.length && (
                <tr><td colSpan={6} style={{ color: 'var(--text3)', textAlign: 'center' }}>No publications</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}