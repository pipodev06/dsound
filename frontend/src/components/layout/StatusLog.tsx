import type { LogLine } from "@/types";

const TAGS: Record<LogLine["tag"], string> = { ok: "[+]", err: "[-]", info: "[*]", warn: "[!]" };
const COLORS: Record<LogLine["tag"], string> = {
  ok: "text-accent",
  err: "text-danger",
  info: "text-info",
  warn: "text-warn",
};

export function StatusLog({ lines }: { lines: LogLine[] }) {
  return (
    <section className="flex flex-col-reverse gap-1 pt-4" aria-live="polite">
      {lines.map((line, i) => (
        <div key={i} className="flex gap-2 font-mono text-sm">
          <span className={`shrink-0 font-bold ${COLORS[line.tag]}`}>{TAGS[line.tag]}</span>
          <span className="text-text">{line.text}</span>
        </div>
      ))}
    </section>
  );
}
