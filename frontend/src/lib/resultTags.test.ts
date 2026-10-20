import { describe, expect, it } from "vitest";

import { downloadOverrides, initialArtistTitle } from "@/lib/resultTags";
import type { SearchResult } from "@/types";

const base: SearchResult = {
  id: "x",
  title: "Bad Bunny - Monaco (Official Video)",
  channel: "Bad Bunny",
  duration: 200,
  thumbnail: "",
  webpage_url: "https://youtu.be/x",
};

const preset = {
  artist: "Pitbull, Sensato",
  title: "Global Warming",
  album: "Global Warming",
  cover_url: "https://image-cdn-fa.spotifycdn.com/image/big",
  year: "2012",
  track_number: 1,
};

describe("initialArtistTitle", () => {
  it("uses the backend cleaned guess, not the raw video title", () => {
    expect(initialArtistTitle({ ...base, artist_guess: "Bad Bunny", title_guess: "Monaco" })).toEqual({
      artist: "Bad Bunny",
      title: "Monaco",
    });
  });

  it("prefers manual edits, then preset", () => {
    expect(initialArtistTitle({ ...base, preset }, { artist: "Yo", title: "Tema" })).toEqual({ artist: "Yo", title: "Tema" });
    expect(initialArtistTitle({ ...base, preset })).toEqual({ artist: "Pitbull, Sensato", title: "Global Warming" });
  });

  it("falls back to splitting the title", () => {
    expect(initialArtistTitle(base)).toEqual({ artist: "Bad Bunny", title: "Monaco (Official Video)" });
  });
});

describe("downloadOverrides", () => {
  it("nothing to send for a plain result", () => {
    expect(downloadOverrides(base)).toBeUndefined();
  });

  it("manual rename only", () => {
    expect(downloadOverrides(base, { artist: "A", title: "B" })).toEqual({ artist_override: "A", title_override: "B" });
  });

  it("preset sends album tags", () => {
    expect(downloadOverrides({ ...base, preset })).toEqual({
      artist_override: "Pitbull, Sensato",
      title_override: "Global Warming",
      album: "Global Warming",
      cover_url: "https://image-cdn-fa.spotifycdn.com/image/big",
      year: "2012",
      track_number: 1,
    });
  });

  it("manual rename keeps preset album tags", () => {
    const o = downloadOverrides({ ...base, preset }, { artist: "Pitbull", title: "GW" });
    expect(o?.artist_override).toBe("Pitbull");
    expect(o?.title_override).toBe("GW");
    expect(o?.album).toBe("Global Warming");
    expect(o?.track_number).toBe(1);
  });
});
