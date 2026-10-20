import { useState } from "react";

import { useModal } from "@/context/ModalContext";
import { requestDownload } from "@/lib/api";
import { pollJob } from "@/lib/pollJob";
import { progressLabel } from "@/lib/progress";
import { downloadOverrides, initialArtistTitle, type ArtistTitle } from "@/lib/resultTags";
import type { LogLine, SearchResult } from "@/types";

export interface DownloadState {
  disabled: boolean;
  label: string;
}

export const DEFAULT_DOWNLOAD_STATE: DownloadState = { disabled: false, label: "Descargar" };

type Log = (tag: LogLine["tag"], text: string) => void;

function doneLabel(result: { artist: string; title: string }) {
  return result.artist ? `${result.artist} - ${result.title}` : result.title;
}

/** Descargas que se lanzan desde la pestaña Buscar: de a un resultado, links
 * pegados directo, y renombres manuales antes de bajar. */
export function useResultDownloads(bitrate: string, log: Log) {
  const { openEditModal, openDuplicateModal } = useModal();
  const [manual, setManual] = useState<Record<string, ArtistTitle>>({});
  const [states, setStates] = useState<Record<string, DownloadState>>({});

  function setState(id: string, state: DownloadState) {
    setStates((prev) => ({ ...prev, [id]: state }));
  }

  async function downloadOne(result: SearchResult, confirmDuplicate = false): Promise<void> {
    setState(result.id, { disabled: true, label: "En cola..." });
    try {
      const res = await requestDownload(
        result.webpage_url,
        result.title,
        confirmDuplicate,
        bitrate,
        { ...downloadOverrides(result, manual[result.id]), thumbnail: result.thumbnail || null }
      );
      if (res.status === "duplicate") {
        setState(result.id, DEFAULT_DOWNLOAD_STATE);
        const choice = await openDuplicateModal(`Ya tienes algo parecido: "${res.existing}". ¿Descargar de todos modos?`, null);
        if (choice === "force") return downloadOne(result, true);
        log("warn", `omitido (ya existe "${res.existing}")`);
        return;
      }
      if (res.status === "error") {
        log("err", res.error);
        setState(result.id, DEFAULT_DOWNLOAD_STATE);
        return;
      }
      const job = await pollJob(res.jobId, (j) => {
        const label = progressLabel(j);
        if (label) setState(result.id, { disabled: true, label });
      });
      if (job.status === "done" && job.result) {
        log("ok", doneLabel(job.result));
        setState(result.id, { disabled: true, label: "Descargado" });
      } else if (job.status === "cancelled") {
        log("warn", `cancelado: ${result.title}`);
        setState(result.id, DEFAULT_DOWNLOAD_STATE);
      } else {
        log("err", job.error || "no se pudo descargar.");
        setState(result.id, DEFAULT_DOWNLOAD_STATE);
      }
    } catch {
      log("err", `${result.title}: error de red.`);
      setState(result.id, DEFAULT_DOWNLOAD_STATE);
    }
  }

  async function downloadLink(url: string) {
    try {
      const res = await requestDownload(url, "", false, bitrate);
      if (res.status === "duplicate") return log("warn", `omitido (ya existe "${res.existing}")`);
      if (res.status === "error") return log("err", res.error);
      let lastLabel = "";
      const job = await pollJob(res.jobId, (j) => {
        const label = progressLabel(j);
        // el log no se llena de porcentajes: solo cambios de fase
        const phase = label.replace(/\d+%$/, "");
        if (!label || phase === lastLabel) return;
        lastLabel = phase;
        if (j.status === "queued") log("info", "hay otras descargas en cola, espera...");
        else log("info", label.toLowerCase());
      });
      if (job.status === "done" && job.result) log("ok", doneLabel(job.result));
      else if (job.status === "cancelled") log("warn", "descarga cancelada.");
      else log("err", job.error || "no se pudo descargar.");
    } catch {
      log("err", "error de red al descargar el enlace.");
    }
  }

  async function downloadLinks(links: string[]) {
    log("info", links.length === 1 ? "descargando enlace..." : `descargando ${links.length} enlaces...`);
    await Promise.all(links.map((url) => downloadLink(url)));
  }

  function rename(result: SearchResult) {
    const current = initialArtistTitle(result, manual[result.id]);
    openEditModal(current.artist, current.title, async (artist, title) => {
      setManual((prev) => ({ ...prev, [result.id]: { artist, title } }));
    });
  }

  function stateFor(id: string): DownloadState {
    return states[id] ?? DEFAULT_DOWNLOAD_STATE;
  }

  /** Lo que muestra la tarjeta: el renombre manual o los datos fijados (Spotify). */
  function labelOverride(result: SearchResult): ArtistTitle | null {
    return manual[result.id] || (result.preset ? { artist: result.preset.artist, title: result.preset.title } : null);
  }

  return { downloadOne, downloadLinks, rename, stateFor, labelOverride };
}
