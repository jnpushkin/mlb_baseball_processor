"""Pure browser utilities, also exercised directly by Node regression tests."""

CODE = r'''
const toSortableDate = (value) => {
    if (!value) return '';
    const text = String(value).trim();
    if (/^\d{8}$/.test(text)) return text;
    const iso = text.match(/^(\d{4})-(\d{2})-(\d{2})(?:$|T)/);
    if (iso) return iso.slice(1).join('');
    const us = text.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
    if (us) return `${us[3]}${us[1].padStart(2, '0')}${us[2].padStart(2, '0')}`;
    const parsed = Date.parse(text);
    if (!Number.isNaN(parsed)) {
        const date = new Date(parsed);
        return `${date.getFullYear()}${String(date.getMonth() + 1).padStart(2, '0')}${String(date.getDate()).padStart(2, '0')}`;
    }
    return text;
};
const isDateInRange = (value, start, end) => {
    const day = toSortableDate(value);
    if (!/^\d{8}$/.test(day)) return !start && !end;
    return (!start || day >= toSortableDate(start)) && (!end || day <= toSortableDate(end));
};
const normalizeSearchText = (value) => String(value ?? '').normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '').toLowerCase()
    .replace(/[.'’`]/g, '').replace(/[^a-z0-9]+/g, ' ').trim();
const countPlayersSeen = (data) => new Set([
    ...(data.players || []), ...(data.pitchers || []), ...(data.playersWithoutStats || [])
].map(p => p.playerId).filter(Boolean)).size;

const getGlobalSearchResults = (data, searchQuery, TEAM_CODE_TO_NAME = {}) => {
    if (!data || !searchQuery || searchQuery.length < 2) return { items: [], totalPlayers: 0 };
    const q = normalizeSearchText(searchQuery);
    const items = [];
    let totalPlayers = 0;
    const pushLimited = (item, type, limit) => {
        if (items.filter(r => r.type === type).length < limit) items.push(item);
    };

    // Search players (with stats context)
    const seenPlayers = new Set();
    (data.players || []).forEach(p => {
        if (p.name && normalizeSearchText(p.name).includes(q) && !seenPlayers.has(p.playerId)) {
            seenPlayers.add(p.playerId);
            totalPlayers++;
            if (items.filter(r => r.type === 'player' || r.type === 'pitcher').length < 6) {
                items.push({ type: 'player', icon: '👤', label: p.name, sub: `${p.team || ''} • ${p.games}G, ${p.avg || ''} AVG, ${p.hr || 0} HR`, tab: 'players', id: p.playerId });
            }
        }
    });
    (data.pitchers || []).forEach(p => {
        if (p.name && normalizeSearchText(p.name).includes(q) && !seenPlayers.has(p.playerId)) {
            seenPlayers.add(p.playerId);
            totalPlayers++;
            if (items.filter(r => r.type === 'player' || r.type === 'pitcher').length < 6) {
                items.push({ type: 'pitcher', icon: '⚾', label: p.name, sub: `${p.team || ''} • ${p.games}G, ${p.era || ''} ERA, ${p.so || 0} K`, tab: 'players', id: p.playerId });
            }
        }
    });

    // Search teams
    const teamRows = data.teams || [];
    teamRows.forEach(t => {
        const code = t.team || '';
        const name = TEAM_CODE_TO_NAME[code] || '';
        const text = normalizeSearchText(`${code} ${name}`);
        if (text.includes(q)) {
            pushLimited({ type: 'team', icon: '🧢', label: code, sub: `${name || 'Team'} • ${t.games || 0} games`, tab: 'venues', searchValue: code }, 'team', 4);
        }
    });

    // Search venues
    (data.stadiums || []).forEach(v => {
        const stadiumName = v.name || v.stadium || '';
        const text = normalizeSearchText(`${stadiumName} ${v.city || ''} ${v.state || ''} ${v.team || ''}`);
        if (text.includes(q)) {
            pushLimited({ type: 'venue', icon: '🏟️', label: stadiumName, sub: `${v.games || 0} games${v.city ? ` • ${v.city}` : ''}`, tab: 'venues', searchValue: stadiumName }, 'venue', 4);
        }
    });

    // Search games (by team, date, venue, score, id)
    const seenGames = new Set();
    [...(data.games || [])].sort((a, b) => toSortableDate(b.date).localeCompare(toSortableDate(a.date))).forEach(g => {
        if (items.filter(r => r.type === 'game').length >= 5) return;
        const text = normalizeSearchText(`${g.awayTeam || ''} ${g.homeTeam || ''} ${g.date || ''} ${g.venue || ''} ${g.score || ''} ${g.gameId || ''}`);
        if (text.includes(q) && !seenGames.has(g.gameId)) {
            seenGames.add(g.gameId);
            items.push({ type: 'game', icon: '📋', label: `${g.awayTeam} @ ${g.homeTeam}`, sub: `${g.date || ''} • ${g.score || ''} • ${g.venue || ''}`, tab: 'gamelog', id: g.gameId });
        }
    });

    // Search milestones
    (data.milestones || []).forEach(m => {
        if (items.filter(r => r.type === 'milestone').length >= 5) return;
        const text = normalizeSearchText(`${m.player || ''} ${m.type || ''} ${m.description || ''} ${m.detail || ''} ${m.team || ''}`);
        if (text.includes(q)) {
            items.push({ type: 'milestone', icon: '🏆', label: m.player || m.type, sub: `${m.type || ''}${m.date ? ` • ${m.date}` : ''}`, tab: 'milestones', subtab: 'milestones', searchValue: m.player || m.type || searchQuery });
        }
    });
    (data.careerFirsts || []).forEach(m => {
        if (items.filter(r => r.type === 'career').length >= 4) return;
        const text = normalizeSearchText(`${m.player_name || ''} ${m.milestone || ''} ${m.venue || ''} ${m.opponent || ''}`);
        if (text.includes(q)) {
            items.push({ type: 'career', icon: '⭐', label: m.player_name || 'Career event', sub: `${m.milestone || ''}${m.date_display ? ` • ${m.date_display}` : ''}`, tab: 'milestones', subtab: 'milestones', searchValue: m.player_name || m.milestone || searchQuery });
        }
    });
    (data.careerLasts || []).forEach(m => {
        if (items.filter(r => r.type === 'last').length >= 3) return;
        const text = normalizeSearchText(`${m.player_name || ''} ${m.milestone || ''} ${m.venue || ''} ${m.opponent || ''}`);
        if (text.includes(q)) {
            items.push({ type: 'last', icon: '🏁', label: m.player_name || 'Career last', sub: `${m.milestone || ''}${m.date_display ? ` • ${m.date_display}` : ''}`, tab: 'milestones', subtab: 'milestones', searchValue: m.player_name || m.milestone || searchQuery });
        }
    });
    (data.allTimePassings || []).forEach(p => {
        if (items.filter(r => r.type === 'history').length >= 3) return;
        const text = normalizeSearchText(`${p.player_name || ''} ${p.stat_name || ''} ${p.new_rank || ''}`);
        if (text.includes(q)) {
            items.push({ type: 'history', icon: '📈', label: p.player_name || 'All-time movement', sub: `#${p.new_rank} ${p.stat_name || ''}${p.date_display ? ` • ${p.date_display}` : ''}`, tab: 'milestones', subtab: 'history', searchValue: p.player_name || p.stat_name || searchQuery });
        }
    });

    return { items, totalPlayers };
};

const TEAM_DISPLAY_ALIASES = {NYN:'NYM',NYA:'NYY',SFN:'SF',LAN:'LAD',SDN:'SD',SLN:'STL',CHN:'CHC',CHA:'CWS',CHW:'CWS',KCA:'KC',TBA:'TB',WAS:'WSH',WSN:'WSH',ANA:'LAA',FLO:'FLA'};
const displayTeamCode = code => TEAM_DISPLAY_ALIASES[code] || code;
const franchiseTeamCode = code => ({OAK:'ATH',FLA:'MIA',MON:'WSH',CAL:'LAA'})[displayTeamCode(code)] || displayTeamCode(code);
const sameTeam = (a,b,franchise=false) => (franchise ? franchiseTeamCode(a) : displayTeamCode(a)) === (franchise ? franchiseTeamCode(b) : displayTeamCode(b));
const gameScores = game => {
    const away = game?.linescore?.away?.runs, home = game?.linescore?.home?.runs;
    if (away != null && home != null && Number.isFinite(Number(away)) && Number.isFinite(Number(home))) return {awayScore:Number(away),homeScore:Number(home)};
    const match = String(game?.score || '').match(/(?:[A-Z]+\s+)?(\d+)\s*[-–]\s*(\d+)/);
    return match ? {awayScore:Number(match[1]),homeScore:Number(match[2])} : null;
};
const canonicalVenue = (games, venue) => games.find(g => g.venue === venue)?._venueKey || venue;
const venueIdentity = (venue, aliases = {}, stadiums = []) => {
    const key = normalizeSearchText(aliases[venue] || venue);
    const stadium = stadiums.find(s => [s.name, ...(s.aliases || [])].some(name => normalizeSearchText(aliases[name] || name) === key));
    return stadium ? `stadium:${stadium.id}` : `name:${key}`;
};
'''
