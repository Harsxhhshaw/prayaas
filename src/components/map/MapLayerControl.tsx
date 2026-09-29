import { useState } from 'react';
import { Layers, ChevronDown, ChevronRight, Sliders, Info, X } from 'lucide-react';
import type { MapLayer } from '../../types';

interface MapLayerControlProps {
  layers: MapLayer[];
  onToggleLayer: (layerId: string) => void;
  opacity: number;
  onOpacityChange: (val: number) => void;
  isOpen: boolean;
  onClose: () => void;
}

export function MapLayerControl({
  layers,
  onToggleLayer,
  opacity,
  onOpacityChange,
  isOpen,
  onClose,
}: MapLayerControlProps) {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    HAZARDS: true,
    HABITATION: true,
    RELOCATION: true,
    TERRAIN: false,
  });

  if (!isOpen) return null;

  const toggleSection = (sec: string) => {
    setExpandedSections((prev) => ({ ...prev, [sec]: !prev[sec] }));
  };

  const hazardLayers = layers.filter((l) => l.group === 'HAZARDS');
  const exposureLayers = layers.filter((l) => l.group === 'HABITATION');
  const relocationLayers = layers.filter((l) => l.group === 'RELOCATION');
  const terrainLayers = layers.filter((l) => l.group === 'TERRAIN');

  return (
    <div className="absolute top-12 left-3 z-[1000] w-64 bg-panel-bg border border-border-default rounded-[2px] shadow-2xl text-xs font-sans select-none overflow-hidden animate-in fade-in duration-150">
      {/* Panel Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-panel-header border-b border-border-default">
        <div className="flex items-center gap-1.5 font-mono text-[11px] font-semibold text-text-primary tracking-wider uppercase">
          <Layers className="w-3.5 h-3.5 text-text-muted" />
          <span>Layer Management</span>
        </div>
        <button
          onClick={onClose}
          className="text-text-muted hover:text-text-primary p-0.5 rounded-[1px] hover:bg-surface-hover"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="max-h-[380px] overflow-y-auto p-2 space-y-3 font-sans">
        {/* SECTION: HAZARDS */}
        <div>
          <button
            onClick={() => toggleSection('HAZARDS')}
            className="w-full flex items-center justify-between text-[10px] font-mono font-bold text-text-muted uppercase tracking-wider py-1 hover:text-text-primary"
          >
            <div className="flex items-center gap-1">
              {expandedSections.HAZARDS ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
              <span>Hazards</span>
            </div>
            <span className="text-[10px] text-text-muted">
              {hazardLayers.filter((l) => l.enabled).length}/{hazardLayers.length}
            </span>
          </button>

          {expandedSections.HAZARDS && (
            <div className="pl-4 space-y-1.5 pt-1">
              {hazardLayers.map((layer) => (
                <label
                  key={layer.id}
                  className="flex items-center justify-between cursor-pointer group hover:text-text-primary py-0.5"
                >
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={layer.enabled}
                      onChange={() => onToggleLayer(layer.id)}
                      className="w-3.5 h-3.5 accent-gis-red rounded-[2px] bg-panel-header border-border-default cursor-pointer"
                    />
                    <span className={`text-[11px] ${layer.enabled ? 'text-text-primary' : 'text-text-secondary'}`}>
                      {layer.name}
                    </span>
                  </div>
                  {layer.id === 'composite-risk' && (
                    <span className="w-2 h-2 rounded-full bg-gis-red" title="Critical hazard layer" />
                  )}
                  {layer.id === 'landslide' && <span className="w-2 h-2 rounded-full bg-gis-orange" />}
                  {layer.id === 'flood' && <span className="w-2 h-2 rounded-full bg-gis-blue" />}
                  {layer.id === 'cloudburst' && <span className="w-2 h-2 rounded-full bg-gis-yellow" />}
                </label>
              ))}
            </div>
          )}
        </div>

        {/* SECTION: EXPOSURE / HABITATION */}
        <div className="border-t border-border-subtle pt-2">
          <button
            onClick={() => toggleSection('HABITATION')}
            className="w-full flex items-center justify-between text-[10px] font-mono font-bold text-text-muted uppercase tracking-wider py-1 hover:text-text-primary"
          >
            <div className="flex items-center gap-1">
              {expandedSections.HABITATION ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
              <span>Exposure & Assets</span>
            </div>
            <span className="text-[10px] text-text-muted">
              {exposureLayers.filter((l) => l.enabled).length}/{exposureLayers.length}
            </span>
          </button>

          {expandedSections.HABITATION && (
            <div className="pl-4 space-y-1.5 pt-1">
              {exposureLayers.map((layer) => (
                <label
                  key={layer.id}
                  className="flex items-center justify-between cursor-pointer group hover:text-text-primary py-0.5"
                >
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={layer.enabled}
                      onChange={() => onToggleLayer(layer.id)}
                      className="w-3.5 h-3.5 accent-gis-blue rounded-[2px] bg-panel-header border-border-default cursor-pointer"
                    />
                    <span className={`text-[11px] ${layer.enabled ? 'text-text-primary' : 'text-text-secondary'}`}>
                      {layer.name}
                    </span>
                  </div>
                  {layer.id === 'population' && (
                    <span className="text-[9px] font-mono text-text-muted">DENSITY</span>
                  )}
                  {layer.id === 'infrastructure' && (
                    <span className="w-2 h-2 rounded-[1px] bg-gis-cyan" />
                  )}
                </label>
              ))}
            </div>
          )}
        </div>

        {/* SECTION: RELOCATION */}
        <div className="border-t border-border-subtle pt-2">
          <button
            onClick={() => toggleSection('RELOCATION')}
            className="w-full flex items-center justify-between text-[10px] font-mono font-bold text-text-muted uppercase tracking-wider py-1 hover:text-text-primary"
          >
            <div className="flex items-center gap-1">
              {expandedSections.RELOCATION ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
              <span>Relocation Strategy</span>
            </div>
            <span className="text-[10px] text-text-muted">
              {relocationLayers.filter((l) => l.enabled).length}/{relocationLayers.length}
            </span>
          </button>

          {expandedSections.RELOCATION && (
            <div className="pl-4 space-y-1.5 pt-1">
              {relocationLayers.map((layer) => (
                <label
                  key={layer.id}
                  className="flex items-center justify-between cursor-pointer group hover:text-text-primary py-0.5"
                >
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={layer.enabled}
                      onChange={() => onToggleLayer(layer.id)}
                      className="w-3.5 h-3.5 accent-gis-green rounded-[2px] bg-panel-header border-border-default cursor-pointer"
                    />
                    <span className={`text-[11px] ${layer.enabled ? 'text-text-primary' : 'text-text-secondary'}`}>
                      {layer.name}
                    </span>
                  </div>
                  {layer.id === 'candidate-sites' && (
                    <span className="w-2 h-2 border border-gis-green bg-gis-green/30" />
                  )}
                  {layer.id === 'candidate-parcels' && (
                    <span className="w-2 h-2 border border-cyan-400 bg-cyan-400/40" />
                  )}
                </label>
              ))}
            </div>
          )}
        </div>

        {/* SECTION: TERRAIN */}
        <div className="border-t border-border-subtle pt-2">
          <button
            onClick={() => toggleSection('TERRAIN')}
            className="w-full flex items-center justify-between text-[10px] font-mono font-bold text-text-muted uppercase tracking-wider py-1 hover:text-text-primary"
          >
            <div className="flex items-center gap-1">
              {expandedSections.TERRAIN ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
              <span>Terrain & Slope</span>
            </div>
            <span className="text-[10px] text-text-muted">
              {terrainLayers.filter((l) => l.enabled).length}/{terrainLayers.length}
            </span>
          </button>

          {expandedSections.TERRAIN && (
            <div className="pl-4 space-y-1.5 pt-1">
              {terrainLayers.map((layer) => (
                <label
                  key={layer.id}
                  className="flex items-center justify-between cursor-pointer group hover:text-text-primary py-0.5"
                >
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={layer.enabled}
                      onChange={() => onToggleLayer(layer.id)}
                      className="w-3.5 h-3.5 accent-gis-yellow rounded-[2px] bg-panel-header border-border-default cursor-pointer"
                    />
                    <span className={`text-[11px] ${layer.enabled ? 'text-text-primary' : 'text-text-secondary'}`}>
                      {layer.name}
                    </span>
                  </div>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Opacity Control */}
        <div className="border-t border-border-subtle pt-2">
          <div className="flex items-center justify-between text-[10px] font-mono text-text-muted mb-1">
            <span className="flex items-center gap-1">
              <Sliders className="w-3 h-3" />
              OVERLAY OPACITY
            </span>
            <span className="text-text-primary tabular-nums">{Math.round(opacity * 100)}%</span>
          </div>
          <input
            type="range"
            min="20"
            max="100"
            value={Math.round(opacity * 100)}
            onChange={(e) => onOpacityChange(Number(e.target.value) / 100)}
            className="w-full h-1 bg-border-default rounded-[1px] accent-text-primary cursor-pointer"
          />
        </div>

        {/* Metadata Footer */}
        <div className="pt-2 border-t border-border-subtle flex items-start gap-1 text-[9px] font-mono text-text-muted leading-tight">
          <Info className="w-3 h-3 shrink-0 mt-0.5" />
          <span>DATA: GSI LANDSLIDE SUSCEPTIBILITY / ISRO BHUVAN 2026</span>
        </div>
      </div>
    </div>
  );
}
