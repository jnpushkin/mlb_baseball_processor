const analysisGameColumn = {
  key: "gameId",
  label: "Game",
  render: (id, row) => (
    <button
      className="text-blue-600 underline"
      onClick={() =>
        navigatePassport({
          game: id,
          detail: row.playIndex != null ? "playbyplay" : null,
          inning: row.inning ? String(row.inning) : null,
          half: row.half || null,
          playIndex: row.playIndex != null ? String(row.playIndex) : null,
        })
      }
    >
      Open game
    </button>
  ),
};
const analysisPlayerColumn = (key, label, idKey) => ({
  key,
  label,
  render: (name, row) =>
    row[idKey] ? (
      <PlayerLink playerId={row[idKey]} name={name} />
    ) : (
      <span>
        {name || "Unknown"}{" "}
        <span className="text-xs text-slate-500">(unresolved)</span>
      </span>
    ),
});
const analysisRate = (a, b, digits = 3) =>
  b > 0 ? (a / b).toFixed(digits) : null;
const openAnalysis = (tool, patch = {}) =>
  navigatePassport({
    tab: "dashboard",
    subtab: "discover",
    tool,
    game: null,
    player: null,
    ...patch,
  });
const AnalysisSelect = ({ label, value, onChange, options, all = "All" }) => (
  <label className="text-sm">
    {label}
    <select
      className="passport-input block mt-1 max-w-full"
      aria-label={label}
      value={value || ""}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="">{all}</option>
      {options.map((o) => (
        <option
          key={typeof o === "string" ? o : o.id}
          value={typeof o === "string" ? o : o.id}
        >
          {typeof o === "string" ? o : o.name}
        </option>
      ))}
    </select>
  </label>
);
const filterAnalysisEvents = (events, route) =>
  events.filter(
    (p) =>
      (!route.batter || p.batterId === route.batter) &&
      (!route.pitcher || p.pitcherId === route.pitcher) &&
      (!route.event ||
        (route.event === "grand_slam"
          ? p.isGrandSlam
          : route.event === "scoring"
            ? p.runs > 0
            : route.event === "extra_base_hit"
              ? ["double", "triple", "home_run"].includes(p.eventType)
              : p.eventType === route.event)) &&
      (!route.outs || p.outsBefore === Number(route.outs) - 1) &&
      (!route.situation ||
        (route.situation === "risp"
          ? p.basesBefore?.some((b) => b >= 2)
          : route.situation === "late"
            ? p.inning >= 7 && p.scoreDiff != null && Math.abs(p.scoreDiff) <= 3
            : route.situation === "ahead"
              ? p.scoreDiff > 0
              : route.situation === "behind"
                ? p.scoreDiff != null && p.scoreDiff < 0
                : route.situation === "tied"
                  ? p.scoreDiff === 0
                  : p.basesBefore?.length === 3)),
  );
const matchupRows = (events) => {
  const rows = new Map();
  events
    .filter((p) => p.isPA && p.batterId && p.pitcherId)
    .forEach((p) => {
      const key = p.batterId + "|" + p.pitcherId;
      const row = rows.get(key) || {
        id: key,
        batter: p.batter,
        batterId: p.batterId,
        pitcher: p.pitcher,
        pitcherId: p.pitcherId,
        pa: 0,
        ab: 0,
        h: 0,
        hr: 0,
        bb: 0,
        so: 0,
        games: new Set(),
      };
      row.pa++;
      row.ab += Number(p.isAB);
      row.h += Number(p.isHit);
      row.hr += Number(p.isHomeRun);
      row.bb += Number(p.isWalk);
      row.so += Number(p.isStrikeout);
      row.games.add(p.gameId);
      rows.set(key, row);
    });
  return [...rows.values()].map((r) => ({
    ...r,
    games: r.games.size,
    avg: analysisRate(r.h, r.ab),
  }));
};
const AnalysisPlays = ({ events, route, duels = false }) => {
  const filtered = filterAnalysisEvents(events, route),
    pa = filtered.filter((p) => p.isPA),
    resolved = pa.filter((p) => p.batterId && p.pitcherId);
  const people = (name, id) =>
    [
      ...new Map(
        events
          .filter((p) => p[id])
          .map((p) => [p[id], { id: p[id], name: p[name] }]),
      ).values(),
    ].sort((a, b) => a.name.localeCompare(b.name));
  const [minimum, setMinimum] = useState(1);
  const rows = duels
    ? matchupRows(filtered).filter((r) => r.pa >= minimum)
    : filtered;
  const columns = duels
    ? [
        analysisPlayerColumn("batter", "Batter", "batterId"),
        analysisPlayerColumn("pitcher", "Pitcher", "pitcherId"),
        ...["pa", "ab", "h", "hr", "bb", "so", "avg", "games"].map((k) => ({
          key: k,
          label: k.toUpperCase(),
        })),
        {
          key: "id",
          label: "Encounters",
          render: (_, r) => (
            <button
              className="text-blue-600 underline"
              onClick={() =>
                openAnalysis("plays", {
                  batter: r.batterId,
                  pitcher: r.pitcherId,
                })
              }
            >
              See plays
            </button>
          ),
        },
      ]
    : [
        { key: "date", label: "Date" },
        analysisPlayerColumn("batter", "Batter", "batterId"),
        analysisPlayerColumn("pitcher", "Pitcher", "pitcherId"),
        {
          key: "inning",
          label: "Inning",
          render: (v, r) => `${r.half === "top" ? "Top" : "Bot"} ${v}`,
        },
        { key: "outsBefore", label: "Outs before" },
        {
          key: "eventType",
          label: "Result",
          render: (v) => v.replaceAll("_", " "),
        },
        { key: "description", label: "Play" },
        analysisGameColumn,
      ];
  return (
    <section className="space-y-4">
      <div className="passport-panel space-y-3">
        <h2 className="text-xl font-bold">
          {duels ? "Batter vs. pitcher history" : "Play explorer"}
        </h2>
        <p className="text-sm text-slate-500">
          {filtered.length.toLocaleString()} events ·{" "}
          {pa.length.toLocaleString()} classified plate appearances ·{" "}
          {resolved.length.toLocaleString()} with both player identities.
          Matchup statistics describe only the encounters witnessed in this
          scope. Unknown events and identities are excluded from matchup rates.
        </p>
        <div className="flex flex-wrap gap-3">
          <AnalysisSelect
            label="Batter"
            value={route.batter}
            onChange={(v) => navigatePassport({ batter: v })}
            options={people("batter", "batterId")}
          />
          <AnalysisSelect
            label="Pitcher"
            value={route.pitcher}
            onChange={(v) => navigatePassport({ pitcher: v })}
            options={people("pitcher", "pitcherId")}
          />
          <AnalysisSelect
            label="Play result"
            value={route.event}
            onChange={(v) => navigatePassport({ event: v })}
            options={[...new Set(events.map((p) => p.eventType))]
              .sort()
              .map((k) => ({ id: k, name: k.replaceAll("_", " ") }))
              .concat([
                { id: "grand_slam", name: "Grand slam" },
                { id: "scoring", name: "Scoring play" },
                { id: "extra_base_hit", name: "Extra-base hit" },
              ])}
          />
          <AnalysisSelect
            label="Outs before play"
            value={route.outs}
            onChange={(v) => navigatePassport({ outs: v })}
            options={[
              { id: "1", name: "0 outs" },
              { id: "2", name: "1 out" },
              { id: "3", name: "2 outs" },
            ]}
          />
          <AnalysisSelect
            label="Situation"
            value={route.situation}
            onChange={(v) => navigatePassport({ situation: v })}
            options={[
              { id: "risp", name: "Runners in scoring position" },
              { id: "loaded", name: "Bases loaded" },
              { id: "late", name: "7th+ inning, within 3 runs" },
              { id: "ahead", name: "Batting team ahead" },
              { id: "tied", name: "Tied" },
              { id: "behind", name: "Batting team behind" },
            ]}
          />
          {duels && (
            <label className="text-sm">
              Minimum PA
              <input
                aria-label="Minimum matchup PA"
                type="number"
                min="1"
                className="passport-input block w-24 mt-1"
                value={minimum}
                onChange={(e) =>
                  setMinimum(Math.max(1, Number(e.target.value)))
                }
              />
            </label>
          )}
        </div>
        <p className="text-xs text-slate-500">
          Base state available for{" "}
          {pa.filter((p) => p.basesBefore != null).length.toLocaleString()} of
          these plate appearances; pre-play score for{" "}
          {pa.filter((p) => p.scoreBefore != null).length.toLocaleString()}.
          Situation filters exclude unknown state.
        </p>
        <button
          className="passport-button"
          onClick={() =>
            navigatePassport({
              batter: null,
              pitcher: null,
              event: null,
              outs: null,
              situation: null,
            })
          }
        >
          Reset play filters
        </button>
      </div>
      <DataTable
        key={duels ? "duels" : "plays"}
        title={duels ? "Witnessed matchups" : "Matching plays"}
        data={rows}
        columns={columns}
        defaultSortKey={duels ? "pa" : "date"}
        rowsPerPage={25}
        persistKey={duels ? "analysis-duels" : "analysis-plays"}
      />
    </section>
  );
};
const AnalysisSharedGames = ({ data, games, route }) => {
  const [selected, setSelected] = useState(null);
  const ids = new Set(games.flatMap((g) => g._players || []));
  const people = [
    ...new Map(
      [...(data.playerGames || []), ...(data.pitcherGames || [])]
        .filter((p) => ids.has(p.playerId))
        .map((p) => [p.playerId, { id: p.playerId, name: p.name }]),
    ).values(),
  ].sort((a, b) => a.name.localeCompare(b.name));
  const names = new Map(people.map((p) => [p.id, p.name])),
    pairs = new Map();
  games
    .filter((g) => (g._players || []).includes(route.coPlayer))
    .forEach((g) =>
      (g._players || [])
        .filter((id) => id !== route.coPlayer)
        .forEach((id) => {
          const row = pairs.get(id) || {
            playerId: id,
            name: names.get(id) || id,
            games: [],
          };
          row.games.push(g);
          pairs.set(id, row);
        }),
    );
  const rows = [...pairs.values()].map((r) => ({
    ...r,
    count: r.games.length,
  }));
  return (
    <section className="space-y-4">
      <div className="passport-panel space-y-3">
        <h2 className="text-xl font-bold">Players who shared your games</h2>
        <p className="text-sm text-slate-500">
          Counts include teammates and opponents who appeared in the same
          attended game. These are co-appearances; use Matchups for actual
          batter–pitcher encounters.
        </p>
        <AnalysisSelect
          label="Shared games player"
          all="Choose a player"
          value={route.coPlayer}
          onChange={(v) => navigatePassport({ coPlayer: v })}
          options={people}
        />
      </div>
      <DataTable
        title="Shared appearances"
        data={rows}
        defaultSortKey="count"
        columns={[
          analysisPlayerColumn("name", "Player", "playerId"),
          { key: "count", label: "Games together" },
          {
            key: "playerId",
            label: "Evidence",
            render: (_, r) => (
              <button
                className="passport-button"
                onClick={() => setSelected(r)}
              >
                See shared games
              </button>
            ),
          },
        ]}
      />
      {selected && (
        <Modal label="Shared games" onClose={() => setSelected(null)}>
          <div className="passport-panel max-h-[85vh] overflow-auto">
            <button
              className="passport-button"
              onClick={() => setSelected(null)}
            >
              Close shared games
            </button>
            <DataTable
              title={`Games with ${selected.name}`}
              data={selected.games}
              columns={[
                { key: "date", label: "Date" },
                { key: "score", label: "Score" },
                { key: "venue", label: "Ballpark" },
                {
                  ...analysisGameColumn,
                  render: (id, r) => (
                    <button
                      className="text-blue-600 underline"
                      onClick={() => {
                        setSelected(null);
                        requestGameDetails(id);
                      }}
                    >
                      Open game
                    </button>
                  ),
                },
              ]}
            />
          </div>
        </Modal>
      )}
    </section>
  );
};
const AnalysisStories = ({ data, ids }) => {
  const [selected, setSelected] = useState(null);
  const rows = (data.gameStories || []).filter((r) => ids.has(r.gameId));
  return (
    <div className="space-y-4">
      <div className="passport-panel">
        <h2 className="text-xl font-bold">Game stories</h2>
        <p className="text-sm text-slate-500">
          Rankings use completed half innings. Lead changes count a change from
          one leading team to the other, allowing a tie between them. They do
          not count leads that changed within a half inning.{" "}
          {rows.filter((r) => r.complete).length} of {rows.length} linescores
          reconcile to the final score.
        </p>
      </div>
      <DataTable
        title="Comebacks and changing leads"
        data={rows}
        columns={[
          { key: "date", label: "Date" },
          { key: "matchup", label: "Matchup" },
          { key: "score", label: "Score" },
          { key: "comeback", label: "Winning comeback" },
          { key: "leadChanges", label: "Lead changes" },
          { key: "scorelessHalves", label: "Scoreless half innings" },
          { key: "runs", label: "Total runs" },
          {
            key: "timeline",
            label: "Timeline",
            render: (_, r) => (
              <button
                className="text-blue-600 underline"
                onClick={() => setSelected(r)}
              >
                Show timeline
              </button>
            ),
          },
          analysisGameColumn,
        ]}
        defaultSortKey="comeback"
        persistKey="analysis-stories"
      />
      {selected && (
        <Modal
          label="Game scoring timeline"
          onClose={() => setSelected(null)}
          className="fixed inset-0 bg-black/50 flex items-center justify-center p-4"
        >
          <div className="passport-panel w-full max-w-xl max-h-[85vh] overflow-auto">
            <div className="flex justify-between">
              <h3 className="font-bold">
                {selected.date} · {selected.matchup}
              </h3>
              <button
                className="passport-button"
                onClick={() => setSelected(null)}
              >
                Close
              </button>
            </div>
            <p>{selected.score}</p>
            {!selected.complete && (
              <p role="status">
                Incomplete linescore: ranking metrics are unavailable.
              </p>
            )}
            <ol className="mt-4 space-y-2">
              {selected.timeline.map((r, i) => (
                <li key={i} className="flex items-center gap-3">
                  <span className="w-16 text-sm">
                    {r.half === "top" ? "Top" : "Bot"} {r.inning}
                  </span>
                  <span
                    className="h-3 rounded bg-blue-500"
                    style={{ width: Math.max(2, r.runs * 12) }}
                  />
                  <span className="text-sm">
                    {r.runs} runs · {r.away}–{r.home}
                  </span>
                  <button
                    className="ml-auto text-blue-600 underline text-sm"
                    onClick={() => {
                      setSelected(null);
                      navigatePassport({
                        game: selected.gameId,
                        detail: "playbyplay",
                        inning: String(r.inning),
                        half: r.half,
                        playIndex: null,
                      });
                    }}
                  >
                    Plays
                  </button>
                </li>
              ))}
            </ol>
          </div>
        </Modal>
      )}
    </div>
  );
};
const AnalysisArsenal = ({ data, ids }) => {
  const [pitcher, setPitcher] = useState("");
  const source = (data.pitchArsenal || []).filter((r) => ids.has(r.gameId));
  const rows = source.filter((r) => !pitcher || r.playerId === pitcher);
  const grouped = new Map();
  rows.forEach((r) => {
    const key = r.playerId + "|" + r.code;
    const v = grouped.get(key) || {
      playerId: r.playerId,
      name: r.name,
      pitchType: r.pitchType,
      count: 0,
      games: new Set(),
    };
    v.count += r.count;
    v.games.add(r.gameId);
    grouped.set(key, v);
  });
  const totals = new Map();
  rows.forEach((r) =>
    totals.set(r.playerId, (totals.get(r.playerId) || 0) + r.count),
  );
  const mix = [...grouped.values()].map((r) => ({
    ...r,
    games: r.games.size,
    share: ((100 * r.count) / totals.get(r.playerId)).toFixed(1),
  }));
  const starts = [
    ...new Map(rows.map((r) => [r.playerId + "|" + r.gameId, r])).values(),
  ];
  return (
    <div className="space-y-4">
      <div className="passport-panel">
        <h2 className="text-xl font-bold">Pitch arsenals</h2>
        <p className="text-sm text-slate-500">
          Mix percentages use classified pitches in the selected games. Average
          velocity below covers all measured pitch types in that appearance; it
          is not fastball velocity.
        </p>
        <AnalysisSelect
          label="Arsenal pitcher"
          value={pitcher}
          onChange={setPitcher}
          options={[
            ...new Map(
              source.map((r) => [r.playerId, { id: r.playerId, name: r.name }]),
            ).values(),
          ].sort((a, b) => a.name.localeCompare(b.name))}
        />
      </div>
      <DataTable
        title="Pitch mix witnessed"
        data={mix}
        columns={[
          analysisPlayerColumn("name", "Pitcher", "playerId"),
          { key: "pitchType", label: "Pitch" },
          { key: "count", label: "Classified pitches" },
          { key: "share", label: "Mix %" },
          { key: "games", label: "Appearances with this pitch" },
        ]}
        defaultSortKey="count"
        persistKey="analysis-arsenals"
      />
      <DataTable
        title="Velocity by appearance"
        data={starts}
        columns={[
          { key: "date", label: "Date" },
          analysisPlayerColumn("name", "Pitcher", "playerId"),
          { key: "avgSpeed", label: "Average mph" },
          { key: "totalPitches", label: "Pitches" },
          analysisGameColumn,
        ]}
        defaultSortKey="date"
        persistKey="analysis-velocity"
      />
    </div>
  );
};
const careerShareRows = (data, games, metric) => {
  const definitions = {
    h: ["hitting", "hits", "h"],
    hr: ["hitting", "homeRuns", "hr"],
    sb: ["hitting", "stolenBases", "sb"],
    starts: ["pitching", "gamesStarted", "gameStarts"],
    so: ["pitching", "strikeOuts", "so"],
  };
  const [group, totalKey, rowKey] = definitions[metric] || definitions.h;
  const allowed = new Set(
    games.filter((g) => g.gameType === "regular").map((g) => g.gameId),
  );
  const totals = new Map();
  (data[group === "hitting" ? "playerGames" : "pitcherGames"] || [])
    .filter((r) => allowed.has(r.gameId))
    .forEach((r) => {
      const t = totals.get(r.playerId) || {
        playerId: r.playerId,
        name: r.name,
        witnessed: 0,
        dates: [],
      };
      t.witnessed += Number(r[rowKey] || 0);
      t.dates.push(toSortableDate(r.date));
      totals.set(r.playerId, t);
    });
  return [...totals.values()]
    .filter((r) => r.witnessed > 0)
    .map((r) => {
      const c = data.careerContext?.[r.playerId],
        denominator = c?.totals?.[group]?.[totalKey];
      const refreshed = c?.cacheRefreshedAt?.slice(0, 10) || "";
      // A cache timestamp is not a guarantee every season fetch succeeded.
      const fresh =
        refreshed &&
        toSortableDate(refreshed) >= r.dates.sort().at(-1) &&
        denominator >= r.witnessed;
      return {
        ...r,
        careerTotal: denominator ?? null,
        cacheDate: refreshed,
        share:
          fresh && denominator > 0
            ? ((100 * r.witnessed) / denominator).toFixed(2)
            : null,
        status: !c
          ? "No career cache"
          : fresh
            ? "Cached denominator; verify for current totals"
            : "Refresh required",
        mlbId: c?.mlbId,
      };
    });
};
const AnalysisCareer = ({ data, games }) => {
  const [metric, setMetric] = useState("h"),
    [live, setLive] = useState({}),
    [message, setMessage] = useState("");
  const rows = careerShareRows(data, games, metric).map((r) => {
    const v = live[r.playerId + ":" + metric];
    return v
      ? {
          ...r,
          ...v,
          share:
            v.careerTotal >= r.witnessed && v.careerTotal > 0
              ? ((100 * r.witnessed) / v.careerTotal).toFixed(2)
              : null,
        }
      : r;
  });
  const refresh = async (row) => {
    setMessage(`Loading career totals for ${row.name}…`);
    try {
      const group = ["starts", "so"].includes(metric) ? "pitching" : "hitting";
      const response = await fetch(
        `https://statsapi.mlb.com/api/v1/people/${row.mlbId}/stats?stats=career&group=${group}&gameType=R`,
      );
      if (!response.ok) throw Error(`HTTP ${response.status}`);
      const body = await response.json(),
        stats = body.stats?.find((s) => s.group?.displayName === group)
          ?.splits?.[0]?.stat;
      const key = {
          h: "hits",
          hr: "homeRuns",
          sb: "stolenBases",
          starts: "gamesStarted",
          so: "strikeOuts",
        }[metric],
        total = stats?.[key];
      if (total == null || Number(total) < row.witnessed)
        throw Error(
          "Career total unavailable or smaller than the attended sample",
        );
      setLive((v) => ({
        ...v,
        [row.playerId + ":" + metric]: {
          careerTotal: Number(total),
          share: total > 0 ? ((100 * row.witnessed) / total).toFixed(2) : null,
          cacheDate: new Date().toISOString().slice(0, 10),
          status: "MLB API career total, retrieved now",
        },
      }));
      setMessage(`Updated ${row.name}.`);
    } catch (e) {
      setMessage(
        `Could not verify ${row.name}: ${e.message}. Cached values were preserved.`,
      );
    }
  };
  return (
    <div className="space-y-4">
      <div className="passport-panel space-y-3">
        <h2 className="text-xl font-bold">Your share of a career</h2>
        <p className="text-sm text-slate-500">
          Only regular-season appearances count here, matching the career
          denominator. Cached percentages are withheld when the cache predates a
          witnessed game. Verify a player to retrieve current MLB career totals.
        </p>
        <AnalysisSelect
          label="Career statistic"
          value={metric}
          onChange={(v) => setMetric(v || "h")}
          all="Hits"
          options={[
            { id: "h", name: "Hits" },
            { id: "hr", name: "Home runs" },
            { id: "sb", name: "Stolen bases" },
            { id: "starts", name: "Pitching starts" },
            { id: "so", name: "Pitching strikeouts" },
          ]}
        />
        <p role="status">{message}</p>
      </div>
      <DataTable
        title="Career share"
        data={rows}
        columns={[
          analysisPlayerColumn("name", "Player", "playerId"),
          { key: "witnessed", label: "Witnessed" },
          { key: "careerTotal", label: "Career total" },
          { key: "share", label: "Share %" },
          { key: "cacheDate", label: "Reference refreshed" },
          { key: "status", label: "Reference status" },
          {
            key: "playerId",
            label: "Verify",
            render: (_, r) => (
              <button
                className="passport-button"
                disabled={!r.mlbId}
                onClick={() => refresh(r)}
              >
                Verify current total
              </button>
            ),
          },
        ]}
        defaultSortKey="witnessed"
        persistKey="analysis-career"
      />
    </div>
  );
};
const personalMilestones = (games, appearances = []) => {
  const rows = [],
    parks = new Map(),
    players = new Map(),
    teams = new Map(),
    lastPark = new Map(),
    longestGap = new Map(),
    playerTeams = new Map();
  const byGame = new Map();
  appearances.forEach((r) => {
    if (!byGame.has(r.gameId)) byGame.set(r.gameId, []);
    byGame.get(r.gameId).push(r);
  });
  const ordered = [...games].sort(
    (a, b) =>
      toSortableDate(a.date).localeCompare(toSortableDate(b.date)) ||
      a.gameId.localeCompare(b.gameId),
  );
  const thresholds = new Set([1, 5, 10, 25, 50, 100, 150, 200, 250, 500, 1000]);
  ordered.forEach((g, i) => {
    const add = (kind, n, label) => {
      if (thresholds.has(n))
        rows.push({
          id: g.gameId + kind + label,
          date: g.date,
          gameId: g.gameId,
          kind,
          count: n,
          label,
        });
    };
    add("Games", i + 1, `Game ${i + 1} in this scope`);
    const park = g._venueKey || g.venue;
    const day = toSortableDate(g.date),
      time = Date.parse(
        `${day.slice(0, 4)}-${day.slice(4, 6)}-${day.slice(6, 8)}T12:00:00Z`,
      );
    if (lastPark.has(park)) {
      const gap = Math.round((time - lastPark.get(park)) / 86400000);
      if (gap > (longestGap.get(park) || 0)) {
        longestGap.set(park, gap);
        rows.push({
          id: g.gameId + "gap" + park,
          date: g.date,
          gameId: g.gameId,
          kind: "Return gaps",
          count: gap,
          label: `Back to ${park} after ${gap.toLocaleString()} days — longest gap so far in this scope`,
        });
      }
    }
    lastPark.set(park, time);
    parks.set(park, (parks.get(park) || 0) + 1);
    add("Ballpark", parks.get(park), `${park} visit ${parks.get(park)}`);
    for (const t of [g.homeTeam, g.awayTeam]) {
      teams.set(t, (teams.get(t) || 0) + 1);
      add("Team", teams.get(t), `${t} appearance ${teams.get(t)}`);
    }
    for (const id of g._players || []) {
      players.set(id, (players.get(id) || 0) + 1);
    }
    const participants = new Map(
      (byGame.get(g.gameId) || []).map((r) => [r.playerId, r]),
    );
    for (const [pid, p] of participants) {
      const known = playerTeams.get(pid) || new Set();
      if (p.team && !known.has(p.team) && known.size)
        rows.push({
          id: g.gameId + "newteam" + pid,
          date: g.date,
          gameId: g.gameId,
          kind: "New team",
          label: `First time seeing ${p.name} with ${p.team}`,
          count: known.size + 1,
        });
      if (p.team) known.add(p.team);
      playerTeams.set(pid, known);
      const n = players.get(pid) || 1;
      if (thresholds.has(n))
        rows.push({
          id: g.gameId + "player" + pid,
          date: g.date,
          gameId: g.gameId,
          kind: "Player",
          count: n,
          label: `${p.name}: appearance ${n} in this scope`,
        });
    }
  });
  return { rows, parks, players, teams };
};
const AnalysisMilestones = ({ games, data }) => {
  const stats = personalMilestones(games, [
      ...(data.playerGames || []),
      ...(data.pitcherGames || []),
    ]),
    [kind, setKind] = useState("Games");
  const next = [...stats.parks]
    .map(([name, count]) => ({
      name,
      count,
      next: [1, 5, 10, 25, 50, 100, 150, 200, 250, 500, 1000].find(
        (n) => n > count,
      ),
    }))
    .filter((r) => r.next)
    .map((r) => ({ ...r, remaining: r.next - r.count }));
  return (
    <div className="space-y-4">
      <div className="passport-panel">
        <h2 className="text-xl font-bold">Personal milestones</h2>
        <p className="text-sm text-slate-500">
          Recomputed chronologically within Browse scope, so newly added
          historical games fit into the right place.
        </p>
        <AnalysisSelect
          label="Personal milestone category"
          value={kind}
          onChange={setKind}
          options={[
            "Games",
            "Ballpark",
            "Team",
            "Player",
            "New team",
            "Return gaps",
          ]}
        />
      </div>
      <DataTable
        title="Your milestones"
        data={stats.rows.filter((r) => !kind || r.kind === kind)}
        columns={[
          { key: "date", label: "Date" },
          { key: "label", label: "Milestone" },
          analysisGameColumn,
        ]}
        defaultSortKey="date"
        persistKey="analysis-personal"
      />
      <DataTable
        title="Next ballpark milestones"
        data={next}
        columns={[
          { key: "name", label: "Ballpark" },
          { key: "count", label: "Visits" },
          { key: "next", label: "Next mark" },
          { key: "remaining", label: "Visits to go" },
        ]}
        defaultSortKey="remaining"
        defaultSortDir="asc"
        persistKey="analysis-next-marks"
      />
    </div>
  );
};
const AnalysisHub = ({ data, route }) => {
  const tools = [
    ["plays", "Plays"],
    ["duels", "Matchups"],
    ["shared", "Shared games"],
    ["stories", "Game stories"],
    ["career", "Career share"],
    ["arsenal", "Pitch arsenals"],
    ["personal", "Personal milestones"],
    ["context", "Then & now"],
    ["trips", "Trips"],
    ["journeys", "Player journeys"],
    ["quiz", "Trivia"],
  ];
  const tool = tools.some(([id]) => id === route.tool) ? route.tool : "plays";
  const games = scopeGames(data.games || [], route),
    ids = new Set(games.map((g) => g.gameId));
  const events = (data.playEvents || []).filter((p) => ids.has(p.gameId));
  return (
    <div className="space-y-4">
      <div className="passport-panel">
        <h1 className="text-2xl font-bold">Discover your baseball history</h1>
        <p className="text-sm text-slate-500">
          {games.length} games in Browse scope. Every analysis keeps its source
          games within reach.
        </p>
        <label className="block sm:hidden mt-3 text-sm">
          Discovery tool
          <select
            aria-label="Discovery tool"
            className="passport-input w-full block mt-1"
            value={tool}
            onChange={(e) => openAnalysis(e.target.value)}
          >
            {tools.map(([id, label]) => (
              <option key={id} value={id}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <nav
          aria-label="Discovery tools"
          className="hidden sm:flex flex-wrap gap-2 mt-3"
        >
          {tools.map(([id, label]) => (
            <button
              className="passport-button"
              aria-current={tool === id ? "page" : undefined}
              key={id}
              onClick={() => openAnalysis(id)}
            >
              {label}
            </button>
          ))}
        </nav>
        <button
          className="text-blue-600 underline text-sm mt-3"
          onClick={() =>
            navigatePassport({ tab: "players", subtab: "explorer" })
          }
        >
          Open advanced stat queries →
        </button>
      </div>
      {["plays", "duels"].includes(tool) && (
        <AnalysisPlays events={events} route={route} duels={tool === "duels"} />
      )}
      {tool === "stories" && <AnalysisStories data={data} ids={ids} />}
      {tool === "shared" && (
        <AnalysisSharedGames data={data} games={games} route={route} />
      )}
      {tool === "arsenal" && <AnalysisArsenal data={data} ids={ids} />}
      {tool === "career" && <AnalysisCareer data={data} games={games} />}
      {tool === "personal" && <AnalysisMilestones data={data} games={games} />}
      {tool === "context" && <AnalysisContext data={data} games={games} />}
      {tool === "trips" && <AnalysisTrips data={data} games={games} />}
      {tool === "journeys" && <AnalysisJourneys data={data} games={games} />}
      {tool === "quiz" && <AnalysisQuiz data={data} games={games} />}
    </div>
  );
};

const AnalysisContext = ({ data, games }) => {
  const [id, setId] = useState(""),
    [standings, setStandings] = useState([]),
    [message, setMessage] = useState("");
  const ordered = [...games].sort((a, b) =>
    toSortableDate(b.date).localeCompare(toSortableDate(a.date)),
  );
  const game = ordered.find((g) => g.gameId === id) || ordered[0];
  const standingsRequest = useRef(0);
  useEffect(() => {
    standingsRequest.current++;
    setStandings([]);
    setMessage("");
    return () => {
      standingsRequest.current++;
    };
  }, [game?.gameId]);
  const people = new Map(
    [...(data.players || []), ...(data.pitchers || [])].map((p) => [
      p.playerId,
      p,
    ]),
  );
  const participants = (game?._players || []).map((pid) => {
    const bio = data.playerBios?.[pid] || {},
      day = toSortableDate(game.date),
      born = toSortableDate(bio.birthDate);
    const age = /^\d{8}$/.test(born)
      ? Number(day.slice(0, 4)) -
        Number(born.slice(0, 4)) -
        Number(day.slice(4) < born.slice(4))
      : null;
    const debut = toSortableDate(bio.debutDate);
    return {
      playerId: pid,
      name: people.get(pid)?.name || bio.name || pid,
      age,
      debut: bio.debutDate || "",
      stage:
        debut && day.slice(0, 4) === debut.slice(0, 4)
          ? "MLB debut season"
          : debut && day >= debut
            ? `${Number(day.slice(0, 4)) - Number(debut.slice(0, 4))} years after debut year`
            : "Debut unavailable",
    };
  });
  const seen = new Set(game?._players || []),
    year = Number(toSortableDate(game?.date).slice(0, 4));
  const awards = (data.awardChecklists?.groups || []).flatMap((group) =>
    group.items
      .filter((r) => seen.has(r.playerId) && Number(r.year) === year)
      .map((r) => ({ ...r, award: group.award })),
  );
  const loadStandings = async () => {
    if (!game) return;
    const request = ++standingsRequest.current;
    setStandings([]);
    setMessage("Loading historical standings…");
    try {
      const day = toSortableDate(game.date),
        date = new Date(
          `${day.slice(0, 4)}-${day.slice(4, 6)}-${day.slice(6, 8)}T12:00:00Z`,
        );
      date.setUTCDate(date.getUTCDate() - 1);
      const previous = date.toISOString().slice(0, 10),
        response = await fetch(
          `https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=${year}&date=${previous}&standingsTypes=regularSeason`,
        );
      if (!response.ok) throw Error(`HTTP ${response.status}`);
      const body = await response.json(),
        teamIds = [TEAM_LOGO_IDS[game.homeTeam], TEAM_LOGO_IDS[game.awayTeam]];
      const rows = (body.records || [])
        .flatMap((r) => r.teamRecords || [])
        .filter((r) => teamIds.includes(r.team?.id));
      if (request !== standingsRequest.current) return;
      setStandings(rows);
      setMessage(
        rows.length
          ? `Regular-season standings through ${previous}, retrieved from MLB. Same-day earlier games are excluded.`
          : "Historical standings are unavailable for this date.",
      );
    } catch (e) {
      if (request !== standingsRequest.current) return;
      setMessage(`Standings unavailable: ${e.message}.`);
    }
  };
  return (
    <div className="space-y-4">
      <section className="passport-panel space-y-3">
        <h2 className="text-xl font-bold">Then & now</h2>
        <AnalysisSelect
          label="Context game"
          value={game?.gameId}
          onChange={(v) => {
            setId(v);
            setStandings([]);
            setMessage("");
          }}
          all="Most recent in scope"
          options={ordered.map((g) => ({
            id: g.gameId,
            name: `${g.date} · ${g.awayTeam} @ ${g.homeTeam}`,
          }))}
        />
        <button
          className="passport-button"
          disabled={!game}
          onClick={loadStandings}
        >
          Load standings entering this day
        </button>
        <p role="status" className="text-sm">
          {message}
        </p>
        {standings.map((r) => (
          <p key={r.team.id}>
            {r.team.name}: {r.leagueRecord?.wins}–{r.leagueRecord?.losses} ·
            division rank {r.divisionRank} · {r.gamesBack} games back
          </p>
        ))}
      </section>
      <DataTable
        title="Players at the time"
        data={participants}
        columns={[
          analysisPlayerColumn("name", "Player", "playerId"),
          { key: "age", label: "Age on game date" },
          { key: "debut", label: "MLB debut" },
          { key: "stage", label: "Career stage" },
        ]}
        defaultSortKey="age"
        persistKey="analysis-context"
      />
      <div className="passport-panel">
        <h3 className="font-bold">Awards associated with this season</h3>
        <p className="text-sm text-slate-500">
          Retrospective context from the award reference. These awards were not
          necessarily known on the game date.
        </p>
        {awards.length ? (
          awards.map((r, i) => (
            <p key={r.id || i}>
              <PlayerLink playerId={r.playerId} name={r.name} /> · {r.year}{" "}
              {r.award} {r.league}
            </p>
          ))
        ) : (
          <p>No matching awards in the current reference.</p>
        )}
      </div>
    </div>
  );
};
const downloadTextFile = (text, name, type = "text/plain") => {
  const url = URL.createObjectURL(new Blob([text], { type })),
    a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};
const escapeCalendar = (value) =>
  String(value || "")
    .replaceAll("\\", "\\\\")
    .replace(/\r?\n/g, "\\n")
    .replaceAll(",", "\\,")
    .replaceAll(";", "\\;");
const calendarForGames = (rows) => {
  const stamp = new Date()
    .toISOString()
    .replace(/[-:]/g, "")
    .replace(/\.\d{3}Z$/, "Z");
  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//MLB Game Passport//Visits//EN",
  ];
  rows.forEach((g) => {
    const day = toSortableDate(g.date),
      timed =
        g.gameDate && !g.isTimeTBA && Number.isFinite(Date.parse(g.gameDate));
    const start = timed
      ? new Date(g.gameDate)
          .toISOString()
          .replace(/[-:]/g, "")
          .replace(/\.\d{3}Z$/, "Z")
      : day;
    lines.push(
      "BEGIN:VEVENT",
      `UID:${escapeCalendar(g.gamePk || g.gameId)}@mlb-game-passport`,
      `DTSTAMP:${stamp}`,
      `${timed ? "DTSTART" : "DTSTART;VALUE=DATE"}:${start}`,
      `SUMMARY:${escapeCalendar(g.matchup || `${g.awayTeam} @ ${g.homeTeam}`)}`,
      `LOCATION:${escapeCalendar(typeof g.venue === "object" ? g.venue.name : g.venue)}`,
      "END:VEVENT",
    );
  });
  return [...lines, "END:VCALENDAR", ""].join("\r\n");
};
const AnalysisTrips = ({ games }) => {
  const [journal] = usePersonal("journal", {}),
    [trip, setTrip] = useState("");
  const names = [
    ...new Set(
      Object.values(journal)
        .map((r) => r.trip?.trim())
        .filter(Boolean),
    ),
  ].sort();
  const rows = games
    .filter(
      (g) =>
        journal[g.gameId]?.trip?.trim() &&
        (!trip || journal[g.gameId].trip.trim() === trip),
    )
    .map((g) => ({
      ...g,
      ...journal[g.gameId],
      trip: journal[g.gameId].trip.trim(),
      currency: journal[g.gameId].currency || "USD",
    }));
  const costs = {};
  rows.forEach((r) => {
    if (
      r.ticketCost !== "" &&
      r.ticketCost != null &&
      Number.isFinite(Number(r.ticketCost))
    )
      costs[r.currency] = (costs[r.currency] || 0) + Number(r.ticketCost);
  });
  const ratings = rows.filter(
    (r) => Number(r.rating) >= 1 && Number(r.rating) <= 5,
  );
  return (
    <div className="space-y-4">
      <section className="passport-panel space-y-3">
        <h2 className="text-xl font-bold">Your baseball trips</h2>
        <p className="text-sm text-slate-500">
          Add a trip name, rating, and ticket cost in the game journal. These
          records stay private in this browser and your private backup.
        </p>
        <AnalysisSelect
          label="Trip"
          value={trip}
          onChange={setTrip}
          options={names}
        />
        <p>
          {rows.length} games ·{" "}
          {new Set(rows.map((r) => r._venueKey || r.venue)).size} parks ·{" "}
          {ratings.length
            ? `${(ratings.reduce((n, r) => n + Number(r.rating), 0) / ratings.length).toFixed(1)} / 5 average rating (${ratings.length} rated)`
            : "No ratings yet"}
        </p>
        <p>
          {Object.entries(costs)
            .map(([currency, value]) => `${currency} ${value.toFixed(2)}`)
            .join(" · ") || "No ticket costs entered"}
        </p>
        <div className="flex flex-wrap gap-2">
          <button
            className="passport-button"
            disabled={!rows.length}
            onClick={() =>
              downloadTextFile(
                calendarForGames(rows),
                "baseball-trip.ics",
                "text/calendar",
              )
            }
          >
            Export game dates
          </button>
          <button
            className="passport-button"
            disabled={!rows.length}
            onClick={() => downloadPassport(rows, "private-baseball-trip.json")}
          >
            Export private trip details
          </button>
          <button
            className="passport-button"
            onClick={() =>
              navigatePassport({ tab: "dashboard", subtab: "journal" })
            }
          >
            Open journal
          </button>
        </div>
      </section>
      <DataTable
        title="Trip games"
        data={rows}
        columns={[
          { key: "trip", label: "Trip" },
          { key: "date", label: "Date" },
          { key: "score", label: "Game" },
          { key: "venue", label: "Ballpark" },
          { key: "rating", label: "Rating / 5" },
          { key: "ticketCost", label: "Ticket cost" },
          { key: "currency", label: "Currency" },
          analysisGameColumn,
        ]}
        defaultSortKey="date"
        persistKey="analysis-trips"
      />
    </div>
  );
};
const AnalysisJourneys = ({ data, games }) => {
  const archive = data.playerJourneys || {},
    [player, setPlayer] = useState(""),
    ids = new Set(games.flatMap((g) => g._players || []));
  const players = (archive.players || []).filter((p) => ids.has(p.playerId));
  const rows = players
    .filter((p) => !player || p.playerId === player)
    .flatMap((p) =>
      p.appearances.map((r) => ({ ...r, playerId: p.playerId, name: p.name })),
    );
  return (
    <div className="space-y-4">
      <div className="passport-panel space-y-3">
        <h2 className="text-xl font-bold">Player journeys</h2>
        <p className="text-sm text-slate-500">
          Players present in your MLB Browse scope, followed across all
          available linked college, minor-league and MLB appearances. Matching
          uses shared player IDs, not names alone.{" "}
          {archive.available
            ? `${players.length} linked players. Shared reference refreshed ${archive.generatedAt || "date unavailable"}.`
            : "The sibling appearance archive is unavailable."}
        </p>
        <AnalysisSelect
          label="Journey player"
          value={player}
          onChange={setPlayer}
          options={players
            .map((p) => ({ id: p.playerId, name: p.name }))
            .sort((a, b) => a.name.localeCompare(b.name))}
        />
      </div>
      <DataTable
        title="Appearances across levels"
        data={rows}
        columns={[
          { key: "date", label: "Date" },
          analysisPlayerColumn("name", "Player", "playerId"),
          { key: "level", label: "Level" },
          { key: "team", label: "Team" },
          { key: "opponent", label: "Opponent" },
          {
            key: "gameId",
            label: "Source",
            render: (id, r) =>
              r.level === "MLB" ? (
                <button
                  className="text-blue-600 underline"
                  onClick={() => navigatePassport({ game: id })}
                >
                  Open MLB game
                </button>
              ) : r.websiteUrl && /^https:\/\//.test(r.websiteUrl) ? (
                <a
                  className="text-blue-600 underline"
                  href={r.websiteUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  College/minor archive ↗
                </a>
              ) : (
                <span>{id}</span>
              ),
          },
        ]}
        defaultSortKey="date"
        persistKey="analysis-journeys"
      />
    </div>
  );
};
const AnalysisQuiz = ({ games, data }) => {
  const [index, setIndex] = useState(0),
    [revealed, setRevealed] = useState(false);
  const ordered = [...games].sort(
    (a, b) =>
      toSortableDate(a.date).localeCompare(toSortableDate(b.date)) ||
      a.gameId.localeCompare(b.gameId),
  );
  const first = ordered[0],
    last = ordered.at(-1),
    questions = [];
  if (first)
    questions.push({
      q: "Where was your first game in this scope?",
      answer: `${first.venue} · ${first.date}`,
      gameId: first.gameId,
    });
  if (last)
    questions.push({
      q: "Which teams played in your most recent game in this scope?",
      answer: `${last.awayTeam} @ ${last.homeTeam} · ${last.date}`,
      gameId: last.gameId,
    });
  const high = [...games]
    .filter((g) => gameScores(g))
    .sort((a, b) => {
      const x = gameScores(a),
        y = gameScores(b);
      return y.awayScore + y.homeScore - x.awayScore - x.homeScore;
    })[0];
  if (high) {
    const s = gameScores(high);
    questions.push({
      q: "Name a highest-scoring game you attended in this scope.",
      answer: `${high.score} · ${high.date} (${s.awayScore + s.homeScore} runs; ties may exist)`,
      gameId: high.gameId,
    });
  }
  const entries = [...personalMilestones(games).parks].sort(
    (a, b) => b[1] - a[1],
  );
  if (entries.length)
    questions.push({
      q: "Which ballpark did you visit most in this scope?",
      answer: entries
        .filter((x) => x[1] === entries[0][1])
        .map(([name, n]) => `${name}: ${n} games`)
        .join(" · "),
    });
  const q = questions[index % Math.max(1, questions.length)];
  return (
    <section className="passport-panel space-y-4">
      <h2 className="text-xl font-bold">Personal baseball trivia</h2>
      {q ? (
        <>
          <p className="text-lg">{q.q}</p>
          {revealed ? (
            <div>
              <p className="font-semibold">{q.answer}</p>
              {q.gameId && (
                <button
                  className="text-blue-600 underline"
                  onClick={() => navigatePassport({ game: q.gameId })}
                >
                  See the game
                </button>
              )}
            </div>
          ) : (
            <button
              className="passport-button"
              onClick={() => setRevealed(true)}
            >
              Reveal answer
            </button>
          )}
          <button
            className="passport-button"
            onClick={() => {
              setIndex((i) => i + 1);
              setRevealed(false);
            }}
          >
            Next question
          </button>
          <p className="text-xs text-slate-500">
            Answers are computed from the games in Browse scope.
          </p>
        </>
      ) : (
        <p>Add games to begin.</p>
      )}
    </section>
  );
};

const AnalysisHealthDetails = ({ data }) => {
  const [issue, setIssue] = useState("unknown");
  const byGame = new Map((data.analysisHealth || []).map((r) => [r.gameId, r]));
  const rows = (data.games || [])
    .map((g) => ({ ...g, ...byGame.get(g.gameId) }))
    .filter((g) => {
      if (issue === "pitchData" || issue === "hitData")
        return !g._coverage?.[issue];
      if (issue === "changed")
        return (data.__health?.corrections || []).includes(g.gameId);
      return issue ? Number(g[issue] || 0) > 0 : true;
    });
  return (
    <section className="space-y-3">
      <h2 className="text-lg font-bold">Inspect affected games</h2>
      <AnalysisSelect
        label="Data issue"
        value={issue}
        onChange={setIssue}
        options={[
          { id: "unknown", name: "Unclassified play descriptions" },
          { id: "unresolved", name: "Unresolved matchup identities" },
          { id: "missingBases", name: "Missing pre-play bases" },
          { id: "missingScore", name: "Missing pre-play score" },
          { id: "pitchData", name: "No pitch velocity measurements" },
          { id: "hitData", name: "No exit velocity measurements" },
          { id: "changed", name: "Changed since previous build" },
        ]}
      />
      <p className="text-sm text-slate-500">
        Missing measurements can reflect source limitations, especially older
        games. Review the source before attempting a repair. Export this list to
        scope a local enrichment or identity-repair run.
      </p>
      <DataTable
        title="Data review list"
        data={rows}
        columns={[
          { key: "date", label: "Date" },
          { key: "score", label: "Game" },
          { key: "source", label: "Source" },
          { key: "pa", label: "Classified PA" },
          { key: "unknown", label: "Unknown events" },
          { key: "unresolved", label: "Unresolved identities" },
          { key: "missingBases", label: "PA without bases" },
          analysisGameColumn,
        ]}
        defaultSortKey="date"
        persistKey="analysis-health"
      />
      {(data.dataChanges || []).length > 0 && (
        <DataTable
          title="Published value changes"
          data={data.dataChanges}
          columns={[
            { key: "date", label: "Date" },
            { key: "field", label: "Field" },
            { key: "before", label: "Previous value" },
            { key: "after", label: "New value" },
            analysisGameColumn,
          ]}
          defaultSortKey="date"
          persistKey="analysis-changes"
        />
      )}
    </section>
  );
};
