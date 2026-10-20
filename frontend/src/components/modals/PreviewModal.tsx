import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { useModal } from "@/context/ModalContext";
import { getPreview } from "@/lib/api";
import type { PreviewResponse } from "@/types";

type PreviewState = { videoId: string; stream?: PreviewResponse; error?: string };

/** Vista previa de un resultado antes de descargarlo.
 *
 * La URL del stream se pasa al reproductor como prop (src) en el render. Antes
 * se buscaba el <video> con un ref dentro del efecto, pero el Dialog dibuja su
 * contenido un instante después (portal), así que el ref todavía estaba vacío y
 * el reproductor quedaba sin fuente: la vista previa nunca sonaba. */
export function PreviewModal() {
  const { modal, closeModal } = useModal();
  const videoId = modal.type === "preview" ? modal.videoId : null;
  const [state, setState] = useState<PreviewState | null>(null);

  useEffect(() => {
    if (!videoId) return;
    let cancelled = false;
    getPreview(videoId)
      .then(({ ok, data }) => {
        if (cancelled) return;
        if (!ok || "error" in data) {
          setState({ videoId, error: ("error" in data && data.error) || "no se pudo cargar la vista previa." });
        } else {
          setState({ videoId, stream: data });
        }
      })
      .catch(() => {
        if (!cancelled) setState({ videoId, error: "error de red al cargar la vista previa." });
      });
    return () => {
      cancelled = true;
    };
  }, [videoId]);

  if (modal.type !== "preview") return null;

  // si quedó guardado el estado de otro video, todavía se está cargando este
  const current = state && state.videoId === modal.videoId ? state : null;
  const stream = current?.stream;

  return (
    <Dialog open onOpenChange={(next) => !next && closeModal()}>
      <DialogContent aria-label="Vista previa" showCloseButton={false}>
        {stream?.has_video ? (
          <video
            key={modal.videoId}
            className="max-h-[70vh] w-full rounded-md bg-bg"
            src={stream.stream_url}
            poster={modal.thumbnail}
            controls
            autoPlay
            playsInline
          />
        ) : (
          <>
            {modal.thumbnail && (
              <img className="max-h-[50vh] w-full rounded-md bg-bg object-cover" src={modal.thumbnail} alt="" />
            )}
            {stream && (
              <audio key={modal.videoId} className="w-full" src={stream.stream_url} controls autoPlay />
            )}
          </>
        )}
        <DialogTitle>{modal.title}</DialogTitle>
        <div className="text-sm text-text-muted" role="status">
          {!current && "cargando vista previa..."}
          {current?.error}
          {stream && !stream.has_video && "Vista previa solo de audio."}
        </div>
        <Button variant="ghost" size="sm" onClick={closeModal}>
          Cerrar (Esc)
        </Button>
      </DialogContent>
    </Dialog>
  );
}
