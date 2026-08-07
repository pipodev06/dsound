import { useState } from "react";

import { Dialog, DialogContent, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useModal } from "@/context/ModalContext";

export function ConfirmDeleteModal() {
  const { modal, closeModal } = useModal();
  const open = modal.type === "confirmDelete";
  const [deleting, setDeleting] = useState(false);

  if (modal.type !== "confirmDelete") return null;

  async function handleConfirm() {
    if (modal.type !== "confirmDelete") return;
    setDeleting(true);
    try {
      await modal.onConfirm();
      closeModal();
    } finally {
      setDeleting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={(next) => !next && closeModal()}>
      <DialogContent aria-label="Confirmar eliminacion">
        <div className="text-sm text-text">{modal.text}</div>
        {modal.items && modal.items.length > 0 && (
          <div className="flex max-h-48 flex-col gap-1 overflow-y-auto rounded-md border border-border bg-surface-2 p-2 font-mono text-xs text-text-muted">
            {modal.items.map((item, i) => (
              <div key={i}>{item}</div>
            ))}
          </div>
        )}
        <DialogFooter>
          <Button variant="ghost" size="sm" onClick={closeModal}>
            Cancelar
          </Button>
          <Button variant="danger" size="sm" disabled={deleting} onClick={handleConfirm}>
            Eliminar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
