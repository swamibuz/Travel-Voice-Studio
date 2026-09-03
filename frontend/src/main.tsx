import React from 'react';
import { createRoot } from 'react-dom/client';
import { ArrowDown, ArrowUp, BookOpen, FileAudio, FileText, Globe2, LogOut, Plane, Printer, RefreshCw, Save, Upload } from 'lucide-react';
import './styles.css';

type User = { username: string; role: string };
type Trip = { id: number; title: string; description: string; route_summary: string };
type Section = {
  id: number;
  batch_id: number;
  original_name: string;
  file_size: number;
  order_index: number;
  inferred_title: string;
  country: string;
  city: string;
  place_name: string;
  visit_date: string;
  route_order: number;
  blog_title: string;
  chapter_title: string;
  tags: string;
  notes: string;
  status: string;
  error: string;
  raw_text?: string;
  cleaned_text?: string;
  blog_draft_text?: string;
  chapter_draft_text?: string;
  reviewed_status?: string;
  location?: string;
};

const apiBase = (import.meta.env.VITE_API_BASE_URL ?? '/api').replace(/\/$/, '');

function App() {
  const [token, setToken] = React.useState(localStorage.getItem('bookwriting-token') ?? '');
  const [user, setUser] = React.useState<User | null>(null);
  const [trips, setTrips] = React.useState<Trip[]>([]);
  const [batchId, setBatchId] = React.useState<number | null>(null);
  const [sections, setSections] = React.useState<Section[]>([]);
  const [selectedId, setSelectedId] = React.useState<number | null>(null);
  const [summary, setSummary] = React.useState('');
  const [exportResult, setExportResult] = React.useState<Record<string, string> | null>(null);
  const [message, setMessage] = React.useState('Ready for travel voice notes.');

  const selected = sections.find((section) => section.id === selectedId) ?? sections[0];

  async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers = new Headers(options.headers);
    if (token) headers.set('Authorization', `Bearer ${token}`);
    const response = await fetch(`${apiBase}${path}`, { ...options, headers });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail ?? 'Request failed');
    }
    return response.json() as Promise<T>;
  }

  async function login(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const result = await fetch(`${apiBase}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: data.get('username'), password: data.get('password') }),
    });
    if (!result.ok) {
      setMessage('Login failed. Try admin / admin123 for local testing.');
      return;
    }
    const payload = await result.json();
    localStorage.setItem('bookwriting-token', payload.token);
    setToken(payload.token);
    setUser(payload.user);
    setMessage('Logged in. Upload voice notes or process the sample MP3.');
  }

  async function loadTrips() {
    const payload = await request<{ trips: Trip[] }>('/trips');
    setTrips(payload.trips);
  }

  React.useEffect(() => {
    if (token) void loadTrips().catch((error) => setMessage(error.message));
  }, [token]);

  async function createTrip(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const trip = await request<Trip>('/trips', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: data.get('title'),
        description: data.get('description'),
        route_summary: data.get('route_summary'),
      }),
    });
    setTrips([trip, ...trips]);
    setMessage('Trip created. Add audio files for this route.');
  }

  async function upload(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const input = event.currentTarget.elements.namedItem('files') as HTMLInputElement;
    if (!input.files?.length) return setMessage('Choose at least one audio file.');
    const form = new FormData();
    Array.from(input.files).forEach((file) => form.append('files', file));
    const tripId = trips[0]?.id;
    const query = tripId ? `?trip_id=${tripId}` : '';
    const payload = await request<{ batch_id: number; files: Section[] }>(`/uploads${query}`, { method: 'POST', body: form });
    setBatchId(payload.batch_id);
    setSections(payload.files);
    setSelectedId(payload.files[0]?.id ?? null);
    setMessage(`Uploaded ${payload.files.length} file(s). Add travel metadata, reorder, then process.`);
  }

  async function processBatch() {
    if (!batchId) return;
    setMessage('Processing files sequentially...');
    const payload = await request<{ sections: Section[] }>(`/jobs/${batchId}/process`, { method: 'POST' });
    setSections(payload.sections);
    setSelectedId(payload.sections[0]?.id ?? null);
    setMessage('Processing complete. Review the raw, cleaned, blog, and chapter drafts.');
  }

  async function saveMetadata(section: Section) {
    const updated = await request<Section>(`/uploads/${section.id}/travel-metadata`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(section),
    });
    setSections((current) => current.map((item) => (item.id === updated.id ? { ...item, ...updated } : item)));
    setMessage('Travel metadata saved.');
  }

  async function saveTranscript(section: Section) {
    const payload = await request<{ section: Section }>(`/transcripts/${section.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cleaned_text: section.cleaned_text ?? '',
        blog_draft_text: section.blog_draft_text ?? '',
        chapter_draft_text: section.chapter_draft_text ?? '',
        reviewed_status: 'reviewed',
      }),
    });
    setSections((current) => current.map((item) => (item.id === payload.section.id ? payload.section : item)));
    setMessage('Transcript review saved.');
  }

  async function moveSection(section: Section, direction: -1 | 1) {
    const index = sections.findIndex((item) => item.id === section.id);
    const nextIndex = index + direction;
    if (nextIndex < 0 || nextIndex >= sections.length) return;
    const reordered = [...sections];
    [reordered[index], reordered[nextIndex]] = [reordered[nextIndex], reordered[index]];
    const normalized = reordered.map((item, order_index) => ({ ...item, order_index, route_order: order_index + 1 }));
    setSections(normalized);
    await request('/uploads/order', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items: normalized.map(({ id, order_index }) => ({ id, order_index })) }),
    });
  }

  async function createSummary() {
    if (!batchId) return;
    const payload = await request<{ text: string }>('/summaries', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ batch_id: batchId, summary_type: 'medium' }),
    });
    setSummary(payload.text);
  }

  async function exportBatch() {
    if (!batchId) return;
    const payload = await request<{ artifacts: Record<string, string> }>('/exports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ batch_id: batchId, include_raw: true }),
    });
    setExportResult(payload.artifacts);
    setMessage('Export files created under voiceoutput.');
  }

  function updateSection(id: number, patch: Partial<Section>) {
    setSections((current) => current.map((section) => (section.id === id ? { ...section, ...patch } : section)));
  }

  if (!token) {
    return <LoginScreen onLogin={login} message={message} />;
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow"><Globe2 size={16} /> Travel Voice Studio</p>
          <h1>Around the World Book Builder</h1>
        </div>
        <button className="ghost" onClick={() => { localStorage.removeItem('bookwriting-token'); setToken(''); }}><LogOut size={17} /> Logout</button>
      </header>

      <section className="status-line">{message}</section>

      <div className="workspace-grid">
        <section className="panel sidebar">
          <h2><Plane size={18} /> Trip Setup</h2>
          <form onSubmit={createTrip} className="stack">
            <input name="title" defaultValue="Around the World Travel Book" />
            <textarea name="description" defaultValue="Voice notes and visit documentation for a travel blog and manuscript." />
            <textarea name="route_summary" placeholder="Route summary: India, Singapore, Paris, New York..." />
            <button><Save size={17} /> Save Trip</button>
          </form>
          <div className="trip-list">
            {trips.map((trip) => <p key={trip.id}><strong>{trip.title}</strong><span>{trip.route_summary || trip.description}</span></p>)}
          </div>

          <h2><Upload size={18} /> Audio Upload</h2>
          <form onSubmit={upload} className="stack upload-box">
            <input type="file" name="files" multiple accept="audio/*,video/mp4" />
            <button><FileAudio size={17} /> Upload Files</button>
          </form>
          <button className="wide accent" disabled={!batchId} onClick={processBatch}><RefreshCw size={17} /> Process Batch</button>
        </section>

        <section className="panel list-panel">
          <h2><FileAudio size={18} /> Route Order</h2>
          <div className="section-list">
            {sections.map((section) => (
              <button key={section.id} className={selected?.id === section.id ? 'section-card active' : 'section-card'} onClick={() => setSelectedId(section.id)}>
                <span>{section.route_order}. {section.inferred_title}</span>
                <small>{section.status} · {section.location || 'metadata pending'}</small>
                <span className="inline-actions">
                  <ArrowUp size={16} onClick={(event) => { event.stopPropagation(); void moveSection(section, -1); }} />
                  <ArrowDown size={16} onClick={(event) => { event.stopPropagation(); void moveSection(section, 1); }} />
                </span>
              </button>
            ))}
          </div>
        </section>

        <section className="panel editor-panel">
          {selected ? (
            <Editor section={selected} updateSection={updateSection} saveMetadata={saveMetadata} saveTranscript={saveTranscript} />
          ) : (
            <div className="empty-state"><BookOpen size={36} /><p>Upload travel voice notes to begin building the manuscript.</p></div>
          )}
        </section>

        <section className="panel output-panel">
          <h2><Printer size={18} /> Summary and Export</h2>
          <div className="action-row">
            <button disabled={!batchId} onClick={createSummary}><FileText size={17} /> Summarize</button>
            <button disabled={!batchId} onClick={exportBatch}><Printer size={17} /> Export</button>
          </div>
          {summary && <pre className="output-text">{summary}</pre>}
          {exportResult && <div className="artifact-list">{Object.entries(exportResult).map(([key, value]) => <p key={key}><strong>{key}</strong><span>{value}</span></p>)}</div>}
        </section>
      </div>
    </main>
  );
}

function LoginScreen({ onLogin, message }: { onLogin: (event: React.FormEvent<HTMLFormElement>) => void; message: string }) {
  return (
    <main className="login-screen">
      <form className="login-card" onSubmit={onLogin}>
        <p className="eyebrow"><Globe2 size={16} /> BookWriting</p>
        <h1>Travel voice notes to book chapters</h1>
        <input name="username" defaultValue="admin" aria-label="Username" />
        <input name="password" defaultValue="admin123" type="password" aria-label="Password" />
        <button>Login</button>
        <p className="message-text">{message}</p>
      </form>
    </main>
  );
}

function Editor({ section, updateSection, saveMetadata, saveTranscript }: {
  section: Section;
  updateSection: (id: number, patch: Partial<Section>) => void;
  saveMetadata: (section: Section) => Promise<void>;
  saveTranscript: (section: Section) => Promise<void>;
}) {
  return (
    <div className="editor-stack">
      <div className="editor-head">
        <div>
          <p className="eyebrow">Visit Documentation</p>
          <h2>{section.inferred_title}</h2>
        </div>
        <span className="badge">{section.reviewed_status || section.status}</span>
      </div>

      <div className="metadata-grid">
        <input value={section.country} placeholder="Country" onChange={(event) => updateSection(section.id, { country: event.target.value })} />
        <input value={section.city} placeholder="City" onChange={(event) => updateSection(section.id, { city: event.target.value })} />
        <input value={section.place_name} placeholder="Place visited" onChange={(event) => updateSection(section.id, { place_name: event.target.value })} />
        <input value={section.visit_date} placeholder="Visit date" onChange={(event) => updateSection(section.id, { visit_date: event.target.value })} />
        <input value={section.blog_title} placeholder="Blog title" onChange={(event) => updateSection(section.id, { blog_title: event.target.value })} />
        <input value={section.chapter_title} placeholder="Chapter title" onChange={(event) => updateSection(section.id, { chapter_title: event.target.value })} />
      </div>
      <textarea value={section.notes} placeholder="Travel notes: food, people, culture, cost, recommendations..." onChange={(event) => updateSection(section.id, { notes: event.target.value })} />
      <button className="fit" onClick={() => void saveMetadata(section)}><Save size={17} /> Save Metadata</button>

      <div className="transcript-grid">
        <label>Raw Transcript<textarea readOnly value={section.raw_text || ''} /></label>
        <label>Cleaned Transcript<textarea value={section.cleaned_text || ''} onChange={(event) => updateSection(section.id, { cleaned_text: event.target.value })} /></label>
        <label>Blog Draft<textarea value={section.blog_draft_text || ''} onChange={(event) => updateSection(section.id, { blog_draft_text: event.target.value })} /></label>
        <label>Chapter Draft<textarea value={section.chapter_draft_text || ''} onChange={(event) => updateSection(section.id, { chapter_draft_text: event.target.value })} /></label>
      </div>
      <button className="fit accent" onClick={() => void saveTranscript(section)}><Save size={17} /> Save Review</button>
    </div>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
