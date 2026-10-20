import { useRef, useState } from "react";

import { getPlaylist, getSpotifyCollection, resolveSpotify, search as searchApi } from "@/lib/api";
import type { LogLine, SearchResult } from "@/types";

export const PAGE_SIZE = 25;
export const SEARCH_LIMIT_CAP = 300;
const PLAYLIST_LIMIT = 100;

type Log = (tag: LogLine["tag"], text: string) => void;

/** Resultados de la grilla de Buscar: busqueda por texto (paginada, "Mas
 * resultados" vuelve a pedir con un limite mayor), playlists/canales de
 * YouTube y links de Spotify. Tambien la seleccion para bajar en lote. */
export function useSearchResults(log: Log) {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [shownCount, setShownCount] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);
  // "keyword" se puede seguir paginando contra el server; "fixed" (playlist,
  // canal, Spotify) ya viene completa de una
  const [mode, setMode] = useState<"keyword" | "fixed">("keyword");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const lastQueryRef = useRef("");

  function reset(nextMode: "keyword" | "fixed") {
    setResults([]);
    setShownCount(0);
    setMode(nextMode);
  }

  function show(items: SearchResult[]) {
    setResults(items);
    setShownCount(Math.min(PAGE_SIZE, items.length));
    setSelectedIds(new Set());
  }

  async function runSearch(q: string) {
    log("info", `buscando "${q}"...`);
    reset("keyword");
    lastQueryRef.current = q;
    try {
      const res = await searchApi(q, PAGE_SIZE);
      if (!res.ok) return log("err", res.error || "busqueda fallida.");
      const items = res.results || [];
      if (items.length === 0) return log("warn", "sin resultados.");
      show(items);
      log("ok", `${items.length} resultado(s) para "${q}"`);
    } catch {
      log("err", "fallo de red al buscar.");
    }
  }

  async function runYoutubeCollection(url: string) {
    log("info", "leyendo playlist/canal...");
    reset("fixed");
    try {
      const res = await getPlaylist(url, PLAYLIST_LIMIT);
      if (!res.ok) return log("err", res.error || "no se pudo leer la playlist.");
      const items = res.results || [];
      if (items.length === 0) return log("warn", "sin videos encontrados.");
      show(items);
      log("ok", `${items.length} video(s) encontrados (primeros ${PLAYLIST_LIMIT} como maximo)`);
    } catch {
      log("err", "fallo de red al leer la playlist.");
    }
  }

  /** Track de Spotify -> "Artista Titulo" -> busqueda normal. Devuelve la
   * query resuelta para mostrarla en el buscador. */
  async function runSpotifyTrack(url: string): Promise<string | null> {
    log("info", "leyendo link de Spotify...");
    reset("keyword");
    try {
      const res = await resolveSpotify(url);
      if (!res.ok || !res.query) {
        log("err", res.error || "no se pudo leer el link de Spotify.");
        return null;
      }
      log("ok", `Spotify: "${res.query}"`);
      await runSearch(res.query);
      return res.query;
    } catch {
      log("err", "fallo de red al leer el link de Spotify.");
      return null;
    }
  }

  async function runSpotifyCollection(url: string) {
    log("info", "leyendo playlist/album de Spotify y buscando cada tema en YouTube (puede tardar un poco)...");
    reset("fixed");
    try {
      const res = await getSpotifyCollection(url);
      if (!res.ok || !res.data) return log("err", res.error || "no se pudo leer el link de Spotify.");
      const { kind, name, total, results: items, missing } = res.data;
      show(items);
      // se viene a bajar la playlist/album entero: quedan todos tildados
      setSelectedIds(new Set(items.map((r) => r.id)));
      const what = kind === "album" ? "album" : "playlist";
      log("ok", `Spotify ${what} "${name}": ${items.length} de ${total} tema(s) encontrados en YouTube`);
      if (missing.length > 0) log("warn", `sin coincidencia en YouTube: ${missing.join(", ")}`);
      if (items.length > 0) log("info", 'quedaron todos seleccionados: usa "Descargar seleccionadas" para bajarlos.');
    } catch {
      log("err", "fallo de red al leer el link de Spotify.");
    }
  }

  async function loadMore() {
    if (shownCount < results.length) {
      setShownCount((prev) => Math.min(prev + PAGE_SIZE, results.length));
      return;
    }
    if (mode === "fixed" || results.length >= SEARCH_LIMIT_CAP) return;
    setLoadingMore(true);
    try {
      const nextLimit = Math.min(results.length + PAGE_SIZE, SEARCH_LIMIT_CAP);
      const res = await searchApi(lastQueryRef.current, nextLimit);
      if (!res.ok) return log("err", res.error || "no se pudieron cargar mas resultados.");
      const newResults = res.results || [];
      if (newResults.length <= results.length) return log("info", "no hay mas resultados.");
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

  const visible = results.slice(0, shownCount);
  const exhausted = shownCount >= results.length && (mode === "fixed" || results.length >= SEARCH_LIMIT_CAP);

  return {
    results,
    visible,
    canLoadMore: results.length > 0 && !exhausted,
    loadingMore,
    selectedIds,
    clearSelection: () => setSelectedIds(new Set()),
    toggleSelect,
    clearResults: () => reset("keyword"),
    runSearch,
    runYoutubeCollection,
    runSpotifyTrack,
    runSpotifyCollection,
    loadMore,
  };
}
