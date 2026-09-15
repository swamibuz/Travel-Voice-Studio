import React from 'react';
import { createRoot } from 'react-dom/client';
import { AlertCircle, BookOpen, Clock, FileAudio, Globe2, Loader2, LogOut, RefreshCw, Upload } from 'lucide-react';
import './styles.css';

type User = { username: string };
type RecordingStatus = 'uploaded' | 'processing' | 'completed' | 'failed';
type Recording = {
  id: number;
  title: string;
  recorded_at: string | null;
  status: RecordingStatus;
  error?: string | null;
  transcript?: string;
};

type UploadStage = 'idle' | 'uploading' | 'ready-to-convert' | 'converting';

const apiBase = '/api';

function formatDateTime(iso: string | null): string {
  if (!iso) return '';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '';
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(date);
}

// The backend returns "# title\ndate line\n\nbody" — split it for styled display.
function parseTranscript(text: string): { title: string; dateLine: string; paragraphs: string[] } {
  const [headerBlock, ...rest] = text.split('\n\n');
  const headerLines = headerBlock.split('\n');
  const title = (headerLines[0] ?? '').replace(/^#\s*/, '');
  const dateLine = headerLines[1] ?? '';
  const body = rest.join('\n\n');
  return { title, dateLine, paragraphs: body ? body.split('\n\n') : [] };
}

function App() {
  const [token, setToken] = React.useState(localStorage.getItem('bookwriting-token') ?? '');
  const [user, setUser] = React.useState<User | null>(null);
  const [message, setMessage] = React.useState('');
  const [loginError, setLoginError] = React.useState('');
  const [recordings, setRecordings] = React.useState<Recording[]>([]);
  const [selectedId, setSelectedId] = React.useState<number | null>(null);
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [uploadStage, setUploadStage] = React.useState<UploadStage>('idle');
  const [activeId, setActiveId] = React.useState<number | null>(null);
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);

  const selected = recordings.find((recording) => recording.id === selectedId) ?? null;

  async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers = new Headers(options.headers);
    if (token) headers.set('Authorization', `Bearer ${token}`);
    const response = await fetch(`${apiBase}${path}`, { ...options, headers });
    if (response.status === 401) {
      // The token expired or is stale (e.g. the backend restarted with a new secret) — force a fresh login.
      localStorage.removeItem('bookwriting-token');
      setToken('');
      throw new Error('Your session expired. Please log in again.');
    }
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail ?? 'Request failed');
    }
    return response.json() as Promise<T>;
  }

  const loadRecordings = React.useCallback(async () => {
    if (!token) return;
    try {
      const payload = await request<{ items: Recording[] }>('/recordings');
      setRecordings(payload.items);
    } catch {
      // Session may have expired — the user will be prompted to log in again on their next action.
    }
  }, [token]);

  React.useEffect(() => {
    loadRecordings();
  }, [loadRecordings]);

  async function login(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoginError('');
    const data = new FormData(event.currentTarget);
    const result = await fetch(`${apiBase}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: data.get('username'), password: data.get('password') }),
    });
    if (!result.ok) {
      setLoginError('Invalid username or password.');
      return;
    }
    const payload = await result.json();
    localStorage.setItem('bookwriting-token', payload.token);
    setToken(payload.token);
    setUser(payload.user);
  }

  function logout() {
    localStorage.removeItem('bookwriting-token');
    setToken('');
    setUser(null);
    setRecordings([]);
    setSelectedId(null);
    setActiveId(null);
    setUploadStage('idle');
  }

  function chooseFile(event: React.ChangeEvent<HTMLInputElement>) {
    setSelectedFile(event.target.files?.[0] ?? null);
  }

  async function uploadFile() {
    if (!selectedFile) return;
    setUploadStage('uploading');
    setMessage(`Uploading "${selectedFile.name}"...`);
    try {
      const form = new FormData();
      form.append('file', selectedFile);
      form.append('original_name', selectedFile.name);
      form.append('recorded_at', new Date(selectedFile.lastModified).toISOString());
      const recording = await request<Recording>('/recordings', { method: 'POST', body: form });
      setRecordings((current) => [recording, ...current]);
      setSelectedId(recording.id);
      setActiveId(recording.id);
      setUploadStage('ready-to-convert');
      setMessage(`Uploaded "${selectedFile.name}". Click "Convert to Text" to transcribe it.`);
    } catch (error) {
      setUploadStage('idle');
      setMessage((error as Error).message);
    }
  }

  async function convertActive() {
    if (!activeId) return;
    setUploadStage('converting');
    setMessage('Converting the recording to text. This can take a while for long recordings...');
    try {
      const result = await request<Recording>(`/recordings/${activeId}/convert`, { method: 'POST' });
      setRecordings((current) => current.map((recording) => (recording.id === activeId ? result : recording)));
      setSelectedId(activeId);
      setUploadStage('idle');
      setActiveId(null);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      setMessage('Conversion complete.');
    } catch (error) {
      setUploadStage('ready-to-convert');
      setMessage((error as Error).message);
      setRecordings((current) =>
        current.map((recording) => (recording.id === activeId ? { ...recording, status: 'failed' } : recording)),
      );
    }
  }

  async function selectRecording(recording: Recording) {
    setSelectedId(recording.id);
    if (recording.status === 'completed' && recording.transcript === undefined) {
      try {
        const detail = await request<Recording>(`/recordings/${recording.id}`);
        setRecordings((current) => current.map((item) => (item.id === recording.id ? detail : item)));
      } catch (error) {
        setMessage((error as Error).message);
      }
    }
    if (recording.status === 'uploaded' || recording.status === 'failed') {
      setActiveId(recording.id);
      setUploadStage('ready-to-convert');
    }
  }

  if (!token) {
    return (
      <>
        <TravelScene />
        <LoginScreen onLogin={login} error={loginError} />
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
            <h1>Voice Notes to Book Chapters</h1>
          </div>
          <div className="topbar-right">
            {user && <span className="username-badge">{user.username}</span>}
            <button className="ghost" onClick={logout}><LogOut size={17} /> Logout</button>
          </div>
        </header>

        {message && <section className="status-line">{message}</section>}

        <div className="workspace-grid-simple">
          <section className="panel recordings-panel">
            <h2><Upload size={18} /> Upload a Recording</h2>
            <div className="stack upload-box">
              <input
                ref={fileInputRef}
                type="file"
                accept="audio/*,video/mp4"
                onChange={chooseFile}
                disabled={uploadStage === 'uploading' || uploadStage === 'converting'}
              />
              <button
                onClick={uploadFile}
                disabled={!selectedFile || uploadStage !== 'idle'}
              >
                {uploadStage === 'uploading' ? <Loader2 size={17} className="spin" /> : <FileAudio size={17} />}
                {uploadStage === 'uploading' ? 'Uploading...' : 'Upload'}
              </button>
              {(uploadStage === 'ready-to-convert' || uploadStage === 'converting') && (
                <button className="accent" onClick={convertActive} disabled={uploadStage === 'converting'}>
                  {uploadStage === 'converting' ? <Loader2 size={17} className="spin" /> : <RefreshCw size={17} />}
                  {uploadStage === 'converting' ? 'Converting...' : 'Convert to Text'}
                </button>
              )}
            </div>

            <h2 className="recordings-heading"><Clock size={18} /> Recordings</h2>
            <div className="recording-list">
              {recordings.length === 0 && <p className="empty-hint">No recordings yet.</p>}
              {recordings.map((recording) => (
                <button
                  key={recording.id}
                  className={selected?.id === recording.id ? 'recording-item active' : 'recording-item'}
                  onClick={() => selectRecording(recording)}
                >
                  <span>{recording.title}</span>
                  <small>{formatDateTime(recording.recorded_at)} · {recording.status}</small>
                </button>
              ))}
            </div>
          </section>

          <section className="panel transcript-panel">
            {selected && selected.status === 'completed' && selected.transcript ? (
              <TranscriptView transcript={selected.transcript} />
            ) : selected && selected.status === 'failed' ? (
              <div className="empty-state">
                <AlertCircle size={36} />
                <p>Conversion failed: {selected.error || 'Unknown error'}. Select it and click Convert to Text to retry.</p>
              </div>
            ) : selected ? (
              <div className="empty-state">
                <BookOpen size={36} />
                <p>Click "Convert to Text" to transcribe "{selected.title}".</p>
              </div>
            ) : (
              <div className="empty-state">
                <BookOpen size={36} />
                <p>Upload a voice recording to begin.</p>
              </div>
            )}
          </section>
        </div>
      </main>
    </>
  );
}

function TranscriptView({ transcript }: { transcript: string }) {
  const { title, dateLine, paragraphs } = parseTranscript(transcript);
  return (
    <div className="transcript-view">
      <h2 className="transcript-title">{title}</h2>
      {dateLine && <p className="transcript-date">{dateLine}</p>}
      <div className="transcript-body">
        {paragraphs.length ? paragraphs.map((paragraph, index) => <p key={index}>{paragraph}</p>) : <p>(No speech detected.)</p>}
      </div>
    </div>
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

function LoginScreen({ onLogin, error }: { onLogin: (event: React.FormEvent<HTMLFormElement>) => void; error: string }) {
  return (
    <main className="login-screen">
      <form className="login-card" onSubmit={onLogin}>
        <p className="eyebrow"><Globe2 size={16} /> BookWriting</p>
        <h1>Travel voice notes to book chapters</h1>
        <input name="username" aria-label="Username" placeholder="Username" autoComplete="username" />
        <input name="password" type="password" aria-label="Password" placeholder="Password" autoComplete="current-password" />
        <button>Login</button>
        {error && <p className="message-text error-text">{error}</p>}
      </form>
    </main>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
