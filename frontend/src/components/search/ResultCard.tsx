import { IconDownload, IconExternalLink, IconPencil, IconPlayerPlay } from "@tabler/icons-react";

import { Checkbox } from "@/components/ui/checkbox";
import { IconButton } from "@/components/ui/icon-button";
import { formatDuration } from "@/lib/format";
import type { SearchResult } from "@/types";

interface ResultCardProps {
  result: SearchResult;
  selected: boolean;
  override: { artist: string; title: string } | null;
  downloadDisabled: boolean;
  downloadTitle: string;
  onToggleSelect: (checked: boolean) => void;
  onListen: () => void;
  onRename: () => void;
  onDownload: () => void;
}

export function ResultCard({
  result,
  selected,
  override,
  downloadDisabled,
  downloadTitle,
  onToggleSelect,
  onListen,
  onRename,
  onDownload,
}: ResultCardProps) {
  const label = override ? (override.artist ? `${override.artist} - ${override.title}` : override.title) : result.title;

  return (
    <li className="relative flex flex-col overflow-hidden rounded-md border border-border bg-surface">
      <label className="absolute top-2 left-2 z-1 flex cursor-pointer rounded-[4px] bg-bg/55 p-[3px]">
        <Checkbox
          aria-label={`Seleccionar ${result.title}`}
          checked={selected}
          onCheckedChange={(checked) => onToggleSelect(checked === true)}
        />
      </label>
      <div className="relative aspect-video bg-surface-2">
        <img className="block h-full w-full object-cover" src={result.thumbnail || ""} alt="" loading="lazy" />
        <button
          type="button"
          className="absolute inset-0 m-auto flex size-10 items-center justify-center rounded-full border-none bg-bg/55 text-text transition-colors hover:bg-bg/85"
          aria-label="Escuchar preview"
          onClick={onListen}
        >
          <IconPlayerPlay className="size-4" />
        </button>
      </div>
      <div className="flex flex-1 flex-col gap-1 p-3">
        <div className="line-clamp-2 font-mono text-[0.82rem] leading-tight text-text" title={label}>
          {label}
        </div>
        <div className="overflow-hidden text-[0.72rem] text-ellipsis whitespace-nowrap text-text-muted">
          {result.channel || "?"} · {formatDuration(result.duration)}
        </div>
        <div className="mt-auto flex gap-2 pt-2">
          <IconButton aria-label="Escuchar" title="Escuchar" onClick={onListen}>
            <IconPlayerPlay />
          </IconButton>
          <IconButton
            variant="accent"
            aria-label="Descargar"
            title={downloadTitle}
            disabled={downloadDisabled}
            onClick={onDownload}
          >
            <IconDownload />
          </IconButton>
          <IconButton aria-label="Renombrar" title="Renombrar" onClick={onRename}>
            <IconPencil />
          </IconButton>
          <IconButton asChild aria-label="Ir al enlace" title="Ver en YouTube">
            <a href={result.webpage_url} target="_blank" rel="noopener noreferrer">
              <IconExternalLink />
            </a>
          </IconButton>
        </div>
      </div>
    </li>
  );
}
