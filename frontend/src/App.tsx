import { useEffect, useRef, useState } from "react";

import { Header } from "@/components/layout/Header";
import { FfmpegNotice } from "@/components/layout/FfmpegNotice";
import { UpdateBanner } from "@/components/layout/UpdateBanner";
import { QuitDialog } from "@/components/modals/QuitDialog";
import { SettingsModal } from "@/components/modals/SettingsModal";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { SearchTab } from "@/components/search/SearchTab";
import { AlbumsTab } from "@/components/albums/AlbumsTab";
import { LibraryTab } from "@/components/library/LibraryTab";
import { DownloadsTab } from "@/components/downloads/DownloadsTab";
import { PreviewModal } from "@/components/modals/PreviewModal";
import { EditModal } from "@/components/modals/EditModal";
import { DuplicateModal } from "@/components/modals/DuplicateModal";
import { ConfirmDeleteModal } from "@/components/modals/ConfirmDeleteModal";
import { OutputDirModal } from "@/components/modals/OutputDirModal";
import { ModalProvider, useModal } from "@/context/ModalContext";
import { JobsProvider, useJobs } from "@/context/JobsContext";
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";
import { getStatus, openOutputDir, pickOutputDir, setOutputDir as apiSetOutputDir, shutdownApp } from "@/lib/api";
import type { TabHandle } from "@/types";

type TabId = "search" | "albums" | "library" | "downloads";

function AppContent() {
  const { openOutputDirModal } = useModal();
  const { activeCount } = useJobs();

  const [activeTab, setActiveTab] = useState<TabId>("search");
  const [bitrate, setBitrate] = useState("320");
  const [outputDir, setOutputDirState] = useState("");
  const [ffmpegOk, setFfmpegOk] = useState(true);
  const [ffmpegMessage, setFfmpegMessage] = useState("");
  const [changingFolder, setChangingFolder] = useState(false);
  const [version, setVersion] = useState("");
  const [isLocal, setIsLocal] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [quitOpen, setQuitOpen] = useState(false);
  const [closed, setClosed] = useState(false);

  const searchInputRef = useRef<HTMLInputElement>(null);
  const searchTabRef = useRef<TabHandle>(null);
  const albumsTabRef = useRef<TabHandle>(null);
  const libraryTabRef = useRef<TabHandle>(null);

  useKeyboardShortcuts(searchInputRef, activeTab);

  useEffect(() => {
    getStatus()
      .then((data) => {
        setOutputDirState(data.output_dir);
        setFfmpegOk(data.ffmpeg);
        setFfmpegMessage(data.ffmpeg_message);
        setVersion(data.version || "");
        setIsLocal(data.local === true);
      })
      .catch(() => {});
  }, []);

  function activeTabHandle(): TabHandle | null {
    if (activeTab === "search") return searchTabRef.current;
    if (activeTab === "albums") return albumsTabRef.current;
    return libraryTabRef.current;
  }

  async function handleOpenFolder() {
    try {
      const res = await openOutputDir();
      if (!res.ok) activeTabHandle()?.log("err", res.error || "no se pudo abrir la carpeta.");
    } catch {
      activeTabHandle()?.log("err", "error de red al abrir la carpeta.");
    }
  }

  async function handleQuit() {
    setQuitOpen(false);
    try {
      await shutdownApp();
    } catch {
      // el servidor se cierra: que falle la respuesta es esperable
    }
    setClosed(true);
  }

  async function handleChangeFolder() {
    setChangingFolder(true);
    try {
      const data = await pickOutputDir();
      if (data.error) {
        activeTabHandle()?.log("err", data.error);
      } else if (!data.available) {
        const manual = await openOutputDirModal(outputDir);
        if (manual) {
          const res2 = await apiSetOutputDir(manual);
          if (res2.output_dir) {
            setOutputDirState(res2.output_dir);
            activeTabHandle()?.log("ok", `carpeta cambiada a: ${res2.output_dir}`);
          } else if (res2.error) {
            activeTabHandle()?.log("err", res2.error);
          }
        }
      } else if (data.cancelled) {
        // se cerró el diálogo sin elegir: no se hace nada
      } else if (data.output_dir) {
        setOutputDirState(data.output_dir);
        activeTabHandle()?.log("ok", `carpeta cambiada a: ${data.output_dir}`);
      }
    } catch {
      activeTabHandle()?.log("err", "no se pudo cambiar la carpeta.");
    } finally {
      setChangingFolder(false);
    }
  }

  if (closed) {
    return (
      <main className="mx-auto flex min-h-screen max-w-[560px] flex-col items-center justify-center gap-3 p-8 text-center">
        <div className="font-mono text-xl font-semibold text-accent">dsound se cerró.</div>
        <p className="m-0 text-sm text-text-muted">Ya puedes cerrar esta pestaña. Para volver a usarlo, abre dsound de nuevo.</p>
      </main>
    );
  }

  return (
    <>
      <UpdateBanner />
      <Header
        outputDir={outputDir}
        version={version}
        isLocal={isLocal}
        changing={changingFolder}
        onChangeFolder={handleChangeFolder}
        onOpenFolder={handleOpenFolder}
        onOpenSettings={() => setSettingsOpen(true)}
        onQuit={() => setQuitOpen(true)}
        bitrate={bitrate}
        onBitrateChange={setBitrate}
      />

      <main className="mx-auto max-w-[1440px] p-8">
        <FfmpegNotice visible={!ffmpegOk} message={ffmpegMessage} />

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabId)}>
          <TabsList>
            <TabsTrigger value="search">Buscar</TabsTrigger>
            <TabsTrigger value="albums">Álbumes</TabsTrigger>
            <TabsTrigger value="library">Biblioteca</TabsTrigger>
            <TabsTrigger value="downloads">
              Descargas
              {activeCount > 0 && (
                <span className="ml-1 rounded-full bg-accent px-1.5 text-[0.65rem] font-bold text-[#06210f]">
                  {activeCount}
                </span>
              )}
            </TabsTrigger>
          </TabsList>
        </Tabs>

        <SearchTab ref={searchTabRef} hidden={activeTab !== "search"} bitrate={bitrate} searchInputRef={searchInputRef} />
        <AlbumsTab ref={albumsTabRef} hidden={activeTab !== "albums"} bitrate={bitrate} />
        <LibraryTab ref={libraryTabRef} hidden={activeTab !== "library"} active={activeTab === "library"} />
        <DownloadsTab hidden={activeTab !== "downloads"} canOpenFolder={isLocal} onOpenFolder={handleOpenFolder} />
      </main>

      <PreviewModal />
      <EditModal />
      <DuplicateModal />
      <ConfirmDeleteModal />
      <OutputDirModal />
      <SettingsModal
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        onSaved={(message) => activeTabHandle()?.log("ok", message)}
      />
      <QuitDialog
        open={quitOpen}
        activeDownloads={activeCount}
        onCancel={() => setQuitOpen(false)}
        onConfirm={handleQuit}
      />
    </>
  );
}

export default function App() {
  return (
    <ModalProvider>
      <JobsProvider>
        <AppContent />
      </JobsProvider>
    </ModalProvider>
  );
}
