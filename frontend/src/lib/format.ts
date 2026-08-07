export function formatDuration(seconds: number): string {
  const total = Math.round(seconds || 0);
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

export function formatBytes(bytes: number): string {
  const mb = (bytes || 0) / (1024 * 1024);
  return `${mb.toFixed(1)} MB`;
}

export function guessArtistTitle(rawTitle: string): { artist: string; title: string } {
  const parts = (rawTitle || "").split(" - ");
  if (parts.length >= 2) {
    return { artist: parts[0].trim(), title: parts.slice(1).join(" - ").trim() };
  }
  return { artist: "", title: (rawTitle || "").trim() };
}
