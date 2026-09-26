const RECORD_CATEGORIES = {
  games: "Games",
  batting: "Batting",
  pitching: "Pitching",
  ballpark: "Ballpark",
};
const recordValue = (record, value) => {
  if (record.format === "duration")
    return `${Math.floor(value / 60)}h ${value % 60}m`;
  if (record.format === "clock")
    return `${Math.floor(value / 60) % 12 || 12}:${String(value % 60).padStart(2, "0")} ${value >= 720 ? "PM" : "AM"}`;
  if (record.format === "outs") return formatOutsAsIP(value);
  if (record.format === "wpa")
    return `${value > 0 ? "+" : ""}${value.toFixed(3)}`;
  return value.toLocaleString("en-US", { maximumFractionDigits: 3 });
};
const recordScopeGames = (games, route) =>
  (games || []).filter((g) => {
    const preset = route.recordScope || "all";
    const orioles = ["orioles", "orioles-dad"].includes(preset);
    const dad = ["dad", "orioles-dad"].includes(preset);
    const type = route.recordType || "mlb";
    return (
      (type === "mlb" ? g.gameType !== "spring" : g.gameType === type) &&
      (!orioles || [g.homeTeam, g.awayTeam].includes("BAL")) &&
      (!dad ||
        (g._companions || []).some((n) => normalizeSearchText(n) === "dad")) &&
      (!route.recordYear ||
        toSortableDate(g.date).startsWith(route.recordYear)) &&
      (!route.recordTeam ||
        [g.homeTeam, g.awayTeam].includes(route.recordTeam)) &&
      (!route.recordVenue || (g._venueKey || g.venue) === route.recordVenue) &&
      (!route.recordCompanion ||
        (g._companions || []).includes(route.recordCompanion))
    );
  });
const recordChronology = (game) => {
  const start = String(game.startTime || "").match(
    /(\d{1,2}):(\d{2})\s*([ap])\.?m/i,
  );
  const minutes = start
    ? (Number(start[1]) % 12) * 60 +
      Number(start[2]) +
      (start[3].toLowerCase() === "p" ? 720 : 0)
    : 0;
  return `${toSortableDate(game.date)}:${String(minutes).padStart(4, "0")}:${game.gameId}`;
};
const recordHolderLabel = (row) =>
  row.holder && [row.game.homeTeam, row.game.awayTeam].includes(row.holder)
    ? `${row.holder} vs ${row.holder === row.game.homeTeam ? row.game.awayTeam : row.game.homeTeam}`
    : row.holder || `${row.game.awayTeam} at ${row.game.homeTeam}`;
const recordHolderText = (row) =>
  normalizeSearchText(
    [
      row.holder,
      row.team,
      row.detail,
      row.game.date,
      row.game.venue,
      row.game.homeTeam,
      row.game.awayTeam,
    ].join(" "),
  );
const rankRecordBook = (definitions, games, scoped = false) => {
  const gameMap = new Map(games.map((g) => [g.gameId, g]));
  return (definitions || [])
    .filter((r) => !scoped || r.coverage !== "holders-only")
    .flatMap((record) => {
      const candidates = record.candidates
        .filter((r) => gameMap.has(r.gameId))
        .map((r) => ({ ...r, game: gameMap.get(r.gameId) }));
      if (!candidates.length) return [];
      const direction = record.direction === "min" ? 1 : -1;
      const chronological = (a, b) =>
        recordChronology(a.game).localeCompare(recordChronology(b.game));
      const ranked = [...candidates].sort(
        (a, b) =>
          direction * (a.value - b.value) ||
          chronological(b, a) ||
          a.holder.localeCompare(b.holder),
      );
      let previous, rank;
      ranked.forEach((row, i) => {
        if (row.value !== previous) rank = i + 1;
        row.rank = rank;
        previous = row.value;
      });
      const holders = ranked.filter((r) => r.rank === 1);
      const history = [];
      let best;
      const byGame = new Map();
      [...candidates].sort(chronological).forEach((row) => {
        if (!byGame.has(row.gameId)) byGame.set(row.gameId, []);
        byGame.get(row.gameId).push(row);
      });
      if (record.coverage !== "holders-only")
        byGame.forEach((rows) => {
          const value = rows.reduce(
            (v, r) => (direction * (r.value - v) < 0 ? r.value : v),
            rows[0].value,
          );
          const type =
            best === undefined
              ? "First witnessed"
              : direction * (value - best) < 0
                ? "New record"
                : value === best
                  ? "Tied record"
                  : null;
          if (type) {
            history.push({
              type,
              value,
              previous: best,
              game: rows[0].game,
              holders: rows.filter((r) => r.value === value),
            });
            best = value;
          }
        });
      return [
        {
          ...record,
          value: ranked[0].value,
          holders,
          ranked,
          history,
          coverageCount: byGame.size,
          latestDate: holders[0].game.date,
          firstDate: holders.at(-1).game.date,
        },
      ];
    });
};
const recordHasScope = (route) =>
  ["recordYear", "recordTeam", "recordVenue", "recordCompanion"].some(
    (k) => route[k],
  ) ||
  (route.recordScope && route.recordScope !== "all") ||
  (route.recordType && route.recordType !== "mlb");
const recordScopeLabel = (route) =>
  (({
    all: "All attended games",
    orioles: "Orioles games",
    dad: "Games with Dad",
    "orioles-dad": "Orioles games with Dad",
  })[route.recordScope || "all"] || "Selected games") +
  [route.recordYear, route.recordTeam, route.recordVenue, route.recordCompanion]
    .filter(Boolean)
    .map((v) => ` · ${v}`)
    .join("");

const RecordHolder = ({ row, record, showRank = false }) => (
  <article className="flex items-start justify-between gap-3 border-b border-slate-100 py-3 last:border-0">
    <div className="min-w-0">
      <p className="font-semibold text-slate-900">
        {showRank && (
          <span className="mr-2 text-sm text-slate-500">#{row.rank}</span>
        )}
        {recordHolderLabel(row)}
        {row.playerId && row.team && (
          <span className="ml-2 text-xs font-normal text-slate-500">
            {row.team}
          </span>
        )}
      </p>
      <p className="mt-1 text-sm text-slate-600">
        {row.game.date} ·{" "}
        {row.game.score || `${row.game.awayTeam} at ${row.game.homeTeam}`}
      </p>
      <p className="mt-1 text-xs text-slate-500">{row.game.venue}</p>
      {row.detail && (
        <p className="mt-1 text-xs text-slate-500">{row.detail}</p>
      )}
    </div>
    <div className="shrink-0 text-right">
      {showRank && (
        <p className="mb-1 font-semibold tabular-nums">
          {recordValue(record, row.value)}{" "}
          <span className="text-xs font-normal text-slate-500">
            {record.unit}
          </span>
        </p>
      )}
      <SpecialGameButton gameId={row.gameId} />
    </div>
  </article>
);
const RecordBookDialog = ({ record, scopeLabel, gameCount, onClose }) => {
  const [view, setView] = useState("holders");
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(12);
  const [copied, setCopied] = useState("");
  const full = record.coverage !== "holders-only";
  const rows = (
    view === "rankings"
      ? record.ranked.filter((r) => r.rank <= 5)
      : record.holders
  ).filter((r) => recordHolderText(r).includes(normalizeSearchText(query)));
  const history = [...record.history]
    .reverse()
    .filter((e) =>
      normalizeSearchText(
        `${e.game.date} ${e.game.venue} ${e.holders.map((r) => r.holder).join(" ")}`,
      ).includes(normalizeSearchText(query)),
    );
  const next = record.ranked.find((r) => r.value !== record.value);
  const gap = next ? Math.abs(record.value - next.value) : null;
  return (
    <Modal
      label={record.label}
      onClose={onClose}
      className="fixed inset-0 flex items-center justify-center bg-black/50 p-3 sm:p-6"
    >
      <section className="flex max-h-[88vh] w-full max-w-3xl flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl">
        <header className="border-b border-slate-200 p-4 sm:p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {RECORD_CATEGORIES[record.category]} · {scopeLabel}
              </p>
              <h2 className="mt-1 text-xl font-bold text-slate-900">
                {record.label}
              </h2>
              <p className="mt-2 text-3xl font-bold tabular-nums text-blue-700">
                {recordValue(record, record.value)}{" "}
                <span className="text-sm font-normal text-slate-500">
                  {record.unit}
                </span>
              </p>
            </div>
            <button
              data-dialog-close
              onClick={onClose}
              className="passport-button"
            >
              Close
            </button>
          </div>
          <p className="mt-2 text-sm text-slate-600">
            {record.holders.length}{" "}
            {record.holders.length === 1
              ? "record holder"
              : "tied record holders"}{" "}
            ·{" "}
            {full
              ? `Based on ${record.coverageCount} of ${gameCount} games in this scope`
              : "Historical record; full WPA game data is unavailable"}
          </p>
          {record.format === "wpa" && (
            <p className="mt-2 text-sm text-slate-500">
              {(record.value * 100).toFixed(1)} percentage points of win
              probability added.
            </p>
          )}
          <div
            className="mt-3 flex flex-wrap gap-2"
            role="group"
            aria-label="Record details views"
          >
            {[
              ["holders", "Record holders"],
              ...(full
                ? [
                    ["rankings", "Top five"],
                    ["history", "Record history"],
                  ]
                : []),
            ].map(([key, label]) => (
              <button
                key={key}
                className="passport-button"
                aria-pressed={view === key}
                onClick={() => {
                  setView(key);
                  setLimit(12);
                }}
              >
                {label}
              </button>
            ))}
            <button
              className="passport-button"
              onClick={async () => {
                try {
                  await navigator.clipboard.writeText(location.href);
                  setCopied("Link copied");
                } catch {
                  setCopied("Copy the address from your browser");
                }
              }}
            >
              Copy record link
            </button>
          </div>
          {copied && (
            <p role="status" className="mt-2 text-xs">
              {copied}
            </p>
          )}
        </header>
        <div className="overflow-y-auto p-4 sm:p-5">
          <label className="block text-sm font-semibold text-slate-700">
            Find a related game
            <input
              type="search"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setLimit(12);
              }}
              placeholder="Player, team, ballpark, or date"
              className="passport-input mt-1 w-full"
            />
          </label>
          {view === "rankings" && (
            <p className="mt-3 text-sm text-slate-500">
              Top five places, including ties.
              {gap !== null
                ? ` The next distinct mark is ${record.format === "clock" || record.format === "duration" ? `${gap} minutes` : `${recordValue(record, gap)} ${record.unit}`} ${record.direction === "min" ? "higher" : "lower"}.`
                : ""}
            </p>
          )}
          {view === "history" ? (
            <div className="mt-2">
              {history.slice(0, limit).map((e) => (
                <section
                  key={e.game.gameId}
                  className="mt-4 border-l-2 border-blue-200 pl-3"
                >
                  <p className="text-sm font-semibold text-blue-700">
                    {e.type} · {recordValue(record, e.value)} {record.unit}
                  </p>
                  {e.previous !== undefined && e.previous !== e.value && (
                    <p className="text-xs text-slate-500">
                      Previous best: {recordValue(record, e.previous)}{" "}
                      {record.unit}
                    </p>
                  )}
                  {e.holders.map((row, i) => (
                    <RecordHolder key={i} {...{ row, record }} />
                  ))}
                </section>
              ))}
            </div>
          ) : (
            <div className="mt-2">
              {rows.slice(0, limit).map((row, i) => (
                <RecordHolder
                  key={`${row.gameId}:${row.playerId || row.holder}:${i}`}
                  {...{ row, record }}
                  showRank={view === "rankings"}
                />
              ))}
            </div>
          )}
          {(view === "history" ? history.length : rows.length) === 0 && (
            <p role="status" className="py-5 text-sm text-slate-500">
              No related games match this search.
            </p>
          )}
          {(view === "history" ? history.length : rows.length) > limit && (
            <button
              className="passport-button mt-3 w-full"
              onClick={() => setLimit((n) => n + 12)}
            >
              Show more
            </button>
          )}
        </div>
      </section>
    </Modal>
  );
};
const PersonalRecords = ({ data }) => {
  const route = usePassportRoute();
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [order, setOrder] = useState("featured");
  const scopedGames = useMemo(
    () => recordScopeGames(data.games, route),
    [
      data.games,
      route.recordScope,
      route.recordYear,
      route.recordTeam,
      route.recordVenue,
      route.recordCompanion,
      route.recordType,
    ],
  );
  const scoped = recordHasScope(route);
  const book = useMemo(
    () => rankRecordBook(data.recordBook, scopedGames, scoped),
    [data.recordBook, scopedGames, scoped],
  );
  const query = normalizeSearchText(search);
  const rows = book.filter(
    (r) =>
      (category === "all" || r.category === category) &&
      (!query ||
        normalizeSearchText(`${r.label} ${recordValue(r, r.value)}`).includes(
          query,
        ) ||
        r.holders.some((h) => recordHolderText(h).includes(query))),
  );
  const ordered = [...rows].sort((a, b) =>
    order === "az"
      ? a.label.localeCompare(b.label)
      : order === "recent"
        ? toSortableDate(b.latestDate).localeCompare(
            toSortableDate(a.latestDate),
          )
        : order === "oldest"
          ? toSortableDate(a.firstDate).localeCompare(
              toSortableDate(b.firstDate),
            )
          : 0,
  );
  const selected = book.find((r) => r.id === route.record);
  const latest = book
    .flatMap((record) =>
      record.history
        .filter((e) => e.type !== "First witnessed")
        .map((event) => ({ record, event })),
    )
    .sort(
      (a, b) =>
        toSortableDate(b.event.game.date).localeCompare(
          toSortableDate(a.event.game.date),
        ) ||
        Number(b.event.type === "New record") -
          Number(a.event.type === "New record") ||
        a.record.label.localeCompare(b.record.label),
    )[0];
  const changeScope = (patch) =>
    navigatePassport(
      { ...patch, record: null },
      { replace: true, preserveScroll: true },
    );
  const resetScope = () =>
    changeScope({
      recordScope: null,
      recordYear: null,
      recordTeam: null,
      recordVenue: null,
      recordCompanion: null,
      recordType: null,
    });
  const openRecord = (r) =>
    navigatePassport({ record: r.id }, { preserveScroll: true });
  const closeRecord = () =>
    history.state?.passportParent
      ? history.back()
      : navigatePassport(
          { record: null },
          { replace: true, preserveScroll: true },
        );
  const filterOptions = {
    recordYear: [
      ...new Set(
        (data.games || []).map((g) => toSortableDate(g.date).slice(0, 4)),
      ),
    ]
      .sort()
      .reverse(),
    recordTeam: [
      ...new Set((data.games || []).flatMap((g) => [g.homeTeam, g.awayTeam])),
    ].sort(),
    recordVenue: [
      ...new Set(
        (data.games || []).map((g) => g._venueKey || g.venue).filter(Boolean),
      ),
    ].sort(),
    recordCompanion: [
      ...new Set((data.games || []).flatMap((g) => g._companions || [])),
    ].sort(),
  };
  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">
            Personal records
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            {scopedGames.length} games ·{" "}
            {route.recordType === "spring"
              ? "Spring training"
              : route.recordType === "regular"
                ? "Regular season"
                : route.recordType === "postseason"
                  ? "Postseason"
                  : "Regular season + postseason"}{" "}
            · {recordScopeLabel(route)}
          </p>
        </div>
      </header>
      {latest && !search && category === "all" && order === "featured" && (
        <button
          onClick={() => openRecord(latest.record)}
          className="flex w-full flex-wrap items-center gap-x-3 gap-y-1 rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-left text-sm"
        >
          <span className="font-semibold text-blue-700">
            {latest.event.type} · {latest.event.game.date}
          </span>
          <span className="text-slate-700">
            {latest.record.label}:{" "}
            <strong>
              {recordValue(latest.record, latest.event.value)}{" "}
              {latest.record.unit}
            </strong>
          </span>
          <span className="ml-auto text-blue-700" aria-hidden="true">
            →
          </span>
        </button>
      )}
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-[minmax(0,1fr)_13rem_11rem]">
          <label className="col-span-2 text-xs font-semibold text-slate-600 sm:col-span-1">
            Search records
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Record, player, team, ballpark, or year"
              className="passport-input mt-1 w-full"
            />
          </label>
          <label className="text-xs font-semibold text-slate-600">
            Records for
            <select
              aria-label="Records for"
              value={route.recordScope || "all"}
              onChange={(e) => changeScope({ recordScope: e.target.value })}
              className="passport-input mt-1 w-full"
            >
              <option value="all">All games</option>
              <option value="orioles">Orioles games</option>
              <option value="dad">With Dad</option>
              <option value="orioles-dad">Orioles with Dad</option>
            </select>
          </label>
          <label className="text-xs font-semibold text-slate-600">
            Record order
            <select
              aria-label="Record order"
              value={order}
              onChange={(e) => setOrder(e.target.value)}
              className="passport-input mt-1 w-full"
            >
              <option value="featured">Recommended</option>
              <option value="recent">Most recent</option>
              <option value="oldest">First witnessed</option>
              <option value="az">A–Z</option>
            </select>
          </label>
        </div>
        <div className="relative">
          <details className="text-sm">
            <summary className="min-h-11 cursor-pointer py-3 pr-36 font-medium text-slate-600">
              More filters{scoped ? " · filters active" : ""}
            </summary>
            <div className="mt-2 grid gap-3 sm:grid-cols-3">
              {[
                ["recordYear", "Season"],
                ["recordTeam", "Team"],
                ["recordVenue", "Ballpark"],
                ["recordCompanion", "Companion"],
              ].map(([key, label]) => (
                <label
                  key={key}
                  className="text-xs font-semibold text-slate-600"
                >
                  {label}
                  <select
                    aria-label={label}
                    value={route[key] || ""}
                    onChange={(e) =>
                      changeScope({ [key]: e.target.value || null })
                    }
                    className="passport-input mt-1 w-full"
                  >
                    <option value="">All {label.toLowerCase()}s</option>
                    {filterOptions[key].map((v) => (
                      <option key={v}>{v}</option>
                    ))}
                  </select>
                </label>
              ))}
              <label className="text-xs font-semibold text-slate-600">
                Game type
                <select
                  aria-label="Record game type"
                  value={route.recordType || "mlb"}
                  onChange={(e) => changeScope({ recordType: e.target.value })}
                  className="passport-input mt-1 w-full"
                >
                  <option value="mlb">Regular + postseason</option>
                  <option value="regular">Regular season</option>
                  <option value="postseason">Postseason</option>
                  <option value="spring">Spring training</option>
                </select>
              </label>
            </div>
          </details>
          {scoped && (
            <button
              className="absolute right-0 top-0 min-h-11 text-sm font-semibold text-blue-700"
              onClick={resetScope}
            >
              Reset game filters
            </button>
          )}
        </div>
        <div
          className="flex flex-wrap items-center gap-2"
          role="group"
          aria-label="Record category"
        >
          {[["all", "All"], ...Object.entries(RECORD_CATEGORIES)].map(
            ([key, label]) => (
              <button
                key={key}
                onClick={() => setCategory(key)}
                aria-pressed={category === key}
                className={`min-h-11 rounded-lg px-3 text-sm font-semibold ${category === key ? "bg-blue-600 text-white" : "bg-white text-slate-600 border border-slate-200"}`}
              >
                {label}
              </button>
            ),
          )}
          <span
            role="status"
            className="sr-only text-xs text-slate-500 sm:not-sr-only sm:ml-auto"
          >
            {rows.length} records
          </span>
        </div>
        {(search || category !== "all") && (
          <button
            className="text-sm font-semibold text-blue-700 min-h-11"
            onClick={() => {
              setSearch("");
              setCategory("all");
            }}
          >
            Clear search and category
          </button>
        )}
      </div>
      {route.record && !selected && (
        <p role="status" className="rounded-lg bg-slate-100 p-4 text-sm">
          This record has no data in the selected games.{" "}
          <button
            className="text-blue-700 underline"
            onClick={() =>
              navigatePassport({ record: null }, { replace: true })
            }
          >
            Return to records
          </button>
        </p>
      )}
      {rows.length ? (
        <div data-testid="record-results" className="space-y-5">
          {(category === "all" && order === "featured" && !search
            ? Object.keys(RECORD_CATEGORIES)
            : ["results"]
          ).map((group) => {
            const groupRows =
              group === "results"
                ? ordered
                : ordered.filter((r) => r.category === group);
            if (!groupRows.length) return null;
            return (
              <section
                key={group}
                aria-label={RECORD_CATEGORIES[group] || "Matching records"}
              >
                {group !== "results" && (
                  <h3 className="mb-2 text-sm font-bold text-slate-700">
                    {RECORD_CATEGORIES[group]}
                  </h3>
                )}
                <div className="overflow-hidden rounded-xl border border-slate-200 bg-white divide-y divide-slate-100">
                  {groupRows.map((record) => {
                    const holder =
                      (query &&
                        record.holders.find((h) =>
                          recordHolderText(h).includes(query),
                        )) ||
                      record.holders[0];
                    return (
                      <article key={record.id} aria-label={record.label}>
                        <button
                          onClick={() => openRecord(record)}
                          aria-label={`${record.label}: ${recordValue(record, record.value)}. Explore record`}
                          aria-haspopup="dialog"
                          className="grid w-full grid-cols-[5.5rem_minmax(0,1fr)_1rem] items-center gap-3 px-4 py-4 text-left hover:bg-slate-50 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-500 sm:grid-cols-[8rem_minmax(0,1fr)_1rem]"
                        >
                          <span className="min-w-0">
                            <strong className="block text-xl font-bold tabular-nums tracking-tight text-slate-900 sm:text-2xl">
                              {recordValue(record, record.value)}
                            </strong>
                            <span className="text-xs text-slate-500">
                              {record.unit}
                            </span>
                          </span>
                          <span className="min-w-0">
                            <span className="block font-semibold text-slate-900">
                              {record.label}
                            </span>
                            <span className="mt-1 block text-sm text-slate-600">
                              {recordHolderLabel(holder)}
                              {record.holders.length > 1
                                ? ` · ${record.holders.length} tied holders`
                                : ""}
                            </span>
                            <span className="mt-1 block text-xs text-slate-500">
                              {holder.game.date} · {holder.game.venue}
                            </span>
                          </span>
                          <span aria-hidden="true" className="text-blue-600">
                            →
                          </span>
                        </button>
                      </article>
                    );
                  })}
                </div>
              </section>
            );
          })}
        </div>
      ) : (
        <p
          role="status"
          className="rounded-xl border border-dashed border-slate-300 p-6 text-center text-slate-600"
        >
          {scopedGames.length
            ? "No records match these filters."
            : "No games match these filters."}
        </p>
      )}
      {scoped &&
        data.recordBook?.some((r) => r.coverage === "holders-only") && (
          <p className="text-xs text-slate-500">
            The historical WPA record is available under All games; its full
            game history is not available to recalculate for filters.
          </p>
        )}
      <footer className="flex flex-wrap gap-4 text-sm">
        <a className="text-blue-700 underline" href="#milestones/counts">
          Milestone counts
        </a>
        <a className="text-blue-700 underline" href="#dashboard/totals">
          Lifetime totals & averages
        </a>
      </footer>
      {selected && (
        <RecordBookDialog
          key={selected.id}
          record={selected}
          scopeLabel={recordScopeLabel(route)}
          gameCount={scopedGames.length}
          onClose={closeRecord}
        />
      )}
    </div>
  );
};
const ArchiveSummaries = ({ data, kind }) => {
  const [selected, setSelected] = useState(null);
  const [search, setSearch] = useState("");
  const records = buildSpecialRecordBook(data).filter(
    (r) =>
      r.kind === kind && r.searchText.includes(normalizeSearchText(search)),
  );
  return (
    <section className="space-y-4">
      <header>
        <h2 className="text-2xl font-bold text-slate-900">
          {kind === "summary"
            ? "Lifetime totals & averages"
            : "Milestone counts"}
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Regular season and postseason. Counts distinguish performances, games,
          and events.
        </p>
      </header>
      <label className="block text-sm font-semibold">
        Find a statistic
        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="passport-input mt-1 w-full"
        />
      </label>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {records.map((record) => (
          <SpecialRecordCard
            key={record.record}
            record={record}
            onSelect={setSelected}
          />
        ))}
      </div>
      {!records.length && <p>No statistics match this search.</p>}
      {selected && (
        <SpecialRecordDialog
          record={selected}
          games={data.games || []}
          onClose={() => setSelected(null)}
        />
      )}
    </section>
  );
};
