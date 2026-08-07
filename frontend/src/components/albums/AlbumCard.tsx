import { Button } from "@/components/ui/button";
import type { AlbumSummary } from "@/types";

interface AlbumCardProps {
  album: AlbumSummary;
  downloading: boolean;
  buttonLabel: string;
  onDownload: () => void;
}

export function AlbumCard({ album, downloading, buttonLabel, onDownload }: AlbumCardProps) {
  return (
    <li className="flex flex-col overflow-hidden rounded-md border border-border bg-surface">
      <div className="relative aspect-video bg-surface-2">
        <img className="block h-full w-full object-cover" src={album.thumbnail || ""} alt="" loading="lazy" />
      </div>
      <div className="flex flex-1 flex-col gap-1 p-3">
        <div className="line-clamp-2 font-mono text-[0.82rem] leading-tight text-text" title={album.title}>
          {album.title}
        </div>
        <div className="flex items-center justify-between gap-2">
          <div className="flex-1 overflow-hidden text-[0.72rem] text-ellipsis whitespace-nowrap text-text-muted">
            {album.artist || "?"}
            {album.year ? ` · ${album.year}` : ""}
          </div>
        </div>
        <div className="mt-auto flex gap-2 pt-2">
          <Button size="sm" className="flex-1" disabled={downloading} onClick={onDownload}>
            {buttonLabel}
          </Button>
        </div>
      </div>
    </li>
  );
}
