import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
import test from "node:test";

const source = fs.readFileSync(
  new URL("../../frontend/runtime.js", import.meta.url),
  "utf8",
);
const index = (tag = "old") => ({
  __schemaVersion: 2,
  games: [],
  __libraries: { players: `${tag}-players.json`, awards: `${tag}-awards.json` },
  __gameFiles: { GAME: `${tag}-game.json` },
});
const json = (value) =>
  new Response(JSON.stringify(value), {
    headers: { "content-type": "application/json" },
  });
const missing = () => new Response("", { status: 404 });
const deferred = () => {
  let resolve;
  const promise = new Promise((r) => {
    resolve = r;
  });
  return { promise, resolve };
};
async function runtime(fetcher) {
  let now = Date.now();
  const boot = deferred(),
    calls = [],
    errors = [],
    events = {},
    saved = new Map([["passport:journal", "private note"]]);
  const addEventListener = (name, fn) => {
    events[name] = fn;
  };
  const context = {
    Response,
    URL,
    setTimeout,
    clearTimeout,
    setInterval: (fn) => {
      events.interval = fn;
    },
    Date: class extends Date {
      static now() {
        return now;
      }
    },
    addEventListener,
    document: { visibilityState: "visible", addEventListener },
    __BOOT_URL: "boot.json",
    navigator: {},
    location: { protocol: "https:", href: "https://example.test/" },
    localStorage: {
      getItem: (k) => saved.get(k) ?? null,
      setItem: (k, v) => saved.set(k, v),
    },
    __onDataReady: () => boot.resolve(),
    __onDataError: (error) => {
      errors.push(error);
      boot.resolve();
    },
    fetch: async (path, options) => {
      calls.push({ path, options });
      return fetcher(path, options);
    },
  };
  context.window = context;
  vm.runInNewContext(source, context);
  await boot.promise;
  return {
    context,
    calls,
    errors,
    saved,
    events,
    advance: (ms) => {
      now += ms;
    },
  };
}

test("open tabs refresh visible player totals atomically without a missing file", async () => {
  const late = deferred();
  const {
    context: app,
    calls,
    events,
    advance,
  } = await runtime((path) => {
    if (path === "boot.json") return json(index());
    if (path === "data.json") return json(index("new"));
    if (path === "new-players.json") return late.promise;
    return json([path]);
  });
  await app.loadPassportKeys(["players"]);
  advance(60_000);
  const update = events.focus();
  await events.visibilitychange();
  assert.equal(app.BASEBALL_DATA.__gameFiles.GAME, "old-game.json");
  assert.equal(app.passportKeysLoaded(["players"]), true);
  late.resolve(json(["new-players.json"]));
  await update;
  assert.equal(app.BASEBALL_DATA.__gameFiles.GAME, "new-game.json");
  assert.deepEqual([...app.BASEBALL_DATA.players], ["new-players.json"]);
  assert.equal(app.passportKeysLoaded(["players"]), true);
  assert.equal(calls.filter((c) => c.path === "data.json").length, 1);
  assert.equal(
    calls.some((c) => c.path === "new-awards.json"),
    false,
  );
});

test("background checks skip hidden tabs and retry failed updates without losing data", async () => {
  let failing = true;
  const {
    context: app,
    calls,
    events,
    advance,
    errors,
  } = await runtime((path) => {
    if (path === "boot.json") return json(index());
    if (path === "data.json") return json(index("new"));
    if (path === "new-players.json" && failing) return missing();
    return json([path]);
  });
  await app.loadPassportKeys(["players"]);
  advance(60_000);
  app.document.visibilityState = "hidden";
  await events.interval();
  assert.equal(
    calls.some((c) => c.path === "data.json"),
    false,
  );
  app.document.visibilityState = "visible";
  await events.visibilitychange();
  assert.equal(app.BASEBALL_DATA.__gameFiles.GAME, "old-game.json");
  assert.deepEqual([...app.BASEBALL_DATA.players], ["old-players.json"]);
  assert.equal(errors.length, 0);
  failing = false;
  advance(60_000);
  await events.interval();
  assert.deepEqual([...app.BASEBALL_DATA.players], ["new-players.json"]);
});

test("concurrent missing sections refresh once and discard late old responses", async () => {
  const late = deferred(),
    oldStarted = deferred();
  const { context: app, calls } = await runtime(async (path) => {
    if (path === "boot.json") return json(index());
    if (path === "data.json") return json(index("new"));
    if (path === "old-players.json") {
      oldStarted.resolve();
      return late.promise;
    }
    if (path.startsWith("old-")) return missing();
    return json([path]);
  });
  const players = app.loadPassportKeys(["players"]);
  await oldStarted.promise;
  await Promise.all([
    app.loadPassportKeys(["awards"]),
    app.loadPassportKeys(["awards"]),
  ]);
  late.resolve(json(["OUTDATED"]));
  await players;
  assert.deepEqual([...app.BASEBALL_DATA.players], ["new-players.json"]);
  assert.deepEqual([...app.BASEBALL_DATA.awards], ["new-awards.json"]);
  assert.equal(calls.filter((c) => c.path === "data.json").length, 1);
  assert.equal(
    calls.find((c) => c.path === "data.json").options.cache,
    "no-store",
  );
});

test("refresh retains only libraries whose immutable paths did not change", async () => {
  const fresh = index("new");
  fresh.__libraries.players = "old-players.json";
  const { context: app } = await runtime((path) => {
    if (path === "boot.json") return json(index());
    if (path === "data.json") return json(fresh);
    if (path === "old-awards.json") return missing();
    return json([path]);
  });
  await app.loadPassportKeys(["players"]);
  const players = app.BASEBALL_DATA.players;
  await app.loadPassportKeys(["awards"]);
  assert.equal(app.BASEBALL_DATA.players, players);
  assert.equal(app.passportKeysLoaded(["players", "awards"]), true);
});

test("unchanged index and broken replacement stop with a retryable error", async () => {
  for (const latest of [index(), index("new")]) {
    const { context: app, calls } = await runtime((path) =>
      path === "boot.json"
        ? json(index())
        : path === "data.json"
          ? json(latest)
          : missing(),
    );
    await assert.rejects(app.loadPassportKeys(["awards"]), /HTTP 404/);
    assert.equal(calls.filter((c) => c.path === "data.json").length, 1);
    assert.equal(app.passportKeysLoaded(["awards"]), false);
  }
});

test("failed metadata refresh can be retried without losing loaded data", async () => {
  let fail = true;
  const { context: app } = await runtime((path) => {
    if (path === "boot.json") return json(index());
    if (path === "data.json")
      return fail ? new Response("", { status: 503 }) : json(index("new"));
    if (path === "old-awards.json") return missing();
    return json([path]);
  });
  await app.loadPassportKeys(["players"]);
  await assert.rejects(app.loadPassportKeys(["awards"]), /HTTP 503/);
  assert.equal(app.passportKeysLoaded(["players"]), true);
  fail = false;
  await app.loadPassportKeys(["awards"]);
  assert.equal(app.passportKeysLoaded(["players"]), false);
  await app.loadPassportKeys(["players"]);
  assert.deepEqual([...app.BASEBALL_DATA.players], ["new-players.json"]);
});

test("stale boot index falls back to latest metadata, but server errors do not", async () => {
  const { context: app, errors } = await runtime((path) =>
    path === "boot.json" ? missing() : json(index("new")),
  );
  assert.equal(errors.length, 0);
  assert.equal(app.BASEBALL_DATA.__gameFiles.GAME, "new-game.json");
  const unavailable = await runtime(() => new Response("", { status: 503 }));
  assert.match(unavailable.errors[0], /HTTP 503/);
  assert.equal(unavailable.calls.length, 1);
});

test("incompatible index is rejected without replacing the working archive", async () => {
  const { context: app } = await runtime((path) =>
    path === "boot.json"
      ? json(index())
      : path === "data.json"
        ? json({ ...index("new"), __schemaVersion: 3 })
        : missing(),
  );
  await assert.rejects(app.loadPassportKeys(["awards"]), /site reload/);
  assert.equal(app.BASEBALL_DATA.__gameFiles.GAME, "old-game.json");
});

test("game loading and offline saves recover expired paths without changing private notes", async () => {
  for (const operation of ["load", "save"]) {
    const { context: app, saved } = await runtime((path) =>
      path === "boot.json"
        ? json(index())
        : path === "data.json"
          ? json(index("new"))
          : path.startsWith("old-")
            ? missing()
            : json({ gameId: "GAME", date: "test" }),
    );
    const writes = [];
    app.caches = {
      open: async () => ({
        put: async (url, response) =>
          writes.push([url.pathname, await response.json()]),
      }),
    };
    app.navigator.serviceWorker = { ready: Promise.resolve() };
    if (operation === "load")
      assert.equal((await app.loadPassportGame("GAME")).gameId, "GAME");
    else {
      await app.saveOfflineGame("GAME");
      assert.equal(writes[0][0], "/new-game.json");
      assert.equal(
        JSON.parse(saved.get("passport:offline"))[0].path,
        "new-game.json",
      );
    }
    assert.equal(saved.get("passport:journal"), "private note");
  }
});

test("saved game remains available when release recovery is offline", async () => {
  const { context: app, saved } = await runtime((path) =>
    path === "boot.json"
      ? json(index())
      : path === "data.json"
        ? Promise.reject(new Error("offline"))
        : missing(),
  );
  saved.set(
    "passport:offline",
    JSON.stringify([{ id: "GAME", path: "saved.json" }]),
  );
  app.caches = {
    open: async () => ({
      match: async () => json({ gameId: "GAME", saved: true }),
    }),
  };
  assert.equal((await app.loadPassportGame("GAME")).saved, true);
});

test("service worker bypasses cache for stable metadata and explicit refreshes", async () => {
  const handlers = {};
  const worker = fs
    .readFileSync(new URL("../../frontend/sw.js", import.meta.url), "utf8")
    .replace("__SHELL__", '["index.html"]');
  vm.runInNewContext(worker, {
    URL,
    self: {
      location: { origin: "https://example.test" },
      addEventListener: (name, fn) => {
        handlers[name] = fn;
      },
    },
    caches: { match: async () => "OLD CACHE" },
    fetch: async () => "NETWORK",
  });
  for (const [path, cache, expected] of [
    ["data.json", "default", "NETWORK"],
    ["release.json", "default", "NETWORK"],
    ["data-players-abc.json", "no-store", "NETWORK"],
    ["data-game-abc.json", "default", "OLD CACHE"],
  ]) {
    let response;
    handlers.fetch({
      request: {
        url: `https://example.test/${path}`,
        method: "GET",
        mode: "cors",
        cache,
      },
      respondWith: (p) => {
        response = p;
      },
    });
    assert.equal(await response, expected);
  }
});
