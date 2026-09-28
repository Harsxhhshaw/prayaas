import { useState, useCallback, useEffect } from 'react';
import { CommandCentreMap } from '../components/map/CommandCentreMap';
import { FeatureInspector, type SelectedFeature } from '../components/inspector/FeatureInspector';
import { AnalyticalDrawer } from '../components/drawer/AnalyticalDrawer';
import type { Habitation } from '../types';

export function CommandCentre() {
  const [selectedFeature, setSelectedFeature] = useState<SelectedFeature>(null);
  const [focusPosition, setFocusPosition] = useState<{ lat: number; lng: number } | null>(null);

  const handleSelectFeature = useCallback((feature: SelectedFeature) => {
    setSelectedFeature(feature);
    if (feature?.type === 'HABITATION') {
      setFocusPosition({ ...feature.data.position });
    } else if (feature?.type === 'CANDIDATE_SITE') {
      setFocusPosition({ ...feature.data.position });
    } else if (feature?.type === 'INFRASTRUCTURE') {
      setFocusPosition({ ...feature.data.position });
    }
  }, []);

  const handleSelectHabitation = useCallback((hab: Habitation) => {
    setSelectedFeature({ type: 'HABITATION', data: hab });
    setFocusPosition({ ...hab.position });
  }, []);

  // Listen for reset extent custom event
  useEffect(() => {
    const handleReset = () => {
      setFocusPosition({ lat: 30.43, lng: 79.35 });
    };
    window.addEventListener('map:reset-extent', handleReset);
    return () => window.removeEventListener('map:reset-extent', handleReset);
  }, []);

  // Listen for escape key to close inspector
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setSelectedFeature(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="w-full h-full flex flex-row overflow-hidden relative bg-workspace">
      {/* 1. Map Workstation Area (Occupies 70-85% or 100% when inspector closed) */}
      <div className="flex-1 h-full flex flex-col relative overflow-hidden">
        {/* Central GIS Map Canvas */}
        <div className="flex-1 relative overflow-hidden">
          <CommandCentreMap
            onSelectFeature={handleSelectFeature}
            selectedFeature={selectedFeature}
            focusPosition={focusPosition}
          />
        </div>

        {/* Collapsible Bottom Analytical Drawer */}
        <AnalyticalDrawer
          onSelectHabitation={handleSelectHabitation}
          selectedHabitationId={selectedFeature?.type === 'HABITATION' ? selectedFeature.data.id : undefined}
        />
      </div>

      {/* 2. Right Contextual Feature Inspector (Closed by default, opens on selection) */}
      <FeatureInspector
        feature={selectedFeature}
        onClose={() => setSelectedFeature(null)}
        onFocusFeature={setFocusPosition}
      />
    </div>
  );
}
