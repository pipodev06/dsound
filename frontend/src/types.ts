export interface SearchResult {
  id: string;
  title: string;
  channel: string;
  duration: number;
  thumbnail: string;
  webpage_url: string;
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

export interface Job {
  status: JobStatus;
  result?: { filename: string; artist: string; title: string };
  error?: string;
}

export interface JobListItem {
  id: string;
  status: JobStatus;
  display: string;
  album: string | null;
  result?: { filename: string; artist: string; title: string };
  error?: string;
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
}

export type LogTag = "ok" | "err" | "info" | "warn";

export interface LogLine {
  tag: LogTag;
  text: string;
}

export interface TabHandle {
  log: (tag: LogTag, text: string) => void;
}
