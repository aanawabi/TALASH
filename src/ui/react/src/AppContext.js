import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [candidates, setCandidates]       = useState([]);
  const [selectedId, setSelectedId]       = useState(null);
  const [logs, setLogs]                   = useState([]);
  const [loading, setLoading]             = useState(false);
  const [backendOnline, setBackendOnline] = useState(null);

  // Track IDs that were explicitly cleared this session
  const clearedIds = useRef(new Set());

  useEffect(() => {
    fetch('/').then(r => setBackendOnline(r.ok)).catch(() => setBackendOnline(false));
  }, []);

  const loadCandidates = useCallback(async () => {
    try {
      const r = await fetch('/candidates');
      if (r.ok) {
        const data = await r.json();
        // Filter out any candidate the user already cleared this session
        const filtered = data.filter(c => !clearedIds.current.has(c.candidate_id));
        setCandidates(filtered);
        setBackendOnline(true);
      }
    } catch {
      setBackendOnline(false);
    }
  }, []);

  useEffect(() => { loadCandidates(); }, [loadCandidates]);

  const addLog = useCallback((entry) => {
    setLogs(prev => [
      { ...entry, time: new Date().toLocaleTimeString(), id: Date.now() },
      ...prev,
    ]);
  }, []);

  const addCandidate = useCallback((c) => {
    setCandidates(prev => {
      if (prev.find(x => x.candidate_id === c.candidate_id)) return prev;
      return [c, ...prev];
    });
  }, []);

  const clearCandidates = useCallback(() => {
    // Remember every current candidate ID as cleared
    setCandidates(prev => {
      prev.forEach(c => clearedIds.current.add(c.candidate_id));
      return [];
    });
    setSelectedId(null);
  }, []);

  const selectedCandidate = candidates.find(c => c.candidate_id === selectedId) || null;

return (
  <AppContext.Provider value={{
    candidates, setCandidates, addCandidate, clearCandidates,
    selectedId, setSelectedId, selectedCandidate,
    logs, addLog, setLogs,
    loading, setLoading,
    backendOnline, loadCandidates,
    clearedIds,   // ← add this line
  }}>
    {children}
  </AppContext.Provider>
);
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be inside AppProvider');
  return ctx;
}