import { describe, expect, it } from "vitest";

import { progressLabel, progressPercent } from "@/lib/progress";

describe("progress", () => {
  it("percent", () => {
    expect(progressPercent({ status: "downloading", progress: 42.7 })).toBe(42);
    expect(progressPercent({ status: "downloading", progress: null })).toBeNull();
    expect(progressPercent({ status: "queued", progress: null })).toBeNull();
    expect(progressPercent({ status: "done", progress: null })).toBe(100);
    expect(progressPercent({ status: "downloading", progress: 140 })).toBe(100);
  });

  it("label", () => {
    expect(progressLabel({ status: "queued" })).toBe("En cola...");
    expect(progressLabel({ status: "downloading", phase: "downloading", progress: 9.9 })).toBe("Descargando 9%");
    expect(progressLabel({ status: "downloading", phase: "downloading", progress: null })).toBe("Descargando...");
    expect(progressLabel({ status: "downloading", phase: "converting", progress: 100 })).toBe("Convirtiendo a mp3...");
    expect(progressLabel({ status: "done" })).toBe("");
  });
});
