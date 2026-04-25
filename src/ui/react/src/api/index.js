const BASE = '';

export async function getCandidates() {
  const r = await fetch(`${BASE}/candidates`);
  if (!r.ok) throw new Error('Failed to fetch candidates');
  return r.json();
}

export async function getCandidate(candidateId) {
  const r = await fetch(`${BASE}/candidates/${candidateId}`);
  if (!r.ok) throw new Error('Failed to fetch candidate');
  return r.json();
}

export async function uploadCV(file, onProgress) {
  const form = new FormData();
  form.append('file', file);
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${BASE}/upload`);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) onProgress(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) resolve(JSON.parse(xhr.responseText));
      else reject(new Error(xhr.responseText));
    };
    xhr.onerror = () => reject(new Error('Network error'));
    xhr.send(form);
  });
}

export async function processFolder(inputFolder = 'data/input_cvs', format = 'excel') {
  const r = await fetch(`${BASE}/process-folder`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ input_folder: inputFolder, format }),
  });
  if (!r.ok) throw new Error('Processing failed');
  return r.json();
}

export async function getOutputFiles() {
  const r = await fetch(`${BASE}/outputs`);
  if (!r.ok) throw new Error('Failed to fetch outputs');
  return r.json();
}

export async function getLogs() {
  const r = await fetch(`${BASE}/logs`);
  if (!r.ok) return [];
  return r.json();
}

export async function healthCheck() {
  const r = await fetch(`${BASE}/`);
  return r.ok;
}