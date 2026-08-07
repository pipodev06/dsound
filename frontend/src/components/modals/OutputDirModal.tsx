import { useEffect, useState } from "react";

import { Dialog, DialogContent, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useModal } from "@/context/ModalContext";

export function OutputDirModal() {
  const { modal, closeModal } = useModal();
  const open = modal.type === "outputDir";
  const [path, setPath] = useState("");

  useEffect(() => {
    if (modal.type === "outputDir") setPath(modal.currentPath);
  }, [modal]);

  if (modal.type !== "outputDir") return null;

  function resolve(value: string | null) {
    if (modal.type !== "outputDir") return;
    modal.resolve(value);
    closeModal();
  }

  function handleSubmit(ev: React.FormEvent) {
    ev.preventDefault();
    const trimmed = path.trim();
    if (!trimmed) return;
    resolve(trimmed);
  }

  return (
    <Dialog open={open} onOpenChange={(next) => !next && resolve(null)}>
      <DialogContent aria-label="Cambiar carpeta de salida">
        <DialogTitle>Carpeta de salida</DialogTitle>
        <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
          <Label className="flex flex-col items-start gap-1">
            <span>Ruta de la carpeta</span>
            <Input autoComplete="off" value={path} onChange={(e) => setPath(e.target.value)} autoFocus />
          </Label>
          <DialogFooter>
            <Button type="button" variant="ghost" size="sm" onClick={() => resolve(null)}>
              Cancelar
            </Button>
            <Button type="submit" size="sm">
              Guardar
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
