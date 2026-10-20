import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { checkUpdate } from "@/lib/api";
import type { UpdateInfo } from "@/types";

const DISMISS_KEY = "dsound.updateDismissed";

function dismissedVersion(): string | null {
  try {
    return localStorage.getItem(DISMISS_KEY);
  } catch {
    return null;
  }
}

/** Aviso de versión nueva (consulta GitHub Releases vía el backend). "Ahora no"
 * lo oculta hasta que salga otra versión. */
export function UpdateBanner() {
  const [info, setInfo] = useState<UpdateInfo | null>(null);

  useEffect(() => {
    let cancelled = false;
    checkUpdate().then((data) => {
      if (!cancelled && data?.update_available && data.latest !== dismissedVersion()) setInfo(data);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  if (!info) return null;

  function dismiss() {
    try {
      localStorage.setItem(DISMISS_KEY, info?.latest || "");
    } catch {
      // sin almacenamiento: solo se oculta por esta vez
    }
    setInfo(null);
  }

  return (
    <div
      className="flex flex-wrap items-center justify-between gap-3 border-b border-accent bg-surface px-6 py-2 text-sm"
      role="status"
    >
      <span>
        Hay una nueva versión de dsound: <strong className="text-accent">v{info.latest}</strong> (tienes la v{info.current}).
      </span>
      <div className="flex gap-2">
        {info.url && (
          <Button size="sm" asChild>
            <a href={info.url} target="_blank" rel="noopener noreferrer">
              Descargar
            </a>
          </Button>
        )}
        <Button variant="ghost" size="sm" onClick={dismiss}>
          Ahora no
        </Button>
      </div>
    </div>
  );
}
