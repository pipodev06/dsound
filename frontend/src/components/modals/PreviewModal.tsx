import { useEffect, useRef, useState } from "react";

import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useModal } from "@/context/ModalContext";
import { getPreview } from "@/lib/api";

export function PreviewModal() {
  const { modal, closeModal } = useModal();
  const open = modal.type === "preview";
  const videoRef = useRef<HTMLVideoElement>(null);
  const [status, setStatus] = useState("");
  const requestId = useRef(0);

  useEffect(() => {
    if (!open || modal.type !== "preview") return;
    const id = ++requestId.current;
    setStatus("cargando preview...");
    const video = videoRef.current;
    if (video) video.removeAttribute("src");

    getPreview(modal.videoId).then(({ ok, data }) => {
      if (id !== requestId.current) return; // se cerro o abrio otro mientras cargaba
      if (!ok || "error" in data) {
        setStatus(("error" in data && data.error) || "no se pudo cargar el preview.");
        return;
      }
      setStatus(data.has_video ? "" : "solo audio disponible para este video.");
      if (video) {
        video.src = data.stream_url;
        video.play().catch(() => setStatus("toca play para reproducir."));
      }
    });
  }, [open, modal]);

  function handleClose() {
    requestId.current++;
    const video = videoRef.current;
    if (video) {
      video.pause();
      video.removeAttribute("src");
      video.load();
    }
    closeModal();
  }

  if (modal.type !== "preview") return null;

  return (
    <Dialog open={open} onOpenChange={(next) => !next && handleClose()}>
      <DialogContent aria-label="Preview" showCloseButton={false}>
        <video
          ref={videoRef}
          className="max-h-[70vh] w-full rounded-md bg-bg"
          poster={modal.thumbnail}
          controls
          playsInline
          preload="none"
        />
        <DialogTitle>{modal.title}</DialogTitle>
        {status && <div className="text-sm text-text-muted">{status}</div>}
        <Button variant="ghost" size="sm" onClick={handleClose}>
          Cerrar (Esc)
        </Button>
      </DialogContent>
    </Dialog>
  );
}
