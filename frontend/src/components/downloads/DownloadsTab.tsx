import { Button } from "@/components/ui/button";
import { DownloadRow } from "@/components/downloads/DownloadRow";
import { useJobs } from "@/context/JobsContext";

interface DownloadsTabProps {
  hidden: boolean;
  /** "Abrir carpeta" solo funciona en la PC donde se ejecuta dsound */
  canOpenFolder: boolean;
  onOpenFolder: () => void;
}

export function DownloadsTab({ hidden, canOpenFolder, onOpenFolder }: DownloadsTabProps) {
  const { jobs, cancel, retry, clearFinished } = useJobs();
  const finished = jobs.filter((j) => j.status === "done" || j.status === "error" || j.status === "cancelled").length;

  return (
    <div className={hidden ? "hidden" : undefined}>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <span className="text-[0.78rem] text-text-muted">
          {jobs.length} {jobs.length === 1 ? "descarga" : "descargas"}
        </span>
        <div className="flex gap-2">
          {canOpenFolder && (
            <Button variant="ghost" size="sm" onClick={onOpenFolder}>
              Abrir carpeta
            </Button>
          )}
          <Button variant="ghost" size="sm" disabled={finished === 0} onClick={() => clearFinished()}>
            Limpiar terminadas
          </Button>
        </div>
      </div>

      <ul className="m-0 mb-8 flex flex-col gap-2 p-0">
        {jobs.length === 0 && (
          <li className="py-16 text-center text-[0.9rem] text-text-muted">No hay descargas en curso.</li>
        )}
        {jobs.map((job) => (
          <DownloadRow key={job.id} job={job} onCancel={() => cancel(job.id)} onRetry={() => retry(job)} />
        ))}
      </ul>
    </div>
  );
}
