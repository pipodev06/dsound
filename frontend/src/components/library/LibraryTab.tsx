import { useEffect, useImperativeHandle, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { StatusLog } from "@/components/layout/StatusLog";
import { SelectionBar } from "@/components/common/SelectionBar";
import { LibraryRow } from "@/components/library/LibraryRow";
import { useModal } from "@/context/ModalContext";
import { deleteLibraryItem, getLibrary, updateLibraryItem } from "@/lib/api";
import type { LibraryItem, LogLine, TabHandle } from "@/types";

const LIB_PAGE_STEP = 25;

type SortKey = "date" | "artist" | "title" | "size";

function sortItems(items: LibraryItem[], sortBy: SortKey): LibraryItem[] {
  const sorted = [...items];
  switch (sortBy) {
    case "artist":
      sorted.sort((a, b) => (a.artist || "").localeCompare(b.artist || "", "es", { sensitivity: "base" }) || a.title.localeCompare(b.title, "es", { sensitivity: "base" }));
      break;
    case "title":
      sorted.sort((a, b) => a.title.localeCompare(b.title, "es", { sensitivity: "base" }));
      break;
    case "size":
      sorted.sort((a, b) => b.size - a.size);
      break;
    default:
      sorted.sort((a, b) => b.mtime - a.mtime);
  }
  return sorted;
}

export function LibraryTab({ hidden, active, ref }: { hidden: boolean; active: boolean; ref?: React.Ref<TabHandle> }) {
  const { openEditModal, openConfirmDelete } = useModal();

  const [items, setItems] = useState<LibraryItem[]>([]);
  const [filter, setFilter] = useState("");
  const [sortBy, setSortBy] = useState<SortKey>("date");
  const [visibleCount, setVisibleCount] = useState(LIB_PAGE_STEP);
  const [refreshing, setRefreshing] = useState(false);
  const [logs, setLogs] = useState<LogLine[]>([]);
  const [selectedFilenames, setSelectedFilenames] = useState<Set<string>>(new Set());

  function log(tag: LogLine["tag"], text: string) {
    setLogs((prev) => [...prev, { tag, text }]);
  }

  useImperativeHandle(ref, () => ({ log }));

  async function loadLibrary() {
    try {
      const data = await getLibrary();
      setItems(data);
    } catch {
      log("err", "no se pudo cargar la biblioteca.");
    }
  }

  useEffect(() => {
    if (!active) return;
    // si se cambia de pestaña antes de que llegue la respuesta, se descarta
    let stale = false;
    setFilter("");
    setVisibleCount(LIB_PAGE_STEP);
    getLibrary()
      .then((data) => {
        if (!stale) setItems(data);
      })
      .catch(() => {
        if (!stale) log("err", "no se pudo cargar la biblioteca.");
      });
    return () => {
      stale = true;
    };
  }, [active]);

  function changeFilter(value: string) {
    setFilter(value);
    setVisibleCount(LIB_PAGE_STEP);
  }

  function changeSort(value: SortKey) {
    setSortBy(value);
    setVisibleCount(LIB_PAGE_STEP);
  }

  const filtered = useMemo(() => {
    const q = filter.trim().toLowerCase();
    if (!q) return items;
    return items.filter((i) => (i.title || "").toLowerCase().includes(q) || (i.artist || "").toLowerCase().includes(q));
  }, [items, filter]);

  const sorted = useMemo(() => sortItems(filtered, sortBy), [filtered, sortBy]);

  const visible = sorted.slice(0, visibleCount);
  const hasMore = visibleCount < sorted.length;

  async function handleRefresh() {
    setRefreshing(true);
    await loadLibrary();
    setRefreshing(false);
  }

  function handleEdit(item: LibraryItem) {
    openEditModal(item.artist, item.title, async (artist, title) => {
      const res = await updateLibraryItem(item.filename, artist, title);
      if (!res.ok) {
        log("err", res.error || "no se pudo actualizar la cancion.");
        throw new Error(res.error || "update failed");
      }
      log("ok", `actualizado: ${artist ? artist + " - " : ""}${title}`);
      await loadLibrary();
    });
  }

  function handleDelete(item: LibraryItem) {
    const label = `${item.title}${item.artist ? " - " + item.artist : ""}`;
    openConfirmDelete(`¿Estás seguro de eliminar ${label}?`, async () => {
      const res = await deleteLibraryItem(item.filename);
      if (!res.ok) {
        log("err", res.error || "no se pudo eliminar la cancion.");
        return;
      }
      log("ok", `eliminado: ${label}`);
      await loadLibrary();
    });
  }

  function toggleSelect(filename: string, checked: boolean) {
    setSelectedFilenames((prev) => {
      const next = new Set(prev);
      if (checked) next.add(filename);
      else next.delete(filename);
      return next;
    });
  }

  function handleBulkDelete() {
    const selected = items.filter((i) => selectedFilenames.has(i.filename));
    if (selected.length === 0) return;
    const labels = selected.map((i) => `${i.title}${i.artist ? " - " + i.artist : ""}`);
    openConfirmDelete(
      `¿Estás seguro de eliminar ${selected.length} cancion${selected.length === 1 ? "" : "es"}?`,
      async () => {
        // los borrados son independientes entre si: se mandan todos juntos
        const results = await Promise.all(
          selected.map((item) =>
            deleteLibraryItem(item.filename).catch(() => ({ ok: false, error: "fallo de red." }))
          )
        );
        let failed = 0;
        results.forEach((res, i) => {
          if (!res.ok) {
            failed++;
            log("err", `${selected[i].title}: ${res.error || "no se pudo eliminar."}`);
          }
        });
        const ok = selected.length - failed;
        if (ok > 0) log("ok", `eliminadas ${ok} cancion${ok === 1 ? "" : "es"}`);
        setSelectedFilenames(new Set());
        await loadLibrary();
      },
      labels
    );
  }

  return (
    <div className={hidden ? "hidden" : undefined}>
      <div className="mb-4 flex items-center justify-between gap-3">
        <input
          className="max-w-[400px] flex-1 border-0 border-b border-border bg-transparent px-1 py-2 font-mono text-[0.88rem] text-text outline-none focus:border-accent focus-visible:outline-none"
          type="text"
          placeholder="filtrar por artista o titulo..."
          aria-label="Filtrar biblioteca por artista o titulo"
          autoComplete="off"
          value={filter}
          onChange={(e) => changeFilter(e.target.value)}
        />
        <span className="whitespace-nowrap text-[0.78rem] text-text-muted">
          {filtered.length} cancion{filtered.length === 1 ? "" : "es"}
        </span>
        <Select value={sortBy} onValueChange={(v) => changeSort(v as SortKey)}>
          <SelectTrigger aria-label="Ordenar por">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="date">Mas reciente</SelectItem>
            <SelectItem value="artist">Artista</SelectItem>
            <SelectItem value="title">Titulo</SelectItem>
            <SelectItem value="size">Tamaño</SelectItem>
          </SelectContent>
        </Select>
        <Button variant="ghost" size="sm" disabled={refreshing} onClick={handleRefresh}>
          Actualizar
        </Button>
      </div>

      <SelectionBar
        count={selectedFilenames.size}
        actionLabel="Eliminar seleccionadas"
        actionVariant="danger"
        onAction={handleBulkDelete}
        onClear={() => setSelectedFilenames(new Set())}
      />

      <ul className="m-0 mb-8 flex flex-col gap-2 p-0">
        {filtered.length === 0 && <li className="text-[0.9rem] text-text-muted">no hay nada bajado todavia.</li>}
        {visible.map((item) => (
          <LibraryRow
            key={item.filename}
            item={item}
            selected={selectedFilenames.has(item.filename)}
            onToggleSelect={(checked) => toggleSelect(item.filename, checked)}
            onEdit={() => handleEdit(item)}
            onDelete={() => handleDelete(item)}
          />
        ))}
      </ul>

      {hasMore && (
        <Button variant="ghost" className="mx-auto mb-8 block" onClick={() => setVisibleCount((prev) => prev + LIB_PAGE_STEP)}>
          Mas Resultados...
        </Button>
      )}

      <StatusLog lines={logs} />
    </div>
  );
}
