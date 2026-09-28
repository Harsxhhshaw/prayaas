import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowUpRight, Satellite, Cloud, Globe, Radio, Database, CheckCircle2, AlertTriangle, RefreshCw } from 'lucide-react';
import { api } from '../lib/api';
import type { DataSourceFreshnessItem } from '../types';

export function DataSources() {
  const navigate = useNavigate();
  const [sources, setSources] = useState<DataSourceFreshnessItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [staleCount, setStaleCount] = useState(0);

  const loadData = () => {
    setLoading(true);
    api.getDataSourcesFreshness().then((res) => {
      if (res.data?.items) {
        setSources(res.data.items);
        setStaleCount(res.data.stale_count);
      }
      setLoading(false);
    }).catch(() => {
      setLoading(false);
    });
  };

  useEffect(() => {
    loadData();
  }, []);

  const formatRefresh = (secs?: number | null) => {
    if (!secs) return 'Manual / Static';
    if (secs < 3600) return `${Math.round(secs / 60)} min`;
    if (secs < 86400) return `${Math.round(secs / 3600)} hr`;
    return `${Math.round(secs / 86400)} days`;
  };

  return (
    <div className="h-full flex flex-col bg-workspace text-text-primary p-4 overflow-hidden select-none font-sans">
      <div className="flex items-center justify-between pb-3 border-b border-border-default shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-bold font-mono uppercase tracking-wider text-text-primary">
              GEOSPATIAL DATA PIPELINE & FRESHNESS TELEMETRY
            </h1>
            <span className="text-[10px] font-mono px-1.5 py-0.5 bg-gis-green/10 border border-gis-green/30 text-gis-green rounded-[2px] font-bold">
              {sources.length - staleCount} OF {sources.length} FEEDS CURRENT
            </span>
            {staleCount > 0 && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 bg-gis-orange/10 border border-gis-orange/30 text-gis-orange rounded-[2px] font-bold">
                {staleCount} STALE / AGING
              </span>
            )}
          </div>
          <p className="text-xs text-text-muted font-mono mt-0.5">
            Real-time synchronization status, ingestion provenance, and update SLA telemetry across all external data providers.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            className="px-2.5 py-1 bg-panel-header hover:bg-surface-hover border border-border-default rounded-[2px] text-[11px] font-mono text-text-secondary transition-colors flex items-center gap-1.5"
            title="Refresh Telemetry"
          >
            <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
            <span>POLL FRESHNESS</span>
          </button>
          <button
            onClick={() => navigate('/')}
            className="px-2.5 py-1 bg-surface-active hover:bg-border-active border border-border-default rounded-[2px] text-[11px] font-mono text-text-primary transition-colors flex items-center gap-1.5"
          >
            <span>MAP WORKSTATION</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto mt-3 border border-border-default rounded-[2px] bg-panel-bg">
        <table className="w-full text-left border-collapse text-xs font-mono">
          <thead className="sticky top-0 bg-panel-header text-[10px] uppercase tracking-wider text-text-muted border-b border-border-default z-10">
            <tr>
              <th className="py-2 px-3">Feed Identifier</th>
              <th className="py-2 px-3">Data Provider & Source</th>
              <th className="py-2 px-3">Dataset Classification</th>
              <th className="py-2 px-3 text-center">Data Mode</th>
              <th className="py-2 px-3">Expected Cadence</th>
              <th className="py-2 px-3">Last Ingestion</th>
              <th className="py-2 px-3 text-center">Freshness SLA</th>
              <th className="py-2 px-3 text-center">Operational State</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle text-[11px]">
            {sources.map((feed) => (
              <tr key={feed.id} className="hover:bg-surface-hover text-text-secondary transition-colors">
                <td className="py-2.5 px-3 text-text-muted font-bold">{feed.id}</td>
                <td className="py-2.5 px-3">
                  <div className="font-semibold text-text-primary">{feed.name}</div>
                  <div className="text-[10px] text-text-muted">{feed.provider}</div>
                </td>
                <td className="py-2.5 px-3 text-[10px] text-text-secondary">
                  <span className="px-1.5 py-0.5 bg-panel-header border border-border-subtle rounded-[1px]">
                    {feed.type}
                  </span>
                </td>
                <td className="py-2.5 px-3 text-center">
                  <span
                    className={`px-1.5 py-0.5 rounded-[1px] text-[9px] font-bold uppercase tracking-wider ${
                      feed.dataMode === 'LIVE'
                        ? 'bg-gis-green/15 text-gis-green border border-gis-green/40'
                        : feed.dataMode === 'PUBLIC'
                        ? 'bg-gis-blue/15 text-gis-blue border border-gis-blue/40'
                        : 'bg-panel-header text-text-muted border border-border-subtle'
                    }`}
                  >
                    {feed.dataMode}
                  </span>
                </td>
                <td className="py-2.5 px-3 text-text-secondary">
                  {formatRefresh(feed.expectedRefreshSeconds)}
                </td>
                <td className="py-2.5 px-3 tabular-nums text-text-muted text-[10px]">
                  {feed.lastSuccessfulIngestion ? new Date(feed.lastSuccessfulIngestion).toLocaleString() : 'Never'}
                </td>
                <td className="py-2.5 px-3 text-center">
                  <span
                    className={`px-1.5 py-0.5 rounded-[1px] text-[9px] font-bold uppercase tracking-wider ${
                      feed.freshness === 'CURRENT'
                        ? 'bg-gis-green/10 text-gis-green border border-gis-green/30'
                        : feed.freshness === 'AGING'
                        ? 'bg-gis-orange/10 text-gis-orange border border-gis-orange/30'
                        : 'bg-gis-red/10 text-gis-red border border-gis-red/30'
                    }`}
                  >
                    {feed.freshness}
                  </span>
                </td>
                <td className="py-2.5 px-3 text-center">
                  {!feed.isStale ? (
                    <span className="px-1.5 py-0.5 bg-gis-green/10 border border-gis-green/30 text-gis-green text-[9px] font-bold uppercase rounded-[1px] inline-flex items-center gap-1">
                      <CheckCircle2 className="w-2.5 h-2.5" />
                      ACTIVE
                    </span>
                  ) : (
                    <span className="px-1.5 py-0.5 bg-gis-orange/10 border border-gis-orange/30 text-gis-orange text-[9px] font-bold uppercase rounded-[1px] inline-flex items-center gap-1">
                      <AlertTriangle className="w-2.5 h-2.5" />
                      STALE
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

