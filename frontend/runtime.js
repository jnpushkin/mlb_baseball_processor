var BASEBALL_DATA = null;
var DATA_LOAD_ERROR = null;
const loadedKeys = new Set();
const pendingKeys = new Map();
let dataGeneration = 0;
let indexSignature = "";
let refreshingIndex = null;

async function fetchResponse(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) {
    const error = new Error(
      `Could not load this section (HTTP ${response.status}).`,
    );
    error.status = response.status;
    error.path = path;
    throw error;
  }
  return response;
}
async function fetchJSON(path, options) {
  return (await fetchResponse(path, options)).json();
}
function validateIndex(data) {
  if (
    data?.__schemaVersion !== 2 ||
    !Array.isArray(data.games) ||
    !data.__libraries ||
    !data.__gameFiles
  )
    throw new Error(
      "This release needs a site reload. Your saved notes will stay on this device.",
    );
}
function installIndex(data, preloaded = {}) {
  validateIndex(data);
  const signature = JSON.stringify(data);
  if (signature === indexSignature) return;
  const previous = BASEBALL_DATA;
  const retained = {};
  for (const key of loadedKeys) {
    if (
      data.__libraries[key] &&
      data.__libraries[key] === previous?.__libraries?.[key]
    )
      retained[key] = previous[key];
    else loadedKeys.delete(key);
  }
  for (const key of Object.keys(preloaded)) loadedKeys.add(key);
  indexSignature = signature;
  BASEBALL_DATA = {
    ...data,
    ...retained,
    ...preloaded,
    __generation: ++dataGeneration,
  };
  DATA_LOAD_ERROR = null;
  window.__onDataReady?.(BASEBALL_DATA);
}
async function refreshIndex(failedGeneration, preserveLoaded = false) {
  // Several sections can fail together after a deploy; share one refresh.
  if (failedGeneration !== dataGeneration) return;
  if (!refreshingIndex) {
    refreshingIndex = fetchJSON("data.json", { cache: "no-store" })
      .then(async (data) => {
        validateIndex(data);
        const preloaded = {};
        if (preserveLoaded) {
          // Swap the index and already-visible sections together so filters and
          // in-progress forms survive a newly published game.
          await Promise.all(
            [...loadedKeys].map(async (key) => {
              const path = data.__libraries[key];
              if (path && path !== BASEBALL_DATA.__libraries[key])
                preloaded[key] = await fetchJSON(path);
            }),
          );
        }
        if (failedGeneration === dataGeneration) installIndex(data, preloaded);
      })
      .finally(() => {
        refreshingIndex = null;
      });
  }
  await refreshingIndex;
}

const UPDATE_INTERVAL = 60_000;
let lastUpdateCheck = Date.now();
async function checkForUpdates() {
  if (
    !BASEBALL_DATA ||
    document.visibilityState === "hidden" ||
    navigator.onLine === false
  )
    return;
  if (Date.now() - lastUpdateCheck < UPDATE_INTERVAL) return;
  lastUpdateCheck = Date.now();
  try {
    await refreshIndex(dataGeneration, true);
  } catch {
    // A temporary network/deploy failure must leave the working archive intact.
  }
}
window.addEventListener("focus", checkForUpdates);
window.addEventListener("online", checkForUpdates);
window.addEventListener("hashchange", checkForUpdates);
document.addEventListener("visibilitychange", checkForUpdates);
setInterval(checkForUpdates, UPDATE_INTERVAL);
async function fetchCurrentResource(getPath) {
  for (let attempt = 0; attempt < 2; attempt++) {
    const path = getPath();
    if (!path)
      throw new Error(
        "This item is unavailable in this release. Reload the site to update it.",
      );
    const generation = dataGeneration;
    try {
      const response = await fetchResponse(path);
      // A simultaneous refresh must not mix old data into the new index.
      if (path === getPath()) return { path, response };
    } catch (error) {
      if (error.status !== 404 || attempt) throw error;
      await refreshIndex(generation);
      if (path === getPath()) throw error;
    }
  }
  throw new Error("The site updated while loading. Please retry this section.");
}
window.loadPassportKeys = async (keys) => {
  for (let attempt = 0; attempt < 3; attempt++) {
    const generation = dataGeneration;
    try {
      await Promise.all(
        keys
          .filter((key) => BASEBALL_DATA?.__libraries?.[key])
          .map((key) => {
            if (loadedKeys.has(key)) return;
            const path = BASEBALL_DATA.__libraries[key];
            if (!pendingKeys.has(path)) {
              const request = fetchCurrentResource(
                () => BASEBALL_DATA.__libraries[key],
              )
                .then(async ({ path: loadedPath, response }) => {
                  const value = await response.json();
                  if (loadedPath !== BASEBALL_DATA.__libraries[key]) return;
                  BASEBALL_DATA = { ...BASEBALL_DATA, [key]: value };
                  loadedKeys.add(key);
                })
                .finally(() => pendingKeys.delete(path));
              pendingKeys.set(path, request);
            }
            return pendingKeys.get(path);
          }),
      );
    } catch (error) {
      if (
        generation === dataGeneration ||
        !error.path ||
        Object.values(BASEBALL_DATA.__libraries).includes(error.path)
      )
        throw error;
      continue;
    }
    if (window.passportKeysLoaded(keys)) {
      window.__onDataReady?.(BASEBALL_DATA);
      return BASEBALL_DATA;
    }
  }
  throw new Error("The site updated while loading. Please retry this section.");
};
window.passportKeysLoaded = (keys) =>
  keys.every((k) => loadedKeys.has(k) || !BASEBALL_DATA?.__libraries?.[k]);
window.loadPassportGame = async (gameId) => {
  try {
    const { response } = await fetchCurrentResource(
      () => BASEBALL_DATA?.__gameFiles?.[gameId],
    );
    return await response.json();
  } catch (error) {
    let saved = [];
    try {
      saved = JSON.parse(localStorage.getItem("passport:offline") || "[]");
    } catch {}
    const record = saved.find((g) => g.id === gameId);
    if (record && "caches" in window) {
      const response = await (
        await caches.open("passport-saved-games")
      ).match(new URL(record.path, location.href));
      if (response) return response.json();
    }
    throw error;
  }
};
window.saveOfflineGame = async (gameId) => {
  if (!("caches" in window) || !("serviceWorker" in navigator))
    throw new Error("Offline storage is unavailable in this browser.");
  await new Promise((resolve, reject) => {
    const timeout = setTimeout(
      () =>
        reject(
          new Error(
            "Offline setup did not finish. Reload while online and try again.",
          ),
        ),
      15000,
    );
    navigator.serviceWorker.ready.then(
      (value) => {
        clearTimeout(timeout);
        resolve(value);
      },
      (error) => {
        clearTimeout(timeout);
        reject(error);
      },
    );
  });
  const { path, response } = await fetchCurrentResource(
    () => BASEBALL_DATA?.__gameFiles?.[gameId],
  );
  const data = await response.clone().json();
  const cache = await caches.open("passport-saved-games");
  await cache.put(new URL(path, location.href), response);
  const old = JSON.parse(localStorage.getItem("passport:offline") || "[]");
  localStorage.setItem(
    "passport:offline",
    JSON.stringify([
      ...old.filter((g) => g.id !== gameId),
      {
        id: gameId,
        path,
        label: `${data.date} · ${data.awayTeam} @ ${data.homeTeam}`,
      },
    ]),
  );
};
window.__bootPassport = async () => {
  try {
    let data;
    try {
      data = await fetchJSON(window.__BOOT_URL);
    } catch (error) {
      if (error.status !== 404) throw error;
      data = await fetchJSON("data.json", { cache: "no-store" });
    }
    installIndex(data);
    if ("serviceWorker" in navigator)
      navigator.serviceWorker.register("sw.js").catch(() => {});
  } catch (error) {
    DATA_LOAD_ERROR =
      location.protocol === "file:" ? "file_protocol" : error.message;
    window.__onDataError?.(DATA_LOAD_ERROR);
  }
};
window.__bootPassport();
