import { Dialog, DialogContent, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useModal } from "@/context/ModalContext";

export function DuplicateModal() {
  const { modal, closeModal } = useModal();
  const open = modal.type === "duplicate";

  if (modal.type !== "duplicate") return null;

  function resolve(choice: "cancel" | "skip" | "force") {
    if (modal.type !== "duplicate") return;
    modal.resolve(choice);
    closeModal();
  }

  return (
    <Dialog open={open} onOpenChange={(next) => !next && resolve("cancel")}>
      <DialogContent aria-label="Posible duplicado">
        <div className="text-sm text-text">{modal.text}</div>
        {modal.items && modal.items.length > 0 && (
          <div className="flex max-h-48 flex-col gap-1 overflow-y-auto rounded-md border border-border bg-surface-2 p-2 font-mono text-xs text-text-muted">
            {modal.items.map((item, i) => (
              <div key={i}>{item}</div>
            ))}
          </div>
        )}
        <DialogFooter>
          <Button variant="ghost" size="sm" onClick={() => resolve("cancel")}>
            Cancelar
          </Button>
          {modal.items && modal.items.length > 0 && (
            <Button variant="ghost" size="sm" onClick={() => resolve("skip")}>
              Omitir y descargar el resto
            </Button>
          )}
          <Button size="sm" onClick={() => resolve("force")}>
            Descargar de todos modos
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
