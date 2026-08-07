import { IconPencil, IconTrash } from "@tabler/icons-react";

import { Checkbox } from "@/components/ui/checkbox";
import { IconButton } from "@/components/ui/icon-button";
import { formatBytes } from "@/lib/format";
import type { LibraryItem } from "@/types";

interface LibraryRowProps {
  item: LibraryItem;
  selected: boolean;
  onToggleSelect: (checked: boolean) => void;
  onEdit: () => void;
  onDelete: () => void;
}

export function LibraryRow({ item, selected, onToggleSelect, onEdit, onDelete }: LibraryRowProps) {
  const label = item.artist ? `${item.artist} - ${item.title}` : item.title;

  return (
    <li className="flex items-center gap-4 rounded-md border border-border bg-surface p-3">
      <Checkbox
        aria-label={`Seleccionar ${label}`}
        checked={selected}
        onCheckedChange={(checked) => onToggleSelect(checked === true)}
      />
      <div className="min-w-0 flex-1">
        <div className="overflow-hidden text-ellipsis whitespace-nowrap font-mono text-[0.88rem] text-text" title={label}>
          {label}
        </div>
        <div className="text-[0.75rem] text-text-muted">{formatBytes(item.size)}</div>
      </div>
      <div className="flex shrink-0 items-center gap-3">
        <audio className="h-8 max-w-[280px]" controls preload="none" src={`/library/${encodeURIComponent(item.filename)}`} />
        <IconButton aria-label="Editar" title="Editar" onClick={onEdit}>
          <IconPencil />
        </IconButton>
        <IconButton variant="danger" aria-label="Eliminar" title="Eliminar" onClick={onDelete}>
          <IconTrash />
        </IconButton>
      </div>
    </li>
  );
}
