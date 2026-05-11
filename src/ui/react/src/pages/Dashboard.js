import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../AppContext';
import {
  Upload, Users, GraduationCap, FlaskConical, AlertCircle, ArrowRight, BarChart3,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  Cell, PieChart, Pie, Legend,
} from 'recharts';

// ── Helpers ───────────────────────────────────────────────────────────────────

function StatCard({ label, value, sub, color, icon: Icon }) {
  return (
    <div className="stat-card" style={{ '--accent-color': color }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
        <div className="stat-label">{label}</div>
        <Icon size={16} color={color} style={{ opacity: 0.7 }} />
      </div>
      <div className="stat-value">{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}

const PALETTE = ['var(--accent)', 'var(--teal)', 'var(--accent2)', 'var(--green)', 'var(--amber)', 'var(--red)'];

function topDegreeLevel(c) {
  const edu = c.education || [];
  if (edu.find(e => e.degree_level === 'PhD')) return 'PhD';
  if (edu.find(e => /master|mphil|m\.s/i.test(e.degree_level || ''))) return 'Masters / MPhil';
  if (edu.find(e => /bachelor|^bs$|^b\.s/i.test(e.degree_level || ''))) return 'Bachelor\'s';
  return edu[0]?.degree_level || 'Unknown';
}

// ── Main component ────────────────────────────────────────────────────────────
export default function Dashboard() {
  const { candidates, backendOnline } = useApp();
  const navigate = useNavigate();

  const totalPubs  = candidates.reduce((s, c) =>
    s + (c.journal_publications?.length || 0) + (c.conference_publications?.length || 0), 0);
  const withMissing = candidates.filter(c => !c.email || !c.phone).length;

  const recentCandidates = [...candidates]
    .sort((a, b) => new Date(b.extraction_timestamp || 0) - new Date(a.extraction_timestamp || 0))
    .slice(0, 8);

  // ── Comparative chart data ─────────────────────────────────────────────────
  const pubData = [...candidates]
    .map(c => ({
      name:        (c.full_name || '').split(' ').slice(0, 2).join(' '),
      Journals:    c.journal_publications?.length    || 0,
      Conferences: c.conference_publications?.length || 0,
    }))
    .sort((a, b) => (b.Journals + b.Conferences) - (a.Journals + a.Conferences))
    .slice(0, 12);

  const degreeCount = {};
  candidates.forEach(c => {
    const lvl = topDegreeLevel(c);
    degreeCount[lvl] = (degreeCount[lvl] || 0) + 1;
  });
  const degreeData = Object.entries(degreeCount).map(([name, value]) => ({ name, value }));

  const skillsData = [...candidates]
    .map(c => ({
      name:   (c.full_name || '').split(' ').slice(0, 2).join(' '),
      Skills: c.skills?.length || 0,
    }))
    .sort((a, b) => b.Skills - a.Skills)
    .slice(0, 12);

  const expData = [...candidates]
    .map(c => ({
      name:      (c.full_name || '').split(' ').slice(0, 2).join(' '),
      Positions: c.experience?.length || 0,
    }))
    .sort((a, b) => b.Positions - a.Positions)
    .slice(0, 12);

  const showComparative = candidates.length >= 2;

  const tipStyle = { background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 };

  return (
    <div className="fade-up">
      <div className="page-header">
        <h1>Dashboard</h1>
        <p className="subtitle">Overview of all uploaded candidates and processing status</p>
      </div>

      {backendOnline === false && (
        <div style={{
          padding: '10px 16px', marginBottom: 20,
          background: 'rgba(240,82,82,0.08)', border: '1px solid rgba(240,82,82,0.2)',
          borderRadius: 'var(--radius)', fontSize: 13, color: 'var(--red)',
          display: 'flex', alignItems: 'center', gap: 8,
        }}>
          <AlertCircle size={14} />
          FastAPI backend is offline. Run <code style={{ fontFamily: 'var(--font-mono)' }}>python run.py api</code> first.
        </div>
      )}

      {/* ── Stat cards ──────────────────────────────────────────────────── */}
      <div className="stat-grid">
        <StatCard label="Total CVs"    value={candidates.length} sub="loaded this session"   color="var(--accent)"  icon={Users} />
        <StatCard label="Publications" value={totalPubs}         sub="across all candidates" color="var(--teal)"    icon={FlaskConical} />
        <StatCard label="Missing Info" value={withMissing}       sub="candidates flagged"    color="var(--amber)"   icon={AlertCircle} />
        <StatCard label="With PhD"
          value={candidates.filter(c => c.education?.some(e => e.degree_level === 'PhD')).length}
          sub="doctoral candidates"    color="var(--green)"   icon={GraduationCap} />
      </div>

      {/* ── Recent candidates + Quick actions ───────────────────────────── */}
      <div className="grid-2" style={{ gap: 20 }}>
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div className="card-title">Recent candidates</div>
            <button className="btn btn-ghost" style={{ padding: '5px 12px', fontSize: 12 }}
              onClick={() => navigate('/candidates')}>
              View all <ArrowRight size={12} />
            </button>
          </div>

          {recentCandidates.length === 0 ? (
            <div className="empty-state" style={{ padding: '32px 0' }}>
              <Users size={28} /><h3>No candidates yet</h3><p>Upload CVs to get started</p>
            </div>
          ) : (
            <table className="data-table">
              <thead><tr><th>Name</th><th>Degree</th><th>Status</th></tr></thead>
              <tbody>
                {recentCandidates.map(c => {
                  const topDeg = c.education?.find(e => e.degree_level === 'PhD')
                              || c.education?.find(e => e.degree_level?.includes('Master'))
                              || c.education?.[0];
                  return (
                    <tr key={c.candidate_id} style={{ cursor: 'pointer' }}
                      onClick={() => navigate(`/candidates/${c.candidate_id}`)}>
                      <td>
                        <div style={{ fontWeight: 500 }}>{c.full_name}</div>
                        <div className="text-muted text-mono">{c.source_file}</div>
                      </td>
                      <td className="text-muted">{topDeg?.degree_level || '—'}</td>
                      <td><span className="badge badge-green">Processed</span></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="card-title" style={{ marginBottom: 0 }}>Quick actions</div>
          {[
            { icon: Upload,        label: 'Upload new CVs',    sub: 'Add PDF files to the system', path: '/upload',    color: 'var(--accent)'  },
            { icon: GraduationCap, label: 'Education Analysis',sub: 'View academic profiles',      path: '/education', color: 'var(--teal)'    },
            { icon: FlaskConical,  label: 'Research Profile',  sub: 'Publications & metrics',      path: '/research',  color: 'var(--accent2)' },
            { icon: AlertCircle,   label: 'Missing Info',      sub: 'Draft follow-up emails',      path: '/missing',   color: 'var(--amber)'   },
          ].map(item => (
            <div key={item.path} className="card card-sm"
              style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 14, transition: 'border-color 0.15s' }}
              onClick={() => navigate(item.path)}
              onMouseEnter={e => e.currentTarget.style.borderColor = item.color}
              onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
            >
              <div style={{
                width: 38, height: 38, borderRadius: 10,
                background: `${item.color}18`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: item.color, flexShrink: 0,
              }}>
                <item.icon size={17} />
              </div>
              <div>
                <div style={{ fontWeight: 500, fontSize: 13.5 }}>{item.label}</div>
                <div style={{ fontSize: 12, color: 'var(--text3)', marginTop: 1 }}>{item.sub}</div>
              </div>
              <ArrowRight size={14} color="var(--text3)" style={{ marginLeft: 'auto' }} />
            </div>
          ))}
        </div>
      </div>

      {/* ── Comparative analysis section ─────────────────────────────────── */}
      {showComparative && (
        <>
          <div className="section-divider" style={{ margin: '28px 0 20px' }}>
            <span>
              <BarChart3 size={12} style={{ display: 'inline', marginRight: 6 }} />
              Comparative Analysis ({candidates.length} candidates)
            </span>
          </div>

          {/* Row 1: Publications + Degree distribution */}
          <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: 20, marginBottom: 20 }}>
            <div className="card">
              <div className="card-title">Publications per candidate</div>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={pubData} margin={{ left: 0, right: 8, bottom: 40 }}>
                  <XAxis dataKey="name" tick={{ fontSize: 10.5, fill: 'var(--text3)' }} angle={-35} textAnchor="end" interval={0} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: 'var(--text3)' }} />
                  <Tooltip contentStyle={tipStyle} />
                  <Legend wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
                  <Bar dataKey="Journals"    stackId="a" fill="var(--accent)"  radius={[0,0,0,0]} />
                  <Bar dataKey="Conferences" stackId="a" fill="var(--teal)"    radius={[3,3,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <div className="card-title">Highest degree distribution</div>
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={degreeData} dataKey="value" nameKey="name" cx="50%" cy="45%"
                    outerRadius={72} label={({ name, percent }) => `${name} ${Math.round(percent * 100)}%`}
                    labelLine={false} fontSize={10.5}>
                    {degreeData.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={tipStyle} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Row 2: Skills volume + Experience positions */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
            <div className="card">
              <div className="card-title">Skills count per candidate</div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={skillsData} layout="vertical" margin={{ left: 0, right: 20 }}>
                  <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11, fill: 'var(--text3)' }} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 10.5, fill: 'var(--text2)' }} width={90} />
                  <Tooltip contentStyle={tipStyle} />
                  <Bar dataKey="Skills" radius={[0, 4, 4, 0]}>
                    {skillsData.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <div className="card-title">Experience positions per candidate</div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={expData} layout="vertical" margin={{ left: 0, right: 20 }}>
                  <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11, fill: 'var(--text3)' }} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 10.5, fill: 'var(--text2)' }} width={90} />
                  <Tooltip contentStyle={tipStyle} />
                  <Bar dataKey="Positions" radius={[0, 4, 4, 0]}>
                    {expData.map((_, i) => <Cell key={i} fill={PALETTE[(i + 2) % PALETTE.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
