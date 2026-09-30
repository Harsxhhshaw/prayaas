import { useNavigate } from 'react-router-dom';
import { ArrowUpRight, Shield, Globe, Sliders, Server, Bell, Cpu } from 'lucide-react';

export function SettingsPage() {
  const navigate = useNavigate();

  return (
    <div className="h-full flex flex-col bg-workspace text-text-primary p-4 overflow-hidden select-none font-sans">
      <div className="flex items-center justify-between pb-3 border-b border-border-default shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-bold font-mono uppercase tracking-wider text-text-primary">
              GEOSPATIAL PLATFORM CONFIGURATION & PREFERENCES
            </h1>
            <span className="text-[10px] font-mono px-1.5 py-0.5 bg-panel-header border border-border-default text-text-muted rounded-[2px]">
              RELEASE v1.0.4-PROD
            </span>
          </div>
          <p className="text-xs text-text-muted font-mono mt-0.5">
            Coordinate systems, multi-hazard risk thresholds, data refresh rates, and role credentials.
          </p>
        </div>

        <button
          onClick={() => navigate('/')}
          className="px-2.5 py-1 bg-surface-active hover:bg-border-active border border-border-default rounded-[2px] text-[11px] font-mono text-text-primary transition-colors flex items-center gap-1.5"
        >
          <span>MAP WORKSTATION</span>
          <ArrowUpRight className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-3 mt-3 flex-1 overflow-y-auto font-mono text-xs">
        {/* Section 1: Spatial Projections & Basemaps */}
        <div className="bg-panel-bg border border-border-default p-3 rounded-[2px] space-y-2">
          <div className="text-[10px] text-text-muted uppercase font-bold flex items-center gap-1.5 pb-1 border-b border-border-subtle">
            <Globe className="w-3.5 h-3.5 text-gis-blue" />
            <span>COORDINATE REFERENCE SYSTEMS (CRS)</span>
          </div>
          <div className="space-y-1 text-[11px] text-text-secondary">
            <div className="flex justify-between py-1">
              <span>Primary Display CRS:</span>
              <span className="text-text-primary">EPSG:4326 (WGS 84 / Geographic)</span>
            </div>
            <div className="flex justify-between py-1 border-t border-border-subtle">
              <span>Hydrologic Projected Grid:</span>
              <span className="text-text-primary">EPSG:32644 (UTM Zone 44N)</span>
            </div>
            <div className="flex justify-between py-1 border-t border-border-subtle">
              <span>Basemap Default Provider:</span>
              <span className="text-gis-green">Esri Dark Gray Canvas (High Reliability)</span>
            </div>
          </div>
        </div>

        {/* Section 2: Hazard Alert Thresholds */}
        <div className="bg-panel-bg border border-border-default p-3 rounded-[2px] space-y-2">
          <div className="text-[10px] text-text-muted uppercase font-bold flex items-center gap-1.5 pb-1 border-b border-border-subtle">
            <Sliders className="w-3.5 h-3.5 text-gis-red" />
            <span>HAZARD SEVERITY THRESHOLDS</span>
          </div>
          <div className="space-y-1 text-[11px] text-text-secondary">
            <div className="flex justify-between py-1">
              <span>Critical Red Zone Score Cutoff:</span>
              <span className="text-gis-red font-bold">≥ 80.0 / 100</span>
            </div>
            <div className="flex justify-between py-1 border-t border-border-subtle">
              <span>Immediate Relocation Trigger:</span>
              <span className="text-gis-red font-bold">≥ 82.0 Composite Index</span>
            </div>
            <div className="flex justify-between py-1 border-t border-border-subtle">
              <span>Subsidence Escalation Rate:</span>
              <span className="text-gis-orange font-bold">&gt; 3.0 mm / month</span>
            </div>
          </div>
        </div>

        {/* Section 3: Telemetry Refresh Rates */}
        <div className="bg-panel-bg border border-border-default p-3 rounded-[2px] space-y-2">
          <div className="text-[10px] text-text-muted uppercase font-bold flex items-center gap-1.5 pb-1 border-b border-border-subtle">
            <Server className="w-3.5 h-3.5 text-gis-green" />
            <span>TELEMETRY INGESTION CYCLES</span>
          </div>
          <div className="space-y-1 text-[11px] text-text-secondary">
            <div className="flex justify-between py-1">
              <span>IMD Radar Precipitation Poll:</span>
              <span className="text-text-primary">900 seconds (15 min)</span>
            </div>
            <div className="flex justify-between py-1 border-t border-border-subtle">
              <span>Open-Meteo Weather Ingestion:</span>
              <span className="text-text-primary">Hourly sync</span>
            </div>
            <div className="flex justify-between py-1 border-t border-border-subtle">
              <span>Field Verification Registry:</span>
              <span className="text-text-primary">On-demand sync</span>
            </div>
          </div>
        </div>

        {/* Section 4: Authority Credentials */}
        <div className="bg-panel-bg border border-border-default p-3 rounded-[2px] space-y-2">
          <div className="text-[10px] text-text-muted uppercase font-bold flex items-center gap-1.5 pb-1 border-b border-border-subtle">
            <Shield className="w-3.5 h-3.5 text-gis-yellow" />
            <span>OPERATIONAL AUTHORITY CONTEXT</span>
          </div>
          <div className="space-y-1 text-[11px] text-text-secondary">
            <div className="flex justify-between py-1">
              <span>Authorized Authority:</span>
              <span className="text-text-primary">Uttarakhand SDMA / Chamoli DDMA</span>
            </div>
            <div className="flex justify-between py-1 border-t border-border-subtle">
              <span>Decision Support Tier:</span>
              <span className="text-gis-blue font-bold">STATE EMERGENCY OPERATIONS CELL</span>
            </div>
            <div className="flex justify-between py-1 border-t border-border-subtle">
              <span>Cryptographic Session:</span>
              <span className="text-gis-green">ED25519 VERIFIED</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
