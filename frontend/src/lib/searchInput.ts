// Que hacer con lo que se escribe/pega en el buscador.

const YOUTUBE_HOST_RE = /youtube\.com|youtu\.be/;
const YOUTUBE_PLAYLIST_RE = /[?&]list=/;
const YOUTUBE_CHANNEL_RE = /youtube\.com\/(channel\/|@|c\/|user\/)/;
const SPOTIFY_TRACK_RE = /open\.spotify\.com\/(?:[\w-]+\/)?track\//;
const SPOTIFY_COLLECTION_RE = /open\.spotify\.com\/(?:[\w-]+\/)?(playlist|album)\//;

export type ParsedQuery =
  | { kind: "empty" }
  | { kind: "youtubeCollection"; url: string }
  | { kind: "youtubeLinks"; links: string[] }
  | { kind: "spotifyTrack"; url: string }
  | { kind: "spotifyCollection"; url: string }
  | { kind: "keyword"; query: string };

export function classifyQuery(raw: string): ParsedQuery {
  const q = raw.trim();
  if (!q) return { kind: "empty" };
  const tokens = q.split(/\s+/).filter(Boolean);

  if (tokens.length === 1 && (YOUTUBE_PLAYLIST_RE.test(q) || YOUTUBE_CHANNEL_RE.test(q))) {
    return { kind: "youtubeCollection", url: q };
  }

  const links = tokens.filter(
    (t) => YOUTUBE_HOST_RE.test(t) && !YOUTUBE_PLAYLIST_RE.test(t) && !YOUTUBE_CHANNEL_RE.test(t)
  );
  // varios links (aunque haya texto suelto), o un unico link solo
  if (links.length > 1 || (links.length === 1 && tokens.length === 1)) {
    return { kind: "youtubeLinks", links };
  }

  if (tokens.length === 1 && SPOTIFY_COLLECTION_RE.test(q)) return { kind: "spotifyCollection", url: q };
  if (SPOTIFY_TRACK_RE.test(q)) return { kind: "spotifyTrack", url: q };
  return { kind: "keyword", query: q };
}
