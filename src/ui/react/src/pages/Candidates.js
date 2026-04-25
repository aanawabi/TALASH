import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../AppContext';
import { Search, ArrowRight, Trash2, Users } from 'lucide-react';

function initials(name) {
  return (name || '?').split(' ').filter(Boolean).slice(0, 2).map(w => w[0]).join('').toUpperCase();
}

export default function CandidatesPage() {
  const { candidates, clearCandidates, setSelectedId } = useApp();
  const navigate = useNavigate();
  const [search, setSearch]   = useState('');
  const [filter, setFilter]   = useState('All');

  const filtered = candidates.filter(c => {
    const q = search.toLowerCase();
    const matchSearch = !q || c.full_name?.toLowerCase().includes(q) || c.source_file?.toLowerCase().includes(q);
    const missing = !c.email || !c.phone;
    const matchFilter =
      filter === 'All'          ? true :
      filter === 'Missing info' ? missing :
      filter === 'Complete'     ? !missing : true;
    return matchSearch && matchFilter;
  });

  const openProfile = (c) => {
    setSelectedId(c.candidate_id);
    navigate(`/candidates/${c.candidate_id}`);
  };

  return (
    <div className="fade-up">
      <div className="page-header">
        <h1>Candidates</h1>
        <p className="subtitle">All uploaded and processed candidate profiles</p>
      </div>

      <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
        <div className="search-wrap" style={{ flex: 1 }}>
          <Search size={14} />
          <input className="search-input" placeholder="Search by name or file…"
            value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <select className="select-input" value={filter} onChange={e => setFilter(e.target.value)}>
          {['All', 'Complete', 'Missing info'].map(o => <option key={o}>{o}</option>)}
        </select>
        {candidates.length > 0 && (
          <button className="btn btn-danger" onClick={clearCandidates}>
            <Trash2 size={13} /> Clear all
          </button>
        )}
      </div>

      {filtered.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <Users size={32} />
            <h3>No candidates found</h3>
            <p>{candidates.length === 0 ? 'Upload CVs to get started' : 'Try adjusting your filters'}</p>
          </div>
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Candidate</th>
                <th>Highest Degree</th>
                <th>Experience</th>
                <th>Publications</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(c => {
                const topDeg = c.education?.find(e => e.degree_level === 'PhD') ||
                               c.education?.find(e => e.degree_level?.includes('Master')) ||
                               c.education?.[0];
                const jobs = c.experience?.length || 0;
                const pubs = (c.journal_publications?.length || 0) + (c.conference_publications?.length || 0);
                const missing = !c.email || !c.phone;
                return (
                  <tr key={c.candidate_id} style={{ cursor: 'pointer' }} onClick={() => openProfile(c)}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div style={{
                          width: 34, height: 34, borderRadius: '50%',
                          background: 'linear-gradient(135deg, var(--accent), var(--accent2))',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontFamily: 'var(--font-head)', fontSize: 12, fontWeight: 700,
                          color: '#fff', flexShrink: 0
                        }}>
                          {initials(c.full_name)}
                        </div>
                        <div>
                          <div style={{ fontWeight: 500 }}>{c.full_name}</div>
                          <div className="text-muted text-mono">{c.source_file}</div>
                        </div>
                      </div>
                    </td>
                    <td className="text-muted">{topDeg ? `${topDeg.degree_level} · ${topDeg.institution || ''}` : '—'}</td>
                    <td className="text-muted">{jobs} role{jobs !== 1 ? 's' : ''}</td>
                    <td className="text-muted">{pubs} paper{pubs !== 1 ? 's' : ''}</td>
                    <td>
                      {missing
                        ? <span className="badge badge-amber">Missing info</span>
                        : <span className="badge badge-green">Complete</span>}
                    </td>
                    <td><ArrowRight size={14} color="var(--text3)" /></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}