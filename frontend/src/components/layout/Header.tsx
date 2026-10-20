import { IconFolderOpen, IconPower, IconSettings } from "@tabler/icons-react";

import { Button } from "@/components/ui/button";
import { IconButton } from "@/components/ui/icon-button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface HeaderProps {
  outputDir: string;
  version: string;
  /** página abierta en la PC donde se ejecuta dsound (si no, se ocultan las acciones locales) */
  isLocal: boolean;
  changing: boolean;
  onChangeFolder: () => void;
  onOpenFolder: () => void;
  onOpenSettings: () => void;
  onQuit: () => void;
  bitrate: string;
  onBitrateChange: (bitrate: string) => void;
}

export function Header({
  outputDir,
  version,
  isLocal,
  changing,
  onChangeFolder,
  onOpenFolder,
  onOpenSettings,
  onQuit,
  bitrate,
  onBitrateChange,
}: HeaderProps) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-border px-6 py-4 sm:flex-nowrap">
      <div className="flex items-baseline gap-2">
        <div className="font-mono text-xl font-semibold text-accent tracking-wide">
          dsound
          <span className="cursor-blink">_</span>
        </div>
        {version && <span className="font-mono text-[0.7rem] text-text-muted">v{version}</span>}
      </div>
      <div className="flex min-w-0 flex-wrap items-center gap-4">
        <div className="flex items-center gap-2 font-mono text-[0.78rem] text-text-muted">
          <Label htmlFor="bitrate-select">calidad</Label>
          <Select value={bitrate} onValueChange={onBitrateChange}>
            <SelectTrigger id="bitrate-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="128">128 kbps</SelectItem>
              <SelectItem value="192">192 kbps</SelectItem>
              <SelectItem value="320">320 kbps</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex min-w-0 items-center gap-2 font-mono text-[0.82rem] text-text-muted">
          <span>carpeta</span>
          <span className="max-w-[40ch] overflow-hidden text-ellipsis whitespace-nowrap text-text" title={outputDir}>
            {outputDir || "cargando..."}
          </span>
          {isLocal && (
            <>
              <IconButton aria-label="Abrir carpeta de música" title="Abrir carpeta" onClick={onOpenFolder}>
                <IconFolderOpen />
              </IconButton>
              <Button variant="ghost" onClick={onChangeFolder} disabled={changing}>
                cambiar
              </Button>
            </>
          )}
        </div>
        {isLocal && (
          <div className="flex items-center gap-2">
            <IconButton aria-label="Ajustes" title="Ajustes" onClick={onOpenSettings}>
              <IconSettings />
            </IconButton>
            <IconButton variant="danger" aria-label="Cerrar dsound" title="Cerrar dsound" onClick={onQuit}>
              <IconPower />
            </IconButton>
          </div>
        )}
      </div>
    </header>
  );
}
