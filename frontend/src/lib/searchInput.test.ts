import { describe, expect, it } from "vitest";

import { classifyQuery } from "@/lib/searchInput";

describe("classifyQuery", () => {
  it("empty", () => {
    expect(classifyQuery("   ")).toEqual({ kind: "empty" });
  });

  it("plain keyword search", () => {
    expect(classifyQuery(" bad bunny monaco ")).toEqual({ kind: "keyword", query: "bad bunny monaco" });
  });

  it("youtube playlist and channel", () => {
    const pl = "https://www.youtube.com/watch?v=abc&list=PL123";
    expect(classifyQuery(pl)).toEqual({ kind: "youtubeCollection", url: pl });
    expect(classifyQuery("https://www.youtube.com/@artista").kind).toBe("youtubeCollection");
  });

  it("one or many youtube links", () => {
    expect(classifyQuery("https://youtu.be/a")).toEqual({ kind: "youtubeLinks", links: ["https://youtu.be/a"] });
    expect(classifyQuery("https://youtu.be/a\nhttps://youtu.be/b")).toEqual({
      kind: "youtubeLinks",
      links: ["https://youtu.be/a", "https://youtu.be/b"],
    });
  });

  it("a single link with extra words is a keyword search", () => {
    expect(classifyQuery("https://youtu.be/a cancion").kind).toBe("keyword");
  });

  it("spotify track vs playlist/album", () => {
    expect(classifyQuery("https://open.spotify.com/intl-es/track/123").kind).toBe("spotifyTrack");
    expect(classifyQuery("https://open.spotify.com/playlist/37i9dQ?si=x")).toEqual({
      kind: "spotifyCollection",
      url: "https://open.spotify.com/playlist/37i9dQ?si=x",
    });
    expect(classifyQuery("https://open.spotify.com/intl-es/album/4aaw").kind).toBe("spotifyCollection");
  });
});
