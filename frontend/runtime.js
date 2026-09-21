var BASEBALL_DATA = null;
var DATA_LOAD_ERROR = null;
const loadedKeys = new Set();
const pendingKeys = new Map();
async function fetchJSON(path) {
  const response = await fetch(path);
  if (!response.ok)
    throw new Error(`Could not load this section (HTTP ${response.status}).`);
  return response.json();
}
window.loadPassportKeys = async (keys) => {
  await Promise.all(
    keys
      .filter((k) => BASEBALL_DATA?.__libraries?.[k])
      .map((key) => {
        if (loadedKeys.has(key)) return Promise.resolve();
        if (!pendingKeys.has(key))
          pendingKeys.set(
            key,
            fetchJSON(BASEBALL_DATA.__libraries[key])
              .then((value) => {
                BASEBALL_DATA = { ...BASEBALL_DATA, [key]: value };
                loadedKeys.add(key);
              })
              .finally(() => pendingKeys.delete(key)),
          );
        return pendingKeys.get(key);
      }),
  );
  window.__onDataReady?.(BASEBALL_DATA);
  return BASEBALL_DATA;
};
window.passportKeysLoaded = (keys) =>
  keys.every((k) => loadedKeys.has(k) || !BASEBALL_DATA?.__libraries?.[k]);
window.loadPassportGame = async (gameId) => {
  const path = BASEBALL_DATA?.__gameFiles?.[gameId];
  if (!path) throw new Error("This game is unavailable in this build.");
  try {
    return await fetchJSON(path);
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
  const path = BASEBALL_DATA.__gameFiles[gameId];
  const response = await fetch(path);
  if (!response.ok) throw new Error("Could not save this game.");
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
window.__bootPassport = () =>
  fetchJSON(window.__BOOT_URL)
    .then((data) => {
      BASEBALL_DATA = data;
      window.__onDataReady?.(data);
      if ("serviceWorker" in navigator)
        navigator.serviceWorker.register("sw.js").catch(() => {});
    })
    .catch((error) => {
      DATA_LOAD_ERROR =
        location.protocol === "file:" ? "file_protocol" : error.message;
      window.__onDataError?.(DATA_LOAD_ERROR);
    });
window.__bootPassport();
