import type { Job } from "@/types";

/** Porcentaje entero 0-100 para la barra, o null si todavia no se sabe. */
export function progressPercent(job: Pick<Job, "status" | "progress">): number | null {
  if (job.status === "done") return 100;
  if (job.status !== "downloading" || job.progress == null) return null;
  return Math.max(0, Math.min(100, Math.floor(job.progress)));
}

/** Texto corto del estado de una descarga en curso. */
export function progressLabel(job: Pick<Job, "status" | "phase" | "progress">): string {
  if (job.status === "queued") return "En cola...";
  if (job.status !== "downloading") return "";
  if (job.phase === "converting") return "Convirtiendo a mp3...";
  const pct = progressPercent(job);
  return pct === null ? "Descargando..." : `Descargando ${pct}%`;
}
