import { useState, useCallback, useEffect } from 'react';
import { CommandCentreMap } from '../components/map/CommandCentreMap';
import { FeatureInspector, type SelectedFeature } from '../components/inspector/FeatureInspector';
import { AnalyticalDrawer } from '../components/drawer/AnalyticalDrawer';
import type { Habitation } from '../types';
import { useAppStore } from '../state/AppContext';

export function CommandCentre() {
  const {
    selectedHabitationId,
    setSelectedHabitationId,
    habitations,
    focusPosition,
    setFocusPosition,
    resetExtent,
  } = useAppStore();

  const [selectedFeature, setSelectedFeature] = useState<SelectedFeature>(null);

  // Sync selectedHabitationId from store to local selectedFeature and focusPosition
  useEffect(() => {
    if (selectedHabitationId && habitations.length > 0) {
      const match = habitations.find((h) => h.id === selectedHabitationId);
      if (match) {
        setSelectedFeature({ type: 'HABITATION', data: match });
        if (match.position) {
          setFocusPosition({ ...match.position });
        }
      }
    }
  }, [selectedHabitationId, habitations, setFocusPosition]);

  const handleSelectFeature = useCallback((feature: SelectedFeature) => {
    setSelectedFeature(feature);
    if (feature?.type === 'HABITATION') {
      setSelectedHabitationId(feature.data.id);
      setFocusPosition({ ...feature.data.position });
    } else if (feature?.type === 'CANDIDATE_SITE') {
      setFocusPosition({ ...feature.data.position });
    } else if (feature?.type === 'INFRASTRUCTURE') {
      setFocusPosition({ ...feature.data.position });
    }
  }, [setSelectedHabitationId, setFocusPosition]);

  const handleSelectHabitation = useCallback((hab: Habitation) => {
    setSelectedFeature({ type: 'HABITATION', data: hab });
    setSelectedHabitationId(hab.id);
    setFocusPosition({ ...hab.position });
  }, [setSelectedHabitationId, setFocusPosition]);

  const handleCloseInspector = useCallback(() => {
    setSelectedFeature(null);
    setSelectedHabitationId(null);
  }, [setSelectedHabitationId]);

  // Listen for reset extent custom event
  useEffect(() => {
    const handleReset = () => {
      resetExtent();
      setSelectedFeature(null);
    };
    window.addEventListener('map:reset-extent', handleReset);
    return () => window.removeEventListener('map:reset-extent', handleReset);
  }, [resetExtent]);

  // Listen for escape key to close inspector
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleCloseInspector();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleCloseInspector]);

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
