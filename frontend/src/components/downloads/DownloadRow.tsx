import { IconRefresh, IconX } from "@tabler/icons-react";

import { IconButton } from "@/components/ui/icon-button";
import type { JobListItem, JobStatus } from "@/types";

const STATUS_LABEL: Record<JobStatus, string> = {
  queued: "en cola",
  downloading: "descargando",
  done: "listo",
  error: "error",
  cancelled: "cancelado",
};

const STATUS_COLOR: Record<JobStatus, string> = {
  queued: "text-info",
  downloading: "text-info",
  done: "text-accent",
  error: "text-danger",
  cancelled: "text-warn",
};

interface DownloadRowProps {
  job: JobListItem;
  onCancel: () => void;
  onRetry: () => void;
}

export function DownloadRow({ job, onCancel, onRetry }: DownloadRowProps) {
  const cancellable = job.status === "queued" || job.status === "downloading";
  const retriable = job.status === "error" || job.status === "cancelled";

  return (
    <li className="flex items-center justify-between gap-4 rounded-md border border-border bg-surface p-3">
      <div className="min-w-0 flex-1">
        <div className="overflow-hidden text-ellipsis whitespace-nowrap font-mono text-[0.88rem] text-text" title={job.display}>
          {job.display}
        </div>
        <div className={`text-[0.75rem] ${STATUS_COLOR[job.status]}`}>
          {STATUS_LABEL[job.status]}
          {job.status === "error" && job.error ? `: ${job.error}` : ""}
          {job.album ? ` · ${job.album}` : ""}
        </div>
      </div>
      {cancellable && (
        <IconButton variant="danger" aria-label="Cancelar descarga" title="Cancelar" onClick={onCancel}>
          <IconX />
        </IconButton>
      )}
      {retriable && (
        <IconButton aria-label="Reintentar descarga" title="Reintentar" onClick={onRetry}>
          <IconRefresh />
        </IconButton>
      )}
    </li>
  );
}
