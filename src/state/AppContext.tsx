import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { Habitation } from '../types';
import { api } from '../lib/api';

interface AppContextType {
  selectedState: string;
  setSelectedState: (state: string) => void;
  selectedDistrict: string;
  setSelectedDistrict: (district: string) => void;
  selectedHabitationId: string | null;
  setSelectedHabitationId: (id: string | null) => void;
  habitations: Habitation[];
  setHabitations: React.Dispatch<React.SetStateAction<Habitation[]>>;
  focusPosition: { lat: number; lng: number } | null;
  setFocusPosition: (pos: { lat: number; lng: number } | null) => void;
  selectHabitation: (hab: Habitation) => void;
  isLive: boolean;
  isLoadingHabitations: boolean;
  resetExtent: () => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [selectedState, setSelectedState] = useState<string>('Uttarakhand');
  const [selectedDistrict, setSelectedDistrict] = useState<string>('Chamoli');
  const [selectedHabitationId, setSelectedHabitationId] = useState<string | null>(null);
  const [habitations, setHabitations] = useState<Habitation[]>([]);
  const [focusPosition, setFocusPosition] = useState<{ lat: number; lng: number } | null>(null);
  const [isLive, setIsLive] = useState<boolean>(false);
  const [isLoadingHabitations, setIsLoadingHabitations] = useState<boolean>(true);

  // Fetch habitations whenever selectedState or selectedDistrict changes
  const fetchHabitations = useCallback(async (state: string, district: string) => {
    setIsLoadingHabitations(true);
    try {
      const res = await api.getHabitations({ state, district });
      setHabitations(res.data.items);
      setIsLive(res.isLive);
    } catch {
      // Fallback handled inside api.getHabitations
    } finally {
      setIsLoadingHabitations(false);
    }
  }, []);

  useEffect(() => {
    fetchHabitations(selectedState, selectedDistrict);
  }, [selectedState, selectedDistrict, fetchHabitations]);

  const selectHabitation = useCallback((hab: Habitation) => {
    if (hab.district && hab.district !== selectedDistrict) {
      setSelectedDistrict(hab.district);
    }
    setSelectedHabitationId(hab.id);
    if (hab.position) {
      setFocusPosition({ ...hab.position });
    }
  }, [selectedDistrict]);

  const resetExtent = useCallback(() => {
    setFocusPosition({ lat: 30.43, lng: 79.35 });
    setSelectedHabitationId(null);
  }, []);

  return (
    <AppContext.Provider
      value={{
        selectedState,
        setSelectedState,
        selectedDistrict,
        setSelectedDistrict,
        selectedHabitationId,
        setSelectedHabitationId,
        habitations,
        setHabitations,
        focusPosition,
        setFocusPosition,
        selectHabitation,
        isLive,
        isLoadingHabitations,
        resetExtent,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useAppStore(): AppContextType {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppStore must be used within an AppProvider');
  }
  return context;
}
