"""React app chunk: player views."""

CODE = r'''const VALID_TABS = new Set(['dashboard','gamelog','players','milestones','venues','progress','special','trivia','companions','orioles']);
// Legacy tab redirects (old tab IDs -> new locations)
const TAB_REDIRECTS = { 'games': 'gamelog', 'calendar': 'venues', 'history': 'milestones', 'leaderboards': 'players', 'matchups': 'progress' };

const App = () => {
    const route = usePassportRoute();
    const tab = VALID_TABS.has(route.tab) ? route.tab : (TAB_REDIRECTS[route.tab] || 'dashboard');
    const subtab = route.subtab;
    const setTab = (newTab, requestedSubtab) => navigatePassport({tab:newTab,subtab:requestedSubtab||null,game:null,player:null,q:null});
    const setTabRaw = newTab => navigatePassport({tab:newTab,game:null,player:null});
    const setSubtab = subtab => navigatePassport({subtab,game:null,player:null});
    const [darkMode, setDarkMode] = useState(() => {
        const saved = localStorage.getItem('baseballDarkMode');
        if (saved !== null) return saved === 'true';
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
    });
    const [rawData, setData] = useState(BASEBALL_DATA);
    const scoped = (tab==='dashboard'&&[null,'','recap','discover'].includes(subtab)) || ['gamelog','milestones'].includes(tab) || (tab==='players' && ['hitters','pitchers','leaders','leaderboards',null].includes(subtab));
    const data = useMemo(()=>scoped?scopePassportData(rawData,route):rawData,[rawData,JSON.stringify(route),scoped]);
    const keys=passportKeysForRoute(route);
    const [sectionError,setSectionError]=useState('');
    const [sectionRetry,setSectionRetry]=useState(0);
    const [loadingSection,setLoadingSection]=useState(false);
    const ready=!!rawData && window.passportKeysLoaded(keys);
    useEffect(()=>{
        if(!rawData)return;
        let live=true;setSectionError('');
        if(window.passportKeysLoaded(keys)){setLoadingSection(false);return;}
        setLoadingSection(true);
        window.loadPassportKeys(keys).then(()=>{if(live)setLoadingSection(false);}).catch(e=>{if(live){setLoadingSection(false);setSectionError(e.message);}});
        return()=>{live=false;};
    },[!!rawData,JSON.stringify(keys),sectionRetry]);
    const [loadError, setLoadError] = useState(DATA_LOAD_ERROR);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchOpen, setSearchOpen] = useState(false);
    const [showScrollTop, setShowScrollTop] = useState(false);
    const [navCanScrollLeft, setNavCanScrollLeft] = useState(false);
    const [navCanScrollRight, setNavCanScrollRight] = useState(true);
    const searchRef = useRef(null);
    const navScrollRef = useRef(null);

    useEffect(() => {
        window.__onDataReady=setData;window.__onDataError=setLoadError;
        if(BASEBALL_DATA)setData(BASEBALL_DATA);
        if(DATA_LOAD_ERROR)setLoadError(DATA_LOAD_ERROR);
        return()=>{window.__onDataReady=null;window.__onDataError=null;};
    },[]);

    useEffect(() => {
        document.documentElement.classList.toggle('dark', darkMode);
        localStorage.setItem('baseballDarkMode', darkMode);
    }, [darkMode]);

    useEffect(()=>{
        window.__navigateTab=(id,subtab)=>navigatePassport({tab:TAB_REDIRECTS[id]||id,subtab:subtab||null,game:null,player:null});
        return()=>{window.__navigateTab=null;};
    },[]);

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
            if (e.defaultPrevented || dialogStack.length) return;
            if (e.key === 'Escape') {
                if (searchOpen) { setSearchOpen(false); searchRef.current?.querySelector('input')?.focus(); return; }

            }
            // Don't navigate tabs if user is typing in an input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') return;
            if ((e.key === 'ArrowLeft' || e.key === 'ArrowRight') && e.target.closest('[aria-label="Main navigation"][role="tablist"]')) {
                const idx = tabIds.indexOf(tab);
                if (idx === -1) return;
                const next = e.key === 'ArrowRight' ? (idx + 1) % tabIds.length : (idx - 1 + tabIds.length) % tabIds.length;
                e.preventDefault();
                setTab(tabIds[next]);
                navScrollRef.current?.querySelectorAll('[role="tab"]')[next]?.focus();
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
        const all=rawData?passportSearch(rawData,searchQuery):[];
        return {items:all.slice(0,10),total:all.length,totalPlayers:0};
    },[rawData,searchQuery]);

    useEffect(() => {
        if(searchQuery.trim().length < 2) return;
        const timer=setTimeout(()=>window.loadPassportKeys(['searchEvents']).catch(()=>{}),200);
        return ()=>clearTimeout(timer);
    },[searchQuery]);

    const handleSearchResult = (r) => {
        if (searchOpen && searchQuery) navigatePassport({tab:'dashboard',subtab:'search',q:searchQuery,game:null,player:null});
        if(r.type==='player'||r.type==='pitcher')openPassportPlayer(r.id);
        else if(r.type==='game')requestGameDetails(r.id);
        else if(r.gameId)requestGameDetails(r.gameId);
        else if(r.type==='team')navigatePassport({tab:'gamelog',subtab:null,team:r.searchValue,game:null,player:null});
        else if(r.type==='venue')navigatePassport({tab:'gamelog',subtab:null,venue:r.searchValue,game:null,player:null});
        else {
            if(['milestone','career','last','history'].includes(r.type))window._pendingMilestoneSearch=r.searchValue||r.label;
            navigatePassport({tab:r.tab,subtab:r.subtab||null,game:null,player:null});
        }
        setSearchQuery('');setSearchOpen(false);
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
        { id: 'companions', label: 'Companions' },
        { id: 'orioles', label: 'Orioles' },
    ];
    
    return (
        <div className={`min-h-screen ${darkMode ? 'bg-slate-950' : 'bg-slate-50'}`}>
            <header className={`${darkMode ? 'bg-slate-900' : 'bg-white'} border-b ${darkMode ? 'border-slate-800' : 'border-slate-200'}`}>
                <div className="max-w-7xl mx-auto px-4 py-3 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
                    <div>
                        <h1 className={`page-title ${darkMode ? 'text-white' : 'text-slate-900'}`}>MLB Game Passport</h1>
                        <p className={`text-xs mt-0.5 ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>{data.games?.length || 0} games attended • {passportMetrics(data.games||[]).players.toLocaleString()} players seen</p>
                    </div>
                    <div className="flex items-center gap-3">
                        <div ref={searchRef} role="search" onKeyDown={(e) => {
                            if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
                            const buttons = [...searchRef.current.querySelectorAll('[data-search-result]')];
                            if (!buttons.length) return;
                            e.preventDefault();
                            const index = buttons.indexOf(document.activeElement);
                            const next = index < 0 ? (e.key === 'ArrowDown' ? 0 : buttons.length - 1) : (index + (e.key === 'ArrowDown' ? 1 : -1) + buttons.length) % buttons.length;
                            buttons[next].focus();
                        }} className="relative flex-1 sm:flex-none">
                            <input
                                type="text"
                                placeholder="Search players, games, milestones"
                                aria-label="Search players, games, and milestones"
                                aria-expanded={searchOpen && searchQuery.length >= 2}
                                aria-controls="global-search-results"
                                value={searchQuery}
                                onChange={(e) => { setSearchQuery(e.target.value); setSearchOpen(true); }}
                                onFocus={() => setSearchOpen(true)}
                                onKeyDown={e=>{if(e.key==='Enter'){e.preventDefault();navigatePassport({tab:'dashboard',subtab:'search',q:searchQuery,game:null,player:null});setSearchOpen(false);}}}
	                            className={`min-h-11 w-full sm:w-56 md:w-72 px-3 py-2 rounded-lg text-sm transition-colors border ${darkMode ? 'bg-slate-700 border-slate-600 text-white placeholder-slate-400 focus:border-blue-500' : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-400 focus:border-blue-500'} outline-none`}
                            />
                            {searchOpen && searchQuery.length >= 2 && (
                                <div id="global-search-results" aria-label="Search results" className={`absolute top-full right-0 mt-1 w-80 sm:w-96 rounded-lg shadow-md border z-[60] max-h-96 overflow-y-auto ${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-200'}`}>
                                    {searchResults.items.length === 0 ? (
                                        <div className={`px-4 py-6 text-center text-sm ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>No results for "{searchQuery}"</div>
                                    ) : (<>
                                        {searchResults.items.map((r, i) => {
                                            const q = searchQuery.toLowerCase();
                                            const idx = r.label.toLowerCase().indexOf(q);
                                            const highlighted = idx >= 0 ? <>{r.label.slice(0, idx)}<span className="bg-yellow-200 text-yellow-900 rounded px-0.5">{r.label.slice(idx, idx + searchQuery.length)}</span>{r.label.slice(idx + searchQuery.length)}</> : r.label;
                                            return (
                                                <button data-search-result="true" key={`search-${r.type}-${r.id || r.label}-${i}`} onClick={() => handleSearchResult(r)}
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
                                            <button data-search-result="true" onClick={() => { window._pendingPlayerSearch = searchQuery; setTab('players', 'hitters'); setSearchQuery(''); setSearchOpen(false); }}
                                                className={`w-full text-center px-4 py-2 text-xs font-medium border-t transition-colors ${darkMode ? 'text-blue-400 border-slate-700 hover:bg-slate-700' : 'text-blue-600 border-slate-100 hover:bg-blue-50'}`}>
                                                Filter hitter and pitcher tables ({searchResults.totalPlayers} matches)
                                            </button>
                                        )}
                                        <button data-search-result="true" className="passport-button w-full" onClick={()=>{navigatePassport({tab:'dashboard',subtab:'search',q:searchQuery,game:null,player:null});setSearchOpen(false);}}>See all {searchResults.total} results</button>
                                    </>)}
                                </div>
                            )}
                        </div>
	                        <button
	                            onClick={() => setDarkMode(!darkMode)}
	                            className={`min-h-11 min-w-11 inline-flex items-center justify-center rounded-lg transition-colors border ${darkMode ? 'bg-slate-700 border-slate-600 hover:bg-slate-600 text-white' : 'bg-slate-50 border-slate-300 hover:bg-slate-100 text-slate-700'}`}
	                            title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
	                            aria-label={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
	                        >
	                            {darkMode ? (
	                                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="2"/><path d="M12 2v3M12 19v3M4.93 4.93l2.12 2.12M16.95 16.95l2.12 2.12M2 12h3M19 12h3M4.93 19.07l2.12-2.12M16.95 7.05l2.12-2.12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
	                            ) : (
	                                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M21 14.2A8.2 8.2 0 0 1 9.8 3a7.7 7.7 0 1 0 11.2 11.2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
	                            )}
	                        </button>
                    </div>
                </div>
            </header>
            <nav className={`sticky top-0 z-50 ${darkMode ? 'bg-slate-900 border-b border-slate-800' : 'bg-white border-b border-slate-200'}`} style={{ boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.04)' }}>
                <div className="max-w-7xl mx-auto px-2 sm:px-4">
	                    <div className="sm:hidden py-2">
	                        <select
	                            value={tab}
	                            aria-label="Main navigation"
	                            onChange={(e) => setTab(e.target.value)}
	                            className={`w-full min-h-11 rounded-lg border px-3 py-2 body-text font-semibold ${darkMode ? 'bg-slate-800 border-slate-700 text-slate-100' : 'bg-white border-slate-300 text-slate-900'}`}
	                        >
	                            {tabs.map(t => <option key={t.id} value={t.id}>{t.label}</option>)}
	                        </select>
	                    </div>
	                    <div className="relative hidden sm:block">
	                        <div ref={navScrollRef} className="flex overflow-x-auto" role="tablist" aria-label="Main navigation" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none', WebkitOverflowScrolling: 'touch' }}
                            onScroll={(e) => {
                                const el = e.target;
                                setNavCanScrollLeft(el.scrollLeft > 4);
                                setNavCanScrollRight(el.scrollLeft < el.scrollWidth - el.clientWidth - 4);
                            }}>
                            {tabs.map(t => (
	                                <button key={t.id} role="tab" aria-selected={tab === t.id} onClick={() => setTab(t.id)} className={`px-4 py-3 text-[13px] whitespace-nowrap flex-shrink-0 border-b-2 transition-colors ${
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
                <PassportScope data={rawData} route={route}/>
                {!scoped && <p className="text-sm text-slate-500 mb-3">Lifetime archive · this collection does not use the Browse scope.</p>}
                {!ready ? <section className="passport-panel" role="status"><p>{sectionError||'Loading this section…'}</p>{sectionError&&<div className="flex gap-2 mt-3"><button className="passport-button" onClick={()=>setSectionRetry(sectionRetry+1)}>Retry section</button><button className="passport-button" onClick={()=>location.reload()}>Reload site</button></div>}</section> : <>
                {tab === 'dashboard' && <PassportDashboard data={data} allData={rawData} route={route} onResult={handleSearchResult} />}
                {tab === 'gamelog' && (data.games?.length ? <GameLogWithDetails games={data.games} playerGames={data.playerGames || []} pitcherGames={data.pitcherGames || []} careerFirstsByGame={data.careerFirstsByGame || {}} allTimePassingsByGame={data.allTimePassingsByGame || {}} debuts={data.debuts || []} finalGames={data.finalGames || []} /> : <EmptyState icon="📋" title="No Games" message="Add game HTML files to the Current Season Games folder and run the processor." />)}
                {tab === 'players' && <PlayersTabV2 data={data} initialSubtab={subtab} onSubtabChange={setSubtab} />}
                {tab === 'milestones' && <MilestonesTabV2 data={data} onTabChange={setTab} initialSubtab={subtab} onSubtabChange={setSubtab} />}
                {tab === 'venues' && <VenuesTab data={data} initialSubtab={subtab} onSubtabChange={setSubtab} />}
                {tab === 'progress' && <ProgressTab data={data} initialSubtab={subtab} onSubtabChange={setSubtab} />}
                {tab === 'special' && <SpecialTab data={data} initialSubtab={subtab} onSubtabChange={setSubtab} />}
                {tab === 'trivia' && <TriviaTab umpireLog={data.umpireLog || []} jerseyLog={data.jerseyLog || {}} firstRoundDraftPicks={data.firstRoundDraftPicks || {}} playerBios={data.playerBios || {}} players={data.players || []} pitchers={data.pitchers || []} games={subtab==='home-away'?(data.homeAwayGames||data.games||[]):(data.games || [])} playerGames={data.playerGames || []} pitcherGames={data.pitcherGames || []} stadiumAliases={data.stadiumAliases || {}} initialSubtab={subtab} onSubtabChange={setSubtab} />}
                {tab === 'companions' && <CompanionsView companionData={data.companionData} />}
                {tab === 'orioles' && <OriolesDashboard orioles={data.orioles || []} games={data.games || []} />}
                </>}
                {ready&&(route.player||route.game)&&<PassportEntity route={route} data={rawData}/>}
            </main>
            <footer className={`border-t mt-8 ${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'}`}>
                <div className="max-w-7xl mx-auto px-4 py-5 flex items-center justify-between">
                    <p className={`small-text ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
	                        MLB Game Passport
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
