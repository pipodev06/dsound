/** Tags ya decididos por el origen (ej. un album/playlist de Spotify): el mp3
 * se baja con estos datos en vez de adivinarlos del titulo del video. */
export interface ResultPreset {
  artist: string;
  title: string;
  album: string | null;
  cover_url: string | null;
  year: string | null;
  track_number: number | null;
}

export interface SearchResult {
  id: string;
  title: string;
  channel: string;
  duration: number;
  thumbnail: string;
  webpage_url: string;
  /** artista/titulo limpios (misma limpieza que usa el backend al bajar) */
  artist_guess?: string;
  title_guess?: string;
  preset?: ResultPreset;
}

export interface SpotifyCollectionResponse {
  kind: "playlist" | "album";
  name: string;
  total: number;
  results: SearchResult[];
  missing: string[];
}

export interface AlbumSummary {
  browse_id: string;
  title: string;
  artist: string;
  year: string;
  thumbnail: string;
  explicit: boolean;
}

export interface AlbumTrack {
  video_id: string;
  title: string;
  artist: string;
  duration: number;
}

export interface AlbumDetail {
  browse_id: string;
  title: string;
  artist: string;
  year: string;
  thumbnail: string;
  track_count: number;
  tracks: AlbumTrack[];
}

export interface LibraryItem {
  filename: string;
  title: string;
  artist: string;
  size: number;
  mtime: number;
}

export type JobStatus = "queued" | "downloading" | "done" | "error" | "cancelled";

/** "downloading" = bajando el audio, "converting" = ffmpeg pasandolo a mp3 */
export type JobPhase = "downloading" | "converting" | null;

export interface Job {
  status: JobStatus;
  result?: { filename: string; artist: string; title: string; album?: string | null };
  error?: string;
  phase?: JobPhase;
  progress?: number | null;
}

export interface JobListItem {
  id: string;
  status: JobStatus;
  display: string;
  thumbnail?: string | null;
  album: string | null;
  result?: { filename: string; artist: string; title: string; album?: string | null };
  error?: string;
  phase?: JobPhase;
  progress?: number | null;
  webpage_url: string;
  bitrate: string | null;
  title_hint: string;
  artist_override: string | null;
  title_override: string | null;
}

export interface StatusResponse {
  ffmpeg: boolean;
  ffmpeg_message: string;
  output_dir: string;
  version?: string;
  /** true si la página se abrió en la misma PC donde se ejecuta dsound */
  local?: boolean;
}

export interface Settings {
  /** navegador del que se toman las cookies de YouTube ("" = ninguno) */
  cookies_browser: string;
  cookie_browsers: string[];
  music_metadata: boolean;
}

export interface UpdateInfo {
  current: string;
  latest: string | null;
  url: string | null;
  update_available: boolean;
}

export interface ApiError {
  error: string;
}

export interface DownloadDuplicateError extends ApiError {
  duplicate: true;
  existing: string;
}

export interface AlbumDuplicateItem {
  title: string;
  artist: string;
  existing: string;
}

export interface AlbumDuplicateError {
  duplicate: true;
  album: string;
  duplicates: AlbumDuplicateItem[];
}

export interface AlbumDownloadTrack {
  title: string;
  artist: string;
  skipped: boolean;
  existing?: string;
  job_id?: string;
}

export interface AlbumDownloadResponse {
  album: string;
  artist: string;
  tracks: AlbumDownloadTrack[];
}

export type DuplicateMode = "skip" | "force" | null;

export interface PreviewResponse {
  stream_url: string;
  has_video: boolean;
  title: string;
  duration: number;
  thumbnail: string;
}

export interface OutputDirPickResponse {
  available?: boolean;
  cancelled?: boolean;
  output_dir?: string;
  error?: string;
}

export interface DownloadOverrides {
  artist_override?: string;
  title_override?: string;
  album?: string | null;
  cover_url?: string | null;
  year?: string | null;
  track_number?: number | null;
  /** miniatura para mostrar en la pestaña Descargas */
  thumbnail?: string | null;
}

export type LogTag = "ok" | "err" | "info" | "warn";

export interface LogLine {
  /** unico dentro de la pestaña, para usarlo de key */
  id: number;
  tag: LogTag;
  text: string;
}

export interface TabHandle {
  log: (tag: LogTag, text: string) => void;
}
