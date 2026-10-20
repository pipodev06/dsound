import { useImperativeHandle, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { StatusLog } from "@/components/layout/StatusLog";
import { ResultCard } from "@/components/search/ResultCard";
import { SelectionBar } from "@/components/common/SelectionBar";
import { useModal } from "@/context/ModalContext";
import { getPlaylist, requestDownload, resolveSpotify, search as searchApi } from "@/lib/api";
import { pollJob } from "@/lib/pollJob";
import { guessArtistTitle } from "@/lib/format";
import type { DownloadOverrides, LogLine, SearchResult, TabHandle } from "@/types";

const YOUTUBE_HOST_RE = /youtube\.com|youtu\.be/;
const YOUTUBE_PLAYLIST_RE = /[?&]list=/;
const YOUTUBE_CHANNEL_RE = /youtube\.com\/(channel\/|@|c\/|user\/)/;
const SPOTIFY_TRACK_RE = /open\.spotify\.com\/(?:[\w-]+\/)?track\//;
const PAGE_SIZE = 25;
const SEARCH_LIMIT_CAP = 300;
const PLAYLIST_LIMIT = 100;

interface DownloadState {
  disabled: boolean;
  label: string;
}

const DEFAULT_DOWNLOAD_STATE: DownloadState = { disabled: false, label: "Descargar" };

interface SearchTabProps {
  hidden: boolean;
  bitrate: string;
  searchInputRef: React.RefObject<HTMLInputElement | null>;
  ref?: React.Ref<TabHandle>;
}

export function SearchTab({ hidden, bitrate, searchInputRef, ref }: SearchTabProps) {
  const { openPreview, openEditModal, openDuplicateModal } = useModal();

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [shownCount, setShownCount] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [overrides, setOverrides] = useState<Record<string, { artist: string; title: string }>>({});
  const [downloadState, setDownloadState] = useState<Record<string, DownloadState>>({});
  const [logs, setLogs] = useState<LogLine[]>([]);
  const [searchMode, setSearchMode] = useState<"keyword" | "playlist">("keyword");
  const searchQueryRef = useRef("");

  function log(tag: LogLine["tag"], text: string) {
    setLogs((prev) => [...prev, { tag, text }]);
  }

  useImperativeHandle(ref, () => ({ log }));

  function setDlState(id: string, state: DownloadState) {
    setDownloadState((prev) => ({ ...prev, [id]: state }));
  }

  function overridesFor(id: string): DownloadOverrides | undefined {
    const o = overrides[id];
    return o ? { artist_override: o.artist, title_override: o.title } : undefined;
  }

  async function downloadOne(result: SearchResult, confirmDuplicate = false) {
    setDlState(result.id, { disabled: true, label: "En cola..." });
    try {
      const res = await requestDownload(result.webpage_url, result.title, confirmDuplicate, bitrate, overridesFor(result.id));
      if (res.status === "duplicate") {
        setDlState(result.id, DEFAULT_DOWNLOAD_STATE);
        const choice = await openDuplicateModal(`Ya tienes algo parecido: "${res.existing}". ¿Descargar de todos modos?`, null);
        if (choice === "force") return downloadOne(result, true);
        log("warn", `omitido (ya existe "${res.existing}")`);
        return;
      }
      if (res.status === "error") {
        log("err", res.error);
        setDlState(result.id, DEFAULT_DOWNLOAD_STATE);
        return;
      }
      const job = await pollJob(res.jobId, (j) => {
        if (j.status === "downloading") setDlState(result.id, { disabled: true, label: "Descargando..." });
      });
      if (job.status === "done" && job.result) {
        log("ok", job.result.artist ? `${job.result.artist} - ${job.result.title}` : job.result.title);
        setDlState(result.id, { disabled: true, label: "Descargado" });
      } else if (job.status === "cancelled") {
        log("warn", `cancelado: ${result.title}`);
        setDlState(result.id, DEFAULT_DOWNLOAD_STATE);
      } else {
        log("err", job.error || "no se pudo descargar.");
        setDlState(result.id, DEFAULT_DOWNLOAD_STATE);
      }
    } catch {
      log("err", `${result.title}: fallo de red.`);
      setDlState(result.id, DEFAULT_DOWNLOAD_STATE);
    }
  }

  async function downloadDirectLink(url: string) {
    log("info", "descargando enlace...");
    try {
      const res = await requestDownload(url, "", false, bitrate);
      if (res.status === "duplicate") {
        log("warn", `omitido (ya existe "${res.existing}")`);
        return;
      }
      if (res.status === "error") {
        log("err", res.error);
        return;
      }
      let lastStatus = "";
      const job = await pollJob(res.jobId, (j) => {
        if (j.status === lastStatus) return;
        lastStatus = j.status;
        if (j.status === "queued") log("info", "hay otras descargas en cola, espera...");
        else if (j.status === "downloading") log("info", "descargando...");
      });
      if (job.status === "done" && job.result) {
        log("ok", job.result.artist ? `${job.result.artist} - ${job.result.title}` : job.result.title);
      } else if (job.status === "cancelled") {
        log("warn", "descarga cancelada.");
      } else {
        log("err", job.error || "no se pudo descargar.");
      }
    } catch {
      log("err", "fallo de red al descargar el link.");
    }
  }

  async function downloadMultipleLinks(links: string[]) {
    log("info", `descargando ${links.length} enlaces...`);
    await Promise.all(links.map((url) => downloadDirectLink(url)));
  }

  async function runSearch(q: string) {
    log("info", `buscando "${q}"...`);
    setResults([]);
    setShownCount(0);
    setSearchMode("keyword");
    searchQueryRef.current = q;
    try {
      const res = await searchApi(q, PAGE_SIZE);
      if (!res.ok) {
        log("err", res.error || "busqueda fallida.");
        return;
      }
      const items = res.results || [];
      if (items.length === 0) {
        log("warn", "sin resultados.");
        return;
      }
      setResults(items);
      setShownCount(Math.min(PAGE_SIZE, items.length));
      setSelectedIds(new Set());
      log("ok", `${items.length} resultado(s) para "${q}"`);
    } catch {
      log("err", "fallo de red al buscar.");
    }
  }

  async function runPlaylistSearch(url: string) {
    log("info", "leyendo playlist/canal...");
    setResults([]);
    setShownCount(0);
    setSearchMode("playlist");
    try {
      const res = await getPlaylist(url, PLAYLIST_LIMIT);
      if (!res.ok) {
        log("err", res.error || "no se pudo leer la playlist.");
        return;
      }
      const items = res.results || [];
      if (items.length === 0) {
        log("warn", "sin videos encontrados.");
        return;
      }
      setResults(items);
      setShownCount(Math.min(PAGE_SIZE, items.length));
      setSelectedIds(new Set());
      log("ok", `${items.length} video(s) encontrados (primeros ${PLAYLIST_LIMIT} como maximo)`);
    } catch {
      log("err", "fallo de red al leer la playlist.");
    }
  }

  async function resolveSpotifyAndSearch(url: string) {
    log("info", "leyendo link de Spotify...");
    setResults([]);
    setShownCount(0);
    try {
      const res = await resolveSpotify(url);
      if (!res.ok || !res.query) {
        log("err", res.error || "no se pudo leer el link de Spotify.");
        return;
      }
      log("ok", `Spotify: "${res.query}"`);
      setQuery(res.query);
      await runSearch(res.query);
    } catch {
      log("err", "fallo de red al leer el link de Spotify.");
    }
  }

  async function handleSubmit(ev: React.FormEvent) {
    ev.preventDefault();
    const q = query.trim();
    if (!q) return;
    setLogs([]);

    const tokens = q.split(/\s+/).filter(Boolean);

    if (tokens.length === 1 && (YOUTUBE_PLAYLIST_RE.test(q) || YOUTUBE_CHANNEL_RE.test(q))) {
      await runPlaylistSearch(q);
      return;
    }

    const links = tokens.filter(
      (t) => YOUTUBE_HOST_RE.test(t) && !YOUTUBE_PLAYLIST_RE.test(t) && !YOUTUBE_CHANNEL_RE.test(t)
    );

    if (links.length > 1) {
      setQuery("");
      setResults([]);
      setShownCount(0);
      await downloadMultipleLinks(links);
      return;
    }
    if (links.length === 1 && tokens.length === 1) {
      setQuery("");
      setResults([]);
      setShownCount(0);
      await downloadDirectLink(links[0]);
      return;
    }
    if (SPOTIFY_TRACK_RE.test(q)) {
      await resolveSpotifyAndSearch(q);
      return;
    }
    await runSearch(q);
  }

  async function loadMore() {
    if (shownCount < results.length) {
      setShownCount((prev) => Math.min(prev + PAGE_SIZE, results.length));
      return;
    }
    // las playlists/canales se traen completas (hasta el tope) de una sola vez,
    // no re-fetchean con limit creciente como una busqueda por texto
    if (searchMode === "playlist" || results.length >= SEARCH_LIMIT_CAP) return;
    setLoadingMore(true);
    try {
      const nextLimit = Math.min(results.length + PAGE_SIZE, SEARCH_LIMIT_CAP);
      const res = await searchApi(searchQueryRef.current, nextLimit);
      if (!res.ok) {
        log("err", res.error || "no se pudieron cargar mas resultados.");
        return;
      }
      const newResults = res.results || [];
      if (newResults.length <= results.length) {
        log("info", "no hay mas resultados.");
        return;
      }
      setResults(newResults);
      setShownCount((prev) => Math.min(prev + PAGE_SIZE, newResults.length));
    } catch {
      log("err", "fallo de red al cargar mas resultados.");
    } finally {
      setLoadingMore(false);
    }
  }

  function toggleSelect(id: string, checked: boolean) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (checked) next.add(id);
      else next.delete(id);
      return next;
    });
  }

  function handleRename(result: SearchResult) {
    const current = overrides[result.id] || guessArtistTitle(result.title);
    openEditModal(current.artist, current.title, async (artist, title) => {
      setOverrides((prev) => ({ ...prev, [result.id]: { artist, title } }));
    });
  }

  function handleBatchDownload() {
    for (const result of results) {
      if (selectedIds.has(result.id)) downloadOne(result);
    }
    setSelectedIds(new Set());
  }

  const visible = results.slice(0, shownCount);
  const exhausted =
    shownCount >= results.length && (searchMode === "playlist" || results.length >= SEARCH_LIMIT_CAP);
  const showLoadMore = results.length > 0 && !exhausted;

  return (
    <div className={hidden ? "hidden" : undefined}>
      <form className="mx-auto mb-6 flex max-w-[960px] items-center gap-3 rounded-md border border-border bg-surface px-4 py-3" onSubmit={handleSubmit}>
        <Label htmlFor="query" className="font-mono font-semibold text-accent">
          música &gt;
        </Label>
        <input
          id="query"
          ref={searchInputRef}
          className="min-w-0 flex-1 border-0 border-b border-transparent bg-transparent pb-0.5 font-mono text-[0.95rem] text-text outline-none placeholder:text-text-muted focus:border-accent focus-visible:outline-none"
          type="text"
          placeholder="buscar cancion, pegar link(s) de YouTube, playlist/canal, o de Spotify"
          autoComplete="off"
          autoFocus
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button type="submit">Buscar</Button>
      </form>

      <SelectionBar
        count={selectedIds.size}
        actionLabel="Descargar seleccionadas"
        onAction={handleBatchDownload}
        onClear={() => setSelectedIds(new Set())}
      />

      <ul className="m-0 mb-4 grid grid-cols-2 gap-4 p-0 sm:grid-cols-3 min-[900px]:grid-cols-4 min-[1100px]:grid-cols-5">
        {visible.map((result) => (
          <ResultCard
            key={result.id}
            result={result}
            selected={selectedIds.has(result.id)}
            override={overrides[result.id] || null}
            downloadDisabled={downloadState[result.id]?.disabled ?? DEFAULT_DOWNLOAD_STATE.disabled}
            downloadTitle={downloadState[result.id]?.label ?? DEFAULT_DOWNLOAD_STATE.label}
            onToggleSelect={(checked) => toggleSelect(result.id, checked)}
            onListen={() => openPreview(result.id, result.title, result.thumbnail)}
            onRename={() => handleRename(result)}
            onDownload={() => downloadOne(result)}
          />
        ))}
      </ul>

      {showLoadMore && (
        <Button variant="ghost" className="mx-auto mb-8 block" disabled={loadingMore} onClick={loadMore}>
          {loadingMore ? "Cargando..." : "Mas Resultados..."}
        </Button>
      )}

      <StatusLog lines={logs} />
    </div>
  );
}
