import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppProvider } from './AppContext';
import Sidebar from './components/Sidebar';

import Dashboard        from './pages/Dashboard';
import UploadPage       from './pages/Upload';
import CandidatesPage   from './pages/Candidates';
import CandidateProfile from './pages/CandidateProfile';
import EducationPage    from './pages/Education';
import ExperiencePage   from './pages/Experience';
import ResearchPage     from './pages/Research';
import SkillsPage       from './pages/Skills';
import MissingInfoPage  from './pages/MissingInfo';
import SummaryPage      from './pages/Summary';
import ChartsPage       from './pages/Charts';
import LogsPage         from './pages/Logs';

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <div className="app-shell">
          <Sidebar />
          <main className="main-content">
            <Routes>
              <Route path="/"                   element={<Dashboard />} />
              <Route path="/upload"             element={<UploadPage />} />
              <Route path="/candidates"         element={<CandidatesPage />} />
              <Route path="/candidates/:id"     element={<CandidateProfile />} />
              <Route path="/education"          element={<EducationPage />} />
              <Route path="/experience"         element={<ExperiencePage />} />
              <Route path="/research"           element={<ResearchPage />} />
              <Route path="/skills"             element={<SkillsPage />} />
              <Route path="/missing"            element={<MissingInfoPage />} />
              <Route path="/summary"            element={<SummaryPage />} />
              <Route path="/charts"             element={<ChartsPage />} />
              <Route path="/logs"               element={<LogsPage />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </AppProvider>
  );
}