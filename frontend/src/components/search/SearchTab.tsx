import { useImperativeHandle, useState } from "react";

import { Button } from "@/components/ui/button";
import { StatusLog } from "@/components/layout/StatusLog";
import { SelectionBar } from "@/components/common/SelectionBar";
import { ResultCard } from "@/components/search/ResultCard";
import { SearchForm } from "@/components/search/SearchForm";
import { useResultDownloads } from "@/components/search/useResultDownloads";
import { useSearchResults } from "@/components/search/useSearchResults";
import { useModal } from "@/context/ModalContext";
import { useLog } from "@/hooks/useLog";
import { classifyQuery } from "@/lib/searchInput";
import type { TabHandle } from "@/types";

interface SearchTabProps {
  hidden: boolean;
  bitrate: string;
  searchInputRef: React.RefObject<HTMLInputElement | null>;
  ref?: React.Ref<TabHandle>;
}

export function SearchTab({ hidden, bitrate, searchInputRef, ref }: SearchTabProps) {
  const { openPreview } = useModal();
  const { logs, log, clearLogs } = useLog();
  const [query, setQuery] = useState("");
  const search = useSearchResults(log);
  const downloads = useResultDownloads(bitrate, log);

  useImperativeHandle(ref, () => ({ log }));

  async function handleSubmit() {
    const parsed = classifyQuery(query);
    if (parsed.kind === "empty") return;
    clearLogs();
    switch (parsed.kind) {
      case "youtubeCollection":
        return search.runYoutubeCollection(parsed.url);
      case "youtubeLinks":
        setQuery("");
        search.clearResults();
        return downloads.downloadLinks(parsed.links);
      case "spotifyCollection":
        return search.runSpotifyCollection(parsed.url);
      case "spotifyTrack": {
        const resolved = await search.runSpotifyTrack(parsed.url);
        if (resolved) setQuery(resolved);
        return;
      }
      case "keyword":
        return search.runSearch(parsed.query);
    }
  }

  function handleBatchDownload() {
    for (const result of search.results) {
      if (search.selectedIds.has(result.id)) downloads.downloadOne(result);
    }
    search.clearSelection();
  }

  return (
    <div className={hidden ? "hidden" : undefined}>
      <SearchForm query={query} onQueryChange={setQuery} onSubmit={handleSubmit} inputRef={searchInputRef} />

      <SelectionBar
        count={search.selectedIds.size}
        actionLabel="Descargar seleccionadas"
        onAction={handleBatchDownload}
        onClear={search.clearSelection}
      />

      <ul className="m-0 mb-4 grid grid-cols-2 gap-4 p-0 sm:grid-cols-3 min-[900px]:grid-cols-4 min-[1100px]:grid-cols-5">
        {search.visible.map((result) => {
          const state = downloads.stateFor(result.id);
          return (
            <ResultCard
              key={result.id}
              result={result}
              selected={search.selectedIds.has(result.id)}
              override={downloads.labelOverride(result)}
              downloadDisabled={state.disabled}
              downloadTitle={state.label}
              onToggleSelect={(checked) => search.toggleSelect(result.id, checked)}
              onListen={() => openPreview(result.id, result.title, result.thumbnail)}
              onRename={() => downloads.rename(result)}
              onDownload={() => downloads.downloadOne(result)}
            />
          );
        })}
      </ul>

      {search.canLoadMore && (
        <Button variant="ghost" className="mx-auto mb-8 block" disabled={search.loadingMore} onClick={search.loadMore}>
          {search.loadingMore ? "Cargando..." : "Mas Resultados..."}
        </Button>
      )}

      <StatusLog lines={logs} />
    </div>
  );
}
