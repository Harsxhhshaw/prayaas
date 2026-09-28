import { Outlet } from 'react-router-dom';
import { ToolRail } from './ToolRail';
import { TopBar } from './TopBar';
import { MetricsStrip } from './MetricsStrip';

export function AppShell() {
  return (
    <div className="h-screen w-screen flex flex-col bg-workspace overflow-hidden select-none">
      {/* 1. Top Command Bar (48px) */}
      <TopBar />

      {/* 2. Operational Metrics Strip (28px) */}
      <MetricsStrip />

      {/* 3. Workstation Body: Tool Rail + Central Workspace */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Tool Rail (52px) */}
        <ToolRail />

        {/* Central Workspace (70-85% map or full-page inventory) */}
        <main className="flex-1 relative overflow-hidden bg-workspace">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
