import { useCallback, useRef, useState } from "react";

import type { LogLine } from "@/types";

const MAX_LINES = 200;

/** Log de estado de una pestaña. Se queda con las ultimas MAX_LINES lineas
 * para no crecer sin limite en sesiones largas. */
export function useLog() {
  const [logs, setLogs] = useState<LogLine[]>([]);
  const nextId = useRef(0);
  const log = useCallback((tag: LogLine["tag"], text: string) => {
    const id = nextId.current++;
    setLogs((prev) => [...prev.slice(-(MAX_LINES - 1)), { id, tag, text }]);
  }, []);
  const clearLogs = useCallback(() => setLogs([]), []);
  return { logs, log, clearLogs };
}
