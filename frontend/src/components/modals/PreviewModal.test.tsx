import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PreviewModal } from "@/components/modals/PreviewModal";
import { ModalProvider, useModal } from "@/context/ModalContext";
import { getPreview } from "@/lib/api";

vi.mock("@/lib/api", () => ({ getPreview: vi.fn() }));

// jsdom no reproduce medios: se evita el error de autoplay
window.HTMLMediaElement.prototype.play = vi.fn(() => Promise.resolve());
window.HTMLMediaElement.prototype.pause = vi.fn();

function Opener() {
  const { openPreview } = useModal();
  return <button onClick={() => openPreview("abc", "Artista - Tema", "https://i.ytimg.com/vi/abc/hq.jpg")}>abrir</button>;
}

function setup() {
  render(
    <ModalProvider>
      <Opener />
      <PreviewModal />
    </ModalProvider>
  );
  fireEvent.click(screen.getByText("abrir"));
}

afterEach(() => {
  cleanup();
  vi.mocked(getPreview).mockReset();
});

describe("PreviewModal", () => {
  it("gives the stream to the player (audio only)", async () => {
    vi.mocked(getPreview).mockResolvedValue({
      ok: true,
      data: { stream_url: "https://rr1.googlevideo.com/audio", has_video: false, title: "x", duration: 1, thumbnail: "" },
    });
    setup();
    await waitFor(() => {
      const media = document.querySelector("audio, video") as HTMLMediaElement | null;
      expect(media?.getAttribute("src")).toBe("https://rr1.googlevideo.com/audio");
    });
    expect(screen.getByText("Vista previa solo de audio.")).toBeTruthy();
  });

  it("uses <video> when there is video", async () => {
    vi.mocked(getPreview).mockResolvedValue({
      ok: true,
      data: { stream_url: "https://rr1.googlevideo.com/v", has_video: true, title: "x", duration: 1, thumbnail: "" },
    });
    setup();
    await waitFor(() => expect(document.querySelector("video")?.getAttribute("src")).toBe("https://rr1.googlevideo.com/v"));
  });

  it("shows the server error", async () => {
    vi.mocked(getPreview).mockResolvedValue({ ok: false, data: { error: "Este video es privado." } });
    setup();
    expect(await screen.findByText("Este video es privado.")).toBeTruthy();
    expect(document.querySelector("audio, video")).toBeNull();
  });

  it("closing removes the player (stops playback)", async () => {
    vi.mocked(getPreview).mockResolvedValue({
      ok: true,
      data: { stream_url: "https://rr1.googlevideo.com/audio", has_video: false, title: "x", duration: 1, thumbnail: "" },
    });
    setup();
    await waitFor(() => expect(document.querySelector("audio")).not.toBeNull());
    await act(async () => fireEvent.click(screen.getByText("Cerrar (Esc)")));
    expect(document.querySelector("audio")).toBeNull();
  });
});
