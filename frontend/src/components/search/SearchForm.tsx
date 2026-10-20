import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

interface SearchFormProps {
  query: string;
  onQueryChange: (value: string) => void;
  onSubmit: () => void;
  inputRef: React.RefObject<HTMLInputElement | null>;
}

export function SearchForm({ query, onQueryChange, onSubmit, inputRef }: SearchFormProps) {
  return (
    <form
      className="mx-auto mb-6 flex max-w-[960px] items-center gap-3 rounded-md border border-border bg-surface px-4 py-3"
      onSubmit={(ev) => {
        ev.preventDefault();
        onSubmit();
      }}
    >
      <Label htmlFor="query" className="font-mono font-semibold text-accent">
        música &gt;
      </Label>
      <input
        id="query"
        ref={inputRef}
        className="min-w-0 flex-1 border-0 border-b border-transparent bg-transparent pb-0.5 font-mono text-[0.95rem] text-text outline-none placeholder:text-text-muted focus:border-accent focus-visible:outline-none"
        type="text"
        placeholder="buscar cancion, pegar link(s) de YouTube, playlist/canal, o de Spotify (tema, playlist o album)"
        autoComplete="off"
        autoFocus
        value={query}
        onChange={(e) => onQueryChange(e.target.value)}
      />
      <Button type="submit">Buscar</Button>
    </form>
  );
}
