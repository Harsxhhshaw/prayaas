import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  Compass,
  Building2,
  AlertOctagon,
  ArrowUpDown,
  MapPin,
  Cpu,
  ClipboardCheck,
  FileText,
  Database,
  Settings,
} from 'lucide-react';

interface ToolItem {
  id: string;
  label: string;
  path: string;
  icon: typeof Compass;
  shortcut: string;
}

const primaryTools: ToolItem[] = [
  { id: 'command', label: 'Command Workstation', path: '/', icon: Compass, shortcut: '1' },
  { id: 'habitations', label: 'Habitations Register', path: '/habitations', icon: Building2, shortcut: '2' },
  { id: 'hazards', label: 'Hazard Red Zones', path: '/red-zones', icon: AlertOctagon, shortcut: '3' },
  { id: 'relocation', label: 'Relocation Priorities', path: '/relocation-priority', icon: ArrowUpDown, shortcut: '4' },
  { id: 'candidates', label: 'Candidate Relocation Sites', path: '/candidate-sites', icon: MapPin, shortcut: '5' },
  { id: 'simulation', label: 'Scenario Lab & Digital Twin', path: '/scenario-lab', icon: Cpu, shortcut: '6' },
  { id: 'field', label: 'Field Verification', path: '/field-verification', icon: ClipboardCheck, shortcut: '7' },
  { id: 'reports', label: 'Intelligence Reports', path: '/reports', icon: FileText, shortcut: '8' },
  { id: 'data', label: 'Geospatial Data Sources', path: '/data-sources', icon: Database, shortcut: '9' },
];

export function ToolRail() {
  const location = useLocation();
  const [hoveredTool, setHoveredTool] = useState<ToolItem | null>(null);

  return (
    <aside className="w-[52px] bg-panel-bg border-r border-border-default flex flex-col justify-between items-center py-2 z-30 select-none shrink-0 relative">
      {/* Primary Tools List */}
      <div className="flex flex-col gap-1 w-full items-center">
        {primaryTools.map((tool) => {
          const Icon = tool.icon;
          const isActive = location.pathname === tool.path;

          return (
            <div
              key={tool.id}
              className="relative flex items-center justify-center w-full"
              onMouseEnter={() => setHoveredTool(tool)}
              onMouseLeave={() => setHoveredTool(null)}
            >
              <NavLink
                to={tool.path}
                className={`w-9 h-9 rounded-[2px] flex items-center justify-center transition-colors relative ${
                  isActive
                    ? 'bg-surface-active text-gis-blue font-semibold border-l-2 border-gis-blue'
                    : 'text-text-muted hover:text-text-primary hover:bg-surface-hover'
                }`}
              >
                <Icon className="w-4 h-4" />
              </NavLink>

              {/* Tooltip on hover */}
              {hoveredTool?.id === tool.id && (
                <div className="absolute left-[54px] px-2 py-1 bg-panel-header border border-border-default rounded-[2px] text-[11px] whitespace-nowrap z-50 shadow-md flex items-center gap-2 pointer-events-none">
                  <span className="text-text-primary font-medium">{tool.label}</span>
                  <span className="text-[10px] font-mono text-text-muted bg-panel-bg px-1 rounded-[1px] border border-border-subtle">
                    Alt+{tool.shortcut}
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Bottom Tool: Settings */}
      <div className="w-full flex flex-col items-center pt-2 border-t border-border-subtle">
        <div
          className="relative flex items-center justify-center w-full"
          onMouseEnter={() =>
            setHoveredTool({ id: 'settings', label: 'System Configuration', path: '/settings', icon: Settings, shortcut: 'S' })
          }
          onMouseLeave={() => setHoveredTool(null)}
        >
          <NavLink
            to="/settings"
            className={`w-9 h-9 rounded-[2px] flex items-center justify-center transition-colors ${
              location.pathname === '/settings'
                ? 'bg-surface-active text-gis-blue border-l-2 border-gis-blue'
                : 'text-text-muted hover:text-text-primary hover:bg-surface-hover'
            }`}
          >
            <Settings className="w-4 h-4" />
          </NavLink>

          {hoveredTool?.id === 'settings' && (
            <div className="absolute left-[54px] px-2 py-1 bg-panel-header border border-border-default rounded-[2px] text-[11px] whitespace-nowrap z-50 shadow-md flex items-center gap-2 pointer-events-none">
              <span className="text-text-primary font-medium">Settings</span>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
