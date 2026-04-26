import React, { useState } from 'react';
import { useApp } from '../AppContext';
import { ScrollText, Trash2 } from 'lucide-react';

const LEVEL_COLOR = { success: 'var(--green)', warning: 'var(--amber)', error: 'var(--red)', info: 'var(--accent)' };
const LEVEL_BADGE = { success: 'badge-green', warning: 'badge-amber', error: 'badge-red', info: 'badge-blue' };

export default function LogsPage() {
  const { logs, setLogs } = useApp();
  const [levelFilter, setLevelFilter] = useState('All');
  const [fileFilter, setFileFilter]   = useState('All');

  const files = ['All', ...new Set(logs.map(l => l.file).filter(Boolean))];

  const filtered = logs.filter(l => {
    const matchLevel = levelFilter === 'All' || l.level === levelFilter.toLowerCase();
    const matchFile  = fileFilter === 'All'  || l.file === fileFilter;
    return matchLevel && matchFile;
  });

  return (
    <div className="fade-up">
      <div className="page-header">
        <h1>Extraction logs</h1>
        <p className="subtitle">Timestamped record of every extraction and processing event</p>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
        <select className="select-input" value={levelFilter} onChange={e => setLevelFilter(e.target.value)}>
          {['All','Success','Warning','Error','Info'].map(o => <option key={o}>{o}</option>)}
        </select>
        <select className="select-input" value={fileFilter} onChange={e => setFileFilter(e.target.value)}>
          {files.map(f => <option key={f}>{f}</option>)}
        </select>
        <div style={{ flex: 1 }} />
        <button className="btn btn-danger" onClick={() => setLogs([])} disabled={!logs.length}>
          <Trash2 size={13} /> Clear logs
        </button>
      </div>

      <div className="card" style={{ padding: '4px 20px' }}>
        {filtered.length === 0 ? (
          <div className="empty-state">
            <ScrollText size={32} />
            <h3>No log entries</h3>
            <p>{logs.length === 0 ? 'Logs appear here after uploading and processing CVs' : 'No entries match your filters'}</p>
          </div>
        ) : (
          <div className="log-list">
            {filtered.map((l, i) => (
              <div key={l.id || i} className="log-entry">
                <div className="log-dot" style={{ background: LEVEL_COLOR[l.level] || 'var(--text3)' }} />
                <div className="log-time">{l.time}</div>
                <div className="log-file">{l.file || '—'}</div>
                <div className="log-msg">
                  {l.msg}
                  {l.detail && <div className="log-detail">{l.detail}</div>}
                </div>
                <span className={`badge ${LEVEL_BADGE[l.level] || 'badge-teal'}`} style={{ marginLeft: 8, flexShrink: 0 }}>
                  {l.level}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}