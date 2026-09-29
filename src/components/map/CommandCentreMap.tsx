import { useEffect, useState, useCallback, useMemo } from 'react';
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Polygon,
  Tooltip,
  useMap,
  useMapEvents,
} from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import {
  Layers,
  Map as MapIcon,
  Maximize2,
  Ruler,
  MousePointer,
  Plus,
  Minus,
  RotateCcw,
} from 'lucide-react';
import type { MapLayer, Habitation, RedZone, CandidateRelocationSite, InfrastructurePoint, CandidateParcelItem } from '../../types';
import { habitations, redZones, candidateSites, infrastructurePoints, defaultMapLayers } from '../../data/mockData';
import { api } from '../../lib/api';
import { MapLayerControl } from './MapLayerControl';
import type { SelectedFeature } from '../inspector/FeatureInspector';

interface CommandCentreMapProps {
  onSelectFeature: (feature: SelectedFeature) => void;
  selectedFeature: SelectedFeature;
  focusPosition?: { lat: number; lng: number } | null;
}

// Basemap Tile Providers (Reliable, free, no API key required, zero watermarks)
const basemapOptions = {
  darkCanvas: {
    id: 'darkCanvas',
    name: 'Dark Canvas',
    base: 'https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
    ref: 'https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Esri, HERE, Garmin, OpenStreetMap contributors',
  },
  satellite: {
    id: 'satellite',
    name: 'Satellite',
    base: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    ref: 'https://services.arcgisonline.com/arcgis/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Source: Esri, Maxar, Earthstar Geographics, GIS User Community',
  },
  topo: {
    id: 'topo',
    name: 'Topographic',
    base: 'https://services.arcgisonline.com/arcgis/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
    ref: null,
    attribution: 'Esri, HERE, Garmin, Intermap, USGS, METI/NASA',
  },
};

// Smooth Camera Controller
function MapCameraController({
  position,
  bounds,
}: {
  position?: { lat: number; lng: number } | null;
  bounds?: [number, number][];
}) {
  const map = useMap();

  useEffect(() => {
    if (position) {
      map.flyTo([position.lat, position.lng], 13, { duration: 1.2 });
    }
  }, [position, map]);

  useEffect(() => {
    if (bounds && bounds.length > 0) {
      map.fitBounds(bounds, { padding: [50, 50], duration: 1.2 });
    }
  }, [bounds, map]);

  return null;
}

// Mouse coordinate tracker & zoom level
function MapCoordinateTracker({
  onCoordinatesChange,
}: {
  onCoordinatesChange: (coords: { lat: number; lng: number; zoom: number }) => void;
}) {
  const map = useMapEvents({
    mousemove(e) {
      onCoordinatesChange({ lat: e.latlng.lat, lng: e.latlng.lng, zoom: map.getZoom() });
    },
    zoomend() {
      onCoordinatesChange({ lat: map.getCenter().lat, lng: map.getCenter().lng, zoom: map.getZoom() });
    },
  });
  return null;
}

// Custom Zoom Controls Hook Wrapper
function CustomZoomControls() {
  const map = useMap();
  return (
    <div className="flex flex-col border border-border-default rounded-[2px] overflow-hidden bg-panel-bg shadow-lg">
      <button
        onClick={() => map.zoomIn()}
        className="p-1.5 text-text-muted hover:text-text-primary hover:bg-surface-hover transition-colors border-b border-border-subtle"
        title="Zoom In"
      >
        <Plus className="w-3.5 h-3.5" />
      </button>
      <button
        onClick={() => map.zoomOut()}
        className="p-1.5 text-text-muted hover:text-text-primary hover:bg-surface-hover transition-colors"
        title="Zoom Out"
      >
        <Minus className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

export function CommandCentreMap({
  onSelectFeature,
  selectedFeature,
  focusPosition,
}: CommandCentreMapProps) {
  const [layers, setLayers] = useState<MapLayer[]>(defaultMapLayers);
  const [opacity, setOpacity] = useState(0.85);
  const [isLayerPanelOpen, setIsLayerPanelOpen] = useState(false);
  const [currentBasemap, setCurrentBasemap] = useState<keyof typeof basemapOptions>('darkCanvas');
  const [isBasemapDropdownOpen, setIsBasemapDropdownOpen] = useState(false);
  const [measureMode, setMeasureMode] = useState(false);
  const [measuredDistance, setMeasuredDistance] = useState<number | null>(null);

  const [mouseCoords, setMouseCoords] = useState({ lat: 30.42, lng: 79.35, zoom: 10 });

  const initialCenter: [number, number] = [30.43, 79.35];

  const handleToggleLayer = useCallback((layerId: string) => {
    setLayers((prev) =>
      prev.map((l) => (l.id === layerId ? { ...l, enabled: !l.enabled } : l))
    );
  }, []);

  const isLayerEnabled = (id: string) => layers.find((l) => l.id === id)?.enabled ?? false;

  const [candidateParcels, setCandidateParcels] = useState<CandidateParcelItem[]>([]);

  useEffect(() => {
    api.getCandidateParcels().then((res) => {
      if (res.data?.items && res.data.items.length > 0) {
        setCandidateParcels(res.data.items);
      }
    });
  }, []);

  const selectedId =
    selectedFeature?.type === 'HABITATION'
      ? selectedFeature.data.id
      : selectedFeature?.type === 'CANDIDATE_SITE'
      ? selectedFeature.data.id
      : selectedFeature?.type === 'CANDIDATE_PARCEL'
      ? selectedFeature.data.id
      : selectedFeature?.type === 'RED_ZONE'
      ? selectedFeature.data.id
      : selectedFeature?.type === 'INFRASTRUCTURE'
      ? selectedFeature.data.id
      : null;

  const activeBasemap = basemapOptions[currentBasemap];

  return (
    <div className="relative w-full h-full bg-workspace select-none overflow-hidden">
      <MapContainer
        center={initialCenter}
        zoom={10}
        zoomControl={false}
        attributionControl={false}
        className="w-full h-full z-0"
      >
        {/* Basemap Tiles (Working Esri, zero watermark, zero key) */}
        <TileLayer
          key={activeBasemap.base}
          url={activeBasemap.base}
          attribution={activeBasemap.attribution}
          maxZoom={18}
          minZoom={6}
        />

        {/* Optional reference labels layer */}
        {activeBasemap.ref && (
          <TileLayer
            key={activeBasemap.ref}
            url={activeBasemap.ref}
            maxZoom={18}
            minZoom={6}
            opacity={0.9}
          />
        )}

        <MapCameraController position={focusPosition} />
        <MapCoordinateTracker onCoordinatesChange={setMouseCoords} />

        {/* ===================================================================
            1. RED ZONE POLYGONS (Translucent fills, distinct borders)
           =================================================================== */}
        {isLayerEnabled('composite-risk') &&
          redZones.map((zone) => {
            const isSelected = selectedId === zone.id;
            return (
              <Polygon
                key={zone.id}
                positions={zone.bounds.map((p) => [p.lat, p.lng] as [number, number])}
                pathOptions={{
                  color: isSelected ? '#ffffff' : '#f85149',
                  fillColor: '#f85149',
                  fillOpacity: isSelected ? 0.24 : 0.12 * opacity,
                  weight: isSelected ? 2 : 1,
                  dashArray: isSelected ? undefined : '4 3',
                }}
                eventHandlers={{
                  click: () => onSelectFeature({ type: 'RED_ZONE', data: zone }),
                }}
              >
                <Tooltip direction="top" opacity={0.95} sticky>
                  <div className="font-mono text-[11px] leading-tight">
                    <span className="text-gis-red font-bold block">{zone.name}</span>
                    <span className="text-text-muted">
                      Risk: {zone.compositRiskScore}/100 • Pop: {zone.populationAffected.toLocaleString()}
                    </span>
                  </div>
                </Tooltip>
              </Polygon>
            );
          })}

        {/* ===================================================================
            2. CANDIDATE RELOCATION SITES (Hatched outline polygons)
           =================================================================== */}
        {isLayerEnabled('candidate-sites') &&
          candidateSites.map((site) => {
            const isSelected = selectedId === site.id;
            return (
              <Polygon
                key={site.id}
                positions={site.bounds.map((p) => [p.lat, p.lng] as [number, number])}
                pathOptions={{
                  color: isSelected ? '#ffffff' : '#3fb950',
                  fillColor: '#3fb950',
                  fillOpacity: isSelected ? 0.22 : 0.10 * opacity,
                  weight: isSelected ? 2 : 1.5,
                  dashArray: isSelected ? undefined : '5 4',
                }}
                eventHandlers={{
                  click: () => onSelectFeature({ type: 'CANDIDATE_SITE', data: site }),
                }}
              >
                <Tooltip direction="top" opacity={0.95} sticky>
                  <div className="font-mono text-[11px] leading-tight">
                    <span className="text-gis-green font-bold block">{site.name}</span>
                    <span className="text-text-muted">
                      Suitability: {site.suitabilityScore}/100 • Capacity: {site.carryingCapacity.toLocaleString()}
                    </span>
                  </div>
                </Tooltip>
              </Polygon>
            );
          })}

        {/* ===================================================================
            2a-ii. FEASIBLE LAND MASK (Subtle continuous mask of land surviving exclusions)
           =================================================================== */}
        {isLayerEnabled('feasible-land') && (
          <>
            <Polygon
              positions={[
                [30.34, 79.28],
                [30.42, 79.32],
                [30.46, 79.44],
                [30.56, 79.56],
                [30.54, 79.62],
                [30.47, 79.60],
                [30.38, 79.40],
                [30.32, 79.33],
              ]}
              pathOptions={{
                color: '#059669',
                fillColor: '#047857',
                fillOpacity: 0.08 * opacity,
                weight: 1.0,
                dashArray: '4 4',
              }}
            >
              <Tooltip direction="top" opacity={0.95} sticky>
                <div className="font-mono text-[10px] leading-tight">
                  <span className="text-emerald-400 font-bold block">Feasible Land Mask (Chamoli Corridor)</span>
                  <span className="text-text-muted">Slope &le; 25° • Hazard buffer &gt; 300m • Connected feasible terrain</span>
                </div>
              </Tooltip>
            </Polygon>
            <Polygon
              positions={[
                [30.27, 78.96],
                [30.33, 79.01],
                [30.41, 79.08],
                [30.39, 79.14],
                [30.30, 79.05],
                [30.26, 78.99],
              ]}
              pathOptions={{
                color: '#059669',
                fillColor: '#047857',
                fillOpacity: 0.08 * opacity,
                weight: 1.0,
                dashArray: '4 4',
              }}
            >
              <Tooltip direction="top" opacity={0.95} sticky>
                <div className="font-mono text-[10px] leading-tight">
                  <span className="text-emerald-400 font-bold block">Feasible Land Mask (Mandakini Valley)</span>
                  <span className="text-text-muted">Slope &le; 25° • Hard exclusions satisfied</span>
                </div>
              </Tooltip>
            </Polygon>
          </>
        )}

        {/* ===================================================================
            2b. MODELED CANDIDATE PARCELS (Cyan outline, distinct from benchmark pins)
           =================================================================== */}
        {isLayerEnabled('candidate-parcels') &&
          candidateParcels.map((parcel) => {
            const isSelected = selectedId === parcel.id;
            const c = parcel.centroid;
            // Approximate polygon boundaries from centroid and metric area
            const span = Math.max(0.002, Math.sqrt(Math.max(1.0, parcel.area_hectares) * 10000) / 111132 / 2);
            const positions: [number, number][] = [
              [c.lat - span, c.lng - span * 1.1],
              [c.lat + span, c.lng - span * 0.9],
              [c.lat + span * 1.1, c.lng + span * 0.8],
              [c.lat - span * 0.9, c.lng + span],
            ];

            return (
              <Polygon
                key={parcel.id}
                positions={positions}
                pathOptions={{
                  color: isSelected ? '#ffffff' : '#0891b2',
                  fillColor: '#06b6d4',
                  fillOpacity: isSelected ? 0.18 : 0.08 * opacity,
                  weight: isSelected ? 2.0 : 1.2,
                  dashArray: isSelected ? undefined : '3 3',
                }}
                eventHandlers={{
                  click: () => onSelectFeature({ type: 'CANDIDATE_PARCEL', data: parcel }),
                }}
              >
                <Tooltip direction="top" opacity={0.95} sticky>
                  <div className="font-mono text-[11px] leading-tight">
                    <span className="text-cyan-400 font-bold block">
                      Discovered Parcel #{parcel.rank} ({parcel.area_hectares.toFixed(1)} ha)
                    </span>
                    <span className="text-text-muted">
                      Suitability: {parcel.suitability_score.toFixed(1)}/100 • Robustness: {parcel.robustness_level}
                    </span>
                    <span className="text-[10px] text-amber-300 block mt-0.5">
                      MODELED PARCEL • Field Verification Required
                    </span>
                  </div>
                </Tooltip>
              </Polygon>
            );
          })}

        {/* ===================================================================
            3. INFRASTRUCTURE ASSETS (Small neutral points)
           =================================================================== */}
        {isLayerEnabled('infrastructure') &&
          infrastructurePoints.map((point) => {
            const isSelected = selectedId === point.id;
            const colors: Record<string, string> = {
              HOSPITAL: '#58a6ff',
              SCHOOL: '#bc8cff',
              ROAD_JUNCTION: '#8b949e',
              BRIDGE: '#d29922',
              HELIPAD: '#39c5bb',
              SHELTER: '#3fb950',
            };
            const col = colors[point.type] || '#8b949e';

            return (
              <CircleMarker
                key={point.id}
                center={[point.position.lat, point.position.lng]}
                radius={isSelected ? 6 : 3.5}
                pathOptions={{
                  color: isSelected ? '#ffffff' : col,
                  fillColor: col,
                  fillOpacity: isSelected ? 1 : 0.8,
                  weight: isSelected ? 2 : 1,
                }}
                eventHandlers={{
                  click: () => onSelectFeature({ type: 'INFRASTRUCTURE', data: point }),
                }}
              >
                <Tooltip direction="top" opacity={0.95}>
                  <div className="font-mono text-[10px]">
                    <span className="font-bold text-text-primary block">{point.name}</span>
                    <span className="text-text-muted">{point.type} • {point.status}</span>
                  </div>
                </Tooltip>
              </CircleMarker>
            );
          })}

        {/* ===================================================================
            4. HABITATION MARKERS (Crisp symbols, subtle risk rings)
           =================================================================== */}
        {isLayerEnabled('population') &&
          habitations.map((hab) => {
            const isSelected = selectedId === hab.id;
            const isCritical = hab.riskScore >= 80;
            const isHigh = hab.riskScore >= 60;
            const isWatch = hab.riskScore >= 40;

            const strokeColor = isCritical
              ? '#f85149'
              : isHigh
              ? '#f0883e'
              : isWatch
              ? '#d29922'
              : '#3fb950';

            const fillColor = isCritical
              ? '#3a1315'
              : isHigh
              ? '#382012'
              : isWatch
              ? '#2c2514'
              : '#16281a';

            const radius = isSelected ? 7 : 4.5;

            return (
              <CircleMarker
                key={hab.id}
                center={[hab.position.lat, hab.position.lng]}
                radius={radius}
                pathOptions={{
                  color: isSelected ? '#ffffff' : strokeColor,
                  fillColor: isSelected ? strokeColor : fillColor,
                  fillOpacity: 0.95,
                  weight: isSelected ? 2.5 : 1.5,
                }}
                eventHandlers={{
                  click: () => onSelectFeature({ type: 'HABITATION', data: hab }),
                }}
              >
                <Tooltip direction="top" opacity={0.95} offset={[0, -4]}>
                  <div className="font-mono text-[11px] leading-tight">
                    <div className="flex items-center gap-1.5 font-bold">
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          isCritical ? 'bg-gis-red' : isHigh ? 'bg-gis-orange' : 'bg-gis-yellow'
                        }`}
                      />
                      <span className="text-text-primary">{hab.name}</span>
                      <span className="text-[10px] text-text-muted font-normal">({hab.id})</span>
                    </div>
                    <div className="text-[10px] text-text-secondary mt-0.5">
                      Risk: <strong className={isCritical ? 'text-gis-red' : 'text-text-primary'}>{hab.riskScore}</strong>
                      {' • '}Pop: {hab.population.toLocaleString()}
                    </div>
                  </div>
                </Tooltip>
              </CircleMarker>
            );
          })}
      </MapContainer>

      {/* =====================================================================
          COMPACT GIS FLOATING TOOLBAR (Top-Left)
         ===================================================================== */}
      <div className="absolute top-3 left-3 z-[1000] flex items-center gap-1.5">
        {/* Layer Panel Button */}
        <button
          onClick={() => setIsLayerPanelOpen(!isLayerPanelOpen)}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-[2px] border text-xs font-mono transition-colors shadow-lg ${
            isLayerPanelOpen
              ? 'bg-surface-active border-border-active text-text-primary'
              : 'bg-panel-bg border-border-default text-text-secondary hover:text-text-primary hover:bg-surface-hover'
          }`}
          title="Toggle Geospatial Layers"
        >
          <Layers className="w-3.5 h-3.5 text-text-muted" />
          <span className="text-[11px]">LAYERS</span>
        </button>

        {/* Basemap Switcher */}
        <div className="relative">
          <button
            onClick={() => setIsBasemapDropdownOpen(!isBasemapDropdownOpen)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-[2px] border border-border-default bg-panel-bg text-xs font-mono text-text-secondary hover:text-text-primary hover:bg-surface-hover transition-colors shadow-lg"
            title="Select Basemap Provider"
          >
            <MapIcon className="w-3.5 h-3.5 text-text-muted" />
            <span className="text-[11px] uppercase">{activeBasemap.name}</span>
          </button>

          {isBasemapDropdownOpen && (
            <div className="absolute top-full left-0 mt-1 w-36 bg-panel-bg border border-border-default rounded-[2px] shadow-xl py-1 z-50 text-[11px] font-mono">
              {Object.values(basemapOptions).map((bm) => (
                <button
                  key={bm.id}
                  onClick={() => {
                    setCurrentBasemap(bm.id as keyof typeof basemapOptions);
                    setIsBasemapDropdownOpen(false);
                  }}
                  className={`w-full text-left px-2.5 py-1.5 hover:bg-surface-hover transition-colors flex items-center justify-between ${
                    currentBasemap === bm.id ? 'text-gis-blue font-bold bg-panel-header' : 'text-text-secondary'
                  }`}
                >
                  <span>{bm.name}</span>
                  {currentBasemap === bm.id && <span>●</span>}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Reset Extent */}
        <button
          onClick={() => {
            // Refocus to Chamoli valley
            window.dispatchEvent(new CustomEvent('map:reset-extent'));
          }}
          className="p-1.5 rounded-[2px] border border-border-default bg-panel-bg text-text-muted hover:text-text-primary hover:bg-surface-hover transition-colors shadow-lg"
          title="Reset View Extent to Chamoli Study Region"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>

        {/* Zoom Controls */}
        <CustomZoomControls />
      </div>

      {/* Custom Layer Control Drawer */}
      <MapLayerControl
        layers={layers}
        onToggleLayer={handleToggleLayer}
        opacity={opacity}
        onOpacityChange={setOpacity}
        isOpen={isLayerPanelOpen}
        onClose={() => setIsLayerPanelOpen(false)}
      />

      {/* =====================================================================
          MAP STATUS & TELEMETRY FOOTER (Bottom-Left)
         ===================================================================== */}
      <div className="absolute bottom-2 left-3 z-[1000] flex items-center gap-3 px-2.5 py-1 bg-panel-bg/90 backdrop-blur-xs border border-border-default rounded-[2px] text-[10px] font-mono text-text-muted shadow-lg pointer-events-none">
        <div>
          <span>COORDS: </span>
          <span className="text-text-secondary tabular-nums">
            {mouseCoords.lat.toFixed(4)}°N, {mouseCoords.lng.toFixed(4)}°E
          </span>
        </div>
        <span>•</span>
        <div>
          <span>ZOOM: </span>
          <span className="text-text-secondary tabular-nums">{mouseCoords.zoom}</span>
        </div>
        <span>•</span>
        <div className="hidden sm:inline">
          <span>CRS: </span>
          <span className="text-text-secondary">EPSG:4326</span>
        </div>
        <span>•</span>
        <div className="hidden md:inline">
          <span>GRID: </span>
          <span className="text-text-secondary">UTM 44N</span>
        </div>
      </div>
    </div>
  );
}
