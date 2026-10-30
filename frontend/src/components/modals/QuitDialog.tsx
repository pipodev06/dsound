import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogTitle } from "@/components/ui/dialog";

interface QuitDialogProps {
  open: boolean;
  activeDownloads: number;
  onCancel: () => void;
  onConfirm: () => void;
}

export function QuitDialog({ open, activeDownloads, onCancel, onConfirm }: QuitDialogProps) {
  return (
    <Dialog open={open} onOpenChange={(next) => !next && onCancel()}>
      <DialogContent aria-label="Cerrar dsound">
        <DialogTitle>¿Cerrar dsound?</DialogTitle>
        <p className="m-0 text-sm text-text-muted">
          {activeDownloads > 0
            ? `Hay ${activeDownloads} ${activeDownloads === 1 ? "descarga pendiente" : "descargas pendientes"}: continuarán la próxima vez que abras dsound.`
            : "Para volver a usarlo, abre dsound de nuevo."}
        </p>
        <DialogFooter>
          <Button variant="ghost" size="sm" onClick={onCancel}>
            Cancelar
          </Button>
          <Button variant="danger" size="sm" onClick={onConfirm}>
            Cerrar dsound
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
