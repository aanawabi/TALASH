import React from 'react';
import { useApp } from '../AppContext';
import CandidateSelector from '../components/CandidateSelector';
import { BookOpen } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const CAT_COLORS = {
  Technical: 'var(--accent)', Language: 'var(--teal)',
  Tool: 'var(--accent2)', Framework: 'var(--green)', Other: 'var(--amber)'
};

export default function SkillsPage() {
  const { selectedCandidate: c } = useApp();
  const skills = c?.skills || [];

  const grouped = skills.reduce((acc, s) => {
    const cat = s.skill_category || 'Other';
    acc[cat] = acc[cat] || [];
    acc[cat].push(s.skill_name);
    return acc;
  }, {});

  const pieData = Object.entries(grouped).map(([name, items]) => ({ name, value: items.length }));

  return (
    <div className="fade-up">
      <div className="page-header">
        <h1>Skills</h1>
        <p className="subtitle">Categorised skill profile extracted from the candidate's CV</p>
      </div>
      <CandidateSelector />
      {!c ? (
        <div className="card"><div className="empty-state"><BookOpen size={32} /><h3>Select a candidate</h3></div></div>
      ) : skills.length === 0 ? (
        <div className="card"><div className="empty-state"><BookOpen size={32} /><h3>No skills extracted</h3><p>The CV may not have a dedicated skills section</p></div></div>
      ) : (
        <>
          <div className="grid-2" style={{ gap: 20, marginBottom: 20 }}>
            <div className="card">
              <div className="card-title">Skills by category</div>
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, percent }) => `${name} ${Math.round(percent*100)}%`} labelLine={false}>
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={Object.values(CAT_COLORS)[i % Object.values(CAT_COLORS).length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="card">
              <div className="card-title">Summary</div>
              {Object.entries(grouped).map(([cat, items]) => (
                <div key={cat} style={{ marginBottom: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: 12.5, color: 'var(--text2)' }}>{cat}</span>
                    <span style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: CAT_COLORS[cat] || 'var(--amber)' }}>{items.length}</span>
                  </div>
                  <div className="progress-bar" style={{ height: 4 }}>
                    <div className="progress-fill" style={{ width: `${(items.length / skills.length) * 100}%`, background: CAT_COLORS[cat] || 'var(--amber)' }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
          {Object.entries(grouped).map(([cat, items]) => (
            <div key={cat} style={{ marginBottom: 16 }}>
              <div className="section-divider"><span>{cat}</span></div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {items.map((skill, i) => (
                  <span key={i} style={{
                    padding: '5px 13px', borderRadius: 99, fontSize: 12.5,
                    background: `${CAT_COLORS[cat] || 'var(--amber)'}15`,
                    border: `1px solid ${CAT_COLORS[cat] || 'var(--amber)'}35`,
                    color: CAT_COLORS[cat] || 'var(--amber)',
                  }}>{skill}</span>
                ))}
              </div>
            </div>
          ))}
        </>
      )}
    </div>
  );
}