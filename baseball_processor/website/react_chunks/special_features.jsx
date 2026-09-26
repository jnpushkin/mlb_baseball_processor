const SPECIAL_HIDDEN_RECORDS = new Set([
  "Hits Leaders",
  "Runs Leaders",
  "Home Run Leaders",
  "RBI Leaders",
  "Doubles Leaders",
  "Triples Leaders",
  "Stolen Base Leaders",
  "Walks Leaders (Hitting)",
  "Batting Average Leaders (min. 10 AB)",
  "On-Base Percentage Leaders (min. 10 AB)",
  "OPS Leaders (min. 10 AB)",
  "Wins Leaders",
  "Strikeout Leaders (Pitching)",
  "Save Leaders",
  "Innings Pitched Leaders",
  "ERA Leaders (min. 10 IP)",
  "Career WPA Leaders (Top 3)",
  "Day Games vs Night Games",
  "Weekend vs Weekday Games",
  "Percent of Possible Matchups Seen",
]);

const SPECIAL_RECORD_SECTIONS = {
  "Total Hits Across All Games": "cumulative",
  "Total Home Runs Across All Games": "cumulative",
  "Total Runs Across All Games": "cumulative",
  "Total Strikeouts Across All Games": "cumulative",
  "Total Stolen Bases Across All Games": "cumulative",
  "Back-to-Back HR Events": "rare",
  "Back-to-Back-to-Back HR Events": "rare",
  "Back-to-Back-to-Back-to-Back HR Events": "rare",
  "Inside-the-Park Home Runs": "rare",
  Cycles: "rare",
  "No-Hitters": "rare",
  "Biggest Victory": "extremes",
  "Biggest Comeback": "extremes",
  "Most Combined Runs": "extremes",
  "Most Runs by One Team": "extremes",
  "Most Runs in a Single Inning": "extremes",
  "Longest Game by Innings": "environment",
  "Longest Game by Time": "environment",
  "Shortest Game by Time": "environment",
  "Most Combined HRs": "extremes",
  "Most Combined Triples": "extremes",
  "Most HRs by One Team": "extremes",
  "Both Teams 10+ Runs": "extremes",
  "Coldest Game": "environment",
  "Hottest Game": "environment",
  "Average Temperature": "environment",
  "Highest Attendance": "environment",
  "Lowest Attendance": "environment",
  "Average Attendance": "environment",
  "Earliest Start Time": "environment",
  "Latest Start Time": "environment",
  "Highest Wind Speed": "environment",
  "Average Wind Speed": "environment",
  "Games with Precipitation": "environment",
  "Most Hits by One Team": "individual-hitting",
  "Most Combined Hits": "extremes",
  "Fewest Hits by One Team": "individual-hitting",
  "Fewest Combined Hits": "extremes",
  "Most RBIs in a Game": "individual-hitting",
  "Most SBs by One Player": "individual-hitting",
  "Most SBs by One Team": "individual-hitting",
  "Most Combined SBs in a Game": "extremes",
  "Most Walks by One Team": "individual-pitching",
  "Most Walks Issued by One Team": "individual-pitching",
  "Most Combined Walks": "extremes",
  "Fewest Combined Walks": "extremes",
  "20+ Hit Games by One Team": "individual-hitting",
  "4+ Hit Games": "milestone-counts",
  "5+ RBI Games": "milestone-counts",
  "Multi-HR Games": "milestone-counts",
  "Most Clutch Single Game (WPA)": "individual-hitting",
  "Most Pitching Strikeouts by One Team": "individual-pitching",
  "Most Combined Pitching Strikeouts": "extremes",
  "Fewest Combined Strikeouts": "extremes",
  "Most Pitches by One Pitcher": "individual-pitching",
  "Most Pitchers Used": "individual-pitching",
  "Fewest Pitchers Used": "individual-pitching",
  "10+ K Games": "milestone-counts",
  "Complete Games": "milestone-counts",
  Shutouts: "milestone-counts",
  "Quality Starts": "milestone-counts",
  "1-Run Games": "game-counts",
  "1-0 Games": "game-counts",
  "Extra Inning Games": "game-counts",
  "10+ Run Innings": "game-counts",
  "Unique Players with a Hit": "coverage",
  "Unique Players with a Home Run": "coverage",
  "Unique Pitchers with a Win": "coverage",
  "Unique Pitchers with a Loss": "coverage",
  "Unique Pitchers with a Save": "coverage",
  "Most Teams Seen for a Player": "coverage",
  "Players with RISP Opportunities": "coverage",
  "Players with Bases Loaded Opportunities": "coverage",
};

const SPECIAL_RECORD_LABELS = {
  rare: "Rare moments",
  extremes: "Game extremes",
  "individual-hitting": "Hitting",
  "individual-pitching": "Pitching",
  environment: "At the ballpark",
  "game-counts": "Game counts",
  "milestone-counts": "Performance counts",
  coverage: "Player coverage",
  cumulative: "Totals witnessed",
};
const specialRecords = (data) =>
  (data.summary || [])
    .filter((r) => !SPECIAL_HIDDEN_RECORDS.has(r.record))
    .map((r) => ({
      ...r,
      section: SPECIAL_RECORD_SECTIONS[r.record] || "coverage",
    }));
const specialRecordGames = (record, games) => {
  const ids = new Set(
    String(record.gameIds || "")
      .split(",")
      .map((id) => id.trim())
      .filter(Boolean),
  );
  return games
    .filter((g) => ids.has(g.gameId))
    .sort((a, b) =>
      toSortableDate(b.date).localeCompare(toSortableDate(a.date)),
    );
};
const SPECIAL_RECORD_VIEWS = {
  records: {
    label: "Records",
    description:
      "The biggest, smallest, longest, and shortest games you have witnessed.",
  },
  occurrences: {
    label: "Milestone counts",
    description:
      "How often you have seen a rare event or standout performance. One game can contain multiple performances.",
  },
  summary: {
    label: "Totals & averages",
    description:
      "The bigger picture across your archive. Cumulative statistics exclude spring training.",
  },
  all: {
    label: "Everything",
    description:
      "Every record, milestone count, and archive summary in one place.",
  },
};
const specialRecordKind = (record) => {
  if (
    ["coverage", "cumulative"].includes(record.section) ||
    record.record.startsWith("Average ")
  )
    return "summary";
  if (
    ["rare", "game-counts", "milestone-counts"].includes(record.section) ||
    [
      "Both Teams 10+ Runs",
      "20+ Hit Games by One Team",
      "Games with Precipitation",
    ].includes(record.record)
  )
    return "occurrences";
  return "records";
};
const specialRecordMetric = (record) => {
  const name = record.record;
  const raw = String(record.value ?? "");
  if (
    ["Longest Game by Time", "Shortest Game by Time"].includes(name) &&
    /^\d+:\d{2}$/.test(raw)
  ) {
    const [hours, minutes] = raw.split(":").map(Number);
    return { value: `${hours}h ${minutes}m`, unit: "game time" };
  }
  // Format counts without touching times, temperatures, decimal WPA or other units.
  const value = /^\d[\d,]*$/.test(raw)
    ? Number(raw.replaceAll(",", "")).toLocaleString("en-US")
    : raw;
  let unit = "";
  if (name.includes("Attendance")) unit = "fans";
  else if (name.includes("by Innings")) unit = "innings";
  else if (name.includes("WPA")) unit = "win probability added";
  else if (name === "Most Pitches by One Pitcher") unit = "pitches";
  else if (name.includes("Pitchers Used")) unit = "pitchers";
  else if (name.includes("Start Time")) unit = "local start";
  else if (name.includes("HR Events")) unit = "sequences";
  else if (record.section === "milestone-counts") unit = "performances";
  else if (specialRecordKind(record) === "occurrences")
    unit = name === "Inside-the-Park Home Runs" ? "home runs" : "games";
  else if (name.startsWith("Unique Pitchers")) unit = "pitchers";
  else if (name.startsWith("Unique Players") || name.startsWith("Players with"))
    unit = "players";
  else if (name === "Most Teams Seen for a Player") unit = "teams";
  else if (/Strikeouts/.test(name)) unit = "strikeouts";
  else if (/Walks/.test(name)) unit = "walks";
  else if (/Triples/.test(name)) unit = "triples";
  else if (/Hits/.test(name)) unit = "hits";
  else if (/SBs|Stolen Bases/.test(name)) unit = "stolen bases";
  else if (/RBIs/.test(name)) unit = "RBI";
  else if (/HRs|Home Runs/.test(name)) unit = "home runs";
  else if (/Runs|Victory/.test(name)) unit = "runs";
  if (/\bruns\b/i.test(raw)) unit = "";
  return { value, unit };
};
const buildSpecialRecordBook = (data) =>
  specialRecords(data).map((record) => {
    const linkedGames = specialRecordGames(record, data.games || []);
    return {
      ...record,
      kind: specialRecordKind(record),
      metric: specialRecordMetric(record),
      linkedGames,
      firstDate: linkedGames.at(-1)?.date || "",
      latestDate: linkedGames[0]?.date || "",
      searchText: normalizeSearchText(
        [
          record.record,
          record.value,
          record.detail,
          SPECIAL_RECORD_LABELS[record.section],
          ...linkedGames.map(
            (g) =>
              `${g.awayTeam} ${g.homeTeam} ${g.venue} ${g.date} ${toSortableDate(g.date).slice(0, 4)}`,
          ),
        ].join(" "),
      ),
    };
  });
const SPECIAL_RECORD_PRIORITY = [
  "Biggest Comeback",
  "Most Combined Runs",
  "Biggest Victory",
  "Most Runs in a Single Inning",
  "Most RBIs in a Game",
  "Most Clutch Single Game (WPA)",
  "Most Pitches by One Pitcher",
  "Longest Game by Time",
  "Shortest Game by Time",
];
const sortSpecialRecords = (records, order = "featured") =>
  [...records].sort((a, b) => {
    if (order === "recent") {
      const result = toSortableDate(b.latestDate).localeCompare(
        toSortableDate(a.latestDate),
      );
      if (result) return result;
    } else if (order === "oldest") {
      const result = (toSortableDate(a.firstDate) || "99999999").localeCompare(
        toSortableDate(b.firstDate) || "99999999",
      );
      if (result) return result;
    } else if (order === "featured") {
      const priority = (r) => {
        const index = SPECIAL_RECORD_PRIORITY.indexOf(r.record);
        return index < 0 ? 100 : index;
      };
      const result = priority(a) - priority(b);
      if (result) return result;
    }
    return a.record.localeCompare(b.record);
  });
const SPECIAL_MOMENT_TYPES = {
  debut: { label: "MLB debut", plural: "Debuts", view: "debuts" },
  final: { label: "Final MLB game", plural: "Final games", view: "finals" },
  homer: {
    label: "Landmark home run",
    plural: "Signature HRs",
    view: "splash",
  },
};
const buildSpecialMoments = (data) => {
  const games = new Map((data.games || []).map((g) => [g.gameId, g]));
  const seen = new Set();
  return [
    ["debut", data.debuts],
    ["final", data.finalGames],
    ["homer", data.signatureHRs],
  ]
    .flatMap(([kind, rows]) =>
      (rows || []).map((row) => {
        const game = games.get(row.gameId);
        return {
          ...row,
          kind,
          game,
          date: row.date || game?.date || "",
          id: [
            kind,
            row.gameId,
            row.playerId || row.player,
            row.signatureNumber || "",
          ].join("|"),
        };
      }),
    )
    .filter((row) => {
      if (seen.has(row.id)) return false;
      seen.add(row.id);
      return true;
    })
    .sort(
      (a, b) =>
        toSortableDate(b.date).localeCompare(toSortableDate(a.date)) ||
        a.id.localeCompare(b.id),
    );
};

const SpecialHeader = ({ eyebrow, title, children }) => (
  <header className="rounded-xl border border-slate-200 bg-gradient-to-r from-blue-50 to-indigo-50 p-5 sm:p-6">
    <p className="text-xs font-semibold uppercase tracking-widest text-blue-700">
      {eyebrow}
    </p>
    <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-900">
      {title}
    </h2>
    <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-600">
      {children}
    </p>
  </header>
);
const SpecialGameButton = ({ gameId, children = "Open game", onOpen }) =>
  gameId ? (
    <button
      className="inline-flex min-h-11 items-center justify-center rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-blue-700 hover:bg-blue-50 focus-visible:ring-2 focus-visible:ring-blue-500"
      onClick={() => {
        onOpen?.();
        requestGameDetails(gameId);
      }}
    >
      {children}{" "}
      <span aria-hidden="true" className="ml-2">
        ↗
      </span>
    </button>
  ) : null;
const SpecialRecordDialog = ({ record, games, onClose }) => {
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(12);
  const linkedGames = record.linkedGames || specialRecordGames(record, games);
  const metric = record.metric || specialRecordMetric(record);
  const matching = linkedGames.filter((g) =>
    normalizeSearchText(
      `${g.awayTeam} ${g.homeTeam} ${g.date} ${g.venue} ${g.score}`,
    ).includes(normalizeSearchText(query)),
  );
  const notes = String(record.detail || "")
    .split(";")
    .map((s) => s.trim())
    .filter(Boolean);
  return (
    <Modal
      label={record.record}
      onClose={onClose}
      className="fixed inset-0 flex items-center justify-center bg-black/50 p-3 sm:p-6"
    >
      <div className="flex max-h-[85vh] w-full max-w-2xl flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl">
        <div className="flex items-start justify-between gap-4 border-b border-slate-200 p-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              {SPECIAL_RECORD_LABELS[record.section]}
            </p>
            <h3 className="mt-1 text-xl font-bold text-slate-900">
              {record.record}
            </h3>
            <p className="mt-3 text-3xl font-bold tabular-nums text-blue-700">
              {metric.value}{" "}
              <span className="text-sm font-medium text-slate-500">
                {metric.unit}
              </span>
            </p>
            {specialRecordKind(record) === "records" &&
              linkedGames.length > 1 && (
                <p className="mt-2 text-sm text-slate-500">
                  Shared by {linkedGames.length} games · first witnessed{" "}
                  {linkedGames.at(-1).date}
                </p>
              )}
          </div>
          <button
            data-dialog-close
            onClick={onClose}
            aria-label="Close record details"
            className="min-h-11 rounded-lg border px-3 text-sm font-semibold"
          >
            Close
          </button>
        </div>
        <div className="space-y-5 overflow-y-auto p-5">
          {notes.length > 0 && notes.length <= 4 && (
            <div className="rounded-lg bg-slate-50 p-4">
              <h4 className="mb-2 text-sm font-semibold text-slate-900">
                Record notes
              </h4>
              <ul className="space-y-2 text-sm leading-relaxed text-slate-600">
                {notes.map((note, i) => (
                  <li key={i}>{note}</li>
                ))}
              </ul>
            </div>
          )}
          {linkedGames.length > 0 ? (
            <section aria-label="Games behind this record">
              <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
                <h4 className="font-semibold text-slate-900">
                  Games behind this record · {linkedGames.length}
                </h4>
                <span className="text-xs text-slate-500">Newest first</span>
              </div>
              {linkedGames.length > 1 && (
                <label className="mb-4 block text-sm font-semibold text-slate-700">
                  Find a related game
                  <input
                    type="search"
                    value={query}
                    onChange={(e) => {
                      setQuery(e.target.value);
                      setLimit(12);
                    }}
                    placeholder="Team, ballpark, or date"
                    className="mt-1 block min-h-11 w-full rounded-lg border border-slate-300 px-3 font-normal"
                  />
                </label>
              )}
              <div className="space-y-3">
                {matching.slice(0, limit).map((game) => (
                  <article
                    key={game.gameId}
                    className="flex flex-col justify-between gap-3 rounded-lg border border-slate-200 p-4 sm:flex-row sm:items-center"
                  >
                    <div className="min-w-0">
                      <p className="text-xs text-slate-500">
                        {game.date}
                        {game.gameType === "spring"
                          ? " · Spring training"
                          : game.gameType === "postseason"
                            ? " · Postseason"
                            : ""}
                      </p>
                      <p className="mt-1 text-base font-bold text-slate-900">
                        {game.score || `${game.awayTeam} at ${game.homeTeam}`}
                      </p>
                      <p className="mt-1 text-sm text-slate-500">
                        {game.venue}
                      </p>
                    </div>
                    <SpecialGameButton gameId={game.gameId} onOpen={onClose} />
                  </article>
                ))}
              </div>
              {matching.length === 0 && (
                <p role="status" className="py-4 text-sm text-slate-500">
                  No related games match this search.
                </p>
              )}
              {matching.length > limit && (
                <button
                  onClick={() => setLimit((n) => n + 12)}
                  className="mt-4 min-h-11 w-full rounded-lg border border-slate-200 px-3 text-sm font-semibold text-blue-700"
                >
                  Show more games ({matching.length - limit} remaining)
                </button>
              )}
              {linkedGames.length > 1 && (
                <p role="status" className="mt-3 text-xs text-slate-500">
                  Showing {Math.min(limit, matching.length)} of{" "}
                  {matching.length} matching games
                </p>
              )}
            </section>
          ) : (
            <p className="text-sm text-slate-500">
              An archive summary across your attended games.
            </p>
          )}
          {notes.length > 4 && (
            <details className="rounded-lg border border-slate-200 p-4">
              <summary className="cursor-pointer text-sm font-semibold text-slate-700">
                Record notes ({notes.length})
              </summary>
              <ul className="mt-3 space-y-3 text-sm leading-relaxed text-slate-600">
                {notes.map((note, i) => (
                  <li key={i}>{note}</li>
                ))}
              </ul>
            </details>
          )}
        </div>
      </div>
    </Modal>
  );
};
const SpecialRecordCard = ({ record, onSelect }) => {
  const metric = record.metric || specialRecordMetric(record);
  const linkedGames = record.linkedGames || [];
  const latest = linkedGames[0];
  const canExplore = linkedGames.length > 0;
  const content = (
    <>
      <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {SPECIAL_RECORD_LABELS[record.section]}
      </span>
      <span className="mt-3 block text-base font-semibold leading-snug text-slate-900">
        {record.record}
      </span>
      <span className="mt-3 block text-3xl font-bold tracking-tight tabular-nums text-slate-900">
        {metric.value}
        <span className="ml-2 text-sm font-normal tracking-normal text-slate-500">
          {metric.unit}
        </span>
      </span>
      {record.detail && (
        <span
          className={`mt-3 block text-sm leading-relaxed text-slate-600 ${canExplore ? "line-clamp-2" : ""}`}
        >
          {record.detail}
        </span>
      )}
      {latest && (
        <span className="mt-4 block border-t border-slate-100 pt-3">
          <span className="block text-xs font-medium text-blue-700">
            {linkedGames.length > 1
              ? specialRecordKind(record) === "records"
                ? `Shared by ${linkedGames.length} games · latest`
                : `${linkedGames.length} linked games · latest`
              : "Witnessed on"}{" "}
            {latest.date}
          </span>
          <span className="mt-1 block text-sm font-semibold text-slate-700">
            {latest.awayTeam} at {latest.homeTeam}
          </span>
          <span className="mt-1 block text-xs text-slate-500">
            {latest.venue}
          </span>
        </span>
      )}
      {canExplore && (
        <span className="mt-4 block text-sm font-semibold text-blue-700">
          Explore{" "}
          {linkedGames.length === 1 ? "game" : `${linkedGames.length} games`}{" "}
          <span aria-hidden="true">→</span>
        </span>
      )}
    </>
  );
  return (
    <article
      aria-label={record.record}
      className="h-full min-w-0 overflow-hidden rounded-xl border border-slate-200 bg-white"
    >
      {canExplore ? (
        <button
          onClick={() => onSelect(record)}
          aria-haspopup="dialog"
          aria-label={`${record.record}: ${record.value}. Explore record`}
          className="block h-full w-full p-5 text-left transition hover:bg-slate-50 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-500"
        >
          {content}
        </button>
      ) : (
        <div className="p-5">{content}</div>
      )}
    </article>
  );
};
const PersonalRecords = ({ data }) => {
  const [search, setSearch] = useState("");
  const [section, setSection] = useState("all");
  const [view, setView] = useState("records");
  const [order, setOrder] = useState("featured");
  const [selected, setSelected] = useState(null);
  const records = useMemo(
    () => buildSpecialRecordBook(data),
    [data.summary, data.games],
  );
  const inView = records.filter((r) => view === "all" || r.kind === view);
  const filtered = sortSpecialRecords(
    inView.filter(
      (r) =>
        (section === "all" || r.section === section) &&
        r.searchText.includes(normalizeSearchText(search)),
    ),
    order,
  );
  const latestRecord = sortSpecialRecords(
    records.filter((r) => r.kind === "records" && r.linkedGames.length),
    "recent",
  )[0];
  const spotlight =
    latestRecord &&
    view === "records" &&
    section === "all" &&
    !search &&
    order === "featured";
  const grouped = section === "all" && !search && order === "featured";
  const sections = grouped
    ? Object.entries(SPECIAL_RECORD_LABELS)
        .map(([key, label]) => ({
          key,
          label,
          rows: filtered.filter((r) => r.section === key),
        }))
        .filter((s) => s.rows.length)
    : [{ key: "results", label: null, rows: filtered }];
  const reset = () => {
    setSearch("");
    setSection("all");
    setView("records");
    setOrder("featured");
  };
  return (
    <div className="space-y-5">
      <SpecialHeader
        eyebrow="The games that set the bar"
        title="Personal Record Book"
      >
        Your biggest scores, standout performances, and ballpark extremes—with
        the games that made them memorable.
      </SpecialHeader>
      <div
        className="grid grid-cols-2 gap-2 lg:grid-cols-4"
        role="group"
        aria-label="Record views"
      >
        {Object.entries(SPECIAL_RECORD_VIEWS).map(([key, item]) => {
          const count = records.filter(
            (r) => key === "all" || r.kind === key,
          ).length;
          return (
            <button
              key={key}
              aria-pressed={view === key}
              onClick={() => {
                setView(key);
                setSection("all");
              }}
              className={`flex min-h-14 items-center justify-between gap-2 rounded-xl border px-4 py-3 text-left text-sm font-semibold focus-visible:ring-2 focus-visible:ring-blue-500 ${view === key ? "border-blue-300 bg-blue-50 text-blue-700" : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"}`}
            >
              {item.label}
              <span className="text-xs tabular-nums">{count}</span>
            </button>
          );
        })}
      </div>
      {spotlight && (
        <section
          aria-label="Latest game in the record book"
          className="overflow-hidden rounded-xl border border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50 p-5 sm:p-6"
        >
          <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-center">
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">
                Latest game in the record book · {latestRecord.latestDate}
              </p>
              <h3 className="mt-2 text-xl font-bold text-slate-900">
                {latestRecord.record}
              </h3>
              <p className="mt-2 text-4xl font-bold tracking-tight text-blue-700">
                {latestRecord.metric.value}
                <span className="ml-2 text-sm font-medium tracking-normal text-slate-500">
                  {latestRecord.metric.unit}
                </span>
              </p>
              <p className="mt-3 text-sm font-semibold text-slate-700">
                {latestRecord.linkedGames[0].score ||
                  `${latestRecord.linkedGames[0].awayTeam} at ${latestRecord.linkedGames[0].homeTeam}`}
              </p>
              <p className="mt-1 text-sm text-slate-500">
                {latestRecord.linkedGames[0].venue}
                {latestRecord.linkedGames.length > 1
                  ? ` · One of ${latestRecord.linkedGames.length} games sharing this record`
                  : ""}
              </p>
            </div>
            <div className="flex shrink-0 flex-wrap gap-2 sm:flex-col">
              <SpecialGameButton gameId={latestRecord.linkedGames[0].gameId}>
                Revisit this game
              </SpecialGameButton>
              <button
                onClick={() => setSelected(latestRecord)}
                className="min-h-11 rounded-lg px-3 text-sm font-semibold text-blue-700 hover:bg-blue-50"
              >
                View record details →
              </button>
            </div>
          </div>
        </section>
      )}
      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-[minmax(0,1fr)_13rem_13rem]">
          <label className="text-sm font-semibold text-slate-700 sm:col-span-2 lg:col-span-1">
            Search records
            <input
              className="mt-1 block min-h-11 w-full rounded-lg border border-slate-300 px-3 font-normal"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                if (e.target.value) setView("all");
              }}
              placeholder="Record, player, team, ballpark, or year"
              type="search"
            />
          </label>
          <label className="text-sm font-semibold text-slate-700">
            Record category
            <select
              className="mt-1 block min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 font-normal"
              value={section}
              aria-label="Record category"
              onChange={(e) => setSection(e.target.value)}
            >
              <option value="all">All categories</option>
              {Object.entries(SPECIAL_RECORD_LABELS).map(([key, label]) => {
                const count = inView.filter((r) => r.section === key).length;
                return count ? (
                  <option key={key} value={key}>
                    {label} ({count})
                  </option>
                ) : null;
              })}
            </select>
          </label>
          <label className="text-sm font-semibold text-slate-700">
            Record order
            <select
              className="mt-1 block min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 font-normal"
              value={order}
              aria-label="Record order"
              onChange={(e) => setOrder(e.target.value)}
            >
              <option value="featured">Recommended</option>
              <option value="recent">Most recently witnessed</option>
              <option value="oldest">First witnessed</option>
              <option value="az">A–Z</option>
            </select>
          </label>
        </div>
        <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
          <p className="max-w-3xl text-sm text-slate-500">
            {search
              ? view === "all"
                ? "Searching across all entry types. Category and ordering still apply."
                : `Searching within ${SPECIAL_RECORD_VIEWS[view].label.toLowerCase()}.`
              : SPECIAL_RECORD_VIEWS[view].description}
          </p>
          {(search ||
            section !== "all" ||
            view !== "records" ||
            order !== "featured") && (
            <button
              onClick={reset}
              className="min-h-11 rounded-lg px-3 text-sm font-semibold text-blue-700 hover:bg-blue-50"
            >
              Clear filters
            </button>
          )}
        </div>
      </div>
      <p role="status" className="text-sm text-slate-500">
        {filtered.length} {view === "records" ? "records" : "entries"} ·{" "}
        {records.length} entries in your archive
      </p>
      {filtered.length ? (
        <div data-testid="record-results" className="space-y-7">
          {sections.map((group) => (
            <section
              key={group.key}
              aria-label={group.label || "Matching records"}
            >
              {group.label && (
                <h3 className="mb-3 flex items-center gap-3 text-lg font-bold text-slate-900">
                  {group.label}
                  <span className="text-sm font-normal text-slate-400">
                    {group.rows.length}
                  </span>
                </h3>
              )}
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
                {group.rows.map((record) => (
                  <SpecialRecordCard
                    key={record.record}
                    record={record}
                    onSelect={setSelected}
                  />
                ))}
              </div>
            </section>
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-slate-600">
          {records.length
            ? "No records match these filters."
            : "Records will appear here when game summaries are available."}
        </div>
      )}
      {selected && (
        <SpecialRecordDialog
          record={selected}
          games={data.games || []}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
};
const SpecialMomentCard = ({ moment }) => {
  const type = SPECIAL_MOMENT_TYPES[moment.kind];
  return (
    <article
      aria-label={`${type.label}: ${moment.player}`}
      className="rounded-xl border border-slate-200 bg-white p-4 sm:p-5"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">
            {type.label}
          </p>
          <h3 className="mt-2 text-lg font-bold text-slate-900">
            <PlayerLink playerId={moment.playerId} name={moment.player} />
          </h3>
          <p className="mt-1 text-sm text-slate-500">
            {moment.date} ·{" "}
            {moment.game
              ? `${moment.game.awayTeam} at ${moment.game.homeTeam}`
              : moment.team}
          </p>
          {moment.game?.venue && (
            <p className="mt-1 text-sm text-slate-500">{moment.game.venue}</p>
          )}
        </div>
        <SpecialGameButton gameId={moment.gameId} />
      </div>
      <div className="mt-4 border-t border-slate-100 pt-3 text-sm text-slate-700">
        {moment.kind === "homer" ? (
          <div className="flex flex-wrap items-center gap-3">
            <SignatureHRBadge label={moment.signatureNumber} />
            {moment.pitcher && <span>Off {moment.pitcher}</span>}
          </div>
        ) : (
          <DebutPerformance r={moment} />
        )}
      </div>
    </article>
  );
};
const SpecialHighlights = ({ data, onView }) => {
  const [selected, setSelected] = useState(null);
  const [kind, setKind] = useState("all");
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(12);
  const moments = useMemo(
    () => buildSpecialMoments(data),
    [data.debuts, data.finalGames, data.signatureHRs, data.games],
  );
  const records = useMemo(
    () => buildSpecialRecordBook(data),
    [data.summary, data.games],
  );
  const featured = [
    "Biggest Comeback",
    "Most Combined Runs",
    "Inside-the-Park Home Runs",
  ]
    .map((name) => records.find((r) => r.record === name))
    .filter(Boolean);
  const matching = moments.filter(
    (m) =>
      (kind === "all" || m.kind === kind) &&
      normalizeSearchText(
        `${m.player} ${m.team || ""} ${m.game?.awayTeam || ""} ${m.game?.homeTeam || ""} ${m.game?.venue || ""} ${m.signatureNumber || ""} ${m.date}`,
      ).includes(normalizeSearchText(query)),
  );
  const latest = moments[0];
  const latestGroup = latest
    ? moments.filter(
        (m) => m.kind === latest.kind && m.gameId === latest.gameId,
      )
    : [];
  const visits = new Set(moments.map((m) => m.gameId).filter(Boolean)).size;
  return (
    <div className="space-y-7">
      <SpecialHeader
        eyebrow="Special · witnessed history"
        title="The games that stay with you"
      >
        Career beginnings and endings. Home runs with a destination. Records
        that make a visit stand apart. Explore the moments across your lifetime
        archive.
      </SpecialHeader>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {[
          {
            label: "Record book",
            value: records.length,
            view: "records",
            detail: "Explore personal extremes",
          },
          ...Object.entries(SPECIAL_MOMENT_TYPES).map(([key, t]) => ({
            label: t.plural,
            value: moments.filter((m) => m.kind === key).length,
            view: t.view,
            detail:
              key === "debut"
                ? "There for the first game"
                : key === "final"
                  ? "There for the last appearance"
                  : "Home runs to iconic places",
          })),
        ].map((item) => (
          <button
            key={item.view}
            onClick={() => onView(item.view)}
            className="rounded-xl border border-slate-200 bg-white p-4 text-left hover:border-blue-300 focus-visible:ring-2 focus-visible:ring-blue-500"
          >
            <span className="block text-2xl font-bold tabular-nums text-slate-900">
              {item.value}
            </span>
            <span className="mt-1 block text-sm font-semibold text-slate-900">
              {item.label} <span aria-hidden="true">→</span>
            </span>
            <span className="mt-1 block text-xs leading-relaxed text-slate-500">
              {item.detail}
            </span>
          </button>
        ))}
      </div>
      {latest && (
        <section
          aria-label="Latest special visit"
          className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6"
        >
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">
                Latest special visit · {latest.date}
              </p>
              <h3 className="mt-2 text-xl font-bold text-slate-900">
                {latest.kind === "debut"
                  ? "There at the beginning"
                  : latest.kind === "final"
                    ? "A final appearance"
                    : "A home run to remember"}
              </h3>
              <div className="mt-2 flex flex-wrap gap-x-4 gap-y-2 text-base font-semibold">
                {latestGroup.map((m) => (
                  <PlayerLink
                    key={m.id}
                    playerId={m.playerId}
                    name={m.player}
                  />
                ))}
              </div>
              <p className="mt-2 text-sm text-slate-500">
                {latest.game
                  ? `${latest.game.awayTeam} at ${latest.game.homeTeam} · ${latest.game.venue}`
                  : latest.team}
              </p>
            </div>
            <SpecialGameButton gameId={latest.gameId}>
              Revisit this game
            </SpecialGameButton>
          </div>
        </section>
      )}
      {featured.length > 0 && (
        <section aria-labelledby="special-record-heading">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h3
              id="special-record-heading"
              className="text-lg font-bold text-slate-900"
            >
              A few personal extremes
            </h3>
            <button
              onClick={() => onView("records")}
              className="min-h-11 px-2 text-sm font-semibold text-blue-700"
            >
              Explore all records →
            </button>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {featured.map((r) => (
              <SpecialRecordCard
                key={r.record}
                record={r}
                onSelect={setSelected}
              />
            ))}
          </div>
        </section>
      )}
      <section aria-labelledby="special-timeline-heading" className="space-y-4">
        <div>
          <h3
            id="special-timeline-heading"
            className="text-xl font-bold text-slate-900"
          >
            Your witnessed history
          </h3>
          <p className="mt-1 text-sm text-slate-500">
            {moments.length} moments across {visits} games · newest first
          </p>
        </div>
        <div className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 sm:flex-row">
          <label className="flex-1 text-sm font-semibold text-slate-700">
            Find a moment
            <input
              type="search"
              placeholder="Player, team, ballpark, or date"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setLimit(12);
              }}
              className="mt-1 block min-h-11 w-full rounded-lg border border-slate-300 px-3 font-normal"
            />
          </label>
          <label className="text-sm font-semibold text-slate-700">
            Moment type
            <select
              aria-label="Moment type"
              value={kind}
              onChange={(e) => {
                setKind(e.target.value);
                setLimit(12);
              }}
              className="mt-1 block min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 font-normal sm:w-52"
            >
              <option value="all">All moments</option>
              {Object.entries(SPECIAL_MOMENT_TYPES).map(([key, t]) => (
                <option key={key} value={key}>
                  {t.plural}
                </option>
              ))}
            </select>
          </label>
        </div>
        <p role="status" className="text-sm text-slate-500">
          {matching.length} {matching.length === 1 ? "moment" : "moments"}
          {query || kind !== "all" ? " matching your filters" : ""}
        </p>
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          {matching.slice(0, limit).map((moment) => (
            <SpecialMomentCard key={moment.id} moment={moment} />
          ))}
        </div>
        {!matching.length && (
          <div className="rounded-xl border border-dashed border-slate-300 p-6 text-center text-slate-600">
            <p>
              {moments.length
                ? "No moments match these filters."
                : "Debuts, final appearances, and landmark home runs will appear here as your archive grows."}
            </p>
            {(query || kind !== "all") && (
              <button
                onClick={() => {
                  setQuery("");
                  setKind("all");
                  setLimit(12);
                }}
                className="mt-3 min-h-11 rounded-lg border bg-white px-4 font-semibold text-blue-700"
              >
                Clear moment filters
              </button>
            )}
          </div>
        )}
        {matching.length > limit && (
          <button
            onClick={() => setLimit((n) => n + 12)}
            className="min-h-11 w-full rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-blue-700"
          >
            Show more moments ({matching.length - limit} remaining)
          </button>
        )}
        <p className="text-xs leading-relaxed text-slate-500">
          Final appearances reflect the final-game reference currently in your
          archive; they can change if a player returns to MLB.
        </p>
      </section>
      {selected && (
        <SpecialRecordDialog
          record={selected}
          games={data.games || []}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
};
