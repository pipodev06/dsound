import type {
  AlbumDetail,
  AlbumDownloadResponse,
  AlbumDuplicateError,
  AlbumSummary,
  DownloadDuplicateError,
  DownloadOverrides,
  DuplicateMode,
  Job,
  JobListItem,
  LibraryItem,
  OutputDirPickResponse,
  PreviewResponse,
  SearchResult,
  SpotifyCollectionResponse,
  StatusResponse,
} from "@/types";

/** fetch + si el server pide login (dsound abierto desde otro dispositivo con
 * DSOUND_PASSWORD), manda a la pagina de login en vez de mostrar errores raros. */
async function apiFetch(input: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(input, init);
  if (res.status === 401) {
    window.location.assign("/login");
  }
  return res;
}

// Lee el body como JSON sin romper si el server devolvio otra cosa (ej. una
// pagina HTML de error 500 de Flask): en ese caso devuelve un objeto con
// `error`, asi los llamadores muestran un mensaje en vez de tirar una excepcion.
async function getJson<T>(res: Response): Promise<T> {
  try {
    return (await res.json()) as T;
  } catch {
    return { error: `error del servidor (HTTP ${res.status})` } as T;
  }
}

export async function getStatus(): Promise<StatusResponse> {
  const res = await apiFetch("/api/status");
  return getJson(res);
}

export async function resolveSpotify(url: string): Promise<{ ok: boolean; query?: string; error?: string }> {
  const res = await apiFetch(`/api/resolve-spotify?url=${encodeURIComponent(url)}`);
  const data = await getJson<{ query?: string; error?: string }>(res);
  return { ok: res.ok, ...data };
}

export async function search(query: string, limit: number): Promise<{ ok: boolean; results?: SearchResult[]; error?: string }> {
  const res = await apiFetch(`/api/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  const data = await getJson<{ results?: SearchResult[]; error?: string }>(res);
  return { ok: res.ok, ...data };
}

export async function getPlaylist(url: string, limit: number): Promise<{ ok: boolean; results?: SearchResult[]; error?: string }> {
  const res = await apiFetch(`/api/playlist?url=${encodeURIComponent(url)}&limit=${limit}`);
  const data = await getJson<{ results?: SearchResult[]; error?: string }>(res);
  return { ok: res.ok, ...data };
}

export async function getSpotifyCollection(
  url: string
): Promise<{ ok: boolean; data?: SpotifyCollectionResponse; error?: string }> {
  const res = await apiFetch(`/api/spotify-collection?url=${encodeURIComponent(url)}`);
  const data = await getJson<SpotifyCollectionResponse & { error?: string }>(res);
  if (!res.ok) return { ok: false, error: data.error || "no se pudo leer la playlist/album de Spotify." };
  return { ok: true, data };
}

export async function searchAlbums(query: string, limit: number): Promise<{ ok: boolean; results?: AlbumSummary[]; error?: string }> {
  const res = await apiFetch(`/api/albums/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  const data = await getJson<{ results?: AlbumSummary[]; error?: string }>(res);
  return { ok: res.ok, ...data };
}

export async function getAlbum(browseId: string): Promise<AlbumDetail> {
  const res = await apiFetch(`/api/albums/${encodeURIComponent(browseId)}`);
  return getJson(res);
}

export type AlbumDownloadResult =
  | { status: "duplicate"; data: AlbumDuplicateError }
  | { status: "error"; error: string }
  | { status: "ok"; data: AlbumDownloadResponse };

export async function downloadAlbum(
  browseId: string,
  bitrate: string,
  duplicateMode: DuplicateMode
): Promise<AlbumDownloadResult> {
  const res = await apiFetch(`/api/albums/${encodeURIComponent(browseId)}/download`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ bitrate, duplicate_mode: duplicateMode }),
  });
  const data = await getJson<{ duplicate?: boolean; error?: string }>(res);
  if (res.status === 409 && data.duplicate) return { status: "duplicate", data: data as AlbumDuplicateError };
  if (!res.ok) return { status: "error", error: data.error || "no se pudo descargar el album." };
  return { status: "ok", data: data as AlbumDownloadResponse };
}

export async function getPreview(videoId: string): Promise<{ ok: boolean; data: PreviewResponse | { error: string } }> {
  const res = await apiFetch(`/api/preview/${encodeURIComponent(videoId)}`);
  const data = await getJson<PreviewResponse | { error: string }>(res);
  return { ok: res.ok, data };
}

export type DownloadResult =
  | { status: "duplicate"; existing: string }
  | { status: "error"; error: string }
  | { status: "ok"; jobId: string };

export async function requestDownload(
  webpageUrl: string,
  titleHint: string,
  confirm: boolean,
  bitrate: string,
  overrides?: DownloadOverrides
): Promise<DownloadResult> {
  const res = await apiFetch("/api/download", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      webpage_url: webpageUrl,
      title: titleHint,
      confirm,
      bitrate,
      ...(overrides || {}),
    }),
  });
  const data = await getJson<{ duplicate?: boolean; error?: string; job_id?: string }>(res);
  if (res.status === 409 && data.duplicate) {
    const dup = data as DownloadDuplicateError;
    return { status: "duplicate", existing: dup.existing };
  }
  if (!res.ok) return { status: "error", error: data.error || "no se pudo descargar." };
  if (!data.job_id) return { status: "error", error: "respuesta inesperada del servidor." };
  return { status: "ok", jobId: data.job_id };
}

export async function getJob(jobId: string): Promise<{ ok: boolean; job: Job }> {
  const res = await apiFetch(`/api/jobs/${jobId}`);
  const job = await getJson<Job>(res);
  return { ok: res.ok, job };
}

export async function listJobs(): Promise<JobListItem[]> {
  const res = await apiFetch("/api/jobs");
  const data = await getJson<{ jobs: JobListItem[] }>(res);
  return data.jobs || [];
}

export async function cancelJob(jobId: string): Promise<{ ok: boolean }> {
  const res = await apiFetch(`/api/jobs/${jobId}/cancel`, { method: "POST" });
  return { ok: res.ok };
}

export async function getLibrary(): Promise<LibraryItem[]> {
  const res = await apiFetch("/api/library");
  const data = await getJson<{ items: LibraryItem[] }>(res);
  return data.items || [];
}

export async function deleteLibraryItem(filename: string): Promise<{ ok: boolean; error?: string }> {
  const res = await apiFetch(`/api/library/${encodeURIComponent(filename)}`, { method: "DELETE" });
  const data = await getJson<{ error?: string }>(res);
  return { ok: res.ok, error: data.error };
}

export async function updateLibraryItem(
  filename: string,
  artist: string,
  title: string
): Promise<{ ok: boolean; error?: string }> {
  const res = await apiFetch(`/api/library/${encodeURIComponent(filename)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ artist, title }),
  });
  const data = await getJson<{ error?: string }>(res);
  return { ok: res.ok, error: data.error };
}

export async function pickOutputDir(): Promise<OutputDirPickResponse> {
  const res = await apiFetch("/api/output-dir/pick", { method: "POST" });
  return getJson(res);
}

export async function setOutputDir(path: string): Promise<{ output_dir?: string; error?: string }> {
  const res = await apiFetch("/api/output-dir", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path }),
  });
  return getJson(res);
}
