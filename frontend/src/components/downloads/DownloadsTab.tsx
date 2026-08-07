import { DownloadRow } from "@/components/downloads/DownloadRow";
import { useJobs } from "@/context/JobsContext";

export function DownloadsTab({ hidden }: { hidden: boolean }) {
  const { jobs, cancel, retry } = useJobs();

  return (
    <div className={hidden ? "hidden" : undefined}>
      <div className="mb-4 flex items-center justify-between gap-3">
        <span className="text-[0.78rem] text-text-muted">
          {jobs.length} descarga{jobs.length === 1 ? "" : "s"}
        </span>
      </div>

      <ul className="m-0 mb-8 flex flex-col gap-2 p-0">
        {jobs.length === 0 && <li className="text-[0.9rem] text-text-muted">no hay descargas todavia.</li>}
        {jobs.map((job) => (
          <DownloadRow key={job.id} job={job} onCancel={() => cancel(job.id)} onRetry={() => retry(job)} />
        ))}
      </ul>
    </div>
  );
}
