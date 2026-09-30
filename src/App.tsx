import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppProvider } from './state/AppContext';
import { AppShell } from './components/layout/AppShell';
import { CommandCentre } from './pages/CommandCentre';
import { Habitations } from './pages/Habitations';
import { RedZones } from './pages/RedZones';
import { RelocationPriority } from './pages/RelocationPriority';
import { CandidateSites } from './pages/CandidateSites';
import { DigitalTwin } from './pages/DigitalTwin';
import { ScenarioLab } from './pages/ScenarioLab';
import { FieldVerification } from './pages/FieldVerification';
import { Reports } from './pages/Reports';
import { DataSources } from './pages/DataSources';
import { SettingsPage } from './pages/SettingsPage';

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
