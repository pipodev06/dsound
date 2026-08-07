import { useEffect } from "react";

const TYPING_TAGS = new Set(["INPUT", "TEXTAREA", "SELECT"]);

/**
 * Solo maneja "/" para enfocar el buscador. Esc para cerrar el modal activo
 * ya lo maneja Radix Dialog nativamente (onEscapeKeyDown -> onOpenChange),
 * que es lo que dispara el resolve/cancel de cada modal — un listener global
 * duplicado acá podria pisar ese resolve y dejar colgada una promesa.
 */
export function useKeyboardShortcuts(searchInputRef: React.RefObject<HTMLInputElement | null>, activeTab: string) {
  useEffect(() => {
    function handleKeydown(ev: KeyboardEvent) {
      const typing = TYPING_TAGS.has((document.activeElement?.tagName as string) || "");
      if (ev.key === "/" && !typing && activeTab === "search") {
        ev.preventDefault();
        searchInputRef.current?.focus();
        searchInputRef.current?.select();
      }
    }
    document.addEventListener("keydown", handleKeydown);
    return () => document.removeEventListener("keydown", handleKeydown);
  }, [searchInputRef, activeTab]);
}
