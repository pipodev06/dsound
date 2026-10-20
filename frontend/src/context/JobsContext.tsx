import * as React from "react";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { cancelJob, listJobs, requestDownload } from "@/lib/api";
import type { JobListItem } from "@/types";

const POLL_MS = 2000;

interface JobsContextValue {
  jobs: JobListItem[];
  activeCount: number;
  cancel: (id: string) => Promise<void>;
  retry: (job: JobListItem) => Promise<void>;
}

const JobsContext = createContext<JobsContextValue | null>(null);

// El poll trae una lista nueva cada 2s aunque nada haya cambiado. Si el
// contenido es igual se conserva el array anterior, asi React no re-renderiza
// todos los componentes que usan useJobs() en cada tick.
function keepIfUnchanged(prev: JobListItem[], next: JobListItem[]): JobListItem[] {
  return JSON.stringify(prev) === JSON.stringify(next) ? prev : next;
}

export function JobsProvider({ children }: { children: React.ReactNode }) {
  const [jobs, setJobsRaw] = useState<JobListItem[]>([]);
  const setJobs = useCallback((next: JobListItem[]) => setJobsRaw((prev) => keepIfUnchanged(prev, next)), []);

  useEffect(() => {
    let stopped = false;
    async function tick() {
      try {
        const data = await listJobs();
        if (!stopped) setJobs(data);
      } catch {
        // silencioso — si el server no responde el proximo tick reintenta solo
      }
      if (!stopped) setTimeout(tick, POLL_MS);
    }
    tick();
    return () => {
      stopped = true;
    };
  }, [setJobs]);

  const cancel = useCallback(async (id: string) => {
    await cancelJob(id);
    setJobs(await listJobs());
  }, [setJobs]);

  const retry = useCallback(async (job: JobListItem) => {
    const overrides =
      job.title_override !== null
        ? { artist_override: job.artist_override || "", title_override: job.title_override }
        : undefined;
    await requestDownload(job.webpage_url, job.title_hint, true, job.bitrate || "320", overrides);
    setJobs(await listJobs());
  }, [setJobs]);

  const value = useMemo(() => {
    const activeCount = jobs.filter((j) => j.status === "queued" || j.status === "downloading").length;
    return { jobs, activeCount, cancel, retry };
  }, [jobs, cancel, retry]);

  return <JobsContext.Provider value={value}>{children}</JobsContext.Provider>;
}

export function useJobs() {
  const ctx = useContext(JobsContext);
  if (!ctx) throw new Error("useJobs debe usarse dentro de JobsProvider");
  return ctx;
}
