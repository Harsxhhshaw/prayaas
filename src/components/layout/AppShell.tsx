import { Suspense } from 'react';
import { Outlet } from 'react-router-dom';
import { ToolRail } from './ToolRail';
import { TopBar } from './TopBar';
import { MetricsStrip } from './MetricsStrip';
import { ServerStatusBanner } from './ServerStatusBanner';

export function AppShell() {
  return (
    <div className="h-screen w-screen flex flex-col bg-workspace overflow-hidden select-none">
      {/* 1. Top Command Bar (48px) */}
      <TopBar />

      {/* Global Server Mode / Cold-Start Banner */}
      <ServerStatusBanner />

      {/* 2. Operational Metrics Strip (28px) */}
      <MetricsStrip />

      {/* 3. Workstation Body: Tool Rail + Central Workspace */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Tool Rail (52px) */}
        <ToolRail />

        {/* Central Workspace (70-85% map or full-page inventory) */}
        <main className="flex-1 relative overflow-hidden bg-workspace">
          <Suspense
            fallback={
              <div className="h-full w-full flex flex-col items-center justify-center bg-workspace font-mono text-xs text-text-muted">
                <div className="w-5 h-5 border-2 border-gis-blue border-t-transparent rounded-full animate-spin mb-2" />
                <span>INITIALIZING WORKSPACE...</span>
              </div>
            }
          >
            <Outlet />
          </Suspense>
        </main>
      </div>
    </div>
  );
}
