import { useEffect, useState, useRef, type KeyboardEvent } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Search, ChevronDown, Shield, User } from 'lucide-react';
import { statesAndDistricts } from '../../data/mockData';
import type { Habitation } from '../../types';
import { api } from '../../lib/api';
import { useAppStore } from '../../state/AppContext';

interface TopBarProps {
  onSelectHabitation?: (habitation: Habitation) => void;
}

export function TopBar({ onSelectHabitation }: TopBarProps) {
  const {
    selectedState,
    setSelectedState,
    selectedDistrict,
    setSelectedDistrict,
    habitations,
    selectHabitation,
  } = useAppStore();

  const navigate = useNavigate();
  const location = useLocation();

  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState<number>(-1);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let mounted = true;
    api.getHealth().then((res) => {
      if (mounted) {
        setApiOnline(res.isLive && res.data.status === 'ok');
      }
    });
    return () => {
      mounted = false;
    };
  }, []);

  const currentStateData = statesAndDistricts.find((s) => s.state === selectedState);

  const searchResults = searchQuery.trim()
    ? habitations.filter(
        (h) =>
          h.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          h.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
          (h.district && h.district.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    : [];

  const handleSelect = (hab: Habitation) => {
    selectHabitation(hab);
    onSelectHabitation?.(hab);
    setSearchQuery('');
    setIsSearchFocused(false);
    setSelectedIndex(-1);
    if (location.pathname !== '/') {
      navigate('/');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (!isSearchFocused || searchResults.length === 0) {
      if (e.key === 'Escape') {
        setIsSearchFocused(false);
        setSearchQuery('');
      }
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev < searchResults.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : searchResults.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const target = selectedIndex >= 0 ? searchResults[selectedIndex] : searchResults[0];
      if (target) {
        handleSelect(target);
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setIsSearchFocused(false);
      setSearchQuery('');
      setSelectedIndex(-1);
      inputRef.current?.blur();
    }
  };

  return (
    <header className="h-12 bg-panel-bg border-b border-border-default flex items-center justify-between px-3 z-30 select-none shrink-0 text-xs">
      {/* Left: Branding & Administrative Selection */}
      <div className="flex items-center gap-3">
        {/* Brand */}
        <div className="flex items-center gap-2 pr-3 border-r border-border-default">
          <div className="w-5 h-5 bg-border-active flex items-center justify-center rounded-[2px] text-text-primary">
            <Shield className="w-3.5 h-3.5" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="font-bold tracking-wider text-text-primary text-sm font-mono">PRAYAAS</span>
            <span className="text-[10px] font-mono text-text-muted hidden sm:inline tracking-tight">
              // GEO-INTEL
            </span>
          </div>
        </div>

        {/* Administrative Region Selectors */}
        <div className="flex items-center gap-1.5">
          <span className="text-[11px] text-text-muted font-mono uppercase">AREA:</span>
          {/* State */}
          <div className="relative">
            <select
              value={selectedState}
              onChange={(e) => {
                setSelectedState(e.target.value);
                const st = statesAndDistricts.find((s) => s.state === e.target.value);
                if (st) setSelectedDistrict(st.districts[0]);
              }}
              className="appearance-none bg-panel-header border border-border-default rounded-[2px] pl-2 pr-5 py-1 text-[11px] font-medium text-text-primary cursor-pointer hover:border-border-active transition-colors focus:outline-none"
            >
              {statesAndDistricts.map((s) => (
                <option key={s.state} value={s.state} className="bg-panel-bg">
                  {s.state}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-1.5 top-1/2 -translate-y-1/2 w-3 h-3 text-text-muted pointer-events-none" />
          </div>

          <span className="text-text-muted text-[10px]">/</span>

          {/* District */}
          <div className="relative">
            <select
              value={selectedDistrict}
              onChange={(e) => setSelectedDistrict(e.target.value)}
              className="appearance-none bg-panel-header border border-border-default rounded-[2px] pl-2 pr-5 py-1 text-[11px] font-medium text-text-primary cursor-pointer hover:border-border-active transition-colors focus:outline-none"
            >
              {currentStateData?.districts.map((d) => (
                <option key={d} value={d} className="bg-panel-bg">
                  {d}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-1.5 top-1/2 -translate-y-1/2 w-3 h-3 text-text-muted pointer-events-none" />
          </div>
        </div>

        {/* Global Search */}
        <div className="relative ml-2">
          <div className="flex items-center bg-panel-header border border-border-default focus-within:border-border-active rounded-[2px] px-2 py-1 w-64 transition-colors">
            <Search className="w-3.5 h-3.5 text-text-muted mr-1.5 shrink-0" />
            <input
              ref={inputRef}
              type="text"
              placeholder="Search features, habitations, zones..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setSelectedIndex(-1);
              }}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsSearchFocused(true)}
              onBlur={() => setTimeout(() => setIsSearchFocused(false), 200)}
              className="bg-transparent text-[11px] text-text-primary placeholder:text-text-muted focus:outline-none w-full font-sans"
            />
            {searchQuery && (
              <button
                onClick={() => {
                  setSearchQuery('');
                  setSelectedIndex(-1);
                }}
                className="text-[10px] text-text-muted hover:text-text-primary"
              >
                esc
              </button>
            )}
          </div>

          {/* Search Dropdown */}
          {isSearchFocused && searchResults.length > 0 && (
            <div className="absolute top-full left-0 mt-1 w-80 bg-panel-bg border border-border-default rounded-[2px] shadow-lg py-1 z-50">
              <div className="px-2 py-1 text-[10px] font-mono text-text-muted uppercase border-b border-border-subtle flex justify-between">
                <span>Matching Habitations ({searchResults.length})</span>
                <span className="text-[9px]">↑↓ to navigate · ↵ to select</span>
              </div>
              {searchResults.slice(0, 8).map((hab, idx) => (
                <button
                  key={hab.id}
                  onClick={() => handleSelect(hab)}
                  className={`w-full flex items-center justify-between px-2.5 py-1.5 text-left transition-colors text-xs ${
                    selectedIndex === idx ? 'bg-surface-hover border-l-2 border-border-active' : 'hover:bg-surface-hover'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        hab.riskScore >= 80 ? 'bg-gis-red' : hab.riskScore >= 60 ? 'bg-gis-orange' : 'bg-gis-yellow'
                      }`}
                    />
                    <span className="font-medium text-text-primary">{hab.name}</span>
                    <span className="text-[10px] font-mono text-text-muted">{hab.id}</span>
                  </div>
                  <div className="flex items-center gap-2 text-[11px] font-mono">
                    <span className="text-text-muted">{hab.district}</span>
                    <span
                      className={
                        hab.riskScore >= 80 ? 'text-gis-red font-semibold' : 'text-text-primary'
                      }
                    >
                      {hab.riskScore}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right: Telemetry state, Timestamp, Profile */}
      <div className="flex items-center gap-4 text-[11px] font-mono">
        {/* Dataset timestamp */}
        <div className="hidden md:flex items-center gap-1.5 text-text-muted">
          <span>DATASET:</span>
          <span className="text-text-secondary tabular-nums">2026-09-28 06:00 IST</span>
        </div>

        {/* Live indicator */}
        <div className="flex items-center gap-1.5 px-2 py-0.5 bg-panel-header border border-border-subtle rounded-[2px]" title={apiOnline ? 'Backend API connected (http://localhost:8000)' : 'Standalone mode (using local prototype data)'}>
          <span
            className={`w-2 h-2 rounded-full ${
              apiOnline ? 'bg-gis-green animate-pulse' : 'bg-gis-yellow'
            }`}
          />
          <span
            className={`text-[10px] font-semibold tracking-wider ${
              apiOnline ? 'text-gis-green' : 'text-gis-yellow'
            }`}
          >
            {apiOnline ? 'API LIVE' : 'STANDALONE'}
          </span>
        </div>

        {/* Agency / Profile */}
        <div className="flex items-center gap-2 pl-3 border-l border-border-default text-text-secondary">
          <div className="w-5 h-5 bg-panel-header border border-border-default rounded-[2px] flex items-center justify-center">
            <User className="w-3 h-3 text-text-muted" />
          </div>
          <span className="text-[11px] text-text-primary font-sans hidden lg:inline">
            UK-SDMA / CHAMOLI CELL
          </span>
        </div>
      </div>
    </header>
  );
}
