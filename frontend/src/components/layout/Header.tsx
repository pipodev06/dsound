import { Button } from "@/components/ui/button";

interface HeaderProps {
  outputDir: string;
  changing: boolean;
  onChangeFolder: () => void;
}

export function Header({ outputDir, changing, onChangeFolder }: HeaderProps) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-border px-6 py-4 sm:flex-nowrap">
      <div className="font-mono text-xl font-semibold text-accent tracking-wide">
        dsound
        <span className="cursor-blink">_</span>
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
    </header>
  );
}
