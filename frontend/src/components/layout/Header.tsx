import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface HeaderProps {
  outputDir: string;
  changing: boolean;
  onChangeFolder: () => void;
  bitrate: string;
  onBitrateChange: (bitrate: string) => void;
}

export function Header({ outputDir, changing, onChangeFolder, bitrate, onBitrateChange }: HeaderProps) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-border px-6 py-4 sm:flex-nowrap">
      <div className="font-mono text-xl font-semibold text-accent tracking-wide">
        dsound
        <span className="cursor-blink">_</span>
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
          <Button variant="ghost" onClick={onChangeFolder} disabled={changing}>
            cambiar
          </Button>
        </div>
      </div>
    </header>
  );
}
