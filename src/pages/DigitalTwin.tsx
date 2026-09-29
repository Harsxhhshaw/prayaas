import { useNavigate } from 'react-router-dom';
import { Layers, ArrowUpRight, Cpu, Eye, Activity } from 'lucide-react';

export function DigitalTwin() {
  const navigate = useNavigate();

  return (
    <div className="h-full flex flex-col bg-workspace text-text-primary p-4 overflow-hidden select-none font-sans">
      <div className="flex items-center justify-between pb-3 border-b border-border-default shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-bold font-mono uppercase tracking-wider text-text-primary">
              DIGITAL TWIN SIMULATION WORKSPACE // 3D TERRAIN
            </h1>
            <span className="text-[10px] font-mono px-1.5 py-0.5 bg-panel-header border border-border-default text-text-muted rounded-[2px]">
              MESH RESOLUTION: 10M DEM
            </span>
          </div>
          <p className="text-xs text-text-muted font-mono mt-0.5">
            Volumetric terrain model with real-time InSAR surface displacement and hydrologic runoff physics.
          </p>
        </div>

        <button
          onClick={() => navigate('/')}
          className="px-2.5 py-1 bg-surface-active hover:bg-border-active border border-border-default rounded-[2px] text-[11px] font-mono text-text-primary transition-colors flex items-center gap-1.5"
        >
          <span>RETURN TO 2D WORKSTATION</span>
          <ArrowUpRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Grid of technical spec blocks */}
      <div className="grid grid-cols-3 gap-3 mt-3 shrink-0">
        <div className="bg-panel-bg border border-border-default p-3 rounded-[2px] font-mono space-y-1">
          <div className="text-[10px] uppercase text-text-muted flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-gis-blue" />
            <span>TERRAIN MESH ENGINE</span>
          </div>
          <div className="text-sm font-bold text-text-primary">Cartosat 10m High-Res DEM</div>
          <div className="text-[11px] text-text-secondary leading-normal">
            Slope gradient calculation active. Triangular Irregular Network (TIN) configured for Chamoli drainage basin.

          </div>
        </div>

        <div className="bg-panel-bg border border-border-default p-3 rounded-[2px] font-mono space-y-1">
          <div className="text-[10px] uppercase text-text-muted flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-gis-red" />
            <span>SURFACE DISPLACEMENT</span>
          </div>
          <div className="text-sm font-bold text-gis-red">InSAR Sentinel-1 Telemetry</div>
          <div className="text-[11px] text-text-secondary leading-normal">
            Persistent Scatterer Interferometry (PSI) detecting mm-scale line-of-sight subsidence over Joshimath and Khar slopes.
          </div>
        </div>

        <div className="bg-panel-bg border border-border-default p-3 rounded-[2px] font-mono space-y-1">
          <div className="text-[10px] uppercase text-text-muted flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-gis-green" />
            <span>HYDRO-DYNAMIC ENGINE</span>
          </div>
          <div className="text-sm font-bold text-text-primary">2D Saint-Venant Runoff</div>
          <div className="text-[11px] text-text-secondary leading-normal">
            Flash flood and debris flow path prediction with variable Manning friction coefficients across land-cover classes.
          </div>
        </div>
      </div>

      {/* Architectural Shell Console */}
      <div className="flex-1 mt-3 border border-border-default rounded-[2px] bg-panel-bg p-4 font-mono flex flex-col justify-between overflow-auto">
        <div className="space-y-2">
          <div className="text-[11px] text-text-muted flex items-center gap-2 pb-2 border-b border-border-subtle">
            <span className="w-2 h-2 rounded-full bg-gis-green animate-pulse" />
            <span>MODULE STATUS: READY FOR WEBGPU / CESIUM ENGINE INITIALIZATION</span>
          </div>
          <div className="text-xs text-text-secondary space-y-1">
            <p className="text-text-muted">// Pipeline Configuration:</p>
            <p className="text-text-primary">• Coordinate Reference: WGS84 / UTM zone 44N (EPSG:32644)</p>
            <p className="text-text-primary">• InSAR Velocity Map: 24-day baseline differential phase unwrapping</p>
            <p className="text-text-primary">• Sensor Nodes: 18 autonomous tiltmeters / pore pressure piezometers</p>
            <p className="text-text-primary">• Elevation Range: Alaknanda valley floor (610m) to Nanda Devi foothills (2,680m)</p>
          </div>
        </div>

        <div className="text-[10px] text-text-muted border-t border-border-subtle pt-2 flex justify-between">
          <span>PRAYAAS 3D KERNEL v0.9-DEV</span>
          <span>INTEGRATION READY FOR SDMA PILOT</span>
        </div>
      </div>
    </div>
  );
}
