"""React app chunk: player views."""

CODE = r'''const VALID_TABS = new Set(['dashboard','gamelog','players','milestones','venues','progress','special','trivia','companions','orioles']);
// Legacy tab redirects (old tab IDs -> new locations)
const TAB_REDIRECTS = { 'calendar': 'venues', 'history': 'milestones', 'leaderboards': 'players', 'matchups': 'progress' };

const App = () => {
    const parseHash = (hash) => {
        const parts = (hash || '').split('/');
        let tabId = parts[0];
        if (TAB_REDIRECTS[tabId]) tabId = TAB_REDIRECTS[tabId];
        return { tab: VALID_TABS.has(tabId) ? tabId : null, subtab: parts[1] || null };
    };

    const [tab, setTabRaw] = useState(() => {
        const { tab: t } = parseHash(window.location.hash.slice(1));
        if (t) return t;
        const saved = localStorage.getItem('baseballActiveTab');
        if (saved && VALID_TABS.has(saved)) return saved;
        if (saved && TAB_REDIRECTS[saved]) return TAB_REDIRECTS[saved];
        return 'dashboard';
    });
    const [subtab, setSubtab] = useState(() => {
        const { subtab: s } = parseHash(window.location.hash.slice(1));
        return s;
    });
    const subtabMemory = useRef({}); // Remember last subtab per tab

    const setTab = (newTab) => {
        // Save current subtab for current tab
        if (subtab) subtabMemory.current[tab] = subtab;
        setTabRaw(newTab);
        // Restore remembered subtab for the new tab (or null)
        setSubtab(subtabMemory.current[newTab] || null);
    };
    const [darkMode, setDarkMode] = useState(() => {
        const saved = localStorage.getItem('baseballDarkMode');
        if (saved !== null) return saved === 'true';
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
    });
    const [data, setData] = useState(BASEBALL_DATA);
    const [loadError, setLoadError] = useState(DATA_LOAD_ERROR);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchOpen, setSearchOpen] = useState(false);
    const [showScrollTop, setShowScrollTop] = useState(false);
    const [navCanScrollLeft, setNavCanScrollLeft] = useState(false);
    const [navCanScrollRight, setNavCanScrollRight] = useState(true);
    const searchRef = useRef(null);
    const navScrollRef = useRef(null);

    useEffect(() => {
        if (!data && !loadError) {
            window.__onDataReady = (d) => setData(d);
            window.__onDataError = (e) => setLoadError(e);
            if (BASEBALL_DATA) setData(BASEBALL_DATA);
            if (DATA_LOAD_ERROR) setLoadError(DATA_LOAD_ERROR);
        }
        return () => { window.__onDataReady = null; window.__onDataError = null; };
    }, []);

    useEffect(() => {
        localStorage.setItem('baseballActiveTab', tab);
        const hashTarget = subtab ? `${tab}/${subtab}` : tab;
        if (window.location.hash.slice(1) !== hashTarget) {
            history.replaceState(null, '', '#' + hashTarget);
        }
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }, [tab, subtab]);

    useEffect(() => {
        const onHashChange = () => {
            const { tab: t, subtab: s } = parseHash(window.location.hash.slice(1));
            if (t) { setTabRaw(t); setSubtab(s); }
        };
        window.addEventListener('hashchange', onHashChange);
        return () => window.removeEventListener('hashchange', onHashChange);
    }, []);

    useEffect(() => {
        document.documentElement.classList.toggle('dark', darkMode);
        localStorage.setItem('baseballDarkMode', darkMode);
    }, [darkMode]);

    // Global tab navigation for cross-linking from child components
    useEffect(() => {
        window.__navigateTab = (tabId, subId) => {
            let resolved = tabId;
            if (TAB_REDIRECTS[tabId]) resolved = TAB_REDIRECTS[tabId];
            if (VALID_TABS.has(resolved)) { setTabRaw(resolved); setSubtab(subId || null); }
        };
        return () => { window.__navigateTab = null; };
    }, []);

    // Scroll-to-top visibility
    useEffect(() => {
        const onScroll = () => setShowScrollTop(window.scrollY > 400);
        window.addEventListener('scroll', onScroll, { passive: true });
        return () => window.removeEventListener('scroll', onScroll);
    }, []);

    // Nav scroll indicator initialization
    useEffect(() => {
        const el = navScrollRef.current;
        if (!el) return;
        const check = () => {
            setNavCanScrollLeft(el.scrollLeft > 4);
            setNavCanScrollRight(el.scrollLeft < el.scrollWidth - el.clientWidth - 4);
        };
        check();
        window.addEventListener('resize', check);
        return () => window.removeEventListener('resize', check);
    }, [data]);

    // Keyboard shortcuts
    useEffect(() => {
        const tabIds = [...VALID_TABS];
        const onKey = (e) => {
            if (e.key === 'Escape') {
                if (searchOpen) { setSearchOpen(false); return; }
                // Close any open modal by dispatching a custom event
                window.dispatchEvent(new CustomEvent('closeModals'));
            }
            // Don't navigate tabs if user is typing in an input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') return;
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                const idx = tabIds.indexOf(tab);
                if (idx === -1) return;
                const next = e.key === 'ArrowRight' ? (idx + 1) % tabIds.length : (idx - 1 + tabIds.length) % tabIds.length;
                setTab(tabIds[next]);
            }
            // "/" focuses search
            if (e.key === '/' && !e.ctrlKey && !e.metaKey) {
                e.preventDefault();
                const input = searchRef.current?.querySelector('input');
                if (input) { input.focus(); setSearchOpen(true); }
            }
        };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, [tab, searchOpen]);

    const searchResults = useMemo(() => {
        if (!data || !searchQuery || searchQuery.length < 2) return { items: [], totalPlayers: 0 };
        const q = searchQuery.toLowerCase();
        const items = [];
        let totalPlayers = 0;
        const pushLimited = (item, type, limit) => {
            if (items.filter(r => r.type === type).length < limit) items.push(item);
        };

        // Search players (with stats context)
        const seenPlayers = new Set();
        (data.players || []).forEach(p => {
            if (p.name && p.name.toLowerCase().includes(q) && !seenPlayers.has(p.playerId)) {
                seenPlayers.add(p.playerId);
                totalPlayers++;
                if (items.filter(r => r.type === 'player' || r.type === 'pitcher').length < 6) {
                    items.push({ type: 'player', icon: '👤', label: p.name, sub: `${p.team || ''} • ${p.games}G, ${p.avg || ''} AVG, ${p.hr || 0} HR`, tab: 'players', id: p.playerId });
                }
            }
        });
        (data.pitchers || []).forEach(p => {
            if (p.name && p.name.toLowerCase().includes(q) && !seenPlayers.has(p.playerId)) {
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
            const text = `${code} ${name}`.toLowerCase();
            if (text.includes(q)) {
                pushLimited({ type: 'team', icon: '🧢', label: code, sub: `${name || 'Team'} • ${t.games || 0} games`, tab: 'venues', searchValue: code }, 'team', 4);
            }
        });

        // Search venues
        (data.stadiums || []).forEach(v => {
            const stadiumName = v.name || v.stadium || '';
            const text = `${stadiumName} ${v.city || ''} ${v.state || ''} ${v.team || ''}`.toLowerCase();
            if (text.includes(q)) {
                pushLimited({ type: 'venue', icon: '🏟️', label: stadiumName, sub: `${v.games || 0} games${v.city ? ` • ${v.city}` : ''}`, tab: 'venues', searchValue: stadiumName }, 'venue', 4);
            }
        });

        // Search games (by team, date, venue, score, id)
        const seenGames = new Set();
        (data.games || []).forEach(g => {
            if (items.filter(r => r.type === 'game').length >= 5) return;
            const text = `${g.awayTeam || ''} ${g.homeTeam || ''} ${g.date || ''} ${g.venue || ''} ${g.score || ''} ${g.gameId || ''}`.toLowerCase();
            if (text.includes(q) && !seenGames.has(g.gameId)) {
                seenGames.add(g.gameId);
                items.push({ type: 'game', icon: '📋', label: `${g.awayTeam} @ ${g.homeTeam}`, sub: `${g.date || ''} • ${g.score || ''} • ${g.venue || ''}`, tab: 'gamelog', id: g.gameId });
            }
        });

        // Search milestones
        (data.milestones || []).forEach(m => {
            if (items.filter(r => r.type === 'milestone').length >= 5) return;
            const text = `${m.player || ''} ${m.type || ''} ${m.description || ''} ${m.detail || ''} ${m.team || ''}`.toLowerCase();
            if (text.includes(q)) {
                items.push({ type: 'milestone', icon: '🏆', label: m.player || m.type, sub: `${m.type || ''}${m.date ? ` • ${m.date}` : ''}`, tab: 'milestones', searchValue: m.player || m.type || searchQuery });
            }
        });
        (data.careerFirsts || []).forEach(m => {
            if (items.filter(r => r.type === 'career').length >= 4) return;
            const text = `${m.player_name || ''} ${m.milestone || ''} ${m.venue || ''} ${m.opponent || ''}`.toLowerCase();
            if (text.includes(q)) {
                items.push({ type: 'career', icon: '⭐', label: m.player_name || 'Career event', sub: `${m.milestone || ''}${m.date_display ? ` • ${m.date_display}` : ''}`, tab: 'milestones', searchValue: m.player_name || m.milestone || searchQuery });
            }
        });
        (data.careerLasts || []).forEach(m => {
            if (items.filter(r => r.type === 'last').length >= 3) return;
            const text = `${m.player_name || ''} ${m.milestone || ''} ${m.venue || ''} ${m.opponent || ''}`.toLowerCase();
            if (text.includes(q)) {
                items.push({ type: 'last', icon: '🏁', label: m.player_name || 'Career last', sub: `${m.milestone || ''}${m.date_display ? ` • ${m.date_display}` : ''}`, tab: 'milestones', searchValue: m.player_name || m.milestone || searchQuery });
            }
        });
        (data.allTimePassings || []).forEach(p => {
            if (items.filter(r => r.type === 'history').length >= 3) return;
            const text = `${p.player_name || ''} ${p.stat_name || ''} ${p.new_rank || ''}`.toLowerCase();
            if (text.includes(q)) {
                items.push({ type: 'history', icon: '📈', label: p.player_name || 'All-time movement', sub: `#${p.new_rank} ${p.stat_name || ''}${p.date_display ? ` • ${p.date_display}` : ''}`, tab: 'milestones', subtab: 'history', searchValue: p.player_name || p.stat_name || searchQuery });
            }
        });

        return { items, totalPlayers };
    }, [data, searchQuery]);

    const handleSearchResult = (r) => {
        if (r.type === 'player' || r.type === 'pitcher') {
            window._pendingPlayerSelect = { id: r.id, name: r.label };
        }
        if (r.type === 'game') {
            window._pendingGameId = r.id;
        }
        if (['milestone', 'career', 'last', 'history'].includes(r.type)) {
            window._pendingMilestoneSearch = r.searchValue || r.label;
        }
        if (r.type === 'venue') {
            window._pendingVenueSearch = r.searchValue || r.label;
            localStorage.setItem('dt_stadiums_search', JSON.stringify(r.searchValue || r.label));
        }
        if (r.type === 'team') {
            window._pendingTeamSearch = r.searchValue || r.label;
            localStorage.setItem('dt_teams_search', JSON.stringify(r.searchValue || r.label));
        }
        if (r.subtab) {
            setSubtab(r.subtab);
            setTabRaw(r.tab);
        } else {
            setTab(r.tab);
        }
        setSearchQuery('');
        setSearchOpen(false);
    };

    useEffect(() => {
        if (!searchOpen) return;
        const handleClick = (e) => {
            if (searchRef.current && !searchRef.current.contains(e.target)) setSearchOpen(false);
        };
        document.addEventListener('mousedown', handleClick);
        return () => document.removeEventListener('mousedown', handleClick);
    }, [searchOpen]);

    if (loadError) {
        const isFileProtocol = loadError === 'file_protocol';
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
                <div className="bg-white rounded-xl shadow-lg p-8 max-w-lg text-center">
                    <h2 className="text-xl font-bold text-slate-800 mb-4">{isFileProtocol ? 'Local File Access' : 'Failed to Load Data'}</h2>
                    {isFileProtocol ? (
                        <div className="text-left text-slate-600 space-y-3">
                            <p>This page needs a local server to load data. Run one of these from the folder containing this file:</p>
                            <pre className="bg-slate-100 p-3 rounded text-sm overflow-x-auto">python3 -m http.server 8000</pre>
                            <p>Then open <a href="http://localhost:8000" className="text-blue-600 underline">http://localhost:8000</a></p>
                        </div>
                    ) : (
                        <p className="text-slate-600">{loadError}</p>
                    )}
                </div>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
                <div className="text-center">
                    <div className="inline-block w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full" style={{ animation: 'spin 1s linear infinite' }}></div>
                    <p className="mt-4 text-lg font-medium text-slate-600">Loading baseball data...</p>
                </div>
            </div>
        );
    }

    const tabs = [
        { id: 'dashboard', label: 'Dashboard' },
        { id: 'gamelog', label: 'Games' },
        { id: 'players', label: 'Players' },
        { id: 'milestones', label: 'Milestones' },
        { id: 'venues', label: 'Venues' },
        { id: 'progress', label: 'Progress' },
        { id: 'special', label: 'Special' },
        { id: 'trivia', label: 'Frivolities' },
        { id: 'companions', label: 'With' },
        { id: 'orioles', label: 'Orioles' },
    ];
    
    return (
        <div className={`min-h-screen ${darkMode ? 'bg-slate-950' : 'bg-slate-50'}`}>
            <header className={`${darkMode ? 'bg-slate-900' : 'bg-white'} border-b ${darkMode ? 'border-slate-800' : 'border-slate-200'}`}>
                <div className="max-w-7xl mx-auto px-4 py-3 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
                    <div>
                        <h1 className={`text-base sm:text-lg font-bold tracking-tight ${darkMode ? 'text-white' : 'text-slate-900'}`}>Baseball Statistics Portal</h1>
                        <p className={`text-xs mt-0.5 ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>{data.games?.length || 0} games attended • {new Set([...(data.players || []).map(p => p.playerId), ...(data.pitchers || []).map(p => p.playerId), ...(data.playersWithoutStats || []).map(p => p.playerId)]).size} players seen</p>
                    </div>
                    <div className="flex items-center gap-3">
                        <div ref={searchRef} role="search" className="relative flex-1 sm:flex-none">
                            <input
                                type="text"
                                placeholder="Search..."
                                aria-label="Search players, games, and milestones"
                                value={searchQuery}
                                onChange={(e) => { setSearchQuery(e.target.value); setSearchOpen(true); }}
                                onFocus={() => setSearchOpen(true)}
                                className={`w-full sm:w-48 md:w-64 px-3 py-2 rounded-lg text-sm transition-colors border ${darkMode ? 'bg-slate-700 border-slate-600 text-white placeholder-slate-400 focus:border-blue-500' : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-400 focus:border-blue-500'} outline-none`}
                            />
                            {searchOpen && searchQuery.length >= 2 && (
                                <div className={`absolute top-full right-0 mt-1 w-80 sm:w-96 rounded-lg shadow-md border z-[60] max-h-96 overflow-y-auto ${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-200'}`}>
                                    {searchResults.items.length === 0 ? (
                                        <div className={`px-4 py-6 text-center text-sm ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>No results for "{searchQuery}"</div>
                                    ) : (<>
                                        {searchResults.items.map((r, i) => {
                                            const q = searchQuery.toLowerCase();
                                            const idx = r.label.toLowerCase().indexOf(q);
                                            const highlighted = idx >= 0 ? <>{r.label.slice(0, idx)}<span className="bg-yellow-200 text-yellow-900 rounded px-0.5">{r.label.slice(idx, idx + searchQuery.length)}</span>{r.label.slice(idx + searchQuery.length)}</> : r.label;
                                            return (
                                                <button key={`search-${r.type}-${r.id || r.label}-${i}`} onClick={() => handleSearchResult(r)}
                                                    className={`w-full text-left px-4 py-2 flex items-center gap-3 transition-colors ${darkMode ? 'hover:bg-slate-700 text-slate-200' : 'hover:bg-blue-50 text-slate-800'}`}>
                                                    <span className="text-lg shrink-0 w-6 text-center">{r.icon || '•'}</span>
                                                    <span className="text-xs font-medium uppercase opacity-50 w-16 shrink-0">{r.type}</span>
                                                    <div className="min-w-0">
                                                        <div className="text-sm font-medium truncate">{highlighted}</div>
                                                        {r.sub && <div className={`text-xs truncate ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>{r.sub}</div>}
                                                    </div>
                                                </button>
                                            );
                                        })}
                                        {searchResults.totalPlayers > 6 && (
                                            <button onClick={() => { window._pendingPlayerSearch = searchQuery; setTab('players'); setSearchQuery(''); setSearchOpen(false); }}
                                                className={`w-full text-center px-4 py-2 text-xs font-medium border-t transition-colors ${darkMode ? 'text-blue-400 border-slate-700 hover:bg-slate-700' : 'text-blue-600 border-slate-100 hover:bg-blue-50'}`}>
                                                View all {searchResults.totalPlayers} player matches
                                            </button>
                                        )}
                                    </>)}
                                </div>
                            )}
                        </div>
                        <button
                            onClick={() => setDarkMode(!darkMode)}
                            className={`px-3 py-2 rounded-lg transition-colors border ${darkMode ? 'bg-slate-700 border-slate-600 hover:bg-slate-600 text-white' : 'bg-slate-50 border-slate-300 hover:bg-slate-100 text-slate-700'}`}
                            title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
                        >
                            {darkMode ? '☀️' : '🌙'}
                        </button>
                    </div>
                </div>
            </header>
            <nav className={`sticky top-0 z-50 ${darkMode ? 'bg-slate-900 border-b border-slate-800' : 'bg-white border-b border-slate-200'}`} style={{ boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.04)' }}>
                <div className="max-w-7xl mx-auto px-2 sm:px-4">
                    <div className="relative">
                        <div ref={navScrollRef} className="flex overflow-x-auto" role="tablist" aria-label="Main navigation" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none', WebkitOverflowScrolling: 'touch' }}
                            onScroll={(e) => {
                                const el = e.target;
                                setNavCanScrollLeft(el.scrollLeft > 4);
                                setNavCanScrollRight(el.scrollLeft < el.scrollWidth - el.clientWidth - 4);
                            }}>
                            {tabs.map(t => (
                                <button key={t.id} role="tab" aria-selected={tab === t.id} onClick={() => setTab(t.id)} className={`px-3 sm:px-4 py-2.5 text-xs sm:text-[13px] whitespace-nowrap flex-shrink-0 border-b-2 transition-colors ${
                                    tab === t.id
                                        ? (darkMode ? 'text-blue-400 border-blue-400 font-semibold' : 'text-blue-700 border-blue-700 font-semibold')
                                        : (darkMode ? 'text-slate-400 hover:text-slate-200 border-transparent' : 'text-slate-500 hover:text-slate-800 border-transparent')
                                }`}>
                                    {t.label}
                                </button>
                            ))}
                        </div>
                        {navCanScrollLeft && <div className="absolute left-0 top-0 bottom-0 w-8 pointer-events-none" style={{ background: `linear-gradient(to right, ${darkMode ? '#0f172a' : '#ffffff'}, transparent)` }} />}
                        {navCanScrollRight && <div className="absolute right-0 top-0 bottom-0 w-8 pointer-events-none" style={{ background: `linear-gradient(to left, ${darkMode ? '#0f172a' : '#ffffff'}, transparent)` }} />}
                    </div>
                </div>
            </nav>
            <main role="tabpanel" className="max-w-7xl mx-auto px-2 sm:px-4 py-4 sm:py-8">
                {tab === 'dashboard' && <Dashboard data={data} onTabChange={setTab} />}
                {tab === 'gamelog' && (data.games?.length ? <GameLogWithDetails games={data.games} playerGames={data.playerGames || []} pitcherGames={data.pitcherGames || []} careerFirstsByGame={data.careerFirstsByGame || {}} allTimePassingsByGame={data.allTimePassingsByGame || {}} /> : <EmptyState icon="📋" title="No Games" message="Add game HTML files to the Current Season Games folder and run the processor." />)}
                {tab === 'players' && <PlayersTabV2 data={data} initialSubtab={subtab} onSubtabChange={setSubtab} />}
                {tab === 'milestones' && <MilestonesTabV2 data={data} onTabChange={setTab} initialSubtab={subtab} onSubtabChange={setSubtab} />}
                {tab === 'venues' && <VenuesTab data={data} initialSubtab={subtab} onSubtabChange={setSubtab} />}
                {tab === 'progress' && <ProgressTab data={data} initialSubtab={subtab} onSubtabChange={setSubtab} />}
                {tab === 'special' && <SpecialTab data={data} initialSubtab={subtab} onSubtabChange={setSubtab} />}
                {tab === 'trivia' && <TriviaTab umpireLog={data.umpireLog || []} jerseyLog={data.jerseyLog || {}} firstRoundDraftPicks={data.firstRoundDraftPicks || {}} playerBios={data.playerBios || {}} players={data.players || []} pitchers={data.pitchers || []} games={data.games || []} playerGames={data.playerGames || []} pitcherGames={data.pitcherGames || []} initialSubtab={subtab} onSubtabChange={setSubtab} />}
                {tab === 'companions' && <CompanionsView companionData={data.companionData} />}
                {tab === 'orioles' && <OriolesDashboard orioles={data.orioles || []} games={data.games || []} />}
            </main>
            <footer className={`border-t mt-8 ${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'}`}>
                <div className="max-w-7xl mx-auto px-4 py-5 flex items-center justify-between">
                    <p className={`small-text ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
                        Baseball Statistics Portal
                    </p>
                    {data.generatedAt && <p className={`small-text ${darkMode ? 'text-slate-600' : 'text-slate-300'}`}>{data.generatedAt}</p>}
                </div>
            </footer>
            {showScrollTop && (
                <button
                    onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                    className={`fixed bottom-6 right-6 w-10 h-10 rounded-full shadow-lg flex items-center justify-center transition-all z-50 ${darkMode ? 'bg-slate-700 hover:bg-slate-600 text-white' : 'bg-blue-600 hover:bg-blue-700 text-white'}`}
                    title="Scroll to top"
                    aria-label="Scroll to top"
                >
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 3L3 8h3v5h4V8h3L8 3z" fill="currentColor"/></svg>
                </button>
            )}
        </div>
    );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<ErrorBoundary><App /></ErrorBoundary>);
'''
