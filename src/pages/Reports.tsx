import { useNavigate } from 'react-router-dom';
import { ArrowUpRight, Download, FileText, CheckCircle2 } from 'lucide-react';

const reportsRegistry = [
  {
    id: 'REP-2026-09-01',
    title: 'Chamoli Catchment Multi-Hazard Risk Assessment Q3-2026',
    type: 'QUARTERLY STATUTORY REPORT',
    classification: 'RESTRICTED // SDMA INTERNAL',
    date: '2026-09-15',
    author: 'GIS Analysis Cell, UK-SDMA',
    pages: 48,
    status: 'RATIFIED',
  },
  {
    id: 'REP-2026-09-02',
    title: 'Joshimath Ward-7 InSAR Subsidence Velocity & Structural Deformation',
    type: 'SPECIAL DISASTER MEMORANDUM',
    classification: 'CONFIDENTIAL // NDMA ESCALATION',
    date: '2026-09-20',
    author: 'Geological Survey of India & ISRO-NRSC',
    pages: 26,
    status: 'ACTIVE ESCALATION',
  },
  {
    id: 'REP-2026-09-03',
    title: 'Relocation Feasibility & Carrying Capacity: Khar Village to Pipalkoti Plateau',
    type: 'RELOCATION DOSSIER',
    classification: 'OPERATIONAL WORKING DRAFT',
    date: '2026-09-10',
    author: 'District Collectorate Chamoli',
    pages: 34,
    status: 'PENDING APPROVAL',
  },
  {
    id: 'REP-2026-08-01',
    title: 'Alaknanda Basin Hydrological Surge & Rainfall Runoff Model',
    type: 'TECHNICAL ASSESSMENT',
    classification: 'OPEN GOVERNMENT DATA',
    date: '2026-08-31',
    author: 'Central Water Commission & IMD',
    pages: 52,
    status: 'PUBLISHED',
  },
];

export function Reports() {
  const navigate = useNavigate();

  return (
    <div className="h-full flex flex-col bg-workspace text-text-primary p-4 overflow-hidden select-none font-sans">
      <div className="flex items-center justify-between pb-3 border-b border-border-default shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-bold font-mono uppercase tracking-wider text-text-primary">
              STATUTORY INTELLIGENCE REPORTS & DOSSIERS
            </h1>
            <span className="text-[10px] font-mono px-1.5 py-0.5 bg-panel-header border border-border-default text-text-muted rounded-[2px]">
              {reportsRegistry.length} COMPILED DOCUMENTS
            </span>
          </div>
          <p className="text-xs text-text-muted font-mono mt-0.5">
            Official decision-support briefings, hazard escalation memorandums, and relocation blueprints.
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
              <th className="py-2 px-3">Report ID</th>
              <th className="py-2 px-3">Dossier Document Title</th>
              <th className="py-2 px-3">Category Classification</th>
              <th className="py-2 px-3">Authoring Agency</th>
              <th className="py-2 px-3">Publication Date</th>
              <th className="py-2 px-3 text-right">Pages</th>
              <th className="py-2 px-3 text-center">Status</th>
              <th className="py-2 px-3 text-center">Export</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle text-[11px]">
            {reportsRegistry.map((rep) => (
              <tr key={rep.id} className="hover:bg-surface-hover text-text-secondary transition-colors">
                <td className="py-2 px-3 text-text-muted font-bold">{rep.id}</td>
                <td className="py-2 px-3 font-semibold text-text-primary flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-text-muted shrink-0" />
                  <span>{rep.title}</span>
                </td>
                <td className="py-2 px-3 text-[10px] text-text-muted">{rep.type}</td>
                <td className="py-2 px-3">{rep.author}</td>
                <td className="py-2 px-3 tabular-nums text-text-muted">{rep.date}</td>
                <td className="py-2 px-3 text-right tabular-nums">{rep.pages}</td>
                <td className="py-2 px-3 text-center">
                  <span
                    className={`text-[10px] font-semibold uppercase ${
                      rep.status === 'ACTIVE ESCALATION'
                        ? 'text-gis-red font-bold'
                        : rep.status === 'RATIFIED'
                        ? 'text-gis-green'
                        : 'text-text-muted'
                    }`}
                  >
                    {rep.status}
                  </span>
                </td>
                <td className="py-2 px-3 text-center">
                  <button className="text-[10px] text-gis-blue hover:underline flex items-center justify-center gap-1 mx-auto">
                    <Download className="w-3 h-3" />
                    <span>PDF</span>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
