import { useNavigate } from 'react-router-dom';
import { habitations, candidateSites } from '../data/mockData';
import { ArrowUpRight, CheckCircle2, Clock, AlertTriangle } from 'lucide-react';

export function FieldVerification() {
  const navigate = useNavigate();

  const auditQueue = [
    ...habitations.map((h) => ({
      id: h.id,
      name: h.name,
      type: 'HABITATION',
      district: h.district,
      status: h.verificationStatus,
      lastAudit: h.lastAssessed,
      urgency: h.urgency,
    })),
    ...candidateSites.map((s) => ({
      id: s.id,
      name: s.name,
      type: 'CANDIDATE_SITE',
      district: s.district,
      status: s.verificationStatus,
      lastAudit: '2026-09-18',
      urgency: 'GROUND_SURVEY',
    })),
  ];

  return (
    <div className="h-full flex flex-col bg-workspace text-text-primary p-4 overflow-hidden select-none font-sans">
      <div className="flex items-center justify-between pb-3 border-b border-border-default shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-bold font-mono uppercase tracking-wider text-text-primary">
              FIELD VERIFICATION & GROUND TRUTH AUDIT
            </h1>
            <span className="text-[10px] font-mono px-1.5 py-0.5 bg-gis-green/10 border border-gis-green/30 text-gis-green rounded-[2px] font-bold">
              62% AUDIT COMPLETION RATE
            </span>
          </div>
          <p className="text-xs text-text-muted font-mono mt-0.5">
            District field surveyor verification pipeline for habitations, slope crack gauges, and relocation sites.
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

      <div className="flex-1 overflow-auto mt-3 border border-border-default rounded-[2px] bg-panel-bg">
        <table className="w-full text-left border-collapse text-xs font-mono">
          <thead className="sticky top-0 bg-panel-header text-[10px] uppercase tracking-wider text-text-muted border-b border-border-default z-10">
            <tr>
              <th className="py-2 px-3">Entity ID</th>
              <th className="py-2 px-3">Asset Designation</th>
              <th className="py-2 px-3">Entity Category</th>
              <th className="py-2 px-3">Administrative District</th>
              <th className="py-2 px-3">Last Survey Date</th>
              <th className="py-2 px-3">Relocation Urgency</th>
              <th className="py-2 px-3 text-center">Audit Status</th>
              <th className="py-2 px-3 text-center">Surveyor Log</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle text-[11px]">
            {auditQueue.map((item) => (
              <tr key={item.id} className="hover:bg-surface-hover text-text-secondary transition-colors">
                <td className="py-2 px-3 text-text-muted font-bold">{item.id}</td>
                <td className="py-2 px-3 font-semibold text-text-primary">{item.name}</td>
                <td className="py-2 px-3 text-[10px] text-text-muted">{item.type}</td>
                <td className="py-2 px-3">{item.district}</td>
                <td className="py-2 px-3 tabular-nums text-text-muted">{item.lastAudit}</td>
                <td className="py-2 px-3 text-[10px] font-bold">
                  {item.urgency.replace('_', '-')}
                </td>
                <td className="py-2 px-3 text-center">
                  <span
                    className={`text-[10px] font-semibold uppercase ${
                      item.status === 'VERIFIED'
                        ? 'text-gis-green'
                        : item.status === 'IN_PROGRESS'
                        ? 'text-gis-blue'
                        : item.status === 'FLAGGED'
                        ? 'text-gis-red font-bold'
                        : 'text-gis-yellow'
                    }`}
                  >
                    {item.status}
                  </span>
                </td>
                <td className="py-2 px-3 text-center">
                  <span className="text-[10px] text-text-muted hover:text-text-primary cursor-pointer underline">
                    View Geo-Tagged Photo Log
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
