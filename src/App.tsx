import { lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppProvider } from './state/AppContext';
import { AppShell } from './components/layout/AppShell';

const CommandCentre = lazy(() => import('./pages/CommandCentre').then((m) => ({ default: m.CommandCentre })));
const Habitations = lazy(() => import('./pages/Habitations').then((m) => ({ default: m.Habitations })));
const RedZones = lazy(() => import('./pages/RedZones').then((m) => ({ default: m.RedZones })));
const RelocationPriority = lazy(() => import('./pages/RelocationPriority').then((m) => ({ default: m.RelocationPriority })));
const CandidateSites = lazy(() => import('./pages/CandidateSites').then((m) => ({ default: m.CandidateSites })));
const DigitalTwin = lazy(() => import('./pages/DigitalTwin').then((m) => ({ default: m.DigitalTwin })));
const ScenarioLab = lazy(() => import('./pages/ScenarioLab').then((m) => ({ default: m.ScenarioLab })));
const FieldVerification = lazy(() => import('./pages/FieldVerification').then((m) => ({ default: m.FieldVerification })));
const Reports = lazy(() => import('./pages/Reports').then((m) => ({ default: m.Reports })));
const DataSources = lazy(() => import('./pages/DataSources').then((m) => ({ default: m.DataSources })));
const SettingsPage = lazy(() => import('./pages/SettingsPage').then((m) => ({ default: m.SettingsPage })));

export default function App() {
  return (
    <BrowserRouter>
      <AppProvider>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/" element={<CommandCentre />} />
            <Route path="/habitations" element={<Habitations />} />
            <Route path="/red-zones" element={<RedZones />} />
            <Route path="/relocation-priority" element={<RelocationPriority />} />
            <Route path="/candidate-sites" element={<CandidateSites />} />
            <Route path="/digital-twin" element={<DigitalTwin />} />
            <Route path="/scenario-lab" element={<ScenarioLab />} />
            <Route path="/field-verification" element={<FieldVerification />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/data-sources" element={<DataSources />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </AppProvider>
    </BrowserRouter>
  );
}
