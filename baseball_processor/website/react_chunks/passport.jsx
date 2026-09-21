const readPassportRoute = () => {
  const [path, query = ""] = location.hash.slice(1).split("?");
  const [tab = "dashboard", subtab = null] = path.split("/");
  return {
    tab: tab || "dashboard",
    subtab,
    ...Object.fromEntries(new URLSearchParams(query)),
  };
};
const passportURL = (route) => {
  const { tab, subtab, ...params } = route;
  return (
    "#" +
    (tab || "dashboard") +
    (subtab ? "/" + subtab : "") +
    (Object.values(params).some((v) => v != null && v !== "")
      ? "?" +
        new URLSearchParams(
          Object.entries(params).filter(([k, v]) => v != null && v !== ""),
        )
      : "")
  );
};
const navigatePassport = (patch, options = {}) => {
  const next = { ...readPassportRoute(), ...patch };
  const url = passportURL(next);
  if (url === location.hash) return;
  history.replaceState({ ...history.state, scroll: window.scrollY }, "");
  history[options.replace ? "replaceState" : "pushState"](
    {
      scroll: 0,
      passportParent: options.replace ? history.state?.passportParent : true,
    },
    "",
    url,
  );
  window.dispatchEvent(new Event("passport-route"));
};
const closePassportEntity = () => {
  if (history.state?.passportParent) history.back();
  else navigatePassport({ game: null, player: null }, { replace: true });
};
const openPassportPlayer = (id) => navigatePassport({ player: id, game: null });
const usePassportRoute = () => {
  const [route, setRoute] = useState(readPassportRoute);
  useEffect(() => {
    const change = () => {
      setRoute(readPassportRoute());
      requestAnimationFrame(() =>
        requestAnimationFrame(() =>
          window.scrollTo(0, history.state?.scroll || 0),
        ),
      );
    };
    ["popstate", "hashchange", "passport-route"].forEach((e) =>
      window.addEventListener(e, change),
    );
    return () =>
      ["popstate", "hashchange", "passport-route"].forEach((e) =>
        window.removeEventListener(e, change),
      );
  }, []);
  return route;
};
const scopeGames = (games, scope) => {
  const list = games || [],
    venue = canonicalVenue(list, scope.venue);
  return list.filter(
    (g) =>
      (!scope.year || toSortableDate(g.date).startsWith(scope.year)) &&
      (!scope.type || g.gameType === scope.type) &&
      (!scope.team ||
        sameTeam(g.homeTeam, scope.team, scope.teamMode === "franchise") ||
        sameTeam(g.awayTeam, scope.team, scope.teamMode === "franchise")) &&
      (!scope.venue ||
        (scope.venueMode === "era"
          ? g.venue === scope.venue
          : (g._venueKey || g.venue) === venue)) &&
      (!scope.companion || (g._companions || []).includes(scope.companion)) &&
      (!scope.side ||
        !scope.team ||
        sameTeam(
          scope.side === "home" ? g.homeTeam : g.awayTeam,
          scope.team,
          scope.teamMode === "franchise",
        )),
  );
};
const passportMetrics = (games) => {
  const players = new Set(games.flatMap((g) => g._players || []));
  const totals = {};
  games.forEach((g) =>
    Object.entries(g._totals || {}).forEach(
      ([key, value]) => (totals[key] = (totals[key] || 0) + value),
    ),
  );
  const attendance = games.filter((g) => Number(g.attendance) > 0);
  return {
    games: games.length,
    players: players.size,
    parks: new Set(games.map((g) => g._venueKey || g.venue)).size,
    totals,
    attendanceCoverage: attendance.length,
    averageAttendance: attendance.length
      ? Math.round(
          attendance.reduce((n, g) => n + Number(g.attendance), 0) /
            attendance.length,
        )
      : null,
  };
};
const scopePassportData = (data, route) => {
  if (!data) return null;
  if (
    !route.year &&
    !route.type &&
    !route.team &&
    !route.venue &&
    !route.companion &&
    !route.side
  )
    return data;
  const games = scopeGames(data.games, route),
    ids = new Set(games.map((g) => g.gameId));
  const result = { ...data, games };
  for (const key of [
    "playerGames",
    "pitcherGames",
    "milestones",
    "allMilestones",
    "careerFirsts",
    "careerLasts",
    "allTimePassings",
  ])
    if (Array.isArray(data[key]))
      result[key] = data[key].filter((r) => ids.has(r.gameId || r.game_id));
  if (result.playerGames)
    result.players = aggregateHitterStats(result.playerGames);
  if (result.pitcherGames)
    result.pitchers = aggregatePitcherStats(result.pitcherGames);
  return result;
};
const PASSPORT_FEATURES = [
  [
    "Discover: plays, matchups and career share",
    "dashboard",
    "discover",
    "play explorer batter pitcher duels career share drama stories arsenals personal milestones trivia",
  ],
  ["Season recap", "dashboard", "recap", "season memories share recap"],
  [
    "Collections",
    "dashboard",
    "collections",
    "awards missing completion goals",
  ],
  [
    "Next visit",
    "dashboard",
    "plan",
    "planner goals watchlist orioles ballparks dad",
  ],
  [
    "Compare visits",
    "dashboard",
    "compare",
    "seasons ballparks companions comparison",
  ],
  ["Saved views", "dashboard", "saved", "filters watchlist"],
  [
    "Data health",
    "dashboard",
    "health",
    "coverage sources corrections freshness",
  ],
  ["Signature HRs", "special", "splash", "splash hits mccovey cove"],
  ["Umpires", "trivia", "umpires", "umpires abs"],
  ["Draft picks", "trivia", "drafts", "draft first round"],
  ["Awards", "players", "awards", "mvp cy young gold glove"],
  ["All-Stars", "players", "allstars", "all star roster"],
  ["Jersey numbers", "trivia", "jerseys", "numbers jersey"],
  ["Birthdays", "trivia", "birthdays", "birthday"],
];
const passportSearch = (data, query) => {
  const q = normalizeSearchText(query);
  if (q.length < 2) return [];
  const match = (value) => normalizeSearchText(value).includes(q);
  const results = [];
  const seen = new Set();
  [
    ...(data.players || []),
    ...(data.pitchers || []),
    ...(data.playersWithoutStats || []),
  ].forEach((p) => {
    if (match(p.name) && !seen.has(p.playerId)) {
      seen.add(p.playerId);
      results.push({
        type: "player",
        label: p.name,
        id: p.playerId,
        sub: p.team || "",
        tab: "players",
      });
    }
  });
  [...(data.games || [])]
    .sort((a, b) =>
      toSortableDate(b.date).localeCompare(toSortableDate(a.date)),
    )
    .forEach((g) => {
      const aliases = [
        g.venue,
        ...Object.entries(data.stadiumAliases || {})
          .filter(([k, v]) => v === g.venue || k === g.venue)
          .flat(),
      ];
      if (
        match(
          `${g.date} ${g.awayTeam} ${g.homeTeam} ${TEAM_CODE_TO_NAME[g.awayTeam]} ${TEAM_CODE_TO_NAME[g.homeTeam]} ${aliases.join(" ")} ${g.gameId}`,
        )
      )
        results.push({
          type: "game",
          label: `${g.awayTeam} @ ${g.homeTeam}`,
          id: g.gameId,
          sub: `${g.date} · ${g.venue}`,
          tab: "gamelog",
        });
    });
  PASSPORT_FEATURES.forEach(([label, tab, subtab, aliases]) => {
    if (match(`${label} ${aliases}`))
      results.push({
        type: "feature",
        label,
        tab,
        subtab,
        sub: "Open feature",
      });
  });
  (data.teams || []).forEach((t) => {
    if (match(`${t.team} ${TEAM_CODE_TO_NAME[t.team] || ""}`))
      results.push({
        type: "team",
        label: TEAM_CODE_TO_NAME[t.team] || t.team,
        sub: `${t.games || 0} games`,
        tab: "gamelog",
        searchValue: t.team,
      });
  });
  (data.stadiums || []).forEach((v) => {
    const name = v.name || v.stadium || "";
    if (match(`${name} ${v.city || ""} ${v.state || ""}`))
      results.push({
        type: "venue",
        label: name,
        sub: `${v.games || 0} games`,
        tab: "gamelog",
        searchValue: name,
      });
  });
  (data.searchEvents || []).forEach((event) => {
    if (match(`${event.label} ${event.sub} ${event.searchText || ""}`))
      results.push(event);
  });
  return results.sort(
    (a, b) =>
      Number(normalizeSearchText(b.label) === q) -
      Number(normalizeSearchText(a.label) === q),
  );
};
const passportKeysForRoute = (route) => {
  const basic = [
    "players",
    "pitchers",
    "playerGames",
    "pitcherGames",
    "careerFirstsByGame",
    "careerFirstsByPlayer",
    "milestones",
    "allTimePassings",
    "allTimePassingsByGame",
  ];
  const mapping = {
    gamelog: basic,
    players: [
      ...basic,
      "ncaaCrossRef",
      "ncaaCrossRefMeta",
      "uvaPlayersSeen",
      "hallOfFamers",
      "rispPerformance",
      "twoOutPerformance",
      "rispTwoOutPerformance",
      "basesLoaded",
      "lateClose",
      "wpaLeaders",
      "defensiveLeaders",
      "lineupAnalysis",
      "lineupMatrix",
      "absPlayerStats",
    ],
    milestones: [
      "milestones",
      "allMilestones",
      "careerFirsts",
      "careerLasts",
      "allTimePassings",
    ],
    venues: ["weatherTiming", "orioles"],
    progress: [...basic, "divisionChecklist", "matchupMatrix"],
    special: [
      "summary",
      "signatureHRs",
      "careerFirsts",
      "allTimePassings",
      "players",
      "pitchers",
      "playerGames",
      "pitcherGames",
    ],
    trivia: ["umpireLog", "jerseyLog", "playerGames", "pitcherGames"],
    companions: [],
    orioles: ["orioles"],
  };
  let keys = mapping[route.tab] || [];
  if (route.tab === "dashboard" && route.subtab === "analysis")
    keys = [
      ...basic,
      "summary",
      "careerFirsts",
      "careerLasts",
      "weatherTiming",
    ];
  if (route.tab === "players" && route.subtab === "nostats")
    keys = [...keys, "playersWithoutStats"];
  if (route.subtab === "awards") keys = [...keys, "awardChecklists"];
  if (route.subtab === "allstars") keys = [...keys, "allStarChecklists"];
  if (route.tab === "trivia" && ["drafts", "draftpicks"].includes(route.subtab))
    keys = [...keys, "firstRoundDraftPicks"];
  if (route.tab === "trivia" && ["origins", "birthdays"].includes(route.subtab))
    keys = [...keys, "playerBios"];
  if (route.tab === "trivia" && route.subtab === "home-away")
    keys = [...keys, "homeAwayGames"];
  if (route.tab === "dashboard" && route.subtab === "recap")
    keys = [...keys, "milestones", "careerFirsts"];
  if (route.tab === "dashboard" && route.subtab === "search")
    keys = [...keys, "searchEvents"];
  if (route.tab === "dashboard" && route.subtab === "discover") {
    const analysisKeys = {
      plays: ["playEvents"],
      duels: ["playEvents"],
      shared: ["playerGames", "pitcherGames"],
      stories: ["gameStories"],
      arsenal: ["pitchArsenal"],
      career: ["careerContext", "playerGames", "pitcherGames"],
      personal: ["playerGames", "pitcherGames"],
      context: ["playerBios", "awardChecklists", "careerContext"],
      journeys: ["ncaaCrossRef", "playerBios", "playerJourneys"],
      quiz: [],
    };
    keys = [
      ...keys,
      ...(analysisKeys[route.tool || "plays"] || analysisKeys.plays),
    ];
  }
  if (route.tab === "dashboard" && route.subtab === "health")
    keys = [...keys, "analysisHealth", "dataChanges"];
  if (route.player) keys = [...keys, ...basic];
  return [...new Set(keys)];
};
const readPersonal = (key, fallback) => {
  try {
    return JSON.parse(localStorage.getItem("passport:" + key)) ?? fallback;
  } catch {
    return fallback;
  }
};
const validatePassportBackup = (payload) => {
  const object = (value) =>
    value && typeof value === "object" && !Array.isArray(value);
  if (
    !object(payload) ||
    payload.schemaVersion !== 1 ||
    (payload.journal != null && !object(payload.journal))
  )
    throw Error("Invalid backup");
  for (const [id, entry] of Object.entries(payload.journal || {})) {
    if (
      !id ||
      !object(entry) ||
      [
        "notes",
        "seat",
        "moment",
        "companions",
        "updatedAt",
        "trip",
        "ticketCost",
        "currency",
        "rating",
      ].some((k) => entry[k] != null && typeof entry[k] !== "string")
    )
      throw Error("Invalid journal entry");
    if (
      entry.ticketCost &&
      (!Number.isFinite(Number(entry.ticketCost)) ||
        Number(entry.ticketCost) < 0)
    )
      throw Error("Invalid ticket cost");
    if (entry.rating && !["1", "2", "3", "4", "5"].includes(entry.rating))
      throw Error("Invalid game rating");
    if (entry.currency && !/^[A-Z]{3}$/.test(entry.currency))
      throw Error("Invalid currency");
  }
  for (const key of ["images", "views", "goals", "itinerary"])
    if (payload[key] != null && !Array.isArray(payload[key]))
      throw Error("Invalid backup list");
  for (const row of payload.itinerary || []) {
    if (
      !object(row) ||
      !Number.isInteger(row.gamePk) ||
      typeof row.matchup !== "string" ||
      typeof row.date !== "string" ||
      !/^\d{4}-\d{2}-\d{2}$/.test(row.date) ||
      !Number.isFinite(Date.parse(row.date)) ||
      typeof row.venue !== "string" ||
      (row.gameDate != null && typeof row.gameDate !== "string") ||
      (row.gameDate && !Number.isFinite(Date.parse(row.gameDate))) ||
      (row.isTimeTBA != null && typeof row.isTimeTBA !== "boolean") ||
      (row.withDad != null && typeof row.withDad !== "boolean")
    )
      throw Error("Invalid itinerary");
  }
  for (const row of payload.images || []) {
    if (
      !object(row) ||
      typeof row.gameId !== "string" ||
      !Array.isArray(row.images) ||
      row.images.some(
        (i) =>
          typeof i !== "string" ||
          !/^data:image\/(png|jpeg|webp);base64,[A-Za-z0-9+/=]+$/.test(i),
      )
    )
      throw Error("Invalid image");
  }
  for (const view of payload.views || []) {
    if (
      !object(view) ||
      typeof view.name !== "string" ||
      !object(view.route) ||
      Object.values(view.route).some((v) => v != null && typeof v !== "string")
    )
      throw Error("Invalid view");
    if (
      view.tables &&
      (!object(view.tables) ||
        Object.entries(view.tables).some(
          ([k, v]) => !k.startsWith("dt_") || typeof v !== "string",
        ))
    )
      throw Error("Invalid table preferences");
  }
  for (const goal of payload.goals || [])
    if (
      !object(goal) ||
      typeof goal.id !== "string" ||
      typeof goal.name !== "string" ||
      !["player", "team", "ballpark", "collection"].includes(goal.kind)
    )
      throw Error("Invalid goal");
  return payload;
};
const isOriolesTeam = (team) => {
  if (team?.id === 110) return true;
  const name =
    typeof team === "object" ? team?.abbreviation || team?.name : team;
  return ["bal", "baltimore", "baltimore orioles"].includes(
    normalizeSearchText(name),
  );
};
const ballparkGoalProgress = (data, stadiums) => {
  const identity = (name) =>
    venueIdentity(name, data.stadiumAliases || {}, stadiums);
  const current = stadiums.filter(
    (park) =>
      park.current &&
      !park.springTraining &&
      !park.international &&
      !["ST", "INT"].includes(park.team),
  );
  const targets = [
    ...new Map(current.map((park) => [identity(park.name), park])).values(),
  ];
  const definitions = [
    {
      id: "orioles",
      title: "Orioles in every ballpark",
      orioles: true,
      dad: false,
    },
    {
      id: "orioles-dad",
      title: "Orioles in every ballpark with Dad",
      orioles: true,
      dad: true,
    },
    { id: "dad", title: "Every ballpark with Dad", orioles: false, dad: true },
  ];
  return definitions.map((goal) => {
    const matches = (data.games || []).filter((game) => {
      const companions = [
        ...(game._companions || []),
        ...(data.companionData?.gameCompanions?.[game.gameId] || []),
      ];
      return (
        (!goal.orioles || [game.homeTeam, game.awayTeam].some(isOriolesTeam)) &&
        (!goal.dad ||
          companions.some((name) => normalizeSearchText(name) === "dad"))
      );
    });
    const byPark = new Map();
    for (const game of matches) {
      const key = identity(game._venueKey || game.venue);
      if (!byPark.has(key)) byPark.set(key, []);
      byPark.get(key).push(game);
    }
    const parks = targets.map((park) => ({
      ...park,
      identity: identity(park.name),
      visits: byPark.get(identity(park.name)) || [],
    }));
    const targetKeys = new Set(parks.map((park) => park.identity));
    const otherParks = [...byPark]
      .filter(([key]) => !targetKeys.has(key))
      .map(([key, visits]) => ({
        identity: key,
        name:
          stadiums.find((park) => identity(park.name) === key)?.name ||
          visits[0]._venueKey ||
          visits[0].venue,
        visits,
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
    return {
      ...goal,
      parks,
      otherParks,
      completed: parks.filter((park) => park.visits.length),
      missing: parks.filter((park) => !park.visits.length),
    };
  });
};
const ballparkScheduleMatches = (
  game,
  progress,
  identity,
  withDad = true,
  focus = "all",
) => {
  const park = identity(game.venue?.name);
  const orioles = [game.teams?.home?.team, game.teams?.away?.team].some(
    isOriolesTeam,
  );
  return progress.filter(
    (goal) =>
      (focus === "all" || goal.id === focus) &&
      (!goal.dad || withDad) &&
      (!goal.orioles || orioles) &&
      goal.missing.some((p) => p.identity === park),
  );
};

const usePersonal = (key, fallback) => {
  const [value, setValue] = useState(() => readPersonal(key, fallback));
  const [error, setError] = useState("");
  useEffect(() => {
    const refresh = () => setValue(readPersonal(key, fallback));
    window.addEventListener("passport-personal", refresh);
    return () => window.removeEventListener("passport-personal", refresh);
  }, [key]);
  const save = (next) => {
    try {
      localStorage.setItem("passport:" + key, JSON.stringify(next));
      setValue(next);
      setError("");
      window.dispatchEvent(new Event("passport-personal"));
      return true;
    } catch {
      setError(
        "Storage is full or unavailable. Export a backup before clearing space.",
      );
      return false;
    }
  };
  return [value, save, error];
};
const downloadPassport = (value, filename) => {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(value, null, 2)], { type: "application/json" }),
  );
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};
const PassportNotice = ({ children }) => (
  <p role="status" className="text-sm text-blue-700 dark:text-blue-300 my-2">
    {children}
  </p>
);
const PassportScope = ({ data, route }) => {
  const [name, setName] = useState("");
  const [message, setMessage] = useState("");
  const [saved, save, error] = usePersonal("views", []);
  const years = [
    ...new Set(
      (data.games || []).map((g) => toSortableDate(g.date).slice(0, 4)),
    ),
  ]
    .sort()
    .reverse();
  return (
    <details className="passport-panel passport-scope mb-4 no-print">
      <summary className="text-sm font-semibold">
        Browse: {route.year || "All years"} · {route.type || "All game types"}
        {route.team ? " · " + route.team : ""}
        {route.venue ? " · " + route.venue : ""}
        {route.companion ? " · with " + route.companion : ""}
        {route.side ? " · " + route.side : ""}
      </summary>
      <div className="flex flex-wrap gap-2 mt-2">
        <select
          aria-label="Season scope"
          className="passport-input"
          value={route.year || ""}
          onChange={(e) => navigatePassport({ year: e.target.value })}
        >
          <option value="">All years</option>
          {years.map((y) => (
            <option key={y}>{y}</option>
          ))}
        </select>
        <select
          aria-label="Game type scope"
          className="passport-input"
          value={route.type || ""}
          onChange={(e) => navigatePassport({ type: e.target.value })}
        >
          <option value="">All game types</option>
          <option value="regular">Regular season</option>
          <option value="postseason">Postseason</option>
          <option value="spring">Spring training</option>
        </select>
        <select
          aria-label="Team scope"
          className="passport-input"
          value={route.team || ""}
          onChange={(e) => navigatePassport({ team: e.target.value })}
        >
          <option value="">All teams</option>
          {[...new Set(data.games.flatMap((g) => [g.awayTeam, g.homeTeam]))]
            .sort()
            .map((t) => (
              <option key={t}>{t}</option>
            ))}
        </select>
        <select
          aria-label="Ballpark scope"
          className="passport-input max-w-full"
          value={route.venue || ""}
          onChange={(e) => navigatePassport({ venue: e.target.value })}
        >
          <option value="">All ballparks</option>
          {[
            ...new Set(
              data.games.map((g) =>
                route.venueMode === "era" ? g.venue : g._venueKey || g.venue,
              ),
            ),
          ]
            .sort()
            .map((v) => (
              <option key={v}>{v}</option>
            ))}
        </select>
        <select
          aria-label="Ballpark grouping"
          className="passport-input"
          value={route.venueMode || "park"}
          onChange={(e) =>
            navigatePassport({ venueMode: e.target.value, venue: null })
          }
        >
          <option value="park">Physical ballpark</option>
          <option value="era">Name at the time</option>
        </select>
        <select
          aria-label="Team grouping"
          className="passport-input"
          value={route.teamMode || "era"}
          onChange={(e) => navigatePassport({ teamMode: e.target.value })}
        >
          <option value="era">Team at the time</option>
          <option value="franchise">Whole franchise</option>
        </select>
        <select
          aria-label="Home or away scope"
          className="passport-input"
          disabled={!route.team}
          value={route.side || ""}
          onChange={(e) => navigatePassport({ side: e.target.value })}
        >
          <option value="">Home and away</option>
          <option value="home">Selected team at home</option>
          <option value="away">Selected team away</option>
        </select>
        <select
          aria-label="Companion scope"
          className="passport-input"
          value={route.companion || ""}
          onChange={(e) => navigatePassport({ companion: e.target.value })}
        >
          <option value="">All companions</option>
          {Object.keys(data.companionData?.companions || {}).map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
        <button
          className="passport-button"
          onClick={() =>
            navigatePassport({
              year: null,
              type: null,
              team: null,
              venue: null,
              companion: null,
              side: null,
            })
          }
        >
          Reset scope
        </button>
        <input
          aria-label="Saved view name"
          placeholder="Name this view"
          className="passport-input"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button
          className="passport-button"
          disabled={!name.trim()}
          onClick={() => {
            const savedOK = save([
              ...saved.filter((v) => v.name !== name.trim()),
              {
                name: name.trim(),
                route: { ...route, game: null, player: null },
                tables: Object.fromEntries(
                  Object.keys(localStorage)
                    .filter((k) => k.startsWith("dt_"))
                    .map((k) => [k, localStorage.getItem(k)]),
                ),
              },
            ]);
            if (savedOK) {
              setMessage(`Saved “${name.trim()}” in Saved views.`);
              setName("");
            }
          }}
        >
          Save view
        </button>
      </div>
      {(error || message) && (
        <PassportNotice>{error || message}</PassportNotice>
      )}
    </details>
  );
};
const PassportGameList = ({ games }) => (
  <div className="divide-y divide-slate-200">
    {games.map((g) => (
      <button
        key={g.gameId}
        className="w-full text-left py-3 flex justify-between gap-3 hover:text-blue-600"
        onClick={() => requestGameDetails(g.gameId)}
      >
        <span>
          <strong>
            {g.awayTeam} @ {g.homeTeam}
          </strong>
          <span className="block text-sm text-slate-500">
            {g.date} · {g.venue}
          </span>
        </span>
        <span className="text-sm">{g.score} →</span>
      </button>
    ))}
  </div>
);
const PassportMetrics = ({ games }) => {
  const m = passportMetrics(games);
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {[
        ["Games", m.games],
        ["Players seen", m.players],
        ["Ballparks", m.parks],
        ["Home runs", m.totals.hr || 0],
      ].map(([label, value]) => (
        <StatCard key={label} title={label} value={value.toLocaleString()} />
      ))}
    </div>
  );
};
const PassportHome = ({ data, allData, route }) => {
  const games = [...data.games].sort((a, b) =>
    toSortableDate(b.date).localeCompare(toSortableDate(a.date)),
  );
  const today = new Date();
  const latest = games[0];
  const anniversary = allData.games.filter((g) => {
    const d = toSortableDate(g.date);
    return (
      d.slice(4) ===
      String(today.getMonth() + 1).padStart(2, "0") +
        String(today.getDate()).padStart(2, "0")
    );
  });
  const [knownGames] = useState(() => readPersonal("visitedGameIds", null));
  useEffect(() => {
    try {
      localStorage.setItem(
        "passport:visitedGameIds",
        JSON.stringify(allData.games.map((g) => g.gameId)),
      );
    } catch {}
  }, []);
  const newGames = knownGames
    ? games.filter((g) => !knownGames.includes(g.gameId))
    : [];
  const sets = (allData.__collectionSets || [])
    .filter((s) => s.missing > 0 && s.seen > 0)
    .sort((a, b) => a.missing - b.missing)
    .slice(0, 3);
  return (
    <div className="space-y-5">
      <section className="passport-hero">
        <p className="passport-eyebrow">Your latest visit</p>
        {latest && (
          <>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-5 mt-3">
              <div>
                <h2 className="text-2xl sm:text-3xl font-bold tracking-tight flex flex-wrap items-center gap-3">
                  <TeamToken code={latest.awayTeam} logoSize={32} />{" "}
                  <span className="passport-hero-muted font-normal text-lg">
                    at
                  </span>{" "}
                  <TeamToken code={latest.homeTeam} logoSize={32} />
                </h2>
                <p className="passport-hero-muted mt-2 text-sm">
                  {latest.date} · {latest.venue}
                </p>
              </div>
              <div className="passport-scoreboard">
                <span className="passport-eyebrow">
                  Final ·{" "}
                  {latest.gameType === "spring"
                    ? "Spring training"
                    : latest.gameType === "postseason"
                      ? "Postseason"
                      : "Regular season"}
                </span>
                <p className="text-xl sm:text-2xl font-bold stat-num mt-1">
                  {latest.score}
                </p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-3 mt-5">
              <button
                className="passport-primary"
                onClick={() => requestGameDetails(latest.gameId)}
              >
                Open game recap →
              </button>
              <button
                className="passport-hero-link"
                onClick={() =>
                  navigatePassport({
                    tab: "dashboard",
                    subtab: "plan",
                  })
                }
              >
                Plan the next visit
              </button>
            </div>
          </>
        )}
        {!games.length && (
          <p>
            No games match this scope. Reset the filters to see your archive.
          </p>
        )}
      </section>
      <PassportMetrics games={games} />
      <div className="grid md:grid-cols-2 gap-4">
        <section className="passport-panel">
          <h2 className="text-lg font-bold">What changed</h2>
          {newGames.length ? (
            <>
              <p>{newGames.length} games added since your last visit.</p>
              <PassportGameList games={newGames.slice(0, 3)} />
            </>
          ) : (
            <>
              <p className="text-sm text-slate-500">
                New faces in your latest game
              </p>
              <p className="text-3xl font-bold my-2">
                {games[0]?.firstSeenPlayerIds?.length || 0}
              </p>
              <p className="text-sm">Players you saw for the first time.</p>
            </>
          )}
        </section>
        <section className="passport-panel">
          <h2 className="text-lg font-bold">Close to completing</h2>
          {sets.map((s) => (
            <button
              key={s.id}
              className="block w-full text-left py-2"
              onClick={() =>
                navigatePassport({ tab: "dashboard", subtab: "collections" })
              }
            >
              <strong>{s.title}</strong>
              <span className="block text-sm text-slate-500">
                {s.seen} of {s.total} entries · {s.missing} remaining
              </span>
              <span className="passport-progress" aria-hidden="true">
                <span
                  style={{ width: `${Math.round((s.seen / s.total) * 100)}%` }}
                />
              </span>
            </button>
          ))}
          <p className="text-xs text-slate-500">
            Historical sets can include retired players.
          </p>
        </section>
      </div>
      {anniversary.length > 0 && (
        <section className="passport-panel">
          <h2 className="text-lg font-bold">On this day</h2>
          <PassportGameList games={anniversary.slice(0, 3)} />
        </section>
      )}
      <section className="passport-panel">
        <h2 className="text-lg font-bold">Recent games</h2>
        <PassportGameList games={games.slice(0, 5)} />
      </section>
      <button
        className="passport-button"
        onClick={() =>
          navigatePassport({ tab: "dashboard", subtab: "analysis" })
        }
      >
        Detailed charts and lifetime analysis →
      </button>
    </div>
  );
};
const PassportRecap = ({ data, allData, route }) => {
  const games = data.games;
  const ids = new Set(games.map((g) => g.gameId));
  const firstPlayers = new Set(
    games.flatMap((g) => g.firstSeenPlayerIds || []),
  );
  const previous = allData.games.filter(
    (g) =>
      !ids.has(g.gameId) &&
      (!games.length ||
        toSortableDate(g.date) <
          games.map((g) => toSortableDate(g.date)).sort()[0]),
  );
  const previousParks = new Set(previous.map((g) => g._venueKey || g.venue));
  const newParks = [
    ...new Set(games.map((g) => g._venueKey || g.venue)),
  ].filter((v) => !previousParks.has(v));
  const [message, setMessage] = useState("");
  const records = [];
  const best = { hr: 0, h: 0, so: 0 };
  let priorCount = 0;
  [...allData.games]
    .filter((g) => !route.type || g.gameType === route.type)
    .sort((a, b) =>
      toSortableDate(a.date).localeCompare(toSortableDate(b.date)),
    )
    .forEach((g) => {
      for (const key of Object.keys(best)) {
        const value = g._totals?.[key] || 0;
        if (priorCount && ids.has(g.gameId) && value > best[key])
          records.push({ game: g, key, value });
        best[key] = Math.max(best[key], value);
      }
      priorCount++;
    });
  const moments = (data.milestones || [])
    .filter((m) => ids.has(m.gameId || m.game_id))
    .slice(0, 8);
  const biggest = [...games]
    .sort((a, b) => (b._totals?.hr || 0) - (a._totals?.hr || 0))
    .slice(0, 3);
  const companions = Object.values(allData.companionData?.companions || {})
    .map((c) => ({
      ...c,
      count: (c.games || []).filter((g) => ids.has(g.gameId)).length,
    }))
    .filter((c) => c.count)
    .sort((a, b) => b.count - a.count);
  return (
    <div className="space-y-4">
      <section className="passport-panel">
        <h1 className="text-2xl font-bold">{route.year || "All-time"} recap</h1>
        <p className="text-sm text-slate-500">
          {route.type || "All game types"} · {games.length} attended games in
          this scope
        </p>
        <div className="flex gap-2 mt-3 no-print">
          <button className="passport-button" onClick={() => window.print()}>
            Print / Save PDF
          </button>
          <button
            className="passport-button"
            onClick={async () => {
              try {
                await navigator.clipboard.writeText(location.href);
                setMessage(
                  "Share link copied. Private saved data is not included.",
                );
              } catch {
                setMessage(
                  "Copy the address from your browser to share this recap.",
                );
              }
            }}
          >
            Copy share link
          </button>
        </div>
        <PassportNotice>{message}</PassportNotice>
      </section>
      <PassportMetrics games={games} />
      <section className="passport-panel">
        <h2 className="text-lg font-bold">New to your passport</h2>
        <p>
          {firstPlayers.size} first-seen players · {newParks.length} new
          ballparks
        </p>
        <p className="text-sm mt-2">
          {newParks.join(" · ") || "You returned to familiar parks."}
        </p>
      </section>
      <section className="passport-panel">
        <h2 className="text-lg font-bold">Home run highlights</h2>
        <PassportGameList games={biggest} />
      </section>
      <section className="passport-panel">
        <h2 className="text-lg font-bold">Records broken on your visits</h2>
        <p className="text-sm text-slate-500">
          Combined game totals, compared chronologically with your earlier games
          of the same game-type scope.
        </p>
        {records.length ? (
          records
            .slice(-8)
            .reverse()
            .map((r, i) => (
              <button
                key={i}
                className="block text-left text-sm py-2 text-blue-600"
                onClick={() => requestGameDetails(r.game.gameId)}
              >
                {r.game.date}: {r.value}{" "}
                {
                  { hr: "home runs", h: "hits", so: "pitching strikeouts" }[
                    r.key
                  ]
                }
              </button>
            ))
        ) : (
          <p className="text-sm my-2">No new highs in this scope.</p>
        )}
      </section>
      <section className="passport-panel">
        <h2 className="text-lg font-bold">Top moments</h2>
        {moments.length ? (
          moments.map((m, i) => (
            <button
              key={i}
              className="block text-sm text-left py-2 text-blue-600"
              onClick={() => requestGameDetails(m.gameId || m.game_id)}
            >
              {m.date} · {m.player} · {m.type}
            </button>
          ))
        ) : (
          <p className="text-sm my-2">
            No recorded game milestones in this scope.
          </p>
        )}
      </section>
      <section className="passport-panel">
        <h2 className="text-lg font-bold">Companion highlights</h2>
        {companions.length ? (
          companions.slice(0, 5).map((c) => (
            <p key={c.name}>
              {c.name}: {c.count} games
            </p>
          ))
        ) : (
          <p className="text-sm">No companion records for this scope.</p>
        )}
      </section>
    </div>
  );
};
const photoStore = (mode, key, value) =>
  new Promise((resolve, reject) => {
    const request = indexedDB.open("mlb-passport-private", 1);
    request.onupgradeneeded = () =>
      request.result.createObjectStore("photos", { keyPath: "gameId" });
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const tx = db.transaction(
        "photos",
        mode === "put" ? "readwrite" : "readonly",
      );
      const store = tx.objectStore("photos");
      let operation;
      if (mode === "put") operation = store.put({ gameId: key, images: value });
      else operation = key ? store.get(key) : store.getAll();
      let result;
      operation.onsuccess = () => {
        result = operation.result;
      };
      tx.oncomplete = () => {
        db.close();
        resolve(result);
      };
      tx.onerror = () => {
        db.close();
        reject(tx.error);
      };
    };
  });
const PassportCollections = ({ data }) => {
  const [goals, save, error] = usePersonal("goals", []);
  const [filter, setFilter] = useState("");
  const sets = [...(data.__collectionSets || [])]
    .sort((a, b) => a.missing - b.missing)
    .filter((s) =>
      normalizeSearchText(s.title).includes(normalizeSearchText(filter)),
    );
  const pin = (s) =>
    save(
      goals.some((g) => g.id === s.id)
        ? goals.filter((g) => g.id !== s.id)
        : [...goals, { id: s.id, name: s.title, kind: "collection" }],
    );
  return (
    <div className="space-y-4">
      <section className="passport-panel">
        <h1 className="text-2xl font-bold">Your collections</h1>
        <p className="text-sm text-slate-500">
          Lifetime collection progress. Checked award entries mean you have seen
          the winner at any point, unless the detailed checklist says otherwise.
        </p>
        <div className="flex flex-wrap gap-2 mt-3">
          {[
            ["Ballparks", "venues"],
            ["Division checklist", "progress"],
            ["Awards", "players", "awards"],
            ["All-Stars", "players", "allstars"],
            ["Jerseys", "trivia", "jerseys"],
            ["Draft picks", "trivia", "drafts"],
          ].map(([name, tab, subtab]) => (
            <button
              key={name}
              className="passport-button"
              onClick={() =>
                navigatePassport({
                  tab,
                  subtab,
                  year: null,
                  type: null,
                  team: null,
                  venue: null,
                })
              }
            >
              {name}
            </button>
          ))}
        </div>
      </section>
      <input
        aria-label="Find a collection"
        placeholder="Find a collection"
        className="passport-input w-full"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
      />
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {sets.map((s) => (
          <article key={s.id} className="passport-panel">
            <h2 className="font-bold">{s.title}</h2>
            <p className="text-sm text-slate-500 my-2">
              {s.seen} / {s.total} entries ·{" "}
              {s.missing === 0 ? "Complete" : `${s.missing} missing`}
            </p>
            <progress
              className="w-full"
              value={s.seen}
              max={s.total}
              aria-label={`${s.title} completion`}
            />
            <div className="flex gap-2 mt-2">
              <button
                className="passport-button"
                aria-pressed={goals.some((g) => g.id === s.id)}
                onClick={() => pin(s)}
              >
                {goals.some((g) => g.id === s.id) ? "Unpin goal" : "Pin goal"}
              </button>
              <button
                className="passport-button"
                onClick={() =>
                  navigatePassport({ tab: "players", subtab: "awards" })
                }
              >
                Explore
              </button>
            </div>
          </article>
        ))}
      </div>
      <PassportNotice>{error}</PassportNotice>
    </div>
  );
};
const BallparkGoalCard = ({ goal, onPlan }) => (
  <article className="passport-panel space-y-3" aria-label={goal.title}>
    <h2 className="text-lg font-bold">{goal.title}</h2>
    <p className="text-3xl font-bold text-blue-700 dark:text-blue-300">
      {goal.completed.length}
      <span className="text-lg text-slate-500">
        {" "}
        / {goal.parks.length} parks
      </span>
    </p>
    <progress
      className="w-full accent-blue-600"
      value={goal.completed.length}
      max={goal.parks.length || 1}
      aria-label={`${goal.title} progress`}
    />
    <p className="text-sm text-slate-500">
      {goal.missing.length
        ? `${goal.missing.length} to go`
        : "All current ballparks complete!"}
    </p>
    <button className="passport-button" onClick={() => onPlan(goal)}>
      Plan for this goal
    </button>
    <details>
      <summary className="font-semibold cursor-pointer">
        Missing parks ({goal.missing.length})
      </summary>
      <ul className="mt-2 space-y-2 text-sm">
        {goal.missing.map((park) => (
          <li key={park.id}>{park.name}</li>
        ))}
      </ul>
    </details>
    <details>
      <summary className="font-semibold cursor-pointer">
        Completed parks ({goal.completed.length})
      </summary>
      <ul className="mt-2 space-y-2 text-sm">
        {goal.completed.map((park) => {
          const first = [...park.visits].sort((a, b) =>
            toSortableDate(a.date).localeCompare(toSortableDate(b.date)),
          )[0];
          return (
            <li key={park.id}>
              <button
                className="text-left text-blue-700 dark:text-blue-300 underline"
                onClick={() => requestGameDetails(first.gameId)}
              >
                {park.name}
              </button>
              <span className="block text-slate-500">
                First: {first.date} · {park.visits.length}{" "}
                {park.visits.length === 1 ? "game" : "games"}
              </span>
            </li>
          );
        })}
      </ul>
    </details>
    {!!goal.otherParks.length && (
      <details>
        <summary className="font-semibold cursor-pointer">
          Other parks visited ({goal.otherParks.length})
        </summary>
        <p className="mt-2 text-sm text-slate-500">
          Former home parks, international venues and spring training parks
          count separately.
        </p>
        <ul className="mt-2 space-y-2 text-sm">
          {goal.otherParks.map((park) => (
            <li key={park.identity}>{park.name}</li>
          ))}
        </ul>
      </details>
    )}
  </article>
);

const PassportPlanner = ({ data }) => {
  const [goals, save, error] = usePersonal("goals", []);
  const [name, setName] = useState("");
  const [kind, setKind] = useState("player");
  const seenTeams = new Set(
    data.games.flatMap((g) => [g.homeTeam, g.awayTeam]),
  );
  const parkIdentity = (name) =>
    venueIdentity(name, data.stadiumAliases || {}, ALL_MLB_STADIUMS || []);
  const visited = new Set(
    data.games.map((g) => parkIdentity(g._venueKey || g.venue)),
  );
  const [rosters, setRosters] = useState({});
  const [rosterTeams, setRosterTeams] = useState({});
  const [rosterMessage, setRosterMessage] = useState("");
  const checkRoster = async (goal) => {
    setRosterMessage("Checking current MLB roster status…");
    try {
      const response = await fetch(
        "https://statsapi.mlb.com/api/v1/people/search?names=" +
          encodeURIComponent(goal.name) +
          "&hydrate=currentTeam",
      );
      if (!response.ok) throw Error();
      const body = await response.json();
      const matches = (body.people || []).filter(
        (p) =>
          normalizeSearchText(p.fullName) === normalizeSearchText(goal.name),
      );
      const mlbTeams = new Set(
        Object.entries(TEAM_LOGO_IDS)
          .filter(([code]) => code !== "MTY")
          .map(([, id]) => id),
      );
      const eligibleTeams = [];
      const statuses = await Promise.all(
        matches.slice(0, 5).map(async (p) => {
          if (!p.active) return `${p.fullName} (${p.id}): inactive`;
          if (!mlbTeams.has(p.currentTeam?.id))
            return `${p.fullName} (${p.id}): no current MLB team confirmed`;
          const rosterResponse = await fetch(
            `https://statsapi.mlb.com/api/v1/teams/${p.currentTeam.id}/roster?rosterType=active`,
          );
          if (!rosterResponse.ok) throw Error();
          const roster = await rosterResponse.json();
          const active = (roster.roster || []).some(
            (r) => r.person?.id === p.id,
          );
          if (active) eligibleTeams.push(p.currentTeam.id);
          return `${p.fullName} (${p.id}): ${p.currentTeam.name} · ${active ? "active MLB roster" : "not on active MLB roster"}`;
        }),
      );
      setRosters((old) => ({
        ...old,
        [goal.id]:
          statuses.join(" / ") || "No exact name match; status unverified",
      }));
      setRosterTeams((old) => ({ ...old, [goal.id]: eligibleTeams }));
      setRosterMessage(
        "Checked " +
          new Date().toLocaleDateString() +
          ". Name matches are shown separately. Roster membership does not confirm a game appearance.",
      );
    } catch {
      setRosterMessage(
        "Current roster status is unavailable. This goal remains unverified.",
      );
    }
  };
  const [schedule, setSchedule] = useState([]);
  const [endDate, setEndDate] = useState("");
  const [itinerary, saveItinerary, itineraryError] = usePersonal(
    "itinerary",
    [],
  );
  const progress = useMemo(
    () => ballparkGoalProgress(data, ALL_MLB_STADIUMS),
    [data],
  );
  const [goalFocus, setGoalFocus] = useState("all");
  const [withDad, setWithDad] = useState(true);
  const [onlyMatches, setOnlyMatches] = useState(true);
  const [scheduleLoaded, setScheduleLoaded] = useState(false);
  const [message, setMessage] = useState("");
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const loadSchedule = async () => {
    if (
      !date ||
      (endDate &&
        (endDate < date ||
          (Date.parse(endDate) - Date.parse(date)) / 86400000 > 31))
    ) {
      setMessage(
        "Choose a date range of up to 31 days, with the end on or after the start.",
      );
      return;
    }
    setSchedule([]);
    setScheduleLoaded(false);
    setMessage("Loading schedule…");
    try {
      const res = await fetch(
        `https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=${encodeURIComponent(date)}&endDate=${encodeURIComponent(endDate || date)}&hydrate=team,venue,probablePitcher`,
      );
      if (!res.ok) throw Error();
      const payload = await res.json();
      setSchedule((payload.dates || []).flatMap((d) => d.games || []));
      setScheduleLoaded(true);
      setMessage(
        payload.dates?.length
          ? "Schedule retrieved " +
              new Date().toLocaleString() +
              ". Roster matches are possibilities; probable pitchers can change."
          : "No MLB games are scheduled for this date.",
      );
    } catch {
      setMessage("Schedule unavailable. Your saved goals are still available.");
    }
  };
  const missingCandidates = [
    ...new Set(
      goals
        .filter((g) => g.kind === "collection")
        .flatMap(
          (g) =>
            (data.__collectionSets || []).find((s) => s.id === g.id)
              ?.nextMissing || [],
        ),
    ),
  ];
  const scheduleGoals = (game) =>
    goals
      .filter((goal) => {
        const teams = [game.teams.away.team, game.teams.home.team];
        if (goal.kind === "player")
          return teams.some((t) => (rosterTeams[goal.id] || []).includes(t.id));
        const text = normalizeSearchText(goal.name);
        if (goal.kind === "team")
          return teams.some(
            (t) =>
              normalizeSearchText(t.name) === text ||
              normalizeSearchText(t.abbreviation) === text ||
              normalizeSearchText(
                TEAM_CODE_TO_NAME[goal.name.toUpperCase()] || "",
              ) === normalizeSearchText(t.name),
          );
        if (goal.kind === "ballpark")
          return parkIdentity(game.venue?.name) === parkIdentity(goal.name);
        return false;
      })
      .map((g) => g.name);
  const matchedGoals = new Map(
    schedule.map((game) => [
      game.gamePk,
      ballparkScheduleMatches(game, progress, parkIdentity, withDad, goalFocus),
    ]),
  );
  const goalMatches = (game) => matchedGoals.get(game.gamePk) || [];
  const calculateReasons = (g) => {
    const reasons = [
      ...goalMatches(g).map((goal) => goal.title),
      ...scheduleGoals(g),
    ];
    const venue = data.stadiumAliases?.[g.venue?.name] || g.venue?.name;
    if (venue && !visited.has(parkIdentity(venue)))
      reasons.push("Potential new ballpark");
    for (const team of [g.teams.away.team, g.teams.home.team]) {
      const code = Object.keys(TEAM_LOGO_IDS).find(
        (c) => TEAM_LOGO_IDS[c] === team.id,
      );
      if (code && ![...seenTeams].some((t) => sameTeam(t, code, true)))
        reasons.push(`New franchise: ${team.name}`);
    }
    return [...new Set(reasons)];
  };
  const reasonsByGame = new Map(
    schedule.map((game) => [game.gamePk, calculateReasons(game)]),
  );
  const scheduleReasons = (game) => reasonsByGame.get(game.gamePk) || [];
  const rankedSchedule = [...schedule].sort(
    (a, b) =>
      goalMatches(b).length - goalMatches(a).length ||
      scheduleReasons(b).length - scheduleReasons(a).length ||
      a.gameDate.localeCompare(b.gameDate),
  );
  return (
    <div className="space-y-4">
      <section className="passport-panel">
        <h1 className="text-2xl font-bold">Your next ballpark visit</h1>
        <p className="mt-2 text-slate-500">
          Track the Orioles, the Orioles with Dad, and every ballpark with Dad.
        </p>
        <p className="mt-2 text-sm text-slate-500">
          Progress covers all years at the {progress[0].parks.length} current
          MLB home ballparks. Renamed parks count once. Dad goals use games
          tagged Dad in Companions; the Orioles-with-Dad goal requires both at
          the same game.
        </p>
      </section>
      <div className="grid lg:grid-cols-3 gap-4">
        {progress.map((goal) => (
          <BallparkGoalCard
            key={goal.id}
            goal={goal}
            onPlan={(selected) => {
              setGoalFocus(selected.id);
              if (selected.dad) setWithDad(true);
              document
                .getElementById("next-visit-schedule")
                ?.scrollIntoView({ behavior: "smooth", block: "start" });
            }}
          />
        ))}
      </div>
      <details className="passport-panel">
        <summary className="text-lg font-bold cursor-pointer">
          Other goals and watchlist
        </summary>
        <p className="text-sm text-slate-500">
          Pin collections, players, teams, or ballparks. Player goals stay
          “status unverified” until current roster information confirms
          eligibility; historical missing entries are not presented as
          attainable.
        </p>
        <div className="flex flex-wrap gap-2 mt-3">
          <select
            aria-label="Goal type"
            className="passport-input"
            value={kind}
            onChange={(e) => setKind(e.target.value)}
          >
            {["player", "team", "ballpark"].map((k) => (
              <option key={k}>{k}</option>
            ))}
          </select>
          <input
            aria-label="New goal"
            className="passport-input"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Player, team, or ballpark"
          />
          <button
            className="passport-button"
            disabled={!name.trim()}
            onClick={() => {
              save([
                ...goals,
                { id: crypto.randomUUID(), name: name.trim(), kind },
              ]);
              setName("");
            }}
          >
            Pin goal
          </button>
        </div>
        {goals.length ? (
          goals.map((g) => (
            <div
              key={g.id}
              className="flex items-center justify-between gap-3 border-b py-3"
            >
              <span>
                <strong>{g.name}</strong>
                <small className="block text-slate-500">
                  {g.kind === "player"
                    ? rosters[g.id] || "Roster status unverified"
                    : g.kind === "collection"
                      ? "Historical collection; some entries may be unattainable"
                      : g.kind}
                </small>
              </span>
              <span className="flex gap-2">
                {g.kind === "player" && (
                  <button
                    className="passport-button"
                    onClick={() => checkRoster(g)}
                  >
                    Check roster
                  </button>
                )}
                <button
                  className="passport-button"
                  onClick={() => save(goals.filter((x) => x.id !== g.id))}
                >
                  Unpin
                </button>
              </span>
            </div>
          ))
        ) : (
          <p className="mt-3 text-sm">
            Pin a goal here or in Collections to start planning.
          </p>
        )}
        <PassportNotice>{error || rosterMessage}</PassportNotice>
        {missingCandidates.length > 0 && (
          <div className="mt-4 border-t pt-4">
            <h2 className="font-bold">Missing from your pinned collections</h2>
            <p className="text-sm text-slate-500">
              A few missing entries to explore. Pin a player and check their
              current roster status before planning a visit.
            </p>
            <div className="flex flex-wrap gap-2 mt-2">
              {missingCandidates.map((candidate) => (
                <button
                  key={candidate}
                  className="passport-button"
                  disabled={goals.some(
                    (g) => g.kind === "player" && g.name === candidate,
                  )}
                  onClick={() =>
                    save([
                      ...goals,
                      {
                        id: crypto.randomUUID(),
                        name: candidate,
                        kind: "player",
                      },
                    ])
                  }
                >
                  Pin {candidate}
                </button>
              ))}
            </div>
          </div>
        )}
      </details>
      <section className="passport-panel" id="next-visit-schedule">
        <h2 className="text-lg font-bold">Find the most useful next visit</h2>
        <p className="text-sm text-slate-500">
          Games that fill your ballpark goals come first. Include Dad to find
          visits that move your shared goals forward. Planned games count only
          after they enter your attended-game archive.
        </p>
        <div className="flex flex-wrap items-center gap-3 mt-3">
          <label className="text-sm">
            Planning goal
            <select
              aria-label="Planning goal"
              className="passport-input block mt-1 max-w-full"
              value={goalFocus}
              onChange={(event) => {
                setGoalFocus(event.target.value);
                if (event.target.value.includes("dad")) setWithDad(true);
              }}
            >
              <option value="all">All three ballpark goals</option>
              {progress.map((goal) => (
                <option key={goal.id} value={goal.id}>
                  {goal.title}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <input
              type="checkbox"
              checked={withDad}
              onChange={(event) => {
                setWithDad(event.target.checked);
                if (!event.target.checked && goalFocus.includes("dad"))
                  setGoalFocus("all");
              }}
            />{" "}
            Planning with Dad
          </label>
        </div>
        <div className="flex flex-wrap gap-2 mt-2">
          <input
            type="date"
            aria-label="Planning date"
            className="passport-input"
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
          <input
            type="date"
            aria-label="Planning end date"
            className="passport-input"
            value={endDate}
            min={date}
            onChange={(e) => setEndDate(e.target.value)}
          />
          <label className="text-sm">
            <input
              type="checkbox"
              checked={onlyMatches}
              onChange={(e) => setOnlyMatches(e.target.checked)}
            />{" "}
            Goal matches only
          </label>
          <button className="passport-button" onClick={loadSchedule}>
            Find scheduled games
          </button>
        </div>
        <PassportNotice>{message}</PassportNotice>
        {scheduleLoaded &&
          onlyMatches &&
          !rankedSchedule.some(
            (game) =>
              goalMatches(game).length ||
              (goalFocus === "all" && scheduleGoals(game).length),
          ) && (
            <p className="mt-3" role="status">
              No games match your remaining goals in this date range. Try other
              dates or turn off Goal matches only.
            </p>
          )}
        {rankedSchedule
          .filter(
            (g) =>
              !onlyMatches ||
              goalMatches(g).length ||
              (goalFocus === "all" && scheduleGoals(g).length),
          )
          .map((g) => (
            <article key={g.gamePk} className="py-3 border-b">
              <strong>
                {g.officialDate || g.gameDate?.slice(0, 10)} ·{" "}
                {g.teams.away.team.name} @ {g.teams.home.team.name}
              </strong>
              <p className="text-sm">
                {scheduleReasons(g).length} matches:{" "}
                {scheduleReasons(g).join(" · ") || "No matches yet"}
              </p>
              <p className="text-sm text-slate-500">
                Probable pitchers:{" "}
                {g.teams.away.probablePitcher?.fullName || "TBD"} /{" "}
                {g.teams.home.probablePitcher?.fullName || "TBD"}
              </p>
              <button
                className="passport-button"
                disabled={itinerary.some((r) => r.gamePk === g.gamePk)}
                onClick={() =>
                  saveItinerary([
                    ...itinerary,
                    {
                      gamePk: g.gamePk,
                      gameDate: g.gameDate,
                      isTimeTBA: !!g.isTimeTBA,
                      withDad,
                      date: g.officialDate || g.gameDate.slice(0, 10),
                      matchup: `${g.teams.away.team.name} @ ${g.teams.home.team.name}`,
                      venue: g.venue?.name || "",
                    },
                  ])
                }
              >
                Add to itinerary
              </button>
              <p className="text-sm">
                {g.venue?.name} · {g.status?.detailedState}
                {!visited.has(parkIdentity(g.venue?.name))
                  ? " · Potential new ballpark"
                  : ""}
              </p>
              {scheduleGoals(g).length > 0 && (
                <p className="text-sm font-semibold text-blue-700 dark:text-blue-300">
                  Potential goal matches: {scheduleGoals(g).join(" · ")}
                </p>
              )}
              <a
                className="text-blue-600 text-sm"
                href={`https://www.mlb.com/gameday/${g.gamePk}`}
                target="_blank"
                rel="noopener noreferrer"
              >
                Schedule details ↗
              </a>
            </article>
          ))}
      </section>
      <section className="passport-panel space-y-3">
        <h2 className="text-lg font-bold">Planned itinerary</h2>
        <p className="text-sm text-slate-500">
          Saved privately on this device. Backups are available in Saved views.
          Calendar times follow the schedule as retrieved; check for later
          changes.
        </p>
        {itineraryError && <p role="status">{itineraryError}</p>}
        {[...itinerary]
          .sort((a, b) => a.date.localeCompare(b.date))
          .map((g) => (
            <div key={g.gamePk} className="flex justify-between gap-3">
              <span>
                {g.date} · {g.matchup} · {g.venue}
                {g.withDad ? " · With Dad" : ""}
              </span>
              <button
                className="passport-button"
                onClick={() =>
                  saveItinerary(itinerary.filter((r) => r.gamePk !== g.gamePk))
                }
              >
                Remove
              </button>
            </div>
          ))}
        <button
          className="passport-button"
          disabled={!itinerary.length}
          onClick={() =>
            downloadTextFile(
              calendarForGames(itinerary),
              "baseball-itinerary.ics",
              "text/calendar",
            )
          }
        >
          Export itinerary calendar
        </button>
      </section>
    </div>
  );
};
const PassportCompare = ({ data, route }) => {
  const [axis, setAxis] = useState("season");
  const [a, setA] = useState("");
  const [b, setB] = useState("");
  const companions = Object.values(data.companionData?.companions || {});
  const options =
    axis === "season"
      ? [...new Set(data.games.map((g) => toSortableDate(g.date).slice(0, 4)))]
          .sort()
          .reverse()
      : axis === "venue"
        ? [
            ...new Set(
              data.games.map((g) =>
                route.venueMode === "era" ? g.venue : g._venueKey || g.venue,
              ),
            ),
          ].sort()
        : companions.map((c) => c.name);
  const left = a || options[0],
    right = b || options[1] || options[0];
  const select = (value) => {
    const ids = new Set(
      companions.find((c) => c.name === value)?.games.map((g) => g.gameId) ||
        [],
    );
    return scopeGames(data.games, { type: route.type }).filter((g) =>
      axis === "season"
        ? toSortableDate(g.date).startsWith(value)
        : axis === "venue"
          ? (route.venueMode === "era" ? g.venue : g._venueKey || g.venue) ===
            value
          : ids.has(g.gameId),
    );
  };
  const l = passportMetrics(select(left)),
    r = passportMetrics(select(right));
  const metrics = [
    ["Games", l.games, r.games],
    ["Players seen", l.players, r.players],
    ["Ballparks", l.parks, r.parks],
    ["Home runs", l.totals.hr || 0, r.totals.hr || 0],
    [
      "HR per game",
      l.games ? ((l.totals.hr || 0) / l.games).toFixed(2) : "—",
      r.games ? ((r.totals.hr || 0) / r.games).toFixed(2) : "—",
    ],
    [
      "Average attendance",
      l.averageAttendance?.toLocaleString() || "—",
      r.averageAttendance?.toLocaleString() || "—",
    ],
    ["Attendance sample", l.attendanceCoverage, r.attendanceCoverage],
  ];
  return (
    <section className="passport-panel">
      <h1 className="text-2xl font-bold">Compare your visits</h1>
      <p className="text-sm text-slate-500">
        Matching game-type scope: {route.type || "All game types"}. Each sample
        is shown; totals are not adjusted for unequal attendance.
      </p>
      <div className="flex flex-wrap gap-2 my-4">
        <select
          aria-label="Compare by"
          className="passport-input"
          value={axis}
          onChange={(e) => {
            setAxis(e.target.value);
            setA("");
            setB("");
          }}
        >
          <option value="season">Season</option>
          <option value="venue">Ballpark</option>
          <option value="companion">Companion</option>
        </select>
        {[
          [left, setA, "First comparison"],
          [right, setB, "Second comparison"],
        ].map(([v, set, label]) => (
          <select
            key={label}
            aria-label={label}
            className="passport-input max-w-full"
            value={v || ""}
            onChange={(e) => set(e.target.value)}
          >
            {options.map((o) => (
              <option key={o}>{o}</option>
            ))}
          </select>
        ))}
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr>
            <th className="text-left p-2">Metric</th>
            <th>{left || "No sample"}</th>
            <th>{right || "No sample"}</th>
          </tr>
        </thead>
        <tbody>
          {metrics.map(([name, x, y]) => (
            <tr key={name} className="border-t">
              <th className="text-left p-3 font-medium">{name}</th>
              <td className="text-center tabular-nums">{x}</td>
              <td className="text-center tabular-nums">{y}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
};
const PassportHealth = ({ data }) => {
  const h = data.__health || {};
  return (
    <section className="passport-panel space-y-4">
      <h1 className="text-2xl font-bold">Data health</h1>
      <p className="text-sm">
        Built {data.generatedAt} · Schema {data.__schemaVersion}
      </p>
      <p className="text-sm text-slate-500">
        Coverage reports presence, not completeness. Missing measurements are
        not zero. Statcast availability varies by season and source.
      </p>
      <div className="grid sm:grid-cols-2 gap-3">
        {Object.entries(h.coverage || {}).map(([key, count]) => (
          <div key={key}>
            <strong>
              {
                {
                  pitchData: "Pitch measurements",
                  hitData: "Exit velocity measurements",
                  playByPlay: "Play-by-play",
                  lineups: "Starting lineups",
                  temperature: "Temperature",
                  attendance: "Attendance",
                }[key]
              }
            </strong>
            <p>
              {count} of {h.games} games ({Math.round((count / h.games) * 100)}
              %)
            </p>
          </div>
        ))}
      </div>
      <AnalysisHealthDetails data={data} />
      <h2 className="font-bold">Sources and refreshes</h2>
      {Object.entries(h.sources || {}).map(([s, n]) => (
        <p key={s}>
          {s}: {n} games
        </p>
      ))}
      {Object.entries(h.referenceRefreshes || {}).map(([s, d]) => (
        <p key={s}>
          {s === "awardChecklists" ? "Awards" : "All-Star rosters"}:{" "}
          {d || "Refresh timestamp unavailable"}
        </p>
      ))}
      <p>
        Batting identities using register or placeholder IDs:{" "}
        {h.unresolvedPlayers || 0}
      </p>
      <p className="text-sm">
        Updated game data:{" "}
        {h.corrections?.length
          ? `${h.corrections.length} game records changed since the previous build.`
          : "No changed game records recorded for this build."}{" "}
        Changes may reflect source corrections or newly available enrichment.
      </p>
      <details>
        <summary>Metric definitions</summary>
        <ul className="list-disc pl-5 text-sm">
          <li>
            Players seen: distinct identities across batting, pitching, and
            appearances without statistics.
          </li>
          <li>
            Game totals include the game types selected in Browse; cumulative
            achievement badges retain their documented regular-season/postseason
            scope.
          </li>
          <li>
            Game milestones, career events, and all-time movement are separate
            event categories.
          </li>
          <li>
            Attendance averages include only games with a positive recorded
            attendance.
          </li>
        </ul>
      </details>
    </section>
  );
};
const PassportBackup = () => {
  const [message, setMessage] = useState("");
  const backup = async () => {
    try {
      downloadPassport(
        {
          schemaVersion: 1,
          views: readPersonal("views", []),
          goals: readPersonal("goals", []),
          itinerary: readPersonal("itinerary", []),
          // Preserve legacy private data when exporting, without restoring its retired UI.
          journal: readPersonal("journal", {}),
          images: await photoStore("get"),
        },
        "my-baseball-passport-private-backup.json",
      );
      setMessage("Private backup exported.");
    } catch {
      setMessage("Could not export the backup. Please retry.");
    }
  };
  const importBackup = async (file) => {
    if (!file) return;
    try {
      const payload = validatePassportBackup(JSON.parse(await file.text()));
      for (const row of payload.images || []) {
        const existing = (await photoStore("get", row.gameId))?.images || [];
        await photoStore("put", row.gameId, [
          ...new Set([...existing, ...row.images]),
        ]);
      }
      if (payload.journal)
        localStorage.setItem(
          "passport:journal",
          JSON.stringify({
            ...payload.journal,
            ...readPersonal("journal", {}),
          }),
        );
      for (const key of ["views", "goals", "itinerary"]) {
        if (!payload[key]) continue;
        const identity = (row) =>
          key === "views"
            ? row.name
            : key === "itinerary"
              ? row.gamePk
              : row.id;
        const merged = [...readPersonal(key, []), ...payload[key]].filter(
          (row, i, rows) =>
            rows.findIndex((other) => identity(other) === identity(row)) === i,
        );
        localStorage.setItem("passport:" + key, JSON.stringify(merged));
      }
      window.dispatchEvent(new Event("passport-personal"));
      setMessage("Backup imported. Existing saved items were preserved.");
    } catch {
      setMessage(
        "Could not finish importing. Check the backup and available browser storage, then retry.",
      );
    }
  };
  return (
    <section className="passport-panel space-y-3">
      <h2 className="text-lg font-bold">Private backups</h2>
      <p className="text-sm text-slate-500">
        Keep a copy of your saved views, pinned goals and itinerary before
        changing devices.
      </p>
      <button className="passport-button" onClick={backup}>
        Export private backup
      </button>
      <label className="block text-sm">
        Import backup
        <input
          aria-label="Import backup"
          type="file"
          accept="application/json,.json"
          className="block mt-2 max-w-full"
          onChange={(event) => importBackup(event.target.files?.[0])}
        />
      </label>
      <PassportNotice>{message}</PassportNotice>
    </section>
  );
};

const PassportSaved = () => {
  const [views, save, error] = usePersonal("views", []);
  const [offline, setOffline] = usePersonal("offline", []);
  return (
    <section className="passport-panel">
      <h1 className="text-2xl font-bold">Saved views</h1>
      <p className="text-sm text-slate-500">
        Save your season, team, and ballpark filters from Browse. Back up your
        saved views, pinned goals and itinerary here.
      </p>
      {views.map((v) => (
        <div key={v.name} className="flex gap-2 justify-between border-b py-3">
          <button
            className="text-blue-600 text-left"
            onClick={() => {
              Object.entries(v.tables || {})
                .filter(([k]) => k.startsWith("dt_"))
                .forEach(([k, value]) => localStorage.setItem(k, value));
              navigatePassport({ ...v.route, player: null, game: null });
            }}
          >
            {v.name}
          </button>
          <button
            className="passport-button"
            onClick={() => save(views.filter((x) => x.name !== v.name))}
          >
            Remove
          </button>
        </div>
      ))}
      {!views.length && <p className="my-4">No saved views yet.</p>}
      <h2 className="text-lg font-bold mt-5">Offline recaps</h2>
      <p className="text-sm text-slate-500">
        Use Save offline inside a game recap to keep it on this device.
      </p>
      {offline.map((g) => (
        <div key={g.id} className="flex gap-2 justify-between border-b py-3">
          <button
            className="text-left text-blue-600"
            onClick={() =>
              navigatePassport({
                tab: "dashboard",
                subtab: null,
                game: g.id,
                player: null,
              })
            }
          >
            {g.label}
          </button>
          <button
            className="passport-button"
            onClick={async () => {
              await (
                await caches.open("passport-saved-games")
              ).delete(new URL(g.path, location.href));
              setOffline(offline.filter((x) => x.id !== g.id));
            }}
          >
            Remove copy
          </button>
        </div>
      ))}
      <PassportNotice>{error}</PassportNotice>
    </section>
  );
};
const PassportSearchPage = ({ data, route, onResult }) => {
  const [query, setQuery] = useState(route.q || "");
  useEffect(() => setQuery(route.q || ""), [route.q]);
  const results = passportSearch(data, route.q || "");
  const [type, setType] = useState("all");
  const filtered = results.filter((r) => type === "all" || r.type === type);
  const { page, setPage, totalPages, paginatedData, totalItems } =
    usePagination(filtered, 25);
  return (
    <section className="passport-panel">
      <h1 className="text-2xl font-bold">Search your passport</h1>
      <form
        className="flex gap-2 my-3"
        onSubmit={(e) => {
          e.preventDefault();
          navigatePassport({ q: query });
        }}
      >
        <input
          aria-label="Search query"
          className="passport-input flex-1 min-w-0"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button className="passport-button">Search</button>
      </form>
      <div className="flex flex-wrap gap-2">
        {["all", ...new Set(results.map((r) => r.type))].map((t) => (
          <button
            key={t}
            className="passport-button"
            aria-pressed={type === t}
            onClick={() => setType(t)}
          >
            {t} (
            {t === "all"
              ? results.length
              : results.filter((r) => r.type === t).length}
            )
          </button>
        ))}
      </div>
      <div className="divide-y">
        {paginatedData.map((r, i) => (
          <button
            key={i}
            className="w-full text-left py-3"
            onClick={() => onResult(r)}
          >
            <strong>{r.label}</strong>
            <span className="block text-sm text-slate-500">
              {r.type} · {r.sub}
            </span>
          </button>
        ))}
      </div>
      {!results.length && (
        <p className="my-4">
          No matches. Try a name, team, date, ballpark, or feature such as
          “splash hits.”
        </p>
      )}
      <PaginationControls
        {...{ page, setPage, totalPages, totalItems }}
        rowsPerPage={25}
      />
    </section>
  );
};
const PassportDashboard = ({ data, allData, route, onResult }) => {
  const tabs = [
    ["", "Overview"],
    ["recap", "Recap"],
    ["discover", "Discover"],
    ["collections", "Collections"],
    ["plan", "Next visit"],
    ["compare", "Compare"],
    ["saved", "Saved views"],
    ["health", "Data health"],
  ];
  const view = route.subtab === "journal" ? "plan" : route.subtab || "";
  useEffect(() => {
    if (route.subtab === "journal")
      navigatePassport(
        { subtab: "plan", journalGame: null },
        { replace: true },
      );
  }, [route.subtab]);
  return (
    <div className="space-y-4">
      <label className="block sm:hidden text-sm font-semibold no-print">
        Passport tools
        <select
          aria-label="Passport tools"
          className="passport-input w-full mt-1"
          value={view}
          onChange={(e) =>
            navigatePassport({
              tab: "dashboard",
              subtab: e.target.value || null,
              game: null,
              player: null,
            })
          }
        >
          {tabs.map(([id, label]) => (
            <option key={id} value={id}>
              {label}
            </option>
          ))}
          {view === "search" && <option value="search">Search results</option>}
          {view === "analysis" && (
            <option value="analysis">Detailed analysis</option>
          )}
        </select>
      </label>
      <nav
        aria-label="Passport tools"
        className="hidden sm:flex flex-wrap gap-2 no-print"
      >
        {tabs.map(([id, label]) => (
          <button
            key={id}
            className="passport-button"
            aria-current={view === id ? "page" : undefined}
            onClick={() =>
              navigatePassport({
                tab: "dashboard",
                subtab: id || null,
                game: null,
                player: null,
              })
            }
          >
            {label}
          </button>
        ))}
      </nav>
      {view === "" && <PassportHome {...{ data, allData, route }} />}
      {view === "recap" && <PassportRecap {...{ data, allData, route }} />}
      {view === "discover" && <AnalysisHub data={allData} route={route} />}
      {view === "collections" && <PassportCollections data={allData} />}{" "}
      {view === "plan" && <PassportPlanner data={allData} />}{" "}
      {view === "compare" && <PassportCompare data={allData} route={route} />}{" "}
      {view === "saved" && (
        <>
          <PassportSaved />
          <PassportBackup />
        </>
      )}{" "}
      {view === "health" && <PassportHealth data={allData} />}{" "}
      {view === "search" && (
        <PassportSearchPage data={allData} route={route} onResult={onResult} />
      )}{" "}
      {view === "analysis" && (
        <Dashboard
          data={data}
          onTabChange={(tab, subtab) => navigatePassport({ tab, subtab })}
        />
      )}
    </div>
  );
};
const PassportEntity = ({ route, data, onClose }) => {
  const [game, setGame] = useState(null),
    [error, setError] = useState(""),
    [retry, setRetry] = useState(0),
    [message, setMessage] = useState("");
  useEffect(() => {
    let live = true;
    setGame(null);
    setError("");
    if (route.game)
      window
        .loadPassportGame(route.game)
        .then((g) => {
          if (live) setGame(g);
        })
        .catch((e) => {
          if (live) setError(e.message);
        });
    return () => {
      live = false;
    };
  }, [route.game, retry]);
  const close = onClose || closePassportEntity;
  const orderedGames = scopeGames(data.games || [], route)
    .slice()
    .sort((a, b) =>
      toSortableDate(b.date).localeCompare(toSortableDate(a.date)),
    );
  const gameIndex = orderedGames.findIndex((g) => g.gameId === route.game);
  if (route.game) {
    if (!game)
      return (
        <Modal
          label="Game details"
          onClose={close}
          className="fixed inset-0 bg-black/50 flex items-center justify-center p-4"
        >
          <div className="passport-panel">
            <p role="status">{error || "Loading this game…"}</p>
            {error && (
              <button
                className="passport-button"
                onClick={() => setRetry(retry + 1)}
              >
                Retry game
              </button>
            )}
            <button className="passport-button" onClick={close}>
              Close
            </button>
          </div>
        </Modal>
      );
    return (
      <GameDetailsModal
        game={game}
        playerGames={game._detailPlayerGames || data.playerGames || []}
        pitcherGames={game._detailPitcherGames || data.pitcherGames || []}
        careerFirsts={
          game._detailCareerFirsts ||
          data.careerFirstsByGame?.[game.gameId] ||
          []
        }
        allTimePassings={
          game._detailPassings ||
          data.allTimePassingsByGame?.[game.gameId] ||
          []
        }
        debuts={(data.debuts || []).filter((d) => d.gameId === game.gameId)}
        finalGames={(data.finalGames || []).filter(
          (d) => d.gameId === game.gameId,
        )}
        onClose={close}
        onPrev={
          gameIndex > 0
            ? () =>
                navigatePassport(
                  { game: orderedGames[gameIndex - 1].gameId },
                  { replace: true },
                )
            : undefined
        }
        onNext={
          gameIndex >= 0 && gameIndex < orderedGames.length - 1
            ? () =>
                navigatePassport(
                  { game: orderedGames[gameIndex + 1].gameId },
                  { replace: true },
                )
            : undefined
        }
        gameIndex={gameIndex >= 0 ? gameIndex + 1 : undefined}
        totalGames={orderedGames.length}
        initialTab={route.detail}
        focusPlay={route.playIndex != null ? Number(route.playIndex) : null}
        focusInning={
          route.inning
            ? { inning: Number(route.inning), half: route.half || "top" }
            : null
        }
      />
    );
  }
  const p = [
    ...(data.players || []),
    ...(data.pitchers || []),
    ...(data.playersWithoutStats || []),
  ].find((p) => p.playerId === route.player);
  const isPitcher = !(data.players || []).some(
    (p) => p.playerId === route.player,
  );
  const Timeline = isPitcher ? PitcherTimeline : PlayerTimeline;
  return (
    <Modal
      label={p?.name || "Player profile"}
      onClose={close}
      className="fixed inset-0 bg-black/50 flex items-center justify-center p-4"
    >
      <div className="passport-panel w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between gap-4 mb-4">
          <h2 className="text-xl font-bold">
            {p?.name || "Player unavailable"}
          </h2>
          <button data-dialog-close className="passport-button" onClick={close}>
            Close profile
          </button>
        </div>
        {p ? (
          <>
            <button
              className="passport-button mb-3"
              onClick={() => {
                const goals = readPersonal("goals", []);
                if (!goals.some((g) => g.id === p.playerId)) {
                  try {
                    localStorage.setItem(
                      "passport:goals",
                      JSON.stringify([
                        ...goals,
                        { id: p.playerId, name: p.name, kind: "player" },
                      ]),
                    );
                    setMessage("Player pinned in Next visit.");
                  } catch {
                    setMessage("Could not save this goal.");
                  }
                } else setMessage("This player is already pinned.");
              }}
            >
              Pin player
            </button>
            <PassportNotice>{message}</PassportNotice>
            <p className="text-sm text-slate-500 mb-3">
              Career visits in this archive. Timeline totals exclude spring
              training.
            </p>
            <Timeline
              playerId={p.playerId}
              playerName={p.name}
              playerGames={data.playerGames || []}
              pitcherGames={data.pitcherGames || []}
              careerMilestones={data.careerFirstsByPlayer?.[p.playerId] || []}
              allTimePassings={(data.allTimePassings || []).filter(
                (x) => x.player_id === p.playerId,
              )}
              gameMilestones={(data.milestones || []).filter(
                (x) => x.playerId === p.playerId,
              )}
              debuts={(data.debuts || []).filter(
                (d) => d.playerId === p.playerId,
              )}
              finalGames={(data.finalGames || []).filter(
                (d) => d.playerId === p.playerId,
              )}
              onGameClick={requestGameDetails}
            />
          </>
        ) : (
          <p>This identity is not available in the current archive.</p>
        )}
      </div>
    </Modal>
  );
};
const TableSortControls = ({
  columns,
  sortKey,
  sortDir,
  setSortKey,
  setSortDir,
}) => (
  <div className="flex flex-wrap items-center gap-2 px-4 py-2">
    <label className="text-sm">
      Sort by{" "}
      <select
        aria-label="Sort by"
        className="passport-input"
        value={sortKey || ""}
        onChange={(e) => setSortKey(e.target.value)}
      >
        {columns.map((c) => (
          <option key={c.key} value={c.key}>
            {c.label}
          </option>
        ))}
      </select>
    </label>
    <button
      className="passport-button"
      aria-label="Change sort direction"
      onClick={() => setSortDir(sortDir === "asc" ? "desc" : "asc")}
    >
      {sortDir === "asc" ? "Ascending ↑" : "Descending ↓"}
    </button>
  </div>
);
const StatDefinition = ({ label }) => (
  <abbr
    title={
      {
        PA: "Plate appearances",
        AB: "At bats",
        AVG: "Batting average",
        OBP: "On-base percentage",
        SLG: "Slugging percentage",
        OPS: "On-base plus slugging",
        IP: "Innings pitched: digits after the decimal represent outs",
        ERA: "Earned run average",
        WHIP: "Walks plus hits per inning pitched",
        WPA: "Win probability added",
        HR: "Home runs",
        RBI: "Runs batted in",
        SB: "Stolen bases",
        SO: "Strikeouts",
        K: "Strikeouts",
        BB: "Walks",
        G: "Games",
        HP: "Home plate",
      }[label] || label
    }
  >
    {label}
  </abbr>
);
