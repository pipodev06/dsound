import { useImperativeHandle, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { StatusLog } from "@/components/layout/StatusLog";
import { AlbumCard } from "@/components/albums/AlbumCard";
import { useModal } from "@/context/ModalContext";
import { downloadAlbum as downloadAlbumApi, searchAlbums } from "@/lib/api";
import { pollJob } from "@/lib/pollJob";
import type { AlbumSummary, DuplicateMode, LogLine, TabHandle } from "@/types";

const ALBUM_PAGE_STEP = 20;
const ALBUM_LIMIT_CAP = 100;

interface AlbumDownloadState {
  downloading: boolean;
  label: string;
}

const DEFAULT_STATE: AlbumDownloadState = { downloading: false, label: "Descargar album completo" };

export function AlbumsTab({ hidden, ref }: { hidden: boolean; ref?: React.Ref<TabHandle> }) {
  const { openDuplicateModal } = useModal();

  const [query, setQuery] = useState("");
  const [bitrate, setBitrate] = useState("320");
  const [results, setResults] = useState<AlbumSummary[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [downloadState, setDownloadState] = useState<Record<string, AlbumDownloadState>>({});
  const [logs, setLogs] = useState<LogLine[]>([]);
  const searchQueryRef = useRef("");

  function log(tag: LogLine["tag"], text: string) {
    setLogs((prev) => [...prev, { tag, text }]);
  }

  useImperativeHandle(ref, () => ({ log }));

  function setState(browseId: string, state: AlbumDownloadState) {
    setDownloadState((prev) => ({ ...prev, [browseId]: state }));
  }

  async function runSearch(q: string) {
    setLogs([{ tag: "info", text: `buscando albumes de "${q}"...` }]);
    setResults([]);
    setHasMore(false);
    searchQueryRef.current = q;
    try {
      const res = await searchAlbums(q, ALBUM_PAGE_STEP);
      if (!res.ok) {
        log("err", res.error || "busqueda de albumes fallida.");
        return;
      }
      const items = res.results || [];
      if (items.length === 0) {
        log("warn", "sin albumes encontrados.");
        return;
      }
      setResults(items);
      setHasMore(items.length >= ALBUM_PAGE_STEP && items.length < ALBUM_LIMIT_CAP);
      log("ok", `${items.length} album(es) para "${q}"`);
    } catch {
      log("err", "fallo de red al buscar albumes.");
    }
  }

  async function handleSubmit(ev: React.FormEvent) {
    ev.preventDefault();
    const q = query.trim();
    if (!q) return;
    await runSearch(q);
  }

  async function loadMore() {
    if (results.length >= ALBUM_LIMIT_CAP) return;
    setLoadingMore(true);
    try {
      const nextLimit = Math.min(results.length + ALBUM_PAGE_STEP, ALBUM_LIMIT_CAP);
      const res = await searchAlbums(searchQueryRef.current, nextLimit);
      if (!res.ok) {
        log("err", res.error || "no se pudieron cargar mas albumes.");
        return;
      }
      const newResults = res.results || [];
      if (newResults.length <= results.length) {
        log("info", "no hay mas albumes.");
        setHasMore(false);
        return;
      }
      setResults(newResults);
      setHasMore(newResults.length < ALBUM_LIMIT_CAP);
    } catch {
      log("err", "fallo de red al cargar mas albumes.");
    } finally {
      setLoadingMore(false);
    }
  }

  async function downloadAlbum(album: AlbumSummary) {
    setState(album.browse_id, { downloading: true, label: "Consultando tracks..." });
    try {
      let duplicateMode: DuplicateMode = null;
      let data;
      while (true) {
        const result = await downloadAlbumApi(album.browse_id, bitrate, duplicateMode);
        if (result.status === "duplicate") {
          const items = result.data.duplicates.map(
            (d) => `${d.title}${d.artist ? " - " + d.artist : ""} (ya existe "${d.existing}")`
          );
          const choice = await openDuplicateModal(`${result.data.duplicates.length} cancion(es) de este album ya las tienes:`, items);
          if (choice === "cancel") {
            log("warn", "descarga de album cancelada.");
            setState(album.browse_id, DEFAULT_STATE);
            return;
          }
          duplicateMode = choice;
          continue;
        }
        if (result.status === "error") {
          log("err", result.error);
          setState(album.browse_id, DEFAULT_STATE);
          return;
        }
        data = result.data;
        break;
      }
      const jobs = data.tracks.filter((t) => !t.skipped);
      for (const t of data.tracks) {
        if (t.skipped) log("warn", `omitido "${t.title}" (ya existe "${t.existing}")`);
      }
      let done = 0;
      log("info", `descargando album "${data.album}": ${jobs.length} track(s)...`);
      setState(album.browse_id, { downloading: true, label: `Descargando 0/${jobs.length}` });
      await Promise.all(
        jobs.map(async (t) => {
          const job = await pollJob(t.job_id!);
          done++;
          setState(album.browse_id, { downloading: true, label: `Descargando ${done}/${jobs.length}` });
          if (job.status === "done" && job.result) {
            log("ok", `${job.result.artist} - ${job.result.title}`);
          } else if (job.status === "cancelled") {
            log("warn", `cancelado: ${t.artist} - ${t.title}`);
          } else {
            log("err", `${t.artist} - ${t.title}: ${job.error || "no se pudo descargar."}`);
          }
        })
      );
      setState(album.browse_id, { downloading: true, label: "Album descargado" });
    } catch {
      log("err", "fallo de red al descargar el album.");
      setState(album.browse_id, DEFAULT_STATE);
    }
  }

  return (
    <div className={hidden ? "hidden" : undefined}>
      <form className="mx-auto mb-6 flex max-w-[720px] items-center gap-3 rounded-md border border-border bg-surface px-4 py-3" onSubmit={handleSubmit}>
        <Label htmlFor="album-query" className="font-mono font-semibold text-accent">
          album &gt;
        </Label>
        <input
          id="album-query"
          className="min-w-0 flex-1 border-0 border-b border-transparent bg-transparent pb-0.5 font-mono text-[0.95rem] text-text outline-none placeholder:text-text-muted focus:border-accent focus-visible:outline-none"
          type="text"
          placeholder="buscar album o artista"
          autoComplete="off"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button type="submit">Buscar</Button>
      </form>

      <div className="mb-6 flex items-center justify-center gap-2 font-mono text-[0.78rem] text-text-muted">
        <Label htmlFor="album-bitrate-select">calidad</Label>
        <Select value={bitrate} onValueChange={setBitrate}>
          <SelectTrigger id="album-bitrate-select">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="128">128 kbps</SelectItem>
            <SelectItem value="192">192 kbps</SelectItem>
            <SelectItem value="320">320 kbps</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <ul className="m-0 mb-4 grid grid-cols-2 gap-4 p-0 sm:grid-cols-3 min-[900px]:grid-cols-4 min-[1100px]:grid-cols-5">
        {results.map((album) => (
          <AlbumCard
            key={album.browse_id}
            album={album}
            downloading={downloadState[album.browse_id]?.downloading ?? DEFAULT_STATE.downloading}
            buttonLabel={downloadState[album.browse_id]?.label ?? DEFAULT_STATE.label}
            onDownload={() => downloadAlbum(album)}
          />
        ))}
      </ul>

      {hasMore && (
        <Button variant="ghost" className="mx-auto mb-8 block" disabled={loadingMore} onClick={loadMore}>
          {loadingMore ? "Cargando..." : "Mas Resultados..."}
        </Button>
      )}

      <StatusLog lines={logs} />
    </div>
  );
}
