import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Upload, Users, GraduationCap, Briefcase,
  BookOpen, AlertCircle, FileText, BarChart3, ScrollText, FlaskConical, Trophy,
} from 'lucide-react';
import { useApp } from '../AppContext';

const sections = [
  {
    label: 'Main',
    items: [
      { to: '/',           icon: LayoutDashboard, label: 'Dashboard' },
      { to: '/upload',     icon: Upload,          label: 'Upload CVs' },
      { to: '/candidates', icon: Users,           label: 'Candidates' },
    ]
  },
  {
    label: 'Analysis',
    items: [
      { to: '/education',  icon: GraduationCap, label: 'Education' },
      { to: '/experience', icon: Briefcase,     label: 'Experience' },
      { to: '/research',   icon: FlaskConical,  label: 'Research' },
      { to: '/skills',     icon: BookOpen,      label: 'Skills' },
    ]
  },
  {
    label: 'Reports',
    items: [
      { to: '/missing',  icon: AlertCircle, label: 'Missing Info' },
      { to: '/summary',  icon: FileText,    label: 'Summary' },
      { to: '/ranking',  icon: Trophy,      label: 'Ranking' },
      { to: '/charts',   icon: BarChart3,   label: 'Charts' },
      { to: '/logs',     icon: ScrollText,  label: 'Logs' },
    ]
  },
];

export default function Sidebar() {
  const { candidates, backendOnline } = useApp();

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="brand">TALASH</div>
        <div className="tagline">Smart HR Recruitment</div>
      </div>

      <nav className="sidebar-nav">
        {sections.map(sec => (
          <div key={sec.label}>
            <div className="nav-section-label">{sec.label}</div>
            {sec.items.map(item => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
              >
                <item.icon size={15} />
                {item.label}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
          <span style={{
            width: 7, height: 7, borderRadius: '50%',
            background: backendOnline ? 'var(--green)' : 'var(--red)',
            display: 'inline-block',
          }} />
          {backendOnline ? 'API online' : 'API offline'}
        </div>
        <div>{candidates.length} candidate{candidates.length !== 1 ? 's' : ''} loaded</div>
      </div>
    </aside>
  );
}