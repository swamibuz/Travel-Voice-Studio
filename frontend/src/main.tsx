import React from 'react';
import { createRoot } from 'react-dom/client';
import { ArrowDown, ArrowUp, BookOpen, ChevronLeft, ChevronRight, Download, FileAudio, FileText, Globe2, Loader2, LogOut, Plane, Printer, RefreshCw, Save, Upload } from 'lucide-react';
import './styles.css';

type User = { username: string; role: string };
type Trip = { title: string; description: string; route_summary: string };
type Section = {
  id: string;
  file?: File;
  original_name: string;
  order_index: number;
  route_order: number;
  inferred_title: string;
  country: string;
  city: string;
  place_name: string;
  visit_date: string;
  blog_title: string;
  chapter_title: string;
  tags: string;
  notes: string;
  status: 'queued' | 'processing' | 'complete' | 'failed';
  error: string;
  raw_text?: string;
  cleaned_text?: string;
  blog_draft_text?: string;
  chapter_draft_text?: string;
  reviewed_status?: string;
};

const apiBase = '/api';
const defaultTrip: Trip = {
  title: 'Around the World Travel Book',
  description: 'Voice notes and visit documentation for a travel blog and manuscript.',
  route_summary: '',
};

// Nothing is persisted server-side — trips live only in this browser's storage.
function loadStoredTrips(): Trip[] {
  try {
    return JSON.parse(localStorage.getItem('bookwriting-trips') ?? '[]');
  } catch {
    return [];
  }
}

function displayLocation(section: Pick<Section, 'place_name' | 'city' | 'country'>): string {
  const parts = [section.place_name, section.city, section.country].map((part) => part.trim()).filter(Boolean);
  return parts.join(', ') || 'Location to be reviewed';
}

function downloadTextFile(filename: string, content: string) {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function App() {
  const [token, setToken] = React.useState(localStorage.getItem('bookwriting-token') ?? '');
  const [user, setUser] = React.useState<User | null>(null);
  const [trips, setTrips] = React.useState<Trip[]>(loadStoredTrips);
  const [trip, setTrip] = React.useState<Trip>(defaultTrip);
  const [sections, setSections] = React.useState<Section[]>([]);
  const [selectedId, setSelectedId] = React.useState<string | null>(null);
  const [summary, setSummary] = React.useState('');
  const [exportFiles, setExportFiles] = React.useState<Record<string, string> | null>(null);
  const [message, setMessage] = React.useState('Ready for travel voice notes.');
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(true);
  const [listCollapsed, setListCollapsed] = React.useState(false);
  const [uploading, setUploading] = React.useState(false);
  const [processing, setProcessing] = React.useState(false);

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

  function createTrip(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const nextTrip: Trip = {
      title: String(data.get('title') ?? ''),
      description: String(data.get('description') ?? ''),
      route_summary: String(data.get('route_summary') ?? ''),
    };
    setTrip(nextTrip);
    const nextTrips = [nextTrip, ...trips];
    setTrips(nextTrips);
    localStorage.setItem('bookwriting-trips', JSON.stringify(nextTrips));
    setMessage('Trip saved in this browser. Add audio files for this route.');
  }

  async function upload(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const input = event.currentTarget.elements.namedItem('files') as HTMLInputElement;
    if (!input.files?.length) return setMessage('Choose at least one audio file.');
    const files = Array.from(input.files);
    setUploading(true);
    setMessage('Reading file metadata...');
    try {
      const payload = await request<{ items: { filename: string; inferred_title: string; visit_date: string; blog_title: string; chapter_title: string }[] }>('/metadata/infer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ files: files.map((file, order_index) => ({ filename: file.name, order_index })) }),
      });
      const newSections: Section[] = files.map((file, index) => {
        const meta = payload.items[index];
        return {
          id: crypto.randomUUID(),
          file,
          original_name: file.name,
          order_index: index,
          route_order: index + 1,
          inferred_title: meta.inferred_title,
          country: '',
          city: '',
          place_name: '',
          visit_date: meta.visit_date,
          blog_title: meta.blog_title,
          chapter_title: meta.chapter_title,
          tags: '',
          notes: '',
          status: 'queued',
          error: '',
        };
      });
      setSections(newSections);
      setSelectedId(newSections[0]?.id ?? null);
      setMessage(`Added ${newSections.length} file(s). Add travel metadata, reorder, then process.`);
    } finally {
      setUploading(false);
    }
  }

  async function processBatch() {
    if (!sections.length || processing) return;
    setProcessing(true);
    setMessage('Processing files sequentially...');
    try {
      for (const section of sections) {
        if (!section.file) continue;
        setSections((current) => current.map((item) => (item.id === section.id ? { ...item, status: 'processing', error: '' } : item)));
        const form = new FormData();
        form.append('file', section.file);
        form.append('original_name', section.original_name);
        form.append('country', section.country);
        form.append('city', section.city);
        form.append('place_name', section.place_name);
        form.append('visit_date', section.visit_date);
        form.append('blog_title', section.blog_title);
        form.append('chapter_title', section.chapter_title);
        try {
          const result = await request<{ raw_text: string; cleaned_text: string; blog_draft_text: string; chapter_draft_text: string }>('/transcribe', {
            method: 'POST',
            body: form,
          });
          setSections((current) => current.map((item) => (item.id === section.id ? { ...item, ...result, status: 'complete' } : item)));
        } catch (error) {
          setSections((current) => current.map((item) => (item.id === section.id ? { ...item, status: 'failed', error: (error as Error).message } : item)));
        }
      }
      setMessage('Processing complete. Review the raw, cleaned, blog, and chapter drafts.');
    } finally {
      setProcessing(false);
    }
  }

  function saveMetadata() {
    setMessage('Metadata kept in this browser only — nothing is stored on the server.');
  }

  function saveTranscript() {
    setMessage('Review kept in this browser only — copy the text out or use Export to save it.');
  }

  function moveSection(section: Section, direction: -1 | 1) {
    const index = sections.findIndex((item) => item.id === section.id);
    const nextIndex = index + direction;
    if (nextIndex < 0 || nextIndex >= sections.length) return;
    const reordered = [...sections];
    [reordered[index], reordered[nextIndex]] = [reordered[nextIndex], reordered[index]];
    const normalized = reordered.map((item, order_index) => ({ ...item, order_index, route_order: order_index + 1 }));
    setSections(normalized);
  }

  function sectionsForApi() {
    return sections.map(({ file, ...rest }) => ({ ...rest, location: displayLocation(rest) }));
  }

  async function createSummary() {
    if (!sections.length) return;
    const payload = await request<{ text: string }>('/summaries', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ summary_type: 'medium', sections: sectionsForApi() }),
    });
    setSummary(payload.text);
  }

  async function exportBatch() {
    if (!sections.length) return;
    const payload = await request<{ files: Record<string, string> }>('/exports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: trip.title, include_raw: true, sections: sectionsForApi() }),
    });
    setExportFiles(payload.files);
    setMessage('Export ready — download the files below.');
  }

  function updateSection(id: string, patch: Partial<Section>) {
    setSections((current) => current.map((section) => (section.id === id ? { ...section, ...patch } : section)));
  }

  if (!token) {
    return (
      <>
        <TravelScene />
        <LoginScreen onLogin={login} message={message} />
      </>
    );
  }

  return (
    <>
      <TravelScene />
      <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow"><Globe2 size={16} /> Travel Voice Studio</p>
          <h1>Around the World Book Builder</h1>
        </div>
        <button className="ghost" onClick={() => { localStorage.removeItem('bookwriting-token'); setToken(''); }}><LogOut size={17} /> Logout</button>
      </header>

      <section className="status-line">{message}</section>

      <div
        className="workspace-grid"
        style={{ gridTemplateColumns: `${sidebarCollapsed ? '40px' : '320px'} ${listCollapsed ? '40px' : '300px'} minmax(0, 1fr)` }}
      >
        <section className={sidebarCollapsed ? 'panel sidebar collapsed' : 'panel sidebar'}>
          <button className="collapse-toggle" onClick={() => setSidebarCollapsed((value) => !value)} title={sidebarCollapsed ? 'Expand Trip Setup' : 'Collapse Trip Setup'}>
            {sidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
          {sidebarCollapsed ? (
            <p className="collapsed-label">Trip Setup</p>
          ) : (
            <>
              <h2><Plane size={18} /> Trip Setup</h2>
              <form onSubmit={createTrip} className="stack">
                <input name="title" defaultValue={trip.title} />
                <textarea name="description" defaultValue={trip.description} />
                <textarea name="route_summary" defaultValue={trip.route_summary} placeholder="Route summary: India, Singapore, Paris, New York..." />
                <button><Save size={17} /> Save Trip</button>
              </form>
              <div className="trip-list">
                {trips.map((item, index) => <p key={index}><strong>{item.title}</strong><span>{item.route_summary || item.description}</span></p>)}
              </div>

              {selected && (
                <div className="editor-stack">
                  <div className="editor-head">
                    <div>
                      <p className="eyebrow">Visit Documentation</p>
                      <h2>{selected.inferred_title}</h2>
                    </div>
                    <span className="badge">{selected.reviewed_status || selected.status}</span>
                  </div>

                  <div className="metadata-grid">
                    <input value={selected.country} placeholder="Country" onChange={(event) => updateSection(selected.id, { country: event.target.value })} />
                    <input value={selected.city} placeholder="City" onChange={(event) => updateSection(selected.id, { city: event.target.value })} />
                    <input value={selected.place_name} placeholder="Place visited" onChange={(event) => updateSection(selected.id, { place_name: event.target.value })} />
                    <input value={selected.visit_date} placeholder="Visit date" onChange={(event) => updateSection(selected.id, { visit_date: event.target.value })} />
                    <input value={selected.blog_title} placeholder="Blog title" onChange={(event) => updateSection(selected.id, { blog_title: event.target.value })} />
                    <input value={selected.chapter_title} placeholder="Chapter title" onChange={(event) => updateSection(selected.id, { chapter_title: event.target.value })} />
                  </div>
                  <textarea value={selected.notes} placeholder="Travel notes: food, people, culture, cost, recommendations..." onChange={(event) => updateSection(selected.id, { notes: event.target.value })} />
                  <button className="fit" onClick={() => saveMetadata(selected)}><Save size={17} /> Save Metadata</button>
                </div>
              )}
            </>
          )}
        </section>

        <section className={listCollapsed ? 'panel list-panel collapsed' : 'panel list-panel'}>
          <button className="collapse-toggle" onClick={() => setListCollapsed((value) => !value)} title={listCollapsed ? 'Expand' : 'Collapse'}>
            {listCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
          {listCollapsed ? (
            <p className="collapsed-label">Upload &amp; Route Order</p>
          ) : (
            <>
              <h2><Upload size={18} /> Audio Upload</h2>
              <form onSubmit={upload} className={uploading ? 'stack upload-box uploading' : 'stack upload-box'}>
                <input type="file" name="files" multiple accept="audio/*,video/mp4" disabled={uploading} />
                <button disabled={uploading}>
                  {uploading ? <Loader2 size={17} className="spin" /> : <FileAudio size={17} />}
                  {uploading ? 'Uploading...' : 'Upload Files'}
                </button>
              </form>
              <button className={processing ? 'wide accent processing' : 'wide accent'} disabled={!sections.length || processing} onClick={processBatch}>
                {processing ? <Loader2 size={17} className="spin" /> : <RefreshCw size={17} />}
                {processing ? 'Processing...' : 'Process Batch'}
              </button>

              <h2><FileAudio size={18} /> Route Order</h2>
              <div className="section-list">
                {sections.map((section) => (
                  <button key={section.id} className={selected?.id === section.id ? 'section-card active' : 'section-card'} onClick={() => setSelectedId(section.id)}>
                    <span>{section.route_order}. {section.inferred_title}</span>
                    <small>{section.status} · {displayLocation(section)}</small>
                    <span className="inline-actions">
                      <ArrowUp size={16} onClick={(event) => { event.stopPropagation(); moveSection(section, -1); }} />
                      <ArrowDown size={16} onClick={(event) => { event.stopPropagation(); moveSection(section, 1); }} />
                    </span>
                  </button>
                ))}
              </div>
            </>
          )}
        </section>

        <section className="panel editor-panel">
          {selected ? (
            <Editor section={selected} updateSection={updateSection} saveTranscript={saveTranscript} />
          ) : (
            <div className="empty-state"><BookOpen size={36} /><p>Upload travel voice notes to begin building the manuscript.</p></div>
          )}
        </section>

        <section className="panel output-panel">
          <h2><Printer size={18} /> Summary and Export</h2>
          <div className="action-row">
            <button disabled={!sections.length} onClick={createSummary}><FileText size={17} /> Summarize</button>
            <button disabled={!sections.length} onClick={exportBatch}><Printer size={17} /> Export</button>
          </div>
          {summary && <pre className="output-text">{summary}</pre>}
          {exportFiles && (
            <div className="artifact-list">
              {Object.entries(exportFiles).map(([filename, content]) => (
                <button key={filename} className="fit" onClick={() => downloadTextFile(filename, content)}>
                  <Download size={16} /> {filename}
                </button>
              ))}
            </div>
          )}
        </section>
      </div>
      </main>
    </>
  );
}

function TravelScene() {
  return (
    <div className="travel-scene" aria-hidden="true">
      <div className="stars" />
      <div className="moon" />
      <div className="clouds" />
      <div className="mountains mountains-back" />
      <div className="mountains mountains-front" />
      <div className="tent" />
      <div className="campfire">
        <span className="flame" />
        <span className="flame flame-2" />
      </div>
    </div>
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

function Editor({ section, updateSection, saveTranscript }: {
  section: Section;
  updateSection: (id: string, patch: Partial<Section>) => void;
  saveTranscript: (section: Section) => void;
}) {
  return (
    <div className="editor-stack">
      <div className="transcript-grid">
        <label>Raw Transcript<textarea readOnly value={section.raw_text || ''} /></label>
        <label>Cleaned Transcript<textarea value={section.cleaned_text || ''} onChange={(event) => updateSection(section.id, { cleaned_text: event.target.value })} /></label>
        <label>Blog Draft<textarea value={section.blog_draft_text || ''} onChange={(event) => updateSection(section.id, { blog_draft_text: event.target.value })} /></label>
        <label>Chapter Draft<textarea value={section.chapter_draft_text || ''} onChange={(event) => updateSection(section.id, { chapter_draft_text: event.target.value })} /></label>
      </div>
      <button className="fit accent" onClick={() => saveTranscript(section)}><Save size={17} /> Save Review</button>
    </div>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
