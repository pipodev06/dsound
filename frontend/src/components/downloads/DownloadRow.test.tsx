import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DownloadRow } from "@/components/downloads/DownloadRow";
import type { JobListItem } from "@/types";

const job: JobListItem = {
  id: "1",
  status: "downloading",
  display: "Artista - Tema",
  album: null,
  phase: "downloading",
  progress: 37.5,
  webpage_url: "https://youtu.be/x",
  bitrate: "320",
  title_hint: "",
  artist_override: null,
  title_override: null,
};

afterEach(cleanup);

describe("DownloadRow", () => {
  it("shows a progress bar with the percentage while downloading", () => {
    render(<DownloadRow job={job} onCancel={vi.fn()} onRetry={vi.fn()} />);
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("37");
    expect((bar.firstChild as HTMLElement).style.width).toBe("37%");
    expect(screen.getByText("descargando 37%")).toBeTruthy();
  });

  it("shows converting phase without a fake percentage", () => {
    render(<DownloadRow job={{ ...job, phase: "converting", progress: 100 }} onCancel={vi.fn()} onRetry={vi.fn()} />);
    expect(screen.getByText("convirtiendo a mp3...")).toBeTruthy();
    expect((screen.getByRole("progressbar").firstChild as HTMLElement).style.width).toBe("");
  });

  it("no bar once finished", () => {
    render(<DownloadRow job={{ ...job, status: "done", phase: null }} onCancel={vi.fn()} onRetry={vi.fn()} />);
    expect(screen.queryByRole("progressbar")).toBeNull();
    expect(screen.getByText("listo")).toBeTruthy();
  });
});
