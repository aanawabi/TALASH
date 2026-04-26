import React, { useState, useRef, useCallback } from 'react';
import { Upload, File, CheckCircle, XCircle, Loader, Trash2 } from 'lucide-react';
import { useApp } from '../AppContext';

function FileRow({ file, status, progress, error }) {
  const sizeKb = Math.round(file.size / 1024);
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 12,
      padding: '10px 14px', background: 'var(--bg3)',
      borderRadius: 'var(--radius)', border: '1px solid var(--border)', marginBottom: 8,
    }}>
      <div style={{
        width: 34, height: 34, borderRadius: 8,
        background: 'rgba(240,82,82,0.1)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0
      }}>
        <File size={15} color="var(--red)" />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {file.name}
        </div>
        <div style={{ fontSize: 11.5, color: 'var(--text3)', marginTop: 2 }}>{sizeKb} KB</div>
        {status === 'uploading' && (
          <div className="progress-bar" style={{ marginTop: 6 }}>
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
        )}
        {error && <div style={{ fontSize: 11.5, color: 'var(--red)', marginTop: 3 }}>{error}</div>}
      </div>
      <div>
        {status === 'pending'   && <span className="badge badge-blue">Queued</span>}
        {status === 'uploading' && <Loader size={14} color="var(--accent)" />}
        {status === 'done'      && <CheckCircle size={16} color="var(--green)" />}
        {status === 'error'     && <XCircle size={16} color="var(--red)" />}
      </div>
    </div>
  );
}

export default function UploadPage() {
  const { setCandidates, addLog, loadCandidates, clearedIds } = useApp();
  const [files, setFiles]               = useState([]);
  const [dragging, setDragging]         = useState(false);
  const [running, setRunning]           = useState(false);
  const [successCount, setSuccessCount] = useState(0);
  const inputRef = useRef();

  const addFiles = (newFiles) => {
    const pdfs = Array.from(newFiles).filter(f => f.type === 'application/pdf');
    setFiles(prev => [...prev, ...pdfs.map(f => ({ file: f, status: 'pending', progress: 0, error: null }))]);
    setSuccessCount(0);
  };

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    addFiles(e.dataTransfer.files);
  }, []);

  const updateFile = (idx, patch) =>
    setFiles(prev => prev.map((f, i) => i === idx ? { ...f, ...patch } : f));

  const processAll = async () => {
    const pending = files.filter(f => f.status === 'pending');
    if (!pending.length) return;
    setRunning(true);
    setSuccessCount(0);

    const newCandidates = [];

    for (let i = 0; i < files.length; i++) {
      if (files[i].status !== 'pending') continue;
      updateFile(i, { status: 'uploading', progress: 10 });

      try {
       const form = new FormData();
       form.append('file', files[i].file);

       updateFile(i, { progress: 20 });

  const res = await fetch('/upload-and-process', {
    method: 'POST',
    body: form,
  });

  updateFile(i, { progress: 90 });

  if (!res.ok) throw new Error(`Server error: ${res.status}`);

  const data = await res.json();

  if (!data.success) {
    throw new Error(data.stderr || 'Pipeline failed');
  }

  if (data.candidate && data.candidate.candidate_id) {
    if (clearedIds?.current) {
      clearedIds.current.delete(data.candidate.candidate_id);
    }
    newCandidates.push(data.candidate);
    addLog({
      level: 'success',
      file: files[i].file.name,
      msg: `Extracted: ${data.candidate.full_name || files[i].file.name}`,
      detail: `${data.candidate.education?.length || 0} education, ${data.candidate.experience?.length || 0} experience records`
    });
  } else {
    throw new Error('No candidate data in response');
  }

  updateFile(i, { status: 'done', progress: 100 });

} catch (err) {
  updateFile(i, { status: 'error', error: err.message });
  addLog({ level: 'error', file: files[i].file.name, msg: `Failed: ${files[i].file.name}`, detail: err.message });
}


    }

    setRunning(false);
    setSuccessCount(newCandidates.length);

    if (newCandidates.length > 0) {
      // Directly inject new candidates into global state immediately
      setCandidates(prev => {
        const existingIds = new Set(prev.map(c => c.candidate_id));
        const toAdd = newCandidates.filter(c => !existingIds.has(c.candidate_id));
        return [...toAdd, ...prev];
      });
    } else {
      // Fallback: wait 1s for backend to finish writing JSON, then reload
      setTimeout(() => loadCandidates(), 1000);
    }
  };

  const pendingCount = files.filter(f => f.status === 'pending').length;
  const doneCount    = files.filter(f => f.status === 'done').length;

  return (
    <div className="fade-up">
      <div className="page-header">
        <h1>Upload CVs</h1>
        <p className="subtitle">Upload PDF files to extract and analyse candidate profiles</p>
      </div>

      {successCount > 0 && (
        <div style={{
          padding: '12px 16px', marginBottom: 20,
          background: 'rgba(34,201,122,0.08)', border: '1px solid rgba(34,201,122,0.2)',
          borderRadius: 'var(--radius)', fontSize: 13, color: 'var(--green)',
          display: 'flex', alignItems: 'center', gap: 8
        }}>
          <CheckCircle size={14} />
          {successCount} CV{successCount !== 1 ? 's' : ''} extracted successfully. Go to Candidates to view profiles.
        </div>
      )}

      <div
        className={`upload-zone${dragging ? ' dragging' : ''}`}
        onDrop={onDrop}
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onClick={() => inputRef.current?.click()}
      >
        <input ref={inputRef} type="file" accept=".pdf" multiple
          style={{ display: 'none' }} onChange={e => addFiles(e.target.files)} />
        <div className="upload-icon"><Upload size={22} /></div>
        <h3>Drag & drop CV files here</h3>
        <p>PDF format only · Multiple files supported</p>
      </div>

      {files.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div style={{ fontSize: 12, color: 'var(--text3)', fontFamily: 'var(--font-mono)' }}>
              {files.length} file{files.length !== 1 ? 's' : ''} queued
            </div>
            <button className="btn btn-ghost" style={{ padding: '5px 10px', fontSize: 12 }}
              onClick={() => { setFiles([]); setSuccessCount(0); }} disabled={running}>
              <Trash2 size={12} /> Clear
            </button>
          </div>

          {files.map((f, i) => <FileRow key={i} {...f} />)}

          <div style={{ marginTop: 16 }}>
            <button
              className="btn btn-primary"
              disabled={running || pendingCount === 0}
              onClick={processAll}
            >
              {running
                ? <><Loader size={14} /> Processing…</>
                : pendingCount > 0
                  ? `▶  Extract ${pendingCount} file${pendingCount !== 1 ? 's' : ''}`
                  : doneCount > 0
                    ? `✓  ${doneCount} file${doneCount !== 1 ? 's' : ''} extracted`
                    : 'Extract files'}
            </button>
          </div>
        </div>
      )}

      <div className="card" style={{ marginTop: 28 }}>
        <div className="card-title">Pipeline overview</div>
        <div style={{ display: 'flex', gap: 0 }}>
          {['PDF Upload', 'Text Extract', 'LLM Parse', 'Analysis', 'Export'].map((step, i, arr) => (
            <React.Fragment key={step}>
              <div style={{ flex: 1, textAlign: 'center' }}>
                <div style={{
                  width: 32, height: 32, borderRadius: '50%',
                  background: 'rgba(79,124,255,0.12)', border: '1px solid rgba(79,124,255,0.3)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  margin: '0 auto 8px', fontFamily: 'var(--font-mono)',
                  fontSize: 12, color: 'var(--accent)', fontWeight: 600
                }}>{i + 1}</div>
                <div style={{ fontSize: 11.5, color: 'var(--text2)' }}>{step}</div>
              </div>
              {i < arr.length - 1 && (
                <div style={{ width: 32, display: 'flex', alignItems: 'flex-start', paddingTop: 14, color: 'var(--border2)', fontSize: 16 }}>→</div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
}