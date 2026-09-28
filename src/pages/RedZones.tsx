import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { redZones as mockRedZones } from '../data/mockData';
import { ArrowUpRight, AlertOctagon, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { api } from '../lib/api';
import type { RedZoneIntelligenceItem } from '../types';

export function RedZones() {
  const navigate = useNavigate();
  const [zones, setZones] = useState<RedZoneIntelligenceItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getRedZonesIntelligence().then((res) => {
      if (res.data?.red_zones && res.data.red_zones.length > 0) {
        setZones(res.data.red_zones);
      } else {
        // Fallback mapping
        setZones(mockRedZones.map((rz) => ({
          id: rz.id,
          name: rz.name,
          classification: 'CONDITIONAL_RED',
          composite_risk_score: rz.compositRiskScore,
          dominant_hazard: rz.hazardTypes[0] || 'LANDSLIDE',
          confidence_score: 75.0,
          habitation_count: rz.habitationCount,
          population_affected: rz.populationAffected,
          computed_area_sq_km: rz.areaKmSq,
          source_declared_area_sq_km: rz.areaKmSq,
          reason_codes: ['MONITORED_HAZARD_ZONE'],
          requires_field_verification: false,
        })));
      }
      setLoading(false);
    }).catch(() => {
      setLoading(false);
    });
  }, []);

  return (
    <div className="h-full flex flex-col bg-workspace text-text-primary p-4 overflow-hidden select-none font-sans">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-border-default shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-bold font-mono uppercase tracking-wider text-text-primary">
              STATUTORY RED ZONE REGISTER & DELIMITATION AUDIT
            </h1>
            <span className="text-[10px] font-mono px-1.5 py-0.5 bg-gis-red/10 border border-gis-red/30 text-gis-red rounded-[2px] font-bold">
              {zones.length} ACTIVE DELIMITATIONS
            </span>
          </div>
          <p className="text-xs text-text-muted font-mono mt-0.5">
            Geographic perimeters legally declared unsuitable for permanent human habitation — PRAYAAS-RISK-1.0 classification with geodesic boundary audit.
          </p>
        </div>

        <button
          onClick={() => navigate('/')}
          className="px-2.5 py-1 bg-surface-active hover:bg-border-active border border-border-default rounded-[2px] text-[11px] font-mono text-text-primary transition-colors flex items-center gap-1.5"
        >
          <span>VIEW BOUNDARIES ON GIS WORKSTATION</span>
          <ArrowUpRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Grid */}
      <div className="flex-1 overflow-auto mt-3 border border-border-default rounded-[2px] bg-panel-bg">
        <table className="w-full text-left border-collapse text-xs font-mono">
          <thead className="sticky top-0 bg-panel-header text-[10px] uppercase tracking-wider text-text-muted border-b border-border-default z-10">
            <tr>
              <th className="py-2 px-3">Zone ID</th>
              <th className="py-2 px-3">Designation Name</th>
              <th className="py-2 px-3">Classification</th>
              <th className="py-2 px-3 text-right">Composite Score</th>
              <th className="py-2 px-3 text-right">Declared Area</th>
              <th className="py-2 px-3 text-right">Computed Geodesic</th>
              <th className="py-2 px-3 text-right">Area Delta</th>
              <th className="py-2 px-3 text-right">Habitations</th>
              <th className="py-2 px-3 text-right">Population at Risk</th>
              <th className="py-2 px-3">Dominant Hazard</th>
              <th className="py-2 px-3 text-center">Field Verification</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle text-[11px]">
            {zones.map((rz) => {
              const declared = rz.source_declared_area_sq_km ?? rz.computed_area_sq_km;
              const computed = rz.computed_area_sq_km;
              const delta = (computed - declared).toFixed(2);
              const deltaNum = parseFloat(delta);

              return (
                <tr key={rz.id} className="hover:bg-surface-hover text-text-secondary transition-colors">
                  <td className="py-2 px-3 text-text-muted font-bold">{rz.id}</td>
                  <td className="py-2 px-3 font-semibold text-text-primary">{rz.name}</td>
                  <td className="py-2 px-3">
                    <span
                      className={`px-1.5 py-0.5 rounded-[1px] font-bold text-[9px] uppercase tracking-wider ${
                        rz.classification === 'PERMANENT_RED'
                          ? 'bg-gis-red/10 border border-gis-red/30 text-gis-red'
                          : rz.classification === 'DYNAMIC_RED'
                          ? 'bg-gis-orange/10 border border-gis-orange/30 text-gis-orange'
                          : 'bg-gis-orange/10 border border-gis-orange/30 text-gis-orange'
                      }`}
                    >
                      {rz.classification.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right font-bold tabular-nums text-gis-red">
                    {rz.composite_risk_score.toFixed(1)}/100
                  </td>
                  <td className="py-2 px-3 text-right tabular-nums text-text-secondary">
                    {declared ? `${declared.toFixed(2)} km²` : '—'}
                  </td>
                  <td className="py-2 px-3 text-right tabular-nums text-text-primary font-bold">
                    {computed.toFixed(2)} km²
                  </td>
                  <td className="py-2 px-3 text-right tabular-nums">
                    <span className={Math.abs(deltaNum) > 1.0 ? 'text-gis-orange font-bold' : 'text-text-muted'}>
                      {deltaNum > 0 ? `+${delta}` : delta} km²
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right tabular-nums text-text-primary font-bold">
                    {rz.habitation_count}
                  </td>
                  <td className="py-2 px-3 text-right tabular-nums text-gis-red font-bold">
                    {rz.population_affected.toLocaleString()}
                  </td>
                  <td className="py-2 px-3">
                    <span className="px-1.5 py-0.5 bg-panel-header border border-border-subtle rounded-[1px] text-[10px] text-text-muted">
                      {rz.dominant_hazard}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-center">
                    {rz.requires_field_verification ? (
                      <span className="px-1.5 py-0.5 bg-gis-orange/10 border border-gis-orange/30 text-gis-orange font-bold text-[9px] uppercase tracking-wider rounded-[1px] inline-flex items-center gap-1">
                        <AlertOctagon className="w-2.5 h-2.5" />
                        REQUIRED
                      </span>
                    ) : (
                      <span className="px-1.5 py-0.5 bg-gis-green/10 border border-gis-green/30 text-gis-green font-bold text-[9px] uppercase tracking-wider rounded-[1px] inline-flex items-center gap-1">
                        <CheckCircle2 className="w-2.5 h-2.5" />
                        VERIFIED
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

