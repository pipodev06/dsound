import { Button } from "@/components/ui/button";
import type { VariantProps } from "class-variance-authority";
import type { buttonVariants } from "@/components/ui/button";

interface SelectionBarProps {
  count: number;
  actionLabel: string;
  actionVariant?: VariantProps<typeof buttonVariants>["variant"];
  onAction: () => void;
  onClear: () => void;
}

export function SelectionBar({ count, actionLabel, actionVariant = "accent", onAction, onClear }: SelectionBarProps) {
  if (count === 0) return null;

  return (
    <div className="mb-4 flex items-center gap-3 rounded-md border border-accent bg-surface px-4 py-3">
      <span className="mr-auto font-mono text-[0.85rem] text-accent">
        {count} seleccionada{count === 1 ? "" : "s"}
      </span>
      <Button size="sm" variant={actionVariant} onClick={onAction}>
        {actionLabel}
      </Button>
      <Button variant="ghost" size="sm" onClick={onClear}>
        Cancelar
      </Button>
    </div>
  );
}
