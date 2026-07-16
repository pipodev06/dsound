const $ = (sel) => document.querySelector(sel);

const outputDirEl = $("#output-dir");
const changeFolderBtn = $("#change-folder");
const ffmpegWarning = $("#ffmpeg-warning");
const ffmpegWarningText = $("#ffmpeg-warning-text");
const searchForm = $("#search-form");
const queryInput = $("#query");
const bitrateSelect = $("#bitrate-select");
const resultsEl = $("#results");
const loadMoreBtn = $("#load-more");
const batchBar = $("#batch-bar");
const batchCountEl = $("#batch-count");
const batchDownloadBtn = $("#batch-download");
const batchClearBtn = $("#batch-clear");
const logSearchEl = $("#log-search");
const logAlbumsEl = $("#log-albums");
const logLibraryEl = $("#log-library");

const tabBtns = document.querySelectorAll(".tab-btn");
const viewSearch = $("#view-search");
const viewAlbums = $("#view-albums");
const viewLibrary = $("#view-library");
const albumSearchForm = $("#album-search-form");
const albumQueryInput = $("#album-query");
const albumBitrateSelect = $("#album-bitrate-select");
const albumResultsEl = $("#album-results");
const albumLoadMoreBtn = $("#album-load-more");
const libraryListEl = $("#library-list");
const libFilterInput = $("#lib-filter");
const libCountEl = $("#lib-count");
const libRefreshBtn = $("#lib-refresh");

const YOUTUBE_HOST_RE = /youtube\.com|youtu\.be/;
const SPOTIFY_TRACK_RE = /open\.spotify\.com\/track\//;
const PAGE_SIZE = 25; // 5 columnas x 5 filas
const SEARCH_LIMIT_CAP = 300;

let searchQuery = "";
let searchResults = [];
let shownCount = 0;
let libraryItems = [];
let libraryLoaded = false;
let selectedIndices = new Set();

const PLAY_ICON_SVG = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>`;
const DOWNLOAD_ICON_SVG = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`;
const EDIT_ICON_SVG = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>`;
const TRASH_ICON_SVG = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>`;
const LINK_ICON_SVG = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>`;

function log(kind, text, targetEl) {
  const tags = { ok: "[+]", err: "[-]", info: "[*]", warn: "[!]" };
  const line = document.createElement("div");
  line.className = "log-line";
  line.innerHTML = `<span class="tag tag-${kind}">${tags[kind]}</span><span>${text}</span>`;
  (targetEl || activeLogEl()).appendChild(line);
}

function activeLogEl() {
  if (!viewAlbums.hidden) return logAlbumsEl;
  if (!viewLibrary.hidden) return logLibraryEl;
  return logSearchEl;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML.replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}

function formatDuration(seconds) {
  seconds = Math.round(seconds || 0);
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

async function loadStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    outputDirEl.textContent = data.output_dir;
    outputDirEl.title = data.output_dir;
    if (!data.ffmpeg) {
      ffmpegWarningText.textContent = data.ffmpeg_message;
      ffmpegWarning.hidden = false;
    } else {
      ffmpegWarning.hidden = true;
    }
  } catch (e) {
    log("err", "no se pudo consultar el estado del servidor.");
  }
}

changeFolderBtn.addEventListener("click", async () => {
  changeFolderBtn.disabled = true;
  try {
    const res = await fetch("/api/output-dir/pick", { method: "POST" });
    const data = await res.json();
    if (!data.available) {
      const manual = prompt("Escribi la ruta de la carpeta de salida:", outputDirEl.textContent);
      if (manual) {
        const res2 = await fetch("/api/output-dir", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ path: manual }),
        });
        const data2 = await res2.json();
        if (data2.output_dir) {
          outputDirEl.textContent = data2.output_dir;
          log("ok", `carpeta cambiada a: ${data2.output_dir}`);
        }
      }
    } else if (data.cancelled) {
      // usuario cerro el dialogo sin elegir, no hacemos nada
    } else if (data.output_dir) {
      outputDirEl.textContent = data.output_dir;
      log("ok", `carpeta cambiada a: ${data.output_dir}`);
    }
  } catch (e) {
    log("err", "no se pudo cambiar la carpeta.");
  } finally {
    changeFolderBtn.disabled = false;
  }
});

function thumbHtml(result) {
  return `<img class="card-thumb" src="${result.thumbnail || ""}" alt="" loading="lazy" /><button type="button" class="play-toggle" aria-label="Escuchar preview">&#9658;</button>`;
}

function guessArtistTitle(rawTitle) {
  const parts = (rawTitle || "").split(" - ");
  if (parts.length >= 2) {
    return { artist: parts[0].trim(), title: parts.slice(1).join(" - ").trim() };
  }
  return { artist: "", title: (rawTitle || "").trim() };
}

function cardHtml(result, index) {
  return `
    <li class="card" data-index="${index}">
      <label class="card-select">
        <input type="checkbox" aria-label="Seleccionar ${escapeHtml(result.title)}" />
      </label>
      <div class="card-media">${thumbHtml(result)}</div>
      <div class="card-body">
        <div class="card-title" title="${escapeHtml(result.title)}">${escapeHtml(result.title)}</div>
        <div class="card-meta">${escapeHtml(result.channel || "?")} · ${formatDuration(result.duration)}</div>
        <div class="card-actions">
          <button type="button" class="icon-btn btn-listen" aria-label="Escuchar" title="Escuchar">${PLAY_ICON_SVG}</button>
          <button type="button" class="icon-btn icon-btn-accent btn-download" aria-label="Descargar" title="Descargar">${DOWNLOAD_ICON_SVG}</button>
          <button type="button" class="icon-btn btn-rename" aria-label="Renombrar" title="Renombrar">${EDIT_ICON_SVG}</button>
          <a class="icon-btn" href="${escapeHtml(result.webpage_url)}" target="_blank" rel="noopener noreferrer" aria-label="Ir al enlace" title="Ver en YouTube">${LINK_ICON_SVG}</a>
        </div>
      </div>
    </li>
  `;
}

const previewModal = $("#preview-modal");
const previewTitle = $("#preview-title");
const previewStatus = $("#preview-status");
const previewVideo = $("#preview-video");
const previewCloseBtn = $("#preview-close");

let previewRequestId = 0;

function closePreview() {
  previewRequestId++;
  previewVideo.pause();
  previewVideo.removeAttribute("src");
  previewVideo.load();
  previewModal.hidden = true;
}

async function openPreview(result) {
  const requestId = ++previewRequestId;
  previewVideo.poster = result.thumbnail || "";
  previewVideo.removeAttribute("src");
  previewTitle.textContent = result.title;
  previewStatus.textContent = "cargando preview...";
  previewModal.hidden = false;

  try {
    const res = await fetch(`/api/preview/${encodeURIComponent(result.id)}`);
    const data = await res.json();
    if (requestId !== previewRequestId) return; // se cerro o abrio otro mientras cargaba
    if (!res.ok) {
      previewStatus.textContent = data.error || "no se pudo cargar el preview.";
      return;
    }
    previewStatus.textContent = data.has_video ? "" : "solo audio disponible para este video.";
    previewVideo.src = data.stream_url;
    previewVideo.play().catch(() => {
      previewStatus.textContent = "toca play para reproducir.";
    });
  } catch (e) {
    if (requestId !== previewRequestId) return;
    previewStatus.textContent = "fallo de red al cargar el preview.";
  }
}

previewCloseBtn.addEventListener("click", closePreview);
previewModal.addEventListener("click", (ev) => {
  if (ev.target === previewModal) closePreview();
});

function overridesFor(result) {
  if (!result._override) return null;
  return { artist_override: result._override.artist, title_override: result._override.title };
}

resultsEl.addEventListener("click", (ev) => {
  const li = ev.target.closest(".card");
  if (!li) return;
  const result = searchResults[Number(li.dataset.index)];

  if (ev.target.closest(".play-toggle") || ev.target.closest(".btn-listen")) {
    openPreview(result);
    return;
  }
  if (ev.target.closest(".btn-rename")) {
    const current = result._override || guessArtistTitle(result.title);
    openEditModal(current.artist, current.title, (artist, title) => {
      result._override = { artist, title };
      const label = artist ? `${artist} - ${title}` : title;
      const titleEl = li.querySelector(".card-title");
      titleEl.textContent = label;
      titleEl.title = label;
    });
    return;
  }
  const downloadBtn = ev.target.closest(".btn-download");
  if (downloadBtn) {
    downloadResult(result, downloadBtn, false, overridesFor(result));
  }
});

resultsEl.addEventListener("change", (ev) => {
  const checkbox = ev.target.closest(".card-select input");
  if (!checkbox) return;
  const li = ev.target.closest(".card");
  const index = Number(li.dataset.index);
  if (checkbox.checked) selectedIndices.add(index);
  else selectedIndices.delete(index);
  updateBatchBar();
});

function updateBatchBar() {
  const n = selectedIndices.size;
  batchBar.hidden = n === 0;
  batchCountEl.textContent = `${n} seleccionada${n === 1 ? "" : "s"}`;
}

batchClearBtn.addEventListener("click", () => {
  selectedIndices.clear();
  resultsEl.querySelectorAll(".card-select input:checked").forEach((cb) => (cb.checked = false));
  updateBatchBar();
});

batchDownloadBtn.addEventListener("click", () => {
  const indices = Array.from(selectedIndices);
  for (const index of indices) {
    const li = resultsEl.querySelector(`.card[data-index="${index}"]`);
    if (!li) continue;
    const btn = li.querySelector(".btn-download");
    const checkbox = li.querySelector(".card-select input");
    if (checkbox) checkbox.checked = false;
    downloadResult(searchResults[index], btn, false, overridesFor(searchResults[index]));
  }
  selectedIndices.clear();
  updateBatchBar();
});

function showMore() {
  const next = searchResults.slice(shownCount, shownCount + PAGE_SIZE);
  resultsEl.insertAdjacentHTML("beforeend", next.map((r, i) => cardHtml(r, shownCount + i)).join(""));
  shownCount += next.length;
  const exhausted = shownCount >= searchResults.length && searchResults.length >= SEARCH_LIMIT_CAP;
  loadMoreBtn.hidden = exhausted;
}

async function fetchSearchResults(query, limit) {
  const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  const data = await res.json();
  return { ok: res.ok, data };
}

loadMoreBtn.addEventListener("click", async () => {
  if (shownCount < searchResults.length) {
    showMore();
    return;
  }
  if (searchResults.length >= SEARCH_LIMIT_CAP) {
    loadMoreBtn.hidden = true;
    return;
  }
  const original = loadMoreBtn.textContent;
  loadMoreBtn.disabled = true;
  loadMoreBtn.textContent = "Cargando...";
  try {
    const nextLimit = Math.min(searchResults.length + PAGE_SIZE, SEARCH_LIMIT_CAP);
    const { ok, data } = await fetchSearchResults(searchQuery, nextLimit);
    if (!ok) {
      log("err", data.error || "no se pudieron cargar mas resultados.", logSearchEl);
      return;
    }
    const newResults = data.results || [];
    if (newResults.length <= searchResults.length) {
      log("info", "no hay mas resultados.", logSearchEl);
      loadMoreBtn.hidden = true;
      return;
    }
    searchResults = newResults;
    showMore();
  } catch (e) {
    log("err", "fallo de red al cargar mas resultados.", logSearchEl);
  } finally {
    loadMoreBtn.disabled = false;
    loadMoreBtn.textContent = original;
  }
});

function renderResults(results) {
  searchResults = results;
  shownCount = 0;
  selectedIndices.clear();
  updateBatchBar();
  resultsEl.innerHTML = "";
  showMore();
}

async function pollJob(jobId, onTick) {
  while (true) {
    const res = await fetch(`/api/jobs/${jobId}`);
    const job = await res.json();
    if (!res.ok) {
      return { status: "error", error: job.error || "el servidor perdio el rastro de esta descarga (¿se reinicio?)." };
    }
    if (onTick) onTick(job);
    if (job.status === "done" || job.status === "error") return job;
    await new Promise((r) => setTimeout(r, 700));
  }
}

async function requestDownload(webpageUrl, titleHint, confirmDuplicate, overrides) {
  const res = await fetch("/api/download", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      webpage_url: webpageUrl,
      title: titleHint,
      confirm: confirmDuplicate,
      bitrate: bitrateSelect.value,
      ...(overrides || {}),
    }),
  });
  const data = await res.json();
  return { ok: res.ok, status: res.status, data };
}

async function downloadResult(result, btn, confirmDuplicate = false, overrides = null) {
  btn.disabled = true;
  btn.title = "En cola...";
  try {
    const { ok, status, data } = await requestDownload(result.webpage_url, result.title, confirmDuplicate, overrides);
    if (status === 409 && data.duplicate) {
      btn.disabled = false;
      btn.title = "Descargar";
      const choice = await openDuplicateModal(
        `Ya tienes algo parecido: "${data.existing}". ¿Descargar de todos modos?`,
        null
      );
      if (choice === "force") return downloadResult(result, btn, true, overrides);
      log("warn", `omitido (ya existe "${data.existing}")`, logSearchEl);
      return;
    }
    if (!ok) {
      log("err", data.error || "no se pudo descargar.", logSearchEl);
      btn.disabled = false;
      btn.title = "Descargar";
      return;
    }
    const job = await pollJob(data.job_id, (j) => {
      if (j.status === "downloading") btn.title = "Descargando...";
    });
    if (job.status === "done") {
      log("ok", job.result.artist ? `${job.result.artist} - ${job.result.title}` : job.result.title, logSearchEl);
      btn.title = "Descargado";
    } else {
      log("err", job.error || "no se pudo descargar.", logSearchEl);
      btn.disabled = false;
      btn.title = "Descargar";
    }
  } catch (e) {
    log("err", `${result.title}: fallo de red.`, logSearchEl);
    btn.disabled = false;
    btn.title = "Descargar";
  }
}

async function downloadDirectLink(url) {
  log("info", "descargando enlace...", logSearchEl);
  try {
    const { ok, data } = await requestDownload(url, "", false);
    if (!ok) {
      log("err", data.error || "no se pudo descargar.", logSearchEl);
      return;
    }
    let lastStatus = null;
    const job = await pollJob(data.job_id, (j) => {
      if (j.status === lastStatus) return;
      lastStatus = j.status;
      if (j.status === "queued") log("info", "hay otras descargas en cola, espera...", logSearchEl);
      else if (j.status === "downloading") log("info", "descargando...", logSearchEl);
    });
    if (job.status === "done") {
      log("ok", job.result.artist ? `${job.result.artist} - ${job.result.title}` : job.result.title, logSearchEl);
    } else {
      log("err", job.error || "no se pudo descargar.", logSearchEl);
    }
  } catch (e) {
    log("err", "fallo de red al descargar el link.", logSearchEl);
  }
}

async function runYoutubeSearch(query) {
  log("info", `buscando "${query}"...`, logSearchEl);
  resultsEl.innerHTML = "";
  loadMoreBtn.hidden = true;
  searchQuery = query;
  try {
    const { ok, data } = await fetchSearchResults(query, PAGE_SIZE);
    if (!ok) {
      log("err", data.error || "busqueda fallida.", logSearchEl);
      return;
    }
    if (!data.results || data.results.length === 0) {
      log("warn", "sin resultados.", logSearchEl);
      return;
    }
    renderResults(data.results);
    log("ok", `${data.results.length} resultado(s) para "${query}"`, logSearchEl);
  } catch (e) {
    log("err", "fallo de red al buscar.", logSearchEl);
  }
}

async function resolveSpotifyAndSearch(url) {
  log("info", "leyendo link de Spotify...", logSearchEl);
  resultsEl.innerHTML = "";
  loadMoreBtn.hidden = true;
  try {
    const res = await fetch(`/api/resolve-spotify?url=${encodeURIComponent(url)}`);
    const data = await res.json();
    if (!res.ok) {
      log("err", data.error || "no se pudo leer el link de Spotify.", logSearchEl);
      return;
    }
    log("ok", `Spotify: "${data.query}"`, logSearchEl);
    queryInput.value = data.query;
    await runYoutubeSearch(data.query);
  } catch (e) {
    log("err", "fallo de red al leer el link de Spotify.", logSearchEl);
  }
}

searchForm.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const query = queryInput.value.trim();
  if (!query) return;

  logSearchEl.innerHTML = "";

  if (YOUTUBE_HOST_RE.test(query)) {
    queryInput.value = "";
    resultsEl.innerHTML = "";
    loadMoreBtn.hidden = true;
    await downloadDirectLink(query);
    return;
  }

  if (SPOTIFY_TRACK_RE.test(query)) {
    await resolveSpotifyAndSearch(query);
    return;
  }

  await runYoutubeSearch(query);
});

function formatBytes(bytes) {
  const mb = (bytes || 0) / (1024 * 1024);
  return `${mb.toFixed(1)} MB`;
}

function libRowHtml(item) {
  const label = item.artist ? `${item.artist} - ${item.title}` : item.title;
  return `
    <li class="lib-row" data-filename="${escapeHtml(item.filename)}" data-artist="${escapeHtml(item.artist)}" data-title="${escapeHtml(item.title)}">
      <div class="lib-row-info">
        <div class="lib-row-title" title="${escapeHtml(label)}">${escapeHtml(label)}</div>
        <div class="lib-row-meta">${formatBytes(item.size)}</div>
      </div>
      <div class="lib-row-controls">
        <audio controls preload="none" src="/library/${encodeURIComponent(item.filename)}"></audio>
        <button type="button" class="icon-btn lib-edit-btn" aria-label="Editar" title="Editar">${EDIT_ICON_SVG}</button>
        <button type="button" class="icon-btn icon-btn-danger lib-delete-btn" aria-label="Eliminar" title="Eliminar">${TRASH_ICON_SVG}</button>
      </div>
    </li>
  `;
}

function renderLibrary(items) {
  libCountEl.textContent = `${items.length} cancion${items.length === 1 ? "" : "es"}`;
  libraryListEl.innerHTML = items.length
    ? items.map(libRowHtml).join("")
    : `<li class="lib-empty">no hay nada bajado todavia.</li>`;
}

async function loadLibrary() {
  try {
    const res = await fetch("/api/library");
    const data = await res.json();
    libraryItems = data.items || [];
    libraryLoaded = true;
    applyLibraryFilter();
  } catch (e) {
    log("err", "no se pudo cargar la biblioteca.", logLibraryEl);
  }
}

function applyLibraryFilter() {
  const q = libFilterInput.value.trim().toLowerCase();
  const filtered = !q
    ? libraryItems
    : libraryItems.filter(
        (i) => (i.title || "").toLowerCase().includes(q) || (i.artist || "").toLowerCase().includes(q)
      );
  renderLibrary(filtered);
}

const deleteModal = $("#delete-modal");
const deleteModalText = $("#delete-modal-text");
const deleteCancelBtn = $("#delete-cancel");
const deleteConfirmBtn = $("#delete-confirm");
let pendingDelete = null;

function openDeleteModal(filename, artist, title) {
  pendingDelete = { filename, artist, title };
  deleteModalText.textContent = `¿Estás seguro de eliminar ${title}${artist ? " - " + artist : ""}?`;
  deleteModal.hidden = false;
}

function closeDeleteModal() {
  deleteModal.hidden = true;
  pendingDelete = null;
}

deleteCancelBtn.addEventListener("click", closeDeleteModal);
deleteModal.addEventListener("click", (ev) => {
  if (ev.target === deleteModal) closeDeleteModal();
});

deleteConfirmBtn.addEventListener("click", async () => {
  if (!pendingDelete) return;
  const { filename, artist, title } = pendingDelete;
  const label = `${title}${artist ? " - " + artist : ""}`;
  deleteConfirmBtn.disabled = true;
  try {
    const res = await fetch(`/api/library/${encodeURIComponent(filename)}`, { method: "DELETE" });
    const data = await res.json();
    if (!res.ok) {
      log("err", data.error || "no se pudo eliminar la cancion.", logLibraryEl);
      return;
    }
    log("ok", `eliminado: ${label}`, logLibraryEl);
    closeDeleteModal();
    await loadLibrary();
  } catch (e) {
    log("err", "fallo de red al eliminar la cancion.", logLibraryEl);
  } finally {
    deleteConfirmBtn.disabled = false;
  }
});

const duplicateModal = $("#duplicate-modal");
const duplicateModalText = $("#duplicate-modal-text");
const duplicateModalList = $("#duplicate-modal-list");
const duplicateCancelBtn = $("#duplicate-cancel");
const duplicateSkipBtn = $("#duplicate-skip");
const duplicateConfirmBtn = $("#duplicate-confirm");
let pendingDuplicateResolve = null;

function openDuplicateModal(text, items) {
  return new Promise((resolve) => {
    pendingDuplicateResolve = resolve;
    duplicateModalText.textContent = text;
    if (items && items.length) {
      duplicateModalList.hidden = false;
      duplicateModalList.innerHTML = items.map((i) => `<div>${escapeHtml(i)}</div>`).join("");
      duplicateSkipBtn.hidden = false;
    } else {
      duplicateModalList.hidden = true;
      duplicateModalList.innerHTML = "";
      duplicateSkipBtn.hidden = true;
    }
    duplicateModal.hidden = false;
  });
}

function closeDuplicateModal(result) {
  duplicateModal.hidden = true;
  if (pendingDuplicateResolve) pendingDuplicateResolve(result);
  pendingDuplicateResolve = null;
}

duplicateCancelBtn.addEventListener("click", () => closeDuplicateModal("cancel"));
duplicateSkipBtn.addEventListener("click", () => closeDuplicateModal("skip"));
duplicateConfirmBtn.addEventListener("click", () => closeDuplicateModal("force"));
duplicateModal.addEventListener("click", (ev) => {
  if (ev.target === duplicateModal) closeDuplicateModal("cancel");
});

const editModal = $("#edit-modal");
const editForm = $("#edit-form");
const editArtistInput = $("#edit-modal-artist");
const editTitleInput = $("#edit-modal-title");
const editCancelBtn = $("#edit-cancel");
let pendingEditSave = null;

function openEditModal(artist, title, onSave) {
  pendingEditSave = onSave;
  editArtistInput.value = artist;
  editTitleInput.value = title;
  editModal.hidden = false;
  editArtistInput.focus();
}

function closeEditModal() {
  editModal.hidden = true;
  pendingEditSave = null;
}

editCancelBtn.addEventListener("click", closeEditModal);
editModal.addEventListener("click", (ev) => {
  if (ev.target === editModal) closeEditModal();
});

editForm.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  if (!pendingEditSave) return;
  const artist = editArtistInput.value.trim();
  const title = editTitleInput.value.trim();
  if (!title) {
    log("err", "el titulo no puede quedar vacio.");
    return;
  }
  const submitBtn = editForm.querySelector('button[type="submit"]');
  submitBtn.disabled = true;
  try {
    await pendingEditSave(artist, title);
    closeEditModal();
  } catch (e) {
    // el callback ya logueo el error especifico; dejamos el modal abierto pa reintentar
  } finally {
    submitBtn.disabled = false;
  }
});

libraryListEl.addEventListener("click", (ev) => {
  const li = ev.target.closest(".lib-row");
  if (!li) return;
  const { filename, artist, title } = li.dataset;

  if (ev.target.closest(".lib-edit-btn")) {
    openEditModal(artist, title, async (newArtist, newTitle) => {
      let res;
      try {
        res = await fetch(`/api/library/${encodeURIComponent(filename)}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ artist: newArtist, title: newTitle }),
        });
      } catch (e) {
        log("err", "fallo de red al actualizar la cancion.", logLibraryEl);
        throw e;
      }
      const data = await res.json();
      if (!res.ok) {
        log("err", data.error || "no se pudo actualizar la cancion.", logLibraryEl);
        throw new Error(data.error || "update failed");
      }
      log("ok", `actualizado: ${newArtist ? newArtist + " - " : ""}${newTitle}`, logLibraryEl);
      await loadLibrary();
    });
    return;
  }
  if (ev.target.closest(".lib-delete-btn")) {
    openDeleteModal(filename, artist, title);
    return;
  }
});

libFilterInput.addEventListener("input", applyLibraryFilter);

libRefreshBtn.addEventListener("click", async () => {
  libRefreshBtn.disabled = true;
  await loadLibrary();
  libRefreshBtn.disabled = false;
});

tabBtns.forEach((btn) => {
  btn.addEventListener("click", () => {
    tabBtns.forEach((b) => b.classList.remove("is-active"));
    btn.classList.add("is-active");
    const tab = btn.dataset.tab;
    viewSearch.hidden = tab !== "search";
    viewAlbums.hidden = tab !== "albums";
    viewLibrary.hidden = tab !== "library";
    if (tab === "library") {
      libFilterInput.value = "";
      loadLibrary();
    }
  });
});

function albumCardHtml(album, index) {
  return `
    <li class="card" data-index="${index}">
      <div class="card-media"><img class="card-thumb" src="${album.thumbnail || ""}" alt="" loading="lazy" /></div>
      <div class="card-body">
        <div class="card-title" title="${escapeHtml(album.title)}">${escapeHtml(album.title)}</div>
        <div class="card-meta-row">
          <div class="card-meta">${escapeHtml(album.artist || "?")}${album.year ? " · " + escapeHtml(album.year) : ""}</div>
        </div>
        <div class="card-actions">
          <button type="button" class="btn btn-accent btn-sm btn-album-download">Descargar album completo</button>
        </div>
      </div>
    </li>
  `;
}

const ALBUM_PAGE_STEP = 20;
const ALBUM_LIMIT_CAP = 100;

let albumResults = [];
let albumSearchQuery = "";

function renderAlbumResults(results) {
  albumResults = results;
  albumResultsEl.innerHTML = results.map(albumCardHtml).join("");
}

async function fetchAlbumResults(query, limit) {
  const res = await fetch(`/api/albums/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  const data = await res.json();
  return { ok: res.ok, data };
}

async function runAlbumSearch(query) {
  logAlbumsEl.innerHTML = "";
  log("info", `buscando albumes de "${query}"...`, logAlbumsEl);
  albumResultsEl.innerHTML = "";
  albumLoadMoreBtn.hidden = true;
  albumSearchQuery = query;
  try {
    const { ok, data } = await fetchAlbumResults(query, ALBUM_PAGE_STEP);
    if (!ok) {
      log("err", data.error || "busqueda de albumes fallida.", logAlbumsEl);
      return;
    }
    if (!data.results || data.results.length === 0) {
      log("warn", "sin albumes encontrados.", logAlbumsEl);
      return;
    }
    renderAlbumResults(data.results);
    albumLoadMoreBtn.hidden = data.results.length < ALBUM_PAGE_STEP || data.results.length >= ALBUM_LIMIT_CAP;
    log("ok", `${data.results.length} album(es) para "${query}"`, logAlbumsEl);
  } catch (e) {
    log("err", "fallo de red al buscar albumes.", logAlbumsEl);
  }
}

albumSearchForm.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const query = albumQueryInput.value.trim();
  if (!query) return;
  await runAlbumSearch(query);
});

albumLoadMoreBtn.addEventListener("click", async () => {
  if (albumResults.length >= ALBUM_LIMIT_CAP) {
    albumLoadMoreBtn.hidden = true;
    return;
  }
  const original = albumLoadMoreBtn.textContent;
  albumLoadMoreBtn.disabled = true;
  albumLoadMoreBtn.textContent = "Cargando...";
  try {
    const nextLimit = Math.min(albumResults.length + ALBUM_PAGE_STEP, ALBUM_LIMIT_CAP);
    const { ok, data } = await fetchAlbumResults(albumSearchQuery, nextLimit);
    if (!ok) {
      log("err", data.error || "no se pudieron cargar mas albumes.", logAlbumsEl);
      return;
    }
    const newResults = data.results || [];
    if (newResults.length <= albumResults.length) {
      log("info", "no hay mas albumes.", logAlbumsEl);
      albumLoadMoreBtn.hidden = true;
      return;
    }
    renderAlbumResults(newResults);
    albumLoadMoreBtn.hidden = newResults.length >= ALBUM_LIMIT_CAP;
  } catch (e) {
    log("err", "fallo de red al cargar mas albumes.", logAlbumsEl);
  } finally {
    albumLoadMoreBtn.disabled = false;
    albumLoadMoreBtn.textContent = original;
  }
});

async function requestAlbumDownload(browseId, bitrate, duplicateMode) {
  const res = await fetch(`/api/albums/${encodeURIComponent(browseId)}/download`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ bitrate, duplicate_mode: duplicateMode }),
  });
  const data = await res.json();
  return { ok: res.ok, status: res.status, data };
}

async function downloadAlbum(album, btn) {
  btn.disabled = true;
  const original = btn.textContent;
  btn.textContent = "Consultando tracks...";
  try {
    let duplicateMode;
    let data;
    while (true) {
      const result = await requestAlbumDownload(album.browse_id, albumBitrateSelect.value, duplicateMode);
      if (result.status === 409 && result.data.duplicate) {
        const items = result.data.duplicates.map(
          (d) => `${d.title}${d.artist ? " - " + d.artist : ""} (ya existe "${d.existing}")`
        );
        const choice = await openDuplicateModal(
          `${result.data.duplicates.length} cancion(es) de este album ya las tienes:`,
          items
        );
        if (choice === "cancel") {
          log("warn", "descarga de album cancelada.", logAlbumsEl);
          btn.disabled = false;
          btn.textContent = original;
          return;
        }
        duplicateMode = choice; // "skip" o "force"
        continue;
      }
      if (!result.ok) {
        log("err", result.data.error || "no se pudo descargar el album.", logAlbumsEl);
        btn.disabled = false;
        btn.textContent = original;
        return;
      }
      data = result.data;
      break;
    }
    const jobs = data.tracks.filter((t) => !t.skipped);
    for (const t of data.tracks) {
      if (t.skipped) log("warn", `omitido "${t.title}" (ya existe "${t.existing}")`, logAlbumsEl);
    }
    let done = 0;
    log("info", `descargando album "${data.album}": ${jobs.length} track(s)...`, logAlbumsEl);
    btn.textContent = `Descargando 0/${jobs.length}`;
    await Promise.all(
      jobs.map(async (t) => {
        const job = await pollJob(t.job_id);
        done++;
        btn.textContent = `Descargando ${done}/${jobs.length}`;
        if (job.status === "done") {
          log("ok", `${job.result.artist} - ${job.result.title}`, logAlbumsEl);
        } else {
          log("err", `${t.artist} - ${t.title}: ${job.error || "no se pudo descargar."}`, logAlbumsEl);
        }
      })
    );
    btn.textContent = "Album descargado";
  } catch (e) {
    log("err", "fallo de red al descargar el album.", logAlbumsEl);
    btn.disabled = false;
    btn.textContent = original;
  }
}

albumResultsEl.addEventListener("click", (ev) => {
  const li = ev.target.closest(".card");
  if (!li) return;
  const album = albumResults[Number(li.dataset.index)];
  const downloadBtn = ev.target.closest(".btn-album-download");
  if (downloadBtn) {
    downloadAlbum(album, downloadBtn);
  }
});

const TYPING_TAGS = new Set(["INPUT", "TEXTAREA", "SELECT"]);

document.addEventListener("keydown", (ev) => {
  if (ev.key === "/" && !TYPING_TAGS.has(document.activeElement.tagName)) {
    ev.preventDefault();
    queryInput.focus();
    queryInput.select();
  } else if (ev.key === "Escape" && !previewModal.hidden) {
    closePreview();
  } else if (ev.key === "Escape" && !deleteModal.hidden) {
    closeDeleteModal();
  } else if (ev.key === "Escape" && !editModal.hidden) {
    closeEditModal();
  } else if (ev.key === "Escape" && !duplicateModal.hidden) {
    closeDuplicateModal("cancel");
  }
});

loadStatus();
