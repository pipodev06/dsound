import { useEffect, useState } from "react";

import { Dialog, DialogContent, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useModal } from "@/context/ModalContext";

export function EditModal() {
  const { modal, closeModal } = useModal();
  const open = modal.type === "edit";
  const [artist, setArtist] = useState("");
  const [title, setTitle] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (modal.type === "edit") {
      setArtist(modal.artist);
      setTitle(modal.title);
    }
  }, [modal]);

  if (modal.type !== "edit") return null;

  async function handleSubmit(ev: React.FormEvent) {
    ev.preventDefault();
    if (modal.type !== "edit") return;
    const trimmedTitle = title.trim();
    if (!trimmedTitle) return;
    setSaving(true);
    try {
      await modal.onSave(artist.trim(), trimmedTitle);
      closeModal();
    } catch {
      // el callback ya logueo el error especifico; dejamos el modal abierto para reintentar
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={(next) => !next && closeModal()}>
      <DialogContent aria-label="Editar cancion">
        <DialogTitle>Editar cancion</DialogTitle>
        <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
          <Label className="flex flex-col items-start gap-1">
            <span>Artista</span>
            <Input autoComplete="off" value={artist} onChange={(e) => setArtist(e.target.value)} />
          </Label>
          <Label className="flex flex-col items-start gap-1">
            <span>Titulo</span>
            <Input autoComplete="off" value={title} onChange={(e) => setTitle(e.target.value)} autoFocus />
          </Label>
          <DialogFooter>
            <Button type="button" variant="ghost" size="sm" onClick={closeModal}>
              Cancelar
            </Button>
            <Button type="submit" size="sm" disabled={saving}>
              Guardar
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
