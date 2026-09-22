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
  const linkedGames = specialRecordGames(record, games);
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
            <p className="mt-2 text-3xl font-bold tabular-nums text-blue-700">
              {record.value}
            </p>
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
        <div className="space-y-6 overflow-y-auto p-5">
          {record.detail && (
            <div>
              <h4 className="mb-2 font-semibold text-slate-900">The record</h4>
              <ul className="space-y-2 text-sm leading-relaxed text-slate-600">
                {String(record.detail)
                  .split(";")
                  .filter((s) => s.trim())
                  .map((detail, i) => (
                    <li key={i}>{detail.trim()}</li>
                  ))}
              </ul>
            </div>
          )}
          {linkedGames.length > 0 ? (
            <section aria-label="Games behind this record">
              <h4 className="mb-3 font-semibold text-slate-900">
                Games behind this record · {linkedGames.length}
              </h4>
              <div className="space-y-3">
                {linkedGames.map((game) => (
                  <article
                    key={game.gameId}
                    className="flex flex-col justify-between gap-3 rounded-lg border border-slate-200 p-3 sm:flex-row sm:items-center"
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-slate-900">
                        {game.awayTeam} at {game.homeTeam}{" "}
                        <span className="font-normal text-slate-500">
                          · {game.date}
                        </span>
                      </p>
                      <p className="mt-1 text-sm text-slate-600">
                        {game.score}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">
                        {game.venue}
                      </p>
                    </div>
                    <SpecialGameButton gameId={game.gameId} onOpen={onClose} />
                  </article>
                ))}
              </div>
            </section>
          ) : (
            <p className="text-sm text-slate-500">
              This is an archive-wide summary; no individual game is linked.
            </p>
          )}
        </div>
      </div>
    </Modal>
  );
};
const SpecialRecordCard = ({ record, onSelect }) => (
  <button
    onClick={() => onSelect(record)}
    aria-haspopup="dialog"
    aria-label={`${record.record}: ${record.value}. Explore record`}
    className="group flex h-full w-full flex-col rounded-xl border border-slate-200 bg-white p-5 text-left transition hover:border-blue-300 hover:shadow-sm focus-visible:ring-2 focus-visible:ring-blue-500"
  >
    <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
      {SPECIAL_RECORD_LABELS[record.section]}
    </span>
    <span className="mt-3 text-3xl font-bold tabular-nums text-slate-900">
      {record.value}
    </span>
    <span className="mt-2 text-sm font-semibold text-slate-900">
      {record.record}
    </span>
    {record.detail && (
      <span className="mt-2 line-clamp-2 text-sm leading-relaxed text-slate-500">
        {record.detail}
      </span>
    )}
    <span className="mt-4 text-sm font-semibold text-blue-700">
      Explore record <span aria-hidden="true">→</span>
    </span>
  </button>
);
const PersonalRecords = ({ data }) => {
  const [search, setSearch] = useState("");
  const [section, setSection] = useState("all");
  const [selected, setSelected] = useState(null);
  const records = useMemo(() => specialRecords(data), [data.summary]);
  const filtered = records.filter(
    (r) =>
      (section === "all" || r.section === section) &&
      normalizeSearchText(`${r.record} ${r.detail || ""}`).includes(
        normalizeSearchText(search),
      ),
  );
  const reset = () => {
    setSearch("");
    setSection("all");
  };
  return (
    <div className="space-y-5">
      <SpecialHeader eyebrow="Your personal bests" title="Personal Record Book">
        Find the games behind your biggest scores, standout performances, and
        ballpark extremes. Cumulative totals exclude spring training.
      </SpecialHeader>
      <div className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 sm:flex-row sm:items-end">
        <label className="flex-1 text-sm font-semibold text-slate-700">
          Search records
          <input
            className="mt-1 block min-h-11 w-full rounded-lg border border-slate-300 px-3 font-normal"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Record, player, or team"
            type="search"
          />
        </label>
        <label className="text-sm font-semibold text-slate-700">
          Record category
          <select
            aria-label="Record category"
            className="mt-1 block min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 font-normal sm:w-56"
            value={section}
            onChange={(e) => setSection(e.target.value)}
          >
            <option value="all">All categories ({records.length})</option>
            {Object.entries(SPECIAL_RECORD_LABELS).map(([key, label]) => {
              const count = records.filter((r) => r.section === key).length;
              return count ? (
                <option key={key} value={key}>
                  {label} ({count})
                </option>
              ) : null;
            })}
          </select>
        </label>
        {(search || section !== "all") && (
          <button
            onClick={reset}
            className="min-h-11 rounded-lg border px-3 text-sm font-semibold text-slate-700"
          >
            Clear filters
          </button>
        )}
      </div>
      <p role="status" className="text-sm text-slate-500">
        {filtered.length} of {records.length} records
      </p>
      {filtered.length ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((r) => (
            <SpecialRecordCard
              key={r.record}
              record={r}
              onSelect={setSelected}
            />
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
  const records = useMemo(() => specialRecords(data), [data.summary]);
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
