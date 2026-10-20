import { getJob } from "@/lib/api";
import type { Job } from "@/types";

export async function pollJob(jobId: string, onTick?: (job: Job) => void): Promise<Job> {
  while (true) {
    const { ok, job } = await getJob(jobId);
    if (!ok) {
      return { status: "error", error: (job as { error?: string }).error || "el servidor perdió el rastro de esta descarga (¿se reinició dsound?)." };
    }
    onTick?.(job);
    if (job.status === "done" || job.status === "error" || job.status === "cancelled") return job;
    await new Promise((r) => setTimeout(r, 700));
  }
}
