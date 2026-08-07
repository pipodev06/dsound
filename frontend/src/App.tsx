import { useEffect, useRef, useState } from "react";

import { Header } from "@/components/layout/Header";
import { FfmpegNotice } from "@/components/layout/FfmpegNotice";
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
import { getStatus, pickOutputDir, setOutputDir as apiSetOutputDir } from "@/lib/api";
import type { TabHandle } from "@/types";

type TabId = "search" | "albums" | "library" | "downloads";

function AppContent() {
  const { openOutputDirModal } = useModal();
  const { activeCount } = useJobs();

  const [activeTab, setActiveTab] = useState<TabId>("search");
  const [outputDir, setOutputDirState] = useState("");
  const [ffmpegOk, setFfmpegOk] = useState(true);
  const [ffmpegMessage, setFfmpegMessage] = useState("");
  const [changingFolder, setChangingFolder] = useState(false);

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
      })
      .catch(() => {});
  }, []);

  function activeTabHandle(): TabHandle | null {
    if (activeTab === "search") return searchTabRef.current;
    if (activeTab === "albums") return albumsTabRef.current;
    return libraryTabRef.current;
  }

  async function handleChangeFolder() {
    setChangingFolder(true);
    try {
      const data = await pickOutputDir();
      if (!data.available) {
        const manual = await openOutputDirModal(outputDir);
        if (manual) {
          const res2 = await apiSetOutputDir(manual);
          if (res2.output_dir) {
            setOutputDirState(res2.output_dir);
            activeTabHandle()?.log("ok", `carpeta cambiada a: ${res2.output_dir}`);
          }
        }
      } else if (data.cancelled) {
        // usuario cerro el dialogo sin elegir, no hacemos nada
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

  return (
    <>
      <Header outputDir={outputDir} changing={changingFolder} onChangeFolder={handleChangeFolder} />

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

        <SearchTab ref={searchTabRef} hidden={activeTab !== "search"} searchInputRef={searchInputRef} />
        <AlbumsTab ref={albumsTabRef} hidden={activeTab !== "albums"} />
        <LibraryTab ref={libraryTabRef} hidden={activeTab !== "library"} active={activeTab === "library"} />
        <DownloadsTab hidden={activeTab !== "downloads"} />
      </main>

      <PreviewModal />
      <EditModal />
      <DuplicateModal />
      <ConfirmDeleteModal />
      <OutputDirModal />
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
