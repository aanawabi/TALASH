import React from 'react';
import { useApp } from '../AppContext';
import { Users } from 'lucide-react';

export default function CandidateSelector({ label = 'Viewing candidate:' }) {
  const { candidates, selectedId, setSelectedId } = useApp();

  if (!candidates.length) {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '10px 16px', background: 'var(--bg3)',
        borderRadius: 'var(--radius)', border: '1px solid var(--border)', marginBottom: 24
      }}>
        <Users size={14} color="var(--text3)" />
        <span style={{ fontSize: 13, color: 'var(--text3)' }}>
          No candidates loaded — go to Upload to add CVs
        </span>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
      <span style={{
        fontSize: 12, color: 'var(--text3)',
        fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap'
      }}>
        {label}
      </span>
      <select
        className="select-input"
        style={{ flex: 1, maxWidth: 400 }}
        value={selectedId || ''}
        onChange={e => setSelectedId(e.target.value)}
      >
        <option value="">— Select a candidate —</option>
        {candidates.map(c => (
          <option key={c.candidate_id} value={c.candidate_id}>
            {c.full_name}  —  {c.source_file}
          </option>
        ))}
      </select>
    </div>
  );
}