import { guessArtistTitle } from "@/lib/format";
import type { DownloadOverrides, SearchResult } from "@/types";

export interface ArtistTitle {
  artist: string;
  title: string;
}

/** Con que artista/titulo arranca la ventana "Renombrar": lo que el usuario ya
 * edito, o los datos fijados (Spotify), o la misma limpieza que usa el backend. */
export function initialArtistTitle(result: SearchResult, manual?: ArtistTitle | null): ArtistTitle {
  if (manual) return manual;
  if (result.preset) return { artist: result.preset.artist, title: result.preset.title };
  if (result.title_guess) return { artist: result.artist_guess || "", title: result.title_guess };
  return guessArtistTitle(result.title);
}

/** Datos extra que van en el pedido de descarga. Un renombre manual pisa
 * artista/titulo pero conserva album/portada/año/nº de pista del origen. */
export function downloadOverrides(result: SearchResult, manual?: ArtistTitle | null): DownloadOverrides | undefined {
  const preset = result.preset;
  if (!manual && !preset) return undefined;
  const base: DownloadOverrides = preset
    ? {
        artist_override: preset.artist,
        title_override: preset.title,
        album: preset.album,
        cover_url: preset.cover_url,
        year: preset.year,
        track_number: preset.track_number,
      }
    : {};
  if (manual) {
    base.artist_override = manual.artist;
    base.title_override = manual.title;
  }
  return base;
}
