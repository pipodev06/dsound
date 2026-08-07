import * as React from "react";
import { createContext, useCallback, useContext, useMemo, useState } from "react";

export type DuplicateChoice = "cancel" | "skip" | "force";

type ModalState =
  | { type: "none" }
  | { type: "preview"; videoId: string; title: string; thumbnail: string }
  | { type: "edit"; artist: string; title: string; onSave: (artist: string, title: string) => Promise<void> }
  | { type: "confirmDelete"; text: string; items?: string[]; onConfirm: () => Promise<void> }
  | { type: "duplicate"; text: string; items: string[] | null; resolve: (choice: DuplicateChoice) => void }
  | { type: "outputDir"; currentPath: string; resolve: (path: string | null) => void };

interface ModalContextValue {
  modal: ModalState;
  closeModal: () => void;
  openPreview: (videoId: string, title: string, thumbnail: string) => void;
  openEditModal: (artist: string, title: string, onSave: (artist: string, title: string) => Promise<void>) => void;
  openConfirmDelete: (text: string, onConfirm: () => Promise<void>, items?: string[]) => void;
  openDuplicateModal: (text: string, items: string[] | null) => Promise<DuplicateChoice>;
  openOutputDirModal: (currentPath: string) => Promise<string | null>;
}

const ModalContext = createContext<ModalContextValue | null>(null);

export function ModalProvider({ children }: { children: React.ReactNode }) {
  const [modal, setModal] = useState<ModalState>({ type: "none" });

  const closeModal = useCallback(() => setModal({ type: "none" }), []);

  const openPreview = useCallback((videoId: string, title: string, thumbnail: string) => {
    setModal({ type: "preview", videoId, title, thumbnail });
  }, []);

  const openEditModal = useCallback(
    (artist: string, title: string, onSave: (artist: string, title: string) => Promise<void>) => {
      setModal({ type: "edit", artist, title, onSave });
    },
    []
  );

  const openConfirmDelete = useCallback((text: string, onConfirm: () => Promise<void>, items?: string[]) => {
    setModal({ type: "confirmDelete", text, items, onConfirm });
  }, []);

  const openDuplicateModal = useCallback((text: string, items: string[] | null) => {
    return new Promise<DuplicateChoice>((resolve) => {
      setModal({ type: "duplicate", text, items, resolve });
    });
  }, []);

  const openOutputDirModal = useCallback((currentPath: string) => {
    return new Promise<string | null>((resolve) => {
      setModal({ type: "outputDir", currentPath, resolve });
    });
  }, []);

  const value = useMemo(
    () => ({ modal, closeModal, openPreview, openEditModal, openConfirmDelete, openDuplicateModal, openOutputDirModal }),
    [modal, closeModal, openPreview, openEditModal, openConfirmDelete, openDuplicateModal, openOutputDirModal]
  );

  return <ModalContext.Provider value={value}>{children}</ModalContext.Provider>;
}

export function useModal() {
  const ctx = useContext(ModalContext);
  if (!ctx) throw new Error("useModal debe usarse dentro de ModalProvider");
  return ctx;
}
